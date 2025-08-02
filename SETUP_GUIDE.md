# 🚀 Flipkart Search System - Complete Setup Guide

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start (Recommended)](#quick-start-recommended)
- [Detailed Setup Steps](#detailed-setup-steps)
- [Environment Configuration](#environment-configuration)
- [Running the Application](#running-the-application)
- [Verification Steps](#verification-steps)
- [Troubleshooting](#troubleshooting)
- [Common Issues & Solutions](#common-issues--solutions)

---

## 🔧 Prerequisites

### Required Software

1. **Python 3.9+** (Recommended: Python 3.11.9)

   - Download from: https://www.python.org/downloads/
   - ⚠️ **IMPORTANT**: Check "Add Python to PATH" during installation

2. **Git** (for cloning repository)

   - Download from: https://git-scm.com/downloads

3. **Optional but Recommended:**
   - **Redis** (for caching): https://redis.io/download
   - **PostgreSQL** (for production): https://www.postgresql.org/download/

### System Requirements

- **RAM**: Minimum 4GB, Recommended 8GB+
- **Storage**: At least 2GB free space
- **OS**: Windows 10/11, macOS, or Linux

---

## ⚡ Quick Start (Recommended)

### Backend Only Setup

### Step 1: Clone Repository

```bash
git clone https://github.com/KrishnaRandad2023/search_system.git
cd search_system
```

### Step 2: Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Generate Product Database ⚠️ **CRITICAL**

```bash
# IMPORTANT: Generate product data (this creates 12,000+ products)
python scripts/generate_flipkart_products.py

# Verify database was created (database will be in data/db/ folder)
python -c "import os; print('Database exists (data/db):', os.path.exists('data/db/flipkart_products.db'))"
# Should show: Database exists (data/db): True
```

### Step 5: Run the Application

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 6: Open in Browser

```
Backend API: http://localhost:8000
API Docs: http://localhost:8000/docs
```

### Full Stack Setup (Backend + Frontend)

If you want the complete UI experience:

### Additional Steps for Frontend:

```bash
# After completing backend steps above, open a new terminal

# Navigate to frontend
cd frontend

# Install Node.js dependencies
npm install

# Create environment file
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start frontend server
npm run dev
```

### Access Complete Application:

```
Frontend: http://localhost:3000
Backend API: http://localhost:8000
```

**✅ If this works, you're done! If not, follow the detailed steps below.**

---

## 📚 Detailed Setup Steps

### 1. Environment Setup

#### Windows Users:

```powershell
# Open PowerShell as Administrator (recommended)
# Check Python installation
python --version
# Should show: Python 3.11.9 or similar

# If Python not found, install from python.org
# Make sure to check "Add Python to PATH"
```

#### macOS Users:

```bash
# Check Python installation
python3 --version

# If not installed, use Homebrew:
brew install python@3.11
```

#### Linux Users:

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev

# CentOS/RHEL
sudo yum install python311 python311-devel
```

### 2. Clone and Navigate

```bash
git clone https://github.com/KrishnaRandad2023/search_system.git
cd search_system

# Verify you're in the right directory
ls -la
# You should see: app/, requirements.txt, README.md, etc.
```

### 3. Virtual Environment (CRITICAL STEP)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Verify activation - you should see (venv) in your prompt
# Example: (venv) C:\path\to\search_system>
```

### 4. Install Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip

# Install all requirements
pip install -r requirements.txt

# If you get permission errors on Windows:
pip install --user -r requirements.txt

# Verify installation
pip list
# Should see: fastapi, uvicorn, sqlalchemy, etc.
```

### 5. Database Setup & Product Data Loading ⚠️ **CRITICAL STEP**

```bash
# Check if database exists (will show False initially)
python -c "import os; print('Database exists (root):', os.path.exists('flipkart_search.db')); print('Database exists (data/db):', os.path.exists('data/db/flipkart_products.db'))"

# Generate and populate database with 10,000+ products
python scripts/generate_flipkart_products.py

# Verify database was created successfully
python -c "import os; print('Database exists (root):', os.path.exists('flipkart_search.db')); print('Database exists (data/db):', os.path.exists('data/db/flipkart_products.db'))"
# Should now show: Database exists (data/db): True

# Check product count and verify data
python -c "
import sqlite3
import os
db_paths = ['flipkart_search.db', 'data/db/flipkart_products.db', 'data/flipkart_products.db']
for db_path in db_paths:
    if os.path.exists(db_path):
        print(f'Found database: {db_path}')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM products')
        count = cursor.fetchone()[0]
        print(f'Products in {db_path}: {count}')
        conn.close()
        break
else:
    print('No database found!')
"
```

**🎯 Without this step, you'll see:**

- ❌ Autosuggest works but no search results
- ❌ Empty product database
- ❌ API returns no products

**✅ After this step, you'll have:**

- ✅ 12,000+ realistic Flipkart products
- ✅ Categories: Electronics, Fashion, Home & Kitchen, Books, Sports, Beauty, Grocery, Toys & Baby
- ✅ Full search functionality with real data
- ✅ Database location: `data/db/flipkart_products.db`

---

## 🔧 Environment Configuration

### Option 1: Use Default Configuration (Recommended for Testing)

The app works out-of-the-box with SQLite and no additional configuration.

### Option 2: Custom Configuration

Create a `.env` file in the project root:

```bash
# Create .env file
touch .env  # macOS/Linux
# OR create manually on Windows
```

Add these variables to `.env`:

```env
# Database
DATABASE_URL=sqlite:///./flipkart_search.db

# Redis (Optional)
REDIS_HOST=localhost
REDIS_PORT=6379

# API Configuration
DEBUG=true
HOST=0.0.0.0
PORT=8000

# Logging
LOG_LEVEL=INFO
```

---

## 🚀 Running the Application

### Method 1: Using Uvicorn (Recommended)

```bash
# Make sure virtual environment is activated
# You should see (venv) in your prompt

# Run the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# You should see output like:
# INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
# INFO:     Started reloader process
```

### Method 2: Using Python directly

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Method 3: Using the provided script (if available)

```bash
python main.py
```

---

## ✅ Verification Steps

### 1. Check if Server is Running

Open your browser and go to:

- **Main API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### 2. Test Basic Functionality

```bash
# In a new terminal (keep the server running in the first one)
curl http://localhost:8000/health

# Should return: {"status": "healthy"}
```

### 3. Test Search API

```bash
curl "http://localhost:8000/api/search?query=mobile"

# Should return JSON with search results
```

### 4. Test Autosuggest

```bash
curl "http://localhost:8000/api/autosuggest?query=mob"

# Should return JSON with suggestions
```

### 5. Verify Database & Products

```bash
# Check if database has products (checks multiple possible locations)
python -c "
import sqlite3
import os
db_paths = ['flipkart_search.db', 'data/db/flipkart_products.db', 'data/flipkart_products.db']
for db_path in db_paths:
    if os.path.exists(db_path):
        print(f'Found database: {db_path}')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM products')
        count = cursor.fetchone()[0]
        print(f'Products in database: {count}')

        # Show sample products
        cursor.execute('SELECT title, category, current_price FROM products LIMIT 3')
        products = cursor.fetchall()
        print('Sample products:')
        for product in products:
            print(f'  - {product[0]} ({product[1]}) - ₹{product[2]}')

        conn.close()
        break
else:
    print('❌ No database found! Run: python scripts/generate_flipkart_products.py')
"

# Should show: Products in database: 12000+ (or similar number)
```

---

## 🎨 Frontend Setup (Optional but Recommended)

The project includes a modern Next.js frontend with TypeScript and Tailwind CSS.

### Prerequisites for Frontend

- **Node.js 18+** (Recommended: Node.js 20+)
  - Download from: https://nodejs.org/downloads/
  - Verify: `node --version` and `npm --version`

### Frontend Setup Steps

#### Step 1: Navigate to Frontend Directory

```bash
# Make sure you're in the main project directory
cd frontend
```

#### Step 2: Install Dependencies

```bash
# Install all frontend dependencies
npm install

# Or use yarn if you prefer
yarn install
```

#### Step 3: Configure Environment

Create `.env.local` file in the frontend directory:

```bash
# Create environment file
touch .env.local  # macOS/Linux
# OR create manually on Windows
```

Add these variables to `.env.local`:

```env
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# Optional: For production
# NEXT_PUBLIC_API_URL=https://your-production-api.com
```

#### Step 4: Run Frontend Development Server

```bash
# Start the frontend server
npm run dev

# You should see output like:
# ▲ Next.js 15.4.5
# - Local:        http://localhost:3000
# - ready in 2.1s
```

#### Step 5: Access the Application

Open your browser and go to:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000 (should be running separately)

### Frontend Verification Steps

#### 1. Check Frontend is Running

```bash
# Should show the main search interface
curl http://localhost:3000

# Or open in browser: http://localhost:3000
```

#### 2. Test Search Interface

1. Open http://localhost:3000 in your browser
2. Type in the search box (should show autosuggest)
3. Press Enter or click search
4. Verify results are displayed

#### 3. Check Console for Errors

- Open browser Developer Tools (F12)
- Check Console tab for any JavaScript errors
- Check Network tab to verify API calls are working

### Full Stack Setup (Backend + Frontend)

#### Option 1: Two Terminals (Recommended for Development)

```bash
# Terminal 1: Backend
cd search_system
source venv/bin/activate  # or venv\Scripts\activate on Windows
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd search_system/frontend
npm run dev
```

#### Option 2: Production Build

```bash
# Build frontend for production
cd frontend
npm run build
npm start

# Backend with production settings
cd ..
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend Troubleshooting

#### Problem: "Node.js not found"

**Solution:**

```bash
# Download and install Node.js from nodejs.org
# Verify installation
node --version
npm --version
```

#### Problem: "npm install fails"

**Solution:**

```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json  # macOS/Linux
rmdir /s node_modules && del package-lock.json  # Windows
npm install
```

#### Problem: "Port 3000 already in use"

**Solution:**

```bash
# Use different port
npm run dev -- -p 3001

# Or kill process using port 3000
# Windows:
netstat -ano | findstr :3000
taskkill /PID <PID_NUMBER> /F

# macOS/Linux:
lsof -ti:3000 | xargs kill -9
```

#### Problem: "API calls failing"

**Solution:**

```bash
# Check if backend is running on port 8000
curl http://localhost:8000/health

# Verify .env.local has correct API URL
cat frontend/.env.local  # Should show NEXT_PUBLIC_API_URL=http://localhost:8000

# Check browser console for CORS errors
# Backend should handle CORS automatically
```

#### Problem: "Build errors"

**Solution:**

```bash
# Check TypeScript errors
cd frontend
npm run lint

# Fix common issues
npm run build  # This will show specific errors to fix
```

### Frontend Features

#### 🎯 **Search Interface**

- Real-time autosuggest with debouncing
- Advanced search with filters
- Product grid with images and details
- Pagination and sorting options

#### 🎨 **UI Components**

- Modern Flipkart-inspired design
- Responsive mobile-first layout
- Loading states and error handling
- Accessibility features

#### ⚡ **Performance**

- Next.js optimizations
- Image optimization
- Code splitting
- Fast refresh during development

---

## 🔧 Troubleshooting

### Problem: "Python not found"

**Solution:**

```bash
# Windows: Add Python to PATH
# 1. Search "Environment Variables" in Start Menu
# 2. Click "Environment Variables"
# 3. Add Python installation path to PATH

# Alternative: Use full path
C:\Users\YourName\AppData\Local\Programs\Python\Python311\python.exe -m venv venv
```

### Problem: "pip not found"

**Solution:**

```bash
# Windows
python -m pip install --upgrade pip

# macOS
python3 -m pip install --upgrade pip
```

### Problem: "ModuleNotFoundError"

**Solution:**

```bash
# Make sure virtual environment is activated
# Look for (venv) in your prompt

# If not activated:
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Reinstall requirements
pip install -r requirements.txt
```

### Problem: "ModuleNotFoundError: No module named 'faker'"

**Solution:**

```bash
# Install faker specifically (it was missing from requirements.txt)
pip install faker>=20.1.0

# Or reinstall all requirements (faker is now included)
pip install -r requirements.txt

# Then try running the database generation again
python scripts/generate_flipkart_products.py
```

### Problem: "Port 8000 already in use"

**Solution:**

```bash
# Use a different port
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# Or kill the process using port 8000
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID_NUMBER> /F

# macOS/Linux:
lsof -ti:8000 | xargs kill -9
```

### Problem: "Permission denied" errors

**Solution:**

```bash
# Windows: Run PowerShell as Administrator
# macOS/Linux: Use sudo for system-wide installations
sudo pip install -r requirements.txt

# Or install in user directory:
pip install --user -r requirements.txt
```

---

## 🚨 Common Issues & Solutions

### Issue 1: Virtual Environment Not Working

```bash
# Delete existing venv and recreate
rm -rf venv  # macOS/Linux
rmdir /s venv  # Windows

# Recreate
python -m venv venv
# Activate and install again
```

### Issue 2: Import Errors

```bash
# Check Python path
python -c "import sys; print(sys.path)"

# Verify you're in the right directory
pwd  # Should show path ending with 'search_system'

# Check if app directory exists
ls app/
# Should show: __init__.py, main.py, api/, etc.
```

### Issue 3: Database Errors / No Search Results

**Problem**: Autosuggest works but no search results, or database schema errors like "no such column: products.product_id"

**Solution:**

```bash
# Step 1: Check if you have the schema mismatch issue
# If you see errors like "no such column: products.product_id", you have a schema mismatch

# Step 2: Verify database exists and has products
python -c "
import sqlite3
conn = sqlite3.connect('data/db/flipkart_products.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM products')
count = cursor.fetchone()[0]
print(f'Products in database: {count}')
conn.close()
"

# Step 3: If schema mismatch occurred, restart the server
# The models have been fixed to match the actual database schema
# Stop server (Ctrl+C) and restart:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Step 4: Test search functionality
curl "http://localhost:8000/api/search?query=shirt"
# Should now return actual products!
```

**Common Schema Issues:**

- ❌ `product_id` column not found → Fixed: Model now matches actual DB schema
- ❌ `current_price` vs `price` → Fixed: Using `price` column name
- ❌ `is_available` vs `is_in_stock` → Fixed: Using `is_in_stock` column name

### Issue 4: Redis Connection Errors (Optional)

Redis is optional. If you see Redis errors:

```bash
# Option 1: Install Redis
# Windows: Download from https://github.com/microsoftarchive/redis/releases
# macOS: brew install redis
# Linux: sudo apt install redis-server

# Option 2: Disable Redis in config
# The app will work without Redis (uses fallback)
```

---

## 🎯 Production Setup (Optional)

For production deployment:

1. **Use PostgreSQL:**

```bash
pip install psycopg2-binary
# Set DATABASE_URL in .env to PostgreSQL connection string
```

2. **Use Redis:**

```bash
pip install redis
# Start Redis server
redis-server
```

3. **Use Gunicorn:**

```bash
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

---

## 📞 Need Help?

If you're still having issues:

1. **Check the logs** in the terminal where you ran the server
2. **Verify all prerequisites** are installed correctly
3. **Try the Quick Start** method first
4. **Check GitHub Issues**: https://github.com/KrishnaRandad2023/search_system/issues

### Contact Information

- **GitHub**: https://github.com/KrishnaRandad2023/search_system
- **Issues**: Create an issue on GitHub with:
  - Your operating system
  - Python version (`python --version`)
  - Error message (copy-paste the full error)
  - Steps you followed

---

## 🎉 Success Indicators

### Backend Success

You know the backend is working when:

- ✅ Server starts without errors
- ✅ http://localhost:8000 shows the API
- ✅ http://localhost:8000/docs shows Swagger UI
- ✅ http://localhost:8000/health returns `{"status": "healthy"}`
- ✅ Search API returns results: http://localhost:8000/api/search?query=test

### Frontend Success (if using frontend)

You know the frontend is working when:

- ✅ Frontend server starts without errors
- ✅ http://localhost:3000 shows the search interface
- ✅ Search box shows autosuggest when typing
- ✅ Search results display after pressing Enter
- ✅ No console errors in browser Developer Tools

### Full Stack Success

Complete system is working when:

- ✅ Both backend (port 8000) and frontend (port 3000) are running
- ✅ Frontend can communicate with backend API
- ✅ Search functionality works end-to-end
- ✅ Autosuggest appears in under 100ms
- ✅ Search results load in under 500ms

**Happy coding! 🚀**
