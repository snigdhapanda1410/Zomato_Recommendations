# 📊 Evaluation Plan

## AI-Powered Restaurant Recommendation System (Zomato Use Case)

---

## 📖 Table of Contents

1. [Evaluation Overview](#1-evaluation-overview)
2. [Evaluation Dimensions](#2-evaluation-dimensions)
3. [Functional Evaluation](#3-functional-evaluation)
4. [LLM Output Quality Evaluation](#4-llm-output-quality-evaluation)
5. [Recommendation Relevance Evaluation](#5-recommendation-relevance-evaluation)
6. [Performance Evaluation](#6-performance-evaluation)
7. [User Experience Evaluation](#7-user-experience-evaluation)
8. [Robustness & Error Handling Evaluation](#8-robustness--error-handling-evaluation)
9. [Code Quality Evaluation](#9-code-quality-evaluation)
10. [Phase-Wise Evaluation Criteria](#10-phase-wise-evaluation-criteria)
11. [Evaluation Rubric & Scoring](#11-evaluation-rubric--scoring)
12. [Evaluation Execution Checklist](#12-evaluation-execution-checklist)

---

## 1. Evaluation Overview

### Purpose

This document defines **how to evaluate** the Zomato AI Restaurant Recommendation System across multiple quality dimensions — from functional correctness to LLM output quality, performance, and user experience.

### Evaluation Approach

```
┌─────────────────────────────────────────────────────────┐
│                    EVALUATION LAYERS                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│   Layer 1: Functional Correctness                        │
│   ├── Does each module work as specified?                │
│   └── Do components integrate correctly?                 │
│                                                          │
│   Layer 2: LLM Output Quality                            │
│   ├── Are responses well-structured?                     │
│   ├── Are explanations coherent & helpful?               │
│   └── Is output grounded in real data?                   │
│                                                          │
│   Layer 3: Recommendation Relevance                      │
│   ├── Do results match user preferences?                 │
│   ├── Is ranking order reasonable?                       │
│   └── Are edge cases handled gracefully?                 │
│                                                          │
│   Layer 4: Performance                                   │
│   ├── Response latency                                   │
│   ├── Resource usage                                     │
│   └── Caching effectiveness                              │
│                                                          │
│   Layer 5: User Experience                               │
│   ├── UI clarity and usability                           │
│   ├── Error messaging                                    │
│   └── Overall satisfaction                               │
│                                                          │
│   Layer 6: Code Quality                                  │
│   ├── Test coverage                                      │
│   ├── Documentation                                      │
│   └── Maintainability                                    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Evaluation Dimensions

| Dimension                    | Weight | What It Measures                                              | Evaluated By        |
|------------------------------|--------|---------------------------------------------------------------|---------------------|
| **Functional Correctness**   | 25%    | Modules work as designed; integration is seamless             | Automated tests     |
| **LLM Output Quality**      | 25%    | Structured, coherent, grounded, and helpful LLM responses     | Manual review + automated checks |
| **Recommendation Relevance** | 20%    | Results match user intent; ranking is sensible                | Test scenarios      |
| **Performance**              | 10%    | Speed, resource efficiency, caching                           | Benchmarks          |
| **User Experience**          | 10%    | UI polish, error handling, information clarity                | Manual review       |
| **Code Quality**             | 10%    | Test coverage, documentation, structure, maintainability      | Code review         |

---

## 3. Functional Evaluation

### 3.1 Module-Level Tests

Each module is evaluated against its contract defined in [architecture.md](file:///c:/Projects/Zomato_recommendation/docs/architecture.md).

#### Data Loader (`src/data/loader.py`)

| Test ID | Test Description                                   | Pass Criteria                                              |
|---------|----------------------------------------------------|------------------------------------------------------------|
| F-DL-01 | Load dataset from Hugging Face                     | Returns `pd.DataFrame` with > 0 rows                      |
| F-DL-02 | Cache dataset after first download                 | `.parquet` file exists in `data/cache/`                    |
| F-DL-03 | Load from cache on subsequent calls                | No network call; load time < 1 second                      |
| F-DL-04 | Handle Hugging Face unavailability                 | Falls back to cache; raises error if no cache              |
| F-DL-05 | Validate dataset schema                            | Expected columns are present; error on schema mismatch     |

#### Data Preprocessor (`src/data/preprocessor.py`)

| Test ID | Test Description                                   | Pass Criteria                                              |
|---------|----------------------------------------------------|------------------------------------------------------------|
| F-PP-01 | Normalize ratings to 0–5 float scale               | All ratings ∈ [0.0, 5.0]; non-numeric values handled      |
| F-PP-02 | Categorize budget (Low/Medium/High)                | Cost mapped correctly per thresholds (0–400/401–1000/1001+)|
| F-PP-03 | Clean cuisine strings                              | Consistent title-case; whitespace stripped                  |
| F-PP-04 | Handle missing values                              | No null `restaurant_name` or `rating` in output            |
| F-PP-05 | Remove duplicates                                  | No duplicate `(name, location)` pairs                      |
| F-PP-06 | Handle non-numeric cost values                     | Numeric extracted from strings like "₹500"                 |

#### Filter Engine (`src/filters/filter_engine.py`)

| Test ID | Test Description                                   | Pass Criteria                                              |
|---------|----------------------------------------------------|------------------------------------------------------------|
| F-FE-01 | Filter by location (case-insensitive)              | Returns restaurants matching location; ignoring case       |
| F-FE-02 | Filter by budget category                          | Returns only restaurants in selected budget tier            |
| F-FE-03 | Filter by cuisine (partial match)                  | "Italian" matches "North Indian, Italian, Chinese"         |
| F-FE-04 | Filter by minimum rating                           | All returned restaurants have rating ≥ min_rating          |
| F-FE-05 | Combined filters (AND logic)                       | Results satisfy ALL active filters simultaneously          |
| F-FE-06 | Skip filter when preference is None/empty          | Other filters still applied correctly                      |
| F-FE-07 | Progressive relaxation triggers when results < 3   | Filters dropped in correct order; results increase         |
| F-FE-08 | Relaxation tracking                                | `relaxed_filters` list accurately reports dropped filters  |
| F-FE-09 | Truncation to top 50 when results > 50             | Only top 50 by rating passed to LLM                        |

#### Prompt Builder (`src/llm/prompt_builder.py`)

| Test ID | Test Description                                   | Pass Criteria                                              |
|---------|----------------------------------------------------|------------------------------------------------------------|
| F-PB-01 | Prompt includes all user preferences               | Each non-null preference appears in the prompt text        |
| F-PB-02 | Prompt includes restaurant data table              | Filtered restaurants formatted as readable table           |
| F-PB-03 | Prompt requests JSON output format                 | Output format specification present in prompt              |
| F-PB-04 | Prompt handles missing preferences gracefully      | "Not specified" for null fields; no empty placeholders     |
| F-PB-05 | Prompt truncates long additional_prefs             | Prefs > 500 chars are truncated with indicator             |

#### LLM Client (`src/llm/llm_client.py`)

| Test ID | Test Description                                   | Pass Criteria                                              |
|---------|----------------------------------------------------|------------------------------------------------------------|
| F-LC-01 | Successful API call returns response               | Non-empty string returned                                  |
| F-LC-02 | Retry on transient errors (500, 503)               | Retries up to 3 times with exponential backoff             |
| F-LC-03 | Handle rate limiting (429)                         | Backoff applied; eventual success or graceful failure      |
| F-LC-04 | Timeout after 30 seconds                           | `TimeoutError` raised; not hung indefinitely               |
| F-LC-05 | Handle invalid API key                             | Clear `AuthenticationError` message                        |

#### Response Parser (`src/llm/response_parser.py`)

| Test ID | Test Description                                   | Pass Criteria                                              |
|---------|----------------------------------------------------|------------------------------------------------------------|
| F-RP-01 | Parse valid JSON array                             | Returns `list[Recommendation]` with correct fields         |
| F-RP-02 | Handle JSON wrapped in markdown code fences        | Strips ` ```json ... ``` ` and parses successfully         |
| F-RP-03 | Handle JSON with trailing commas                   | Cleans and parses successfully                             |
| F-RP-04 | Fallback parsing for plain text responses          | Extracts restaurant names and details via regex            |
| F-RP-05 | Validate restaurant names against dataset          | Hallucinated names are filtered out                        |
| F-RP-06 | Handle missing fields with defaults                | Missing `explanation` → default text; missing `rating` → 0|

#### Recommendation Engine (`src/recommendation/engine.py`)

| Test ID | Test Description                                   | Pass Criteria                                              |
|---------|----------------------------------------------------|------------------------------------------------------------|
| F-RE-01 | Full pipeline: preferences → recommendations       | Returns `list[Recommendation]` with `len >= 1`             |
| F-RE-02 | Fallback when LLM is unavailable                  | Returns top-rated restaurants with generic explanations     |
| F-RE-03 | Pipeline with empty preferences                    | Returns top-rated globally; no crash                       |
| F-RE-04 | Pipeline with all preferences set                  | Results reflect all preferences; LLM explanations present  |

### 3.2 Integration Tests

| Test ID  | Test Description                                   | Pass Criteria                                              |
|----------|----------------------------------------------------|------------------------------------------------------------|
| I-01     | Loader → Preprocessor chain                        | Raw data loads and preprocesses without errors             |
| I-02     | Preprocessor → Filter chain                        | Preprocessed data filters correctly on all criteria        |
| I-03     | Filter → PromptBuilder → Parser chain (mocked LLM) | Prompt built; mock response parsed into Recommendations   |
| I-04     | Full pipeline end-to-end (mocked LLM)              | User preferences → structured recommendations             |
| I-05     | Full pipeline end-to-end (real LLM)                | Live Gemini API returns valid, parseable recommendations   |

---

## 4. LLM Output Quality Evaluation

### 4.1 Evaluation Criteria

Each LLM response is evaluated on 5 quality dimensions:

| Criterion             | Description                                                          | Score Range |
|-----------------------|----------------------------------------------------------------------|-------------|
| **Groundedness**      | Are ALL recommended restaurants from the provided dataset?           | 0–5         |
| **Relevance**         | Do recommendations match the stated user preferences?                | 0–5         |
| **Explanation Quality**| Are explanations specific, helpful, and personalized?               | 0–5         |
| **Format Compliance** | Is the response valid JSON matching the requested schema?            | 0–5         |
| **Ranking Quality**   | Is the best match ranked #1? Does ordering make sense?               | 0–5         |

### 4.2 LLM Evaluation Test Scenarios

| Scenario ID | User Preferences                                                      | Expected LLM Behavior                                                    |
|-------------|-----------------------------------------------------------------------|--------------------------------------------------------------------------|
| LLM-E-01    | Location: Bangalore, Budget: Medium, Cuisine: Italian, Rating: 4.0   | Top results are Italian restaurants in Bangalore, ₹401–1000, rated ≥ 4.0 |
| LLM-E-02    | Location: Delhi, Budget: Low, Cuisine: Chinese, Rating: 3.5          | Affordable Chinese restaurants in Delhi; explanations mention budget      |
| LLM-E-03    | Location: Mumbai, Budget: High, Cuisine: None, Rating: 4.5           | Premium restaurants in Mumbai across cuisines; highest rated first        |
| LLM-E-04    | Location: None, Budget: None, Cuisine: North Indian, Rating: 0       | Best North Indian restaurants nationwide; varied locations                |
| LLM-E-05    | All preferences empty                                                 | Top-rated restaurants globally; diverse selection                         |
| LLM-E-06    | Additional prefs: "family-friendly, outdoor seating"                  | Explanations reference family-friendliness and seating                    |
| LLM-E-07    | Additional prefs: "quick service, lunch under 30 min"                 | LLM factors speed into ranking and explanations                          |
| LLM-E-08    | Very niche: Location: small city, Cuisine: rare type                  | Few or no matches → relaxation → LLM explains broader results            |

### 4.3 Automated LLM Quality Checks

```python
def evaluate_llm_response(recommendations, filtered_df, preferences):
    """Automated quality checks on LLM output."""
    
    scores = {}
    
    # 1. Groundedness: All names exist in dataset
    dataset_names = set(filtered_df['name'].str.lower())
    grounded = all(
        r.restaurant_name.lower() in dataset_names 
        for r in recommendations
    )
    scores['groundedness'] = 5 if grounded else 0
    
    # 2. Format: All required fields present
    format_ok = all(
        r.restaurant_name and r.cuisine and r.explanation 
        for r in recommendations
    )
    scores['format_compliance'] = 5 if format_ok else 2
    
    # 3. Explanation length: Meaningful (> 20 chars)
    good_explanations = all(
        len(r.explanation) > 20 for r in recommendations
    )
    scores['explanation_quality'] = 5 if good_explanations else 3
    
    # 4. No duplicates
    names = [r.restaurant_name for r in recommendations]
    no_dupes = len(names) == len(set(names))
    scores['no_duplicates'] = 5 if no_dupes else 2
    
    # 5. Count matches requested top_n
    scores['count_match'] = 5 if len(recommendations) == 5 else 3
    
    return scores
```

### 4.4 LLM Hallucination Detection

| Check                                  | Method                                                          | Action on Failure              |
|----------------------------------------|-----------------------------------------------------------------|--------------------------------|
| Restaurant name exists in dataset      | Compare against `filtered_df['name']`                           | Drop the recommendation        |
| Rating matches dataset                 | Compare `r.rating` vs actual rating (±0.5 tolerance)            | Replace with actual value      |
| Cost is plausible                      | Compare `r.estimated_cost` vs actual cost (±30% tolerance)      | Replace with actual value      |
| Cuisine matches dataset                | Compare `r.cuisine` vs actual cuisine list                      | Replace with actual value      |
| Explanation doesn't contradict data    | Check for "budget-friendly" when cost > ₹2000                  | Flag for manual review         |

---

## 5. Recommendation Relevance Evaluation

### 5.1 Relevance Test Matrix

Each test scenario checks whether recommendations match user intent:

| Scenario ID | Input Preferences                          | Relevance Check                                                       | Pass Criteria                                      |
|-------------|-------------------------------------------|-----------------------------------------------------------------------|-----------------------------------------------------|
| RR-01       | Location: "Bangalore"                     | All results in Bangalore                                              | ≥ 80% of results match location                    |
| RR-02       | Budget: "Low"                             | All results have cost ≤ ₹400                                          | ≥ 80% of results in "Low" budget category           |
| RR-03       | Cuisine: "Chinese"                        | All results serve Chinese cuisine                                     | ≥ 80% of results contain "Chinese" in cuisines      |
| RR-04       | Min Rating: 4.0                           | All results rated ≥ 4.0                                               | 100% of results meet rating threshold               |
| RR-05       | Combined: Bangalore + Medium + Italian    | Results match ALL three criteria                                      | ≥ 60% match all; 100% match at least 2 of 3        |
| RR-06       | Contradictory: Low budget + Fine dining   | Results lean toward one preference                                    | LLM explains the tradeoff in explanations           |
| RR-07       | Very specific (1-2 possible matches)      | Returns the specific matches + close alternatives                     | Specific matches ranked highest                     |
| RR-08       | No matches → relaxation                   | Relaxed results are reasonably close to original intent               | Relaxation notice shown; results still useful       |

### 5.2 Ranking Quality Evaluation

| Check                                    | Method                                                           | Pass Criteria                       |
|------------------------------------------|------------------------------------------------------------------|-------------------------------------|
| #1 recommendation is the best match      | Manual review against preferences                                | Subjectively correct in ≥ 70% of cases |
| Higher-rated restaurants rank higher      | Compare positions vs ratings (when other prefs are equal)        | Positive correlation (ρ > 0.5)      |
| Budget-aligned restaurants rank higher    | Compare positions vs budget match                                | Exact budget matches in top 3       |
| Cuisine-matched restaurants rank higher   | Compare positions vs cuisine relevance                           | Exact cuisine matches in top 3      |
| Ranking is stable across repeated calls   | Run same preferences 3 times; compare rankings                   | ≥ 3/5 restaurants appear in all runs|

### 5.3 Diversity Evaluation

| Check                           | Pass Criteria                                                        |
|---------------------------------|----------------------------------------------------------------------|
| Not all results from same area  | At least 2 distinct sub-locations when location is broad (e.g., city)|
| Not all results same cuisine    | At least 2 cuisine types (when cuisine filter is broad or absent)    |
| Not all results same price tier | At least 2 price points (when budget filter is absent)               |
| Results aren't trivially ranked | Not simply sorted by rating descending                               |

---

## 6. Performance Evaluation

### 6.1 Latency Benchmarks

| Metric                           | Target       | Measurement Method                                        |
|----------------------------------|-------------|-----------------------------------------------------------|
| **Dataset load (cached)**        | < 1 second  | `time.time()` around `loader.load()`                      |
| **Dataset load (first download)**| < 30 seconds| `time.time()` around first `loader.load()`                |
| **Preprocessing**                | < 2 seconds | `time.time()` around `preprocessor.preprocess()`          |
| **Filtering**                    | < 500 ms    | `time.time()` around `filter_engine.filter()`             |
| **Prompt building**              | < 100 ms    | `time.time()` around `prompt_builder.build()`             |
| **LLM API call**                 | < 15 seconds| `time.time()` around `llm_client.generate()`              |
| **Response parsing**             | < 100 ms    | `time.time()` around `response_parser.parse()`            |
| **Total end-to-end (cached)**    | < 20 seconds| `time.time()` around full `engine.recommend()`            |
| **UI render time**               | < 500 ms    | Perceived time after LLM response returns                 |

### 6.2 Performance Test Script

```python
import time

def benchmark_pipeline(engine, preferences, n_runs=5):
    """Benchmark the full recommendation pipeline."""
    
    timings = {
        'load': [], 'preprocess': [], 'filter': [],
        'prompt': [], 'llm': [], 'parse': [], 'total': []
    }
    
    for i in range(n_runs):
        t_start = time.time()
        
        # Step 1: Load
        t0 = time.time()
        df = engine.loader.load()
        timings['load'].append(time.time() - t0)
        
        # Step 2: Preprocess
        t0 = time.time()
        clean_df = engine.preprocessor.preprocess(df)
        timings['preprocess'].append(time.time() - t0)
        
        # Step 3: Filter
        t0 = time.time()
        filtered = engine.filter_engine.filter(clean_df, preferences)
        timings['filter'].append(time.time() - t0)
        
        # Step 4: Prompt
        t0 = time.time()
        prompt = engine.prompt_builder.build(filtered, preferences)
        timings['prompt'].append(time.time() - t0)
        
        # Step 5: LLM
        t0 = time.time()
        response = engine.llm_client.generate(prompt)
        timings['llm'].append(time.time() - t0)
        
        # Step 6: Parse
        t0 = time.time()
        recs = engine.response_parser.parse(response)
        timings['parse'].append(time.time() - t0)
        
        timings['total'].append(time.time() - t_start)
    
    # Report averages
    for step, times in timings.items():
        avg = sum(times) / len(times)
        print(f"{step:>12}: {avg:.3f}s (avg over {n_runs} runs)")
    
    return timings
```

### 6.3 Resource Usage Benchmarks

| Metric                       | Target        | Measurement                          |
|------------------------------|---------------|--------------------------------------|
| **Memory (DataFrame)**       | < 100 MB      | `df.memory_usage(deep=True).sum()`   |
| **Cache file size**          | < 50 MB       | File size of `.parquet` cache        |
| **LLM tokens per request**   | < 4000 tokens | Count from API response metadata     |
| **API cost per request**     | < $0.01       | Based on Gemini pricing              |

---

## 7. User Experience Evaluation

### 7.1 UI Usability Checklist

| ID    | Criterion                                          | Pass Criteria                                                  |
|-------|----------------------------------------------------|-----------------------------------------------------------------|
| UX-01 | Preference inputs are clearly labeled              | Each input has descriptive label and helper text                |
| UX-02 | Default values are sensible                        | User can get results without changing any default               |
| UX-03 | Loading state is visible                           | Spinner + message shown during LLM processing                  |
| UX-04 | Recommendation cards are readable                  | Name, cuisine, rating, cost, explanation all visible at glance  |
| UX-05 | Rating is visually represented                     | Stars or numeric display; not just raw float                    |
| UX-06 | Filter relaxation is communicated                  | Info banner explains which filters were adjusted                |
| UX-07 | Error messages are user-friendly                   | No stack traces; plain language explanations                    |
| UX-08 | Empty state is handled                             | "No restaurants found" with suggestions to adjust preferences   |
| UX-09 | Page is responsive                                 | Usable on desktop and tablet viewports                         |
| UX-10 | Button is disabled during processing               | No duplicate submissions possible                               |

### 7.2 Information Clarity Evaluation

| Element                     | Evaluation Question                                               | Score (1–5) |
|-----------------------------|-------------------------------------------------------------------|-------------|
| Restaurant name             | Is it clearly the most prominent element?                         |             |
| Cuisine type                | Is it easy to scan which cuisines are served?                     |             |
| Rating                      | Is the rating immediately understandable?                         |             |
| Cost estimate               | Is the cost clear (currency, per-person vs per-two)?              |             |
| AI explanation               | Is the explanation helpful for decision-making?                   |             |
| Relaxation notice           | Does the user understand why results differ from their query?     |             |
| Error messages              | Can the user understand and act on the error?                     |             |

### 7.3 User Journey Evaluation

| Step | User Action                         | Expected System Response                         | Pass? |
|------|-------------------------------------|--------------------------------------------------|-------|
| 1    | Opens the app                       | Page loads in < 3s; inputs are visible            |       |
| 2    | Selects location                    | Dropdown populated with dataset locations         |       |
| 3    | Selects budget tier                 | Radio button selection works                      |       |
| 4    | Selects cuisine                     | Dropdown populated with dataset cuisines          |       |
| 5    | Adjusts rating slider               | Slider moves smoothly; value displayed            |       |
| 6    | Types additional preferences        | Text area accepts input; no lag                   |       |
| 7    | Clicks "Get Recommendations"        | Button disables; spinner appears                  |       |
| 8    | Waits for results                   | Spinner visible; message "AI is thinking..."      |       |
| 9    | Views recommendations               | 5 cards displayed with all fields                 |       |
| 10   | Reads AI explanation                | Explanation references their specific preferences |       |
| 11   | Changes preferences & re-submits    | New results reflect new preferences               |       |

---

## 8. Robustness & Error Handling Evaluation

### 8.1 Failure Scenario Tests

| Scenario ID | Failure Scenario                                | Expected Recovery                                           | Pass Criteria                          |
|-------------|------------------------------------------------|-------------------------------------------------------------|----------------------------------------|
| RB-01       | Hugging Face API down (first load, no cache)   | Clear error message; app doesn't crash                      | Error shown in UI; no traceback        |
| RB-02       | Hugging Face API down (cache exists)           | App loads from cache; no user-visible error                 | Recommendations work normally          |
| RB-03       | Gemini API key invalid                         | Startup/runtime error with clear guidance                   | Message mentions `.env` and API key    |
| RB-04       | Gemini API rate limited                        | Retry with backoff; fallback if retries exhausted           | User sees results (possibly non-LLM)   |
| RB-05       | Gemini API returns 500 error                   | Retry then fallback                                         | User sees results within 45 seconds    |
| RB-06       | Gemini API timeout (> 30s)                     | Timeout raised; fallback activates                          | User not stuck waiting > 35 seconds    |
| RB-07       | LLM returns invalid JSON                       | Fallback parser attempts recovery                           | Some recommendations shown             |
| RB-08       | LLM returns empty response                     | Fallback to top-rated restaurants                           | User sees results with fallback notice |
| RB-09       | All filters return 0 results + relaxation fails| Empty state with helpful message                            | "No restaurants found" + suggestions   |
| RB-10       | Corrupted cache file                           | Re-download dataset; new cache written                      | App recovers; no crash                 |

### 8.2 Recovery Time Objectives

| Failure Type               | Max Acceptable Downtime | Recovery Method                |
|----------------------------|-------------------------|--------------------------------|
| LLM API transient error    | 15 seconds              | Automatic retry                |
| LLM API sustained outage   | 5 seconds               | Fallback to non-LLM results   |
| Dataset download failure   | 0 seconds (if cached)   | Load from cache                |
| Dataset download failure   | Immediate error          | Error message (no cache)       |

---

## 9. Code Quality Evaluation

### 9.1 Test Coverage Targets

| Module                     | Target Coverage | Critical Paths                                     |
|----------------------------|----------------|----------------------------------------------------|
| `loader.py`                | ≥ 80%          | Load, cache, fallback                              |
| `preprocessor.py`          | ≥ 90%          | All normalization functions                        |
| `filter_engine.py`         | ≥ 90%          | Each filter, relaxation logic, edge cases          |
| `prompt_builder.py`        | ≥ 85%          | Prompt construction, truncation, missing fields    |
| `llm_client.py`            | ≥ 75%          | Successful call, retries, timeout (mock API)       |
| `response_parser.py`       | ≥ 90%          | JSON parsing, fallback, validation                 |
| `engine.py`                | ≥ 85%          | Full pipeline, fallback paths                      |
| **Overall**                | **≥ 85%**      | —                                                  |

### 9.2 Code Quality Checklist

| Criterion                          | Pass Criteria                                                 |
|------------------------------------|---------------------------------------------------------------|
| **Type hints**                     | All function signatures have type annotations                 |
| **Docstrings**                     | All public classes and methods have docstrings                |
| **No hardcoded values**            | Magic numbers/strings extracted to config                     |
| **Error handling**                 | All external calls wrapped in try/except                      |
| **Logging**                        | Key operations logged (load, filter, LLM call, parse)         |
| **No print statements**            | All output via logger; no raw `print()`                       |
| **Single responsibility**          | Each class/function does one thing                            |
| **DRY (Don't Repeat Yourself)**    | No duplicated logic across modules                            |
| **Consistent naming**              | snake_case for functions/variables; PascalCase for classes     |
| **Requirements pinned**            | All dependencies have version constraints                     |

### 9.3 Documentation Completeness

| Document                   | Required Contents                                             | Status |
|----------------------------|---------------------------------------------------------------|--------|
| `README.md`                | Overview, setup, usage, screenshots, architecture link        |        |
| `problemStatement.md`      | Requirements and workflow                                     | ✅     |
| `architecture.md`          | System design, components, data flow                          | ✅     |
| `implementation-plan.md`   | Phase-wise tasks and acceptance criteria                      | ✅     |
| `edge-case.md`             | Corner scenarios and mitigations                              | ✅     |
| `eval.md`                  | This document                                                 | ✅     |
| `.env.example`             | All config variables with descriptions                        |        |
| Code docstrings            | Every public class and method documented                      |        |

---

## 10. Phase-Wise Evaluation Criteria

### Phase 1: Project Setup & Infrastructure

| Eval ID | Criterion                                        | Method              | Pass/Fail |
|---------|--------------------------------------------------|---------------------|-----------|
| P1-01   | All packages install without errors              | `pip install -r requirements.txt` | ✅ Pass |
| P1-02   | `AppConfig` loads `.env` values                  | Unit test           | ✅ Pass   |
| P1-03   | Logger outputs to console                        | Manual check        | ✅ Pass   |
| P1-04   | All module imports work                          | `python -c "from src.data import loader"` | ✅ Pass |
| P1-05   | `.gitignore` excludes `.env` and `__pycache__`   | `cat .gitignore`    | ✅ Pass   |

### Phase 2: Data Ingestion & Preprocessing

| Eval ID | Criterion                                        | Method              | Pass/Fail |
|---------|--------------------------------------------------|---------------------|-----------|
| P2-01   | Dataset loads with correct schema                | F-DL-01 to F-DL-05  |           |
| P2-02   | Cache works correctly                            | F-DL-02, F-DL-03    |           |
| P2-03   | Preprocessing produces clean data                | F-PP-01 to F-PP-06  |           |
| P2-04   | No null names or invalid ratings in output       | Assertion check      |           |
| P2-05   | Budget categories distributed across Low/Med/High| Value counts check   |           |

### Phase 3: Filtering Engine

| Eval ID | Criterion                                        | Method              | Pass/Fail |
|---------|--------------------------------------------------|---------------------|-----------|
| P3-01   | Each individual filter works correctly           | F-FE-01 to F-FE-04  |           |
| P3-02   | Combined filtering works                         | F-FE-05             |           |
| P3-03   | Relaxation triggers at < 3 results              | F-FE-07             |           |
| P3-04   | Relaxation order is correct                      | F-FE-07, F-FE-08    |           |
| P3-05   | Truncation caps at 50 results                   | F-FE-09             |           |

### Phase 4: LLM Integration

| Eval ID | Criterion                                        | Method              | Pass/Fail |
|---------|--------------------------------------------------|---------------------|-----------|
| P4-01   | Prompt includes all preferences and data         | F-PB-01 to F-PB-05  |           |
| P4-02   | LLM returns valid JSON                           | F-LC-01, LLM-E-01   |           |
| P4-03   | Response parser handles all formats              | F-RP-01 to F-RP-06  |           |
| P4-04   | Hallucination detection works                    | F-RP-05             |           |
| P4-05   | Fallback works when LLM is unavailable           | F-RE-02             |           |
| P4-06   | LLM explanations are personalized                | LLM-E-01 to LLM-E-07|          |

### Phase 5: Streamlit UI

| Eval ID | Criterion                                        | Method              | Pass/Fail |
|---------|--------------------------------------------------|---------------------|-----------|
| P5-01   | App launches without errors                      | `streamlit run ui/app.py` |      |
| P5-02   | All input components work                        | UX-01 to UX-03      |           |
| P5-03   | Recommendation cards display correctly           | UX-04, UX-05        |           |
| P5-04   | Loading and error states work                    | UX-03, UX-07, UX-08 |           |
| P5-05   | Full user journey works                          | User Journey table   |           |

### Phase 6: Testing, Polish & Documentation

| Eval ID | Criterion                                        | Method              | Pass/Fail |
|---------|--------------------------------------------------|---------------------|-----------|
| P6-01   | All unit tests pass                              | `pytest`            |           |
| P6-02   | Test coverage ≥ 85%                              | `pytest --cov`      |           |
| P6-03   | Integration tests pass                           | I-01 to I-05        |           |
| P6-04   | All edge cases from edge-case.md addressed       | Cross-reference     |           |
| P6-05   | README.md is complete                            | Documentation check  |           |
| P6-06   | No `print()` statements in production code       | `grep -r "print("` |           |

---

## 11. Evaluation Rubric & Scoring

### Overall Project Scoring

| Grade | Score Range | Criteria                                                                   |
|-------|-------------|----------------------------------------------------------------------------|
| **A** | 90–100%     | All functional tests pass; LLM quality ≥ 4.0/5; performance meets targets; polished UI |
| **B** | 75–89%      | Core functionality works; LLM quality ≥ 3.5/5; minor UI issues            |
| **C** | 60–74%      | Basic recommendation pipeline works; some edge cases unhandled             |
| **D** | 40–59%      | Partial functionality; significant issues                                  |
| **F** | < 40%       | Core pipeline broken; critical failures                                    |

### Scoring Breakdown

| Dimension                    | Max Score | Scoring Method                                                      |
|------------------------------|-----------|---------------------------------------------------------------------|
| Functional Correctness (25%) | 25        | (Tests passing / Total tests) × 25                                  |
| LLM Output Quality (25%)    | 25        | Average of 5 quality criteria (0–5) × 1                             |
| Recommendation Relevance (20%)| 20      | (Relevant results / Total results) across test scenarios × 20       |
| Performance (10%)            | 10        | (Benchmarks met / Total benchmarks) × 10                            |
| User Experience (10%)        | 10        | (UX checklist passed / Total UX items) × 10                         |
| Code Quality (10%)           | 10        | (Coverage % × 0.5) + (Checklist items passed / Total × 0.5) × 10   |
| **Total**                    | **100**   |                                                                     |

---

## 12. Evaluation Execution Checklist

### Pre-Evaluation Setup

- [ ] Virtual environment activated
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` configured with valid `GEMINI_API_KEY`
- [ ] Dataset cached locally (or network available)

### Evaluation Steps

- [ ] **Step 1**: Run unit tests → `pytest tests/ -v --cov=src`
- [ ] **Step 2**: Run integration tests → `pytest tests/ -v -k "integration"`
- [ ] **Step 3**: Run performance benchmarks → `python scripts/benchmark.py`
- [ ] **Step 4**: Execute LLM quality scenarios (LLM-E-01 to LLM-E-08)
- [ ] **Step 5**: Execute relevance test matrix (RR-01 to RR-08)
- [ ] **Step 6**: Walk through UI user journey (Steps 1–11)
- [ ] **Step 7**: Execute failure scenarios (RB-01 to RB-10)
- [ ] **Step 8**: Review code quality checklist
- [ ] **Step 9**: Verify documentation completeness
- [ ] **Step 10**: Calculate final score using rubric

### Post-Evaluation

- [ ] Document all findings in evaluation results report
- [ ] Log any bugs discovered during evaluation
- [ ] Create follow-up tasks for failed criteria
- [ ] Archive test outputs and benchmark results

---

## 📎 References

- **Implementation Plan**: [`implementation-plan.md`](file:///c:/Projects/Zomato_recommendation/docs/implementation-plan.md) — phase-wise tasks and acceptance criteria
- **Architecture**: [`architecture.md`](file:///c:/Projects/Zomato_recommendation/docs/architecture.md) — system design and component specifications
- **Edge Cases**: [`edge-case.md`](file:///c:/Projects/Zomato_recommendation/docs/edge-case.md) — corner scenarios and mitigations
- **Problem Statement**: [`problemStatement.md`](file:///c:/Projects/Zomato_recommendation/docs/problemStatement.md) — project requirements
