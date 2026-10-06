# 🧠 Enterprise Knowledge Intelligence Assistant

> **An authenticated, document-grounded enterprise RAG system for querying internal organizational knowledge using natural language.**

The **Enterprise Knowledge Intelligence Assistant** is an AI-powered knowledge retrieval system designed to help employees interact with internal company documents through natural-language questions.

Instead of manually searching through policies, manuals, reports, and other organizational documents, users can ask questions such as:

> **"What are the password requirements?"**

The system retrieves relevant information from authorized documents and generates a **grounded answer with source information**, ensuring that the response is based on the organization's available knowledge rather than unsupported model knowledge.

---

## ✨ Key Features

| Area | Capability |
|---|---|
| 📄 **Document Ingestion** | PDF and TXT loading, text extraction, cleaning, and configurable chunking |
| 🧩 **Embeddings** | Sentence Transformers using `all-MiniLM-L6-v2` with 384-dimensional embeddings |
| 🔎 **Semantic Search** | PostgreSQL + pgvector similarity search |
| 🔐 **Authentication** | JWT authentication with OAuth2 password flow |
| 🛡️ **Authorization** | Role-based access control with document-level access filtering |
| 🤖 **RAG** | Retrieval-Augmented Generation using authorized document context |
| 📚 **Grounded Answers** | Answers generated from retrieved organizational content with source information |
| 🧠 **Local AI** | Local embedding and generation models for development without paid API credits |
| 🔄 **Provider Abstraction** | Pluggable embedding and LLM providers |
| ⚡ **Caching** | Redis-based caching layer |
| 🌐 **API** | FastAPI REST API with interactive Swagger/OpenAPI documentation |
| 🐳 **Infrastructure** | Docker Compose with PostgreSQL/pgvector and Redis |
| 🧪 **Testing & Evaluation** | Unit/integration tests and retrieval/generation evaluation structure |
| 📊 **Logging** | Structured application logging |

---

# 🏗️ Architecture

The system follows a layered architecture separating authentication, document ingestion, retrieval, authorization, generation, and API concerns.

```text
                         ┌──────────────────────┐
                         │      Client/User     │
                         └───────────┬──────────┘
                                     │
                                     ▼
                         ┌──────────────────────┐
                         │    FastAPI REST API  │
                         └───────────┬──────────┘
                                     │
                                     ▼
                         ┌──────────────────────┐
                         │ JWT Authentication   │
                         │ + RBAC / ACL         │
                         └───────────┬──────────┘
                                     │
                                     ▼
                         ┌──────────────────────┐
                         │     Query Service    │
                         └───────────┬──────────┘
                                     │
                                     ▼
                         ┌──────────────────────┐
                         │   Query Embedding    │
                         │ Sentence Transformers│
                         └───────────┬──────────┘
                                     │
                                     ▼
                  ┌────────────────────────────────────┐
                  │       PostgreSQL + pgvector        │
                  │                                    │
                  │     Semantic Vector Retrieval      │
                  └─────────────────┬──────────────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Authorized Context   │
                         │ Filtering / Retrieval│
                         └───────────┬──────────┘
                                     │
                                     ▼
                         ┌──────────────────────┐
                         │      Local LLM       │
                         │      FLAN-T5         │
                         └───────────┬──────────┘
                                     │
                                     ▼
                         ┌──────────────────────┐
                         │ Grounded Answer +    │
                         │ Sources / Citations  │
                         └──────────────────────┘
```

---

# 📥 Document Ingestion Pipeline

Documents follow a separate ingestion pipeline before becoming searchable.

```text
PDF / TXT
   │
   ▼
Document Loader
   │
   ▼
Text Extraction
   │
   ▼
Text Cleaning
   │
   ▼
Configurable Chunking
   │
   ▼
Sentence Transformer
   │
   ▼
384-Dimensional Embedding
   │
   ▼
PostgreSQL + pgvector
```

This allows the query pipeline to perform semantic retrieval against previously processed organizational knowledge.

---

# 🔐 Security Model

Security is treated as part of the retrieval architecture rather than something delegated to the LLM.

### Authentication

Users authenticate through:

- JWT access tokens
- OAuth2 password flow
- Protected API endpoints

