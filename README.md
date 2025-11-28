# 🔥 Hot Stock - 美股热度分析平台

一个基于新闻和市场数据的美股智能分析系统，每日自动收集、分析并评分美股，生成多维度榜单。

## ✨ 功能特性

- **📊 多维度评分系统**
  - 价格变化分析（涨跌幅、趋势）
  - 成交量分析（活跃度、异常交易）
  - 新闻热度分析（报道数量、情绪分析）
  - 技术指标分析（SMA、RSI 等）
  - 综合评分算法

- **📈 四大榜单**
  - 🔥 热度榜：综合评分最高的股票
  - 📈 涨幅榜：价格涨幅最大的股票
  - 💬 讨论榜：新闻报道最多的股票
  - ⚡ 活跃榜：成交量最活跃的股票

- **⏰ 自动化分析**
  - 每日定时任务自动收集数据
  - 自动分析并生成报表
  - 历史数据追踪

- **🌐 Web 界面**
  - 现代化响应式设计
  - 实时数据展示
  - 股票详情查看
  - 历史数据查询

## 🏗️ 系统架构

```
Hot-Stock/
├── backend/              # 后端代码
│   ├── app/
│   │   ├── collectors/   # 数据收集器
│   │   │   ├── stock_data.py    # 股票价格数据
│   │   │   └── news_data.py     # 新闻数据
│   │   ├── analyzers/    # 分析器
│   │   │   ├── scoring.py       # 评分系统
│   │   │   └── trends.py        # 趋势分析
│   │   ├── api/          # API 路由
│   │   │   └── routes.py
│   │   ├── scheduler/    # 定时任务
│   │   │   └── daily_task.py
│   │   ├── models.py     # 数据库模型
│   │   └── database.py   # 数据库连接
│   ├── main.py           # 主程序入口
│   └── requirements.txt  # 依赖包
├── frontend/             # 前端代码
│   ├── index.html
│   ├── css/
│   └── js/
├── data/                 # 数据存储
├── logs/                 # 日志文件
├── config.py             # 配置文件
├── manage.py             # 管理工具
└── README.md
```

## 🚀 快速开始

### 1. 环境要求

- Python 3.8+
- pip

### 2. 安装依赖

```bash
cd Hot-Stock
pip install -r backend/requirements.txt
```

### 3. 配置环境变量（可选）

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入你的 NewsAPI key
# 可从 https://newsapi.org/ 免费申请
```

### 4. 初始化数据库

```bash
python manage.py init
```

### 5. 运行首次分析（可选）

```bash
# 运行一次分析任务，收集数据并生成报表
python manage.py analyze
```

注意：首次运行需要下载大量数据，可能需要 5-10 分钟。

### 6. 启动 Web 服务器

```bash
python manage.py server
```

或者直接运行：

```bash
cd backend
python main.py
```

### 7. 访问网站

打开浏览器访问：`http://localhost:8000`

API 文档：`http://localhost:8000/docs`

## 📋 使用说明

### 管理命令

```bash
# 初始化数据库
python manage.py init

# 手动运行分析任务
python manage.py analyze

# 启动 Web 服务器
python manage.py server

# 查看统计信息
python manage.py stats
```

### API 接口

#### 获取榜单数据
```
GET /api/rankings?date=2025-01-01&top_n=10
```

#### 获取股票详情
```
GET /api/stock/{symbol}?days=30
```

#### 获取趋势股票
```
GET /api/trending?days=7&min_growth=10
```

#### 获取股票新闻
```
GET /api/news/{symbol}?days=7
```

#### 获取可用日期列表
```
GET /api/dates
```

### 定时任务

系统默认配置为每日 UTC 16:30（美股收盘后）自动运行分析任务。

可在 `config.py` 中修改：

```python
COLLECT_TIME = "16:30"  # UTC 时间
```

## ⚙️ 配置说明

### 主要配置项（config.py）

