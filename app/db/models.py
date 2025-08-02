"""
Database Models for Flipkart Search System
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Product(Base):
    """Product model - Exact match to database schema"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(String(50), unique=True, index=True, nullable=False)
    title = Column(String(500), nullable=False, index=True)
    description = Column(Text)
    category = Column(String(100), nullable=False, index=True)
    subcategory = Column(String(100), index=True)
    brand = Column(String(100), index=True)
    specifications = Column(Text)
    
    # Pricing - Exact schema match
    original_price = Column(Float)
    current_price = Column(Float, nullable=False, index=True)
    discount_percent = Column(Float)
    savings = Column(Float)
    
    # Ratings and Reviews
    rating = Column(Float, index=True)
    num_ratings = Column(Integer, default=0)
    
    # Inventory
    stock_quantity = Column(Integer, default=0)
    is_available = Column(Boolean, default=True, index=True)
    
    # Seller information
    seller_name = Column(String(200))
    seller_rating = Column(Float)
    seller_location = Column(String(200))
    
    # Policies
    return_policy = Column(Text)
    exchange_available = Column(Boolean, default=False)
    cod_available = Column(Boolean, default=False)
    
    # Media and metadata
    images = Column(Text)
    tags = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Metrics
    views = Column(Integer, default=0)
    purchases = Column(Integer, default=0)
    
    # Flags - Exact order as in database
    is_featured = Column(Boolean, default=False, index=True)
    is_bestseller = Column(Boolean, default=False, index=True)
    
    # Delivery
    delivery_days = Column(Integer)
    free_delivery = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<Product(id={self.product_id}, title='{self.title[:50]}...')>"


class AutosuggestQuery(Base):
    """Autosuggest queries model"""
    __tablename__ = "autosuggest_queries"
    
    id = Column(Integer, primary_key=True, index=True)
    query = Column(String(200), nullable=False, unique=True, index=True)
    popularity = Column(Integer, default=0, index=True)
    category = Column(String(100), index=True)
    
    # Note: No timestamp columns in current DB schema
    # These can be added with a migration if needed
    
    def __repr__(self):
        return f"<AutosuggestQuery(query='{self.query}', popularity={self.popularity})>"


class Review(Base):
    """Product reviews model"""
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(String(50), unique=True, index=True, nullable=False)
    product_id = Column(String(50), nullable=False, index=True)
    user_id = Column(String(50), nullable=False, index=True)
    
    rating = Column(Integer, nullable=False)
    review_text = Column(Text)
    helpful_votes = Column(Integer, default=0)
    verified_purchase = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Review(id={self.review_id}, product_id={self.product_id}, rating={self.rating})>"


class SearchLog(Base):
    """Search analytics model"""
    __tablename__ = "search_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), index=True)
    query = Column(String(500), nullable=False, index=True)
    results_count = Column(Integer)
    response_time_ms = Column(Float)
    
    # User interaction
    clicked_product_id = Column(String(50), index=True)
    click_position = Column(Integer)
    
    # Metadata
    user_agent = Column(String(500))
    ip_address = Column(String(50))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<SearchLog(query='{self.query}', results={self.results_count})>"


class UserEvent(Base):
    """User interaction events model"""
    __tablename__ = "user_events"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), index=True)
    event_type = Column(String(50), nullable=False, index=True)  # search, click, view, etc.
    
    # Event data
    query = Column(String(500), index=True)
    product_id = Column(String(50), index=True)
    category = Column(String(100), index=True)
    
    # Additional metadata
    page_url = Column(String(500))
    referrer = Column(String(500))
    user_agent = Column(String(500))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<UserEvent(type={self.event_type}, query='{self.query}')>"
