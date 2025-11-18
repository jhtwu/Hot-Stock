"""
配置文件 - 美股分析平台
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 项目根目录
BASE_DIR = Path(__file__).parent

# 加载 .env 文件
load_dotenv(BASE_DIR / '.env')

# 数据库配置
DATABASE_URL = f"sqlite:///{BASE_DIR}/data/hotstock.db"

# API 配置
API_HOST = "0.0.0.0"
API_PORT = 8000

# 新闻 API 配置 (需要申请免费的 NewsAPI key: https://newsapi.org/)
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "your_newsapi_key_here")

# 数据收集配置
# 监控的股票池（精选最热门股票，避免 API 速率限制）
# 注意：一次性监控太多股票可能触发 Yahoo Finance API 限制
# 如需添加更多股票，建议分批运行或增加延迟
STOCK_SYMBOLS = [
    # 科技巨头
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "AMD",
    # 金融科技
    "JPM", "V", "MA", "PYPL",
    # 消费品牌
    "WMT", "DIS", "NFLX", "NKE",
    # 医疗保健
    "JNJ", "PFE", "UNH",
    # 热门科技股
    "COIN", "PLTR", "RBLX"
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

# API 请求配置
REQUEST_DELAY = 1.0  # 请求之间的延迟（秒），避免速率限制
MAX_RETRIES = 3      # API 请求最大重试次数

# 演示模式（使用模拟数据）
# 如果无法访问 Yahoo Finance API，设置为 True
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

# 日志配置
LOG_LEVEL = "INFO"
LOG_FILE = BASE_DIR / "logs" / "hotstock.log"
