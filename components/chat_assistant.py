"""
Gemini-backed assistant that answers questions about the DataHub's data.

The assistant gets read-only tools over the sample metadata and gene
expression tables (see db/chat_tools.py). They are plain Python functions
passed to the Google Gen AI SDK, whose automatic function calling runs the
tool loop: Gemini asks for a tool, the SDK calls the function and sends the
result back, until Gemini writes its answer. Conversation history between
turns is kept as plain text only, which keeps the browser-side history
store small.

Requires GEMINI_API_KEY in the environment (loaded from .env). On the free
tier, Google may use questions and answers to improve its products.
"""

import json
import logging
import os
from typing import Any
from urllib.parse import urlencode

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types
from pydantic import BaseModel

from db import chat_tools

load_dotenv()

logger = logging.getLogger(__name__)

MODEL = "gemini-3.5-flash-lite"
API_KEY_ENV = "GEMINI_API_KEY"
# Caps how many tool calls one question may make, bounding latency and
# free-tier quota use if the model keeps searching.
MAX_TOOL_CALLS = 8
# Only the most recent turns are replayed, so a long session cannot grow the
# request without bound.
MAX_HISTORY_MESSAGES = 20

NOT_CONFIGURED_MESSAGE = (
    "The data assistant isn't configured yet (missing or invalid API key)."
)
BUSY_MESSAGE = (
    "The data assistant has reached its usage limit for now. "
    "Please try again in a minute."
)
ERROR_MESSAGE = "Sorry, the data assistant hit an error. Please try again."
BLOCKED_MESSAGE = "Sorry, I can't help with that question."
INCOMPLETE_MESSAGE = (
    "I couldn't finish answering that. Try asking a narrower question, "
    "for example about one gene or one dataset."
)

# Field names the tools accept. Tool parameters are annotated `str`, not
# Literal, because the SDK's automatic function calling cannot invoke a
# function with a Literal parameter; db/chat_tools.py rejects any other name
# with an error listing these, which Gemini sees and can correct.
SAMPLE_FIELD_NAMES = (
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
)

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
the age argument (min_days/max_days) to filter by age.
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


class SampleFilters(BaseModel):
    """Exact sample metadata values to match (case-insensitive).

    Leave a field out to not filter on it. Use values as returned by
    list_field_values.
    """

    scientific_name: str | None = None
    sample_type: str | None = None
    sex: str | None = None
    underlying_variant: str | None = None
    genotype: str | None = None
    strain: str | None = None
    tissue: str | None = None
    source_name: str | None = None
    age: str | None = None
    treatment: str | None = None
    treatment_group: str | None = None
    library_layout: str | None = None
    platform: str | None = None


class AgeRange(BaseModel):
    """Age bounds in days; leave a bound out to not limit that side."""

    min_days: float | None = None
    max_days: float | None = None


def _age_bounds(age: AgeRange | None) -> tuple[float | None, float | None]:
    """Return (min_days, max_days) from an optional AgeRange."""
    return (age.min_days, age.max_days) if age else (None, None)


def _filter_map(filters: SampleFilters | None) -> dict[str, str]:
    """Return the filters that were set, as a field name -> value map."""
    if filters is None:
        return {}
    return {
        name: value
        for name, value in filters.model_dump(exclude_none=True).items()
        if value
    }


def _json_safe(payload: dict) -> dict[str, Any]:
    """Round-trip a tool result through JSON so every value is serializable."""
    return json.loads(json.dumps(payload, default=str))


def list_field_values(field: str) -> dict[str, Any]:
    """List the distinct values of one sample metadata field, with counts.

    Call this before filtering on a field, because values are not
    standardized across datasets.

    Args:
        field: The sample metadata field to list. One of: scientific_name,
            sample_type, sex, underlying_variant, genotype, strain, tissue,
            source_name, age, treatment, treatment_group, library_layout,
            platform.
    """
    return _json_safe(chat_tools.list_field_values(field))


def find_datasets(
    filters: SampleFilters | None = None,
    age: AgeRange | None = None,
) -> dict[str, Any]:
    """Find datasets that have samples matching all the given filters.

    Returns each matching BioProject with its count of matching samples.

    Args:
        filters: Sample metadata values to match, e.g. sex "female" and
            underlying_variant "Pkd1".
        age: Keep samples whose age range overlaps these bounds, in days.
    """
    return _json_safe(chat_tools.find_datasets(_filter_map(filters), *_age_bounds(age)))


def describe_dataset(bioproject: str) -> dict[str, Any]:
    """Describe one dataset: total samples and value counts for each field.

    Args:
        bioproject: The dataset's BioProject accession, e.g. PRJNA285844.
    """
    return _json_safe(chat_tools.describe_dataset(bioproject))


