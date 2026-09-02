"""Tests for the main Dash app layout, rendering, and gene search."""
from app import app


def test_server_is_flask_app():
    """App exposes a Flask server instance."""
    assert app.server is not None


def test_layout_contains_h1():
    """Home page layout includes exactly one H1 element."""
    from dash import html
    from pages import home

    def find_all(node, component_type):
        found = []
        if isinstance(node, component_type):
            found.append(node)
        children = getattr(node, "children", None)
        if children is None:
            return found
        if not isinstance(children, list):
            children = [children]
        for child in children:
            found.extend(find_all(child, component_type))
        return found

    h1_elements = find_all(home.layout, html.H1)
    assert len(h1_elements) == 1
    assert h1_elements[0].children == "RRC PKD DataHub"


def test_heading_renders(dash_duo):
    """H1 is visible in the browser after page load."""
    dash_duo.start_server(app)
    dash_duo.wait_for_text_to_equal("h1", "RRC PKD DataHub")


def test_graph_renders(dash_duo):
    """Plotly violin chart renders in the browser on the charts page."""
    dash_duo.start_server(app)
    dash_duo.driver.get(dash_duo.server_url + "/charts")
    dash_duo.wait_for_element(".js-plotly-plot")


def test_lang_attribute(dash_duo):
    """HTML element has lang attribute set to 'en' (WCAG 3.1.1)."""
    dash_duo.start_server(app)
    lang = dash_duo.driver.execute_script("return document.documentElement.lang")
    assert lang == "en"


class TestGeneSearch:
    """Tests for the landing-page gene search callback (handle_gene_search).

    resolve_gene() is mocked rather than hitting the real gene database --
    these tests cover the search bar's own logic (empty input, success,
    typo-correction, redirect URL, and no-match handling), not the accuracy
    of the gene reference data itself.
    """

    def test_empty_query_shows_prompt_and_no_redirect(self, monkeypatch):
        import landing_search
        from dash import no_update

        feedback, redirect = landing_search.handle_gene_search(1, "")

        assert feedback == "Enter a gene name to search."
        assert redirect is no_update

    def test_none_query_shows_prompt_and_no_redirect(self, monkeypatch):
        import landing_search
        from dash import no_update

        feedback, redirect = landing_search.handle_gene_search(1, None)

        assert feedback == "Enter a gene name to search."
        assert redirect is no_update

    def test_exact_match_redirects_with_gene_param(self, monkeypatch):
        import landing_search
        from gene_validate import GeneSearchResult

        monkeypatch.setattr(
            landing_search,
            "resolve_gene",
            lambda query: GeneSearchResult(
                query=query, resolved_gene="Pkd1", corrected=False
            ),
        )

        feedback, redirect = landing_search.handle_gene_search(1, "Pkd1")

        assert "Pkd1" in feedback
        assert "matched from" not in feedback
        assert redirect == f"{landing_search.EXISTING_TAB_PATH}?gene=Pkd1"

    def test_corrected_typo_match_notes_original_query(self, monkeypatch):
        import landing_search
        from gene_validate import GeneSearchResult

        monkeypatch.setattr(
            landing_search,
            "resolve_gene",
            lambda query: GeneSearchResult(
                query=query, resolved_gene="Pkd1", corrected=True
            ),
        )

        feedback, redirect = landing_search.handle_gene_search(1, "Pkd11")

        assert "Pkd1" in feedback
        assert "matched from 'Pkd11'" in feedback
        assert redirect == f"{landing_search.EXISTING_TAB_PATH}?gene=Pkd1"

    def test_no_match_shows_error_and_no_redirect(self, monkeypatch):
        import landing_search
        from dash import no_update
        from gene_validate import GeneSearchResult

        monkeypatch.setattr(
            landing_search,
            "resolve_gene",
            lambda query: GeneSearchResult(
                query=query,
                resolved_gene=None,
                corrected=False,
                error="No gene matching 'Xyz123' found in DataHub.",
            ),
        )

        feedback, redirect = landing_search.handle_gene_search(1, "Xyz123")

        assert feedback == "No gene matching 'Xyz123' found in DataHub."
        assert redirect is no_update

    def test_search_input_has_associated_label(self):
        """Accessibility: gene-search-input must have a <label for=...>
        pointing at its id (regression check for the Pa11y fix)."""
        from dash import html
        import landing_search

        def find_all(node, component_type):
            found = []
            if isinstance(node, component_type):
                found.append(node)
            children = getattr(node, "children", None)
            if children is None:
                return found
            if not isinstance(children, list):
                children = [children]
            for child in children:
                found.extend(find_all(child, component_type))
            return found

        labels = find_all(landing_search.layout, html.Label)
        matching = [label for label in labels if label.htmlFor == "gene-search-input"]
        assert len(matching) == 1
