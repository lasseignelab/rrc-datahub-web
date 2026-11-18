"""
OpenAI-backed assistant that answers questions about the DataHub's data.

The assistant gets read-only tools over the sample metadata and gene
expression tables (see db/chat_tools.py) through OpenAI Chat Completions
function calling. This module runs the tool loop itself: each tool call the
model makes is dispatched to a Python function and its JSON result is sent
back until the model writes its answer. Conversation history between turns
is kept as plain text only, which keeps the browser-side history store small.

Requires OPENAI_API_KEY in the environment (loaded from .env). OPENAI_MODEL
optionally overrides the default model.
"""

import json
import logging
import os
from collections.abc import Callable
from urllib.parse import urlencode

import openai
from dotenv import load_dotenv
from openai.types.chat import (
    ChatCompletionFunctionToolParam,
    ChatCompletionMessageParam,
)

from db import chat_tools

load_dotenv()

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gpt-5.4-mini"
API_KEY_ENV = "OPENAI_API_KEY"
MODEL_ENV = "OPENAI_MODEL"
# Caps how many tool round-trips one question may take, bounding cost and
# latency if the model keeps searching.
MAX_TOOL_ITERATIONS = 8
# Only the most recent turns are replayed, so a long session cannot grow the
# request (and its cost) without bound.
MAX_HISTORY_MESSAGES = 20

NOT_CONFIGURED_MESSAGE = (
    "The data assistant isn't configured yet (missing or invalid API key)."
)
BUSY_MESSAGE = "The data assistant is busy right now. Please try again in a minute."
ERROR_MESSAGE = "Sorry, the data assistant hit an error. Please try again."
UNREACHABLE_MESSAGE = "The data assistant couldn't be reached. Please try again later."
REFUSAL_MESSAGE = "Sorry, I can't help with that question."
INCOMPLETE_MESSAGE = (
    "I couldn't finish answering that. Try asking a narrower question, "
    "for example about one gene or one dataset."
)

# Must match the whitelist in db/chat_tools.SAMPLE_FIELDS (a test checks).
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
- Each dataset was reprocessed with the same pipeline for the DataHub, so \
expression values are more comparable across datasets.
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
            params.append((name, f"{float(number):g}"))
    return "/charts?" + urlencode(params) if params else "/charts"


def _chart_link(**arguments) -> dict:
    """Tool wrapper: return the charts URL as a JSON-ready dict."""
    return {"url": build_chart_link(**arguments)}


# Each tool name maps to the Python function that runs it. The model's
# arguments are passed as keyword arguments, so names must match the
# "properties" in the schemas below.
TOOL_FUNCTIONS: dict[str, Callable[..., dict]] = {
    "list_field_values": chat_tools.list_field_values,
    "find_datasets": chat_tools.find_datasets,
    "describe_dataset": chat_tools.describe_dataset,
    "gene_expression_summary": chat_tools.gene_expression_summary,
    "chart_link": _chart_link,
}

_FIELD_SCHEMA = {"type": "string", "enum": list(SAMPLE_FIELD_NAMES)}
_FILTERS_SCHEMA = {
    "type": "object",
    "description": (
        "Map of sample field name to the exact value to match "
        '(case-insensitive), e.g. {"sex": "female", "underlying_variant": '
        '"Pkd1"}. Field names are the same as for list_field_values.'
    ),
    "properties": {name: {"type": "string"} for name in SAMPLE_FIELD_NAMES},
    "additionalProperties": False,
}
_VALUE_LIST_SCHEMA = {"type": "array", "items": {"type": "string"}}


def _tool(name: str, description: str, properties: dict, required=()):
    """Build one function-tool definition in the Chat Completions format."""
    tool: ChatCompletionFunctionToolParam = {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": list(required),
                "additionalProperties": False,
            },
        },
    }
    return tool


TOOLS: list[ChatCompletionFunctionToolParam] = [
    _tool(
        "list_field_values",
        "List the distinct values of one sample metadata field, with counts. "
        "Call this before filtering on a field, because values are not "
        "standardized across datasets.",
        {"field": _FIELD_SCHEMA},
        required=["field"],
    ),
    _tool(
        "find_datasets",
        "Find datasets that have samples matching all the given filters. "
        "Returns each matching BioProject with its count of matching samples.",
        {
            "filters": _FILTERS_SCHEMA,
            "min_age_days": {
                "type": "number",
                "description": "Keep samples whose age range reaches at "
                "least this many days.",
            },
            "max_age_days": {
                "type": "number",
                "description": "Keep samples whose age range starts at or "
                "below this many days.",
            },
        },
    ),
    _tool(
        "describe_dataset",
        "Describe one dataset: total samples and value counts for each field.",
        {
            "bioproject": {
                "type": "string",
                "description": "The dataset's BioProject accession, "
                "e.g. PRJNA285844.",
            }
        },
        required=["bioproject"],
    ),
    _tool(
        "gene_expression_summary",
        "Summarize a gene's expression (TPM) per dataset and sample group. "
        "Returns sample count, mean, median, min and max TPM for each "
        "dataset/group pair. Gene names are matched case-insensitively with "
        "typo tolerance.",
        {
            "gene": {"type": "string", "description": "Gene symbol, e.g. Pkd1."},
            "group_by": {
                **_FIELD_SCHEMA,
                "description": "Sample field to split each dataset's samples "
                "by (default genotype).",
            },
            "bioproject": {
                "type": "string",
                "description": "Limit to one dataset's BioProject accession.",
            },
            "filters": _FILTERS_SCHEMA,
        },
        required=["gene"],
    ),
    _tool(
        "chart_link",
        "Build the link to the charts page for an answer. The charts page "
        "opens with its dataset table limited to `datasets`, the first of "
        "them selected for plotting, `gene` selected, and its dataset filters "
        "set to the values given here. Only these filters exist on the charts "
        "page; leave out others (e.g. genotype or tissue). Use exact values "
        "as returned by list_field_values.",
        {
            "datasets": {
                **_VALUE_LIST_SCHEMA,
                "description": "BioProject accessions the answer names, most "
                "relevant first.",
            },
            "gene": {"type": "string", "description": "Gene symbol to plot."},
            "scientific_name": {
                **_VALUE_LIST_SCHEMA,
                "description": 'Species values to select, e.g. ["Mus musculus"].',
            },
            "sex": {**_VALUE_LIST_SCHEMA, "description": "Sex values to select."},
            "underlying_variant": {
                **_VALUE_LIST_SCHEMA,
                "description": "Underlying variant values to select.",
            },
            "sample_type": {
                **_VALUE_LIST_SCHEMA,
                "description": "Sample type values to select.",
            },
            "min_age_days": {
                "type": "number",
                "description": "Lower bound of the age filter, in days.",
            },
            "max_age_days": {
                "type": "number",
                "description": "Upper bound of the age filter, in days.",
            },
        },
        required=["datasets"],
    ),
]

