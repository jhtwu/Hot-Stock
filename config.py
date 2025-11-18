"""
配置文件 - 美股分析平台
"""
import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).parent

# 数据库配置
DATABASE_URL = f"sqlite:///{BASE_DIR}/data/hotstock.db"

# API 配置
API_HOST = "0.0.0.0"
API_PORT = 8000

# 新闻 API 配置 (需要申请免费的 NewsAPI key: https://newsapi.org/)
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "your_newsapi_key_here")

# 数据收集配置
# 监控的股票池（可以根据需要添加更多）
STOCK_SYMBOLS = [
    # 科技股
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "AMD", "INTC", "CRM",
    # 金融股
    "JPM", "BAC", "WFC", "GS", "MS", "C", "V", "MA", "PYPL", "SQ",
    # 消费股
    "WMT", "KO", "PEP", "NKE", "SBUX", "MCD", "DIS", "NFLX", "BABA", "JD",
    # 医疗股
    "JNJ", "PFE", "UNH", "ABBV", "TMO", "MRK", "LLY", "BMY", "AMGN", "GILD",
    # 能源股
    "XOM", "CVX", "COP", "SLB", "EOG",
    # 其他热门股
    "COIN", "RBLX", "HOOD", "RIVN", "LCID", "NIO", "PLTR", "SOFI", "SHOP", "SQ"
]

# 评分权重配置
SCORING_WEIGHTS = {
    "price_change": 0.25,      # 价格变化权重
    "volume_ratio": 0.20,      # 成交量比率权重
    "news_count": 0.25,        # 新闻数量权重
    "news_sentiment": 0.15,    # 新闻情绪权重
    "trend_score": 0.15,       # 趋势分数权重
}

# Top N 配置
TOP_N = 10

# 数据收集时间配置
COLLECT_TIME = "16:30"  # 美股收盘后收集数据 (UTC)

# 日志配置
LOG_LEVEL = "INFO"
LOG_FILE = BASE_DIR / "logs" / "hotstock.log"
