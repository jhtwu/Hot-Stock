"""
性能监控模块
记录和分析系统性能指标
"""
import time
from typing import Dict, Optional
from datetime import datetime
from contextlib import contextmanager
import logging

logger = logging.getLogger('hotstock.performance')


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self):
        self.metrics: Dict[str, Dict] = {}
        self.start_times: Dict[str, float] = {}

    @contextmanager
    def measure(self, operation: str):
        """
        测量操作执行时间的上下文管理器

        Args:
            operation: 操作名称

        Example:
            with monitor.measure('data_collection'):
                collect_data()
        """
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.record(operation, duration)

    def record(self, operation: str, duration: float, success: bool = True):
        """
        记录性能指标

        Args:
            operation: 操作名称
            duration: 执行时长（秒）
            success: 是否成功
        """
        if operation not in self.metrics:
            self.metrics[operation] = {
                'count': 0,
                'total_time': 0.0,
                'min_time': float('inf'),
                'max_time': 0.0,
                'success_count': 0,
                'failure_count': 0,
                'last_execution': None
            }

        metric = self.metrics[operation]
        metric['count'] += 1
        metric['total_time'] += duration
        metric['min_time'] = min(metric['min_time'], duration)
        metric['max_time'] = max(metric['max_time'], duration)
        metric['last_execution'] = datetime.now()

        if success:
            metric['success_count'] += 1
        else:
            metric['failure_count'] += 1

        # 记录超时操作
        if duration > 5.0:
            logger.warning(f"操作 '{operation}' 执行时间过长: {duration:.2f}s")

    def get_metrics(self, operation: Optional[str] = None) -> Dict:
        """
        获取性能指标

        Args:
            operation: 操作名称，None 表示获取所有指标

        Returns:
            性能指标字典
        """
        if operation:
            if operation not in self.metrics:
                return {}

            metric = self.metrics[operation]
            avg_time = metric['total_time'] / metric['count'] if metric['count'] > 0 else 0

            return {
                'operation': operation,
                'count': metric['count'],
                'avg_time': avg_time,
                'min_time': metric['min_time'] if metric['min_time'] != float('inf') else 0,
                'max_time': metric['max_time'],
                'success_rate': metric['success_count'] / metric['count'] if metric['count'] > 0 else 0,
                'last_execution': metric['last_execution'].isoformat() if metric['last_execution'] else None
            }

        # 返回所有指标
        return {
            op: self.get_metrics(op)
            for op in self.metrics.keys()
        }

    def reset(self):
        """重置所有指标"""
        self.metrics.clear()
        self.start_times.clear()

    def report(self) -> str:
        """
        生成性能报告

        Returns:
            格式化的报告字符串
        """
        if not self.metrics:
            return "暂无性能数据"

        lines = ["\n" + "="*80]
        lines.append("性能监控报告")
        lines.append("="*80)
        lines.append(f"{'操作':<30} {'次数':<8} {'平均':<10} {'最小':<10} {'最大':<10} {'成功率':<10}")
        lines.append("-"*80)

        for operation in sorted(self.metrics.keys()):
            metric = self.get_metrics(operation)
            lines.append(
                f"{operation:<30} "
                f"{metric['count']:<8} "
                f"{metric['avg_time']:<10.2f} "
                f"{metric['min_time']:<10.2f} "
                f"{metric['max_time']:<10.2f} "
                f"{metric['success_rate']*100:<9.1f}%"
            )

        lines.append("="*80)
        return "\n".join(lines)


# 全局性能监控器实例
_global_monitor = PerformanceMonitor()


def get_monitor() -> PerformanceMonitor:
    """获取全局性能监控器"""
    return _global_monitor
