"""
Starlette ASGI Web Server for Zomato AI Concierge.

Serves the pixel-perfect Google Stitch dark-theme frontend and provides REST API
endpoints connected to the RecommendationEngine and Groq Llama 3.3 70B inference.
"""

from contextlib import asynccontextmanager
import html
import os
from pathlib import Path
import re
import sys
from typing import Any
import pandas as pd
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, Response
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles
import uvicorn

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.filters.filter_engine import UserPreferences
from src.recommendation.engine import RecommendationEngine, RecommendationResult
from src.utils.config import AppConfig
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Global singleton engine
_engine: RecommendationEngine | None = None
_preprocessed_df: pd.DataFrame | None = None


def get_engine() -> RecommendationEngine:
    global _engine, _preprocessed_df
    if _engine is None:
        logger.info("Initializing RecommendationEngine for Web Server...")
        cfg = AppConfig()
        _engine = RecommendationEngine.from_config(cfg)
        _preprocessed_df = _engine.get_preprocessed_data()
        logger.info(f"Engine ready with {len(_preprocessed_df):,} restaurants.")
    return _engine


def lookup_metadata(name: str) -> dict[str, Any]:
    global _preprocessed_df
    if _preprocessed_df is None or _preprocessed_df.empty:
        return {}
    matches = _preprocessed_df[
        _preprocessed_df["name"].str.lower() == str(name).strip().lower()
    ]
    if not matches.empty:
        row = matches.iloc[0]
        return {
            "location": str(row.get("location", "Bangalore")),
            "votes": int(row.get("votes", 0)),
            "online_order": bool(row.get("online_order", False)),
            "book_table": bool(row.get("book_table", False)),
            "cost_for_two": str(row.get("approx_cost", row.get("cost_for_two", "₹800"))),
            "cuisines": str(row.get("cuisines", "")),
        }
    return {}


async def index_handler(request: Request) -> Response:
    """Serve the Stitch dark-theme web page."""
    html_path = PROJECT_ROOT / "index.html"
    if not html_path.exists():
        html_path = Path(__file__).parent / "index.html"
    if not html_path.exists():
        html_path = PROJECT_ROOT / "stitch" / "code.html"
    return HTMLResponse(html_path.read_text(encoding="utf-8"))


async def health_handler(request: Request) -> Response:
    """Health check endpoint."""
    return JSONResponse({"status": "ok", "service": "zomato-ai-concierge"})


async def options_handler(request: Request) -> Response:
    """Return available areas, cuisines, and counts for UI selectors."""
    engine = get_engine()
    locations = engine.get_available_locations()
    cuisines = engine.get_available_cuisines()
    df = engine.get_preprocessed_data()
    return JSONResponse(
        {
            "locations": locations,
            "cuisines": cuisines,
            "total_spots": len(df),
            "total_regions": len(locations),
            "total_cuisines": len(cuisines),
        }
    )


async def recommend_handler(request: Request) -> Response:
    """
    Handle recommendation requests with user filter criteria.
    Accepts JSON payload and returns ranked recommendations with metadata.
    """
    try:
        body = await request.json()
    except Exception:
        body = {}

    area = body.get("location")
    if area in ("all", "Any Neighborhood (Bangalore)", "All Bangalore", "", None):
        area = None

    budget = body.get("budget")
    if budget in ("any", "Any Budget", "", None):
        budget = None
    elif budget == "low":
        budget = "Low"
    elif budget == "med":
        budget = "Medium"
    elif budget == "high":
        budget = "High"

    cuisine = body.get("cuisine")
    if cuisine in ("all", "All Cuisines", "", None):
        cuisine = None

    try:
        min_rating = float(body.get("min_rating", 3.5))
    except (ValueError, TypeError):
        min_rating = 3.5

    try:
        top_n = int(body.get("top_n", 3))
    except (ValueError, TypeError):
        top_n = 3

    vibe_raw = str(body.get("additional_prefs", "")).strip()
    vibe = re.sub(r"<[^>]*>", "", vibe_raw)[:500] if vibe_raw else None

    user_prefs = UserPreferences(
        location=area,
        budget=budget,
        cuisine=cuisine,
        min_rating=min_rating,
        additional_prefs=vibe,
    )

    engine = get_engine()
    result: RecommendationResult = engine.recommend(user_prefs, top_n=top_n)

    # Format recommendations for Stitch UI card rendering
    formatted_recs: list[dict[str, Any]] = []
    base_match = 98.4
    for idx, rec in enumerate(result.recommendations, start=1):
        meta = lookup_metadata(rec.restaurant_name)
        score = max(85.0, round(base_match - ((idx - 1) * 3.8), 1))
        
        # Tags calculation
        votes = meta.get("votes", 1200)
        sentiment = "Very High Sentiment" if rec.rating >= 4.5 else f"{votes:,}+ reviews"
        
        # Determine a contextual highlight badge
        cuisine_lower = rec.cuisine.lower()
        if "pizza" in cuisine_lower or "italian" in cuisine_lower:
            special_tag = "Wood Fired" if idx % 2 == 1 else "Artisanal Crust"
        elif "cafe" in cuisine_lower or "dessert" in cuisine_lower:
            special_tag = "Fast WiFi & Calm"
        elif "biryani" in cuisine_lower or "indian" in cuisine_lower:
            special_tag = "Heritage Legacy"
        elif "brew" in cuisine_lower or "bar" in cuisine_lower:
            special_tag = "Craft Brews"
        else:
            special_tag = "Chef's Special"

        if idx == 1 and rec.rating >= 4.4:
            special_tag = "Pet Friendly"

        formatted_recs.append(
            {
                "rank": idx,
                "name": rec.restaurant_name,
                "cuisine": rec.cuisine,
                "rating": round(rec.rating, 1),
                "estimated_cost": rec.estimated_cost or meta.get("cost_for_two", "₹800 for two"),
                "explanation": rec.explanation,
                "location": meta.get("location", area or "Bangalore"),
                "votes": votes,
                "match_score": score,
                "sentiment": sentiment,
                "online_order": meta.get("online_order", True),
                "book_table": meta.get("book_table", True),
                "special_tag": special_tag,
            }
        )

    return JSONResponse(
        {
            "success": True,
            "recommendations": formatted_recs,
            "total_matches": result.total_matches,
            "filters_applied": result.filters_applied,
            "filters_relaxed": result.filters_relaxed,
            "is_fallback": result.is_fallback,
            "fallback_reason": result.fallback_reason,
        }
    )


@asynccontextmanager
async def lifespan(app: Starlette):
    # Pre-warm recommendation engine on server start
    get_engine()
    yield


middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
]

routes = [
    Route("/", index_handler, methods=["GET"]),
    Route("/api/health", health_handler, methods=["GET"]),
    Route("/api/options", options_handler, methods=["GET"]),
    Route("/api/recommend", recommend_handler, methods=["POST"]),
]

app = Starlette(
    debug=True,
    routes=routes,
    middleware=middleware,
    lifespan=lifespan,
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("ui.server:app", host="0.0.0.0", port=port, reload=False)