### Roles

The current development setup supports:

```text
ADMIN
ENGINEER
EMPLOYEE
```

### Authorization

Documents contain access-level metadata such as:

```text
PUBLIC
INTERNAL
ENGINEERING
SECURITY
ADMIN
```

The retrieval layer evaluates the requesting user's permissions before constructing the context sent to the generation layer.

### Security Boundary

The important design principle is:

```text
User
  ↓
Authentication
  ↓
Authorization
  ↓
Semantic Retrieval
  ↓
Authorized Context
  ↓
LLM
```

The LLM is **not treated as a security boundary**.

Unauthorized document content should therefore never become part of the LLM context.

Secrets are loaded through environment configuration and should never be committed to the repository.

---

# 🧠 RAG Pipeline

For a user query, the system follows this flow:

```text
User Question
     │
     ▼
Authentication
     │
     ▼
Authorization
     │
     ▼
Query Embedding
     │
     ▼
pgvector Similarity Search
     │
     ▼
Authorized Retrieved Chunks
     │
     ▼
Context Construction
     │
     ▼
Local LLM Generation
     │
     ▼
Grounded Answer
     │
     ▼
Sources / Citations
```

This architecture separates **retrieval** from **generation**, making the system easier to test, secure, and extend.

---

# 🛠️ Technology Stack

## Backend

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- Async PostgreSQL
- REST APIs

## 🤖 AI / RAG

- Sentence Transformers
- `all-MiniLM-L6-v2`
- 384-dimensional embeddings
- Hugging Face Transformers
- `google/flan-t5-small`
- Retrieval-Augmented Generation
- Prompt-based grounded generation
- Embedding provider abstraction
- LLM provider abstraction

## 🗄️ Data Layer

- PostgreSQL
- pgvector
- Redis

## 🔐 Security

- JWT
- OAuth2 password flow
- Role-Based Access Control
- Document-level authorization

## 🐳 Infrastructure

- Docker
- Docker Compose
- PostgreSQL/pgvector container
- Redis container
- Structured application logging

---

# 📁 Project Structure

```text
enterprise-knowledge-assistant/
│
├── app/
│   ├── api/
│   │   ├── auth.py
│   │   ├── documents.py
│   │   └── query.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── logging.py
│   │
│   ├── db/
│   │   ├── database.py
│   │   ├── models.py
│   │   └── vector_store.py
│   │
│   ├── ingestion/
│   │   ├── loader.py
│   │   ├── cleaner.py
│   │   ├── chunker.py
│   │   └── embeddings.py
│   │
│   ├── retrieval/
│   │   ├── retriever.py
│   │   ├── access_control.py
│   │   └── reranker.py
│   │
│   ├── rag/
│   │   ├── prompts.py
│   │   ├── chain.py
│   │   └── citations.py
│   │
│   ├── services/
│   │   ├── document_service.py
│   │   ├── query_service.py
│   │   └── cache_service.py
│   │
│   └── schemas/
│       ├── auth.py
│       ├── documents.py
│       └── query.py
│
├── data/
│   ├── documents/
│   └── processed/
│
├── evaluation/
│   ├── dataset.json
│   ├── evaluate_retrieval.py
│   ├── evaluate_generation.py
│   └── regression_tests.py
│
├── tests/
│   ├── test_auth.py
│   ├── test_ingestion.py
│   ├── test_retrieval.py
│   ├── test_rag.py
│   └── test_api.py
│
├── scripts/
│   ├── seed_database.py
│   └── ingest_documents.py
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
├── LICENSE
└── README.md
```

---

# 🚀 Quick Start

## 1. Clone the repository

```bash
git clone <repository-url>
cd enterprise-knowledge-assistant
```

## 2. Create a virtual environment

```bash
python -m venv .venv
```

### Windows — PowerShell

```powershell
.venv\Scripts\Activate.ps1
```

### Linux / macOS

```bash
source .venv/bin/activate
```

---

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure environment variables

Copy:

```text
.env.example
```

to:

```text
.env
```

Windows:

```powershell
Copy-Item .env.example .env
```

Linux/macOS:

```bash
cp .env.example .env
```

