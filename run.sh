#!/bin/bash

echo "==================================="
echo "Hot Stock Analysis Platform"
echo "==================================="
echo ""

# 检查是否首次运行
if [ ! -f "data/hotstock.db" ]; then
    echo "检测到首次运行，正在初始化..."
    echo ""

    # 初始化数据库
    echo "1. 初始化数据库..."
    python manage.py init
    echo ""

    # 运行首次分析
    echo "2. 运行首次分析（这可能需要几分钟）..."
    python manage.py analyze
    echo ""
fi

# 启动服务器
echo "启动 Web 服务器..."
echo "访问地址: http://localhost:8000"
echo "API 文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止服务器"
echo ""

python manage.py server
