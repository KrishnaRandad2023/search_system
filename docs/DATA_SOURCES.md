# 📊 Data Sources & Resources Guide

## 🎯 Where to Get Data for Your E-commerce Search System

Since Flipkart's internal data isn't publicly available, here are the **exact sources and methods** to obtain or generate the data you need:

---

## 📦 1. Product Catalog Data

### ✅ **Generated Sample Data (Already Done!)**

Your system now has **5,000 realistic products** with:

- Product IDs, titles, descriptions
- Categories (Electronics, Fashion, Home, Sports, Books)
- Brands, prices, ratings, stock levels
- Bestseller and new arrival flags

**Location**: `data/raw/flipkart_products.csv`

### 🔹 **Alternative Real Data Sources**

```bash
# Option 1: Kaggle Datasets
# - Flipkart Product Dataset (363K products)
# - Amazon Product Dataset
# - Fashion Product Images Dataset

# Option 2: Web Scraping (Legal & Ethical)
# - Flipkart public product pages
# - Amazon product listings
# - Other e-commerce sites
```

---

## 🔍 2. Autosuggest Query Data

### ✅ **Generated from Product Titles (Already Done!)**

Your system has **2,000 autosuggest queries** extracted from:

- N-grams from product titles
- Brand names and categories
- Popular search terms

**Location**: `data/raw/autosuggest_queries.csv`

### 🔹 **Alternative Sources**

```bash
# Real query data sources:
# - Google Trends API
# - Google Keyword Planner
# - SEMrush/Ahrefs keyword data
# - Site search analytics
```

---

## ⭐ 3. Reviews & Ratings Data

### ✅ **Generated Sample Reviews (Already Done!)**

Your system has **1,000 sample reviews** with:

- Review IDs, product IDs, user IDs
- Star ratings (1-5)
- Review text and helpful votes
- Verified purchase flags

**Location**: `data/raw/flipkart_reviews.csv`

---

## 🧠 4. ML Models & Embeddings

### 📥 **Pre-trained Models (Ready to Use)**

```python
# Already configured in your system:
SENTENCE_TRANSFORMER_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
# - 384-dimensional embeddings
# - Optimized for semantic search
# - No training required!
```

### 🚀 **Next Steps for ML Enhancement**

```bash
# Run these commands to add ML capabilities:
python scripts/generate_embeddings.py  # Create BERT embeddings
python scripts/build_faiss_index.py    # Build vector search index
```

---

## 💾 5. Database Setup

### ✅ **SQLite Database (Already Created!)**

Your database now contains:

- **5,000 products** in the `products` table
- **2,000 autosuggest queries** in the `autosuggest_queries` table
- **1,000 reviews** in the `reviews` table

**Location**: `data/db/flipkart.db`

### 🔄 **Schema Overview**

```sql
-- Products table
CREATE TABLE products (
    product_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    category TEXT,
    brand TEXT,
    price REAL,
    rating REAL,
    stock INTEGER
);

-- Autosuggest table
CREATE TABLE autosuggest_queries (
    query TEXT PRIMARY KEY,
    popularity INTEGER,
    category TEXT
);
```

---

## 🌐 6. API Endpoints (Already Working!)

Your search system is now running with these endpoints:

### 🔍 **Search API**

```bash
GET /search?q=mobile phones&category=Electronics
GET /search/similar/{product_id}
GET /search/filters
```

### 💡 **Autosuggest API**

```bash
GET /autosuggest?q=mobile&limit=10
GET /autosuggest/trending?limit=20
GET /autosuggest/categories
```

### 📊 **Analytics API**

```bash
POST /analytics/event
GET /analytics/search-stats
GET /analytics/popular-products
```

---

## 🚀 7. How to Start Using Your System

### **Option 1: Start the API Server**

```bash
# Already running! Check: http://localhost:8000/docs
uvicorn app.main:app --reload
```

### **Option 2: Test the APIs**

```bash
# Test autosuggest
curl "http://localhost:8000/autosuggest?q=mobile"

# Test search
curl "http://localhost:8000/search?q=samsung"

# View API documentation
# Open: http://localhost:8000/docs
```

---

## 📈 8. Scale with Real Data (Production)

### **Step 1: Replace Sample Data**

```python
# Update data/raw/flipkart_products.csv with real products
# Update data/raw/autosuggest_queries.csv with real queries
# Run: python scripts/seed_db.py
```

### **Step 2: Add ML Enhancements**

```python
# Generate BERT embeddings for semantic search
# Build FAISS vector index for fast similarity search
# Add typo correction and query understanding
```

### **Step 3: Deploy to Production**

```bash
# Use PostgreSQL instead of SQLite
# Add Redis for caching
# Deploy with Docker Compose
docker-compose up -d
```

---

## 🎯 **Current System Status**

✅ **Backend API**: Fully functional with FastAPI  
✅ **Database**: Populated with 5K products + 2K queries  
✅ **Search**: Text-based search with filters  
✅ **Autosuggest**: Real-time query completion  
✅ **Analytics**: Event tracking and statistics  
✅ **Documentation**: Interactive API docs at `/docs`

**Next**: Add frontend UI, ML embeddings, and advanced ranking!
