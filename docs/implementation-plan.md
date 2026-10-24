# 📋 Implementation Plan

## AI-Powered Restaurant Recommendation System (Zomato Use Case)

---

## 📌 Plan Overview

This document breaks down the project into **6 phases**, each with clearly defined tasks, deliverables, estimated effort, and acceptance criteria. Phases are designed to be **incremental** — each phase produces a working artifact that builds upon the previous one.

### Phase Summary

| Phase | Name                          | Duration  | Key Deliverable                              |
|-------|-------------------------------|-----------|----------------------------------------------|
| 1     | Project Setup & Infrastructure| 1 day     | Runnable project skeleton with config & deps |
| 2     | Data Ingestion & Preprocessing| 1–2 days  | Clean, cached DataFrame ready for filtering  |
| 3     | Filtering Engine              | 1 day     | Multi-criteria filter with relaxation logic  |
| 4     | LLM Integration               | 2–3 days  | Prompt engineering + Groq API integration    |
| 5     | Streamlit UI                  | 1–2 days  | Interactive web app with recommendation cards|
| 6     | Testing, Polish & Documentation| 1–2 days | Test suite, error handling, final README     |

**Total Estimated Effort**: 7–11 days

---

## Phase 1: Project Setup & Infrastructure

> **Goal**: Establish the project skeleton, dependencies, configuration system, and development environment.

### Tasks

