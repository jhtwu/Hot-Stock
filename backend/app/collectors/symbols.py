"""
熱門股票清單提供者
透過 Yahoo Finance 的 most_active screener 取得前一交易日最活躍的美股列表
"""
from __future__ import annotations

import logging
from typing import Dict, List, Tuple
from pathlib import Path
import sys

import requests

# 將專案根目錄加入匯入路徑
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from config import HOT_STOCK_LIMIT, USE_DYNAMIC_SYMBOLS, STOCK_SECTORS  # type: ignore  # noqa: E402

logger = logging.getLogger(__name__)


class HotSymbolProvider:
    """從公開來源取得熱門美股代碼，失敗時退回預設清單。"""

    YAHOO_MOST_ACTIVE_URL = "https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved"

    def __init__(self, fallback_symbols: List[str], limit: int = HOT_STOCK_LIMIT):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (HotStockBot)",
                "Accept": "application/json, text/plain, */*",
            }
        )
        self.fallback_symbols = [s.upper() for s in fallback_symbols]
        self.limit = limit

    def _fetch_from_yahoo(self) -> List[Dict[str, str]]:
        """
        從 Yahoo Finance most_actives screener 抓取熱門美股。

        Returns:
            內含 symbol/name/sector 的清單
        """
        params = {"scrIds": "most_actives", "count": self.limit, "offset": 0}
        response = self.session.get(self.YAHOO_MOST_ACTIVE_URL, params=params, timeout=10)
        response.raise_for_status()

        payload = response.json()
        results = payload.get("finance", {}).get("result", [])
        if not results:
            raise ValueError("Yahoo Finance most_actives 無結果")

        quotes = results[0].get("quotes", []) or []
        symbols: List[Dict[str, str]] = []
        seen = set()

        for quote in quotes:
            symbol = quote.get("symbol")
            if not symbol:
                continue

            symbol = symbol.upper()
            if symbol in seen:
                continue

            quote_type = (quote.get("quoteType") or "").lower()
            if quote_type and quote_type not in ("equity", "etf"):
                continue

            market = (quote.get("market") or "").lower()
            exchange = (quote.get("fullExchangeName") or "").lower()

            # 只保留美股市場
            if market and "us" not in market:
                continue
            if exchange and all(key not in exchange for key in ("nasdaq", "nyse")):
                continue

            name = quote.get("shortName") or quote.get("longName") or symbol
            sector = (
                quote.get("sectorDisp")
                or quote.get("industryDisp")
                or STOCK_SECTORS.get(symbol)
                or "未分類"
            )

            symbols.append({"symbol": symbol, "name": name, "sector": sector})
            seen.add(symbol)

            if len(symbols) >= self.limit:
                break

        if not symbols:
            raise ValueError("Yahoo Finance 返回空的熱門股票清單")

        return symbols

    def _fallback(self) -> Tuple[List[str], Dict[str, Dict[str, str]]]:
        """返回備援的股票清單及其基本資訊。"""
        symbols = self.fallback_symbols[: self.limit]
        metadata = {
            symbol: {"name": symbol, "sector": STOCK_SECTORS.get(symbol, "未分類")}
            for symbol in symbols
        }
        return symbols, metadata

    def get_hot_symbols(self) -> Tuple[List[str], Dict[str, Dict[str, str]]]:
        """
        取得熱門美股清單及其簡單資訊。

        Returns:
            (symbols, metadata) 其中 metadata 以 symbol 為 key，包含 name/sector
        """
        if not USE_DYNAMIC_SYMBOLS:
            logger.info("動態股票列表已停用，使用備援清單")
            return self._fallback()

        try:
            records = self._fetch_from_yahoo()
            symbols = [r["symbol"] for r in records]
            metadata = {r["symbol"]: {"name": r["name"], "sector": r["sector"]} for r in records}
            logger.info("已從 Yahoo Finance 取得 %d 檔熱門美股", len(symbols))
            return symbols, metadata
        except Exception as exc:  # pragma: no cover - 避免部署時中斷
            logger.warning("熱門美股取得失敗，改用備援清單: %s", exc)
            return self._fallback()
