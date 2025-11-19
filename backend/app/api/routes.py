"""
API 路由
提供获取榜单、股票详情等接口
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from datetime import datetime, timedelta
from typing import List, Optional
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.app.database import get_db
from backend.app.models import Stock, DailyScore, NewsArticle, StockHistory
from backend.app.analyzers import TrendAnalyzer
from config import TOP_N

router = APIRouter()


@router.get("/api")
async def root():
    """API 根路径"""
    return {
        "name": "Hot Stock Analysis API",
        "version": "1.0.0",
        "endpoints": {
            "rankings": "/api/rankings",
            "stock_detail": "/api/stock/{symbol}",
            "trending": "/api/trending",
            "news": "/api/news/{symbol}",
        }
    }


@router.get("/api/rankings")
async def get_rankings(
    date: Optional[str] = None,
    top_n: int = Query(default=TOP_N, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    获取各类榜单

    Args:
        date: 日期 (YYYY-MM-DD)，默认为最新
        top_n: 返回前 N 个
        db: 数据库会话

    Returns:
        榜单数据
    """
    try:
        # 确定查询日期
        if date:
            query_date = datetime.strptime(date, '%Y-%m-%d')
        else:
            # 获取最新日期
            latest = db.query(DailyScore.date).order_by(desc(DailyScore.date)).first()
            if not latest:
                raise HTTPException(status_code=404, detail="暂无数据")
            query_date = latest[0]

        # 查询当天的评分数据
        scores = db.query(DailyScore, Stock).join(
            Stock, DailyScore.stock_id == Stock.id
        ).filter(
            DailyScore.date == query_date
        ).all()

        if not scores:
            raise HTTPException(status_code=404, detail=f"未找到 {query_date.date()} 的数据")

        # 构建股票数据列表
        stocks_data = []
        for score, stock in scores:
            stocks_data.append({
                'symbol': stock.symbol,
                'name': stock.name,
                'sector': stock.sector,
                'total_score': score.total_score,
                'price_change': score.price_change,
                'volume_ratio': score.volume_ratio,
                'news_count': score.news_count,
                'hot_rank': score.hot_rank,
                'growth_rank': score.growth_rank,
                'price_change_score': score.price_change_score,
                'volume_score': score.volume_score,
                'news_count_score': score.news_count_score,
                'news_sentiment_score': score.news_sentiment_score,
                'trend_score': score.trend_score,
            })

        # 生成各类榜单
        hot_stocks = sorted(stocks_data, key=lambda x: x['total_score'], reverse=True)[:top_n]
        growth_stocks = sorted(stocks_data, key=lambda x: x['price_change'], reverse=True)[:top_n]
        discussion_stocks = sorted(stocks_data, key=lambda x: x['news_count'], reverse=True)[:top_n]
        active_stocks = sorted(stocks_data, key=lambda x: x['volume_ratio'], reverse=True)[:top_n]

        return {
            'date': query_date.strftime('%Y-%m-%d'),
            'rankings': {
                'hot': hot_stocks,
                'growth': growth_stocks,
                'discussion': discussion_stocks,
                'active': active_stocks,
            }
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="日期格式错误，应为 YYYY-MM-DD")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/stock/{symbol}")
async def get_stock_detail(
    symbol: str,
    days: int = Query(default=30, ge=1, le=90),
    db: Session = Depends(get_db)
):
    """
    获取股票详情

    Args:
        symbol: 股票代码
        days: 历史天数
        db: 数据库会话

    Returns:
        股票详细信息
    """
    try:
        # 查询股票
        stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
        if not stock:
            raise HTTPException(status_code=404, detail=f"未找到股票: {symbol}")

        # 获取历史评分
        start_date = datetime.now() - timedelta(days=days)
        scores = db.query(DailyScore).filter(
            and_(
                DailyScore.stock_id == stock.id,
                DailyScore.date >= start_date
            )
        ).order_by(desc(DailyScore.date)).all()

        # 获取历史价格
        histories = db.query(StockHistory).filter(
            and_(
                StockHistory.stock_id == stock.id,
                StockHistory.date >= start_date
            )
        ).order_by(desc(StockHistory.date)).all()

        # 获取最新新闻
        recent_news = db.query(NewsArticle).filter(
            NewsArticle.stock_id == stock.id
        ).order_by(desc(NewsArticle.published_at)).limit(10).all()

        # 构建响应
        return {
            'symbol': stock.symbol,
            'name': stock.name,
            'sector': stock.sector,
            'latest_score': {
                'total_score': scores[0].total_score if scores else None,
                'hot_rank': scores[0].hot_rank if scores else None,
                'growth_rank': scores[0].growth_rank if scores else None,
                'price_change': scores[0].price_change if scores else None,
                'news_count': scores[0].news_count if scores else None,
            } if scores else None,
            'history': {
                'scores': [
                    {
                        'date': s.date.strftime('%Y-%m-%d'),
                        'total_score': s.total_score,
                        'hot_rank': s.hot_rank,
                        'price_change': s.price_change,
                        'news_count': s.news_count,
                    }
                    for s in scores
                ],
                'prices': [
                    {
                        'date': h.date.strftime('%Y-%m-%d'),
                        'open': h.open_price,
                        'high': h.high_price,
                        'low': h.low_price,
                        'close': h.close_price,
                        'volume': h.volume,
                    }
                    for h in histories
                ]
            },
            'recent_news': [
                {
                    'title': n.title,
                    'source': n.source,
                    'published_at': n.published_at.strftime('%Y-%m-%d %H:%M'),
                    'url': n.url,
                    'sentiment': n.sentiment_score,
                }
                for n in recent_news
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/trending")
async def get_trending_stocks(
    days: int = Query(default=7, ge=1, le=30),
    min_growth: float = Query(default=10.0, ge=0),
    limit: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    获取趋势上升的股票

    Args:
        days: 分析天数
        min_growth: 最小增长率
        limit: 返回数量
        db: 数据库会话

    Returns:
        趋势股票列表
    """
    try:
        analyzer = TrendAnalyzer(db)
        trending = analyzer.get_trending_stocks(days, min_growth, limit)

        return {
            'days': days,
            'min_growth': min_growth,
            'stocks': trending
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/news/{symbol}")
async def get_stock_news(
    symbol: str,
    days: int = Query(default=7, ge=1, le=30),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    获取股票新闻

    Args:
        symbol: 股票代码
        days: 获取多少天内的新闻
        limit: 返回数量
        db: 数据库会话

    Returns:
        新闻列表
    """
    try:
        # 查询股票
        stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
        if not stock:
            raise HTTPException(status_code=404, detail=f"未找到股票: {symbol}")

        # 查询新闻
        start_date = datetime.now() - timedelta(days=days)
        news = db.query(NewsArticle).filter(
            and_(
                NewsArticle.stock_id == stock.id,
                NewsArticle.published_at >= start_date
            )
        ).order_by(desc(NewsArticle.published_at)).limit(limit).all()

        return {
            'symbol': stock.symbol,
            'name': stock.name,
            'news_count': len(news),
            'news': [
                {
                    'title': n.title,
                    'description': n.description,
                    'source': n.source,
                    'published_at': n.published_at.strftime('%Y-%m-%d %H:%M'),
                    'url': n.url,
                    'sentiment': n.sentiment_score,
                }
                for n in news
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/dates")
async def get_available_dates(db: Session = Depends(get_db)):
    """
    获取可用的数据日期列表

    Returns:
        日期列表
    """
    try:
        dates = db.query(DailyScore.date).distinct().order_by(desc(DailyScore.date)).all()

        return {
            'dates': [d[0].strftime('%Y-%m-%d') for d in dates]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/run-analysis")
async def run_analysis_task():
    """
    手动触发分析任务

    Returns:
        任务状态
    """
    try:
        from backend.app.scheduler import DailyAnalysisTask
        import threading

        # 在后台线程中运行任务
        def run_task():
            task = DailyAnalysisTask()
            task.run()

        thread = threading.Thread(target=run_task)
        thread.daemon = True
        thread.start()

        return {
            'status': 'started',
            'message': '分析任务已启动，请等待几分钟后刷新页面查看结果'
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
