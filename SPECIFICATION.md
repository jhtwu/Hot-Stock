# Hot Stock Analysis Platform - System Specification

## 1. 系统概述

### 1.1 系统目标
构建一个美股热度分析平台，通过多维度数据分析，为用户提供每日热门股票排行榜和趋势分析。

### 1.2 核心价值
- 自动化数据收集和分析
- 多维度评分系统
- 实时榜单生成
- 历史数据追踪

## 2. 功能需求规格

### 2.1 数据收集模块

#### 2.1.1 股票价格数据
**功能描述**：从可靠数据源获取美股历史和实时价格数据

**数据源优先级**：
1. **主要数据源**: Stooq (stooq.pl)
   - 免费、稳定、无需 API key
   - 支持美股历史数据
   - CSV 格式直接下载

2. **备用数据源**: Yahoo Finance
   - 通过 yfinance 库访问
   - 数据更新及时
   - 可能有访问限制

**输入规格**：
- `symbol`: 股票代码 (String, 必需)
- `period`: 时间周期 (String, 可选, 默认 "5d")
- `interval`: 数据间隔 (String, 可选, 默认 "1d")

**输出规格**：
```python
{
    'symbol': str,           # 股票代码
    'date': datetime,        # 日期
    'open': float,          # 开盘价
    'high': float,          # 最高价
    'low': float,           # 最低价
    'close': float,         # 收盘价
    'volume': float,        # 成交量
    'change_percent': float,# 涨跌幅 (%)
    'volume_ratio': float   # 成交量比率
}
```

**性能要求**：
- 单个股票查询：< 5 秒
- 批量查询（22个股票）：< 2 分钟
- 请求间隔：≥ 2 秒

**错误处理**：
- 主要数据源失败 → 尝试备用数据源
- 所有数据源失败 → 返回 None，记录日志
- 不使用模拟数据（确保数据真实性）

#### 2.1.2 新闻数据
**功能描述**：从 NewsAPI 获取股票相关新闻

**输入规格**：
- `symbol`: 股票代码 (String, 必需)
- `company_name`: 公司名称 (String, 可选)
- `days`: 获取天数 (Integer, 可选, 默认 1)

**输出规格**：
```python
[
    {
        'title': str,           # 标题
        'description': str,     # 描述
        'url': str,            # 链接
        'source': str,         # 来源
        'published_at': datetime, # 发布时间
        'sentiment_score': float  # 情绪分数 (-1 到 1)
    },
    ...
]
```

**API 限制**：
- 免费版：100 请求/天
- 只能获取 30 天内新闻
- 需要有效 API key

**错误处理**：
- API 失败 → 使用模拟新闻数据
- API key 无效 → 记录警告，使用模拟数据

### 2.2 数据分析模块

#### 2.2.1 评分系统
**功能描述**：基于多维度指标对股票进行综合评分

**评分维度**：

1. **价格变化分数** (25% 权重)
   - 输入：`change_percent`
   - 计算方法：百分位排名
   - 输出范围：0-100

2. **成交量分数** (20% 权重)
   - 输入：`volume_ratio`
   - 计算方法：相对成交量活跃度
   - 输出范围：0-100

3. **新闻数量分数** (25% 权重)
   - 输入：`news_count`
   - 计算方法：归一化到最大值
   - 输出范围：0-100

4. **新闻情绪分数** (15% 权重)
   - 输入：`avg_sentiment` (-1 到 1)
   - 计算方法：线性映射到 0-100
   - 输出范围：0-100

5. **趋势分数** (15% 权重)
   - 输入：SMA, RSI 等技术指标
   - 计算方法：综合技术面评估
   - 输出范围：0-100

**综合评分公式**：
```
total_score = Σ(维度分数 × 对应权重)
```

**输出规格**：
```python
{
    'price_change_score': float,
    'volume_score': float,
    'news_count_score': float,
    'news_sentiment_score': float,
    'trend_score': float,
    'total_score': float  # 0-100
}
```

#### 2.2.2 榜单生成
**功能描述**：根据不同维度生成 Top N 榜单

**榜单类型**：

1. **热度榜** (Hot List)
   - 排序依据：综合评分 (`total_score`)
   - 展示：Top 10

2. **涨幅榜** (Growth List)
   - 排序依据：价格涨幅 (`price_change`)
   - 展示：Top 10

3. **讨论榜** (Discussion List)
   - 排序依据：新闻数量 (`news_count`)
   - 展示：Top 10

4. **活跃榜** (Active List)
   - 排序依据：成交量比率 (`volume_ratio`)
   - 展示：Top 10

**输出规格**：
```python
{
    'hot': [股票列表],
    'growth': [股票列表],
    'discussion': [股票列表],
    'active': [股票列表]
}
```

### 2.3 API 接口规格

#### 2.3.1 获取榜单
**端点**: `GET /api/rankings`

**查询参数**：
- `date`: 日期 (YYYY-MM-DD, 可选)
- `top_n`: 返回数量 (Integer, 可选, 默认 10, 范围 1-50)

**响应格式**：
```json
{
    "date": "2025-11-19",
    "rankings": {
        "hot": [...],
        "growth": [...],
        "discussion": [...],
        "active": [...]
    }
}
```

#### 2.3.2 获取股票详情
**端点**: `GET /api/stock/{symbol}`

**查询参数**：
- `days`: 历史天数 (Integer, 可选, 默认 30, 范围 1-90)

