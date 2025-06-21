"""
Advanced logging system with filtering, rotation, and performance optimization
"""

import logging
import time
import threading
from typing import Dict, List, Optional, Callable, Any
from pathlib import Path
from datetime import datetime
import queue
import json
from dataclasses import dataclass, asdict
from enum import Enum

class LogLevel(Enum):
    """Log level enumeration"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

@dataclass
class LogEntry:
    """Log entry data structure"""
    timestamp: float
    level: str
    message: str
    category: str = "GENERAL"
    source: str = ""
    emoji: str = "ℹ️"
    thread_id: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())

class LogFormatter:
    """Custom log formatter with emoji and color support"""
    
    # Emoji mappings for different log types
    EMOJI_MAP = {
        'DEBUG': '🔍',
        'INFO': 'ℹ️',
        'WARNING': '⚠️',
        'ERROR': '❌',
        'CRITICAL': '🚨',
        'SUCCESS': '✅',
        'COMBAT': '⚔️',
        'HEAL': '🏥',
        'MOVE': '🏃',
        'TARGET': '🎯',
        'SKILL': '⚡',
        'PICKUP': '💎',
        'MEMORY': '🧠',
        'DETECTION': '👁️',
        'INPUT': '⌨️',
        'BREAK': '😴',
        'SYSTEM': '🖥️'
    }
    
    # Color codes for console output
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[37m',     # White
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[91m', # Bright Red
        'SUCCESS': '\033[32m',  # Green
        'RESET': '\033[0m'      # Reset
    }
    
    def __init__(self, use_colors: bool = True, use_emojis: bool = True):
        self.use_colors = use_colors
        self.use_emojis = use_emojis
    
    def format_message(self, entry: LogEntry, include_timestamp: bool = True) -> str:
        """Format a log entry for display"""
        # Get emoji
        emoji = ""
        if self.use_emojis:
            emoji = entry.emoji or self.EMOJI_MAP.get(entry.level, 'ℹ️')
            emoji = f"{emoji} "
        
        # Get color
        color_start = ""
        color_end = ""
        if self.use_colors:
            color_start = self.COLORS.get(entry.level, '')
            color_end = self.COLORS['RESET'] if color_start else ''
        
        # Format timestamp
        timestamp_str = ""
        if include_timestamp:
            dt = datetime.fromtimestamp(entry.timestamp)
            timestamp_str = f"[{dt.strftime('%H:%M:%S')}] "
        
        # Format category
        category_str = f"[{entry.category}] " if entry.category != "GENERAL" else ""
        
        # Format source
        source_str = f"({entry.source}) " if entry.source else ""
        
        # Combine all parts
        formatted = f"{timestamp_str}{emoji}{color_start}{category_str}{source_str}{entry.message}{color_end}"
        
        return formatted
    
    def format_for_file(self, entry: LogEntry) -> str:
        """Format entry for file logging (no colors, structured)"""
        dt = datetime.fromtimestamp(entry.timestamp)
        timestamp_str = dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        
        parts = [
            timestamp_str,
            entry.level.ljust(8),
            f"[{entry.category}]" if entry.category != "GENERAL" else "[GENERAL]",
            f"({entry.source})" if entry.source else "",
            entry.message
        ]
        
        return " ".join(filter(None, parts))

class LogFilter:
    """Advanced log filtering system"""
    
    def __init__(self):
        self.level_filters = {level.value: True for level in LogLevel}
        self.category_filters = {}
        self.source_filters = {}
        self.custom_filters = []
        self.max_entries_per_second = 100
        self.last_check_time = time.time()
        self.entries_this_second = 0
    
    def should_log(self, entry: LogEntry) -> bool:
        """Determine if an entry should be logged"""
        current_time = time.time()
        
        # Rate limiting
        if current_time - self.last_check_time >= 1.0:
            self.last_check_time = current_time
            self.entries_this_second = 0
        
        self.entries_this_second += 1
        if self.entries_this_second > self.max_entries_per_second:
            return False
        
        # Level filter
        if not self.level_filters.get(entry.level, True):
            return False
        
        # Category filter
        if entry.category in self.category_filters:
            if not self.category_filters[entry.category]:
                return False
        
        # Source filter
        if entry.source in self.source_filters:
            if not self.source_filters[entry.source]:
                return False
        
        # Custom filters
        for filter_func in self.custom_filters:
            if not filter_func(entry):
                return False
        
        return True
    
    def set_level_filter(self, level: str, enabled: bool):
        """Set level filter"""
        self.level_filters[level] = enabled
    
    def set_category_filter(self, category: str, enabled: bool):
        """Set category filter"""
        self.category_filters[category] = enabled
    
    def set_source_filter(self, source: str, enabled: bool):
        """Set source filter"""
        self.source_filters[source] = enabled
    
    def add_custom_filter(self, filter_func: Callable[[LogEntry], bool]):
        """Add custom filter function"""
        self.custom_filters.append(filter_func)
    
    def clear_custom_filters(self):
        """Clear all custom filters"""
        self.custom_filters.clear()

class LogHandler:
    """Base class for log handlers"""
    
    def __init__(self, name: str):
        self.name = name
        self.enabled = True
        self.filter = LogFilter()
        self.formatter = LogFormatter()
    
    def handle(self, entry: LogEntry):
        """Handle a log entry"""
        if self.enabled and self.filter.should_log(entry):
            self._write_entry(entry)
    
    def _write_entry(self, entry: LogEntry):
        """Override this method to implement actual writing"""
        raise NotImplementedError

class ConsoleHandler(LogHandler):
    """Console output handler"""
    
    def __init__(self):
        super().__init__("console")
        self.lock = threading.Lock()
    
    def _write_entry(self, entry: LogEntry):
        with self.lock:
            formatted = self.formatter.format_message(entry)
            print(formatted)

class FileHandler(LogHandler):
    """File output handler with rotation"""
    
    def __init__(self, filepath: str, max_size_mb: int = 10, backup_count: int = 5):
        super().__init__("file")
        self.filepath = Path(filepath)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.backup_count = backup_count
        self.lock = threading.Lock()
        self.current_size = 0
        
        # Create directory if it doesn't exist
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Get current file size
        if self.filepath.exists():
            self.current_size = self.filepath.stat().st_size
    
    def _write_entry(self, entry: LogEntry):
        with self.lock:
            # Check if rotation is needed
            if self.current_size > self.max_size_bytes:
                self._rotate_file()
            
            # Write entry
            formatted = self.formatter.format_for_file(entry)
            with open(self.filepath, 'a', encoding='utf-8') as f:
                f.write(formatted + '\n')
                self.current_size += len(formatted.encode('utf-8')) + 1
    
    def _rotate_file(self):
        """Rotate log files"""
        if not self.filepath.exists():
            return
        
        # Move existing backup files
        for i in range(self.backup_count - 1, 0, -1):
            old_backup = self.filepath.with_suffix(f'.{i}.log')
            new_backup = self.filepath.with_suffix(f'.{i + 1}.log')
            
            if old_backup.exists():
                if new_backup.exists():
                    new_backup.unlink()
                old_backup.rename(new_backup)
        
        # Move current file to .1 backup
        backup_file = self.filepath.with_suffix('.1.log')
        if backup_file.exists():
            backup_file.unlink()
        self.filepath.rename(backup_file)
        
        # Reset size counter
        self.current_size = 0

class MemoryHandler(LogHandler):
    """In-memory handler for GUI display"""
    
    def __init__(self, max_entries: int = 1000):
        super().__init__("memory")
        self.max_entries = max_entries
        self.entries = []
        self.lock = threading.Lock()
        self.observers = []
    
    def _write_entry(self, entry: LogEntry):
        with self.lock:
            self.entries.append(entry)
            
            # Maintain max entries
            if len(self.entries) > self.max_entries:
                self.entries.pop(0)
            
            # Notify observers
            for observer in self.observers:
                try:
                    observer(entry)
                except Exception:
                    pass  # Don't let observer errors break logging
    
    def add_observer(self, callback: Callable[[LogEntry], None]):
        """Add observer for new log entries"""
        self.observers.append(callback)
    
    def remove_observer(self, callback: Callable[[LogEntry], None]):
        """Remove observer"""
        if callback in self.observers:
            self.observers.remove(callback)
    
    def get_entries(self, limit: Optional[int] = None, level_filter: Optional[str] = None) -> List[LogEntry]:
        """Get log entries with optional filtering"""
        with self.lock:
            entries = self.entries.copy()
        
        # Apply level filter
        if level_filter:
            entries = [e for e in entries if e.level == level_filter]
        
        # Apply limit
        if limit:
            entries = entries[-limit:]
        
        return entries
    
    def clear(self):
        """Clear all entries"""
        with self.lock:
            self.entries.clear()

class AsyncLogHandler(LogHandler):
    """Asynchronous log handler for performance"""
    
    def __init__(self, wrapped_handler: LogHandler, queue_size: int = 1000):
        super().__init__(f"async_{wrapped_handler.name}")
        self.wrapped_handler = wrapped_handler
        self.log_queue = queue.Queue(maxsize=queue_size)
        self.worker_thread = None
        self.stop_event = threading.Event()
        self.start_worker()
    
    def start_worker(self):
        """Start the worker thread"""
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
    
    def _worker_loop(self):
        """Worker thread loop"""
        while not self.stop_event.is_set():
            try:
                # Get entry with timeout
                entry = self.log_queue.get(timeout=1.0)
                if entry is None:  # Shutdown signal
                    break
                
                # Handle entry
                self.wrapped_handler.handle(entry)
                self.log_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Async log handler error: {e}")
    
    def _write_entry(self, entry: LogEntry):
        try:
            self.log_queue.put_nowait(entry)
        except queue.Full:
            # Drop entry if queue is full (prevent blocking)
            pass
    
    def stop(self):
        """Stop the async handler"""
        self.stop_event.set()
        self.log_queue.put(None)  # Shutdown signal
        if self.worker_thread:
            self.worker_thread.join(timeout=5)

class Logger:
    """Main logger class with multiple handlers and advanced features"""
    
    def __init__(self, name: str = "TamerBot"):
        self.name = name
        self.handlers = {}
        self.lock = threading.Lock()
        self.stats = {
            'total_logs': 0,
            'logs_by_level': {level.value: 0 for level in LogLevel},
            'logs_by_category': {},
            'start_time': time.time()
        }
        
        # Setup default handlers
        self._setup_default_handlers()
    
    def _setup_default_handlers(self):
        """Setup default log handlers"""
        # Console handler
        console = ConsoleHandler()
        self.add_handler(console)
        
        # File handler
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        file_handler = FileHandler(log_dir / "tamerbot.log")
        async_file = AsyncLogHandler(file_handler)
        self.add_handler(async_file)
        
        # Memory handler for GUI
        memory = MemoryHandler()
        self.add_handler(memory)
    
    def add_handler(self, handler: LogHandler):
        """Add a log handler"""
        with self.lock:
            self.handlers[handler.name] = handler
    
    def remove_handler(self, name: str):
        """Remove a log handler"""
        with self.lock:
            if name in self.handlers:
                handler = self.handlers.pop(name)
                if isinstance(handler, AsyncLogHandler):
                    handler.stop()
    
    def _log(self, level: str, message: str, category: str = "GENERAL", 
             source: str = "", emoji: str = ""):
        """Internal logging method"""
        current_time = time.time()
        thread_id = threading.get_ident()
        
        # Create log entry
        entry = LogEntry(
            timestamp=current_time,
            level=level,
            message=message,
            category=category,
            source=source,
            emoji=emoji,
            thread_id=thread_id
        )
        
        # Update statistics
        with self.lock:
            self.stats['total_logs'] += 1
            self.stats['logs_by_level'][level] += 1
            self.stats['logs_by_category'][category] = self.stats['logs_by_category'].get(category, 0) + 1
        
        # Send to handlers
        for handler in self.handlers.values():
            try:
                handler.handle(entry)
            except Exception as e:
                # Fallback to print if handler fails
                print(f"Log handler {handler.name} failed: {e}")
    
    def debug(self, message: str, category: str = "DEBUG", source: str = ""):
        """Log debug message"""
        self._log("DEBUG", message, category, source, "🔍")
    
    def info(self, message: str, category: str = "INFO", source: str = ""):
        """Log info message"""
        self._log("INFO", message, category, source, "ℹ️")
    
    def warning(self, message: str, category: str = "WARNING", source: str = ""):
        """Log warning message"""
        self._log("WARNING", message, category, source, "⚠️")
    
    def error(self, message: str, category: str = "ERROR", source: str = ""):
        """Log error message"""
        self._log("ERROR", message, category, source, "❌")
    
    def critical(self, message: str, category: str = "CRITICAL", source: str = ""):
        """Log critical message"""
        self._log("CRITICAL", message, category, source, "🚨")
    
    def success(self, message: str, category: str = "SUCCESS", source: str = ""):
        """Log success message"""
        self._log("INFO", message, category, source, "✅")
    
    def combat(self, message: str, source: str = ""):
        """Log combat-related message"""
        self._log("INFO", message, "COMBAT", source, "⚔️")
    
    def heal(self, message: str, source: str = ""):
        """Log healing-related message"""
        self._log("INFO", message, "HEAL", source, "🏥")
    
    def move(self, message: str, source: str = ""):
        """Log movement-related message"""
        self._log("INFO", message, "MOVE", source, "🏃")
    
    def target(self, message: str, source: str = ""):
        """Log targeting-related message"""
        self._log("INFO", message, "TARGET", source, "🎯")
    
    def skill(self, message: str, source: str = ""):
        """Log skill-related message"""
        self._log("INFO", message, "SKILL", source, "⚡")
    
    def pickup(self, message: str, source: str = ""):
        """Log pickup-related message"""
        self._log("INFO", message, "PICKUP", source, "💎")
    
    def memory(self, message: str, source: str = ""):
        """Log memory-related message"""
        self._log("INFO", message, "MEMORY", source, "🧠")
    
    def detection(self, message: str, source: str = ""):
        """Log detection-related message"""
        self._log("INFO", message, "DETECTION", source, "👁️")
    
    def input_action(self, message: str, source: str = ""):
        """Log input-related message"""
        self._log("INFO", message, "INPUT", source, "⌨️")
    
    def break_time(self, message: str, source: str = ""):
        """Log break-related message"""
        self._log("INFO", message, "BREAK", source, "😴")
    
    def system(self, message: str, source: str = ""):
        """Log system-related message"""
        self._log("INFO", message, "SYSTEM", source, "🖥️")
    
    def get_memory_handler(self) -> Optional[MemoryHandler]:
        """Get the memory handler for GUI integration"""
        return self.handlers.get("memory")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get logging statistics"""
        with self.lock:
            uptime = time.time() - self.stats['start_time']
            return {
                'total_logs': self.stats['total_logs'],
                'logs_by_level': self.stats['logs_by_level'].copy(),
                'logs_by_category': self.stats['logs_by_category'].copy(),
                'uptime': uptime,
                'logs_per_minute': (self.stats['total_logs'] / max(1, uptime)) * 60,
                'active_handlers': len(self.handlers),
                'handler_names': list(self.handlers.keys())
            }
    
    def set_handler_filter(self, handler_name: str, filter_type: str, filter_value: str, enabled: bool):
        """Set filter for a specific handler"""
        if handler_name in self.handlers:
            handler = self.handlers[handler_name]
            if filter_type == "level":
                handler.filter.set_level_filter(filter_value, enabled)
            elif filter_type == "category":
                handler.filter.set_category_filter(filter_value, enabled)
            elif filter_type == "source":
                handler.filter.set_source_filter(filter_value, enabled)
    
    def clear_logs(self, handler_name: str = "memory"):
        """Clear logs from a specific handler"""
        if handler_name in self.handlers:
            handler = self.handlers[handler_name]
            if isinstance(handler, MemoryHandler):
                handler.clear()
    
    def export_logs(self, filepath: str, format: str = "json", limit: Optional[int] = None):
        """Export logs to file"""
        memory_handler = self.get_memory_handler()
        if not memory_handler:
            self.error("No memory handler available for export")
            return False
        
        try:
            entries = memory_handler.get_entries(limit=limit)
            
            if format == "json":
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump([entry.to_dict() for entry in entries], f, indent=2)
            elif format == "txt":
                formatter = LogFormatter(use_colors=False)
                with open(filepath, 'w', encoding='utf-8') as f:
                    for entry in entries:
                        f.write(formatter.format_message(entry) + '\n')
            else:
                self.error(f"Unsupported export format: {format}")
                return False
            
            self.success(f"Logs exported to {filepath}")
            return True
            
        except Exception as e:
            self.error(f"Failed to export logs: {e}")
            return False
    
    def shutdown(self):
        """Shutdown the logger and all handlers"""
        with self.lock:
            for handler in self.handlers.values():
                if isinstance(handler, AsyncLogHandler):
                    handler.stop()
            self.handlers.clear()
        
        self.info("Logger shutdown complete")

# Global logger instance
_global_logger = None

def get_logger(name: str = "TamerBot") -> Logger:
    """Get global logger instance"""
    global _global_logger
    if _global_logger is None:
        _global_logger = Logger(name)
    return _global_logger