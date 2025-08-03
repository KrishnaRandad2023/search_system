# Flipkart Search System - Database Setup & Configuration Guide

## 🚀 Quick Start Guide

This guide provides step-by-step instructions for setting up the Flipkart Search System database and configuring the application after cloning the repository.

## 📋 Prerequisites

- Python 3.9 or higher
- Git
- Virtual environment (recommended)
- 2GB+ free disk space

## 🔧 Initial Setup

### 1. Clone and Navigate to Repository

```bash
git clone https://github.com/KrishnaRandad2023/search_system.git
cd search_system
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Create Required Directories

```bash
# Windows PowerShell:
New-Item -ItemType Directory -Path data, data\raw, data\processed, data\embeddings, data\db, logs, models -Force

# Linux/Mac:
mkdir -p data/raw data/processed data/embeddings data/db logs models
```

## 🗄️ Database Configuration & Data Population

### Method 1: Automated Setup (⭐ Recommended)

**Single Command Setup:**

```bash
python scripts/setup.py
```

This script automatically runs all the following steps in the correct order and handles error checking.

---

### Method 2: Manual Step-by-Step Setup

If you prefer to run each step manually or need to debug issues:

#### ⚡ Step 1: Generate Base Product Database

```bash
python scripts/generate_flipkart_products.py
```

**What it does:**

- ✅ Creates `data/db/flipkart_products.db`
- ✅ Generates **12,000 realistic products** across 8 categories
- ✅ Sets up proper database schema with performance indexes
- ✅ Categories: Electronics, Fashion, Home & Kitchen, Books, Sports, Beauty, Grocery, Toys

**Expected Output:**

```
Generated 12000/12000 products...
✅ Successfully generated and inserted 12000 products!

📊 DATABASE STATISTICS
=====================================
Total Products: 12,000
Products In Stock: 11,400
Price Range: ₹99.00 - ₹149,999.00
Average Price: ₹15,647.23
Average Rating: 4.1
High Rated Products (4.0+): 8,640

📈 CATEGORY DISTRIBUTION:
  Electronics: 1,680 (14.0%)
  Fashion: 1,560 (13.0%)
  Home & Kitchen: 1,440 (12.0%)
  ...
```

#### ⚡ Step 2: Create Main Database & Transfer Data
`
```bash
python scripts/load_full_data.py
```

**What it does:**

- ✅ Creates main database `flipkart_search.db` in root directory
- ✅ Sets up complete schema with 6 tables:
  - `products` - Product information
  - `reviews` - Product reviews
  - `queries` - Search queries
  - `autosuggest_queries` - Autosuggest data
  - `search_logs` - Search analytics
  - `user_events` - User interaction tracking
- ✅ Transfers all 12,000 products from Step 1
- ✅ Loads additional data from JSON/CSV files if available

**Expected Output:**

```
✅ Database tables created
Loading products from JSON...
✅ Loaded 12000 products from JSON
Loading reviews...
✅ Loaded 1000 reviews
Loading queries...
✅ Loaded 500 queries
Loading autosuggest queries...
✅ Loaded 2000 autosuggest queries

🎉 Database fully loaded with all existing data!
Database size: 45.67 MB
```

#### ⚡ Step 3: Ingest Additional Products

```bash
python scripts/ingest_products.py
```

**What it does:**

- ✅ Generates additional **5,000 specialized products**
- ✅ Adds more variety to existing categories
- ✅ Creates enhanced autosuggest data
- ✅ Generates sample reviews for new products
- ✅ **Final total: ~17,005 products**

**Expected Output:**

```
✅ Generated 5000 products
✅ Generated 1500 autosuggest queries
✅ Saved 5000 products to data/raw/flipkart_products.csv
✅ Saved 1500 autosuggest queries to data/raw/autosuggest_queries.csv
✅ Saved 1000 reviews to data/raw/flipkart_reviews.csv

🎉 Data generation complete!

Next steps:
1. Run: python scripts/seed_db.py (to populate database)
2. Run: python scripts/generate_embeddings.py (to create vector embeddings)
```

