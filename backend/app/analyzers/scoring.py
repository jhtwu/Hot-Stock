"""
评分系统
根据多个指标对股票进行综合评分
"""
import numpy as np
from typing import Dict, List
import logging
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from config import SCORING_WEIGHTS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScoringSystem:
    """评分系统"""

    def __init__(self, weights: Dict[str, float] = None):
        """
        初始化评分系统

        Args:
            weights: 各指标权重字典
        """
        self.weights = weights or SCORING_WEIGHTS

    def normalize_score(self, value: float, min_val: float, max_val: float) -> float:
        """
        将值标准化到 0-100 分

        Args:
            value: 原始值
            min_val: 最小值
            max_val: 最大值

        Returns:
            标准化后的分数 (0-100)
        """
        if max_val == min_val:
            return 50.0

        normalized = ((value - min_val) / (max_val - min_val)) * 100
        return max(0.0, min(100.0, normalized))

    def calculate_price_change_score(self, change_percent: float, all_changes: List[float]) -> float:
        """
        计算价格变化分数

        Args:
            change_percent: 价格变化百分比
            all_changes: 所有股票的价格变化列表（用于归一化）

        Returns:
            分数 (0-100)
        """
        if not all_changes:
            return 50.0

        # 使用百分位数进行归一化
        percentile = (np.searchsorted(sorted(all_changes), change_percent) / len(all_changes)) * 100

        return percentile

    def calculate_volume_score(self, volume_ratio: float, all_ratios: List[float]) -> float:
        """
        计算成交量分数

        Args:
            volume_ratio: 成交量比率
            all_ratios: 所有股票的成交量比率列表

        Returns:
            分数 (0-100)
        """
        if not all_ratios:
            return 50.0

        # 成交量异常高是好的信号
        percentile = (np.searchsorted(sorted(all_ratios), volume_ratio) / len(all_ratios)) * 100

        return percentile

    def calculate_news_count_score(self, news_count: int, all_counts: List[int]) -> float:
        """
        计算新闻数量分数

        Args:
            news_count: 新闻数量
            all_counts: 所有股票的新闻数量列表

        Returns:
            分数 (0-100)
        """
        if not all_counts or max(all_counts) == 0:
            return 0.0

        # 新闻数量越多，热度越高
        max_count = max(all_counts)
        score = (news_count / max_count) * 100

        return min(100.0, score)

    def calculate_sentiment_score(self, avg_sentiment: float) -> float:
        """
        计算新闻情绪分数

        Args:
            avg_sentiment: 平均情绪分数 (-1 到 1)

        Returns:
            分数 (0-100)
        """
        # 将 -1 到 1 映射到 0 到 100
        score = (avg_sentiment + 1) * 50

        return max(0.0, min(100.0, score))

    def calculate_trend_score(self, trend_data: Dict) -> float:
        """
        计算趋势分数

        Args:
            trend_data: 趋势数据（包含 SMA, RSI 等）

        Returns:
            分数 (0-100)
        """
        if not trend_data:
            return 50.0

        score = 50.0

        # RSI 指标 (30-70 是正常范围)
        rsi = trend_data.get('rsi')
        if rsi is not None:
            if 40 <= rsi <= 60:
                score += 10  # 中性偏好
            elif 60 < rsi <= 70:
                score += 20  # 强势但未超买
            elif rsi > 70:
                score += 5   # 超买，有风险
            elif 30 <= rsi < 40:
                score += 5   # 偏弱

        # 趋势方向
        if trend_data.get('trend_up'):
            score += 20

        return min(100.0, score)

    def calculate_total_score(self, stock_data: Dict) -> Dict[str, float]:
        """
        计算单个股票的各项分数和总分

        Args:
            stock_data: 股票数据，包含各项指标

        Returns:
            包含各项分数和总分的字典
        """
        scores = {
            'price_change_score': stock_data.get('price_change_score', 0.0),
            'volume_score': stock_data.get('volume_score', 0.0),
            'news_count_score': stock_data.get('news_count_score', 0.0),
            'news_sentiment_score': stock_data.get('news_sentiment_score', 0.0),
            'trend_score': stock_data.get('trend_score', 0.0),
        }

        # 计算加权总分
        total_score = sum(
            scores[key] * self.weights.get(key.replace('_score', ''), 0)
            for key in scores.keys()
        )

        scores['total_score'] = total_score

        return scores

    def score_all_stocks(self, stocks_data: List[Dict]) -> List[Dict]:
        """
        对所有股票进行评分

        Args:
            stocks_data: 股票数据列表

        Returns:
            包含评分的股票数据列表（按总分降序排列）
        """
        if not stocks_data:
            return []

        # 提取各项指标用于归一化
        price_changes = [s.get('price_change', 0.0) for s in stocks_data]
        volume_ratios = [s.get('volume_ratio', 1.0) for s in stocks_data]
        news_counts = [s.get('news_count', 0) for s in stocks_data]

        # 计算每个股票的各项分数
        for stock in stocks_data:
            # 价格变化分数
            stock['price_change_score'] = self.calculate_price_change_score(
                stock.get('price_change', 0.0),
                price_changes
            )

            # 成交量分数
            stock['volume_score'] = self.calculate_volume_score(
                stock.get('volume_ratio', 1.0),
                volume_ratios
            )

            # 新闻数量分数
            stock['news_count_score'] = self.calculate_news_count_score(
                stock.get('news_count', 0),
                news_counts
            )

            # 新闻情绪分数
            avg_sentiment = stock.get('avg_sentiment', 0.0)
            stock['news_sentiment_score'] = self.calculate_sentiment_score(avg_sentiment)

            # 趋势分数
            trend_data = stock.get('trend_data', {})
            stock['trend_score'] = self.calculate_trend_score(trend_data)

            # 计算总分
            scores = self.calculate_total_score(stock)
            stock.update(scores)

        # 按总分排序
        stocks_data.sort(key=lambda x: x.get('total_score', 0), reverse=True)

        return stocks_data

    def get_top_stocks(self, stocks_data: List[Dict], top_n: int = 10) -> Dict:
        """
        获取 Top N 股票榜单

        Args:
            stocks_data: 已评分的股票数据列表
            top_n: 返回前 N 个

        Returns:
            包含各种榜单的字典
        """
        # 按总分排序 - 热度榜
        hot_stocks = sorted(
            stocks_data,
            key=lambda x: x.get('total_score', 0),
            reverse=True
        )[:top_n]

        # 按价格涨幅排序 - 涨幅榜
        growth_stocks = sorted(
            stocks_data,
            key=lambda x: x.get('price_change', 0),
            reverse=True
        )[:top_n]

        # 按新闻数量排序 - 讨论榜
        discussion_stocks = sorted(
            stocks_data,
            key=lambda x: x.get('news_count', 0),
            reverse=True
        )[:top_n]

        # 按成交量比率排序 - 活跃榜
        active_stocks = sorted(
            stocks_data,
            key=lambda x: x.get('volume_ratio', 0),
            reverse=True
        )[:top_n]

        return {
            'hot': hot_stocks,
            'growth': growth_stocks,
            'discussion': discussion_stocks,
            'active': active_stocks,
        }
