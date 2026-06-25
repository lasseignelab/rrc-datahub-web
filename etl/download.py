# ETL download step: pulls source data into a local staging directory.
#
# Three sources:
#   1. GitHub (lasseignelab/rrc-datahub) — doc/geo_datasets.csv
#   2. GitHub (lasseignelab/rrc-datahub) — results/transformed-metadata/ (recursive)
#   3. UAB Cheaha via SSH/SCP — PRJNA*/star_salmon/salmon.merged.gene_tpm.tsv
#
# Required environment variables (see .env.example):
#   GITHUB_TOKEN          — personal access token with repo read scope
#   CHEAHA_HOST           — Cheaha SSH hostname (e.g. cheaha.rc.uab.edu)
#   CHEAHA_USER           — Cheaha SSH username
#   CHEAHA_BASE_PATH      — remote base path containing PRJNA* directories
#   STAGING_DIR           — local directory for downloaded files (default: staging/)

# pylint: disable=import-error
import getpass
import logging
import os
import re
from pathlib import Path
from typing import Sequence

import paramiko  # type: ignore[import-untyped]
import requests  # type: ignore[import-untyped]
from dotenv import load_dotenv  # type: ignore[import-untyped]

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"
GITHUB_REPO = "lasseignelab/rrc-datahub"
GEO_DATASETS_PATH = "doc/geo_datasets.csv"
TRANSFORMED_METADATA_PATH = "results/transformed-metadata"
CHEAHA_TPM_GLOB = "PRJNA*/star_salmon/salmon.merged.gene_tpm.tsv"


