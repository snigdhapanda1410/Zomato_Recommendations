"""
Unit tests for UI styles and card HTML rendering.
"""

from ui.styles import CUSTOM_CSS, render_recommendation_card_html


def test_custom_css_presence() -> None:
    """Verify custom CSS contains expected styling tokens and font imports."""
    assert "<style>" in CUSTOM_CSS
    assert "</style>" in CUSTOM_CSS
    assert "--primary-red" in CUSTOM_CSS
    assert "recom-card" in CUSTOM_CSS


def test_render_recommendation_card_html() -> None:
    """Verify HTML card is formatted with sanitized values and badges."""
    html = render_recommendation_card_html(
        rank=1,
        name="Truffles & Burgers",
        cuisine="American, Continental",
        rating=4.7,
        cost="₹800 for two",
        explanation="Amazing handcrafted burgers and cozy atmosphere.",
        location="Koramangala",
        votes=5200,
    )

    assert "#1 MATCH" in html
    assert "Truffles &amp; Burgers" in html or "Truffles & Burgers" in html
    assert "American, Continental" in html
    assert "★ 4.7" in html
    assert "₹800 for two" in html
    assert "📍 Koramangala" in html
    assert "5,200 reviews" in html
    assert "Amazing handcrafted burgers" in html


def test_render_card_handles_missing_optional_metadata() -> None:
    """Verify HTML card gracefully omits location and reviews when None."""
    html = render_recommendation_card_html(
        rank=2,
        name="Simple Cafe",
        cuisine="Cafe",
        rating=4.2,
        cost="₹500 for two",
        explanation="Nice tea and snacks.",
        location=None,
        votes=None,
    )

    assert "#2 MATCH" in html
    assert "Simple Cafe" in html
    assert "badge-location" not in html
    assert "badge-votes" not in html
