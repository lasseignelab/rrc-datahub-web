
import dash_bootstrap_components as dbc
from dash import html


def section_header(
    title,
    tooltip_text=None,
    header_id=None,
    heading_id=None,
):
    """Render a styled section title with an optional info tooltip."""

    children = [title]
    elements = []

    if tooltip_text is not None:
        if not header_id:
            raise ValueError(
                "header_id is required when tooltip_text is provided"
            )

        icon_id = f"{header_id}-info-icon"
        tooltip_id = f"{icon_id}-tooltip"

        children.append(
            html.Button(
                html.I(
                    className="bi bi-info-circle-fill",
                    **{"aria-hidden": "true"},
                ),
                id=icon_id,
                type="button",
                className="section-info-button",
                **{
                    "aria-label": f"More information about {title}",
                    "aria-describedby": tooltip_id,
                },
            )
        )

        elements.append(
            dbc.Tooltip(
                tooltip_text,
                target=icon_id,
                id=tooltip_id,
            )
        )

    elements.append(
        html.Div(
            children,
            **({"id": heading_id} if heading_id else {}),
            className="section-header-title",
        )
    )

    return html.Div(elements, className="section-header")