def _staging_dir() -> Path:
    """Return the local staging directory, creating it if necessary."""
    path = Path(os.getenv("STAGING_DIR", "staging"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def _github_headers() -> dict:
    """Build Authorization headers from GITHUB_TOKEN."""
    token = os.environ["GITHUB_TOKEN"]
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }


def _download_github_file(repo_path: str, dest: Path) -> None:
    """Download a single file from the GitHub repo via the Contents API."""
    url = f"{GITHUB_API}/repos/{GITHUB_REPO}/contents/{repo_path}"
    response = requests.get(url, headers=_github_headers(), timeout=30)
    response.raise_for_status()
    data = response.json()

    file_response = requests.get(
        data["download_url"], headers=_github_headers(), timeout=60
    )
    file_response.raise_for_status()

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(file_response.content)
    log.info("Downloaded %s → %s", repo_path, dest)


def _download_github_directory(repo_path: str, dest: Path) -> None:
    """Recursively download all files under a GitHub directory."""
    url = f"{GITHUB_API}/repos/{GITHUB_REPO}/contents/{repo_path}"
    response = requests.get(url, headers=_github_headers(), timeout=30)
    response.raise_for_status()

    for entry in response.json():
        entry_dest = dest / entry["name"]
        if entry["type"] == "file":
            _download_github_file(entry["path"], entry_dest)
        elif entry["type"] == "dir":
            _download_github_directory(entry["path"], entry_dest)


def _open_cheaha_transport(host: str, user: str, password: str) -> paramiko.Transport:
    """Open and authenticate a Transport to Cheaha using keyboard-interactive auth.

    Cheaha rejects the SSH password-auth protocol method and uses
    keyboard-interactive instead (server sends prompts; client responds).
    SSHClient.connect(password=...) tries password-auth first, which causes the
    server to close the connection before keyboard-interactive is attempted.
    Using Transport directly lets us call auth_interactive() without that detour.
    """
    transport = paramiko.Transport((host, 22))
    transport.start_client()

    # Verify the server's host key against ~/.ssh/known_hosts.
    server_key = transport.get_remote_server_key()
    known_hosts_path = os.path.expanduser("~/.ssh/known_hosts")
    host_keys = paramiko.HostKeys()
    host_keys.load(known_hosts_path)
    if not host_keys.check(host, server_key):
        transport.close()
        raise paramiko.SSHException(
            f"Host key for {host!r} not found in {known_hosts_path}. "
            f"Run: ssh-keyscan {host} >> {known_hosts_path}"
        )

    def _kbd_handler(
        _title: str, _instructions: str, prompts: Sequence[tuple[str, bool]]
    ) -> list[str]:
        return [password for _ in prompts]

    transport.auth_interactive(user, _kbd_handler)
    return transport


def _list_cheaha_tpm_files(transport: paramiko.Transport, base_path: str) -> list[str]:
    """Return all matching salmon.merged.gene_tpm.tsv paths under base_path.

    base_path comes from CHEAHA_BASE_PATH, a trusted environment variable
    controlled by the operator, not end-user input.
    """
    find_cmd = f"find {base_path} -path '{CHEAHA_TPM_GLOB}' -type f"
    channel = transport.open_session()  # nosec B601
    try:
        channel.exec_command(find_cmd)  # nosec B601
        output = channel.makefile("rb").read().decode("utf-8")
        errors = channel.makefile_stderr("rb").read().decode("utf-8").strip()
        if errors:
            log.warning("Cheaha find stderr: %s", errors)
        return [line.strip() for line in output.splitlines() if line.strip()]
    finally:
        channel.close()


def download_geo_datasets(staging: Path) -> Path:
    """Download geo_datasets.csv from GitHub."""
    dest = staging / "geo_datasets.csv"
    log.info("Downloading geo_datasets.csv from GitHub…")
    _download_github_file(GEO_DATASETS_PATH, dest)
    return dest


def download_transformed_metadata(staging: Path) -> Path:
    """Download the full transformed-metadata directory tree from GitHub."""
    dest = staging / "transformed-metadata"
    log.info("Downloading transformed-metadata from GitHub…")
    _download_github_directory(TRANSFORMED_METADATA_PATH, dest)
    return dest


def download_tpm_files(staging: Path) -> list[Path]:
    """Download all PRJNA*/star_salmon/salmon.merged.gene_tpm.tsv files from Cheaha."""
    host = os.environ["CHEAHA_HOST"]
    user = os.environ["CHEAHA_USER"]
    base_path = os.environ["CHEAHA_BASE_PATH"]

    password = getpass.getpass(f"Cheaha password for {user}@{host}: ")

    log.info("Connecting to Cheaha (%s@%s)…", user, host)
    transport = _open_cheaha_transport(host, user, password)

    downloaded: list[Path] = []
    try:
        remote_files = _list_cheaha_tpm_files(transport, base_path)
        if not remote_files:
            log.warning("No TPM files found under %s", base_path)
            return downloaded

        sftp = paramiko.SFTPClient.from_transport(transport)
        if sftp is None:
            raise RuntimeError("Failed to open SFTP session.")
        try:
            for remote_path in remote_files:
                # Preserve the PRJNA accession as a subdirectory in staging.
                match = re.search(r"(PRJNA\d+)", remote_path)
                accession = match.group(1) if match else "unknown"
                local_path = staging / "tpm" / accession / "salmon.merged.gene_tpm.tsv"
                local_path.parent.mkdir(parents=True, exist_ok=True)
                sftp.get(remote_path, str(local_path))
                log.info("Downloaded %s → %s", remote_path, local_path)
                downloaded.append(local_path)
        finally:
            sftp.close()
    finally:
        transport.close()

    return downloaded


def run_download(staging: Path | None = None) -> dict:
    """Run all three downloads and return paths to staged files.

    Returns a dict with keys:
        geo_datasets   — Path to geo_datasets.csv
        metadata_dir   — Path to transformed-metadata directory
        tpm_files      — list[Path] of downloaded TPM TSV files
    """
    if staging is None:
        staging = _staging_dir()

    log.info("Staging directory: %s", staging)

    geo = download_geo_datasets(staging)
    metadata = download_transformed_metadata(staging)
    tpm = download_tpm_files(staging)

    metadata_file_count = sum(1 for _ in metadata.rglob("*") if _.is_file())
    log.info(
        "Download complete — geo_datasets: %s, metadata files: %d, TPM files: %d",
        geo,
        metadata_file_count,
        len(tpm),
    )

    return {"geo_datasets": geo, "metadata_dir": metadata, "tpm_files": tpm}


if __name__ == "__main__":
    run_download()
