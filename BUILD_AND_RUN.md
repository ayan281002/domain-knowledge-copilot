# Domain Knowledge Co-Pilot: Build and Run Guide

This guide shows how to build the project from scratch and run it locally or with Docker.

## 1. What You Need

- Windows 10/11, macOS, or Linux
- Python 3.11 or newer
- Git
- Optional but recommended: Docker Desktop
- API keys depending on your model choice:
  - `GROQ_API_KEY` for Groq LLM usage
  - `OPENAI_API_KEY` for OpenAI embeddings or OpenAI fallback

## 2. Get the Source Code

If you already have the project folder, you can skip this step.

```bash
git clone <your-repo-url>
cd domain-knowledge-copilot
```

If you are working inside an existing folder, make sure the repository root contains:

- `backend/`
- `frontend/`
- `docker/`
- `docker-compose.yml`
- `.env.example`

## 3. Create the Environment File

Copy the example environment file and edit the values.

```bash
copy .env.example .env
```

Set at least these values:

```env
DATABASE_URL=sqlite:///./database/app.db
JWT_SECRET=change-this-to-a-long-random-secret
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=120
GROQ_API_KEY=your_groq_api_key
OPENAI_API_KEY=your_openai_api_key
CHROMA_PATH=./database/chromadb
UPLOADS_DIR=./uploads
EMBEDDING_PROVIDER=sentence_transformers
LLM_PROVIDER=groq
BACKEND_URL=http://localhost:8000
```

Notes:
- If you use `EMBEDDING_PROVIDER=sentence_transformers`, `OPENAI_API_KEY` is not required for embeddings.
- If you use `LLM_PROVIDER=groq`, `GROQ_API_KEY` is required.
- If you switch to OpenAI embeddings or OpenAI LLM, set `OPENAI_API_KEY`.

## 4. Build and Run Locally

### 4.1 Create a Python virtual environment

From the project root:

```bash
python -m venv .venv
```

Activate it in PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 4.2 Install backend dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 4.3 Run database migrations

From the backend folder:

```bash
alembic upgrade head
```

This creates the SQLite schema in `database/app.db`.

### 4.4 Start the backend API

From the backend folder:

```bash
python main.py
```

The API will be available at:

- `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`

### 4.5 Install frontend dependencies

Open a new terminal and run:

```bash
cd frontend
pip install -r requirements.txt
```

### 4.6 Start the Streamlit frontend

From the frontend folder:

```bash
streamlit run app.py
```

The UI will be available at:

- `http://localhost:8501`

## 5. Use the App

1. Register a user in the Streamlit sidebar.
2. Log in.
3. Create a corpus.
4. Upload PDF, DOCX, TXT, or Markdown files.
5. Ask questions in the chat box.
6. Review citations and retrieved chunks.

## 6. Run With Docker

If you want the full system in one command, use Docker.

```bash
docker compose up --build
```

Services exposed:

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:8501`

Docker uses these mounted volumes:

- `./uploads`
- `./database`

## 7. Run Tests

From the backend folder:

```bash
pytest -q
```

The current suite covers:

- Authentication
- Corpus CRUD
- Upload endpoint
- Retrieval citation serialization
- Query endpoint
- Chat history

## 8. Troubleshooting

### JWT errors

If you see invalid token errors, confirm the frontend is sending the token and that `JWT_SECRET` is the same everywhere.

### Upload errors

Make sure the file extension is one of:

- `.pdf`
- `.docx`
- `.txt`
- `.md`

### Empty answers

If retrieval returns no results, check that:

- the file was uploaded successfully
- indexing completed
- the selected corpus is correct

### Model errors

If Groq or OpenAI calls fail:

- verify the API key is set
- verify the chosen provider matches the available key
- check network access for model downloads on first use

### Chroma issues

If Chroma fails:

- confirm `CHROMA_PATH` points to a writable folder
- ensure the `database/` directory exists

## 9. Recommended Production Checklist

Before deploying publicly:

- Set a strong `JWT_SECRET`
- Store API keys in a secrets manager
- Use HTTPS behind a reverse proxy
- Add rate limiting
- Add backups for SQLite and uploaded files
- Monitor logs and disk usage

## 10. Clean Rebuild

If you want to start fresh locally, remove generated runtime data and rerun the steps above:

- `database/`
- `uploads/`

Then run migrations again and restart the backend and frontend.