_client: openai.OpenAI | None = None


def _get_client() -> openai.OpenAI:
    """Return a shared OpenAI client, created on first use."""
    global _client
    if _client is None:
        _client = openai.OpenAI()
    return _client


def run_tool(name: str, arguments_json: str) -> str:
    """Run one tool call and return its result as a JSON string.

    Bad arguments are reported back to the model as an error result rather
    than raised, so it can correct itself on the next round.
    """
    function = TOOL_FUNCTIONS.get(name)
    if function is None:
        result: dict = {"error": f"Unknown tool '{name}'."}
    else:
        try:
            arguments = json.loads(arguments_json or "{}")
            if not isinstance(arguments, dict):
                raise ValueError("Tool arguments must be a JSON object.")
            # Models sometimes send explicit nulls for optional fields; the
            # Python defaults already mean "not given".
            arguments = {k: v for k, v in arguments.items() if v is not None}
            result = function(**arguments)
        except (ValueError, TypeError) as error:
            result = {"error": str(error)}
    return json.dumps(result, default=str)


def _build_messages(history: list[dict], question: str):
    """Turn the text-only history plus the new question into API messages."""
    messages: list[ChatCompletionMessageParam] = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]
    turns: list[ChatCompletionMessageParam] = []
    for turn in history[-MAX_HISTORY_MESSAGES:]:
        content = str(turn.get("content") or "")
        if not content:
            continue
        if turn.get("role") == "user":
            turns.append({"role": "user", "content": content})
        elif turn.get("role") == "assistant":
            turns.append({"role": "assistant", "content": content})
    # Trimming can leave an assistant turn first; start with a question.
    while turns and turns[0]["role"] != "user":
        turns.pop(0)
    messages.extend(turns)
    messages.append({"role": "user", "content": question})
    return messages


def _complete(messages, model: str, allow_tools: bool):
    """Make one Chat Completions request and return its first choice."""
    response = _get_client().chat.completions.create(
        model=model,
        messages=messages,
        tools=TOOLS,
        # On the last round tools are switched off so the model has to
        # answer with what it has found instead of searching again.
        tool_choice="auto" if allow_tools else "none",
    )
    return response.choices[0]


def _run_conversation(messages, model: str) -> str:
    """Run the tool loop until the model answers; return its reply."""
    for iteration in range(MAX_TOOL_ITERATIONS + 1):
        choice = _complete(messages, model, iteration < MAX_TOOL_ITERATIONS)
        message = choice.message
        if message.refusal or choice.finish_reason == "content_filter":
            return REFUSAL_MESSAGE
        tool_calls = [
            call for call in message.tool_calls or [] if call.type == "function"
        ]
        if not tool_calls:
            if choice.finish_reason == "length":
                logger.warning("Data chat reply hit the token limit")
            return (message.content or "").strip() or INCOMPLETE_MESSAGE
        messages.append(
            {
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": call.function.name,
                            "arguments": call.function.arguments,
                        },
                    }
                    for call in tool_calls
                ],
            }
        )
        for call in tool_calls:
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": run_tool(call.function.name, call.function.arguments),
                }
            )
    return INCOMPLETE_MESSAGE


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
    # Without a key the SDK raises when the client is created; check up
    # front and answer politely instead.
    if not os.environ.get(API_KEY_ENV):
        return NOT_CONFIGURED_MESSAGE
    model = os.environ.get(MODEL_ENV) or DEFAULT_MODEL
    messages = _build_messages(history, question)
    try:
        return _run_conversation(messages, model)
    except (openai.AuthenticationError, openai.PermissionDeniedError):
        logger.exception("OpenAI rejected the API key")
        return NOT_CONFIGURED_MESSAGE
    except openai.RateLimitError:
        # Also raised when the account is out of credit (insufficient_quota).
        logger.warning("OpenAI rate limit or quota hit")
        return BUSY_MESSAGE
    except openai.APIConnectionError:
        logger.exception("Could not reach the OpenAI API")
        return UNREACHABLE_MESSAGE
    except openai.APIError:
        logger.exception("OpenAI API error")
        return ERROR_MESSAGE