#### ⚡ Step 4: Seed Database with Analytics Data

```bash
python scripts/seed_db.py
```

**What it does:**

- ✅ Populates search queries for intelligent autosuggest
- ✅ Adds realistic user reviews with ratings
- ✅ Creates sample search logs for analytics
- ✅ Sets up user behavior tracking data
- ✅ Initializes popularity metrics

**Expected Output:**

```
🌱 Starting database seeding...
✅ Seeded 2000 search queries
✅ Seeded 1000 product reviews
✅ Seeded 500 search logs
✅ Seeded 300 user events

📊 SEEDING SUMMARY:
Total Products: 17,005
Search Queries: 2,000
Reviews: 1,000
Search Logs: 500
User Events: 300

🎉 Database seeding completed successfully!
```

#### ⚡ Step 5: Generate ML Embeddings (Optional)

```bash
python scripts/generate_embeddings.py
```

**What it does:**

- ✅ Creates vector embeddings for semantic search
- ✅ Generates FAISS indexes for ultra-fast similarity search
- ✅ Saves embeddings to `data/embeddings/`
- ✅ Enables "smart search" that understands context

## ✅ Verification Steps

### 1. Quick Database Check

```bash
python -c "import sqlite3; conn = sqlite3.connect('flipkart_search.db'); print('Total Products:', conn.execute('SELECT COUNT(*) FROM products').fetchone()[0])"
```

**Expected**: `Total Products: 17005`

### 2. Category Distribution Check

```bash
python scripts/check_data.py
```

### 3. Comprehensive Health Check

```bash
python scripts/final_health_check.py
```

### 4. Test Database Connection

```bash
python test_db_connection.py
```

## 🚀 Starting the Application

### Development Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Using VS Code Task (Recommended)

1. Open VS Code
2. Press `Ctrl+Shift+P`
3. Type "Tasks: Run Task"
4. Select "Run Flipkart Search API"

### Production Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Using Docker

```bash
docker-compose up --build
```

## 🌐 API Endpoints & Testing

Once the server is running, access:

### Core Endpoints

- **🏠 API Documentation**: http://localhost:8000/docs
- **❤️ Health Check**: http://localhost:8000/health
- **🔍 Search API**: http://localhost:8000/search/?q=smartphone
- **💡 Autosuggest**: http://localhost:8000/autosuggest/?q=phone

### Test Queries

```bash
# Basic search
curl "http://localhost:8000/search/?q=smartphone"

# Filtered search
curl "http://localhost:8000/search/?q=laptop&category=Electronics&min_price=30000&max_price=80000"

# Autosuggest
curl "http://localhost:8000/autosuggest/?q=mob"
```

## 🗃️ Final Database Schema

The completed database contains:

### 📊 Tables Overview

| Table                 | Records | Purpose            |
| --------------------- | ------- | ------------------ |
| `products`            | ~17,005 | Product catalog    |
| `autosuggest_queries` | ~2,000  | Search suggestions |
| `search_logs`         | ~500+   | Search analytics   |
| `user_events`         | ~300+   | User behavior      |
| `reviews`             | ~1,000+ | Product reviews    |

### 🏷️ Product Categories Distribution

```
Electronics: 2,465 products (14.5%)
Fashion: 2,056 products (12.1%)
Home & Kitchen: 2,507 products (14.7%)
Sports & Fitness: 2,471 products (14.5%)
Beauty & Health: 2,019 products (11.9%)
Books & Media: 1,987 products (11.7%)
Other Categories: ~3,500 products (20.6%)
```

## 🐛 Troubleshooting

### Common Issues & Solutions

#### 1. Import/Module Errors

```bash
pip install -r requirements.txt --upgrade
pip install faker sqlalchemy fastapi uvicorn pandas
```

#### 2. Database Permission Issues

