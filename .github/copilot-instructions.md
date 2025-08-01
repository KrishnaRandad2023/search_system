<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# Flipkart Search System - Copilot Instructions

## Project Overview

This is a production-grade AI/ML-powered e-commerce search system built for Flipkart Grid 7.0. The system includes intelligent autosuggest, semantic search, and ML-driven ranking capabilities.

## Architecture

- **Backend**: FastAPI with Python 3.9+
- **Database**: SQLite (dev), PostgreSQL (prod)
- **ML/AI**: BERT embeddings, FAISS vector search, sentence-transformers
- **Frontend**: React with TypeScript (planned)
- **Search**: BM25, TF-IDF, vector similarity

## Code Standards

- Follow PEP 8 for Python code
- Use type hints consistently
- Write docstrings for all functions and classes
- Use Pydantic models for API schemas
- Implement proper error handling with HTTP exceptions

## Key Components

1. **API Layer** (`app/api/`): FastAPI routers for different endpoints
2. **Database** (`app/db/`): SQLAlchemy models and database operations
3. **Schemas** (`app/schemas/`): Pydantic models for request/response
4. **ML Components** (`app/ml/`): Machine learning pipelines and models
5. **Services** (`app/services/`): Business logic layer

## Development Guidelines

- Use async/await for database operations when possible
- Implement proper logging with loguru
- Add comprehensive error handling
- Write unit tests for all new features
- Follow the existing project structure

## ML/AI Focus Areas

- Semantic search with BERT embeddings
- Real-time autosuggest with Trie structures
- Product ranking with multiple signals
- Typo correction and query understanding

## Performance Requirements

- Autosuggest: <100ms response time
- Search: <500ms response time
- Support for 1000+ concurrent users

## Deployment

- Containerized with Docker
- Production-ready with proper monitoring
- Scalable architecture for high traffic
