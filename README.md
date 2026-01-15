# Log Error Resolver

**Enterprise AI-powered Log Error Resolution System using Retrieval-Augmented Generation (RAG)**

A production-grade FastAPI application that ingests application and infrastructure logs, detects recurring error patterns using vector embeddings, and generates actionable troubleshooting insights using RAG with LLM via OpenRouter.

---

## 🎯 Project Overview

The **Log Error Resolver** is a comprehensive DevOps tool designed to:

- **Ingest** structured and unstructured application logs
- **Parse and normalize** logs for consistent processing
- **Detect patterns** using vector embeddings and similarity search (ChromaDB)
- **Generate resolutions** using Retrieval-Augmented Generation (RAG) with LLM
- **Provide actionable insights** with root cause analysis and recommended fixes

---

## 🏗️ Architecture

### System Architecture

```
┌─────────────┐
│   FastAPI   │
│   REST API  │
└──────┬──────┘
       │
       ├─── Log Ingestion ────┐
       │                      │
       ├─── Analysis ─────────┤
       │                      │
       └─── Resolution ───────┤
                              │
                    ┌─────────▼──────────┐
                    │   Service Layer    │
                    ├────────────────────┤
                    │  • Log Parser      │
                    │  • Embedding       │
                    │  • Vector Store    │
                    │  • Retriever       │
                    │  • RAG Engine      │
                    │  • Resolver        │
                    └─────────┬──────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼──────┐   ┌──────────▼──────────┐   ┌─────▼──────┐
│   SQLite     │   │    ChromaDB         │   │ OpenRouter │
│   (Metadata) │   │    (Vectors)        │   │   (LLM)    │
└──────────────┘   └─────────────────────┘   └────────────┘
```

### RAG Workflow

1. **Log Ingestion**: Logs are parsed and normalized
2. **Embedding Generation**: Text is converted to vector embeddings using SentenceTransformers
3. **Vector Storage**: Embeddings are stored in ChromaDB with metadata
4. **Similarity Search**: When resolving an error, similar historical logs are retrieved
5. **Context Construction**: Similar logs are formatted for LLM context
6. **RAG Generation**: LLM (via OpenRouter) generates resolution with context
7. **Response**: Root cause, recommended fix, and confidence score are returned

---

## 📁 Project Structure

```
log-error-resolver/
│
├── app/
│   ├── main.py                      # FastAPI application entry point
│   │
│   ├── api/
│   │   └── v1/
│   │       └── routes/
│   │           ├── logs.py          # Log ingestion endpoints
│   │           ├── analysis.py      # Log analysis endpoints
│   │           ├── resolution.py    # Error resolution endpoints
│   │           └── health.py        # Health check endpoint
│   │
│   ├── core/
│   │   ├── config.py                # Configuration management
│   │   ├── database.py              # Database setup and sessions
│   │   ├── logging.py               # Logging configuration
│   │   └── exceptions.py            # Custom exception classes
│   │
│   ├── models/
│   │   ├── domain.py                # SQLAlchemy domain models
│   │   └── schemas.py               # Pydantic request/response schemas
│   │
│   ├── services/
│   │   ├── log_parser.py            # Log parsing and normalization
│   │   ├── embedding_service.py     # Embedding generation (SentenceTransformers)
│   │   ├── vector_store.py          # ChromaDB vector store operations
│   │   ├── retriever.py             # Similar log retrieval
│   │   ├── rag_engine.py            # RAG pipeline with OpenRouter
│   │   └── resolver.py              # Resolution orchestration
│   │
│   ├── utils/
│   │   ├── text_cleaner.py          # Text normalization utilities
│   │   ├── similarity.py            # Similarity calculation utilities
│   │   └── helpers.py               # General helper functions
│   │
│   └── tests/
│       ├── unit/                    # Unit tests
│       │   ├── test_log_parser.py
│       │   ├── test_embeddings.py
│       │   └── test_vector_store.py
│       └── integration/             # Integration tests
│           ├── test_log_ingestion_api.py
│           └── test_rag_pipeline.py
│
├── requirements.txt                 # Python dependencies
├── pyproject.toml                   # Pytest and tool configuration
├── .env.example                     # Environment variables template
├── .gitignore                       # Git ignore patterns
└── README.md                        # This file
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- OpenRouter API key ([Get one here](https://openrouter.ai/))

### Installation

1. **Clone the repository** (or extract the project)
   ```bash
   cd log-error-resolver
   ```

2. **Create virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp env.example .env
   # Edit .env and add your OpenRouter API key
   ```

   Edit `.env`:
   ```env
   OPENROUTER_API_KEY=your_actual_api_key_here
   OPENROUTER_MODEL=openai/gpt-4o-mini
   ```

