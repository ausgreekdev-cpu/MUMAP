from typing import Optional
import time

from ..config import settings

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
    agents_total = Gauge('agents_total', 'Total number of agents', ['status'])
    tasks_total = Gauge('tasks_total', 'Total number of tasks', ['status', 'priority'])
    system_cpu_usage = Gauge('system_cpu_usage_percent', 'System CPU usage percentage')
    system_memory_usage = Gauge('system_memory_usage_percent', 'System memory usage percentage')
    app_info = Info('multi_agent_platform', 'Multi-Agent Platform information')
else:
    class _Stub:
        def __getattr__(self, name):
            return lambda *a, **kw: None
    http_requests_total = _Stub()
    http_request_duration_seconds = _Stub()
    agents_total = _Stub()
    tasks_total = _Stub()
    system_cpu_usage = _Stub()
    system_memory_usage = _Stub()
    app_info = _Stub()


class MetricsCollector:
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

    def update_system_metrics(self):
        if PSUTIL_AVAILABLE:
            try:
                cpu_percent = psutil.cpu_percent(interval=0.1)
                system_cpu_usage.set(cpu_percent)
                memory = psutil.virtual_memory()
                system_memory_usage.set(memory.percent)
            except Exception:
                pass


def generate_latest():
    if PROMETHEUS_AVAILABLE:
        return prom_generate_latest()
    return b""


metrics = MetricsCollector()
