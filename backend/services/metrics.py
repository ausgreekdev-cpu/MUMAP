from typing import Optional
import time
import os

from ..config import settings

# ============================================================
# Optional Prometheus Metrics
# ============================================================

try:
    from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest as prom_generate_latest
    from prometheus_client.registry import REGISTRY as PROM_REGISTRY

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


if PROMETHEUS_AVAILABLE:
    # HTTP Metrics
    http_requests_total = Counter(
        'http_requests_total',
        'Total HTTP requests',
        ['method', 'endpoint', 'status_code']
    )

    http_request_duration_seconds = Histogram(
        'http_request_duration_seconds',
        'HTTP request duration in seconds',
        ['method', 'endpoint'],
        buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
    )

    # Agent Metrics
    agents_total = Gauge(
        'agents_total',
        'Total number of agents',
        ['status']
    )

    agent_tasks_completed = Counter(
        'agent_tasks_completed_total',
        'Total tasks completed by agents',
        ['agent_id', 'agent_name']
    )

    agent_tasks_failed = Counter(
        'agent_tasks_failed_total',
        'Total tasks failed by agents',
        ['agent_id', 'agent_name']
    )

    agent_health_score = Gauge(
        'agent_health_score',
        'Agent health score',
        ['agent_id', 'agent_name']
    )

    # Task Metrics
    tasks_total = Gauge(
        'tasks_total',
        'Total number of tasks',
        ['status', 'priority']
    )

    task_processing_duration_seconds = Histogram(
        'task_processing_duration_seconds',
        'Task processing duration in seconds',
        ['task_type'],
        buckets=[1, 5, 10, 30, 60, 300, 600]
    )

    tasks_created_total = Counter(
        'tasks_created_total',
        'Total tasks created'
    )

    tasks_completed_total = Counter(
        'tasks_completed_total',
        'Total tasks completed'
    )

    tasks_failed_total = Counter(
        'tasks_failed_total',
        'Total tasks failed'
    )

    # System Metrics
    system_cpu_usage = Gauge(
        'system_cpu_usage_percent',
        'System CPU usage percentage'
    )

    system_memory_usage = Gauge(
        'system_memory_usage_percent',
        'System memory usage percentage'
    )

    system_disk_usage = Gauge(
        'system_disk_usage_percent',
        'System disk usage percentage'
    )

    # Application Info
    app_info = Info(
        'multi_agent_platform',
        'Multi-Agent Platform information'
    )
else:
    # Stub objects so code that references these doesn't crash
    class _Stub:
        def __getattr__(self, name):
            return lambda *a, **kw: None
    http_requests_total = _Stub()
    http_request_duration_seconds = _Stub()
    agents_total = _Stub()
    agent_tasks_completed = _Stub()
    agent_tasks_failed = _Stub()
    agent_health_score = _Stub()
    tasks_total = _Stub()
    task_processing_duration_seconds = _Stub()
    tasks_created_total = _Stub()
    tasks_completed_total = _Stub()
    tasks_failed_total = _Stub()
    system_cpu_usage = _Stub()
    system_memory_usage = _Stub()
    system_disk_usage = _Stub()
    app_info = _Stub()


# ============================================================
# Metrics Collector
# ============================================================

class MetricsCollector:
    """Collects and exposes metrics for monitoring."""
    
    def __init__(self):
        self.start_time = time.time()
        if PROMETHEUS_AVAILABLE:
            app_info.info({
                'version': settings.VERSION,
                'environment': settings.ENVIRONMENT,
            })
    
    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        if PROMETHEUS_AVAILABLE:
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=str(status_code)
            ).inc()
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
    
    def record_agent_created(self, agent_id: int, agent_name: str):
        if PROMETHEUS_AVAILABLE:
            agents_total.labels(status='idle').inc()
    
    def record_agent_status(self, agent_id: int, agent_name: str, status: str):
        if PROMETHEUS_AVAILABLE:
            agents_total.labels(status=status).inc()
    
    def record_task_completed(self, agent_id: int, agent_name: str, duration: float, task_type: str = 'simple'):
        if PROMETHEUS_AVAILABLE:
            agent_tasks_completed.labels(
                agent_id=str(agent_id),
                agent_name=agent_name
            ).inc()
            task_processing_duration_seconds.labels(
                task_type=task_type
            ).observe(duration)
            tasks_completed_total.inc()
    
    def record_task_failed(self, agent_id: int, agent_name: str):
        if PROMETHEUS_AVAILABLE:
            agent_tasks_failed.labels(
                agent_id=str(agent_id),
                agent_name=agent_name
            ).inc()
            tasks_failed_total.inc()
    
    def update_system_metrics(self):
        if PSUTIL_AVAILABLE:
            try:
                cpu_percent = psutil.cpu_percent(interval=0.1)
                system_cpu_usage.set(cpu_percent)
                memory = psutil.virtual_memory()
                system_memory_usage.set(memory.percent)
                disk = psutil.disk_usage('/')
                system_disk_usage.set(disk.percent)
            except Exception:
                pass
    
    def update_task_counts(self, counts: dict):
        if PROMETHEUS_AVAILABLE:
            for status, count in counts.items():
                tasks_total.labels(status=status, priority='all').set(count)


def generate_latest():
    """Generate Prometheus metrics text."""
    if PROMETHEUS_AVAILABLE:
        return prom_generate_latest()
    return b""


# Global metrics collector
metrics = MetricsCollector()