5. **Initialize database** (automatically done on startup)

6. **Run the application**
   ```bash
   python -m app.main
   ```
   
   Or using uvicorn directly:
   ```bash
   uvicorn app.main:app --reload
   ```

7. **Access the API**
   - API Docs (Swagger): http://localhost:8000/docs
   - API Docs (ReDoc): http://localhost:8000/redoc
   - Health Check: http://localhost:8000/api/v1/health

---

## 📚 API Documentation

### Endpoints

#### 1. Health Check
```http
GET /api/v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-01T10:00:00",
  "database": "healthy",
  "vector_store": "healthy (10 embeddings)",
  "embedding_service": "healthy (dim=384)",
  "llm_service": "configured"
}
```

#### 2. Ingest Structured Log
```http
POST /api/v1/logs
Content-Type: application/json

{
  "service_name": "api-service",
  "error_level": "ERROR",
  "error_message": "Connection timeout to database",
  "raw_log": "2024-01-01 10:00:00 ERROR api-service Connection timeout to database",
  "metadata": {
    "environment": "production",
    "version": "1.0.0"
  }
}
```

**Response:**
```json
{
  "id": 1,
  "service_name": "api-service",
  "error_level": "ERROR",
  "error_message": "Connection timeout to database",
  "raw_log": "2024-01-01 10:00:00 ERROR api-service Connection timeout to database",
  "normalized_text": "connection timeout to database",
  "embedding_id": "log_1",
  "metadata": null,
  "created_at": "2024-01-01T10:00:00",
  "updated_at": "2024-01-01T10:00:00"
}
```

#### 3. Ingest Unstructured Log
```http
POST /api/v1/logs/unstructured
Content-Type: application/json

{
  "log_text": "2024-01-01 10:00:00 ERROR [api-service] Connection timeout",
  "service_name": "api-service",
  "metadata": {}
}
```

#### 4. Analyze Log Similarity
```http
GET /api/v1/analysis/{log_id}/similar?top_k=5
```

**Response:**
```json
{
  "log_id": 1,
  "similar_logs": [
    {
      "id": 2,
      "service_name": "api-service",
      "error_level": "ERROR",
      "error_message": "Connection timeout occurred",
      "similarity_score": 0.89,
      "created_at": "2024-01-01T09:00:00"
    }
  ],
  "pattern_detected": true,
  "pattern_frequency": 3
}
```

#### 5. Resolve Error
```http
POST /api/v1/resolve
Content-Type: application/json

{
  "log_id": 1,
  "top_k": 5
}
```

**Or with ad-hoc log text:**
```json
{
  "log_text": "Database connection failed",
  "service_name": "api-service",
  "top_k": 5
}
```

**Response:**
```json
{
  "log_id": 1,
  "root_cause": "Database connection pool exhausted or network connectivity issues",
  "recommended_fix": "1. Check database server status\n2. Verify network connectivity\n3. Review connection pool settings\n4. Check database logs for errors",
  "confidence_score": 0.85,
  "similar_logs": [...],
  "resolution_id": 1,
  "created_at": "2024-01-01T10:00:00"
}
```

---

## 🧪 Testing

### Run All Tests

```bash
pytest
```

### Run with Coverage

```bash
pytest --cov=app --cov-report=html --cov-report=term-missing
```

### Run Unit Tests Only

```bash
pytest app/tests/unit/
```

### Run Integration Tests Only

```bash
pytest app/tests/integration/
```

### Run Specific Test File

```bash
pytest app/tests/unit/test_log_parser.py
```

## 📦 Demo Data Seeding (Optional)

**Note: This is for demo/testing purposes only. Do not run in production.**

The project includes an optional script to seed the database and vector store with realistic synthetic DevOps log entries covering common failure scenarios:

- Database connection timeouts
- Authentication failures
- Disk space exhaustion
- API gateway timeouts
- Memory pressure warnings

### Seed Demo Data

```bash
python -m scripts.seed_demo_data
```

This script will:
- Insert realistic log entries into the SQLite database
- Generate embeddings using the existing embedding service
- Populate ChromaDB with vectors and metadata
- Display a summary of inserted data

