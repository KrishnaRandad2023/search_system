# Flipkart Grid 7.0 - AI/ML-Powered E-commerce Search System

## 🚀 Overview

A production-grade, modular e-commerce search system featuring:

- **Intelligent Autosuggest**: Real-time query completion with typo correction
- **Semantic Search**: BERT-powered product discovery
- **ML-Driven Ranking**: Personalized search result optimization
- **Modern UI**: React-based interface mimicking Flipkart's design

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI       │    │   ML Pipeline   │
│   (React)       │◄──►│   Backend       │◄──►│   (BERT/Vector) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Database      │
                       │ (SQLite/Postgres)│
                       └─────────────────┘
```

## 🛠️ Tech Stack

- **Backend**: FastAPI, Python 3.9+
- **Frontend**: React, TypeScript, Tailwind CSS
- **ML/AI**: BERT, Sentence Transformers, FAISS
- **Database**: SQLite (dev), PostgreSQL (prod)
- **Search**: BM25, TF-IDF, Vector Similarity
- **Deployment**: Docker, Docker Compose

## 📁 Project Structure

```
flipkart_search_system/
├── app/                    # FastAPI backend
├── frontend/              # React frontend
├── data/                  # Datasets and models
├── scripts/               # Data processing scripts
├── configs/               # Configuration files
├── tests/                 # Test suites
├── notebooks/             # Jupyter experiments
└── docs/                  # Documentation
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- Docker (optional)

### Setup

1. **Clone and navigate**:

   ```bash
   cd flipkart_search_system
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Setup database**:

   ```bash
   python scripts/seed_db.py
   ```

4. **Run backend**:

   ```bash
   uvicorn app.main:app --reload
   ```

5. **Run frontend**:

   ```bash
   cd frontend
   npm install && npm start
   ```

6. **Access the application**:
   - Frontend: http://localhost:3000
   - API Docs: http://localhost:8000/docs

## 🔧 Development

### Data Sources

- **Products**: Generated from public datasets + web scraping
- **Autosuggest**: N-gram analysis of product titles
- **ML Models**: Pretrained BERT + custom ranking models

### Key Features

- ⚡ Sub-100ms autosuggest response
- 🧠 Semantic search with 85%+ relevance
- 📊 Real-time analytics and logging
- 🎯 Personalized result ranking
- 🔍 Typo-tolerant search

## 📊 Performance Metrics

| Feature             | Target | Achieved |
| ------------------- | ------ | -------- |
| Autosuggest Latency | <100ms | TBD      |
| Search Relevance    | >85%   | TBD      |
| System Uptime       | 99.9%  | TBD      |

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_search.py -v

# Performance testing
python tests/test_performance.py
```

## 📚 Documentation

- [API Reference](docs/API_REFERENCE.md)
- [System Architecture](docs/SYSTEM_ARCHITECTURE.md)
- [ML Pipelines](docs/ML_PIPELINES.md)
- [Demo Setup](docs/DEMO_SETUP.md)

## 🎯 Flipkart Grid 7.0 Submission

This project addresses the Grid 7.0 challenge requirements:

- ✅ Real-time autosuggest functionality
- ✅ Intelligent search result pages
- ✅ ML-powered ranking and recommendations
- ✅ Scalable, production-ready architecture

## 👥 Team

- **Your Name**: Full-stack development, ML engineering
- **Team Member 2**: Frontend, UI/UX
- **Team Member 3**: Backend, DevOps

## 📄 License

MIT License - Built for Flipkart Grid 7.0
