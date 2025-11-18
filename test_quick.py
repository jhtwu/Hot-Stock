#!/usr/bin/env python3
"""
快速测试脚本 - 只测试 5 个股票
用于验证系统是否正常工作
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from backend.app.collectors import StockDataCollector, NewsDataCollector
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 测试用的少量股票
TEST_SYMBOLS = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]

def test_stock_collector():
    """测试股票数据收集"""
    print("\n" + "="*50)
    print("测试股票数据收集器")
    print("="*50)

    collector = StockDataCollector()

    print(f"\n正在测试 {len(TEST_SYMBOLS)} 个股票...")
    data = collector.get_batch_latest_data(TEST_SYMBOLS, delay_between_requests=1.5)

    if data:
        print(f"\n✓ 成功获取 {len(data)} 个股票的数据")
        for symbol, stock_data in data.items():
            print(f"\n{symbol}:")
            print(f"  价格: ${stock_data['close']:.2f}")
            print(f"  涨跌幅: {stock_data['change_percent']:.2f}%")
            print(f"  成交量比率: {stock_data['volume_ratio']:.2f}x")
    else:
        print("\n✗ 未能获取数据")
        return False

    return True

def test_news_collector():
    """测试新闻数据收集"""
    print("\n" + "="*50)
    print("测试新闻数据收集器")
    print("="*50)

    collector = NewsDataCollector()

    print(f"\n正在测试 AAPL 的新闻收集...")
    news = collector.get_stock_news("AAPL", "Apple Inc.", days=1)

    if news:
        print(f"\n✓ 获取到 {len(news)} 条新闻")
        if len(news) > 0:
            print(f"\n示例新闻:")
            print(f"  标题: {news[0]['title']}")
            print(f"  来源: {news[0]['source']}")
            print(f"  情绪分数: {news[0]['sentiment_score']:.2f}")
    else:
        print("\n! 未获取到新闻（可能使用的是模拟数据）")

    return True

def main():
    print("\n" + "="*50)
    print("Hot Stock 快速测试")
    print("="*50)
    print("\n这将测试系统的核心功能，预计需要 1-2 分钟...")

    # 测试股票数据收集
    if not test_stock_collector():
        print("\n✗ 股票数据收集测试失败")
        return

    # 测试新闻数据收集
    test_news_collector()

    print("\n" + "="*50)
    print("✓ 测试完成！系统运行正常")
    print("="*50)
    print("\n你现在可以运行完整分析:")
    print("  python manage.py analyze")
    print("\n或者启动 Web 服务器:")
    print("  python manage.py server")
    print()

if __name__ == '__main__':
    main()
