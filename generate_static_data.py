#!/usr/bin/env python3
"""
生成靜態 JSON 資料用於 GitHub Pages 部署
每天運行此腳本來更新網站資料
"""
import json
import sys
from pathlib import Path
from datetime import datetime

# 添加項目路徑
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR / "backend"))

from app.database.db import SessionLocal
from app.database.models import StockAnalysis, StockData, NewsItem
from app.collectors.stock_data import StockDataCollector
from app.collectors.news_data import NewsDataCollector
from app.analyzers.scoring import StockScorer
from app.utils.logger import logger


def run_analysis():
    """運行完整的數據收集和分析流程"""
    logger.info("=== 開始數據收集和分析 ===")

    # 1. 收集股票數據
    logger.info("步驟 1: 收集股票數據...")
    stock_collector = StockDataCollector()
    stock_data = stock_collector.collect_batch()
    logger.info(f"成功收集 {len(stock_data)} 支股票數據")

    # 2. 收集新聞數據
    logger.info("步驟 2: 收集新聞數據...")
    news_collector = NewsDataCollector()
    news_data = news_collector.collect_batch()
    logger.info(f"成功收集 {sum(len(news) for news in news_data.values())} 條新聞")

    # 3. 計算分數並儲存分析結果
    logger.info("步驟 3: 計算股票分數...")
    db = SessionLocal()
    try:
        scorer = StockScorer(db)
        analysis_results = []

        for stock in stock_data:
            try:
                scores = scorer.calculate_comprehensive_score(
                    stock['symbol'],
                    stock,
                    news_data.get(stock['symbol'], [])
                )

                # 創建分析記錄
                analysis = StockAnalysis(
                    symbol=stock['symbol'],
                    name=stock['name'],
                    price=stock['current_price'],
                    change_percent=stock['change_percent'],
                    volume=stock['volume'],
                    news_count=scores['news_count'],
                    sentiment_score=scores['sentiment_score'],
                    hot_score=scores['hot_score'],
                    growth_score=scores['growth_score'],
                    discussion_score=scores['discussion_score'],
                    active_score=scores['active_score']
                )
                db.add(analysis)
                analysis_results.append(analysis)

            except Exception as e:
                logger.error(f"分析股票 {stock['symbol']} 失敗: {e}")
                continue

        db.commit()
        logger.info(f"成功分析 {len(analysis_results)} 支股票")
        return True

    except Exception as e:
        logger.error(f"分析過程出錯: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def generate_rankings_json(output_dir: Path):
    """生成排行榜 JSON 文件"""
    db = SessionLocal()
    try:
        # 獲取最新分析日期
        latest_analysis = db.query(StockAnalysis).order_by(
            StockAnalysis.analysis_date.desc()
        ).first()

        if not latest_analysis:
            logger.error("沒有找到分析數據")
            return False

        analysis_date = latest_analysis.analysis_date.date()

        # 獲取當天所有分析結果
        analyses = db.query(StockAnalysis).filter(
            StockAnalysis.analysis_date >= analysis_date
        ).all()

        # 生成各類排行榜
        rankings = {
            'hot': sorted(analyses, key=lambda x: x.hot_score, reverse=True)[:10],
            'growth': sorted(analyses, key=lambda x: x.growth_score, reverse=True)[:10],
            'discussion': sorted(analyses, key=lambda x: x.discussion_score, reverse=True)[:10],
            'active': sorted(analyses, key=lambda x: x.active_score, reverse=True)[:10]
        }

        # 格式化輸出
        output = {}
        for rank_type, stocks in rankings.items():
            output[rank_type] = [
                {
                    'rank': idx + 1,
                    'symbol': stock.symbol,
                    'name': stock.name,
                    'price': float(stock.price) if stock.price else 0,
                    'change_percent': float(stock.change_percent) if stock.change_percent else 0,
                    'volume': int(stock.volume) if stock.volume else 0,
                    'score': float(getattr(stock, f'{rank_type}_score')),
                    'news_count': stock.news_count or 0,
                    'sentiment_score': float(stock.sentiment_score) if stock.sentiment_score else 0
                }
                for idx, stock in enumerate(stocks)
            ]

        # 添加更新時間
        output['last_updated'] = latest_analysis.analysis_date.isoformat()
        output['date'] = analysis_date.isoformat()

        # 寫入 JSON 文件
        rankings_file = output_dir / 'rankings.json'
        with open(rankings_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        logger.info(f"✓ 成功生成排行榜數據: {rankings_file}")
        return True

    except Exception as e:
        logger.error(f"生成排行榜 JSON 失敗: {e}")
        return False
    finally:
        db.close()


def generate_stocks_json(output_dir: Path):
    """生成個別股票詳細資料 JSON 文件"""
    db = SessionLocal()
    try:
        # 獲取最新分析結果
        latest_date = db.query(StockAnalysis.analysis_date).order_by(
            StockAnalysis.analysis_date.desc()
        ).first()

        if not latest_date:
            return False

        analyses = db.query(StockAnalysis).filter(
            StockAnalysis.analysis_date >= latest_date[0].date()
        ).all()

        # 為每支股票生成詳細資料
        stocks_dir = output_dir / 'stocks'
        stocks_dir.mkdir(exist_ok=True)

        for analysis in analyses:
            # 獲取歷史數據
            historical_data = db.query(StockData).filter(
                StockData.symbol == analysis.symbol
            ).order_by(StockData.date.desc()).limit(30).all()

            # 獲取新聞
            news_items = db.query(NewsItem).filter(
                NewsItem.symbol == analysis.symbol
            ).order_by(NewsItem.published_at.desc()).limit(10).all()

            stock_detail = {
                'symbol': analysis.symbol,
                'name': analysis.name,
                'current_price': float(analysis.price) if analysis.price else 0,
                'change_percent': float(analysis.change_percent) if analysis.change_percent else 0,
                'volume': int(analysis.volume) if analysis.volume else 0,
                'scores': {
                    'hot': float(analysis.hot_score),
                    'growth': float(analysis.growth_score),
                    'discussion': float(analysis.discussion_score),
                    'active': float(analysis.active_score)
                },
                'news_count': analysis.news_count or 0,
                'sentiment_score': float(analysis.sentiment_score) if analysis.sentiment_score else 0,
                'historical_data': [
                    {
                        'date': data.date.isoformat(),
                        'open': float(data.open_price) if data.open_price else 0,
                        'high': float(data.high_price) if data.high_price else 0,
                        'low': float(data.low_price) if data.low_price else 0,
                        'close': float(data.close_price) if data.close_price else 0,
                        'volume': int(data.volume) if data.volume else 0
                    }
                    for data in historical_data
                ],
                'news': [
                    {
                        'title': news.title,
                        'url': news.url,
                        'source': news.source,
                        'published_at': news.published_at.isoformat() if news.published_at else None,
                        'sentiment': news.sentiment
                    }
                    for news in news_items
                ],
                'last_updated': analysis.analysis_date.isoformat()
            }

            # 寫入個別股票 JSON
            stock_file = stocks_dir / f'{analysis.symbol}.json'
            with open(stock_file, 'w', encoding='utf-8') as f:
                json.dump(stock_detail, f, ensure_ascii=False, indent=2)

        logger.info(f"✓ 成功生成 {len(analyses)} 支股票的詳細資料")
        return True

    except Exception as e:
        logger.error(f"生成股票詳細資料失敗: {e}")
        return False
    finally:
        db.close()


def generate_summary_json(output_dir: Path):
    """生成摘要資訊 JSON"""
    db = SessionLocal()
    try:
        # 統計資訊
        total_stocks = db.query(StockAnalysis).count()
        latest_analysis = db.query(StockAnalysis).order_by(
            StockAnalysis.analysis_date.desc()
        ).first()

        if not latest_analysis:
            return False

        summary = {
            'last_updated': latest_analysis.analysis_date.isoformat(),
            'date': latest_analysis.analysis_date.date().isoformat(),
            'total_stocks_analyzed': total_stocks,
            'api_mode': 'static',
            'data_sources': ['Stooq', 'NewsAPI'],
            'update_frequency': 'daily'
        }

        summary_file = output_dir / 'summary.json'
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        logger.info(f"✓ 成功生成摘要資訊: {summary_file}")
        return True

    except Exception as e:
        logger.error(f"生成摘要資訊失敗: {e}")
        return False
    finally:
        db.close()


def main():
    """主流程"""
    print("=" * 60)
    print("Hot Stock Analysis - 靜態資料生成器")
    print("=" * 60)
    print()

    # 創建輸出目錄
    output_dir = BASE_DIR / 'frontend' / 'data'
    output_dir.mkdir(exist_ok=True)

    # 步驟 1: 運行分析
    print("📊 步驟 1/4: 運行數據分析...")
    if not run_analysis():
        print("❌ 數據分析失敗")
        return 1
    print("✓ 數據分析完成\n")

    # 步驟 2: 生成排行榜
    print("📈 步驟 2/4: 生成排行榜資料...")
    if not generate_rankings_json(output_dir):
        print("❌ 生成排行榜失敗")
        return 1
    print("✓ 排行榜資料完成\n")

    # 步驟 3: 生成股票詳細資料
    print("📋 步驟 3/4: 生成股票詳細資料...")
    if not generate_stocks_json(output_dir):
        print("❌ 生成股票資料失敗")
        return 1
    print("✓ 股票詳細資料完成\n")

    # 步驟 4: 生成摘要
    print("📄 步驟 4/4: 生成摘要資訊...")
    if not generate_summary_json(output_dir):
        print("❌ 生成摘要失敗")
        return 1
    print("✓ 摘要資訊完成\n")

    print("=" * 60)
    print("✅ 所有靜態資料生成完成！")
    print("=" * 60)
    print(f"輸出目錄: {output_dir}")
    print()
    print("生成的文件：")
    print("  - frontend/data/rankings.json       (排行榜)")
    print("  - frontend/data/summary.json        (摘要資訊)")
    print("  - frontend/data/stocks/*.json       (個別股票資料)")
    print()
    print("下一步：請運行 git add、commit 和 push 來更新網站")
    print("=" * 60)

    return 0


if __name__ == '__main__':
    sys.exit(main())
