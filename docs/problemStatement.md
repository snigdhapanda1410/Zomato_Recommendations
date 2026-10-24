# 🍽️ Problem Statement

## AI-Powered Restaurant Recommendation System (Zomato Use Case)

---

## 📌 Overview

Build an **AI-powered restaurant recommendation service** inspired by Zomato. The system should intelligently suggest restaurants based on user preferences by combining **structured data** with a **Large Language Model (LLM)** to deliver personalized, human-like recommendations.

---

## 🎯 Objective

Design and implement an application that:

1. **Takes user preferences** — such as location, budget, cuisine, and ratings
2. **Uses a real-world dataset** of restaurants for grounding recommendations in actual data
3. **Leverages an LLM** to generate personalized, human-like recommendations with explanations
4. **Displays clear and useful results** to the user in a friendly format

---

## ⚙️ System Workflow

The system follows a five-stage pipeline from data ingestion to final output:

```
┌──────────────┐    ┌──────────────┐    ┌───────────────────┐    ┌──────────────────────┐    ┌──────────────────┐
│ 1. Data      │───▶│ 2. User      │───▶│ 3. Integration    │───▶│ 4. Recommendation    │───▶│ 5. Output        │
│    Ingestion │    │    Input      │    │    Layer           │    │    Engine (LLM)      │    │    Display       │
└──────────────┘    └──────────────┘    └───────────────────┘    └──────────────────────┘    └──────────────────┘
```

### 1️⃣ Data Ingestion

- Load and preprocess the Zomato dataset from Hugging Face:
  **[ManikaSaini/zomato-restaurant-recommendation](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation)**
- Extract relevant fields such as:
  - Restaurant name
  - Location
  - Cuisine type
  - Cost for two
  - Aggregate rating
  - Other metadata (votes, online ordering, table booking, etc.)

### 2️⃣ User Input

Collect user preferences through an interactive interface:

| Preference           | Example Values                              |
|----------------------|---------------------------------------------|
| **Location**         | Delhi, Bangalore, Mumbai, etc.              |
| **Budget**           | Low, Medium, High                           |
| **Cuisine**          | Italian, Chinese, North Indian, etc.        |
| **Minimum Rating**   | 3.5, 4.0, 4.5                              |
| **Additional Prefs** | Family-friendly, quick service, fine dining |

### 3️⃣ Integration Layer

- **Filter** the dataset based on user input (location, budget, cuisine, rating)
- **Prepare** structured restaurant data for the LLM
- **Design a prompt** that helps the LLM reason about and rank the filtered options effectively

### 4️⃣ Recommendation Engine (LLM)

Use the LLM to:

- **Rank** restaurants based on how well they match user preferences
- **Provide explanations** — why each recommendation is a good fit
- **Optionally summarize** the top choices for quick decision-making

### 5️⃣ Output Display

Present top recommendations in a user-friendly format with:

| Field                      | Description                                      |
|----------------------------|--------------------------------------------------|
| 🏪 **Restaurant Name**     | Name of the recommended restaurant               |
| 🍕 **Cuisine**             | Type of cuisine served                           |
| ⭐ **Rating**              | Aggregate rating from the dataset                |
| 💰 **Estimated Cost**      | Approximate cost for two                         |
| 🤖 **AI Explanation**      | LLM-generated reasoning for why it's recommended |

---

## 📂 Dataset

- **Source**: [Hugging Face — ManikaSaini/zomato-restaurant-recommendation](https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation)
- **Domain**: Restaurant listings (Zomato-style)
- **Key Fields**: Restaurant name, location, cuisines, average cost, ratings, votes, online ordering availability, table booking

---

## 🏗️ High-Level Architecture

```
                        ┌─────────────────────┐
                        │     User Interface   │
                        │  (Preferences Input) │
                        └─────────┬───────────┘
                                  │
                                  ▼
                        ┌─────────────────────┐
                        │   Data Filtering &   │
                        │   Preprocessing      │
                        │  (Zomato Dataset)     │
                        └─────────┬───────────┘
                                  │
                                  ▼
                        ┌─────────────────────┐
                        │   Prompt Engineering │
                        │  (Structured Data +  │
                        │   User Preferences)  │
                        └─────────┬───────────┘
                                  │
                                  ▼
                        ┌─────────────────────┐
                        │     LLM Engine       │
                        │  (Ranking + Explain) │
                        └─────────┬───────────┘
                                  │
                                  ▼
                        ┌─────────────────────┐
                        │   Recommendation     │
                        │   Output Display     │
                        └─────────────────────┘
```

---

## ✅ Success Criteria

- Recommendations are **relevant** to user-specified preferences
- LLM explanations are **coherent and helpful** for decision-making
- The system handles **edge cases** gracefully (e.g., no restaurants match the filters)
- Output is **well-formatted** and easy to read

---

> **Source**: This document was generated from [`problemStatement.txt`](file:///c:/Projects/Zomato_recommendation/docs/problemStatement.txt)
