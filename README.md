# job-tracker-backend

FastAPI backend for Job Application Tracker — Python REST API with PostgreSQL.

## Local Setup

```bash
# 1. Clone the repo
git clone https://github.com/QA-Master505/job-tracker-backend.git
cd job-tracker-backend

# 2. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate      # macOS/Linux
# .venv\Scripts\activate       # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env            # edit values as needed

# 5. Run the development server
uvicorn app.main:app --reload
```

Server runs at http://localhost:8000  
Interactive docs at http://localhost:8000/docs

## Health Check

```
GET /health  →  { "status": "ok", "app": "Job Tracker API" }
```

## Project Structure

```
job-tracker-backend/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app + middleware
│   ├── config.py        # Settings via pydantic-settings
│   └── routers/
│       └── __init__.py
├── requirements.txt
├── .env                 # local only, not committed
└── README.md
```
