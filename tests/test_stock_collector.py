"""
股票数据收集器单元测试
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.collectors.stock_data import StockDataCollector
from backend.app.utils.performance import get_monitor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_stock_info():
    """测试获取股票基本信息"""
    print("\n【测试 1: 获取股票基本信息】")
    print("-" * 60)

    collector = StockDataCollector(demo_mode=False)
    symbol = "AAPL"

    info = collector.get_stock_info(symbol)

    assert info is not None, "应该返回股票信息"
    assert info['symbol'] == symbol, "股票代码应该匹配"
    assert 'name' in info, "应该包含公司名称"
    assert 'sector' in info, "应该包含行业信息"

    print(f"✓ 股票信息: {info}")
    print("✓ 测试通过")


def test_historical_data():
    """测试获取历史数据"""
    print("\n【测试 2: 获取历史数据】")
    print("-" * 60)

    collector = StockDataCollector(demo_mode=False)
    monitor = get_monitor()

    test_symbols = ["AAPL", "MSFT", "GOOGL"]

    for symbol in test_symbols:
        print(f"\n测试 {symbol}...")

        with monitor.measure(f'fetch_history_{symbol}'):
            df = collector.get_historical_data(symbol, period="5d")

        if df is not None and not df.empty:
            print(f"✓ 成功获取数据")
            print(f"  数据点数量: {len(df)}")
            print(f"  列: {list(df.columns)}")
            print(f"  最新日期: {df.index[-1]}")

            # 验证数据格式
            assert 'Open' in df.columns, "应该包含开盘价"
            assert 'High' in df.columns, "应该包含最高价"
            assert 'Low' in df.columns, "应该包含最低价"
            assert 'Close' in df.columns, "应该包含收盘价"
            assert 'Volume' in df.columns, "应该包含成交量"

            print(f"✓ 数据格式验证通过")
        else:
            print(f"✗ 未能获取数据")

    print("\n" + monitor.report())


def test_latest_data():
    """测试获取最新数据"""
    print("\n【测试 3: 获取最新交易日数据】")
    print("-" * 60)

    collector = StockDataCollector(demo_mode=False)
    symbol = "AAPL"

    data = collector.get_latest_data(symbol)

    if data:
        print(f"✓ 成功获取最新数据")
        print(f"  股票代码: {data['symbol']}")
        print(f"  日期: {data['date']}")
        print(f"  收盘价: ${data['close']:.2f}")
        print(f"  涨跌幅: {data['change_percent']:.2f}%")
        print(f"  成交量比率: {data['volume_ratio']:.2f}x")

        # 验证数据字段
        required_fields = ['symbol', 'date', 'open', 'high', 'low', 'close', 'volume', 'change_percent', 'volume_ratio']
        for field in required_fields:
            assert field in data, f"应该包含字段: {field}"

        print("✓ 数据字段验证通过")
    else:
        print("✗ 未能获取最新数据")


def test_batch_collection():
    """测试批量数据收集"""
    print("\n【测试 4: 批量数据收集】")
    print("-" * 60)

    collector = StockDataCollector(demo_mode=False)
    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]

    print(f"批量获取 {len(symbols)} 个股票的数据...")

    monitor = get_monitor()
    with monitor.measure('batch_collection'):
        results = collector.get_batch_latest_data(symbols, delay_between_requests=2.0)

    print(f"\n✓ 成功获取 {len(results)} / {len(symbols)} 个股票的数据")

    for symbol, data in results.items():
        print(f"  {symbol}: ${data['close']:.2f} ({data['change_percent']:+.2f}%)")

    success_rate = len(results) / len(symbols) * 100
    print(f"\n成功率: {success_rate:.1f}%")

    # 验证成功率
    assert success_rate >= 60, "成功率应该 >= 60%"
    print("✓ 测试通过")


def test_data_sources():
    """测试数据源优先级"""
    print("\n【测试 5: 数据源优先级】")
    print("-" * 60)

    collector = StockDataCollector(demo_mode=False)
    symbol = "AAPL"

    # 清空缓存
    collector.cache.clear()

    # 测试 Stooq
    print("测试 Stooq 数据源...")
    stooq_df = collector._fetch_stooq_history(symbol)

    if stooq_df is not None:
        print(f"✓ Stooq 数据源可用")
        print(f"  数据点: {len(stooq_df)}")
    else:
        print("✗ Stooq 数据源不可用")

    # 测试整体获取（会尝试 Stooq 然后 Yahoo）
    print("\n测试整体数据获取...")
    df = collector.get_historical_data(symbol, period="5d")

    if df is not None:
        print(f"✓ 成功获取数据")
        print(f"  使用的数据源: {'Stooq' if stooq_df is not None else 'Yahoo Finance'}")
    else:
        print("✗ 所有数据源都失败")


def main():
    """运行所有测试"""
    print("\n" + "="*80)
    print("股票数据收集器 - 单元测试")
    print("="*80)

    tests = [
        ("获取股票基本信息", test_stock_info),
        ("获取历史数据", test_historical_data),
        ("获取最新数据", test_latest_data),
        ("批量数据收集", test_batch_collection),
        ("数据源优先级", test_data_sources),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"\n✗ 测试失败: {e}")
            failed += 1
        except Exception as e:
            print(f"\n✗ 测试错误: {e}")
            failed += 1

    print("\n" + "="*80)
    print(f"测试完成: {passed} 通过, {failed} 失败")
    print("="*80)

    # 显示性能报告
    monitor = get_monitor()
    print(monitor.report())


if __name__ == '__main__':
    main()