Configure the required local settings in `.env`.

> ⚠️ **Never commit `.env` to Git.**  
> Keep API keys, database passwords, JWT secrets, and other credentials outside version control.

---

# 🐳 Start Infrastructure

Start PostgreSQL/pgvector and Redis:

```bash
docker compose up -d db redis
```

Verify containers:

```bash
docker compose ps
```

---

# 👤 Seed Demo Users

Run:

```bash
python -m scripts.seed_database
```

The development seed creates users for the supported roles.

> ⚠️ These credentials are intended only for local development/demo environments. Change them before any real deployment.

---

# 📄 Ingest Documents

Place supported files into:

```text
data/documents/
```

Supported formats:

```text
.pdf
.txt
```

Then run:

```bash
python -m scripts.ingest_documents
```

The ingestion process:

1. Loads the document
2. Extracts text
3. Cleans the text
4. Splits the content into chunks
5. Generates embeddings
6. Stores document metadata
7. Stores embeddings in PostgreSQL/pgvector

---

# ▶️ Start the API

Run:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:

```text
http://localhost:8000
```

### 📚 Swagger UI

```text
http://localhost:8000/docs
```

### Health Check

```text
http://localhost:8000/health
```

---

# 🔌 API Overview

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/auth/register` | Register a user |
| `POST` | `/api/v1/auth/login` | Obtain JWT using OAuth2 password flow |
| `GET` | `/api/v1/auth/me` | Get current authenticated user |
| `POST` | `/api/v1/documents/upload` | Upload PDF/TXT document |
| `GET` | `/api/v1/documents` | List documents visible to the user |
| `GET` | `/api/v1/documents/{id}` | Retrieve document metadata |
| `POST` | `/api/v1/query` | Ask a natural-language question |
| `GET` | `/health` | Health check |

Protected endpoints require a valid Bearer token.

---

# 💬 Example Query

After authentication, a user can submit:

```json
{
  "question": "What are the password requirements?"
}
```

The system performs semantic retrieval against authorized documents and generates a grounded response.

---

# ✅ Verified End-to-End Demo

The complete pipeline has been tested using:

```text
password-security-policy.txt
```

The document contains the organization's password security requirements.

The database was verified after ingestion with:

```text
1 document
1 document chunk
384-dimensional embedding
```

### Query

```json
{
  "question": "What are the password requirements?"
}
```

### Actual Result

The system successfully returned a grounded response stating that:

> All employees must use passwords containing at least 12 characters, including uppercase letters, lowercase letters, numbers, and special characters.

The response also returned:

- Source information
- Access level
- Similarity information
- `context_used`
- Cache status

This verified the complete flow:

```text
Document
   ↓
Ingestion
   ↓
Embedding
   ↓
pgvector
   ↓
Semantic Retrieval
   ↓
Authorization
   ↓
Context
   ↓
Local LLM
   ↓
Grounded Answer
   ↓
Source Information
```

---

# 🧪 Testing

Run the test suite with:

```bash
pytest
```

The project contains tests covering areas including:

- Authentication
- Ingestion utilities
- Text cleaning
- Chunking
- Retrieval
- Access-control mapping
- RAG prompt construction
- Citation generation
- API health checks

The `evaluation/` directory also contains the structure for evaluating retrieval relevance, generation quality, and regression behavior against a fixed dataset.

---

# ⚙️ Engineering Decisions

### 🗄️ Why PostgreSQL + pgvector?

Keeping vector search inside PostgreSQL allows document metadata, permissions, and embeddings to remain within the same primary data layer while avoiding the operational overhead of a separate vector database.

### 🔌 Why Provider Abstraction?

Embedding and generation providers are isolated behind service abstractions.

This makes it possible to change models or providers without rewriting the API, retrieval, or authorization layers.

### 🧠 Why Local Models?

The development setup uses local models so the complete RAG workflow can be demonstrated without depending on paid external inference APIs.

### 🔐 Why Authorization Before Generation?

Authorization is enforced before context construction.

This prevents unauthorized document content from being passed into the generation layer.

### 🧩 Why Chunking?

Documents are divided into smaller semantic units so retrieval can identify relevant portions instead of passing entire documents into the model.

### ⚡ Why Redis?

Redis provides a caching layer for frequently repeated operations and creates a path toward reducing unnecessary repeated computation in higher-traffic deployments.

---

# 📊 Evaluation & Quality

The project includes an evaluation structure for measuring:

```text
Retrieval Relevance
        +
