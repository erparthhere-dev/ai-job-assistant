# 🤖 AI Job Assistant

An AI-powered system that matches your resume to job postings and generates personalized cover letters.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| LLM | OpenAI GPT-4o |
| Embeddings | OpenAI text-embedding-3-small |
| Vector Store | FAISS |
| Agent Workflow | LangGraph |
| Backend | FastAPI + Python |
| Job Data | RapidAPI JSearch |
| Frontend | React + TypeScript |

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

---

## ✨ Features

- 📄 Upload your PDF resume
- 🤖 AI extracts your skills and experience
- 🔍 Fetches real job postings
- 🧠 Matches jobs using vector similarity
- ✅ Shows why you match each job
- 📝 Generates personalized cover letters
