# 🚀 快速開始 - GitHub Pages 部署

## ✅ 已完成的改動

已成功將 Hot Stock Analysis 改造為支援 GitHub Pages 靜態部署！

### 新增文件
- ✅ `generate_static_data.py` - 生成靜態 JSON 資料的腳本
- ✅ `update_site.sh` - 一鍵更新腳本
- ✅ `DEPLOYMENT.md` - 完整部署指南
- ✅ `requirements.txt` - Python 依賴列表
- ✅ `.github/workflows/update-data.yml` - GitHub Actions 自動化配置
- ✅ `frontend/.nojekyll` - GitHub Pages 配置

### 修改文件
- ✅ `frontend/js/app.js` - 支援靜態/API 雙模式
- ✅ `.gitignore` - 保留 frontend/data/ 目錄

---

## 📝 詳細操作步驟

### 階段 1: 手動更新部署（推薦先做這個）

#### 步驟 1：啟用 GitHub Pages

1. **進入 GitHub Repository**
   - 打開 https://github.com/your-username/Hot-Stock

2. **設置 GitHub Pages**
   ```
   Settings → Pages

   Source: Deploy from a branch
   Branch: claude/stock-analysis-platform-01DxrhetChaG9XmjDPy8mz1a
   Folder: /frontend

   點擊 Save
   ```

3. **記下您的網站 URL**
   - 類似 `https://your-username.github.io/Hot-Stock/`

#### 步驟 2：首次生成資料

在專案根目錄執行：

```bash
# 1. 確認在正確分支
git status

# 2. 確保虛擬環境已啟動
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 3. 檢查 .env 文件
cat .env
# 應該包含: NEWS_API_KEY=586d6197e7b34a01b9ea74e11f5f9dfc

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
```

#### 步驟 3：提交並推送資料

**方式 A：使用一鍵腳本（推薦）**
```bash
./update_site.sh
```

**方式 B：手動操作**
```bash
git add frontend/data/
git commit -m "data: 首次生成靜態資料"
git push origin claude/stock-analysis-platform-01DxrhetChaG9XmjDPy8mz1a
```

#### 步驟 4：驗證部署

1. 等待 1-3 分鐘
2. 前往 GitHub → Actions 查看建置狀態
3. 訪問您的 GitHub Pages URL
4. 應該能看到股票排行榜！

---

### 階段 2: GitHub Actions 自動化（可選）

如果您想要每天自動更新資料：

#### 步驟 1：設置 GitHub Secret

```
GitHub Repository → Settings → Secrets and variables → Actions

點擊 "New repository secret"

Name: NEWS_API_KEY
Value: 586d6197e7b34a01b9ea74e11f5f9dfc

點擊 "Add secret"
```

#### 步驟 2：測試自動化

```
GitHub Repository → Actions → Update Stock Data

點擊 "Run workflow" 按鈕

選擇分支: claude/stock-analysis-platform-01DxrhetChaG9XmjDPy8mz1a

點擊 "Run workflow"
```

#### 步驟 3：查看執行結果

- Actions 頁面會顯示執行狀態
- 成功後會自動提交資料更新
- 每天 UTC 01:00（台北時間 09:00）自動執行

---

## 🎯 每日更新流程

設置完成後，每天更新只需要：

### 手動更新（階段 1）
```bash
cd /path/to/Hot-Stock
./update_site.sh
```
就這麼簡單！

### 自動更新（階段 2）
什麼都不用做，GitHub Actions 會自動執行！

---

## 📂 生成的文件結構

執行 `generate_static_data.py` 後會生成：

```
frontend/data/
├── rankings.json          # 四個排行榜的資料
├── summary.json           # 摘要資訊（更新時間等）
└── stocks/
    ├── AAPL.json         # Apple 的詳細資料
    ├── TSLA.json         # Tesla 的詳細資料
    ├── GOOGL.json        # Alphabet 的詳細資料
    └── ...               # 其他股票
```

---

## 🔍 驗證資料是否正確

### 檢查本地文件
```bash
# 查看生成的文件
ls -lh frontend/data/

# 查看排行榜資料
cat frontend/data/rankings.json | python -m json.tool | head -30

# 查看特定股票
cat frontend/data/stocks/AAPL.json | python -m json.tool
```

### 檢查網站資料
在瀏覽器打開開發者工具（F12），然後訪問：
- Network 標籤
- 刷新頁面
- 應該看到 `rankings.json` 請求成功（Status 200）

---

## ⚠️ 常見問題

### Q1: 資料生成失敗怎麼辦？

**A:** 檢查以下項目：

1. **環境變數**
   ```bash
   cat .env
   # 確認 NEWS_API_KEY 存在
   ```

2. **依賴安裝**
   ```bash
   pip install -r requirements.txt
   ```

3. **資料庫權限**
   ```bash
   mkdir -p data
   chmod 755 data
   ```

### Q2: GitHub Pages 顯示 404

**A:** 確認以下設置：

1. Pages 設置正確：
   - Branch: `claude/stock-analysis-platform-01DxrhetChaG9XmjDPy8mz1a`
   - Folder: `/frontend`

2. 檔案已推送：
   ```bash
   git log --oneline -5
   # 應該看到最新的提交
   ```

3. Actions 建置成功：
   - 前往 Actions 頁面查看綠色勾勾

### Q3: 資料沒有更新

**A:** 檢查以下項目：

1. **本地有生成新資料嗎？**
   ```bash
   ls -lt frontend/data/
   # 檢查檔案修改時間
   ```

2. **有提交並推送嗎？**
   ```bash
   git status
   # 應該顯示 "nothing to commit, working tree clean"
   ```

3. **GitHub Actions 有執行嗎？**
   - 前往 Actions 頁面查看執行記錄

### Q4: 網站顯示「無法載入資料」

**A:** 打開瀏覽器開發者工具（F12）查看：

1. Console 是否有錯誤訊息
2. Network 標籤查看 API 請求：
   - `rankings.json` 是否成功載入
   - `stocks/*.json` 是否存在

3. 確認 `app.js` 設置：
   ```javascript
   const STATIC_MODE = true;  // 應該為 true
   ```

---

## 📞 需要更多幫助？

查看詳細文檔：
- **完整部署指南**: `DEPLOYMENT.md`
- **專案規格**: `SPECIFICATION.md`
- **代碼審查**: `CODE_REVIEW.md`

---

## 🎉 恭喜！

如果您成功完成以上步驟，您的 Hot Stock Analysis 網站現在應該已經在 GitHub Pages 上運行了！

**下一步建議：**
1. ⭐ 將 repository 設為 public（如果您想分享給其他人）
2. 📱 測試在手機瀏覽器上的顯示效果
3. 🔔 設置定時任務或使用 GitHub Actions 自動更新
4. 📊 監控資料準確性和更新頻率

**祝您使用愉快！** 🚀
