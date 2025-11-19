"""
主程序入口
启动 FastAPI 服务器和定时任务调度器
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import uvicorn
import logging
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.api.routes import router
from backend.app.database import init_db
from backend.app.scheduler import DailyAnalysisTask
from config import API_HOST, API_PORT, COLLECT_TIME, BASE_DIR, LOG_FILE

# 配置日志
LOG_FILE.parent.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(
    title="Hot Stock Analysis API",
    description="美股热度分析平台 API",
    version="1.0.0"
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(router)

# 挂载静态文件
frontend_path = BASE_DIR / "frontend"
if frontend_path.exists():
    app.mount(
        "/static",
        StaticFiles(directory=str(frontend_path)),
        name="static"
    )

# 创建定时任务调度器
scheduler = BackgroundScheduler()


@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    logger.info("正在启动 Hot Stock Analysis 服务...")

    # 初始化数据库
    try:
        init_db()
        logger.info("数据库初始化成功")
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")

    # 启动定时任务
    try:
        daily_task = DailyAnalysisTask()

        # 添加每日定时任务
        hour, minute = COLLECT_TIME.split(':')
        scheduler.add_job(
            daily_task.run,
            CronTrigger(hour=int(hour), minute=int(minute)),
            id='daily_analysis',
            name='每日股票分析任务',
            replace_existing=True
        )

        # 也可以手动触发
        # scheduler.add_job(
        #     daily_task.run,
        #     'interval',
        #     hours=1,
        #     id='hourly_analysis',
        #     name='每小时分析任务（测试用）'
        # )

        scheduler.start()
        logger.info(f"定时任务已启动，每日 {COLLECT_TIME} 执行分析")
    except Exception as e:
        logger.error(f"定时任务启动失败: {str(e)}")

    logger.info("=" * 50)
    logger.info("Hot Stock Analysis 服务启动成功！")
    logger.info(f"API 地址: http://{API_HOST}:{API_PORT}")
    logger.info(f"API 文档: http://{API_HOST}:{API_PORT}/docs")
    logger.info("=" * 50)


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    logger.info("正在关闭服务...")
    if scheduler.running:
        scheduler.shutdown()
    logger.info("服务已关闭")


@app.get("/")
async def home():
    """首页重定向到前端"""
    from fastapi.responses import FileResponse
    frontend_index = BASE_DIR / "frontend" / "index.html"
    if frontend_index.exists():
        return FileResponse(frontend_index)
    return {"message": "Welcome to Hot Stock Analysis API", "docs": "/docs"}


@app.get("/index.html")
async def home_index():
    """显式提供 /index.html 访问"""
    from fastapi.responses import FileResponse
    frontend_index = BASE_DIR / "frontend" / "index.html"
    if frontend_index.exists():
        return FileResponse(frontend_index)
    return {"message": "Welcome to Hot Stock Analysis API", "docs": "/docs"}


if __name__ == "__main__":
    # 运行服务器
    uvicorn.run(
        "main:app",
        host=API_HOST,
        port=API_PORT,
        reload=True,
        log_level="info"
    )
