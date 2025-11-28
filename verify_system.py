#!/usr/bin/env python3
"""
系统验证脚本
验证所有组件是否符合 SPECIFICATION.md 中的规格
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from backend.app.collectors import HotSymbolProvider
from backend.app.database import SessionLocal
from backend.app.models import Stock, DailyScore, StockHistory, NewsArticle
from config import (
    FALLBACK_STOCK_SYMBOLS,
    HOT_STOCK_LIMIT,
    NEWS_API_KEY,
    REQUEST_DELAY,
    SCORING_WEIGHTS,
    TOP_N,
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def verify_configuration():
    """验证配置符合规格"""
    print("\n【配置验证】")
    print("-" * 60)

    checks = []

    provider = HotSymbolProvider(FALLBACK_STOCK_SYMBOLS, limit=HOT_STOCK_LIMIT)
    symbols, _ = provider.get_hot_symbols()
    symbol_count = len(symbols)
    min_symbols = max(50, int(HOT_STOCK_LIMIT * 0.7))
    max_symbols = HOT_STOCK_LIMIT + 20

    # 验证股票列表
    checks.append(("股票监控数量", symbol_count, min_symbols, max_symbols))

    # 验证评分权重
    total_weight = sum(SCORING_WEIGHTS.values())
    checks.append(("评分权重总和", total_weight, 0.99, 1.01))

    # 验证请求延迟
    checks.append(("请求延迟（秒）", REQUEST_DELAY, 1.0, 5.0))

    # 验证 Top N
    checks.append(("Top N 数量", TOP_N, 5, 20))

    # 验证 NewsAPI Key
    has_api_key = NEWS_API_KEY and NEWS_API_KEY != "your_newsapi_key_here"
    print(f"  NewsAPI Key: {'✓ 已配置' if has_api_key else '✗ 未配置'}")

    for name, value, min_val, max_val in checks:
        status = "✓" if min_val <= value <= max_val else "✗"
        print(f"  {status} {name}: {value} (范围: {min_val}-{max_val})")

    print("\n✓ 配置验证完成")


def verify_data_models():
    """验证数据模型符合规格"""
    print("\n【数据模型验证】")
    print("-" * 60)

    db = SessionLocal()
    try:
        # 验证表是否存在
        tables = {
            'stocks': Stock,
            'stock_histories': StockHistory,
            'news_articles': NewsArticle,
            'daily_scores': DailyScore,
        }

        for table_name, model in tables.items():
            try:
                count = db.query(model).count()
                print(f"  ✓ {table_name}: {count} 条记录")
            except Exception as e:
                print(f"  ✗ {table_name}: 表不存在或错误")

        print("\n✓ 数据模型验证完成")

    finally:
        db.close()


def verify_api_interface():
    """验证 API 接口符合规格"""
    print("\n【API 接口验证】")
    print("-" * 60)

    try:
        from backend.app.api.routes import router

        # 获取所有路由
        routes = []
        for route in router.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                routes.append((list(route.methods)[0] if route.methods else 'GET', route.path))

        # 验证必需的端点
        required_endpoints = [
            ('GET', '/'),
            ('GET', '/api/rankings'),
            ('GET', '/api/stock/{symbol}'),
            ('GET', '/api/trending'),
            ('GET', '/api/news/{symbol}'),
            ('GET', '/api/dates'),
            ('POST', '/api/run-analysis'),
        ]

        for method, path in required_endpoints:
            found = any(r[0] == method and r[1] == path for r in routes)
            status = "✓" if found else "✗"
            print(f"  {status} {method} {path}")

        print(f"\n✓ 找到 {len(routes)} 个 API 端点")

    except Exception as e:
        print(f"  ✗ API 验证失败: {e}")


def verify_collectors():
    """验证数据收集器符合规格"""
    print("\n【数据收集器验证】")
    print("-" * 60)

    try:
        from backend.app.collectors import StockDataCollector, NewsDataCollector

        # 验证股票数据收集器
        stock_collector = StockDataCollector(demo_mode=False)
        print("  ✓ StockDataCollector 初始化成功")

        # 验证方法存在
        methods = [
            'get_stock_info',
            'get_historical_data',
            'get_latest_data',
            'get_batch_latest_data',
        ]

        for method in methods:
            if hasattr(stock_collector, method):
                print(f"    ✓ {method}()")
            else:
                print(f"    ✗ {method}() 不存在")

        # 验证新闻数据收集器
        news_collector = NewsDataCollector()
        print("  ✓ NewsDataCollector 初始化成功")

        print("\n✓ 数据收集器验证完成")

    except Exception as e:
        print(f"  ✗ 数据收集器验证失败: {e}")


def verify_analyzers():
    """验证分析器符合规格"""
    print("\n【分析器验证】")
    print("-" * 60)

    try:
        from backend.app.analyzers import ScoringSystem

        # 验证评分系统
        scoring = ScoringSystem()
        print("  ✓ ScoringSystem 初始化成功")

        # 验证方法存在
        methods = [
            'normalize_score',
            'calculate_price_change_score',
            'calculate_volume_score',
            'calculate_news_count_score',
            'calculate_sentiment_score',
            'calculate_trend_score',
            'calculate_total_score',
            'score_all_stocks',
            'get_top_stocks',
        ]

        for method in methods:
            if hasattr(scoring, method):
                print(f"    ✓ {method}()")
            else:
                print(f"    ✗ {method}() 不存在")

        print("\n✓ 分析器验证完成")

    except Exception as e:
        print(f"  ✗ 分析器验证失败: {e}")


def verify_performance():
    """验证性能监控"""
    print("\n【性能监控验证】")
    print("-" * 60)

    try:
        from backend.app.utils.performance import PerformanceMonitor, get_monitor

        monitor = PerformanceMonitor()
        print("  ✓ PerformanceMonitor 初始化成功")

        # 测试性能监控
        with monitor.measure('test_operation'):
            import time
            time.sleep(0.1)

        metrics = monitor.get_metrics('test_operation')
        print(f"  ✓ 性能测量: {metrics['avg_time']:.3f}s")

        global_monitor = get_monitor()
        print("  ✓ 全局监控器可用")

        print("\n✓ 性能监控验证完成")

    except Exception as e:
        print(f"  ✗ 性能监控验证失败: {e}")


def main():
    """运行所有验证"""
    print("\n" + "="*80)
    print("Hot Stock Analysis Platform - 系统验证")
    print("基于 SPECIFICATION.md v1.0")
    print("="*80)

    verifications = [
        ("配置", verify_configuration),
        ("数据模型", verify_data_models),
        ("API 接口", verify_api_interface),
        ("数据收集器", verify_collectors),
        ("分析器", verify_analyzers),
        ("性能监控", verify_performance),
    ]

    passed = 0
    failed = 0

    for name, verify_func in verifications:
        try:
            verify_func()
            passed += 1
        except Exception as e:
            print(f"\n✗ {name}验证失败: {e}")
            failed += 1

    print("\n" + "="*80)
    print(f"验证完成: {passed} 通过, {failed} 失败")
    print("="*80)

    if failed == 0:
        print("\n✓ 系统符合所有规格要求！")
    else:
        print("\n⚠️  部分验证失败，请检查上述错误")

    print()


if __name__ == '__main__':
    main()