Generation Quality
        +
Grounding
        +
Access-Control Regression
```

A particularly important invariant is:

> **Unauthorized content must never enter the LLM context.**

This makes authorization behavior part of the system's correctness criteria rather than treating it as a separate application concern.

---

# 🛡️ Security Considerations

The project follows several security-oriented design principles:

- JWT-based authentication
- Role-based authorization
- Document-level access filtering
- Authorization before context construction
- Environment-based secret configuration
- No secrets committed to source control
- LLM treated as an untrusted generation component rather than a security boundary

For production deployment, additional security controls would be required.

---

# 🔮 Production Hardening / Future Improvements

The following are **not currently implemented** and represent potential production improvements:

- Managed PostgreSQL deployment
- Connection pooling and database scaling
- Higher-capacity embedding models
- Cross-encoder reranking
- Hybrid BM25 + vector retrieval
- Streaming responses
- SSO / OIDC integration
- Enterprise secrets management
- Distributed ingestion workers
- Document versioning
- Automated evaluation in CI
- Stronger prompt-injection defenses
- API rate limiting
- Production Redis configuration
- Distributed tracing
- Advanced observability
- CI/CD pipelines
- Horizontal API scaling

---

# 🎯 Why This Project Matters

This project demonstrates practical experience across both **AI engineering and backend engineering**.

### AI / GenAI

- RAG architecture
- Embeddings
- Semantic search
- Vector databases
- Grounded generation
- Prompt engineering
- Retrieval evaluation
- Provider abstraction

### Backend

- Python
- FastAPI
- Async programming
- PostgreSQL
- SQLAlchemy
- Redis
- REST APIs
- Authentication
- Authorization

### Infrastructure

- Docker
- Docker Compose
- pgvector
- Structured logging
- Environment-based configuration

### Engineering

- Layered architecture
- Separation of concerns
- Security-aware retrieval
- Automated testing
- Evaluation-driven development
- Extensible AI components

---

# How to Explain This Project in an Interview

### 30-second explanation

> **"I built an enterprise document-grounded knowledge assistant that allows authenticated employees to query internal organizational documents using natural language. The system handles document ingestion, chunking, embedding generation, semantic retrieval using PostgreSQL and pgvector, role-based access control, and grounded answer generation with source information."**

### Strong technical talking points

**1. Security boundary**

Authorization happens before context construction, so the LLM does not receive documents the user is not allowed to access.

**2. Local-first AI architecture**

Sentence Transformers and FLAN-T5 allow the complete RAG pipeline to run locally during development without requiring paid inference APIs.

**3. Provider abstraction**

The embedding and generation layers are isolated so model providers can be changed without redesigning the retrieval or API layers.

**4. pgvector**

Vector search is colocated with document metadata and permissions in PostgreSQL, simplifying the data architecture.

**5. Evaluation mindset**

The project includes retrieval, generation, and regression evaluation structures rather than treating RAG quality as a purely subjective output.

**6. Clean architecture**

The application separates:

```text
API
 ↓
Services
 ↓
Retrieval
 ↓
RAG
 ↓
Data Layer
```

This makes individual components easier to test and evolve.

---

# Project Status

**Status: Functional local RAG prototype / portfolio project**

The core end-to-end workflow has been verified:

```text
✅ Document ingestion
✅ Text processing
✅ Local embeddings
✅ PostgreSQL + pgvector
✅ Semantic retrieval
✅ JWT authentication
✅ Role-based authorization
✅ Authorized context construction
✅ Local LLM generation
✅ Grounded answer
✅ Source information
✅ FastAPI API
✅ Swagger documentation
✅ Docker infrastructure
```

---

## Built With

**Python · FastAPI · PostgreSQL · pgvector · Redis · Sentence Transformers · Hugging Face Transformers · FLAN-T5 · SQLAlchemy · Docker**

---
If you find this project useful, consider giving the repository a star.