```python
# 热门股票来源
HOT_STOCK_LIMIT = 100           # 每天自動抓取前 100 檔 Yahoo Finance 最活躍的美股
USE_DYNAMIC_SYMBOLS = True      # 如需停用動態抓取，改為 False
FALLBACK_STOCK_SYMBOLS = [      # 外部來源不可用時的備援清單
    "AAPL", "MSFT", "GOOGL", "AMZN", ...
]

# 评分权重
SCORING_WEIGHTS = {
    "price_change": 0.25,      # 价格变化权重
    "volume_ratio": 0.20,      # 成交量比率权重
    "news_count": 0.25,        # 新闻数量权重
    "news_sentiment": 0.15,    # 新闻情绪权重
    "trend_score": 0.15,       # 趋势分数权重
}

# Top N 配置
TOP_N = 10
```

### 添加更多股票

系统会自动从 Yahoo Finance 抓取前一交易日最热门的美股；如需保证某些标的一定被纳入，可在 `config.py` 的 `FALLBACK_STOCK_SYMBOLS` 中维护备援列表（当外部来源不可用时使用）。

## 📊 评分系统

### 评分维度

1. **价格变化分数（25%）**
   - 基于股价涨跌幅
   - 相对于其他股票的百分位排名

2. **成交量分数（20%）**
   - 基于成交量与平均值的比率
   - 异常高的成交量获得更高分数

3. **新闻数量分数（25%）**
   - 基于新闻报道数量
   - 归一化到 0-100 分

4. **新闻情绪分数（15%）**
   - 基于新闻标题和内容的情绪分析
   - 正面新闻获得更高分数

5. **趋势分数（15%）**
   - 基于技术指标（SMA、RSI）
   - 上升趋势获得更高分数

### 综合评分

总分 = Σ(各维度分数 × 对应权重)

## 🛠️ 技术栈

### 后端
- **FastAPI** - 现代化 Web 框架
- **SQLAlchemy** - ORM 数据库框架
- **yfinance** - 股票数据获取
- **NewsAPI** - 新闻数据获取
- **APScheduler** - 定时任务调度
- **pandas/numpy** - 数据分析

### 前端
- **HTML5/CSS3** - 页面结构和样式
- **JavaScript** - 交互逻辑
- **Fetch API** - 数据请求

### 数据库
- **SQLite** - 轻量级数据库

## 📝 数据库模型

### Stock（股票表）
- 股票代码、名称、板块

### StockHistory（股票历史数据）
- 开盘价、最高价、最低价、收盘价
- 成交量、涨跌幅、成交量比率

### NewsArticle（新闻文章）
- 标题、描述、来源、URL
- 发布时间、情绪分数

### DailyScore（每日评分）
- 各项指标分数
- 综合分数、排名
- 原始数据（新闻数、价格变化等）

## 🔍 故障排查

### 问题：无法获取新闻数据

**原因**：未设置 NewsAPI key 或 key 无效

**解决**：
1. 访问 https://newsapi.org/ 注册并获取免费 API key
2. 在 `.env` 文件中设置 `NEWS_API_KEY`
3. 或直接在 `config.py` 中修改 `NEWS_API_KEY`

**备注**：未设置 key 时会使用模拟数据进行测试

### 问题：股票数据获取失败

**原因**：网络问题或 yfinance 限制

**解决**：
1. 检查网络连接
2. 等待一段时间后重试
3. 减少 `STOCK_SYMBOLS` 中的股票数量

### 问题：定时任务未运行

**原因**：时区设置或调度器未启动

**解决**：
1. 检查 `config.py` 中的 `COLLECT_TIME` 设置
2. 使用 `python manage.py analyze` 手动运行

## 📈 未来计划

- [ ] 添加更多技术指标
- [ ] 支持更多数据源
- [ ] 添加用户自定义监控列表
- [ ] 邮件/推送通知功能
- [ ] 更详细的趋势分析
- [ ] 机器学习预测模型
- [ ] 移动端适配

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## ⚠️ 免责声明

本项目仅供学习和研究使用。所有数据和分析结果仅供参考，不构成任何投资建议。投资有风险，入市需谨慎。

## 👨‍💻 作者

Hot Stock Analysis Platform

## 📞 联系方式

如有问题或建议，欢迎通过 GitHub Issues 联系。

---

**祝投资顺利！📈**