def gene_expression_summary(
    gene: str,
    group_by: str = "genotype",
    bioproject: str | None = None,
    filters: SampleFilters | None = None,
) -> dict[str, Any]:
    """Summarize a gene's expression (TPM) per dataset and sample group.

    Returns sample count, mean, median, min and max TPM for each
    dataset/group pair. Gene names are matched case-insensitively with
    typo tolerance.

    Args:
        gene: Gene symbol, e.g. Pkd1.
        group_by: Sample field to split each dataset's samples by; one of
            the field names listed for list_field_values.
        bioproject: Limit to one dataset's BioProject accession.
        filters: Sample metadata values to match, as in find_datasets, to
            restrict which samples are included.
    """
    return _json_safe(
        chat_tools.gene_expression_summary(
            gene, group_by, bioproject, _filter_map(filters)
        )
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


def chart_link(
    datasets: list[str],
    gene: str | None = None,
    scientific_name: list[str] | None = None,
    sex: list[str] | None = None,
    underlying_variant: list[str] | None = None,
    sample_type: list[str] | None = None,
    age: AgeRange | None = None,
) -> dict[str, str]:
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
        age: Age filter bounds, in days.
    """
    return {
        "url": build_chart_link(
            datasets,
            gene,
            scientific_name,
            sex,
            underlying_variant,
            sample_type,
            *_age_bounds(age),
        )
    }


TOOLS = [
    list_field_values,
    find_datasets,
    describe_dataset,
    gene_expression_summary,
    chart_link,
]

# Finish reasons meaning Gemini declined to answer (safety or policy).
_BLOCKED_FINISH_REASONS = {
    types.FinishReason.SAFETY,
    types.FinishReason.PROHIBITED_CONTENT,
    types.FinishReason.BLOCKLIST,
    types.FinishReason.SPII,
}

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    """Return a shared Gemini client, created on first use."""
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.environ.get(API_KEY_ENV))
    return _client


def _build_contents(history: list[dict], question: str) -> list[types.Content]:
    """Turn earlier text-only turns plus the new question into Gemini contents."""
    roles = {"user": "user", "assistant": "model"}
    contents: list[types.Content] = []
    for turn in history[-MAX_HISTORY_MESSAGES:]:
        text = str(turn.get("content") or "")
        role = roles.get(turn.get("role", ""))
        if text and role:
            contents.append(types.Content(role=role, parts=[types.Part(text=text)]))
    # A conversation must start with a user turn.
    while contents and contents[0].role != "user":
        contents.pop(0)
    contents.append(types.Content(role="user", parts=[types.Part(text=question)]))
    return contents


def _message_for_api_error(error: errors.APIError) -> str:
    """Map a Gemini API error to a short user-facing message."""
    message = str(error.message or "")
    if error.code == 429:
        logger.warning("Gemini quota or rate limit hit: %s", message)
        return BUSY_MESSAGE
    if error.code in (401, 403) or "API key" in message:
        logger.error("Gemini rejected the API key: %s", message)
        return NOT_CONFIGURED_MESSAGE
    if error.code == 503:
        logger.warning("Gemini is overloaded: %s", message)
        return BUSY_MESSAGE
    logger.error("Gemini API error %s: %s", error.code, message)
    return ERROR_MESSAGE


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
    if not os.environ.get(API_KEY_ENV):
        return NOT_CONFIGURED_MESSAGE

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=TOOLS,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(
            maximum_remote_calls=MAX_TOOL_CALLS
        ),
    )
    try:
        response = _get_client().models.generate_content(
            model=MODEL,
            contents=_build_contents(history, question),
            config=config,
        )
    except errors.APIError as error:
        return _message_for_api_error(error)
    # Network failures surface as transport-library exceptions; whatever the
    # cause, the page should show a message rather than a stack trace.
    except Exception:  # pylint: disable=broad-exception-caught
        logger.exception("Could not get an answer from Gemini")
        return ERROR_MESSAGE

    if response.prompt_feedback and response.prompt_feedback.block_reason:
        return BLOCKED_MESSAGE
    candidate = response.candidates[0] if response.candidates else None
    if candidate and candidate.finish_reason in _BLOCKED_FINISH_REASONS:
        return BLOCKED_MESSAGE
    if candidate and candidate.finish_reason == types.FinishReason.MAX_TOKENS:
        logger.warning("Data chat reply hit the output token limit")
    text = (response.text or "").strip()
    return text or INCOMPLETE_MESSAGE
