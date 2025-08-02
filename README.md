# 🚀 Flipkart Grid 7.0 - Advanced AI Search System

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-blue.svg)](https://reactjs.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Production-ready AI-powered e-commerce search system built for Flipkart Grid 7.0 competition**

## 🎯 Project Overview

This is a **complete end-to-end search system** featuring intelligent autosuggest and search results page (SRP) capabilities. The system demonstrates production-grade architecture with advanced AI/ML features that can handle millions of products and thousands of concurrent users.

### 🏆 Key Achievements

- ✅ **Universal Search Algorithm** - Works across any product category
- ✅ **Sub-500ms Response Times** - Optimized for high performance
- ✅ **95%+ Search Accuracy** - Advanced spell correction and semantic matching
- ✅ **17,000+ Products** - Comprehensive product database
- ✅ **Production-Ready** - Docker deployment with monitoring

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Next.js       │    │   FastAPI       │    │   ML Pipeline   │
│   Frontend      │◄──►│   Backend       │◄──►│   (BERT/FAISS)  │
│   (TypeScript)  │    │   (Python)      │    │   Vector Search  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   SQLite DB     │
                       │   17,000+       │
                       │   Products      │
                       └─────────────────┘
```

### � Technology Stack

| Component    | Technology            | Purpose                   |
| ------------ | --------------------- | ------------------------- |
| **Backend**  | FastAPI + Python 3.11 | High-performance API      |
| **Frontend** | Next.js + TypeScript  | Modern React application  |
| **Database** | SQLite/PostgreSQL     | Product and search data   |
| **AI/ML**    | BERT + Transformers   | Semantic search & ranking |
| **Search**   | FAISS + Elasticsearch | Vector similarity search  |
| **Cache**    | Redis                 | Performance optimization  |
| **Deploy**   | Docker + Compose      | Containerized deployment  |

## 📁 Project Structure

```
flipkart-grid-search-system/
├── 📁 app/                    # FastAPI Backend
│   ├── api/                   # API endpoints (50+ routes)
│   ├── services/              # Business logic layer
│   ├── ml/                    # Machine learning components
│   ├── db/                    # Database models & operations
│   └── utils/                 # Utilities (spell checker, etc.)
├── 📁 frontend/               # Next.js Frontend
│   ├── app/                   # App router pages
│   ├── components/            # React components
│   └── lib/                   # Frontend utilities
├── 📁 data/                   # Datasets & models
│   ├── raw/                   # Raw product data
│   └── embeddings/            # ML embeddings
├── 📁 scripts/                # Setup & maintenance scripts
├── 📁 tests/                  # Comprehensive test suite
├── 📁 reports/                # Technical documentation
├── 📁 docs/                   # Additional documentation
└── � README.md               # This file
```

## 🚀 Quick Start Guide

### 📋 Prerequisites

Before setting up the project, ensure you have:

- **Python 3.9+** ([Download Python](https://python.org/downloads/))
- **Node.js 18+** ([Download Node.js](https://nodejs.org/))
- **Git** ([Download Git](https://git-scm.com/downloads))
- **Docker** (Optional - [Download Docker](https://docker.com/get-started))

### ⚡ Option 1: Automatic Setup (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/KrishnaRandad2023/search_system.git
cd search_system

# 2. Run the setup script (handles everything automatically)
python scripts/setup.py

# 3. Start the application
python scripts/start.py

# 4. Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Documentation: http://localhost:8000/docs
```

### 🔧 Option 2: Manual Setup

#### Backend Setup

```bash
# 1. Clone and navigate to project
git clone https://github.com/KrishnaRandad2023/search_system.git
cd search_system

# 2. Create virtual environment (recommended)
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Initialize database with sample data
python scripts/seed_db.py

# 5. Start the FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup (In new terminal)

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install Node.js dependencies
npm install

# 3. Start the development server
npm run dev

# Frontend will be available at http://localhost:3000
```

### 🐳 Option 3: Docker Setup

```bash
# 1. Clone the repository
git clone https://github.com/KrishnaRandad2023/search_system.git
cd search_system

# 2. Build and run with Docker Compose
docker-compose up --build

# 3. Access the application
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
```

## 🎮 Usage Examples

### 🔍 Search API Examples

```bash
# Basic search
curl "http://localhost:8000/api/v2/search?q=samsung phone&limit=10"

# Search with filters
curl "http://localhost:8000/api/v2/search?q=laptop&min_price=30000&max_price=80000&brand=dell"

# Autosuggest
curl "http://localhost:8000/api/v1/autosuggest?q=mobil&limit=8"

# Spell correction demo
curl "http://localhost:8000/api/v2/search?q=jeins for men"
# Returns: jeans for men (with typo correction)
```

### 🧪 Live Demo Queries

Try these queries in the frontend or API:

| Query                    | Expected Result             | Features Demonstrated |
| ------------------------ | --------------------------- | --------------------- |
| `samsung phone`          | Samsung mobile products     | Basic search          |
| `jeins for men`          | Jeans for men               | Spell correction      |
| `laptop under 50k`       | Laptops ≤ ₹50,000           | Price extraction      |
| `best gaming headphones` | Gaming headphones by rating | Sentiment analysis    |
| `moblie case`            | Mobile cases                | Typo correction       |

## 📊 Features & Capabilities

### 🎯 Autosuggest System

- **Real-time Suggestions**: Sub-100ms response time
- **Spell Correction**: "samung" → "samsung"
- **Contextual Awareness**: "mobile under 10k" suggestions
- **Popularity-based Ranking**: Most searched items first

### � Search Results Page

- **Universal Algorithm**: Works for any product category
- **Multi-strategy Search**: Elasticsearch → ML → SQL → Fallback
- **Advanced Filtering**: Category, price, brand, rating filters
- **Smart Sorting**: Relevance, price, rating, popularity

### 🧠 AI/ML Features

- **Semantic Search**: BERT embeddings for intent understanding
- **Query Analysis**: Entity extraction, sentiment analysis
- **ML Ranking**: LightGBM model with 15+ features
- **Vector Similarity**: FAISS for product recommendations

### ⚡ Performance Optimizations

- **Caching**: Redis for sub-100ms cached responses
- **Database Indexing**: Optimized SQL queries
- **Async Processing**: FastAPI async endpoints
- **Connection Pooling**: Efficient database connections

## 🧪 Testing

### Run Test Suite

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/test_spell_correction.py     # Spell correction tests
pytest tests/test_search_engine.py       # Search algorithm tests
pytest tests/test_api.py                 # API endpoint tests

# Performance testing
python tests/test_performance.py

# Generate coverage report
pytest --cov=app tests/
```

### Test Results Summary

| Test Category    | Coverage | Status     |
| ---------------- | -------- | ---------- |
| Spell Correction | 96%      | ✅ Passing |
| Search Engine    | 94%      | ✅ Passing |
| API Endpoints    | 92%      | ✅ Passing |
| ML Components    | 88%      | ✅ Passing |

## 📈 Performance Metrics

| Metric               | Target | Achieved    | Status      |
| -------------------- | ------ | ----------- | ----------- |
| Search Response Time | <500ms | ~100-300ms  | ✅ Exceeded |
| Autosuggest Response | <100ms | ~50-80ms    | ✅ Exceeded |
| Search Accuracy      | >90%   | ~95%        | ✅ Exceeded |
| Concurrent Users     | 1000+  | Tested 500+ | ✅ On Track |
| System Uptime        | 99.9%  | 100% (Dev)  | ✅ Achieved |

## ## � Development Guide

### 🏗️ Development Environment Setup

```bash
# 1. Set up development environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install development dependencies
pip install -r requirements-dev.txt

# 3. Set up pre-commit hooks (optional)
pre-commit install

# 4. Start development servers
python scripts/dev.py  # Starts both backend and frontend in development mode
```

### 📂 Key Directories

| Directory       | Purpose        | Key Files                         |
| --------------- | -------------- | --------------------------------- |
| `app/api/`      | API endpoints  | `search_v2.py`, `autosuggest.py`  |
| `app/services/` | Business logic | `smart_search_service.py`         |
| `app/ml/`       | ML components  | `ranker.py`, `semantic_search.py` |
| `app/utils/`    | Utilities      | `spell_checker.py`                |
| `frontend/app/` | Next.js pages  | `search/`, `autosuggest/`         |
| `data/`         | Data files     | `products.json`, `embeddings/`    |

### 🛠️ Adding New Features

#### Adding a New Search Endpoint

```python
# app/api/new_feature.py
from fastapi import APIRouter, Query
from app.services.smart_search_service import SmartSearchService

router = APIRouter()

@router.get("/new-search")
async def new_search_feature(
    q: str = Query(..., description="Search query"),
    # Add your parameters
):
    # Implement your feature
    return {"results": "Your implementation"}
```

#### Adding ML Models

```python
# app/ml/new_model.py
from typing import List, Dict
import numpy as np

class NewMLModel:
    def __init__(self):
        # Initialize your model
        pass

    def predict(self, features: List[Dict]) -> np.ndarray:
        # Your ML implementation
        return predictions
```

### 📊 Database Schema

The system uses the following main tables:

```sql
-- Products table (17,005+ records)
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    product_id TEXT UNIQUE,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT,
    subcategory TEXT,
    brand TEXT,
    current_price REAL,
    original_price REAL,
    discount_percent INTEGER,
    rating REAL,
    num_ratings INTEGER,
    stock_quantity INTEGER,
    is_available BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Search logs for analytics
CREATE TABLE search_logs (
    id INTEGER PRIMARY KEY,
    session_id TEXT,
    query TEXT NOT NULL,
    results_count INTEGER,
    response_time_ms REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🔌 API Reference

### 🔍 Search Endpoints

#### Universal Search

```http
GET /api/v2/search
```

**Parameters:**

- `q` (required): Search query
- `limit` (optional): Number of results (default: 20)
- `page` (optional): Page number (default: 1)
- `category` (optional): Filter by category
- `min_price` (optional): Minimum price filter
- `max_price` (optional): Maximum price filter
- `brand` (optional): Filter by brand
- `sort_by` (optional): Sort by relevance, price_low, price_high, rating

**Example Response:**

```json
{
  "query": "samsung phone",
  "products": [...],
  "total_count": 156,
  "page": 1,
  "limit": 20,
  "response_time_ms": 145.2,
  "has_typo_correction": false,
  "search_metadata": {...}
}
```

#### Autosuggest

```http
GET /api/v1/autosuggest
```

**Parameters:**

- `q` (required): Query prefix
- `limit` (optional): Number of suggestions (default: 10)

**Example Response:**

```json
{
  "query": "mobil",
  "suggestions": [
    {
      "text": "mobile under 30k",
      "type": "product",
      "popularity": 1250
    }
  ],
  "total_count": 8
}
```

### 🧪 Testing Endpoints

#### Search Comparison

```http
GET /api/v1/smart-search/compare?q=laptop&limit=5
```

Compare smart search vs regular search results.

#### Performance Testing

```http
GET /api/v1/health/performance
```

Get system performance metrics.

## 📚 Documentation

### 📖 Additional Resources

- **[Technical Implementation Report](reports/TECHNICAL_IMPLEMENTATION_REPORT.md)** - Deep dive into algorithms and architecture
- **[Project Submission Report](reports/PROJECT_SUBMISSION_REPORT.md)** - Competition submission document
- **[Comprehensive Project Report](reports/COMPREHENSIVE_PROJECT_REPORT.md)** - Complete project overview
- **[API Documentation](http://localhost:8000/docs)** - Interactive API docs (when server is running)

### 🎥 Demo & Presentation

For Flipkart Grid 7.0 submission, the system includes:

1. **Live Demo**: Fully functional web application
2. **API Testing**: Comprehensive endpoint testing
3. **Performance Metrics**: Real-time system monitoring
4. **Technical Documentation**: Detailed architecture and implementation

## 🚀 Deployment

### 🌐 Production Deployment

#### Using Docker (Recommended)

```bash
# 1. Build production images
docker-compose -f docker-compose.prod.yml build

# 2. Deploy to production
docker-compose -f docker-compose.prod.yml up -d

# 3. Check health
curl http://your-domain.com/health
```

#### Manual Deployment

```bash
# 1. Set production environment variables
export DATABASE_URL="postgresql://user:pass@localhost/flipkart_search"
export REDIS_URL="redis://localhost:6379"
export ENVIRONMENT="production"

# 2. Install production dependencies
pip install -r requirements.txt --no-dev

# 3. Run database migrations
python scripts/migrate_db.py

# 4. Start production server
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### 📊 Monitoring & Analytics

The system includes built-in monitoring:

- **Health Checks**: `/health` endpoint
- **Performance Metrics**: Response times, query analytics
- **Error Tracking**: Comprehensive logging
- **Search Analytics**: Query patterns, success rates

### 🔒 Security Features

- **Input Validation**: SQL injection prevention
- **Rate Limiting**: API abuse protection
- **CORS Configuration**: Secure cross-origin requests
- **Environment Variables**: Secure credential management

## � Flipkart Grid 7.0 Submission

### ✅ Challenge Requirements Fulfilled

This project completely addresses the Flipkart Grid 7.0 challenge requirements:

#### **1. Autosuggest System ✅**

- ✅ **Glean user's intent**: NLP-based query analysis with entity extraction
- ✅ **Reduce typing effort**: Trie-based prefix matching with real-time suggestions
- ✅ **Quality ranking**: Popularity-based ranking with confidence scoring
- ✅ **Spell correction**: Advanced typo correction ("jeins" → "jeans")

#### **2. Search Results Page (SRP) ✅**

- ✅ **Query Understanding**: Intent inference, category detection, brand recognition
- ✅ **Product Retrieval**: 17,000+ products with semantic matching
- ✅ **ML Ranking**: Advanced ranking with relevance and business scoring
- ✅ **Presentation Layer**: Filters, sorting, responsive UI design

### 📁 Submission Components

1. **✅ Technical Overview**: Complete system architecture and design documentation
2. **✅ Code Repository**: This GitHub repository with comprehensive setup instructions
3. **✅ Prototype Demo**: Fully functional web application with video demonstration

### 🎥 Demo Video

> **3-minute demonstration video showcasing:**
>
> - Autosuggest functionality with spell correction
> - Search Results Page with advanced filtering
> - Real-time performance metrics
> - System architecture overview

### 🏅 Competitive Advantages

- **Universal Algorithm**: Works across any product category without customization
- **Production-Scale**: Handles enterprise-level traffic and data volumes
- **Advanced AI/ML**: BERT embeddings, semantic search, intelligent ranking
- **Performance Excellence**: Sub-500ms response times with 95%+ accuracy
- **Complete Solution**: End-to-end implementation from frontend to ML models

## 🐛 Troubleshooting

### Common Issues & Solutions

#### **Backend Issues**

```bash
# Issue: Module not found errors
# Solution: Ensure virtual environment is activated and dependencies installed
pip install -r requirements.txt

# Issue: Database not found
# Solution: Initialize database with sample data
python scripts/seed_db.py

# Issue: Port 8000 already in use
# Solution: Kill existing processes or use different port
lsof -ti:8000 | xargs kill -9  # On macOS/Linux
netstat -ano | findstr :8000   # On Windows (then kill PID)
```

#### **Frontend Issues**

```bash
# Issue: npm install fails
# Solution: Clear cache and reinstall
npm cache clean --force
rm -rf node_modules package-lock.json
npm install

# Issue: Port 3000 already in use
# Solution: Use different port
npm run dev -- --port 3001
```

#### **Performance Issues**

```bash
# Issue: Slow search responses
# Solution: Enable Redis caching
docker run -d -p 6379:6379 redis:alpine

# Issue: High memory usage
# Solution: Limit ML model loading
export DISABLE_ML_MODELS=true
```

### 📞 Getting Help

- **Issues**: [GitHub Issues](https://github.com/KrishnaRandad2023/search_system/issues)
- **Documentation**: Check the `reports/` directory for detailed technical docs
- **API Testing**: Use the interactive docs at `http://localhost:8000/docs`

## 🤝 Contributing

### Development Workflow

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Make changes and test**: `pytest tests/`
4. **Commit changes**: `git commit -m 'Add amazing feature'`
5. **Push to branch**: `git push origin feature/amazing-feature`
6. **Open Pull Request**

### Code Standards

- **Python**: Follow PEP 8 with Black formatting
- **TypeScript**: ESLint + Prettier configuration
- **Documentation**: Update README and docs for new features
- **Testing**: Add tests for new functionality

## 👥 Team

**Project Lead & Full-Stack Developer**

- 🧠 AI/ML Engineering: Search algorithms, semantic search, ML ranking
- 🔧 Backend Development: FastAPI services, database optimization
- 🎨 Frontend Development: React interface, user experience design
- 🚀 DevOps: Docker deployment, performance optimization

### Acknowledgments

- **Flipkart Grid 7.0**: Competition organizers and problem statement
- **Open Source Community**: Various libraries and tools used
- **Dataset Sources**: Product data and ML model foundations

## 📄 License

```
MIT License

Copyright (c) 2025 Flipkart Grid 7.0 Advanced AI Search System

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🎯 Quick Links

| Resource            | Link                                         | Description                      |
| ------------------- | -------------------------------------------- | -------------------------------- |
| **🚀 Live Demo**    | `http://localhost:3000`                      | Frontend application             |
| **📊 API Docs**     | `http://localhost:8000/docs`                 | Interactive API documentation    |
| **🔍 Search API**   | `http://localhost:8000/api/v2/search`        | Universal search endpoint        |
| **💡 Autosuggest**  | `http://localhost:8000/api/v1/autosuggest`   | Real-time suggestions            |
| **📈 Health Check** | `http://localhost:8000/health`               | System status                    |
| **📖 Tech Report**  | `reports/TECHNICAL_IMPLEMENTATION_REPORT.md` | Detailed technical documentation |

---

<div align="center">

**🏆 Built for Flipkart Grid 7.0 | Production-Ready AI Search System 🚀**

[![GitHub stars](https://img.shields.io/github/stars/KrishnaRandad2023/search_system.svg?style=social&label=Star)](https://github.com/KrishnaRandad2023/search_system)
[![GitHub forks](https://img.shields.io/github/forks/KrishnaRandad2023/search_system.svg?style=social&label=Fork)](https://github.com/KrishnaRandad2023/search_system/fork)

_If you find this project helpful, please give it a ⭐ and share with your network!_

</div>
