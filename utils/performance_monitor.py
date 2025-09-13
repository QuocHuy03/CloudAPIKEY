import time
import psutil
import threading
from collections import defaultdict, deque
from functools import wraps
import logging

# Performance monitoring
class PerformanceMonitor:
    def __init__(self):
        self.request_times = deque(maxlen=1000)
        self.api_call_times = defaultdict(lambda: deque(maxlen=100))
        self.error_counts = defaultdict(int)
        self.cache_hit_rates = defaultdict(lambda: {'hits': 0, 'misses': 0})
        self.start_time = time.time()
        
    def record_request_time(self, endpoint, duration):
        """Record request processing time"""
        self.request_times.append({
            'endpoint': endpoint,
            'duration': duration,
            'timestamp': time.time()
        })
    
    def record_api_call_time(self, api_name, duration):
        """Record API call time"""
        self.api_call_times[api_name].append(duration)
    
    def record_error(self, endpoint, error_type):
        """Record error occurrence"""
        self.error_counts[f"{endpoint}_{error_type}"] += 1
    
    def record_cache_hit(self, cache_name, hit=True):
        """Record cache hit/miss"""
        if hit:
            self.cache_hit_rates[cache_name]['hits'] += 1
        else:
            self.cache_hit_rates[cache_name]['misses'] += 1
    
    def get_performance_stats(self):
        """Get current performance statistics"""
        current_time = time.time()
        uptime = current_time - self.start_time
        
        # Calculate average request time
        if self.request_times:
            avg_request_time = sum(r['duration'] for r in self.request_times) / len(self.request_times)
        else:
            avg_request_time = 0
        
        # Calculate cache hit rates
        cache_stats = {}
        for cache_name, stats in self.cache_hit_rates.items():
            total = stats['hits'] + stats['misses']
            if total > 0:
                hit_rate = (stats['hits'] / total) * 100
            else:
                hit_rate = 0
            cache_stats[cache_name] = {
                'hit_rate': hit_rate,
                'hits': stats['hits'],
                'misses': stats['misses']
            }
        
        # System resource usage
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        return {
            'uptime_seconds': uptime,
            'total_requests': len(self.request_times),
            'average_request_time_ms': avg_request_time * 1000,
            'error_counts': dict(self.error_counts),
            'cache_stats': cache_stats,
            'system': {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': memory.available / (1024**3)
            }
        }

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

def monitor_performance(endpoint_name=None):
    """Decorator to monitor function performance"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Record performance metrics
                if endpoint_name:
                    performance_monitor.record_request_time(endpoint_name, duration)
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                if endpoint_name:
                    performance_monitor.record_error(endpoint_name, type(e).__name__)
                raise
        return wrapper
    return decorator

def monitor_api_calls(api_name):
    """Decorator to monitor API call performance"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                performance_monitor.record_api_call_time(api_name, duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                performance_monitor.record_api_call_time(api_name, duration)
                raise
        return wrapper
    return decorator

def get_cache_stats():
    """Get cache performance statistics"""
    return performance_monitor.get_performance_stats()

def clear_performance_data():
    """Clear all performance monitoring data"""
    performance_monitor.request_times.clear()
    performance_monitor.api_call_times.clear()
    performance_monitor.error_counts.clear()
    performance_monitor.cache_hit_rates.clear()
    performance_monitor.start_time = time.time()

# Background monitoring thread
def start_background_monitoring():
    """Start background performance monitoring"""
    def monitor_loop():
        while True:
            try:
                stats = performance_monitor.get_performance_stats()
                
                # Log performance metrics every 5 minutes
                if int(stats['uptime_seconds']) % 300 == 0:
                    logging.info(f"Performance Stats: {stats}")
                
                time.sleep(60)  # Check every minute
            except Exception as e:
                logging.error(f"Performance monitoring error: {e}")
                time.sleep(60)
    
    monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
    monitor_thread.start()
    return monitor_thread
