#!/bin/bash
# 每日更新網站資料的自動化腳本

set -e

echo "================================"
echo "Hot Stock Analysis - 網站更新"
echo "================================"
echo ""

# 步驟 1: 運行數據生成腳本
echo "📊 步驟 1/3: 生成最新資料..."
python3 generate_static_data.py

if [ $? -ne 0 ]; then
    echo "❌ 資料生成失敗！"
    exit 1
fi

echo ""
echo "✓ 資料生成完成"
echo ""

# 步驟 2: Git 提交
echo "📝 步驟 2/3: 提交更新到 Git..."

# 添加變更
git add frontend/data/

# 檢查是否有變更
if git diff --staged --quiet; then
    echo "⚠️  沒有檢測到資料變更，跳過提交"
else
    # 創建提交
    COMMIT_DATE=$(date '+%Y-%m-%d')
    git commit -m "data: 更新每日股票分析資料 ($COMMIT_DATE)"
    echo "✓ 提交完成"
fi

echo ""

# 步驟 3: 推送到遠端
echo "🚀 步驟 3/3: 推送到 GitHub..."
CURRENT_BRANCH=$(git branch --show-current)
git push origin "$CURRENT_BRANCH"

echo ""
echo "================================"
echo "✅ 網站更新完成！"
echo "================================"
echo ""
echo "GitHub Pages 會在幾分鐘內自動部署更新"
echo "請訪問您的 GitHub Pages URL 查看最新資料"
echo ""