**Important Notes:**
- The script does NOT run automatically on application startup
- It is safe to run multiple times (will create duplicate entries)
- Use this for local development, testing, and demonstrations only
- The script uses the same services and database as the main application

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file based on `env.example`:

```env
# OpenRouter Configuration (REQUIRED)
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=openai/gpt-4o-mini
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Application Configuration
APP_NAME=Log Error Resolver
APP_VERSION=1.0.0
DEBUG=False
LOG_LEVEL=INFO

# Database Configuration
DATABASE_URL=sqlite:///./log_resolver.db

# ChromaDB Configuration
CHROMA_PERSIST_DIRECTORY=./chroma_db

# Embedding Configuration
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# RAG Configuration
TOP_K_SIMILAR_LOGS=5
MAX_CONTEXT_LENGTH=4000
TEMPERATURE=0.3

# API Configuration
API_V1_PREFIX=/api/v1
```

### Key Configuration Options

- **OPENROUTER_API_KEY**: Your OpenRouter API key (required)
- **OPENROUTER_MODEL**: LLM model to use (e.g., `openai/gpt-4o-mini`, `anthropic/claude-3-haiku`)
- **EMBEDDING_MODEL**: SentenceTransformer model for embeddings
- **TOP_K_SIMILAR_LOGS**: Number of similar logs to retrieve (default: 5)
- **TEMPERATURE**: LLM temperature for generation (default: 0.3)

---

## 🏛️ Architecture Details

### Clean Architecture

The project follows clean architecture principles:

- **API Layer**: FastAPI routes handle HTTP requests/responses
- **Service Layer**: Business logic and orchestration
- **Data Layer**: SQLAlchemy models and ChromaDB for persistence
- **Utility Layer**: Reusable helper functions

### Key Design Patterns

- **Dependency Injection**: Services are injected via functions (e.g., `get_embedding_service()`)
- **Singleton Pattern**: Global service instances for expensive resources (embeddings, vector store)
- **Repository Pattern**: Abstracted data access through services
- **Factory Pattern**: Service factory functions for lazy initialization

---

## 🔍 How It Works

### 1. Log Ingestion Flow

1. Log arrives via API (structured or unstructured)
2. Log parser extracts: service name, error level, error message
3. Text is normalized (remove timestamps, IPs, UUIDs, etc.)
4. Embedding is generated using SentenceTransformers
5. Embedding is stored in ChromaDB with metadata
6. Log entry is stored in SQLite with reference to embedding

### 2. Error Resolution Flow (RAG)

1. User requests resolution for a log (by ID or text)
2. If by text: parse and normalize the log
3. Generate embedding for the query log
4. Query ChromaDB for similar logs (vector similarity search)
5. Format similar logs as context
6. Construct RAG prompt with current error + similar logs
7. Call LLM via OpenRouter with the prompt
8. Parse LLM response (JSON or structured text)
9. Return: root cause, recommended fix, confidence score
10. Store resolution in database (if log_id provided)

---

## 🛠️ Development

### Code Style

- Follow PEP 8
- Use type hints
- Run black and isort:
  ```bash
  black app/
  isort app/
  ```

### Adding New Features

1. Add domain model in `app/models/domain.py` (if needed)
2. Add schema in `app/models/schemas.py`
3. Implement service in `app/services/`
4. Add API route in `app/api/v1/routes/`
5. Add tests in `app/tests/`

---

## 📝 Notes

- **First Run**: The embedding model will be downloaded on first use (~80MB)
- **Database**: SQLite database is created automatically
- **ChromaDB**: Vector store directory is created automatically
- **API Key**: OpenRouter API key is required for resolution endpoints

---

## 🐛 Troubleshooting

### Common Issues

1. **"OPENROUTER_API_KEY not set"**
   - Ensure `.env` file exists and contains the API key

2. **Embedding model download fails**
   - Check internet connection
   - Model will be downloaded on first use

3. **ChromaDB errors**
   - Ensure write permissions in the project directory
   - Delete `chroma_db/` directory to reset

4. **Database locked errors (SQLite)**
   - Ensure only one instance is running
   - Check for stale database connections

---

## 📄 License

This is an enterprise capstone project. All rights reserved.

---

## 🙏 Acknowledgments

- **FastAPI** for the excellent web framework
- **SentenceTransformers** for embeddings
- **ChromaDB** for vector storage
- **OpenRouter** for LLM API access
- **SQLAlchemy** for database ORM

---

## 📧 Contact

For questions or issues, please refer to the project documentation or create an issue in the repository.
