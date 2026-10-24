# 🍽️ Zomato AI Restaurant Recommender

An AI-powered restaurant recommendation web application for Bangalore foodies. Blends deterministic multi-criteria filtering, progressive constraint relaxation, and Groq-accelerated LLM reasoning (`Llama 3.3 70B`) to deliver personalized dining recommendations grounded in real diner reviews.

---

## 🌟 Overview

Finding the right restaurant usually requires juggling multiple search criteria—neighborhood, budget, cuisine, ambiance, and diner ratings—often resulting in zero matches or generic listicles.

**Zomato AI Restaurant Recommender** solves this with a two-stage hybrid architecture:
1. **Deterministic Filtering Engine**: Scans 51,000+ Bangalore restaurant records, applying sequential AND filters with progressive constraint relaxation if matches are too few.
2. **LLM Reasoning & Personalization**: Takes top matching candidate restaurants and user nuances, prompting Groq's ultra-fast LPU inference to rank the best options and explain *why* each is a great fit in 2–3 sentences.

---

## ✨ Features

- **🎯 Multi-Criteria Filtering**: Filter by Bangalore neighborhood (92 areas), budget tier (Low/Medium/High), cuisine (105+ types), and minimum diner rating.
- **🔄 Progressive Constraint Relaxation**: Never hit a dead end—if strict filters yield < 3 results, constraints are loosened step-by-step (`additional_prefs` → `rating` → `budget` → `cuisine` → `location`) while transparently informing the user.
- **⚡ Ultra-Low Latency Inference**: Powered by Groq's high-speed inference engine with exponential backoff retry handling.
- **🛡️ Hallucination Prevention**: Output parser validates LLM-suggested restaurant names strictly against candidate dataset records; hallucinated names are rejected.
- **🔌 Offline Fallback Mode**: If the LLM API is unavailable or rate-limited, the system falls back to verified, vote-weighted top-rated dining choices without breaking the user experience.
- **✨ One-Click Quick Presets**: Instant discovery presets (*"Romantic Date Night"*, *"Cozy Italian Pizza"*, *"Work-Friendly Cafe"*, *"Authentic Desi Feast"*).
- **🎨 Modern Culinary Aesthetic**: Rich UI built with Streamlit and custom CSS featuring modern typography, star ratings, metadata tags, and CSV export.

---

## 🛠️ Tech Stack

