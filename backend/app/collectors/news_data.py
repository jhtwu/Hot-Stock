"""
新闻数据收集器
使用 NewsAPI 和其他来源收集财经新闻
"""
from newsapi import NewsApiClient
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from config import NEWS_API_KEY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsDataCollector:
    """新闻数据收集器"""

    def __init__(self, api_key: str = NEWS_API_KEY):
        """
        初始化新闻收集器

        Args:
            api_key: NewsAPI 密钥
        """
        self.api_key = api_key
        if api_key and api_key != "your_newsapi_key_here":
            try:
                self.newsapi = NewsApiClient(api_key=api_key)
            except Exception as e:
                logger.warning(f"NewsAPI 初始化失败: {str(e)}, 将使用模拟数据")
                self.newsapi = None
        else:
            logger.warning("未设置 NewsAPI key，将使用模拟数据")
            self.newsapi = None

    def get_stock_news(
        self,
        symbol: str,
        company_name: str = None,
        days: int = 1
    ) -> List[Dict]:
        """
        获取股票相关新闻

        Args:
            symbol: 股票代码
            company_name: 公司名称（可选）
            days: 获取多少天内的新闻

        Returns:
            新闻列表
        """
        if not self.newsapi:
            return self._get_mock_news(symbol, days)

        try:
            # 计算时间范围
            to_date = datetime.now()
            from_date = to_date - timedelta(days=days)

            # 构建搜索查询
            query = symbol
            if company_name:
                query = f"{symbol} OR {company_name}"

            # 调用 NewsAPI
            response = self.newsapi.get_everything(
                q=query,
                from_param=from_date.strftime('%Y-%m-%d'),
                to=to_date.strftime('%Y-%m-%d'),
                language='en',
                sort_by='publishedAt',
                page_size=100
            )

            articles = []
            if response['status'] == 'ok':
                for article in response['articles']:
                    articles.append({
                        'title': article['title'],
                        'description': article['description'],
                        'url': article['url'],
                        'source': article['source']['name'],
                        'published_at': datetime.strptime(
                            article['publishedAt'],
                            '%Y-%m-%dT%H:%M:%SZ'
                        ),
                        'sentiment_score': self._analyze_sentiment(
                            article['title'],
                            article['description']
                        )
                    })

            logger.info(f"获取到 {len(articles)} 条新闻: {symbol}")
            return articles

        except Exception as e:
            logger.error(f"获取新闻失败 {symbol}: {str(e)}")
            return self._get_mock_news(symbol, days)

    def get_batch_news(
        self,
        symbols: List[str],
        stock_info: Dict[str, Dict],
        days: int = 1
    ) -> Dict[str, List[Dict]]:
        """
        批量获取多个股票的新闻

        Args:
            symbols: 股票代码列表
            stock_info: 股票信息字典（包含公司名称）
            days: 获取多少天内的新闻

        Returns:
            字典，key 为股票代码，value 为新闻列表
        """
        results = {}
        for symbol in symbols:
            company_name = stock_info.get(symbol, {}).get('name')
            logger.info(f"获取新闻: {symbol}")
            news = self.get_stock_news(symbol, company_name, days)
            if news:
                results[symbol] = news

        return results

    def _analyze_sentiment(self, title: str, description: str) -> float:
        """
        简单的情绪分析

        Args:
            title: 标题
            description: 描述

        Returns:
            情绪分数 (-1 到 1)
        """
        # 正面词汇
        positive_words = [
            'surge', 'soar', 'rally', 'gain', 'jump', 'rise', 'up', 'high',
            'beat', 'exceed', 'strong', 'growth', 'profit', 'bullish', 'upgrade',
            'buy', 'outperform', 'positive', 'boost', 'record', 'breakthrough'
        ]

        # 负面词汇
        negative_words = [
            'fall', 'drop', 'plunge', 'decline', 'down', 'low', 'miss',
            'weak', 'loss', 'bearish', 'downgrade', 'sell', 'underperform',
            'negative', 'concern', 'risk', 'crash', 'tumble', 'slump'
        ]

        text = f"{title} {description}".lower() if description else title.lower()

        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)

        total = positive_count + negative_count
        if total == 0:
            return 0.0

        # 计算情绪分数
        score = (positive_count - negative_count) / total
        return max(-1.0, min(1.0, score))

    def _get_mock_news(self, symbol: str, days: int) -> List[Dict]:
        """
        生成模拟新闻数据（用于测试）

        Args:
            symbol: 股票代码
            days: 天数

        Returns:
            模拟新闻列表
        """
        import random

        templates = [
            f"{symbol} Stock Surges on Strong Earnings Report",
            f"{symbol} Announces New Product Launch",
            f"Analysts Upgrade {symbol} Price Target",
            f"{symbol} Reports Better Than Expected Revenue",
            f"Why {symbol} Stock Is Moving Today",
        ]

        news = []
        for i in range(random.randint(3, 10)):
            news.append({
                'title': random.choice(templates),
                'description': f"Latest news about {symbol} stock performance and market analysis.",
                'url': f"https://example.com/news/{symbol.lower()}-{i}",
                'source': random.choice(['MarketWatch', 'CNBC', 'Bloomberg', 'Reuters']),
                'published_at': datetime.now() - timedelta(hours=random.randint(1, days * 24)),
                'sentiment_score': random.uniform(-0.3, 0.7)  # 稍微偏向正面
            })

        return news
