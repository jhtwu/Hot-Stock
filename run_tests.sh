#!/bin/bash

echo "================================="
echo "Hot Stock - 单元测试套件"
echo "================================="
echo ""

# 测试股票数据收集器
echo "【1/2】测试股票数据收集器..."
python tests/test_stock_collector.py

echo ""
echo "================================="
echo ""

# 测试评分系统
echo "【2/2】测试评分系统..."
python tests/test_scoring.py

echo ""
echo "================================="
echo "所有测试完成"
echo "================================="
