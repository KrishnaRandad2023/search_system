"""
Database Connection Pool Manager
Addresses database connection issues and performance problems
"""

import sqlite3
import threading
import time
from contextlib import contextmanager
from typing import Optional, Generator
from queue import Queue, Empty, Full
import logging

logger = logging.getLogger(__name__)


class DatabaseConnectionPool:
    """SQLite connection pool for better performance and reliability"""
    
    def __init__(self, database_path: str, pool_size: int = 10, timeout: int = 30):
        self.database_path = database_path
        self.pool_size = pool_size
        self.timeout = timeout
        self._pool = Queue(maxsize=pool_size)
        self._lock = threading.Lock()
        self._created_connections = 0
        
        # Pre-populate the pool
        self._initialize_pool()
        
    def _initialize_pool(self):
        """Initialize the connection pool"""
        for _ in range(self.pool_size):
            try:
                conn = self._create_connection()
                self._pool.put(conn, block=False)
                self._created_connections += 1
            except Full:
                break
            except Exception as e:
                logger.error(f"Failed to create database connection: {e}")
                
    def _create_connection(self) -> sqlite3.Connection:
        """Create a new database connection with optimizations"""
        conn = sqlite3.connect(
            self.database_path,
            check_same_thread=False,
            timeout=self.timeout,
            isolation_level=None  # Enable autocommit mode
        )
        
        # SQLite performance optimizations
        conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
        conn.execute("PRAGMA synchronous=NORMAL")  # Balance safety vs performance
        conn.execute("PRAGMA cache_size=10000")  # 10MB cache
        conn.execute("PRAGMA temp_store=memory")  # Store temp tables in memory
        conn.execute("PRAGMA mmap_size=268435456")  # 256MB memory mapping
        
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys=ON")
        
        return conn
        
    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get a connection from the pool"""
        conn = None
        try:
            # Try to get connection from pool
            try:
                conn = self._pool.get(timeout=self.timeout)
            except Empty:
                # Pool is empty, create new connection if possible
                if self._created_connections < self.pool_size * 2:  # Allow some overflow
                    conn = self._create_connection()
                    self._created_connections += 1
                else:
                    raise Exception("Database connection pool exhausted")
            
            # Test connection is still valid
            try:
                conn.execute("SELECT 1")
            except sqlite3.Error:
                # Connection is stale, create new one
                conn.close()
                conn = self._create_connection()
            
            yield conn
            
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
            raise
        finally:
            # Return connection to pool
            if conn:
                try:
                    # Return to pool if there's space
                    self._pool.put(conn, block=False)
                except Full:
                    # Pool is full, close the connection
                    conn.close()
                    self._created_connections -= 1
                    
    def close_all(self):
        """Close all connections in the pool"""
        while not self._pool.empty():
            try:
                conn = self._pool.get(block=False)
                conn.close()
            except Empty:
                break
        self._created_connections = 0
        
    def get_stats(self) -> dict:
        """Get pool statistics"""
        return {
            "pool_size": self.pool_size,
            "available_connections": self._pool.qsize(),
            "created_connections": self._created_connections,
            "database_path": self.database_path
        }


# Global connection pool instance
_connection_pool: Optional[DatabaseConnectionPool] = None


def initialize_connection_pool(database_path: str, pool_size: int = 10) -> DatabaseConnectionPool:
    """Initialize the global connection pool"""
    global _connection_pool
    if _connection_pool is None:
        _connection_pool = DatabaseConnectionPool(database_path, pool_size)
        logger.info(f"Database connection pool initialized with {pool_size} connections")
    return _connection_pool


def get_connection_pool() -> DatabaseConnectionPool:
    """Get the global connection pool"""
    if _connection_pool is None:
        raise RuntimeError("Connection pool not initialized. Call initialize_connection_pool first.")
    return _connection_pool


@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """Get a database connection from the pool"""
    pool = get_connection_pool()
    with pool.get_connection() as conn:
        yield conn


# Database health check
def check_database_health(database_path: str) -> dict:
    """Check database health and performance"""
    try:
        start_time = time.time()
        
        with sqlite3.connect(database_path, timeout=5) as conn:
            cursor = conn.cursor()
            
            # Basic connectivity test
            cursor.execute("SELECT 1")
            
            # Check database integrity
            cursor.execute("PRAGMA integrity_check")
            integrity = cursor.fetchone()[0]
            
            # Get database size
            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]
            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]
            db_size_mb = (page_count * page_size) / (1024 * 1024)
            
            # Performance metrics
            response_time = (time.time() - start_time) * 1000
            
            return {
                "status": "healthy",
                "integrity": integrity,
                "size_mb": round(db_size_mb, 2),
                "response_time_ms": round(response_time, 2),
                "timestamp": time.time()
            }
            
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }
