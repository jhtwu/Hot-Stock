# Hot Stock Analysis - GitHub Pages 部署指南

## 📋 目錄

1. [概述](#概述)
2. [階段 1: 手動更新部署](#階段-1-手動更新部署)
3. [階段 2: GitHub Actions 自動化](#階段-2-github-actions-自動化)
4. [故障排除](#故障排除)

---

## 概述

本專案支援兩種部署方式：

### 🔧 **階段 1: 手動更新（簡單）**
- 在本地電腦運行數據分析
- 生成靜態 JSON 文件
- 手動提交並推送到 GitHub
- GitHub Pages 自動部署

### 🤖 **階段 2: 自動化更新（進階）**
- 使用 GitHub Actions 定時執行
- 完全自動化，無需本地操作
- 需要配置 Actions secrets

---

## 階段 1: 手動更新部署

### 第一步：配置 GitHub Pages

1. **進入 GitHub Repository 設置**
   - 打開您的 GitHub repository
   - 點擊 `Settings` （設定）
   - 在左側選單找到 `Pages`

2. **設置發佈來源**
   ```
   Source: Deploy from a branch
   Branch: claude/stock-analysis-platform-01DxrhetChaG9XmjDPy8mz1a
   Folder: /frontend
   ```

3. **保存設置**
   - 點擊 `Save` 按鈕
   - GitHub 會顯示您的網站 URL（類似 `https://username.github.io/Hot-Stock/`）

### 第二步：首次生成資料

在專案根目錄執行以下命令：

```bash
# 1. 確保在正確的 git 分支
git checkout claude/stock-analysis-platform-01DxrhetChaG9XmjDPy8mz1a

# 2. 確保虛擬環境已啟動
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 3. 確保環境變數已設置
# 編輯 .env 文件，確保 NEWS_API_KEY 已設置
cat .env  # 檢查內容

# 4. 運行資料生成腳本
python3 generate_static_data.py
```

**預期輸出：**
```
============================================================
Hot Stock Analysis - 靜態資料生成器
============================================================

📊 步驟 1/4: 運行數據分析...
✓ 數據分析完成

📈 步驟 2/4: 生成排行榜資料...
✓ 排行榜資料完成

📋 步驟 3/4: 生成股票詳細資料...
✓ 股票詳細資料完成

📄 步驟 4/4: 生成摘要資訊...
✓ 摘要資訊完成

============================================================
✅ 所有靜態資料生成完成！
============================================================
輸出目錄: /path/to/Hot-Stock/frontend/data

生成的文件：
  - frontend/data/rankings.json       (排行榜)
  - frontend/data/summary.json        (摘要資訊)
  - frontend/data/stocks/*.json       (個別股票資料)
============================================================
```

### 第三步：提交並推送更新

您有兩種方式：

#### 方式 A：使用自動化腳本（推薦）

```bash
./update_site.sh
```

這個腳本會自動：
1. 生成最新資料
2. 提交變更到 Git
3. 推送到 GitHub

#### 方式 B：手動操作

```bash
# 1. 添加生成的資料文件
git add frontend/data/

# 2. 查看變更
git status

# 3. 提交變更
git commit -m "data: 更新每日股票分析資料 ($(date '+%Y-%m-%d'))"

# 4. 推送到遠端
git push origin claude/stock-analysis-platform-01DxrhetChaG9XmjDPy8mz1a
```

### 第四步：驗證部署

1. **等待 GitHub Pages 建置**
   - 推送後，前往 GitHub repository 的 `Actions` 頁面
   - 查看 `pages build and deployment` workflow
   - 等待綠色勾勾（通常需要 1-3 分鐘）

2. **訪問您的網站**
   - 打開 GitHub Pages URL
   - 應該能看到最新的股票排行榜
   - 嘗試點擊股票查看詳情

### 第五步：設置每日更新排程（可選）

在您的本地電腦設置定時任務：

#### Linux/Mac (使用 crontab)

```bash
# 編輯 crontab
crontab -e

# 添加以下行（每天早上 9:00 執行）
0 9 * * * cd /path/to/Hot-Stock && ./update_site.sh >> logs/update.log 2>&1
```

#### Windows (使用任務排程器)

1. 打開「任務排程器」（Task Scheduler）
2. 創建基本任務
3. 觸發程序：每天
4. 動作：啟動程式
5. 程式/指令碼：`C:\path\to\Hot-Stock\update_site.sh`

---

## 階段 2: GitHub Actions 自動化

> ⚠️ **注意**：此階段需要在 GitHub Actions 環境中運行 Python 分析，可能會遇到 API 限制或其他環境問題。

### 第一步：創建 GitHub Actions Workflow

創建文件 `.github/workflows/update-data.yml`：

```yaml
name: Update Stock Data

on:
  schedule:
    # 每天 UTC 01:00 執行（台北時間 09:00）
    - cron: '0 1 * * *'
  workflow_dispatch:  # 允許手動觸發

jobs:
  update-data:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v3
        with:
          ref: claude/stock-analysis-platform-01DxrhetChaG9XmjDPy8mz1a

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Generate static data
        env:
          NEWS_API_KEY: ${{ secrets.NEWS_API_KEY }}
        run: |
          python generate_static_data.py

      - name: Commit and push changes
        run: |
          git config --local user.email "github-actions[bot]@users.noreply.github.com"
          git config --local user.name "github-actions[bot]"
          git add frontend/data/
          git diff --staged --quiet || git commit -m "data: 自動更新每日股票分析資料 ($(date '+%Y-%m-%d'))"
          git push
```

### 第二步：設置 GitHub Secrets

1. 前往 GitHub repository 設置
2. 選擇 `Secrets and variables` > `Actions`
3. 點擊 `New repository secret`
4. 添加以下 secret：
   - Name: `NEWS_API_KEY`
   - Value: 您的 NewsAPI key

### 第三步：測試 Actions

1. 前往 `Actions` 頁面
2. 選擇 `Update Stock Data` workflow
3. 點擊 `Run workflow` 按鈕
4. 手動觸發測試

### 第四步：監控自動執行

- Actions 會每天自動執行
- 可以在 `Actions` 頁面查看執行記錄
- 如果失敗，會收到 GitHub 通知郵件

---

## 📂 文件結構

```
Hot-Stock/
├── generate_static_data.py      # 資料生成腳本
├── update_site.sh                # 一鍵更新腳本
├── DEPLOYMENT.md                 # 本文檔
├── .github/
│   └── workflows/
│       └── update-data.yml       # GitHub Actions（階段2）
├── frontend/
│   ├── .nojekyll                 # GitHub Pages 配置
│   ├── index.html
│   ├── css/
│   ├── js/
│   │   └── app.js                # 已修改為靜態模式
│   └── data/                     # 🔄 每日更新的資料
│       ├── rankings.json         # 排行榜
│       ├── summary.json          # 摘要
│       └── stocks/
│           ├── AAPL.json
│           ├── TSLA.json
│           └── ...
└── backend/                      # 僅用於本地生成資料
    ├── app/
    └── ...
```

---

## 🔍 資料格式說明

### rankings.json
```json
{
  "date": "2025-01-15",
  "last_updated": "2025-01-15T09:00:00",
  "hot": [
    {
      "rank": 1,
      "symbol": "AAPL",
      "name": "Apple Inc.",
      "price": 150.25,
      "change_percent": 2.5,
      "volume": 50000000,
      "score": 85.5,
      "news_count": 25,
      "sentiment_score": 65.0
    }
  ],
  "growth": [...],
  "discussion": [...],
  "active": [...]
}
```

### stocks/{SYMBOL}.json
```json
{
  "symbol": "AAPL",
  "name": "Apple Inc.",
  "current_price": 150.25,
  "change_percent": 2.5,
  "volume": 50000000,
  "scores": {
    "hot": 85.5,
    "growth": 78.3,
    "discussion": 82.1,
    "active": 88.9
  },
  "news_count": 25,
  "sentiment_score": 65.0,
  "historical_data": [...],
  "news": [...],
  "last_updated": "2025-01-15T09:00:00"
}
```

---

## 🛠️ 故障排除

### 問題 1：無法訪問 GitHub Pages

**症狀：** 404 Not Found

**解決方案：**
1. 檢查 GitHub Pages 設置是否正確
   - Branch: `claude/stock-analysis-platform-01DxrhetChaG9XmjDPy8mz1a`
   - Folder: `/frontend`
2. 確認 `frontend/index.html` 文件存在
3. 檢查 Actions 頁面，確認 pages build and deployment 成功

### 問題 2：資料顯示為空

**症狀：** 網頁顯示「無法載入資料」

**解決方案：**
1. 檢查是否已生成資料文件：
   ```bash
   ls -la frontend/data/
   # 應該看到 rankings.json, summary.json 和 stocks/ 目錄
   ```

2. 檢查 JSON 文件是否有效：
   ```bash
   cat frontend/data/rankings.json | python -m json.tool
   ```

3. 確認資料已推送到 GitHub：
   ```bash
   git log --oneline -5
   # 應該看到類似 "data: 更新每日股票分析資料" 的提交
   ```

### 問題 3：CORS 錯誤

**症狀：** 瀏覽器控制台顯示 CORS 錯誤

**解決方案：**
- 這通常不會在 GitHub Pages 上發生
- 如果在本地測試，使用簡單的 HTTP 服務器：
  ```bash
  cd frontend
  python -m http.server 8000
  ```

### 問題 4：資料生成失敗

**症狀：** `generate_static_data.py` 執行錯誤

**常見原因和解決方案：**

1. **Yahoo Finance 或 NewsAPI 限制**
   ```
   錯誤: 429 Too Many Requests
   ```
   解決：增加 `config.py` 中的 `REQUEST_DELAY`
   ```python
   REQUEST_DELAY = 3.0  # 從 2.0 增加到 3.0
   ```

2. **環境變數未設置**
   ```
   錯誤: NEWS_API_KEY not found
   ```
   解決：檢查 `.env` 文件
   ```bash
   cat .env
   # 應該包含: NEWS_API_KEY=your_key_here
   ```

3. **資料庫權限問題**
   ```
   錯誤: unable to open database file
   ```
   解決：確認 data 目錄權限
   ```bash
   mkdir -p data
   chmod 755 data
   ```

### 問題 5：GitHub Actions 失敗

**症狀：** Actions workflow 顯示紅叉

**解決方案：**
1. 查看 Actions 日誌找出錯誤
2. 確認 `NEWS_API_KEY` secret 已正確設置
3. 檢查 requirements.txt 是否包含所有依賴
4. 確認分支名稱正確

---

## 📊 監控和維護

### 檢查網站狀態

```bash
# 檢查最新資料更新時間
curl https://username.github.io/Hot-Stock/data/summary.json | python -m json.tool

# 檢查特定股票資料
curl https://username.github.io/Hot-Stock/data/stocks/AAPL.json | python -m json.tool
```

### 日誌管理

手動更新時建議保存日誌：

```bash
# 創建日誌目錄
mkdir -p logs

# 執行並記錄日誌
./update_site.sh 2>&1 | tee logs/update_$(date +%Y%m%d).log
```

### 定期檢查項目

- ✅ 每週檢查一次 GitHub Actions 執行狀態
- ✅ 每月檢查一次 API key 使用額度（NewsAPI）
- ✅ 每季度檢查一次資料準確性
- ✅ 定期備份資料庫文件（`data/*.db`）

---

## 🎯 最佳實踐

1. **資料更新時間**
   - 建議在美股收盤後（台北時間早上 5:00-9:00）更新
   - 避免在交易時段更新（資料可能不完整）

2. **API 使用**
   - NewsAPI 免費版每天限制 100 次請求
   - 監控您的 API 使用情況：https://newsapi.org/account

3. **Git 提交**
   - 每天只提交一次資料更新
   - 使用清晰的提交訊息格式：`data: 更新每日股票分析資料 (YYYY-MM-DD)`

4. **備份策略**
   - 定期備份 `.env` 文件（但不要提交到 Git）
   - 保留至少一週的資料庫備份

---

## 🔄 版本切換

### 切換回 API 模式（本地開發）

如果需要在本地運行完整的後端 API：

1. 修改 `frontend/js/app.js` 第 2 行：
   ```javascript
   const STATIC_MODE = false;  // 改為 false
   ```

2. 啟動後端服務：
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

3. 在瀏覽器訪問 `http://localhost:8000`

### 切換到靜態模式（GitHub Pages）

1. 修改 `frontend/js/app.js` 第 2 行：
   ```javascript
   const STATIC_MODE = true;  // 改為 true
   ```

2. 生成靜態資料並推送

---

## 📞 支援和資源

- **專案文檔**: `SPECIFICATION.md`
- **代碼審查**: `CODE_REVIEW.md`
- **NewsAPI 文檔**: https://newsapi.org/docs
- **GitHub Pages 文檔**: https://docs.github.com/pages
- **GitHub Actions 文檔**: https://docs.github.com/actions

---

## ✅ 快速檢查清單

階段 1 完成檢查清單：

- [ ] GitHub Pages 已啟用並設置正確的分支/目錄
- [ ] 本地已成功運行 `generate_static_data.py`
- [ ] `frontend/data/` 目錄包含完整的 JSON 文件
- [ ] 資料已提交並推送到 GitHub
- [ ] GitHub Pages 建置成功（綠色勾勾）
- [ ] 網站可以正常訪問並顯示資料
- [ ] `update_site.sh` 腳本可以正常執行
- [ ] （可選）已設置定時任務每日更新

階段 2 完成檢查清單：

- [ ] `.github/workflows/update-data.yml` 已創建
- [ ] `NEWS_API_KEY` secret 已設置
- [ ] 手動觸發測試成功
- [ ] 定時執行正常運作
- [ ] 自動提交和推送正常

---

**祝您使用愉快！** 🚀
