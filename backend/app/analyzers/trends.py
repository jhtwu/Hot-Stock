"""
趋势分析器
分析股票的历史趋势和增长情况
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging

from backend.app.models import DailyScore, Stock

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TrendAnalyzer:
    """趋势分析器"""

    def __init__(self, db: Session):
        """
        初始化趋势分析器

        Args:
            db: 数据库会话
        """
        self.db = db

    def get_historical_scores(
        self,
        symbol: str,
        days: int = 7
    ) -> List[Dict]:
        """
        获取股票的历史评分

        Args:
            symbol: 股票代码
            days: 查询天数

        Returns:
            历史评分列表
        """
        try:
            stock = self.db.query(Stock).filter(Stock.symbol == symbol).first()
            if not stock:
                return []

            start_date = datetime.now() - timedelta(days=days)

            scores = self.db.query(DailyScore).filter(
                DailyScore.stock_id == stock.id,
                DailyScore.date >= start_date
            ).order_by(DailyScore.date.desc()).all()

            return [
                {
                    'date': score.date,
                    'total_score': score.total_score,
                    'hot_rank': score.hot_rank,
                    'growth_rank': score.growth_rank,
                    'news_count': score.news_count,
                    'price_change': score.price_change,
                }
                for score in scores
            ]
        except Exception as e:
            logger.error(f"获取历史评分失败 {symbol}: {str(e)}")
            return []

    def calculate_growth_rate(
        self,
        symbol: str,
        days: int = 7
    ) -> Optional[float]:
        """
        计算讨论度增长率

        Args:
            symbol: 股票代码
            days: 计算天数

        Returns:
            增长率百分比
        """
        scores = self.get_historical_scores(symbol, days)

        if len(scores) < 2:
            return None

        # 比较最近一天和之前平均值
        latest_score = scores[0]['total_score']
        avg_previous = sum(s['total_score'] for s in scores[1:]) / len(scores[1:])

        if avg_previous == 0:
            return 0.0

        growth_rate = ((latest_score - avg_previous) / avg_previous) * 100

        return growth_rate

    def calculate_news_growth(
        self,
        symbol: str,
        days: int = 7
    ) -> Optional[float]:
        """
        计算新闻数量增长率

        Args:
            symbol: 股票代码
            days: 计算天数

        Returns:
            新闻增长率百分比
        """
        scores = self.get_historical_scores(symbol, days)

        if len(scores) < 2:
            return None

        latest_news = scores[0]['news_count']
        avg_previous_news = sum(s['news_count'] for s in scores[1:]) / len(scores[1:])

        if avg_previous_news == 0:
            return 100.0 if latest_news > 0 else 0.0

        growth_rate = ((latest_news - avg_previous_news) / avg_previous_news) * 100

        return growth_rate

    def get_trending_stocks(
        self,
        days: int = 7,
        min_growth: float = 10.0,
        limit: int = 20
    ) -> List[Dict]:
        """
        获取趋势上升的股票

        Args:
            days: 分析天数
            min_growth: 最小增长率要求
            limit: 返回数量限制

        Returns:
            趋势股票列表
        """
        try:
            # 获取所有股票
            stocks = self.db.query(Stock).all()

            trending = []
            for stock in stocks:
                growth_rate = self.calculate_growth_rate(stock.symbol, days)
                news_growth = self.calculate_news_growth(stock.symbol, days)

                if growth_rate and growth_rate >= min_growth:
                    trending.append({
                        'symbol': stock.symbol,
                        'name': stock.name,
                        'growth_rate': growth_rate,
                        'news_growth': news_growth or 0.0,
                    })

            # 按增长率排序
            trending.sort(key=lambda x: x['growth_rate'], reverse=True)

            return trending[:limit]

        except Exception as e:
            logger.error(f"获取趋势股票失败: {str(e)}")
            return []

    def get_rank_changes(
        self,
        symbol: str,
        days: int = 7
    ) -> Dict:
        """
        获取股票排名变化

        Args:
            symbol: 股票代码
            days: 查询天数

        Returns:
            排名变化信息
        """
        scores = self.get_historical_scores(symbol, days)

        if len(scores) < 2:
            return {
                'current_hot_rank': None,
                'previous_hot_rank': None,
                'hot_rank_change': 0,
                'current_growth_rank': None,
                'previous_growth_rank': None,
                'growth_rank_change': 0,
            }

        latest = scores[0]
        previous = scores[1]

        hot_rank_change = 0
        if latest['hot_rank'] and previous['hot_rank']:
            hot_rank_change = previous['hot_rank'] - latest['hot_rank']  # 正数表示上升

        growth_rank_change = 0
        if latest['growth_rank'] and previous['growth_rank']:
            growth_rank_change = previous['growth_rank'] - latest['growth_rank']

        return {
            'current_hot_rank': latest['hot_rank'],
            'previous_hot_rank': previous['hot_rank'],
            'hot_rank_change': hot_rank_change,
            'current_growth_rank': latest['growth_rank'],
            'previous_growth_rank': previous['growth_rank'],
            'growth_rank_change': growth_rank_change,
        }