```bash
# Windows
icacls data /grant Everyone:F /T

# Linux/Mac
chmod 755 data/
chmod 644 data/*.db
```

#### 3. Port Already in Use

```bash
# Find process using port 8000
netstat -ano | findstr :8000
# Kill the process and restart
uvicorn app.main:app --port 8001
```

#### 4. SQLite Database Locked

```bash
# Close all connections and restart
python -c "import sqlite3; conn = sqlite3.connect('flipkart_search.db'); conn.execute('PRAGMA optimize'); conn.close()"
```

### 🔍 Verification Commands

```bash
# Check total products
python -c "import sqlite3; conn = sqlite3.connect('flipkart_search.db'); print('Products:', conn.execute('SELECT COUNT(*) FROM products').fetchone()[0])"

# Check categories
python -c "import sqlite3; conn = sqlite3.connect('flipkart_search.db'); [print(f'{row[0]}: {row[1]}') for row in conn.execute('SELECT category, COUNT(*) FROM products GROUP BY category ORDER BY COUNT(*) DESC').fetchall()]"

# Check database size
python -c "import os; print(f'Database size: {os.path.getsize(\"flipkart_search.db\") / (1024*1024):.2f} MB')"
```

## ⚡ Performance Optimization

### For Better Performance

1. **Enable WAL Mode**:

   ```sql
   PRAGMA journal_mode=WAL;
   PRAGMA synchronous=NORMAL;
   ```

2. **Additional Indexes**:

   ```sql
   CREATE INDEX idx_price_rating ON products(price, rating);
   CREATE INDEX idx_category_brand ON products(category, brand);
   CREATE INDEX idx_search_text ON products(title, description);
   ```

3. **Connection Pooling** in production

## 📁 File Structure After Setup

```
search_system/
├── 📁 data/
│   ├── 📁 db/
│   │   └── 📄 flipkart_products.db (12K products - intermediate)
│   ├── 📁 raw/ (CSV/JSON source files)
│   ├── 📁 processed/ (processed data)
│   └── 📁 embeddings/ (ML vector embeddings)
├── 📄 flipkart_search.db (17K products - MAIN DATABASE)
├── 📁 logs/ (application logs)
├── 📁 models/ (ML models)
├── 📁 app/ (FastAPI application)
└── 📁 scripts/ (setup scripts)
```

## ✅ Success Indicators

**🎉 Setup Complete When:**

- ✅ Main database has ~17,005 products
- ✅ Health endpoint returns `{"status": "healthy"}`
- ✅ Search API returns results for test queries
- ✅ No errors in `logs/app.log`
- ✅ All categories have products
- ✅ Autosuggest returns suggestions

## 🎯 Next Steps After Setup

1. **Test Functionality**: Visit http://localhost:8000/docs
2. **Configure Production**: Edit `app/config/settings.py`
3. **Setup Monitoring**: Configure logging and metrics
4. **Deploy**: Use Docker or cloud services
5. **Frontend Integration**: Connect React/Vue.js frontend

## 📞 Support & Debugging

### Debug Steps:

1. **Check Logs**: `tail -f logs/app.log`
2. **Health Check**: `python scripts/final_health_check.py`
3. **Database Verification**: `python scripts/check_data.py`
4. **API Test**: Visit http://localhost:8000/health

### Log Locations:

- Application logs: `logs/app.log`
- Error logs: `logs/errors.log`
- SQL queries: Console output (dev mode)

---

## 🏆 Final Result

**You'll have a production-ready e-commerce search system with:**

- 🗄️ **17,005+ products** across multiple categories
- 🔍 **Semantic search** with typo correction
- 💡 **Intelligent autosuggest** with 2,000+ queries
- 📊 **Analytics & tracking** for user behavior
- 🚀 **High-performance APIs** with <100ms response times
- 📱 **Mobile-friendly** REST APIs
- 🤖 **ML-powered ranking** and recommendations

**Perfect for Flipkart Grid 7.0 submission! 🎯**
