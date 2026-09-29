from dash import html
import dash_bootstrap_components as dbc


def section_header(title, tooltip_text=None, header_id=None):
    """A section title, optionally with a hover-info icon.

    header_id is required if tooltip_text is provided — dbc.Tooltip
    needs a target id to attach the hover popup to.
    """
    if tooltip_text is None:
        return html.H4(title, className="mb-3")

    icon_id = f"{header_id}-info-icon"
    return html.Div([
        html.H4([
            title,
            html.I(className="bi bi-info-circle-fill text-muted ms-2", id=icon_id),
        ], className="d-inline-flex align-items-center mb-3"),
        dbc.Tooltip(tooltip_text, target=icon_id, placement="right"),
    ])