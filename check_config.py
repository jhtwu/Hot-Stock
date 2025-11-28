#!/usr/bin/env python3
"""
配置检查脚本
验证系统配置是否正确
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import (
    DEMO_MODE,
    FALLBACK_STOCK_SYMBOLS,
    HOT_STOCK_LIMIT,
    NEWS_API_KEY,
    REQUEST_DELAY,
    USE_DYNAMIC_SYMBOLS,
)
from backend.app.collectors import HotSymbolProvider

print("\n" + "="*60)
print("Hot Stock 配置检查")
print("="*60)

# 检查 NewsAPI Key
print("\n【NewsAPI 配置】")
if NEWS_API_KEY and NEWS_API_KEY != "your_newsapi_key_here":
    print(f"✓ NewsAPI Key: {NEWS_API_KEY[:10]}...{NEWS_API_KEY[-4:]}")
    print("  状态: 已配置")
else:
    print("✗ NewsAPI Key: 未设置")
    print("  提示: 编辑 .env 文件设置 NEWS_API_KEY")
    print("  申请地址: https://newsapi.org/")

# 检查演示模式
print("\n【运行模式】")
if DEMO_MODE:
    print("✓ 演示模式: 启用")
    print("  说明: 将使用模拟股票数据")
else:
    print("✓ 正常模式: 启用")
    print("  说明: 将尝试获取真实股票数据")
    print("  备注: API 失败时会自动降级到模拟数据")

# 检查股票列表
print("\n【股票监控】")
provider = HotSymbolProvider(FALLBACK_STOCK_SYMBOLS, limit=HOT_STOCK_LIMIT)
symbols, _ = provider.get_hot_symbols()
mode = "動態熱門榜單 (Yahoo Finance)" if USE_DYNAMIC_SYMBOLS else "備援清單 (config.py)"
print(f"✓ 股票模式: {mode}")
print(f"✓ 监控股票数量: {len(symbols)} 个 (目標: 前 {HOT_STOCK_LIMIT} 檔)")
print(f"  股票列表: {', '.join(symbols[:5])}...")

# 检查请求配置
print("\n【API 配置】")
print(f"✓ 请求延迟: {REQUEST_DELAY} 秒")
estimated_time = len(symbols) * REQUEST_DELAY / 60
print(f"  预计分析时间: {estimated_time:.1f} 分钟")

# 检查数据库
from backend.app.database import engine
from sqlalchemy import inspect

print("\n【数据库状态】")
inspector = inspect(engine)
tables = inspector.get_table_names()

if tables:
    print(f"✓ 数据库已初始化")
    print(f"  表数量: {len(tables)}")
    print(f"  表列表: {', '.join(tables)}")
else:
    print("✗ 数据库未初始化")
    print("  执行: python manage.py init")

# 检查是否有数据
from backend.app.database import SessionLocal
from backend.app.models import Stock, DailyScore

db = SessionLocal()
try:
    stock_count = db.query(Stock).count()
    score_count = db.query(DailyScore).count()

    print("\n【数据统计】")
    if stock_count > 0:
        print(f"✓ 股票记录: {stock_count} 个")
    else:
        print("○ 股票记录: 0 个（尚未运行分析）")

    if score_count > 0:
        print(f"✓ 评分记录: {score_count} 个")
    else:
        print("○ 评分记录: 0 个（尚未运行分析）")

finally:
    db.close()

# 给出建议
print("\n" + "="*60)
print("【下一步建议】")
print("="*60)

if not tables:
    print("\n1. 初始化数据库:")
    print("   python manage.py init")
elif stock_count == 0:
    print("\n1. 运行首次分析:")
    print("   python manage.py analyze")
else:
    print("\n✓ 系统配置正常，可以启动服务器:")
    print("   python manage.py server")
    print("\n  访问地址: http://localhost:8000")

print("\n" + "="*60)
print()
