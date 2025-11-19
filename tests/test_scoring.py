"""
评分系统单元测试
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.analyzers.scoring import ScoringSystem
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_normalize_score():
    """测试分数归一化"""
    print("\n【测试 1: 分数归一化】")
    print("-" * 60)

    scoring = ScoringSystem()

    # 测试正常范围
    score = scoring.normalize_score(50, 0, 100)
    assert score == 50.0, "中间值应该是 50"
    print(f"✓ normalize_score(50, 0, 100) = {score}")

    # 测试边界值
    score_min = scoring.normalize_score(0, 0, 100)
    assert score_min == 0.0, "最小值应该是 0"
    print(f"✓ normalize_score(0, 0, 100) = {score_min}")

    score_max = scoring.normalize_score(100, 0, 100)
    assert score_max == 100.0, "最大值应该是 100"
    print(f"✓ normalize_score(100, 0, 100) = {score_max}")

    print("✓ 测试通过")


def test_price_change_score():
    """测试价格变化评分"""
    print("\n【测试 2: 价格变化评分】")
    print("-" * 60)

    scoring = ScoringSystem()

    # 模拟数据
    all_changes = [-5.0, -2.0, 0.0, 2.0, 5.0, 8.0]

    # 测试不同价格变化
    test_cases = [
        (-5.0, "最低"),
        (0.0, "中等"),
        (8.0, "最高"),
    ]

    for change, desc in test_cases:
        score = scoring.calculate_price_change_score(change, all_changes)
        print(f"  {desc} 涨跌幅 {change:+.1f}% -> 分数: {score:.2f}")
        assert 0 <= score <= 100, "分数应该在 0-100 之间"

    print("✓ 测试通过")


def test_volume_score():
    """测试成交量评分"""
    print("\n【测试 3: 成交量评分】")
    print("-" * 60)

    scoring = ScoringSystem()

    all_ratios = [0.5, 0.8, 1.0, 1.5, 2.0, 3.0]

    test_cases = [
        (0.5, "低成交量"),
        (1.0, "正常成交量"),
        (3.0, "高成交量"),
    ]

    for ratio, desc in test_cases:
        score = scoring.calculate_volume_score(ratio, all_ratios)
        print(f"  {desc} {ratio:.1f}x -> 分数: {score:.2f}")
        assert 0 <= score <= 100, "分数应该在 0-100 之间"

    print("✓ 测试通过")


def test_news_count_score():
    """测试新闻数量评分"""
    print("\n【测试 4: 新闻数量评分】")
    print("-" * 60)

    scoring = ScoringSystem()

    all_counts = [0, 2, 5, 10, 15, 20]

    test_cases = [
        (0, "无新闻"),
        (10, "中等新闻"),
        (20, "高新闻"),
    ]

    for count, desc in test_cases:
        score = scoring.calculate_news_count_score(count, all_counts)
        print(f"  {desc} {count} 条 -> 分数: {score:.2f}")
        assert 0 <= score <= 100, "分数应该在 0-100 之间"

    print("✓ 测试通过")


def test_sentiment_score():
    """测试情绪评分"""
    print("\n【测试 5: 情绪评分】")
    print("-" * 60)

    scoring = ScoringSystem()

    test_cases = [
        (-1.0, "极度负面"),
        (-0.5, "负面"),
        (0.0, "中性"),
        (0.5, "正面"),
        (1.0, "极度正面"),
    ]

    for sentiment, desc in test_cases:
        score = scoring.calculate_sentiment_score(sentiment)
        print(f"  {desc} {sentiment:+.1f} -> 分数: {score:.2f}")
        assert 0 <= score <= 100, "分数应该在 0-100 之间"

    print("✓ 测试通过")


def test_total_score():
    """测试综合评分"""
    print("\n【测试 6: 综合评分】")
    print("-" * 60)

    scoring = ScoringSystem()

    # 模拟股票数据
    stock_data = {
        'price_change_score': 80.0,
        'volume_score': 70.0,
        'news_count_score': 60.0,
        'news_sentiment_score': 65.0,
        'trend_score': 75.0,
    }

    scores = scoring.calculate_total_score(stock_data)

    print(f"  各项分数:")
    for key, value in stock_data.items():
        print(f"    {key}: {value:.2f}")

    print(f"\n  综合评分: {scores['total_score']:.2f}")

    assert 'total_score' in scores, "应该包含综合评分"
    assert 0 <= scores['total_score'] <= 100, "综合评分应该在 0-100 之间"

    print("✓ 测试通过")


def test_score_all_stocks():
    """测试批量评分"""
    print("\n【测试 7: 批量评分】")
    print("-" * 60)

    scoring = ScoringSystem()

    # 模拟多个股票数据
    stocks_data = [
        {
            'symbol': 'AAPL',
            'price_change': 5.0,
            'volume_ratio': 1.5,
            'news_count': 10,
            'avg_sentiment': 0.5,
            'trend_data': {'rsi': 65, 'trend_up': True}
        },
        {
            'symbol': 'MSFT',
            'price_change': 3.0,
            'volume_ratio': 1.2,
            'news_count': 8,
            'avg_sentiment': 0.3,
            'trend_data': {'rsi': 55, 'trend_up': True}
        },
        {
            'symbol': 'GOOGL',
            'price_change': -2.0,
            'volume_ratio': 0.8,
            'news_count': 5,
            'avg_sentiment': -0.2,
            'trend_data': {'rsi': 45, 'trend_up': False}
        },
    ]

    scored_stocks = scoring.score_all_stocks(stocks_data)

    print(f"  评分结果:")
    for stock in scored_stocks:
        print(f"    {stock['symbol']}: 总分 {stock['total_score']:.2f}")

    # 验证排序
    assert scored_stocks[0]['total_score'] >= scored_stocks[1]['total_score'], "应该按总分降序排列"
    assert scored_stocks[1]['total_score'] >= scored_stocks[2]['total_score'], "应该按总分降序排列"

    print("✓ 测试通过")


def test_get_top_stocks():
    """测试获取 Top N 股票"""
    print("\n【测试 8: 获取 Top N 股票】")
    print("-" * 60)

    scoring = ScoringSystem()

    # 模拟已评分的股票数据
    stocks_data = []
    for i in range(15):
        stocks_data.append({
            'symbol': f'STOCK{i}',
            'total_score': 100 - i * 5,
            'price_change': 5.0 - i * 0.5,
            'news_count': 20 - i,
            'volume_ratio': 2.0 - i * 0.1,
        })

    rankings = scoring.get_top_stocks(stocks_data, top_n=10)

    print(f"\n  榜单类型:")
    for list_type, stocks in rankings.items():
        print(f"    {list_type}: {len(stocks)} 个股票")
        assert len(stocks) <= 10, f"{list_type} 榜单应该不超过 10 个"

    print("\n  热度榜 Top 3:")
    for i, stock in enumerate(rankings['hot'][:3], 1):
        print(f"    {i}. {stock['symbol']} - 分数: {stock['total_score']:.2f}")

    print("✓ 测试通过")


def main():
    """运行所有测试"""
    print("\n" + "="*80)
    print("评分系统 - 单元测试")
    print("="*80)

    tests = [
        ("分数归一化", test_normalize_score),
        ("价格变化评分", test_price_change_score),
        ("成交量评分", test_volume_score),
        ("新闻数量评分", test_news_count_score),
        ("情绪评分", test_sentiment_score),
        ("综合评分", test_total_score),
        ("批量评分", test_score_all_stocks),
        ("获取 Top N", test_get_top_stocks),
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


if __name__ == '__main__':
    main()
