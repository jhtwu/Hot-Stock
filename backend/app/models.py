"""
数据库模型定义
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.app.database import Base


class Stock(Base):
    """股票基本信息表"""
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), unique=True, index=True, nullable=False)
    name = Column(String(100))
    sector = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    histories = relationship("StockHistory", back_populates="stock", cascade="all, delete-orphan")
    news_articles = relationship("NewsArticle", back_populates="stock", cascade="all, delete-orphan")
    daily_scores = relationship("DailyScore", back_populates="stock", cascade="all, delete-orphan")


class StockHistory(Base):
    """股票历史数据表"""
    __tablename__ = "stock_histories"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    date = Column(DateTime, nullable=False, index=True)
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float)
    volume = Column(Float)
    change_percent = Column(Float)  # 涨跌幅
    volume_ratio = Column(Float)    # 成交量比率（相对于平均成交量）

    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    stock = relationship("Stock", back_populates="histories")

    # 索引
    __table_args__ = (
        Index('ix_stock_history_date', 'stock_id', 'date'),
    )


class NewsArticle(Base):
    """新闻文章表"""
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    url = Column(String(1000))
    source = Column(String(100))
    published_at = Column(DateTime, nullable=False, index=True)
    sentiment_score = Column(Float, default=0.0)  # 情绪分数 (-1 到 1)

    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    stock = relationship("Stock", back_populates="news_articles")

    # 索引
    __table_args__ = (
        Index('ix_news_stock_date', 'stock_id', 'published_at'),
    )


class DailyScore(Base):
    """每日评分表"""
    __tablename__ = "daily_scores"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    date = Column(DateTime, nullable=False, index=True)

    # 各项指标分数
    price_change_score = Column(Float, default=0.0)      # 价格变化分数
    volume_score = Column(Float, default=0.0)            # 成交量分数
    news_count_score = Column(Float, default=0.0)        # 新闻数量分数
    news_sentiment_score = Column(Float, default=0.0)    # 新闻情绪分数
    trend_score = Column(Float, default=0.0)             # 趋势分数

    # 综合分数
    total_score = Column(Float, default=0.0, index=True)  # 总分
    hot_rank = Column(Integer)           # 热度排名
    growth_rank = Column(Integer)        # 增长排名

    # 原始数据
    news_count = Column(Integer, default=0)              # 新闻数量
    price_change = Column(Float, default=0.0)            # 价格变化百分比
    volume_ratio = Column(Float, default=0.0)            # 成交量比率

    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    stock = relationship("Stock", back_populates="daily_scores")

    # 索引
    __table_args__ = (
        Index('ix_daily_score_date', 'date', 'total_score'),
        Index('ix_daily_score_stock_date', 'stock_id', 'date'),
    )