**响应格式**：
```json
{
    "symbol": "AAPL",
    "name": "Apple Inc.",
    "sector": "Technology",
    "latest_score": {...},
    "history": {
        "scores": [...],
        "prices": [...]
    },
    "recent_news": [...]
}
```

#### 2.3.3 手动触发分析
**端点**: `POST /api/run-analysis`

**响应格式**：
```json
{
    "status": "started",
    "message": "分析任务已启动..."
}
```

### 2.4 定时任务规格

**触发时间**: 每日 UTC 16:30 (美股收盘后)

**执行流程**：
1. 更新股票基本信息
2. 收集股票价格数据
3. 收集新闻数据
4. 计算评分
5. 生成榜单
6. 保存到数据库
7. 生成报表

**执行时长**: < 5 分钟

## 3. 数据模型规格

### 3.1 Stock (股票表)
```python
{
    'id': Integer (PK),
    'symbol': String(10) (Unique, Index),
    'name': String(100),
    'sector': String(50),
    'created_at': DateTime,
    'updated_at': DateTime
}
```

### 3.2 StockHistory (历史数据表)
```python
{
    'id': Integer (PK),
    'stock_id': Integer (FK),
    'date': DateTime (Index),
    'open_price': Float,
    'high_price': Float,
    'low_price': Float,
    'close_price': Float,
    'volume': Float,
    'change_percent': Float,
    'volume_ratio': Float,
    'created_at': DateTime
}
```

### 3.3 NewsArticle (新闻表)
```python
{
    'id': Integer (PK),
    'stock_id': Integer (FK),
    'title': String(500),
    'description': Text,
    'url': String(1000),
    'source': String(100),
    'published_at': DateTime (Index),
    'sentiment_score': Float,
    'created_at': DateTime
}
```

### 3.4 DailyScore (每日评分表)
```python
{
    'id': Integer (PK),
    'stock_id': Integer (FK),
    'date': DateTime (Index),
    'price_change_score': Float,
    'volume_score': Float,
    'news_count_score': Float,
    'news_sentiment_score': Float,
    'trend_score': Float,
    'total_score': Float (Index),
    'hot_rank': Integer,
    'growth_rank': Integer,
    'news_count': Integer,
    'price_change': Float,
    'volume_ratio': Float,
    'created_at': DateTime
}
```

## 4. 性能规格

### 4.1 响应时间
- API 查询: < 1 秒
- 数据收集: < 2 分钟
- 完整分析: < 5 分钟
- 前端加载: < 3 秒

### 4.2 数据量
- 监控股票: 22 个
- 历史保留: 90 天
- 新闻保留: 30 天
- 数据库大小: < 100 MB

### 4.3 并发处理
- API 并发: 10 请求/秒
- 数据库连接池: 5 连接

## 5. 安全规格

### 5.1 API 密钥管理
- 使用环境变量存储
- 不提交到版本控制
- .env 文件必须在 .gitignore

### 5.2 输入验证
- SQL 注入防护 (SQLAlchemy ORM)
- XSS 防护 (前端转义)
- 参数范围检查

### 5.3 错误处理
- 统一错误格式
- 详细日志记录
- 用户友好错误信息

## 6. 部署规格

### 6.1 环境要求
- Python: 3.8+
- SQLite: 3.x
- 磁盘空间: 500 MB
- 内存: 512 MB

### 6.2 依赖项
```
fastapi==0.109.0
uvicorn==0.27.0
sqlalchemy==2.0.25
pandas==2.2.0
numpy==1.26.3
newsapi-python==0.2.7
python-dotenv==1.0.0
apscheduler==3.10.4
pydantic==2.5.3
```

### 6.3 配置项
- `NEWS_API_KEY`: NewsAPI 密钥
- `REQUEST_DELAY`: 请求延迟（秒）
- `DEMO_MODE`: 演示模式开关
- `STOCK_SYMBOLS`: 监控股票列表

## 7. 测试规格

### 7.1 单元测试
- 数据收集器测试
- 评分系统测试
- API 接口测试

### 7.2 集成测试
- 完整分析流程测试
- 数据库操作测试
- API 端到端测试

### 7.3 性能测试
- 负载测试
- 压力测试
- 并发测试

## 8. 文档规格

### 8.1 用户文档
- README.md: 项目概述
- 快速开始.md: 安装和运行
- 故障排除.md: 常见问题

### 8.2 API 文档
- Swagger/OpenAPI 自动生成
- 访问路径: `/docs`

### 8.3 开发文档
- 代码注释
- 架构说明
- 贡献指南

## 9. 维护规格

### 9.1 日志
- 位置: `logs/hotstock.log`
- 级别: INFO
- 轮转: 每日

### 9.2 监控
- 任务执行状态
- API 响应时间
- 数据库大小

### 9.3 备份
- 数据库: 每日备份
- 配置文件: 版本控制

## 10. 扩展性考虑

### 10.1 水平扩展
- API 服务可多实例部署
- 数据库可迁移到 PostgreSQL
- 缓存层可添加 Redis

### 10.2 功能扩展
- 支持更多股票市场
- 添加技术指标
- 机器学习预测

### 10.3 数据源扩展
- 添加更多数据源
- 数据源故障转移
- 数据质量监控

---

**版本**: 1.0
**最后更新**: 2025-11-19
**状态**: 已实现
