#!/bin/bash

echo "================================="
echo "Hot Stock - 部署脚本"
echo "================================="
echo ""

# 检查 Python 版本
echo "【步骤 1/7】检查 Python 版本..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "  Python 版本: $python_version"

required_version="3.8"
if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    echo "  ✓ Python 版本符合要求 (>= 3.8)"
else
    echo "  ✗ Python 版本过低，需要 >= 3.8"
    exit 1
fi

# 创建虚拟环境（可选）
echo ""
echo "【步骤 2/7】创建虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "  ✓ 虚拟环境已创建"
else
    echo "  ✓ 虚拟环境已存在"
fi

# 激活虚拟环境
echo "  激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo ""
echo "【步骤 3/7】安装依赖包..."
pip install -q --upgrade pip
pip install -q -r backend/requirements.txt
echo "  ✓ 依赖包安装完成"

# 检查 .env 文件
echo ""
echo "【步骤 4/7】检查配置文件..."
if [ ! -f ".env" ]; then
    echo "  创建 .env 文件..."
    cp .env.example .env
    echo "  ✓ .env 文件已创建"
    echo "  ⚠️  请编辑 .env 文件设置 NEWS_API_KEY"
else
    echo "  ✓ .env 文件已存在"
fi

# 创建必要目录
echo ""
echo "【步骤 5/7】创建必要目录..."
mkdir -p data logs
echo "  ✓ 目录创建完成"

# 初始化数据库
echo ""
echo "【步骤 6/7】初始化数据库..."
if [ ! -f "data/hotstock.db" ]; then
    python manage.py init
    echo "  ✓ 数据库初始化完成"
else
    echo "  ✓ 数据库已存在"
fi

# 运行测试（可选）
echo ""
echo "【步骤 7/7】运行测试（可选）..."
read -p "是否运行单元测试？(y/n): " run_tests
if [ "$run_tests" = "y" ] || [ "$run_tests" = "Y" ]; then
    chmod +x run_tests.sh
    ./run_tests.sh
fi

echo ""
echo "================================="
echo "部署完成！"
echo "================================="
echo ""
echo "接下来的步骤："
echo ""
echo "1. 配置 NewsAPI Key:"
echo "   编辑 .env 文件，设置 NEWS_API_KEY"
echo ""
echo "2. 运行首次分析:"
echo "   python manage.py analyze"
echo ""
echo "3. 启动 Web 服务器:"
echo "   python manage.py server"
echo ""
echo "4. 访问网站:"
echo "   http://localhost:8000"
echo ""
echo "================================="
