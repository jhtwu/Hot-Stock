#!/usr/bin/env python3
"""
简单的网络连接测试
"""
import urllib.request
import json

print("\n" + "="*60)
print("网络连接测试")
print("="*60)

# 测试 Yahoo Finance
print("\n【测试 1: Yahoo Finance 可达性】")
try:
    url = "https://query1.finance.yahoo.com/v8/finance/chart/AAPL?range=5d&interval=1d"
    req = urllib.request.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0')

    with urllib.request.urlopen(req, timeout=10) as response:
        data = json.loads(response.read())

    if 'chart' in data and 'result' in data['chart']:
        result = data['chart']['result'][0]
        prices = result['indicators']['quote'][0]
        timestamps = result['timestamp']

        print("✓ Yahoo Finance 可访问!")
        print(f"  获取到 {len(timestamps)} 个数据点")
        if prices['close']:
            latest_price = [p for p in prices['close'] if p][-1]
            print(f"  AAPL 最新价格: ${latest_price:.2f}")
    else:
        print("✗ 响应格式异常")

except Exception as e:
    print(f"✗ 无法访问 Yahoo Finance")
    print(f"  错误: {str(e)}")

# 测试 NewsAPI
print("\n【测试 2: NewsAPI 可达性】")
try:
    api_key = "586d6197e7b34a01b9ea74e11f5f9dfc"
    url = f"https://newsapi.org/v2/everything?q=Apple&apiKey={api_key}&pageSize=5"

    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as response:
        data = json.loads(response.read())

    if data.get('status') == 'ok':
        articles = data.get('articles', [])
        print("✓ NewsAPI 可访问!")
        print(f"  API Key 有效")
        print(f"  获取到 {len(articles)} 条新闻")
        if articles:
            print(f"  示例: {articles[0]['title'][:50]}...")
    else:
        print(f"✗ NewsAPI 返回错误: {data.get('message')}")

except Exception as e:
    print(f"✗ 无法访问 NewsAPI")
    print(f"  错误: {str(e)}")

print("\n" + "="*60)
print("测试完成")
print("="*60)
print()