| Component | Technology | Role |
|-----------|------------|------|
| **Frontend** | [Streamlit](https://streamlit.io/) | Interactive web UI with reactive sidebar and cards |
| **Data Processing** | [Pandas](https://pandas.pydata.org/), [PyArrow](https://arrow.apache.org/) | Preprocessing, cleaning, Parquet caching |
| **Dataset** | [Hugging Face Datasets](https://huggingface.co/) | `ManikaSaini/zomato-restaurant-recommendation` |
| **LLM Provider** | [Groq](https://groq.com/) | Ultra-fast inference with `llama-3.3-70b-versatile` |
| **Configuration** | `python-dotenv`, `pydantic`/`dataclasses` | Type-safe environment management |
| **Testing** | [Pytest](https://pytest.org/), `pytest-cov` | 88 tests covering unit, edge cases, and benchmarks |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+ (tested on Python 3.11)
- A free [Groq API Key](https://console.groq.com/keys)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/snigdhapanda1410/Zomato_Recommendations.git
   cd Zomato_Recommendations
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Configuration

Copy the example environment template to `.env`:
```bash
cp .env.example .env
```

Open `.env` and provide your Groq API key:
```env
# Groq API Configuration
GROQ_API_KEY=your_actual_groq_api_key_here
LLM_MODEL=llama-3.3-70b-versatile
LLM_TEMPERATURE=0.7
LLM_MAX_RETRIES=3
LLM_TIMEOUT_SECONDS=30

# Dataset Configuration
DATASET_NAME=ManikaSaini/zomato-restaurant-recommendation
CACHE_DIR=./data/cache
CACHE_ENABLED=true

# Budget Thresholds (₹, cost for two)
BUDGET_LOW_MAX=400
BUDGET_MEDIUM_MAX=1000

# Application Defaults
TOP_N_RECOMMENDATIONS=5
MAX_RESTAURANTS_TO_LLM=50
LOG_LEVEL=INFO
```

### Running the App

Launch the Streamlit web application:
```bash
streamlit run ui/app.py
```
Open your browser at [http://localhost:8501](http://localhost:8501).

---

## 📖 Usage Guide

1. **Select Preferences in Sidebar**:
   - **Neighborhood**: Choose from 92 Bangalore areas (e.g. *Koramangala*, *Indiranagar*, *HSR*) or select *All Bangalore*.
   - **Budget Tier**: Select Low (≤₹400), Medium (₹401–₹1000), or High (>₹1000).
   - **Cuisine**: Select from 105+ cuisine styles (Italian, North Indian, Cafe, Asian, etc.).
   - **Minimum Rating**: Adjust the slider (0.0 to 5.0).
   - **Vibe & Preferences**: Add free-form context (e.g., *"candlelight rooftop, artisan gelato, craft beer"*).
2. **Click "Recommend"**:
   - The engine loads the preprocessed data, applies sequential filters, generates a prompt with candidate restaurants, and requests personalized recommendations from the LLM.
3. **Review Recommendation Cards**:
   - Each card displays match rank, diner rating, cost for two, cuisine tags, neighborhood, and the **AI Critic Verdict**.
   - Expand the **Diner Details** drawer to view online ordering status, table reservations, and review counts.
   - Click **Export Recommendations (CSV)** to download your curated list.

---

## 📁 Project Structure

```
Zomato_recommendation/
├── data/
│   └── cache/                    # Local Parquet cache of Hugging Face dataset
├── docs/
│   ├── architecture.md           # Full system architecture specification
│   ├── implementation-plan.md    # 6-phase project implementation roadmap
│   ├── edge-case.md              # Edge cases, risk matrix, and mitigations
│   └── problemStatement.txt      # Problem statement & context
├── src/
│   ├── __init__.py
│   ├── data/                     # Dataset loader, preprocessor & caching
│   │   ├── cache.py
│   │   ├── loader.py
│   │   └── preprocessor.py
│   ├── filters/                  # Filtering engine & constraint relaxation
│   │   └── filter_engine.py
│   ├── llm/                      # Prompt construction, Groq client & response parser
│   │   ├── llm_client.py
│   │   ├── prompt_builder.py
│   │   └── response_parser.py
│   ├── recommendation/           # Central orchestrator engine
│   │   └── engine.py
│   └── utils/                    # Configuration management & logging
│       ├── config.py
│       └── logger.py
├── ui/
│   ├── assets/                   # App logos and visuals
│   ├── app.py                    # Streamlit web application entry point
│   └── styles.py                 # Custom CSS design tokens & card templates
├── tests/                        # Comprehensive test suite (88 tests)
│   ├── test_config.py
│   ├── test_edge_cases.py        # Dedicated E1–E10 edge case validation
│   ├── test_engine.py            # Orchestrator & integration tests
│   ├── test_filter_engine.py     # Filter logic & relaxation tests
│   ├── test_llm_client.py        # Groq client & retry tests
│   ├── test_loader.py            # Dataset loading & caching tests
│   ├── test_logger.py
│   ├── test_performance.py       # Sub-second latency benchmark tests
│   ├── test_preprocessor.py      # Data cleaning & deduplication tests
│   ├── test_prompt_builder.py    # Prompt template structure tests
│   ├── test_response_parser.py   # JSON parsing, fallback regex, hallucination check
│   └── test_ui_styles.py         # UI styles and HTML card tests
├── .env.example                  # Environment configuration template
├── .gitignore                    # Git exclusions
├── requirements.txt              # Production & development dependencies
└── README.md                     # Documentation
```

---

## 🏛️ Architecture & Data Flow

```
User Query (Sidebar / Preset)
        │
        ▼
RecommendationEngine (Central Orchestrator)
        │
   ┌────┴────────────────────────┐
   │ 1. Load / Get Clean Data    │ ◄── Cached Parquet (9,249 clean rows)
   │ 2. Apply FilterEngine       │
   │    └─ Results < 3? Relax    │
   │ 3. Build Grounded Prompt    │
   │ 4. Call Groq LLM API        │
   │    └─ Error / Timeout?      │ ──► Deterministic Fallback Mode
   │ 5. Parse JSON & Validate    │
   │    └─ Reject hallucinations │
   └────┬────────────────────────┘
        │
        ▼
RecommendationResult ──► Rendered in Stitch Dark Theme UI (HTML/Tailwind) & Streamlit
```

---

## 🚀 Deployment (Railway & Vercel)

The project is architected for continuous multi-cloud deployment:

- **Backend (Railway)**: Containerized ASGI Python service (`uvicorn ui.server:app`) with bundled 175 KB clean dataset ([`data/zomato_clean.parquet`](file:///c:/Projects/Zomato_recommendation/data/zomato_clean.parquet)) for instant ~2s cold boots without remote download overhead. Configured via [`railway.json`](file:///c:/Projects/Zomato_recommendation/railway.json) and [`Procfile`](file:///c:/Projects/Zomato_recommendation/Procfile).
- **Frontend (Vercel)**: Global Edge CDN hosting [`index.html`](file:///c:/Projects/Zomato_recommendation/index.html) with built-in reverse proxy rewrites configured in [`vercel.json`](file:///c:/Projects/Zomato_recommendation/vercel.json) to proxy `/api/*` requests directly to Railway.

For detailed setup, environment variables, and runbooks, refer to [`docs/deployment-plan.md`](file:///c:/Projects/Zomato_recommendation/docs/deployment-plan.md).

---

## 🧪 Testing

Run all unit, integration, edge-case, and performance benchmark tests:

```bash
# Run all tests
pytest

# Run tests with code coverage report
pytest --cov=src --cov-report=term-missing
```

### Edge Case Coverage (E1 – E10)
All 10 project edge cases documented in [`docs/edge-case.md`](file:///c:/Projects/Zomato_recommendation/docs/edge-case.md) are tested in [`tests/test_edge_cases.py`](file:///c:/Projects/Zomato_recommendation/tests/test_edge_cases.py):
- **E1**: Empty user preferences → Returns top-rated Bangalore restaurants.
- **E2**: Nonexistent neighborhood → Relaxes location filter gracefully.
- **E3**: Nonexistent cuisine → Relaxes cuisine constraint.
- **E4**: Unattainable 5.0 rating threshold → Relaxes rating to closest high-scoring spots.
- **E5**: Duplicate restaurant listings → Deduplicates on `(name, location)`.
- **E6**: Non-JSON LLM response → Fallback regex key-value parser.
- **E7**: Hallucinated restaurant names → Validates against candidate dataset.
- **E8**: Missing or invalid API key → Safe error raising & offline fallback.
- **E9**: Network interruption during download → Fallback to local Parquet cache.
- **E10**: Extremely long text in preferences → Clamped to 500 characters safely.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Ensure all tests pass (`pytest`)
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
