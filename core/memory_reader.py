"""
Advanced memory reading system with error handling and validation
"""

import time
import random
import threading
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import psutil

# Optional imports with fallbacks
PYMEM_AVAILABLE = False
try:
    import pymem
    import pymem.process
    PYMEM_AVAILABLE = True
except ImportError:
    print("Warning: pymem not available. Memory reading disabled.")

from config.constants import MEMORY_OFFSETS, GAME_PROCESSES, ERROR_CODES
from utils.logger import Logger

@dataclass
class MemoryStats:
    """Container for memory-read game statistics"""
    hp: int = 1000
    max_hp: int = 1000
    ds: int = 500
    max_ds: int = 500
    level: int = 1
    exp: int = 0
    hp_pct: float = 100.0
    ds_pct: float = 100.0
    position_x: float = 0.0
    position_y: float = 0.0
    position_z: float = 0.0
    in_combat: bool = False
    loading: bool = False
    connected: bool = False
    timestamp: float = 0.0

@dataclass
class DigimonStats:
    """Container for Digimon statistics"""
    hp: int = 1000
    max_hp: int = 1000
    ds: int = 500
    max_ds: int = 500
    level: int = 1
    hp_pct: float = 100.0
    ds_pct: float = 100.0
    connected: bool = False

class MemoryReader:
    """Advanced memory reader with connection management and validation"""
    
    def __init__(self, config):
        self.config = config
        self.logger = Logger()
        self.pm = None
        self.connected = False
        self.base_address = None
        self.last_valid_stats = None
        self.last_digimon_stats = None
        self.connection_attempts = 0
        self.max_connection_attempts = 3
        self.read_errors = 0
        self.max_read_errors = 10
        self.lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # Performance tracking
        self.read_times = []
        self.validation_failures = 0
        self.successful_reads = 0
        
        # Auto-reconnection
        self.last_connection_attempt = 0
        self.reconnection_interval = 5.0
        
    def connect(self) -> bool:
        """Connect to game process memory"""
        if not PYMEM_AVAILABLE:
            self.logger.error("Pymem not available - cannot connect to memory")
            return False
            
        with self.lock:
            try:
                # Check if already connected and process is still alive
                if self.connected and self.pm and psutil.pid_exists(self.pm.process_id):
                    return True
                
                # Find game process
                game_process = self._find_game_process()
                if not game_process:
                    self.logger.warning("No game process found")
                    return False
                
                # Connect to process
                self.pm = pymem.Pymem(game_process['name'])
                self.base_address = pymem.process.module_from_name(
                    self.pm.process_handle, 
                    game_process['name']
                ).lpBaseOfDll
                
                self.connected = True
                self.connection_attempts = 0
                self.read_errors = 0
                
                self.logger.info(f"Connected to {game_process['name']} (PID: {game_process['pid']})")
                return True
                
            except Exception as e:
                self.connected = False
                self.connection_attempts += 1
                self.logger.error(f"Memory connection failed: {e}")
                return False
    
    def disconnect(self):
        """Disconnect from game process"""
        with self.lock:
            try:
                if self.pm:
                    self.pm.close_process()
                    self.pm = None
                self.connected = False
                self.base_address = None
                self.logger.info("Disconnected from memory")
            except Exception as e:
                self.logger.error(f"Error during disconnect: {e}")
    
    def _find_game_process(self) -> Optional[Dict[str, Any]]:
        """Find running game process"""
        try:
            for process in psutil.process_iter(['pid', 'name']):
                process_name = process.info['name'].lower()
                
                for game_process in GAME_PROCESSES:
                    if game_process.lower() in process_name:
                        return {
                            'pid': process.info['pid'],
                            'name': process.info['name']
                        }
            return None
        except Exception as e:
            self.logger.error(f"Error finding game process: {e}")
            return None
    
    def _read_pointer_chain(self, offsets: List[int]) -> int:
        """Read a pointer chain and return final value"""
        if not self.connected or not self.pm:
            return 0
            
        try:
            # Start with base address + offset
            base_offset = int(self.config.base_offset, 16) if isinstance(self.config.base_offset, str) else self.config.base_offset
            addr = self.pm.read_uint(self.base_address + base_offset)
            
            # Follow pointer chain
            for offset in offsets[:-1]:
                if addr == 0:
                    return 0
                addr = self.pm.read_uint(addr + offset)
                # Add small delay to prevent memory access issues
                time.sleep(random.uniform(0.001, 0.003))
            
            # Read final value
            final_addr = addr + offsets[-1]
            value = self.pm.read_int(final_addr)
            
            return value
            
        except Exception as e:
            self.read_errors += 1
            if self.read_errors % 5 == 0:  # Log every 5th error to avoid spam
                self.logger.warning(f"Pointer read error: {e}")
            return 0
    
    def _validate_stats(self, stats: Dict[str, int]) -> bool:
        """Validate memory-read statistics for sanity"""
        try:
            # Check for reasonable value ranges
            if not (0 < stats.get('hp', 0) <= 50000):
                return False
            if not (0 < stats.get('max_hp', 0) <= 50000):
                return False
            if not (0 <= stats.get('ds', 0) <= 10000):
                return False
            if not (0 < stats.get('max_ds', 0) <= 10000):
                return False
            
            # Check relationships
            if stats['hp'] > stats['max_hp'] * 1.1:  # Allow 10% tolerance
                return False
            if stats['ds'] > stats['max_ds'] * 1.1:
                return False
            
            # Check for reasonable level
            level = stats.get('level', 1)
            if not (1 <= level <= 100):
                return False
                
            return True
            
        except Exception:
            return False
    
    def get_player_stats(self) -> MemoryStats:
        """Get current player statistics"""
        if not self.connected:
            if self.config.auto_reconnect and time.time() - self.last_connection_attempt > self.reconnection_interval:
                self.last_connection_attempt = time.time()
                self.connect()
            
            # Return last valid stats if available
            if self.last_valid_stats:
                return self.last_valid_stats
            return MemoryStats()
        
        read_start = time.time()
        
        try:
            # Read all player stats
            raw_stats = {}
            for stat_name, offsets in MEMORY_OFFSETS['player_stats'].items():
                raw_stats[stat_name] = self._read_pointer_chain(offsets)
            
            # Read position
            position_stats = {}
            for pos_name, offsets in MEMORY_OFFSETS['position'].items():
                position_stats[pos_name] = self._read_pointer_chain(offsets)
            
            # Read game state
            state_stats = {}
            for state_name, offsets in MEMORY_OFFSETS['game_state'].items():
                state_stats[state_name] = self._read_pointer_chain(offsets)
            
            # Validate stats
            if self.config.validation_enabled and not self._validate_stats(raw_stats):
                self.validation_failures += 1
                if self.last_valid_stats:
                    return self.last_valid_stats
                return MemoryStats()
            
            # Create MemoryStats object
            stats = MemoryStats(
                hp=raw_stats.get('hp', 1000),
                max_hp=raw_stats.get('max_hp', 1000),
                ds=raw_stats.get('ds', 500),
                max_ds=raw_stats.get('max_ds', 500),
                level=raw_stats.get('level', 1),
                exp=raw_stats.get('exp', 0),
                position_x=float(position_stats.get('x', 0)),
                position_y=float(position_stats.get('y', 0)),
                position_z=float(position_stats.get('z', 0)),
                in_combat=bool(state_stats.get('in_combat', 0)),
                loading=bool(state_stats.get('loading', 0)),
                connected=True,
                timestamp=time.time()
            )
            
            # Calculate percentages
            stats.hp_pct = (stats.hp / stats.max_hp) * 100 if stats.max_hp > 0 else 0
            stats.ds_pct = (stats.ds / stats.max_ds) * 100 if stats.max_ds > 0 else 0
            
            # Track performance
            read_time = time.time() - read_start
            self.read_times.append(read_time)
            if len(self.read_times) > 100:
                self.read_times.pop(0)
            
            self.successful_reads += 1
            self.last_valid_stats = stats
            return stats
            
        except Exception as e:
            self.read_errors += 1
            self.logger.error(f"Error reading player stats: {e}")
            
            # Return last valid stats or defaults
            if self.last_valid_stats:
                return self.last_valid_stats
            return MemoryStats()
    
    def get_digimon_stats(self) -> DigimonStats:
        """Get current Digimon partner statistics"""
        if not self.connected:
            if self.last_digimon_stats:
                return self.last_digimon_stats
            return DigimonStats()
        
        try:
            # Read Digimon stats
            raw_stats = {}
            for stat_name, offsets in MEMORY_OFFSETS['digimon_stats'].items():
                raw_stats[stat_name] = self._read_pointer_chain(offsets)
            
            # Validate Digimon stats
            if self.config.validation_enabled and not self._validate_stats(raw_stats):
                if self.last_digimon_stats:
                    return self.last_digimon_stats
                return DigimonStats()
            
            # Create DigimonStats object
            stats = DigimonStats(
                hp=raw_stats.get('hp', 1000),
                max_hp=raw_stats.get('max_hp', 1000),
                ds=raw_stats.get('ds', 500),
                max_ds=raw_stats.get('max_ds', 500),
                level=raw_stats.get('level', 1),
                connected=True
            )
            
            # Calculate percentages
            stats.hp_pct = (stats.hp / stats.max_hp) * 100 if stats.max_hp > 0 else 0
            stats.ds_pct = (stats.ds / stats.max_ds) * 100 if stats.max_ds > 0 else 0
            
            self.last_digimon_stats = stats
            return stats
            
        except Exception as e:
            self.logger.error(f"Error reading Digimon stats: {e}")
            
            if self.last_digimon_stats:
                return self.last_digimon_stats
            return DigimonStats()
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get complete current game state"""
        player_stats = self.get_player_stats()
        digimon_stats = self.get_digimon_stats()
        
        return {
            'connected': self.connected,
            'player': player_stats,
            'digimon': digimon_stats,
            'stats': {
                'hp': player_stats.hp,
                'max_hp': player_stats.max_hp,
                'ds': player_stats.ds,
                'max_ds': player_stats.max_ds,
                'hp_pct': player_stats.hp_pct,
                'ds_pct': player_stats.ds_pct,
                'level': player_stats.level,
                'in_combat': player_stats.in_combat,
                'loading': player_stats.loading
            },
            'position': {
                'x': player_stats.position_x,
                'y': player_stats.position_y,
                'z': player_stats.position_z
            },
            'performance': self.get_performance_metrics()
        }
    
    def update_base_address(self, new_offset: str):
        """Update base memory offset"""
        try:
            self.config.base_offset = new_offset
            self.logger.info(f"Updated base offset to: {new_offset}")
        except Exception as e:
            self.logger.error(f"Failed to update base offset: {e}")
    
    def test_connection(self) -> Tuple[bool, Dict[str, Any]]:
        """Test memory connection and return diagnostic info"""
        if not self.connected:
            return False, {"error": "Not connected to memory"}
        
        try:
            test_stats = self.get_player_stats()
            
            diagnostic_info = {
                "connected": self.connected,
                "process_id": self.pm.process_id if self.pm else None,
                "base_address": hex(self.base_address) if self.base_address else None,
                "test_hp": test_stats.hp,
                "test_max_hp": test_stats.max_hp,
                "test_ds": test_stats.ds,
                "test_max_ds": test_stats.max_ds,
                "validation_enabled": self.config.validation_enabled,
                "read_errors": self.read_errors,
                "successful_reads": self.successful_reads
            }
            
            return True, diagnostic_info
            
        except Exception as e:
            return False, {"error": str(e)}
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get memory reader performance metrics"""
        avg_read_time = 0
        if self.read_times:
            avg_read_time = sum(self.read_times) / len(self.read_times)
        
        return {
            'connected': self.connected,
            'successful_reads': self.successful_reads,
            'read_errors': self.read_errors,
            'validation_failures': self.validation_failures,
            'avg_read_time': avg_read_time,
            'connection_attempts': self.connection_attempts,
            'error_rate': self.read_errors / max(1, self.successful_reads + self.read_errors)
        }
    
    def reset_error_counters(self):
        """Reset error counters"""
        self.read_errors = 0
        self.validation_failures = 0
        self.connection_attempts = 0
        self.successful_reads = 0