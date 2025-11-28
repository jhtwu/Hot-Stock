"""
每日分析任务
收集数据、分析并生成报表
"""
from datetime import datetime
from typing import List, Dict
from sqlalchemy.orm import Session
import logging
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.app.database import SessionLocal
from backend.app.models import Stock, StockHistory, NewsArticle, DailyScore
from backend.app.collectors import HotSymbolProvider, StockDataCollector, NewsDataCollector
from backend.app.analyzers import ScoringSystem
from config import (
    FALLBACK_STOCK_SYMBOLS,
    HOT_STOCK_LIMIT,
    REQUEST_DELAY,
    TOP_N,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DailyAnalysisTask:
    """每日分析任务"""

    def __init__(self):
        self.stock_collector = StockDataCollector()
        self.news_collector = NewsDataCollector()
        self.scoring_system = ScoringSystem()
        self.symbol_provider = HotSymbolProvider(FALLBACK_STOCK_SYMBOLS, limit=HOT_STOCK_LIMIT)
        self.target_symbols: List[str] = []
        self.symbol_metadata: Dict[str, Dict[str, str]] = {}

    def _load_target_symbols(self):
        """取得今日要分析的股票清單。"""
        symbols, metadata = self.symbol_provider.get_hot_symbols()
        if not symbols:
            raise ValueError("未能取得任何熱門美股代碼")

        self.target_symbols = symbols
        self.symbol_metadata = metadata

        preview = ", ".join(self.target_symbols[:5])
        logger.info("本次分析將使用 %d 檔熱門美股 (前 5 檔: %s)", len(self.target_symbols), preview)

    def run(self):
        """
        执行每日分析任务
        """
        logger.info("=" * 50)
        logger.info(f"开始每日分析任务: {datetime.now()}")
        logger.info("=" * 50)

        db = SessionLocal()
        try:
            # 0. 取得今日熱門美股清單
            self._load_target_symbols()

            # 1. 更新或创建股票信息
            self._update_stocks(db)

            # 2. 收集股票价格数据
            stock_data = self._collect_stock_data(db)

            # 3. 收集新闻数据
            news_data = self._collect_news_data(db, stock_data)

            # 4. 整合数据
            integrated_data = self._integrate_data(stock_data, news_data, db)

            # 5. 计算评分
            scored_stocks = self.scoring_system.score_all_stocks(integrated_data)

            # 6. 保存评分到数据库
            self._save_scores(db, scored_stocks)

            # 7. 生成榜单
            rankings = self.scoring_system.get_top_stocks(scored_stocks, TOP_N)

            # 8. 显示结果
            self._display_results(rankings)

            db.commit()
            logger.info("每日分析任务完成！")

        except Exception as e:
            logger.error(f"每日分析任务失败: {str(e)}", exc_info=True)
            db.rollback()
        finally:
            db.close()

    def _update_stocks(self, db: Session):
        """
        更新股票基本信息

        Args:
            db: 数据库会话
        """
        logger.info("更新股票信息...")

        for symbol in self.target_symbols:
            stock = db.query(Stock).filter(Stock.symbol == symbol).first()
            metadata = self.symbol_metadata.get(symbol, {})

            info = self.stock_collector.get_stock_info(
                symbol,
                fallback_name=metadata.get("name"),
                fallback_sector=metadata.get("sector"),
            )

            if not stock:
                if info:
                    stock = Stock(
                        symbol=info['symbol'],
                        name=info['name'],
                        sector=info['sector']
                    )
                    db.add(stock)
                    logger.info(f"添加新股票: {symbol} ({stock.name})")
                continue

            if info:
                if (not stock.sector or stock.sector in ("Unknown", "未分類")) and info['sector']:
                    stock.sector = info['sector']
                    logger.info(f"更新股票板塊: {symbol} -> {stock.sector}")
                if (not stock.name or stock.name == stock.symbol) and info['name'] != stock.name:
                    stock.name = info['name']
                    logger.info(f"更新股票名稱: {symbol} -> {stock.name}")

        db.commit()

    def _collect_stock_data(self, db: Session) -> Dict[str, Dict]:
        """
        收集股票价格数据

        Args:
            db: 数据库会话

        Returns:
            股票数据字典
        """
        total_symbols = len(self.target_symbols)
        logger.info(f"收集 {total_symbols} 个股票的价格数据...")
        logger.info(
            "请求延迟: %.1f秒，预计需要 %.1f 分钟",
            REQUEST_DELAY,
            total_symbols * REQUEST_DELAY / 60,
        )

        stock_data = self.stock_collector.get_batch_latest_data(
            self.target_symbols,
            delay_between_requests=REQUEST_DELAY,
        )

        # 保存到数据库
        for symbol, data in stock_data.items():
            stock = db.query(Stock).filter(Stock.symbol == symbol).first()
            if not stock:
                continue

            history = StockHistory(
                stock_id=stock.id,
                date=data['date'],
                open_price=data['open'],
                high_price=data['high'],
                low_price=data['low'],
                close_price=data['close'],
                volume=data['volume'],
                change_percent=data['change_percent'],
                volume_ratio=data['volume_ratio']
            )
            db.add(history)

            # 获取趋势数据
            trend_data = self.stock_collector.calculate_trend_indicators(symbol)
            stock_data[symbol]['trend_data'] = trend_data or {}

        db.commit()
        logger.info(f"收集了 {len(stock_data)} 个股票的价格数据")

        return stock_data

    def _collect_news_data(
        self,
        db: Session,
        stock_data: Dict[str, Dict]
    ) -> Dict[str, List[Dict]]:
        """
        收集新闻数据

        Args:
            db: 数据库会话
            stock_data: 股票数据（包含公司名称）

        Returns:
            新闻数据字典
        """
        logger.info("收集新闻数据...")

        # 构建股票信息字典
        stock_info = {}
        for symbol in self.target_symbols:
            stock = db.query(Stock).filter(Stock.symbol == symbol).first()
            if stock:
                stock_info[symbol] = {'name': stock.name or self.symbol_metadata.get(symbol, {}).get("name")}

        news_data = self.news_collector.get_batch_news(self.target_symbols, stock_info)

        # 保存到数据库
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        for symbol, articles in news_data.items():
            stock = db.query(Stock).filter(Stock.symbol == symbol).first()
            if not stock:
                continue

            for article in articles:
                # 检查是否已存在
                existing = db.query(NewsArticle).filter(
                    NewsArticle.stock_id == stock.id,
                    NewsArticle.url == article['url']
                ).first()

                if not existing:
                    news = NewsArticle(
                        stock_id=stock.id,
                        title=article['title'],
                        description=article['description'],
                        url=article['url'],
                        source=article['source'],
                        published_at=article['published_at'],
                        sentiment_score=article['sentiment_score']
                    )
                    db.add(news)

        db.commit()
        logger.info(f"收集了 {sum(len(v) for v in news_data.values())} 条新闻")

        return news_data

    def _integrate_data(
        self,
        stock_data: Dict[str, Dict],
        news_data: Dict[str, List[Dict]],
        db: Session
    ) -> List[Dict]:
        """
        整合股票和新闻数据

        Args:
            stock_data: 股票数据
            news_data: 新闻数据
            db: 数据库会话

        Returns:
            整合后的数据列表
        """
        logger.info("整合数据...")

        integrated = []

        for symbol in self.target_symbols:
            stock = db.query(Stock).filter(Stock.symbol == symbol).first()
            if not stock:
                continue

            stock_info = stock_data.get(symbol, {})
            news_list = news_data.get(symbol, [])
            name = stock.name or self.symbol_metadata.get(symbol, {}).get("name") or symbol
            sector = stock.sector or self.symbol_metadata.get(symbol, {}).get("sector")

            # 计算新闻统计
            news_count = len(news_list)
            avg_sentiment = 0.0
            if news_count > 0:
                avg_sentiment = sum(n['sentiment_score'] for n in news_list) / news_count

            integrated.append({
                'symbol': symbol,
                'name': name,
                'sector': sector,
                'price_change': stock_info.get('change_percent', 0.0),
                'volume_ratio': stock_info.get('volume_ratio', 1.0),
                'news_count': news_count,
                'avg_sentiment': avg_sentiment,
                'trend_data': stock_info.get('trend_data', {}),
                'close_price': stock_info.get('close', 0.0),
                'volume': stock_info.get('volume', 0.0),
            })

        return integrated

    def _save_scores(self, db: Session, scored_stocks: List[Dict]):
        """
        保存评分到数据库

        Args:
            db: 数据库会话
            scored_stocks: 已评分的股票列表
        """
        logger.info("保存评分...")

        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # 获取榜单
        rankings = self.scoring_system.get_top_stocks(scored_stocks, TOP_N)

        # 创建排名映射
        hot_ranks = {s['symbol']: i + 1 for i, s in enumerate(rankings['hot'])}
        growth_ranks = {s['symbol']: i + 1 for i, s in enumerate(rankings['growth'])}

        for stock_data in scored_stocks:
            stock = db.query(Stock).filter(Stock.symbol == stock_data['symbol']).first()
            if not stock:
                continue

            # 检查是否已存在今日评分
            existing = db.query(DailyScore).filter(
                DailyScore.stock_id == stock.id,
                DailyScore.date == today
            ).first()

            if existing:
                # 更新
                existing.price_change_score = stock_data['price_change_score']
                existing.volume_score = stock_data['volume_score']
                existing.news_count_score = stock_data['news_count_score']
                existing.news_sentiment_score = stock_data['news_sentiment_score']
                existing.trend_score = stock_data['trend_score']
                existing.total_score = stock_data['total_score']
                existing.news_count = stock_data['news_count']
                existing.price_change = stock_data['price_change']
                existing.volume_ratio = stock_data['volume_ratio']
                existing.hot_rank = hot_ranks.get(stock_data['symbol'])
                existing.growth_rank = growth_ranks.get(stock_data['symbol'])
            else:
                # 创建新记录
                score = DailyScore(
                    stock_id=stock.id,
                    date=today,
                    price_change_score=stock_data['price_change_score'],
                    volume_score=stock_data['volume_score'],
                    news_count_score=stock_data['news_count_score'],
                    news_sentiment_score=stock_data['news_sentiment_score'],
                    trend_score=stock_data['trend_score'],
                    total_score=stock_data['total_score'],
                    news_count=stock_data['news_count'],
                    price_change=stock_data['price_change'],
                    volume_ratio=stock_data['volume_ratio'],
                    hot_rank=hot_ranks.get(stock_data['symbol']),
                    growth_rank=growth_ranks.get(stock_data['symbol'])
                )
                db.add(score)

        db.commit()

    def _display_results(self, rankings: Dict):
        """
        显示分析结果

        Args:
            rankings: 榜单字典
        """
        logger.info("\n" + "=" * 80)
        logger.info("每日分析报表")
        logger.info("=" * 80)

        # 热度榜 Top 10
        logger.info("\n【热度榜 Top 10】")
        logger.info("-" * 80)
        logger.info(f"{'排名':<6} {'代码':<8} {'名称':<30} {'总分':<10} {'涨幅%':<10}")
        logger.info("-" * 80)
        for i, stock in enumerate(rankings['hot'], 1):
            logger.info(
                f"{i:<6} {stock['symbol']:<8} {stock['name'][:28]:<30} "
                f"{stock['total_score']:<10.2f} {stock['price_change']:<10.2f}"
            )

        # 涨幅榜 Top 10
        logger.info("\n【涨幅榜 Top 10】")
        logger.info("-" * 80)
        logger.info(f"{'排名':<6} {'代码':<8} {'名称':<30} {'涨幅%':<10} {'成交量比':<10}")
        logger.info("-" * 80)
        for i, stock in enumerate(rankings['growth'], 1):
            logger.info(
                f"{i:<6} {stock['symbol']:<8} {stock['name'][:28]:<30} "
                f"{stock['price_change']:<10.2f} {stock['volume_ratio']:<10.2f}"
            )

        # 讨论榜 Top 10
        logger.info("\n【讨论榜 Top 10】")
        logger.info("-" * 80)
        logger.info(f"{'排名':<6} {'代码':<8} {'名称':<30} {'新闻数':<10} {'情绪分':<10}")
        logger.info("-" * 80)
        for i, stock in enumerate(rankings['discussion'], 1):
            logger.info(
                f"{i:<6} {stock['symbol']:<8} {stock['name'][:28]:<30} "
                f"{stock['news_count']:<10} {stock['avg_sentiment']:<10.2f}"
            )

        logger.info("\n" + "=" * 80)
