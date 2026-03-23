# 🤖 AI Job Assistant

An AI-powered system that matches your resume to job postings and generates personalized cover letters.

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-blue)](https://reactjs.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.1-orange)](https://langchain-ai.github.io/langgraph)

---

## ✨ Features

- 📄 Upload your PDF resume — AI extracts skills, experience, education
- 🧠 Skill inference — discovers implied skills beyond what's written
- 🔍 Multi-source job fetching — RapidAPI + SerpApi (Google Jobs)
- 📊 Hybrid matching — semantic similarity + skill overlap + seniority fit
- ✅ Specific match reasons — tool-level explanations, not generic text
- ❌ Actionable missing skills — exactly what to learn for each job
- 📝 Personalized cover letters — unique per job, not a template
- 🧹 HTML cleaning — clean job descriptions for better matching

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| LLM | OpenAI GPT-4o |
| Embeddings | OpenAI text-embedding-3-small |
| Vector Store | FAISS |
| Agent Workflow | LangGraph (6 nodes) |
| Backend | FastAPI + Python |
| Job Data | RapidAPI JSearch + SerpApi Google Jobs |
| Frontend | React + TypeScript + Tailwind CSS |

---

## 🗺️ How It Works
```
User uploads PDF resume
        ↓
PyMuPDF extracts text
        ↓
GPT-4o extracts skills + infers implied skills
        ↓
LangGraph 6-node workflow:
  Node 1 → Fetch jobs (RapidAPI + SerpApi)
  Node 2 → Embed resume (OpenAI)
  Node 3 → Embed jobs (OpenAI)
  Node 4 → Hybrid scoring (FAISS + skill overlap + seniority)
  Node 5 → Analyze matches (GPT-4o)
  Node 6 → Generate cover letters (GPT-4o)
        ↓
React frontend shows results
```

---

## 📈 V1 vs V2 Comparison

| | V1 | V2 |
|---|---|---|
| Skills extracted | 4 | 17 |
| Job sources | 1 (RapidAPI) | 2 (RapidAPI + SerpApi) |
| Jobs fetched | 1 | 12 |
| Matching | Semantic only | Semantic + Skill + Seniority |
| HTML cleaning | ❌ | ✅ |
| Match analysis | Generic | Specific + Actionable |
| Match summaries | ❌ | ✅ |

---

## ⚙️ Prerequisites

### Install uv (Python package manager)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Install Node.js
```bash
# Arch Linux
sudo pacman -S nodejs npm

# Ubuntu/Debian
sudo apt install nodejs npm
```

---

## 🚀 Getting Started

### 1. Clone the project
```bash
git clone https://github.com/erparthhere-dev/ai-job-assistant.git
cd ai-job-assistant
```

### 2. Setup backend
```bash
cd backend
uv sync
cp .env.example .env
```

Open `.env` and add your API keys:
```
OPENAI_API_KEY=sk-...
RAPIDAPI_KEY=...
SERPAPI_KEY=...
```

### 3. Setup frontend
```bash
cd ../frontend
npm install
```

---

## ▶️ Running the App

Open **two terminals**:

**Terminal 1 — Backend**
```bash
cd backend
uv run uvicorn main:app --reload
```

**Terminal 2 — Frontend**
```bash
cd frontend
npm start
```

Then open your browser at:
```
http://localhost:3000
```

---

## 🔑 API Keys Required

| Key | Where to get it |
|---|---|
| `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com) |
| `RAPIDAPI_KEY` | [rapidapi.com](https://rapidapi.com) |
| `SERPAPI_KEY` | [serpapi.com](https://serpapi.com) |

---

## 📁 Project Structure
```
ai-job-assistant/
├── backend/
│   ├── main.py                    # FastAPI app + endpoints
│   ├── core/
│   │   └── config.py              # Settings from .env
│   ├── models/
│   │   └── schemas.py             # Pydantic data models
│   ├── services/
│   │   ├── resume_service.py      # PDF parsing + skill extraction
│   │   ├── openai_service.py      # Embeddings wrapper
│   │   ├── vector_store.py        # FAISS wrapper
│   │   ├── rapidapi_service.py    # RapidAPI job fetching
│   │   ├── serpapi_service.py     # SerpApi job fetching
│   │   └── text_utils.py          # HTML cleaning utilities
│   └── agents/
│       ├── state.py               # LangGraph state definition
│       ├── nodes.py               # 6 workflow nodes
│       └── graph.py               # LangGraph workflow
└── frontend/
    └── src/
        ├── App.tsx                # Main React component
        └── services/
            └── api.ts             # API service layer
```

---

## 🔮 Roadmap

- [ ] User authentication (JWT)
- [ ] PostgreSQL database
- [ ] Cloud deployment (Vercel + Railway)
- [ ] Job alert emails
- [ ] Resume improvement suggestions
- [ ] Interview prep questions