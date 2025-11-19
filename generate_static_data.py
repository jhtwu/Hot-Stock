#!/usr/bin/env python3
"""
生成靜態 JSON 資料用於 GitHub Pages 部署
流程:
  1. 執行每日分析任務（等同於 python manage.py analyze）
  2. 將最新榜單、股票詳情與摘要轉為 JSON
輸出位置: frontend/data/*
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

from sqlalchemy import desc

# 確保可以匯入 backend 套件
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from backend.app.database import SessionLocal, init_db  # type: ignore  # noqa: E402
from backend.app.models import (  # type: ignore  # noqa: E402
    Stock,
    DailyScore,
    StockHistory,
    NewsArticle,
)
from backend.app.scheduler.daily_task import DailyAnalysisTask  # type: ignore  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("static-data")


def run_analysis() -> bool:
    """運行每日分析任務，確保資料是最新的。"""
    logger.info("📊 開始執行每日分析任務...")
    try:
        task = DailyAnalysisTask()
        task.run()
        logger.info("✓ 每日分析任務完成")
        return True
    except Exception as exc:  # pragma: no cover - 僅在部署腳本使用
        logger.error("❌ 分析任務失敗: %s", exc)
        return False


def _latest_score_date(db) -> datetime | None:
    latest = db.query(DailyScore.date).order_by(desc(DailyScore.date)).first()
    return latest[0] if latest else None


def _latest_histories(db) -> Dict[int, StockHistory]:
    """為每支股票取得最新的歷史行情。"""
    history_map: Dict[int, StockHistory] = {}
    histories = db.query(StockHistory).order_by(desc(StockHistory.date)).all()
    for history in histories:
        if history.stock_id not in history_map:
            history_map[history.stock_id] = history
    return history_map


def _to_float(value) -> float:
    return float(value) if value is not None else 0.0


def _to_int(value) -> int:
    return int(value) if value is not None else 0


def generate_rankings_json(output_dir: Path) -> bool:
    """生成排行榜 JSON 文件。"""
    db = SessionLocal()
    try:
        latest_date = _latest_score_date(db)
        if not latest_date:
            logger.error("❌ 尚未找到任何評分資料，請先運行分析任務")
            return False

        scores: List[Tuple[DailyScore, Stock]] = (
            db.query(DailyScore, Stock)
            .join(Stock, DailyScore.stock_id == Stock.id)
            .filter(DailyScore.date == latest_date)
            .all()
        )

        history_map = _latest_histories(db)

        def build_entry(score: DailyScore, stock: Stock) -> Dict:
            history = history_map.get(stock.id)
            price = _to_float(history.close_price) if history else 0.0
            volume = _to_float(history.volume) if history else 0.0
            return {
                "symbol": stock.symbol,
                "name": stock.name,
                "sector": stock.sector or "未分類",
                "price": price,
                "change_percent": _to_float(score.price_change),
                "volume": int(volume),
                "volume_ratio": _to_float(score.volume_ratio),
                "score": _to_float(score.total_score),
                "news_count": score.news_count or 0,
                "sentiment_score": _to_float(score.news_sentiment_score),
            }

        entries = [build_entry(score, stock) for score, stock in scores]

        rankings = {
            "hot": sorted(entries, key=lambda x: x["score"], reverse=True)[:10],
            "growth": sorted(entries, key=lambda x: x["change_percent"], reverse=True)[:10],
            "discussion": sorted(entries, key=lambda x: x["news_count"], reverse=True)[:10],
            "active": sorted(entries, key=lambda x: x["volume_ratio"], reverse=True)[:10],
            "date": latest_date.date().isoformat(),
            "last_updated": latest_date.isoformat(),
        }

        rankings_file = output_dir / "rankings.json"
        with open(rankings_file, "w", encoding="utf-8") as fh:
            json.dump(rankings, fh, ensure_ascii=False, indent=2)

        logger.info("✓ 排行榜資料已輸出至 %s", rankings_file)
        return True

    except Exception as exc:  # pragma: no cover
        logger.error("❌ 生成排行榜失敗: %s", exc)
        return False
    finally:
        db.close()


def generate_stocks_json(output_dir: Path) -> bool:
    """為每支股票生成詳細資料 JSON。"""
    db = SessionLocal()
    try:
        latest_date = _latest_score_date(db)
        if not latest_date:
            logger.error("❌ 尚未找到任何評分資料")
            return False

        scores: List[Tuple[DailyScore, Stock]] = (
            db.query(DailyScore, Stock)
            .join(Stock, DailyScore.stock_id == Stock.id)
            .filter(DailyScore.date == latest_date)
            .all()
        )

        stocks_dir = output_dir / "stocks"
        if stocks_dir.exists():
            for file in stocks_dir.glob("*.json"):
                file.unlink()
        stocks_dir.mkdir(exist_ok=True)

        for score, stock in scores:
            history_records = (
                db.query(StockHistory)
                .filter(StockHistory.stock_id == stock.id)
                .order_by(desc(StockHistory.date))
                .limit(30)
                .all()
            )
            latest_history = history_records[0] if history_records else None

            news_records = (
                db.query(NewsArticle)
                .filter(NewsArticle.stock_id == stock.id)
                .order_by(desc(NewsArticle.published_at))
                .limit(10)
                .all()
            )

            stock_detail = {
                "symbol": stock.symbol,
                "name": stock.name,
                "sector": stock.sector or "未分類",
                "current_price": _to_float(latest_history.close_price) if latest_history else 0.0,
                "change_percent": _to_float(score.price_change),
                "volume": _to_int(latest_history.volume) if latest_history else 0,
                "scores": {
                    "hot": _to_float(score.total_score),
                    "growth": _to_float(score.price_change_score),
                    "discussion": _to_float(score.news_count_score),
                    "active": _to_float(score.volume_score),
                },
                "news_count": score.news_count or 0,
                "sentiment_score": _to_float(score.news_sentiment_score),
                "historical_data": [
                    {
                        "date": hist.date.strftime("%Y-%m-%d"),
                        "open": _to_float(hist.open_price),
                        "high": _to_float(hist.high_price),
                        "low": _to_float(hist.low_price),
                        "close": _to_float(hist.close_price),
                        "volume": _to_int(hist.volume),
                        "change_percent": _to_float(hist.change_percent),
                        "volume_ratio": _to_float(hist.volume_ratio),
                    }
                    for hist in reversed(history_records)
                ],
                "news": [
                    {
                        "title": news.title,
                        "url": news.url,
                        "source": news.source,
                        "published_at": news.published_at.strftime("%Y-%m-%d %H:%M")
                        if news.published_at
                        else None,
                        "sentiment": _to_float(news.sentiment_score),
                    }
                    for news in news_records
                ],
                "last_updated": latest_date.isoformat(),
                "latest_score": {
                    "total_score": _to_float(score.total_score),
                    "hot_rank": score.hot_rank,
                    "growth_rank": score.growth_rank,
                    "price_change": _to_float(score.price_change),
                    "news_count": score.news_count or 0,
                },
            }

            stock_file = stocks_dir / f"{stock.symbol}.json"
            with open(stock_file, "w", encoding="utf-8") as fh:
                json.dump(stock_detail, fh, ensure_ascii=False, indent=2)

        logger.info("✓ 股票詳細資料已輸出至 %s", stocks_dir)
        return True

    except Exception as exc:  # pragma: no cover
        logger.error("❌ 生成股票詳細資料失敗: %s", exc)
        return False
    finally:
        db.close()


def generate_summary_json(output_dir: Path) -> bool:
    """生成摘要資訊 JSON。"""
    db = SessionLocal()
    try:
        latest_date = _latest_score_date(db)
        if not latest_date:
            return False

        stock_count = db.query(Stock).count()
        summary = {
            "last_updated": latest_date.isoformat(),
            "date": latest_date.date().isoformat(),
            "total_stocks_analyzed": stock_count,
            "api_mode": "static",
            "data_sources": ["Stooq", "NewsAPI"],
            "update_frequency": "daily",
        }

        summary_file = output_dir / "summary.json"
        with open(summary_file, "w", encoding="utf-8") as fh:
            json.dump(summary, fh, ensure_ascii=False, indent=2)

        logger.info("✓ 摘要資訊已輸出至 %s", summary_file)
        return True

    except Exception as exc:  # pragma: no cover
        logger.error("❌ 生成摘要資訊失敗: %s", exc)
        return False
    finally:
        db.close()


def main() -> int:
    """主流程。"""
    print("=" * 60)
    print("Hot Stock Analysis - 靜態資料生成器")
    print("=" * 60)
    print()

    init_db()  # 確保資料表存在

    output_dir = BASE_DIR / "frontend" / "data"
    output_dir.mkdir(exist_ok=True)

    print("📊 步驟 1/4: 運行每日分析...")
    if not run_analysis():
        return 1
    print("✓ 分析完成\n")

    print("📈 步驟 2/4: 生成排行榜資料...")
    if not generate_rankings_json(output_dir):
        return 1
    print("✓ 排行榜完成\n")

    print("📋 步驟 3/4: 生成股票詳細資料...")
    if not generate_stocks_json(output_dir):
        return 1
    print("✓ 股票資料完成\n")

    print("📄 步驟 4/4: 生成摘要資訊...")
    if not generate_summary_json(output_dir):
        return 1
    print("✓ 摘要完成\n")

    print("=" * 60)
    print("✅ 所有靜態資料生成完成！")
    print("=" * 60)
    print(f"輸出目錄: {output_dir}")
    print("生成檔案: rankings.json、summary.json、stocks/*.json")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
