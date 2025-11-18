#!/usr/bin/env python3
"""
Hot Stock 管理命令行工具
提供数据库初始化、手动分析等功能
"""
import sys
import argparse
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from backend.app.database import init_db
from backend.app.scheduler import DailyAnalysisTask


def init_database():
    """初始化数据库"""
    print("正在初始化数据库...")
    try:
        init_db()
        print("✓ 数据库初始化成功！")
    except Exception as e:
        print(f"✗ 数据库初始化失败: {str(e)}")
        sys.exit(1)


def run_analysis():
    """运行每日分析任务"""
    print("正在运行分析任务...")
    try:
        task = DailyAnalysisTask()
        task.run()
        print("✓ 分析任务完成！")
    except Exception as e:
        print(f"✗ 分析任务失败: {str(e)}")
        sys.exit(1)


def start_server():
    """启动 Web 服务器"""
    print("正在启动 Web 服务器...")
    import uvicorn
    from config import API_HOST, API_PORT
    from backend.main import app

    uvicorn.run(
        app,
        host=API_HOST,
        port=API_PORT,
        log_level="info"
    )


def show_stats():
    """显示统计信息"""
    from backend.app.database import SessionLocal
    from backend.app.models import Stock, DailyScore, NewsArticle
    from sqlalchemy import func, desc
    from datetime import datetime

    db = SessionLocal()
    try:
        # 统计股票数量
        stock_count = db.query(Stock).count()
        print(f"\n{'='*50}")
        print(f"Hot Stock 统计信息")
        print(f"{'='*50}")
        print(f"监控股票数量: {stock_count}")

        # 统计评分记录
        score_count = db.query(DailyScore).count()
        print(f"评分记录数量: {score_count}")

        # 最新评分日期
        latest_score = db.query(DailyScore.date).order_by(desc(DailyScore.date)).first()
        if latest_score:
            print(f"最新评分日期: {latest_score[0].strftime('%Y-%m-%d')}")

        # 统计新闻数量
        news_count = db.query(NewsArticle).count()
        print(f"新闻记录数量: {news_count}")

        # 最热门股票
        if latest_score:
            hot_stocks = db.query(DailyScore, Stock).join(
                Stock, DailyScore.stock_id == Stock.id
            ).filter(
                DailyScore.date == latest_score[0]
            ).order_by(desc(DailyScore.total_score)).limit(5).all()

            print(f"\n当前热度 Top 5:")
            for i, (score, stock) in enumerate(hot_stocks, 1):
                print(f"  {i}. {stock.symbol:6s} - 评分: {score.total_score:.2f}")

        print(f"{'='*50}\n")

    except Exception as e:
        print(f"获取统计信息失败: {str(e)}")
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description='Hot Stock 管理工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python manage.py init        # 初始化数据库
  python manage.py analyze     # 运行分析任务
  python manage.py server      # 启动 Web 服务器
  python manage.py stats       # 显示统计信息
        """
    )

    parser.add_argument(
        'command',
        choices=['init', 'analyze', 'server', 'stats'],
        help='要执行的命令'
    )

    args = parser.parse_args()

    if args.command == 'init':
        init_database()
    elif args.command == 'analyze':
        run_analysis()
    elif args.command == 'server':
        start_server()
    elif args.command == 'stats':
        show_stats()


if __name__ == '__main__':
    main()
