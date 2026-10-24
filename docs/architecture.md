# 🏗️ Architecture Document

## AI-Powered Restaurant Recommendation System (Zomato Use Case)

---

## 📖 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Technology Stack](#technology-stack)
3. [Project Structure](#project-structure)
4. [Component Design](#component-design)
5. [Data Flow](#data-flow)
6. [Module Specifications](#module-specifications)
7. [API Design](#api-design)
8. [Prompt Engineering Strategy](#prompt-engineering-strategy)
9. [Error Handling & Edge Cases](#error-handling--edge-cases)
10. [Configuration Management](#configuration-management)
11. [Testing Strategy](#testing-strategy)
12. [Deployment Architecture](#deployment-architecture)
13. [Future Enhancements](#future-enhancements)

---

## 1. Architecture Overview

The system follows a **layered architecture** with clear separation of concerns across five layers:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PRESENTATION LAYER                                │
│                  Streamlit Web UI / CLI Interface                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                          APPLICATION LAYER                                 │
│            Orchestrator (coordinates all components)                       │
├──────────────────┬──────────────────────┬───────────────────────────────────┤
│   DATA LAYER     │  INTEGRATION LAYER   │       LLM LAYER                  │
│                  │                      │                                   │
│  • Dataset       │  • Filter Engine     │  • Prompt Builder                │
│    Loader        │  • Data Transformer  │  • LLM Client                   │
│  • Preprocessor  │  • Result Formatter  │  • Response Parser              │
│  • Cache Manager │                      │  • Recommendation Ranker        │
├──────────────────┴──────────────────────┴───────────────────────────────────┤
│                        INFRASTRUCTURE LAYER                                │
│              Config │ Logging │ Error Handling │ Caching                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Design Principles

| Principle                  | Description                                                                 |
|----------------------------|-----------------------------------------------------------------------------|
| **Separation of Concerns** | Each module handles one responsibility                                      |
| **Loose Coupling**         | Components interact through well-defined interfaces                         |
| **Extensibility**          | Easy to swap LLM providers, datasets, or UI frameworks                      |
| **Fail Gracefully**        | Meaningful fallbacks when LLM is unavailable or no results match            |
| **Reproducibility**        | Deterministic filtering; LLM calls logged for debugging                     |

---

## 2. Technology Stack

### Core Technologies

| Layer              | Technology             | Purpose                                      |
|--------------------|------------------------|----------------------------------------------|
| **Language**       | Python 3.10+           | Primary development language                 |
| **UI Framework**   | Streamlit              | Rapid prototyping of interactive web UI      |
| **Data Handling**  | Pandas                 | Dataset loading, filtering, transformation   |
| **Dataset Source** | Hugging Face `datasets`| Load Zomato dataset programmatically         |
| **LLM Provider**   | Google Gemini API      | LLM for ranking and generating explanations  |
| **HTTP Client**    | `requests` / `httpx`   | API communication with LLM provider          |
| **Config**         | `python-dotenv`        | Environment variable management              |
| **Testing**        | `pytest`               | Unit and integration testing                 |

### Python Dependencies

```txt
streamlit>=1.30.0
pandas>=2.0.0
datasets>=2.16.0          # Hugging Face datasets library
google-generativeai>=0.4.0 # Google Gemini SDK
python-dotenv>=1.0.0
pytest>=7.4.0
```

---

## 3. Project Structure

```
Zomato_recommendation/
│
├── docs/
│   ├── problemStatement.txt        # Original problem statement
│   ├── problemStatement.md         # Formatted problem statement
│   └── architecture.md             # This document
│
├── src/
│   ├── __init__.py
│   │
│   ├── data/
│   │   ├── __init__.py
│   │   ├── loader.py               # Dataset loading from Hugging Face
│   │   ├── preprocessor.py         # Data cleaning & normalization
│   │   └── cache.py                # Local caching of dataset
│   │
│   ├── filters/
│   │   ├── __init__.py
│   │   └── filter_engine.py        # Multi-criteria filtering logic
│   │
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── prompt_builder.py       # Prompt template construction
│   │   ├── llm_client.py           # LLM API client (Gemini / OpenAI)
│   │   └── response_parser.py      # Parse & validate LLM output
│   │
│   ├── recommendation/
│   │   ├── __init__.py
│   │   └── engine.py               # Orchestrates filter → LLM → output
│   │
│   └── utils/
│       ├── __init__.py
│       ├── config.py               # Configuration management
│       └── logger.py               # Logging setup
│
├── ui/
│   └── app.py                      # Streamlit application entry point
│
├── tests/
│   ├── test_loader.py
│   ├── test_preprocessor.py
│   ├── test_filter_engine.py
│   ├── test_prompt_builder.py
│   └── test_engine.py
│
├── .env.example                    # Template for API keys
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 4. Component Design

### 4.1 Data Layer

#### `loader.py` — Dataset Loader

**Responsibility**: Load the Zomato dataset from Hugging Face and return a clean DataFrame.

```python
# Interface
class DatasetLoader:
    def load(self) -> pd.DataFrame:
        """Load dataset from Hugging Face or local cache."""
        ...

    def _fetch_from_huggingface(self) -> pd.DataFrame:
        """Download dataset using datasets library."""
        ...

    def _load_from_cache(self) -> pd.DataFrame | None:
        """Load previously cached dataset."""
        ...
```

**Key Decisions**:
- Cache the dataset locally after first download (as `.parquet`) to avoid repeated network calls
- Return a standardized DataFrame with consistent column names regardless of raw dataset schema

#### `preprocessor.py` — Data Preprocessor

**Responsibility**: Clean, normalize, and enrich the raw dataset.

```python
class DataPreprocessor:
    def preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        """Full preprocessing pipeline."""
        ...

    def _normalize_ratings(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize ratings to 0-5 scale."""
        ...

    def _categorize_budget(self, df: pd.DataFrame) -> pd.DataFrame:
        """Map cost values to Low/Medium/High buckets."""
        ...

    def _clean_cuisines(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize cuisine labels."""
        ...

    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fill or drop rows with critical missing data."""
        ...
```

**Budget Categorization Logic**:

| Category   | Cost Range (₹, for two) | Rationale                       |
|------------|-------------------------|---------------------------------|
| **Low**    | 0 – 400                 | Street food, casual eateries    |
| **Medium** | 401 – 1000              | Mid-range dining                |
| **High**   | 1001+                   | Fine dining, premium            |

> [!NOTE]
> Budget thresholds are configurable via `config.py` to support different cities/regions.

---

### 4.2 Filter Layer

#### `filter_engine.py` — Multi-Criteria Filter

**Responsibility**: Apply user preferences as filters on the preprocessed dataset.

```python
@dataclass
class UserPreferences:
    location: str | None = None
    budget: str | None = None             # "Low", "Medium", "High"
    cuisine: str | None = None
    min_rating: float = 0.0
    additional_prefs: str | None = None   # Free-text for LLM context

class FilterEngine:
    def filter(self, df: pd.DataFrame, prefs: UserPreferences) -> pd.DataFrame:
        """Apply all active filters and return matching restaurants."""
        ...

    def _filter_by_location(self, df, location) -> pd.DataFrame: ...
    def _filter_by_budget(self, df, budget) -> pd.DataFrame: ...
    def _filter_by_cuisine(self, df, cuisine) -> pd.DataFrame: ...
    def _filter_by_rating(self, df, min_rating) -> pd.DataFrame: ...
```

**Filtering Strategy**:
- Filters are applied **sequentially** (AND logic)
- Each filter is **optional** — skipped if the user doesn't provide it
- **Case-insensitive** matching for location and cuisine
- **Partial match** for cuisine (e.g., "Italian" matches "North Indian, Italian, Chinese")
- If filters return **< 3 results**, progressively relax constraints (drop budget → drop cuisine)

---

### 4.3 LLM Layer

#### `prompt_builder.py` — Prompt Construction

**Responsibility**: Build structured prompts from filtered data + user preferences.

```python
class PromptBuilder:
    def build_recommendation_prompt(
        self,
        restaurants: pd.DataFrame,
        preferences: UserPreferences,
        top_n: int = 5
    ) -> str:
        """Construct the LLM prompt with restaurant data and user context."""
        ...
```

**Prompt Template** (see [Section 8](#prompt-engineering-strategy) for full details):

```
You are an expert restaurant recommendation assistant.

USER PREFERENCES:
- Location: {location}
- Budget: {budget}
- Cuisine: {cuisine}
- Minimum Rating: {min_rating}
- Additional Preferences: {additional_prefs}

AVAILABLE RESTAURANTS:
{formatted_restaurant_table}

TASK:
Rank the top {top_n} restaurants that best match the user's preferences.
For each recommendation, provide:
1. Restaurant Name
2. Why it's a great match (2-3 sentences)
3. Rating and estimated cost

Return your response as a JSON array.
```

#### `llm_client.py` — LLM API Client

**Responsibility**: Handle API communication with the LLM provider.

```python
class LLMClient:
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        ...

    def generate(self, prompt: str, temperature: float = 0.7) -> str:
        """Send prompt to LLM and return raw response text."""
        ...

    def _handle_rate_limit(self, response) -> None:
        """Implement exponential backoff for rate limits."""
        ...
```

**Key Decisions**:
- Default model: `gemini-2.0-flash` (fast, cost-effective)
- Temperature: `0.7` (balanced creativity for explanations)
- Max retries: `3` with exponential backoff
- Timeout: `30s` per request

#### `response_parser.py` — Response Parser

**Responsibility**: Parse LLM output into structured recommendation objects.

```python
@dataclass
class Recommendation:
    restaurant_name: str
    cuisine: str
    rating: float
    estimated_cost: str
    explanation: str

class ResponseParser:
    def parse(self, raw_response: str) -> list[Recommendation]:
        """Parse LLM JSON response into Recommendation objects."""
        ...

    def _validate(self, data: list[dict]) -> list[Recommendation]:
        """Validate and sanitize parsed data."""
        ...

    def _fallback_parse(self, raw_response: str) -> list[Recommendation]:
        """Attempt regex-based parsing if JSON parsing fails."""
        ...
```

---

### 4.4 Recommendation Engine (Orchestrator)

#### `engine.py` — Central Orchestrator

**Responsibility**: Coordinate the full pipeline from user input to final recommendations.

```python
class RecommendationEngine:
    def __init__(
        self,
        loader: DatasetLoader,
        preprocessor: DataPreprocessor,
        filter_engine: FilterEngine,
        prompt_builder: PromptBuilder,
        llm_client: LLMClient,
        response_parser: ResponseParser
    ):
        ...

    def recommend(self, preferences: UserPreferences) -> list[Recommendation]:
        """
        Full pipeline:
        1. Load & preprocess data (cached)
        2. Filter by user preferences
        3. Build LLM prompt
        4. Call LLM
        5. Parse response
        6. Return recommendations
        """
        ...
```

**Orchestration Flow**:

```
recommend(preferences)
    │
    ├─► loader.load()                    # Step 1: Get dataset
    ├─► preprocessor.preprocess(df)      # Step 2: Clean data
    ├─► filter_engine.filter(df, prefs)  # Step 3: Apply filters
    │       │
    │       ├─ If results == 0 → relax filters & retry
    │       └─ If results > 50 → truncate to top 50 by rating
    │
    ├─► prompt_builder.build(filtered, prefs)  # Step 4: Build prompt
    ├─► llm_client.generate(prompt)            # Step 5: Call LLM
    └─► response_parser.parse(response)        # Step 6: Parse output
```

---

## 5. Data Flow

### End-to-End Sequence Diagram

```
   User            Streamlit UI        Engine         FilterEngine       LLM Client        Gemini API
    │                   │                 │                │                  │                  │
    │  Enter prefs      │                 │                │                  │                  │
    │──────────────────►│                 │                │                  │                  │
    │                   │  recommend()    │                │                  │                  │
    │                   │────────────────►│                │                  │                  │
    │                   │                 │  load + preprocess               │                  │
    │                   │                 │──────┐         │                  │                  │
    │                   │                 │◄─────┘         │                  │                  │
    │                   │                 │                │                  │                  │
    │                   │                 │  filter(prefs) │                  │                  │
    │                   │                 │───────────────►│                  │                  │
    │                   │                 │  filtered_df   │                  │                  │
    │                   │                 │◄───────────────│                  │                  │
    │                   │                 │                                   │                  │
    │                   │                 │  build_prompt + generate()        │                  │
    │                   │                 │─────────────────────────────────►│                  │
    │                   │                 │                                   │  API call        │
    │                   │                 │                                   │─────────────────►│
    │                   │                 │                                   │  LLM response    │
    │                   │                 │                                   │◄─────────────────│
    │                   │                 │  parsed recommendations           │                  │
    │                   │                 │◄─────────────────────────────────│                  │
    │                   │  results        │                                                      │
    │                   │◄────────────────│                                                      │
    │  Display cards    │                                                                        │
    │◄──────────────────│                                                                        │
```

---

## 6. Module Specifications

### Module Dependency Graph

```
                        ┌──────────┐
                        │  app.py  │  (Streamlit UI)
                        └────┬─────┘
                             │
                        ┌────▼─────┐
                        │ engine.py│  (Orchestrator)
                        └────┬─────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
        ┌─────▼─────┐ ┌─────▼──────┐ ┌─────▼──────────┐
        │  loader.py │ │ filter_    │ │ prompt_builder  │
        │preprocessor│ │ engine.py  │ │ llm_client      │
        │  cache.py  │ │            │ │ response_parser │
        └────────────┘ └────────────┘ └────────────────┘
              │                              │
              │                              │
        ┌─────▼─────┐                 ┌──────▼──────┐
        │  Hugging   │                │  Gemini API │
        │  Face Hub  │                │  (External) │
        └────────────┘                └─────────────┘
```

### Module Responsibilities Summary

| Module                | Input                          | Output                        | Dependencies        |
|-----------------------|--------------------------------|-------------------------------|----------------------|
| `loader.py`           | Dataset name / cache path      | Raw `pd.DataFrame`            | `datasets`, `pandas` |
| `preprocessor.py`     | Raw DataFrame                  | Cleaned DataFrame             | `pandas`             |
| `cache.py`            | DataFrame / cache path         | Cached file (`.parquet`)      | `pandas`, `pathlib`  |
| `filter_engine.py`    | DataFrame + UserPreferences    | Filtered DataFrame            | `pandas`             |
| `prompt_builder.py`   | Filtered DataFrame + prefs     | Prompt string                 | —                    |
| `llm_client.py`       | Prompt string                  | Raw LLM response string       | `google-generativeai`|
| `response_parser.py`  | Raw LLM response               | `list[Recommendation]`        | `json`, `re`         |
| `engine.py`           | UserPreferences                | `list[Recommendation]`        | All above modules    |
| `app.py`              | User interaction               | Rendered UI                   | `streamlit`, `engine`|

---

## 7. API Design

### Internal API — `RecommendationEngine`

```python
# Primary interface
engine = RecommendationEngine.from_config(config)
results: list[Recommendation] = engine.recommend(
    UserPreferences(
        location="Bangalore",
        budget="Medium",
        cuisine="Italian",
        min_rating=4.0,
        additional_prefs="family-friendly, outdoor seating"
    )
)
```

### Data Models

```python
@dataclass
class UserPreferences:
    location: str | None = None
    budget: str | None = None          # "Low" | "Medium" | "High"
    cuisine: str | None = None
    min_rating: float = 0.0
    additional_prefs: str | None = None

@dataclass
class Recommendation:
    restaurant_name: str
    cuisine: str
    rating: float
    estimated_cost: str
    explanation: str                    # LLM-generated reasoning

@dataclass
class RecommendationResult:
    recommendations: list[Recommendation]
    total_matches: int                  # Pre-LLM filter count
    filters_applied: dict               # Which filters were active
    filters_relaxed: list[str]          # Filters dropped due to no results
```

---

## 8. Prompt Engineering Strategy

### Prompt Structure

The prompt follows a **Role → Context → Data → Task → Format** pattern:

```
┌────────────────────────────────────────────┐
│  SYSTEM ROLE                               │
│  "You are an expert food critic and        │
│   restaurant recommendation assistant."    │
├────────────────────────────────────────────┤
│  USER CONTEXT                              │
│  Location, budget, cuisine, rating,        │
│  additional preferences                    │
├────────────────────────────────────────────┤
│  RESTAURANT DATA                           │
│  Filtered restaurants as structured table   │
├────────────────────────────────────────────┤
│  TASK INSTRUCTIONS                         │
│  Rank top N, explain reasoning,            │
│  consider all preferences                  │
├────────────────────────────────────────────┤
│  OUTPUT FORMAT                             │
│  JSON array schema with examples           │
└────────────────────────────────────────────┘
```

### Prompt Best Practices

| Practice                    | Implementation                                                  |
|-----------------------------|-----------------------------------------------------------------|
| **Grounding**               | Always include real restaurant data — never let the LLM hallucinate restaurants |
| **Structured Output**       | Request JSON response for reliable parsing                      |
| **Few-Shot Examples**       | Include 1 example recommendation in the prompt                  |
| **Constraint Enforcement**  | Explicitly state "Only recommend from the provided list"        |
| **Reasoning**               | Ask the LLM to explain *why* each restaurant matches            |

### Expected JSON Output Schema

```json
[
  {
    "restaurant_name": "Truffles",
    "cuisine": "American, Italian",
    "rating": 4.5,
    "estimated_cost": "₹800 for two",
    "explanation": "Truffles is a perfect match for your medium budget and Italian cuisine preference. With a 4.5 rating and family-friendly atmosphere, it's ideal for a relaxed dinner."
  }
]
```

---

## 9. Error Handling & Edge Cases

### Error Handling Strategy

| Scenario                          | Handling                                                              |
|-----------------------------------|-----------------------------------------------------------------------|
| **No restaurants match filters**  | Progressively relax filters; show message explaining relaxation       |
| **LLM API failure / timeout**     | Retry with exponential backoff (3 attempts); fallback to top-rated    |
| **LLM returns invalid JSON**      | Attempt regex-based fallback parsing; log error                       |
| **Dataset unavailable**           | Use local cache; show error if no cache exists                        |
| **Rate limiting**                 | Exponential backoff with jitter; queue requests                       |
| **Empty user input**              | Show top-rated restaurants across all categories as default           |

### Filter Relaxation Strategy

When filters return too few results (< 3), relax in this order:

```
1. Drop "additional_prefs"  →  retry
2. Drop "min_rating"        →  retry (set to 0)
3. Drop "budget"            →  retry
4. Drop "cuisine"           →  retry
5. If still < 3 results     →  return whatever is available + message
```

> [!IMPORTANT]
> Always inform the user which filters were relaxed so they understand why results may differ from their original query.

---

## 10. Configuration Management

### Environment Variables (`.env`)

```env
# LLM Configuration
GEMINI_API_KEY=your_api_key_here
LLM_MODEL=gemini-2.0-flash
LLM_TEMPERATURE=0.7
LLM_MAX_RETRIES=3
LLM_TIMEOUT_SECONDS=30

# Dataset Configuration
DATASET_NAME=ManikaSaini/zomato-restaurant-recommendation
CACHE_DIR=./data/cache
CACHE_ENABLED=true

# Budget Thresholds (₹, for two)
BUDGET_LOW_MAX=400
BUDGET_MEDIUM_MAX=1000

# Application
TOP_N_RECOMMENDATIONS=5
MAX_RESTAURANTS_TO_LLM=50
LOG_LEVEL=INFO
```

### `config.py` — Centralized Config

```python
class AppConfig:
    """Loads and validates all configuration from .env"""

    gemini_api_key: str
    llm_model: str = "gemini-2.0-flash"
    llm_temperature: float = 0.7
    dataset_name: str = "ManikaSaini/zomato-restaurant-recommendation"
    cache_dir: Path = Path("./data/cache")
    budget_low_max: int = 400
    budget_medium_max: int = 1000
    top_n: int = 5
```

---

## 11. Testing Strategy

### Test Coverage Plan

| Test Type         | Scope                                     | Tool     |
|-------------------|-------------------------------------------|----------|
| **Unit Tests**    | Individual functions in each module       | `pytest` |
| **Integration**   | Filter → Prompt → (Mock) LLM → Parse     | `pytest` |
| **E2E**           | Full pipeline with mocked LLM responses   | `pytest` |

### Key Test Cases

```python
# test_filter_engine.py
def test_filter_by_location_case_insensitive(): ...
def test_filter_by_cuisine_partial_match(): ...
def test_filter_returns_empty_triggers_relaxation(): ...
def test_all_filters_combined(): ...

# test_prompt_builder.py
def test_prompt_includes_all_preferences(): ...
def test_prompt_truncates_large_datasets(): ...
def test_prompt_handles_missing_preferences(): ...

# test_response_parser.py
def test_parse_valid_json_response(): ...
def test_fallback_parse_on_malformed_json(): ...
def test_parse_handles_missing_fields(): ...

# test_engine.py
def test_full_pipeline_returns_recommendations(): ...
def test_pipeline_with_no_matching_restaurants(): ...
def test_pipeline_with_llm_failure_uses_fallback(): ...
```

---

## 12. Deployment Architecture

### Local Development

```
┌──────────────────────────────────────┐
│         Developer Machine            │
│                                      │
│   ┌──────────┐     ┌─────────────┐  │
│   │ Streamlit │────►│ Python App  │  │           ┌──────────────┐
│   │ (localhost│     │ (Engine)    │──────────────►│  Gemini API  │
│   │  :8501)   │     │             │  │           │  (External)  │
│   └──────────┘     └──────┬──────┘  │           └──────────────┘
│                           │         │
│                    ┌──────▼──────┐   │
│                    │ Local Cache │   │
│                    │ (.parquet)  │   │
│                    └─────────────┘   │
└──────────────────────────────────────┘
```

### Running the Application

```bash
# 1. Clone & setup
git clone <repo-url>
cd Zomato_recommendation

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your GEMINI_API_KEY

# 5. Launch
streamlit run ui/app.py
```

---

## 13. Future Enhancements

| Enhancement                     | Description                                                      | Priority |
|---------------------------------|------------------------------------------------------------------|----------|
| **Conversational Follow-ups**   | Allow users to refine results ("show me cheaper options")        | High     |
| **User History / Profiles**     | Remember past preferences for personalized defaults              | Medium   |
| **Embedding-Based Search**      | Use vector embeddings for semantic similarity matching            | Medium   |
| **Multi-LLM Support**           | Plug in OpenAI, Anthropic, or local models via adapter pattern   | Low      |
| **Review Summarization**        | Summarize user reviews as additional context for LLM             | Medium   |
| **Map Integration**             | Show restaurant locations on an interactive map                  | Low      |
| **A/B Testing Framework**       | Compare prompt strategies and LLM models                         | Low      |

---

## 📎 References

- **Problem Statement**: [`problemStatement.md`](file:///c:/Projects/Zomato_recommendation/docs/problemStatement.md)
- **Dataset**: [Hugging Face — ManikaSaini/zomato-restaurant-recommendation](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation)
- **Gemini API Docs**: [Google AI for Developers](https://ai.google.dev/docs)
- **Streamlit Docs**: [docs.streamlit.io](https://docs.streamlit.io)
