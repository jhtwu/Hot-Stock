"""
股票价格数据收集器
使用 yfinance 获取股票历史数据
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
import time
import random
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from config import DEMO_MODE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StockDataCollector:
    """股票数据收集器"""

    def __init__(self, demo_mode: bool = DEMO_MODE):
        self.cache = {}
        self.demo_mode = demo_mode
        if self.demo_mode:
            logger.warning("演示模式已启用，将使用模拟股票数据")

    def get_stock_info(self, symbol: str) -> Optional[Dict]:
        """
        获取股票基本信息（简化版，避免过多 API 请求）

        Args:
            symbol: 股票代码

        Returns:
            股票信息字典
        """
        try:
            # 简化版：只返回股票代码，不请求详细信息
            # 这样可以避免触发 Yahoo Finance 的速率限制
            return {
                'symbol': symbol,
                'name': symbol,  # 暂时使用代码作为名称
                'sector': 'Unknown',
            }
        except Exception as e:
            logger.error(f"获取股票信息失败 {symbol}: {str(e)}")
            return None

    def get_historical_data(
        self,
        symbol: str,
        period: str = "1mo",
        interval: str = "1d",
        max_retries: int = 3
    ) -> Optional[pd.DataFrame]:
        """
        获取股票历史数据（带重试机制）

        Args:
            symbol: 股票代码
            period: 时间周期 (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: 数据间隔 (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
            max_retries: 最大重试次数

        Returns:
            DataFrame 包含 Open, High, Low, Close, Volume
        """
        for attempt in range(max_retries):
            try:
                # 添加随机延迟，避免速率限制
                if attempt > 0:
                    delay = random.uniform(1, 3) * (attempt + 1)
                    logger.info(f"重试 {symbol} (尝试 {attempt + 1}/{max_retries})，延迟 {delay:.1f}s")
                    time.sleep(delay)

                ticker = yf.Ticker(symbol)
                df = ticker.history(period=period, interval=interval)

                if df.empty:
                    logger.warning(f"未获取到数据: {symbol}")
                    return None

                return df

            except Exception as e:
                if "429" in str(e) or "Too Many Requests" in str(e):
                    if attempt < max_retries - 1:
                        logger.warning(f"速率限制 {symbol}，等待后重试...")
                        time.sleep(random.uniform(3, 6))
                        continue
                logger.error(f"获取历史数据失败 {symbol}: {str(e)}")
                return None

        return None

    def _generate_mock_data(self, symbol: str) -> Dict:
        """
        生成模拟股票数据（用于演示）

        Args:
            symbol: 股票代码

        Returns:
            模拟数据字典
        """
        # 为每个股票生成一致的随机种子
        seed = sum(ord(c) for c in symbol)
        random.seed(seed)

        base_price = random.uniform(50, 500)
        change_percent = random.uniform(-5, 8)  # 稍微偏向正增长
        volume = random.uniform(1000000, 100000000)
        volume_ratio = random.uniform(0.5, 2.5)

        return {
            'symbol': symbol,
            'date': datetime.now(),
            'open': base_price * 0.98,
            'high': base_price * 1.03,
            'low': base_price * 0.97,
            'close': base_price,
            'volume': volume,
            'change_percent': change_percent,
            'volume_ratio': volume_ratio,
        }

    def get_latest_data(self, symbol: str) -> Optional[Dict]:
        """
        获取最新交易日数据

        Args:
            symbol: 股票代码

        Returns:
            最新数据字典
        """
        # 如果是演示模式，直接返回模拟数据
        if self.demo_mode:
            return self._generate_mock_data(symbol)

        try:
            df = self.get_historical_data(symbol, period="5d")
            if df is None or df.empty:
                # API 失败时使用模拟数据
                logger.warning(f"无法获取真实数据，使用模拟数据: {symbol}")
                return self._generate_mock_data(symbol)

            latest = df.iloc[-1]
            previous = df.iloc[-2] if len(df) > 1 else latest

            # 计算变化百分比
            change_percent = ((latest['Close'] - previous['Close']) / previous['Close']) * 100

            # 计算平均成交量
            avg_volume = df['Volume'].mean()
            volume_ratio = latest['Volume'] / avg_volume if avg_volume > 0 else 1.0

            return {
                'symbol': symbol,
                'date': latest.name.to_pydatetime(),
                'open': float(latest['Open']),
                'high': float(latest['High']),
                'low': float(latest['Low']),
                'close': float(latest['Close']),
                'volume': float(latest['Volume']),
                'change_percent': float(change_percent),
                'volume_ratio': float(volume_ratio),
            }
        except Exception as e:
            logger.error(f"获取最新数据失败 {symbol}: {str(e)}")
            # 异常时也使用模拟数据
            logger.warning(f"使用模拟数据: {symbol}")
            return self._generate_mock_data(symbol)

    def get_batch_latest_data(self, symbols: List[str], delay_between_requests: float = 0.5) -> Dict[str, Dict]:
        """
        批量获取多个股票的最新数据

        Args:
            symbols: 股票代码列表
            delay_between_requests: 请求之间的延迟（秒）

        Returns:
            字典，key 为股票代码，value 为最新数据
        """
        results = {}
        total = len(symbols)

        for i, symbol in enumerate(symbols, 1):
            logger.info(f"获取数据 ({i}/{total}): {symbol}")
            data = self.get_latest_data(symbol)
            if data:
                results[symbol] = data

            # 添加延迟避免速率限制
            if i < total:
                time.sleep(delay_between_requests)

        return results

    def calculate_trend_indicators(self, symbol: str, days: int = 30) -> Optional[Dict]:
        """
        计算趋势指标

        Args:
            symbol: 股票代码
            days: 计算天数

        Returns:
            趋势指标字典
        """
        try:
            df = self.get_historical_data(symbol, period=f"{days}d")
            if df is None or df.empty:
                return None

            # 计算简单移动平均线
            df['SMA_5'] = df['Close'].rolling(window=5).mean()
            df['SMA_10'] = df['Close'].rolling(window=10).mean()
            df['SMA_20'] = df['Close'].rolling(window=20).mean()

            # 计算相对强弱指数 RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))

            latest = df.iloc[-1]

            # 判断趋势
            trend_up = latest['SMA_5'] > latest['SMA_10'] > latest['SMA_20']

            return {
                'sma_5': float(latest['SMA_5']) if pd.notna(latest['SMA_5']) else None,
                'sma_10': float(latest['SMA_10']) if pd.notna(latest['SMA_10']) else None,
                'sma_20': float(latest['SMA_20']) if pd.notna(latest['SMA_20']) else None,
                'rsi': float(latest['RSI']) if pd.notna(latest['RSI']) else None,
                'trend_up': trend_up,
            }
        except Exception as e:
            logger.error(f"计算趋势指标失败 {symbol}: {str(e)}")
            return None
