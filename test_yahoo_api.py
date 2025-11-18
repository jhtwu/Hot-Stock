#!/usr/bin/env python3
"""
Yahoo Finance API 测试脚本
测试是否能成功获取真实股票数据
"""
import yfinance as yf
import time

print("\n" + "="*60)
print("Yahoo Finance API 测试")
print("="*60)

# 测试单个股票
test_symbols = ["AAPL", "MSFT", "GOOGL"]

print("\n【方法 1: 使用 yf.download()】")
print("-" * 60)

for symbol in test_symbols:
    print(f"\n正在测试 {symbol}...")
    try:
        df = yf.download(
            symbol,
            period="5d",
            interval="1d",
            progress=False,
            show_errors=False,
            timeout=30
        )

        if not df.empty:
            latest = df.iloc[-1]
            print(f"✓ 成功获取数据!")
            print(f"  日期: {df.index[-1].strftime('%Y-%m-%d')}")
            print(f"  收盘价: ${latest['Close']:.2f}")
            print(f"  成交量: {latest['Volume']:,.0f}")
        else:
            print(f"✗ 数据为空")
    except Exception as e:
        print(f"✗ 失败: {str(e)[:100]}")

    time.sleep(2)  # 延迟避免速率限制

print("\n" + "="*60)
print("【方法 2: 使用 Ticker.history()】")
print("-" * 60)

for symbol in test_symbols:
    print(f"\n正在测试 {symbol}...")
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="5d")

        if not df.empty:
            latest = df.iloc[-1]
            print(f"✓ 成功获取数据!")
            print(f"  日期: {df.index[-1].strftime('%Y-%m-%d')}")
            print(f"  收盘价: ${latest['Close']:.2f}")
            print(f"  成交量: {latest['Volume']:,.0f}")
        else:
            print(f"✗ 数据为空")
    except Exception as e:
        print(f"✗ 失败: {str(e)[:100]}")

    time.sleep(2)

print("\n" + "="*60)
print("【诊断建议】")
print("="*60)

print("""
如果所有测试都失败，可能的原因：

1. 网络连接问题
   - 检查是否能访问 https://finance.yahoo.com
   - 尝试使用代理或 VPN

2. IP 被 Yahoo Finance 限制
   - 等待一段时间后重试
   - 使用不同的网络环境

3. yfinance 库版本问题
   - 尝试升级: pip install --upgrade yfinance

4. 防火墙阻止
   - 检查防火墙设置
   - 尝试关闭防火墙后测试

如果部分测试成功：
- 系统可以获取真实数据
- 批量请求时需要增加延迟
- 建议将 REQUEST_DELAY 设置为 3-5 秒
""")

print("="*60)
print()
