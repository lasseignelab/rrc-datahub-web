"""
Claude-backed assistant that answers questions about the DataHub's data.

The assistant gets read-only tools over the sample metadata and gene
expression tables (see db/chat_tools.py) and runs them through the Anthropic
SDK's tool runner. Conversation history between turns is kept as plain text
only: dropping every earlier thinking/tool block is always valid for the API,
and it keeps the browser-side history store small.

Requires ANTHROPIC_API_KEY in the environment (loaded from .env).
"""

import json
import logging
import os
from typing import Literal
from urllib.parse import urlencode

import anthropic
from anthropic import beta_tool
from anthropic.lib.tools import BetaFunctionTool
from anthropic.types import AnthropicBetaParam
from anthropic.types.beta import (
    BetaCacheControlEphemeralParam,
    BetaMessageParam,
    BetaOutputConfigParam,
)
from dotenv import load_dotenv

from db import chat_tools

load_dotenv()

logger = logging.getLogger(__name__)

MODEL = "claude-opus-5-5"
# Caps how many tool round-trips one question may take, bounding cost and
# latency if the model keeps searching.
MAX_TOOL_ITERATIONS = 8
# Only the most recent turns are replayed, so a long session cannot grow the
# request (and its cost) without bound.
MAX_HISTORY_MESSAGES = 20

NOT_CONFIGURED_MESSAGE = (
    "The data assistant isn't configured yet (missing or invalid API key)."
)

SampleField = Literal[
    "scientific_name",
    "sample_type",
    "sex",
    "underlying_variant",
    "genotype",
    "strain",
    "tissue",
    "source_name",
    "age",
    "treatment",
    "treatment_group",
    "library_layout",
    "platform",
]

SYSTEM_PROMPT = """\
You are the data assistant for the PKD RRC DataHub, a public portal of \
polycystic kidney disease (PKD) RNA-seq datasets from GEO. Researchers ask \
you questions about which datasets and samples exist and how genes are \
expressed in them.

Answer only from what the tools return. Use the tools for every factual \
claim about the data; if the tools cannot answer a question, say so plainly \
rather than guessing. Questions unrelated to the DataHub's data are out of \
scope: say briefly that you can only help with the DataHub's datasets.

About the data:
- Each dataset is a GEO BioProject (e.g. PRJNA285844); each sample is one \
sequencing run.
- Metadata values are often "Not provided" or "Not applicable". Values are \
not fully standardized (e.g. "kidney" vs "whole kidney"), so call \
list_field_values to see the real values before filtering on a field.
- Ages are stored as text (the "age" field) and as a range in days; use \
min_age_days/max_age_days to filter by age.
- Expression is reported in TPM (transcripts per million) from salmon.

When an answer names datasets or a gene, end it with a link to the charts \
page. Always get the link from chart_link and never write a charts URL \
yourself. Pass chart_link the datasets your answer names (most relevant \
first), the gene if there is one, and the scientific_name, sex, \
underlying_variant, sample_type and age filters you searched with, so the \
charts page opens with the same dataset filters selected. Write the link as \
relative Markdown, e.g. [View Pkd1 plots for these datasets](/charts?...), \
using the url exactly as chart_link returns it.

Keep answers short and readable: lead with the direct answer, then a \
compact table or list when there are several datasets or groups. Report \
sample counts so readers can judge how much data supports a number.\
"""


def _as_json(payload: dict) -> str:
    """Serialize a tool result for Claude."""
    return json.dumps(payload, default=str)


@beta_tool
def list_field_values(field: SampleField) -> str:
    """List the distinct values of one sample metadata field, with counts.

    Call this before filtering on a field, because values are not
    standardized across datasets.

    Args:
        field: The sample metadata field to list.
    """
    return _as_json(chat_tools.list_field_values(field))


