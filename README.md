# CrimeGPT - AI-Powered Investigation Operating System

An intelligent investigation management platform that assists police officers from complaint registration to generating court-ready investigation packages.

## Architecture

- **Frontend**: React + Vite + Tailwind CSS + Framer Motion
- **Backend**: FastAPI + SQLAlchemy + Alembic
- **AI**: Gemini 2.5 Flash + LangGraph + LangChain
- **Vector DB**: Qdrant (legal RAG)
- **Database**: PostgreSQL with pgvector
- **OCR**: Tesseract
- **Vision**: YOLOv8
- **Speech**: Whisper
- **Documents**: python-docx

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 20+
- Python 3.11+

### Setup

1. Clone and configure:
```bash
cp .env.example .env
# Edit .env with your GEMINI_API_KEY
```

2. Start services:
```bash
docker-compose up -d
```

3. Access:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/docs
- Qdrant UI: http://localhost:6333/dashboard

### Local Development (without Docker)

Backend:
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

## Multi-Agent System

| Agent | Role |
|-------|------|
| Case Intake | Extracts structured data from complaints |
| Investigation | Recommends next investigative steps |
| Legal RAG | Retrieves BNS/BNSS/BSA provisions |
| Document Gen | Generates FIR, chargesheet, memos |
| Evidence Analysis | OCR + object detection on evidence |
| Translation | Hindi/English translation |
| Case Diary | Maintains investigation diary |

## Legal Document Generation

- First Information Report (FIR)
- Charge Sheet
- Seizure Memo
- Medical Examination Letter
- Court Letter
- Arrest Memo

## Security

- JWT authentication with refresh tokens
- Role-Based Access Control (Admin/Inspector/Sub-Inspector/Constable)
- Audit logging
- Input validation and prompt injection mitigation
- Secure file upload with size/type restrictions

## RAG Pipeline

Place legal documents (BNS, BNSS, BSA PDFs/TXT) in `data/legal_docs/` and the ingestion pipeline will:
1. Extract text
2. Chunk into passages
3. Generate BGE embeddings
4. Store in Qdrant for semantic retrieval

## API Endpoints

- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login
- `GET/POST /api/cases/` - List/create cases
- `GET/PUT /api/cases/{id}` - Get/update case
- `POST /api/evidence/upload/{case_id}` - Upload evidence
- `POST /api/documents/generate/{case_id}` - Generate document
- `POST /api/agents/intake` - AI case intake
- `POST /api/agents/investigate` - AI investigation recommendations
- `POST /api/agents/legal-query` - Legal provision query
