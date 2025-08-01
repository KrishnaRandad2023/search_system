"""
Database Management API - Safe database operations
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Import the database manager
try:
    from app.services.database_manager import get_database_manager
    DB_MANAGER_AVAILABLE = True
except ImportError:
    DB_MANAGER_AVAILABLE = False
    logger.warning("Database manager not available")

router = APIRouter(prefix="/api/v1/admin", tags=["Database Management"])

class DatabaseStats(BaseModel):
    total_products: int
    available_products: int
    top_categories: Dict[str, int]
    total_reviews: int
    total_queries: int

class BackupInfo(BaseModel):
    file: str
    name: str
    size_mb: float
    created: str

class DatabaseResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

@router.get("/database/stats", response_model=DatabaseResponse)
async def get_database_statistics():
    """Get current database statistics"""
    if not DB_MANAGER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database manager not available")
    
    try:
        db_manager = get_database_manager()
        stats = db_manager.get_database_stats()
        
        return DatabaseResponse(
            success=True,
            message="Database statistics retrieved successfully",
            data=stats
        )
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/database/backup", response_model=DatabaseResponse)
async def create_database_backup():
    """Create a backup of the current database"""
    if not DB_MANAGER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database manager not available")
    
    try:
        db_manager = get_database_manager()
        backup_path = db_manager.create_backup()
        
        if backup_path:
            return DatabaseResponse(
                success=True,
                message="Database backup created successfully",
                data={"backup_path": backup_path}
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to create backup")
            
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/database/backups", response_model=DatabaseResponse)
async def list_database_backups():
    """List available database backups"""
    if not DB_MANAGER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database manager not available")
    
    try:
        db_manager = get_database_manager()
        backups = db_manager.list_backups()
        
        return DatabaseResponse(
            success=True,
            message=f"Found {len(backups)} backup(s)",
            data={"backups": backups}
        )
    except Exception as e:
        logger.error(f"Failed to list backups: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/database/generate-data", response_model=DatabaseResponse)
async def generate_additional_data(
    background_tasks: BackgroundTasks,
    num_products: int = 1000
):
    """Generate additional test data (runs in background)"""
    if not DB_MANAGER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database manager not available")
    
    if num_products > 5000:
        raise HTTPException(status_code=400, detail="Maximum 5000 products allowed per generation")
    
    def generate_data_task():
        try:
            db_manager = get_database_manager()
            db_manager.generate_additional_data(num_products)
            logger.info(f"Background task completed: generated {num_products} products")
        except Exception as e:
            logger.error(f"Background data generation failed: {e}")
    
    background_tasks.add_task(generate_data_task)
    
    return DatabaseResponse(
        success=True,
        message=f"Started background generation of {num_products} products",
        data={"num_products": num_products, "status": "in_progress"}
    )

@router.post("/database/restore", response_model=DatabaseResponse)
async def restore_database_backup(backup_path: str):
    """Restore database from backup (DANGEROUS - use with caution)"""
    if not DB_MANAGER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database manager not available")
    
    try:
        db_manager = get_database_manager()
        success = db_manager.restore_backup(backup_path)
        
        if success:
            return DatabaseResponse(
                success=True,
                message="Database restored successfully",
                data={"restored_from": backup_path}
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to restore database")
            
    except Exception as e:
        logger.error(f"Failed to restore database: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/database/health", response_model=DatabaseResponse)
async def check_database_health():
    """Check database health and Amazon lite data availability"""
    try:
        stats = {}
        
        # Check if Amazon lite data is available
        from pathlib import Path
        amazon_prefix_map = Path("data/amazon_lite_prefix_map.json")
        amazon_suggestions = Path("data/amazon_lite_suggestions.json")
        
        stats['amazon_prefix_map_available'] = amazon_prefix_map.exists()
        stats['amazon_suggestions_available'] = amazon_suggestions.exists()
        
        if amazon_prefix_map.exists():
            stats['amazon_prefix_map_size_mb'] = amazon_prefix_map.stat().st_size / (1024 * 1024)
        
        if amazon_suggestions.exists():
            stats['amazon_suggestions_size_mb'] = amazon_suggestions.stat().st_size / (1024 * 1024)
        
        # Check database
        if DB_MANAGER_AVAILABLE:
            db_manager = get_database_manager()
            db_stats = db_manager.get_database_stats()
            stats.update(db_stats)
            stats['database_manager_available'] = True
        else:
            stats['database_manager_available'] = False
        
        return DatabaseResponse(
            success=True,
            message="Database health check completed",
            data=stats
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
