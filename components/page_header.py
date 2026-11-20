import dash_bootstrap_components as dbc
from dash import html


def create_page_header(title: str, description: str, title_id=None, aside=None):
    """Create a consistent introduction header for each page.

    Optional:
    - title_id: id for the H1 (e.g. as an in-page link target).
    - aside: content shown beside the title on extra-wide screens and below
      it on narrower ones (e.g. the About page stat tiles).
    """
    title_props = {"id": title_id} if title_id else {}
    columns = [
        dbc.Col(
            html.Div(
                [
                    html.H1(title, className="page-header-title", **title_props),
                    html.P(
                        description,
                        className="page-header-description",
                    ),
                ],
                className="page-header-content",
            )
        )
    ]
    if aside is not None:
        columns.append(dbc.Col(aside, xs=12, xl="auto", className="page-header-aside"))
    return dbc.Container(
        [dbc.Row(columns, className="align-items-center")],
        fluid=True,
        className="page-header",
    )
