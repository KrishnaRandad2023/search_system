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
    __tablename__ = "products"
    
    id = Column(String(50), primary_key=True, index=True)
    title = Column(Text, nullable=False, index=True)
    brand = Column(Text, index=True)
    category = Column(Text, nullable=False, index=True)
    subcategory = Column(Text, index=True)
    specifications = Column(Text)
    description = Column(Text)
    
    # Pricing - Match actual DB schema
    price = Column(Float, nullable=False, index=True)
    original_price = Column(Float)
    discount_percentage = Column(Integer)
    
    # Ratings and Reviews - Match actual DB schema
    rating = Column(Float, index=True)
    review_count = Column(Integer, default=0)
    
    # Inventory - Match actual DB schema
    stock_quantity = Column(Integer, default=0)
    is_in_stock = Column(Boolean, default=True, index=True)
    
    # Seller information
    seller_name = Column(Text)
    seller_rating = Column(Float)
    
    # Additional fields from actual DB schema
    image_urls = Column(Text)
    is_flipkart_assured = Column(Boolean, default=False)
    is_plus_product = Column(Boolean, default=False)
    delivery_days = Column(Integer, default=5)
    tags = Column(Text)
    color = Column(Text)
    size = Column(Text)
    weight = Column(Text)
    dimensions = Column(Text)
    warranty = Column(Text)
    return_policy = Column(Text)
    
    # Analytics fields
    ctr = Column(Float, default=0.0)
    conversion_rate = Column(Float, default=0.0)
    click_count = Column(Integer, default=0)
    order_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    wishlist_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Product(id={self.id}, title='{self.title[:50]}...')>"


class AutosuggestQuery(Base):
    __tablename__ = "autosuggest_queries"
    
    id = Column(Integer, primary_key=True, index=True)
    query = Column(String(200), nullable=False, unique=True, index=True)
    popularity = Column(Integer, default=0, index=True)
    category = Column(String(100), index=True)
    
    def __repr__(self):
        return f"<AutosuggestQuery(query='{self.query}', popularity={self.popularity})>"


class Review(Base):
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
    __tablename__ = "user_events"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), index=True)
    event_type = Column(String(50), nullable=False, index=True)
    
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
