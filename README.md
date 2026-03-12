# 1. Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Install Node.js (for frontend)
sudo pacman -S nodejs npm   # Arch Linux
# or
sudo apt install nodejs npm  # Ubuntu/Debian


git clone https://github.com/erparthhere-dev/ai-job-assistant.git
cd ai-job-assistant


<h1>Setup backend</h1>

cd backend
uv sync
cp .env.example .env
# Open .env and add:
# OPENAI_API_KEY=sk-...
# RAPIDAPI_KEY=...


<h1>Setup frontend</h1>

cd ../frontend
npm install



<h1>Run backend (Terminal 1)</h1>

cd backend
uv run uvicorn main:app --reload



<h1> Run frontend (Terminal 2)</h1>

cd frontend
npm start


<h1>The only thing you need is API keys:</h1>

OPENAI_API_KEY → from platform.openai.com
RAPIDAPI_KEY → from rapidapi.com