@beta_tool
def find_datasets(
    filters: dict[str, str] | None = None,
    min_age_days: float | None = None,
    max_age_days: float | None = None,
) -> str:
    """Find datasets that have samples matching all the given filters.

    Returns each matching BioProject with its count of matching samples.

    Args:
        filters: Map of sample field name to the exact value to match
            (case-insensitive), e.g. {"sex": "female", "underlying_variant":
            "Pkd1"}. Field names are the same as for list_field_values.
        min_age_days: Keep samples whose age range reaches at least this
            many days.
        max_age_days: Keep samples whose age range starts at or below this
            many days.
    """
    return _as_json(chat_tools.find_datasets(filters, min_age_days, max_age_days))


@beta_tool
def describe_dataset(bioproject: str) -> str:
    """Describe one dataset: total samples and value counts for each field.

    Args:
        bioproject: The dataset's BioProject accession, e.g. PRJNA285844.
    """
    return _as_json(chat_tools.describe_dataset(bioproject))


@beta_tool
def gene_expression_summary(
    gene: str,
    group_by: SampleField = "genotype",
    bioproject: str | None = None,
    filters: dict[str, str] | None = None,
) -> str:
    """Summarize a gene's expression (TPM) per dataset and sample group.

    Returns sample count, mean, median, min and max TPM for each
    dataset/group pair. Gene names are matched case-insensitively with
    typo tolerance.

    Args:
        gene: Gene symbol, e.g. Pkd1.
        group_by: Sample field to split each dataset's samples by.
        bioproject: Limit to one dataset's BioProject accession.
        filters: Map of sample field name to exact value, as in
            find_datasets, to restrict which samples are included.
    """
    return _as_json(
        chat_tools.gene_expression_summary(gene, group_by, bioproject, filters)
    )


def build_chart_link(
    datasets: list[str],
    gene: str | None = None,
    scientific_name: list[str] | None = None,
    sex: list[str] | None = None,
    underlying_variant: list[str] | None = None,
    sample_type: list[str] | None = None,
    min_age_days: float | None = None,
    max_age_days: float | None = None,
) -> str:
    """Return a relative /charts URL that opens with the given dataset limit,
    gene and dataset filters. pages/charts.py parses these parameters
    (_parse_url_filters); the parameter names must stay in step with it.

    Built here, not by the model, so values with spaces or symbols are
    always URL-encoded and the Markdown link cannot break.
    """
    params: list[tuple[str, str]] = []
    if gene and gene.strip():
        params.append(("gene", gene.strip()))
    accessions = [d.strip().upper() for d in datasets if d and d.strip()]
    if accessions:
        params.append(("datasets", ",".join(dict.fromkeys(accessions))))
    for name, values in (
        ("scientific_name", scientific_name),
        ("sex", sex),
        ("underlying_variant", underlying_variant),
        ("sample_type", sample_type),
    ):
        cleaned = [value.strip() for value in values or [] if value.strip()]
        params.extend((name, value) for value in cleaned)
    for name, number in (
        ("min_age_days", min_age_days),
        ("max_age_days", max_age_days),
    ):
        if number is not None:
            params.append((name, f"{number:g}"))
    return "/charts?" + urlencode(params) if params else "/charts"


@beta_tool
def chart_link(
    datasets: list[str],
    gene: str | None = None,
    scientific_name: list[str] | None = None,
    sex: list[str] | None = None,
    underlying_variant: list[str] | None = None,
    sample_type: list[str] | None = None,
    min_age_days: float | None = None,
    max_age_days: float | None = None,
) -> str:
    """Build the link to the charts page for an answer.

    The charts page opens with its dataset table limited to `datasets`, the
    first of them selected for plotting, `gene` selected, and its dataset
    filters set to the values given here. Only these filters exist on the
    charts page; leave out others (e.g. genotype or tissue). Use exact
    values as returned by list_field_values.

    Args:
        datasets: BioProject accessions the answer names, most relevant first.
        gene: Gene symbol to plot, e.g. Pkd1.
        scientific_name: Species values to select, e.g. ["Mus musculus"].
        sex: Sex values to select, e.g. ["female"].
        underlying_variant: Underlying variant values to select.
        sample_type: Sample type values to select.
        min_age_days: Lower bound of the age filter, in days.
        max_age_days: Upper bound of the age filter, in days.
    """
    return _as_json(
        {
            "url": build_chart_link(
                datasets,
                gene,
                scientific_name,
                sex,
                underlying_variant,
                sample_type,
                min_age_days,
                max_age_days,
            )
        }
    )