| #   | Task                                         | Priority | Details                                                                                       |
|-----|----------------------------------------------|----------|-----------------------------------------------------------------------------------------------|
| 1.1 | Create project directory structure           | 🔴 High  | Follow the layout defined in [architecture.md §3](file:///c:/Projects/Zomato_recommendation/docs/architecture.md#L95) |
| 1.2 | Initialize Python virtual environment        | 🔴 High  | `python -m venv venv` + activate                                                              |
| 1.3 | Create `requirements.txt`                    | 🔴 High  | Include: `streamlit`, `pandas`, `datasets`, `google-generativeai`, `python-dotenv`, `pytest`  |
| 1.4 | Install all dependencies                     | 🔴 High  | `pip install -r requirements.txt`                                                             |
| 1.5 | Create `.env.example` template               | 🔴 High  | All config variables with placeholder values (see [architecture.md §10](file:///c:/Projects/Zomato_recommendation/docs/architecture.md#L606)) |
| 1.6 | Implement `src/utils/config.py`              | 🔴 High  | `AppConfig` class — loads `.env`, validates required keys, provides defaults                  |
| 1.7 | Implement `src/utils/logger.py`              | 🟡 Med   | Configured logger with console output and optional file logging                               |
| 1.8 | Create `.gitignore`                          | 🟡 Med   | Ignore: `venv/`, `.env`, `__pycache__/`, `data/cache/`, `*.pyc`                              |
| 1.9 | Add all `__init__.py` files                  | 🔴 High  | In `src/`, `src/data/`, `src/filters/`, `src/llm/`, `src/recommendation/`, `src/utils/`      |

### Directory Structure to Create

```
Zomato_recommendation/
├── docs/                          # ✅ Already exists
├── src/
│   ├── __init__.py
│   ├── data/
│   │   └── __init__.py
│   ├── filters/
│   │   └── __init__.py
│   ├── llm/
│   │   └── __init__.py
│   ├── recommendation/
│   │   └── __init__.py
│   └── utils/
│       ├── __init__.py
│       ├── config.py              # ✅ Implement
│       └── logger.py              # ✅ Implement
├── ui/
├── tests/
├── .env.example                   # ✅ Create
├── .gitignore                     # ✅ Create
└── requirements.txt               # ✅ Create
```

### Deliverables

- [x] Project runs without import errors
- [x] `AppConfig` loads environment variables correctly
- [x] Logger outputs to console
- [x] All packages install cleanly

### Acceptance Criteria

```python
# This should work without errors:
from src.utils.config import AppConfig
from src.utils.logger import get_logger

config = AppConfig()
logger = get_logger(__name__)
logger.info(f"Model: {config.llm_model}")
```

---

## Phase 2: Data Ingestion & Preprocessing

> **Goal**: Load the Zomato dataset from Hugging Face, clean it, normalize fields, and cache locally for fast reuse.

### Tasks

| #   | Task                                          | Priority | Details                                                                                          |
|-----|-----------------------------------------------|----------|--------------------------------------------------------------------------------------------------|
| 2.1 | Implement `src/data/loader.py`                | 🔴 High  | `DatasetLoader.load()` — fetch from Hugging Face using `datasets` library                        |
| 2.2 | Implement `src/data/cache.py`                 | 🟡 Med   | Save/load DataFrame as `.parquet` in `data/cache/`; skip download if cache exists                |
| 2.3 | Explore raw dataset schema                    | 🔴 High  | Print columns, dtypes, sample rows; identify which fields map to our requirements                |
| 2.4 | Implement `src/data/preprocessor.py`          | 🔴 High  | Full preprocessing pipeline (see sub-tasks below)                                                |
| 2.5 | Write unit tests for loader & preprocessor    | 🟡 Med   | `tests/test_loader.py`, `tests/test_preprocessor.py`                                            |

### Preprocessing Sub-Tasks (Task 2.4)

| Sub-Task                     | Logic                                                                                   |
|------------------------------|-----------------------------------------------------------------------------------------|
| **Handle missing values**    | Drop rows missing `restaurant_name` or `rating`; fill optional fields with "Unknown"    |
| **Normalize ratings**        | Ensure all ratings are on a 0–5 float scale                                             |
| **Categorize budget**        | Map `average_cost_for_two` → `Low` (≤₹400) / `Medium` (₹401–1000) / `High` (>₹1000)   |
| **Clean cuisine strings**    | Strip whitespace, normalize casing (e.g., "north indian" → "North Indian")              |
| **Standardize location**     | Strip whitespace, title-case city names                                                 |
| **Select relevant columns**  | Keep only: name, location, cuisines, cost, rating, votes, online_order, book_table      |

### Deliverables

- [x] Dataset loads successfully from Hugging Face
- [x] Cached `.parquet` file is created on first load
- [x] Subsequent loads use cache (< 1 second)
- [x] Preprocessed DataFrame has consistent, clean data

### Acceptance Criteria

```python
from src.data.loader import DatasetLoader
from src.data.preprocessor import DataPreprocessor

loader = DatasetLoader(config)
df = loader.load()
print(df.shape)          # e.g., (8000+, 8)

preprocessor = DataPreprocessor(config)
clean_df = preprocessor.preprocess(df)
print(clean_df.columns)  # ['name', 'location', 'cuisines', 'cost_for_two', 'rating', 'votes', 'budget_category', ...]
print(clean_df['budget_category'].unique())  # ['Low', 'Medium', 'High']
assert clean_df['rating'].between(0, 5).all()
```

---

## Phase 3: Filtering Engine

> **Goal**: Build the multi-criteria filter that narrows restaurants based on user preferences, with smart relaxation when results are too few.

### Tasks

| #   | Task                                           | Priority | Details                                                                                     |
|-----|-------------------------------------------------|----------|---------------------------------------------------------------------------------------------|
| 3.1 | Define `UserPreferences` dataclass             | 🔴 High  | Fields: `location`, `budget`, `cuisine`, `min_rating`, `additional_prefs`                   |
| 3.2 | Implement `src/filters/filter_engine.py`       | 🔴 High  | `FilterEngine.filter()` — apply sequential AND filters                                      |
| 3.3 | Implement individual filter methods            | 🔴 High  | `_filter_by_location()`, `_filter_by_budget()`, `_filter_by_cuisine()`, `_filter_by_rating()`|
| 3.4 | Implement filter relaxation logic              | 🔴 High  | Progressive relaxation when results < 3 (see strategy below)                                |
| 3.5 | Implement result truncation                    | 🟡 Med   | If results > 50, keep top 50 by rating (LLM context window management)                     |
| 3.6 | Write unit tests for filter engine             | 🟡 Med   | `tests/test_filter_engine.py` — test each filter + relaxation + edge cases                  |

### Filter Relaxation Order

```
Step 1: Apply all filters
         │
         ▼
    Results ≥ 3?  ──YES──►  Return results
         │
         NO
         ▼
Step 2: Drop additional_prefs  →  retry
Step 3: Drop min_rating (set 0) →  retry
Step 4: Drop budget             →  retry
Step 5: Drop cuisine            →  retry
Step 6: Return whatever remains + relaxation notice
```

### Key Implementation Details

| Feature                    | Implementation                                                     |
|----------------------------|--------------------------------------------------------------------|
| **Case-insensitive match** | `.str.lower()` comparison for location and cuisine                 |
| **Partial cuisine match**  | Use `.str.contains(cuisine, case=False)` for multi-cuisine fields  |
| **Relaxation tracking**    | Return `relaxed_filters: list[str]` alongside results              |
| **Empty input handling**   | Skip filter if user leaves field blank/None                        |

### Deliverables

- [x] Filters work individually and in combination
- [x] Relaxation logic activates when needed
- [x] User is informed which filters were relaxed
- [x] Edge case: all filters empty → return top-rated restaurants

### Acceptance Criteria

```python
from src.filters.filter_engine import FilterEngine, UserPreferences

engine = FilterEngine()
prefs = UserPreferences(location="Bangalore", budget="Medium", cuisine="Italian", min_rating=4.0)
result = engine.filter(clean_df, prefs)

assert len(result.filtered_df) >= 1
assert all(result.filtered_df['rating'] >= 4.0)
print(f"Relaxed filters: {result.relaxed_filters}")
```

---

## Phase 4: LLM Integration

> **Goal**: Build the prompt engineering pipeline, integrate with Groq API (leveraging ultra-fast inference with Llama 3.3), and parse LLM responses into structured recommendation objects.

### Tasks

| #   | Task                                           | Priority | Details                                                                                        |
|-----|-------------------------------------------------|----------|------------------------------------------------------------------------------------------------|
| 4.1 | Implement `src/llm/prompt_builder.py`          | 🔴 High  | `PromptBuilder.build_recommendation_prompt()` — Role → Context → Data → Task → Format         |
| 4.2 | Design & iterate on prompt template            | 🔴 High  | Test with sample data; refine for consistent JSON output                                       |
| 4.3 | Implement `src/llm/llm_client.py`             | 🔴 High  | `LLMClient.generate()` — Groq API call with retry + timeout (`groq` SDK)                      |
| 4.4 | Implement retry logic with exponential backoff | 🟡 Med   | Max 3 retries; backoff: 1s → 2s → 4s with jitter                                              |
| 4.5 | Implement `src/llm/response_parser.py`         | 🔴 High  | `ResponseParser.parse()` — JSON parsing + validation + fallback regex parsing                  |
| 4.6 | Define `Recommendation` dataclass              | 🔴 High  | Fields: `restaurant_name`, `cuisine`, `rating`, `estimated_cost`, `explanation`                |
| 4.7 | Test prompt with real Groq API calls           | 🔴 High  | Validate output quality, JSON format consistency, explanation quality                          |
| 4.8 | Implement fallback (no LLM available)          | 🟡 Med   | Return top-N by rating with generic explanation if API fails                                   |
| 4.9 | Write tests (mock LLM responses)               | 🟡 Med   | `tests/test_prompt_builder.py`, `tests/test_response_parser.py`                                |

### Prompt Template (Final Version)

```
You are an expert food critic and restaurant recommendation assistant.
Your goal is to help users find the perfect restaurant based on their preferences.

## USER PREFERENCES
- Location: {location}
- Budget: {budget}
- Preferred Cuisine: {cuisine}
- Minimum Rating: {min_rating}/5
- Additional Preferences: {additional_prefs}

## AVAILABLE RESTAURANTS
{restaurant_table}

## YOUR TASK
From the restaurants listed above, select the top {top_n} that BEST match
the user's preferences. For each restaurant, provide:

1. restaurant_name — exact name from the list
2. cuisine — cuisine types offered
3. rating — the restaurant's rating
4. estimated_cost — approximate cost for two
5. explanation — 2-3 sentences explaining WHY this restaurant is a great
   match for the user's specific preferences

IMPORTANT:
- ONLY recommend restaurants from the provided list
- Rank from best match to least
- Consider ALL user preferences when ranking

## OUTPUT FORMAT
Respond ONLY with a valid JSON array:
[
  {
    "restaurant_name": "...",
    "cuisine": "...",
    "rating": 4.5,
    "estimated_cost": "₹800 for two",
    "explanation": "..."
  }
]
```

### LLM Client Configuration

| Parameter       | Value                      | Rationale                                                     |
|-----------------|----------------------------|----------------------------------------------------------------|
| **Provider**    | `Groq`                     | Ultra-low latency inference, high throughput, JSON mode        |
| **Model**       | `llama-3.3-70b-versatile`  | High-quality reasoning, strong instruction following, fast    |
| **Temperature** | `0.7`                      | Balanced: creative explanations, stable ranking                |
| **Max Tokens**  | `2048`                     | Sufficient for 5 detailed recommendations                      |
| **Timeout**     | `30s`                      | Prevents UI hanging                                            |
| **Retries**     | `3`                        | Handles transient API rate limits or network glitches          |

### Deliverables

- [x] Prompt produces consistent, parseable JSON from Groq
- [x] Recommendations are grounded in actual dataset restaurants
- [x] Explanations are personalized and reference user preferences
- [x] Fallback works when LLM is unavailable
- [x] Response parser handles malformed JSON gracefully

### Acceptance Criteria

```python
from src.llm.prompt_builder import PromptBuilder
from src.llm.llm_client import LLMClient
from src.llm.response_parser import ResponseParser

builder = PromptBuilder()
prompt = builder.build_recommendation_prompt(filtered_df, prefs, top_n=5)

client = LLMClient(api_key=config.groq_api_key, model=config.llm_model)
raw_response = client.generate(prompt)

parser = ResponseParser()
recommendations = parser.parse(raw_response)

assert len(recommendations) == 5
assert all(r.explanation for r in recommendations)
assert all(r.restaurant_name for r in recommendations)
```

---

## Phase 5: Streamlit UI

> **Goal**: Build an interactive, user-friendly web interface that collects preferences and displays AI-powered recommendations.

### Tasks

| #   | Task                                           | Priority | Details                                                                              |
|-----|-------------------------------------------------|----------|--------------------------------------------------------------------------------------|
| 5.1 | Create `ui/app.py` — main Streamlit app        | 🔴 High  | Page config, title, layout                                                           |
| 5.2 | Build sidebar for user preferences input       | 🔴 High  | Location dropdown, budget radio, cuisine selector, rating slider, text area for prefs|
| 5.3 | Wire up `RecommendationEngine` to UI           | 🔴 High  | On "Get Recommendations" button click → run pipeline → display results               |
| 5.4 | Design recommendation cards                    | 🔴 High  | Styled cards showing: name, cuisine, rating (stars), cost, AI explanation            |
| 5.5 | Add loading spinner                            | 🟡 Med   | Show spinner while LLM is processing                                                |
| 5.6 | Display filter relaxation notices              | 🟡 Med   | Info banner when filters were relaxed                                                |
| 5.7 | Add error state handling                       | 🟡 Med   | Friendly error messages for API failures, no results, etc.                           |
| 5.8 | Style the UI                                   | 🟡 Med   | Custom CSS for cards, colors, fonts — premium feel                                   |
| 5.9 | Add "About" section in sidebar                 | 🟢 Low   | Brief project description and dataset attribution                                    |

### UI Layout

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     🍽️ Zomato AI Restaurant Recommender                 │
├──────────────┬───────────────────────────────────────────────────────────┤
│   SIDEBAR    │                    MAIN CONTENT                          │
│              │                                                          │
│ 📍 Location  │   ┌──────────────────────────────────────────────────┐   │
│ [Dropdown ▼] │   │  ⚡ Finding your perfect restaurant...           │   │
│              │   │  [Loading Spinner]                                │   │
│ 💰 Budget    │   └──────────────────────────────────────────────────┘   │
│ ○ Low        │                                                          │
│ ● Medium     │   ┌──────────────────────────────────────────────────┐   │
│ ○ High       │   │  🏪 Truffles                          ⭐ 4.5/5  │   │
│              │   │  🍕 American, Italian     💰 ₹800 for two       │   │
│ 🍕 Cuisine   │   │                                                  │   │
│ [Dropdown ▼] │   │  🤖 "Truffles is an excellent match for your    │   │
│              │   │  medium budget and Italian preference. Known     │   │
│ ⭐ Min Rating│   │  for generous portions and a family-friendly     │   │
│ [===●===] 4.0│   │  atmosphere, it's perfect for a weekend dinner." │   │
│              │   └──────────────────────────────────────────────────┘   │
│ 📝 Other     │                                                          │
│ [Text Area]  │   ┌──────────────────────────────────────────────────┐   │
│              │   │  🏪 Pasta Street                      ⭐ 4.3/5  │   │
│ [🔍 Get      │   │  🍕 Italian                💰 ₹600 for two      │   │
│  Recommend-  │   │  ...                                             │   │
│  ations]     │   └──────────────────────────────────────────────────┘   │
│              │                                                          │
│ ── About ──  │   ┌──────────────────────────────────────────────────┐   │
│ Powered by   │   │  🏪 Little Italy                      ⭐ 4.1/5  │   │
│ Groq AI      │   │  ...                                             │   │
│              │   └──────────────────────────────────────────────────┘   │
└──────────────┴───────────────────────────────────────────────────────────┘
```

### Streamlit Components Mapping

| UI Element                | Streamlit Component                          | Source Data                         |
|---------------------------|----------------------------------------------|-------------------------------------|
| Page title & icon         | `st.set_page_config()`, `st.title()`         | Static                              |
| Location selector         | `st.sidebar.selectbox()`                     | Unique locations from dataset       |
| Budget selector           | `st.sidebar.radio()`                         | `["Low", "Medium", "High"]`        |
| Cuisine selector          | `st.sidebar.selectbox()`                     | Unique cuisines from dataset        |
| Rating slider             | `st.sidebar.slider()`                        | Range: `0.0 – 5.0`, step `0.5`     |
| Additional preferences    | `st.sidebar.text_area()`                     | Free-text input                     |
| Submit button             | `st.sidebar.button()`                        | Triggers recommendation pipeline    |
| Loading state             | `st.spinner()`                               | While LLM processes                 |
| Recommendation cards      | `st.container()` + `st.columns()` + `st.markdown()` | `list[Recommendation]`       |
| Relaxation notice         | `st.info()`                                  | `relaxed_filters` from FilterEngine |
| Error messages            | `st.error()` / `st.warning()`               | Exception handling                  |

### Deliverables

- [x] Fully functional Streamlit app at `localhost:8501`
- [x] User can input all 5 preference types
- [x] Recommendations display as styled cards
- [x] Loading, error, and empty states handled
- [x] Filter relaxation communicated to user

### Acceptance Criteria

```bash
# App launches without errors
streamlit run ui/app.py

# User can:
# 1. Select preferences in sidebar
# 2. Click "Get Recommendations"
# 3. See loading spinner
# 4. View 5 recommendation cards with AI explanations
# 5. See relaxation notice if filters were loosened
```

---

## Phase 6: Testing, Polish & Documentation

> **Goal**: Ensure reliability, handle edge cases, write comprehensive tests, and finalize documentation.

### Tasks

| #   | Task                                            | Priority | Details                                                                   |
|-----|-------------------------------------------------|----------|---------------------------------------------------------------------------|
| 6.1 | Write unit tests for all modules               | 🔴 High  | Target: ≥80% code coverage on core modules                               |
| 6.2 | Write integration test (full pipeline)         | 🔴 High  | Mock LLM; test filter → prompt → parse end-to-end                        |
| 6.3 | Test edge cases                                 | 🔴 High  | See edge case checklist below                                             |
| 6.4 | Add input validation in UI                     | 🟡 Med   | Prevent submission with completely empty preferences                      |
| 6.5 | Polish UI styling                              | 🟡 Med   | Custom CSS, consistent spacing, responsive layout                         |
| 6.6 | Write `README.md`                              | 🔴 High  | Setup instructions, usage guide, screenshots, architecture overview       |
| 6.7 | Review & clean up code                         | 🟡 Med   | Remove debug prints, add docstrings, type hints                           |
| 6.8 | Add request logging                            | 🟢 Low   | Log user preferences + LLM responses for debugging                       |
| 6.9 | Performance check                              | 🟢 Low   | Ensure end-to-end response < 10 seconds (excluding LLM latency)          |

### Edge Case Checklist

| #  | Edge Case                                      | Expected Behavior                                         | Test? |
|----|------------------------------------------------|-----------------------------------------------------------|-------|
| E1 | All preference fields are empty                | Return top 5 highest-rated restaurants globally            | ✅    |
| E2 | Location doesn't exist in dataset              | Show "No restaurants found in {location}" + relax          | ✅    |
| E3 | Cuisine not in dataset                         | Relax cuisine filter; inform user                          | ✅    |
| E4 | Min rating = 5.0 (no perfect matches)          | Relax rating; show closest matches                         | ✅    |
| E5 | Dataset has duplicate restaurants               | Deduplicate during preprocessing                           | ✅    |
| E6 | LLM returns non-JSON response                  | Fallback regex parser; if fails, return top-rated          | ✅    |
| E7 | LLM hallucinates a restaurant not in dataset   | Response parser validates names against dataset            | ✅    |
| E8 | Groq API key is missing/invalid                | Clear error message on app startup                         | ✅    |
| E9 | Network failure during dataset download        | Use local cache; error if no cache                         | ✅    |
| E10| Very long additional_prefs text                | Truncate to 500 chars before including in prompt           | ✅    |

### Test File Mapping

| Test File                   | Tests                                                          |
|-----------------------------|----------------------------------------------------------------|
| `tests/test_loader.py`      | Dataset download, caching, schema validation                  |
| `tests/test_preprocessor.py`| Missing values, budget categorization, rating normalization    |
| `tests/test_filter_engine.py`| Each filter, combined filters, relaxation, empty input       |
| `tests/test_prompt_builder.py`| Prompt structure, preference injection, truncation          |
| `tests/test_response_parser.py`| Valid JSON, malformed JSON, fallback parsing, hallucination check |
| `tests/test_engine.py`      | Full pipeline (mocked LLM), error scenarios                   |

### README.md Outline

```markdown
# 🍽️ Zomato AI Restaurant Recommender

## Overview
## Features
## Tech Stack
## Quick Start
  ### Prerequisites
  ### Installation
  ### Configuration
  ### Running the App
## Usage Guide (with screenshots)
## Project Structure
## Architecture
## Testing
## Contributing
## License
```

### Deliverables

- [x] All tests pass (`pytest` green)
- [x] Edge cases handled gracefully
- [x] `README.md` with setup instructions
- [x] Clean, documented codebase

---

## 📅 Implementation Timeline

```
Week 1
├── Day 1:  Phase 1 — Project Setup & Infrastructure
├── Day 2:  Phase 2 — Data Ingestion & Preprocessing
├── Day 3:  Phase 2 (continued) — Preprocessing + Tests
├── Day 4:  Phase 3 — Filtering Engine
└── Day 5:  Phase 4 — LLM Integration (Prompt Builder + Client)

Week 2
├── Day 6:  Phase 4 (continued) — Response Parser + Testing with Groq
├── Day 7:  Phase 4 (continued) — Fallback handling + Orchestrator (engine.py)
├── Day 8:  Phase 5 — Streamlit UI
├── Day 9:  Phase 5 (continued) — UI Polish + Wiring
├── Day 10: Phase 6 — Testing & Edge Cases
└── Day 11: Phase 6 (continued) — Documentation & Final Polish
```

### Milestone Checkpoints

| Milestone | After Phase | Verification                                                     |
|-----------|-------------|------------------------------------------------------------------|
| **M1**    | Phase 2     | `python -c "from src.data.loader import DatasetLoader"` → works  |
| **M2**    | Phase 3     | Filter returns correct results for sample preferences             |
| **M3**    | Phase 4     | LLM returns valid JSON recommendations from real API call         |
| **M4**    | Phase 5     | `streamlit run ui/app.py` → full working demo                     |
| **M5**    | Phase 6     | `pytest` → all green, README complete                             |

---

## ⚠️ Risks & Mitigations

| Risk                                        | Impact  | Mitigation                                                            |
|---------------------------------------------|---------|-----------------------------------------------------------------------|
| Groq API rate limits during development     | Medium  | Cache LLM responses during testing; use mocks for unit tests          |
| Dataset schema changes on Hugging Face      | Low     | Pin dataset version; add schema validation in loader                  |
| LLM output inconsistency (format varies)    | High    | Robust parser with JSON + regex fallback; few-shot examples in prompt |
| Streamlit performance with large dataset    | Medium  | Cache preprocessed data using `@st.cache_data`                        |
| API key exposure in source control          | High    | `.gitignore` includes `.env`; use `.env.example` for template         |

---

## 📎 References

- **Problem Statement**: [`problemStatement.md`](file:///c:/Projects/Zomato_recommendation/docs/problemStatement.md)
- **Architecture**: [`architecture.md`](file:///c:/Projects/Zomato_recommendation/docs/architecture.md)
- **Dataset**: [Hugging Face — ManikaSaini/zomato-restaurant-recommendation](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation)
- **Groq API**: [Groq Cloud Documentation](https://console.groq.com/docs)
- **Streamlit**: [docs.streamlit.io](https://docs.streamlit.io)