TOOLS: list[BetaFunctionTool] = [
    list_field_values,
    find_datasets,
    describe_dataset,
    gene_expression_summary,
    chart_link,
]

# Request settings, typed with the SDK's own param types so the
# tool_runner overloads type-check in every linter environment.
OUTPUT_CONFIG: BetaOutputConfigParam = {"effort": "medium"}
# Stable system prompt + tools: cache them across questions.
CACHE_CONTROL: BetaCacheControlEphemeralParam = {"type": "ephemeral"}
# If a safety classifier declines, the API retries on a fallback model it
# chooses instead of failing the question.
BETAS: list[AnthropicBetaParam] = ["server-side-fallback-2026-07-01"]

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    """Return a shared Anthropic client, created on first use."""
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def _final_text(message) -> str:
    """Join the text blocks of a response into one string."""
    return "\n\n".join(
        block.text for block in message.content if block.type == "text"
    ).strip()


def answer_question(history: list[dict], question: str) -> str:
    """Answer a question about the data, given earlier text-only turns.

    Args:
        history: Earlier turns as [{"role": "user"|"assistant", "content": str}].
        question: The new user question.

    Returns:
        The assistant's reply as Markdown. API failures are turned into a
        short user-facing message rather than raised, so the page never
        shows a stack trace.
    """
    messages: list[BetaMessageParam] = []
    for turn in history[-MAX_HISTORY_MESSAGES:]:
        content = str(turn.get("content") or "")
        if not content:
            continue
        if turn.get("role") == "user":
            messages.append({"role": "user", "content": content})
        elif turn.get("role") == "assistant":
            messages.append({"role": "assistant", "content": content})
    # The API requires the first message to come from the user.
    while messages and messages[0]["role"] != "user":
        messages.pop(0)
    messages.append({"role": "user", "content": question})

    # With no credentials the SDK raises a TypeError at request time rather
    # than an API error, so check up front and answer politely instead.
    if not (
        os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")
    ):
        return NOT_CONFIGURED_MESSAGE

    try:
        # The MegaLinter image bundles anthropic 0.84, which predates
        # `fallbacks`; against the pinned SDK in requirements.txt this call
        # type-checks cleanly, so silence only that stale-stub mismatch.
        runner = (
            _get_client().beta.messages.tool_runner(  # pyright: ignore[reportCallIssue]
                model=MODEL,
                max_tokens=16000,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
                max_iterations=MAX_TOOL_ITERATIONS,
                output_config=OUTPUT_CONFIG,
                cache_control=CACHE_CONTROL,
                betas=BETAS,
                fallbacks="default",
            )
        )
        final = runner.until_done()
    except anthropic.AuthenticationError:
        logger.exception("Anthropic authentication failed")
        return NOT_CONFIGURED_MESSAGE
    except anthropic.RateLimitError:
        logger.warning("Anthropic rate limit hit")
        return "The data assistant is busy right now. Please try again in a minute."
    except anthropic.APIStatusError as error:
        logger.exception("Anthropic API error %s", error.status_code)
        return "Sorry, the data assistant hit an error. Please try again."
    except anthropic.APIConnectionError:
        logger.exception("Could not reach the Anthropic API")
        return "The data assistant couldn't be reached. Please try again later."

    if final.stop_reason == "refusal":
        return "Sorry, I can't help with that question."
    if final.stop_reason == "max_tokens":
        logger.warning("Data chat reply hit max_tokens")
    text = _final_text(final)
    if not text:
        return (
            "I couldn't finish answering that. Try asking a narrower question, "
            "for example about one gene or one dataset."
        )
    return text
