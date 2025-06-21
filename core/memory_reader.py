"""
Fixed Memory Reader for GDMO Bot
Handles game memory access with proper error handling and stability
"""

import time
import random
import logging
import psutil
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# Check for pymem availability
PYMEM_AVAILABLE = False
try:
    import pymem
    PYMEM_AVAILABLE = True
except ImportError:
    logger.warning("Pymem not available - memory features disabled")


class MemoryReader:
    """Enhanced memory reader with stability improvements"""
    
    def __init__(self, process_name: str = "GDMO.exe"):
        self.process_name = process_name
        self.pm = None
        self.connected = False
        self.base_address = None
        self.connection_attempts = 0
        self.max_connection_attempts = 5
        self.last_connection_attempt = 0
        self.connection_retry_delay = 5.0
        
        # Memory offsets for GDMO
        self.base_offset = 0x0072FF80
        self.offsets = {
            'hp': [0x40, 0, 4, 8, 0x14, 0xAC, 0x80],
            'max_hp': [0x40, 0, 4, 8, 0x14, 0xAC, 0x74],
            'ds': [0x40, 0, 4, 8, 0x14, 0xB0, 0x80],
            'max_ds': [0x40, 0, 4, 8, 0x14, 0xB0, 0x7C],
        }
        
        # Cache for valid stats
        self.last_valid_stats = None
        self.last_stats_update = 0
        self.stats_cache_duration = 1.0  # Cache stats for 1 second
        
        # Error tracking
        self.consecutive_errors = 0
        self.max_consecutive_errors = 10

    def connect(self) -> bool:
        """
        Connect to game process with retry logic
        
        Returns:
            True if connected successfully, False otherwise
        """
        if not PYMEM_AVAILABLE:
            logger.error("Pymem not available")
            return False
        
        current_time = time.time()
        
        # Check if we should retry connection
        if (self.connection_attempts >= self.max_connection_attempts and 
            current_time - self.last_connection_attempt < self.connection_retry_delay):
            return False
        
        # Reset connection attempts after retry delay
        if current_time - self.last_connection_attempt > self.connection_retry_delay:
            self.connection_attempts = 0
        
        try:
            # Check if already connected and process still exists
            if self.connected and self.pm:
                try:
                    if psutil.pid_exists(self.pm.process_id):
                        # Test the connection with a simple read
                        test_read = self.pm.read_uint(self.base_address + self.base_offset)
                        return True
                except:
                    pass
            
            # Find game process
            game_processes = []
            for process in psutil.process_iter(['pid', 'name']):
                try:
                    if self.process_name.lower() in process.info['name'].lower():
                        game_processes.append(process)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if not game_processes:
                logger.debug(f"No {self.process_name} processes found")
                return False
            
            # Try to connect to the first available process
            target_process = game_processes[0]
            self.pm = pymem.Pymem(target_process.info['name'])
            
            # Get base address
            self.base_address = pymem.process.module_from_name(
                self.pm.process_handle, 
                self.process_name
            ).lpBaseOfDll
            
            self.connected = True
            self.connection_attempts = 0
            self.consecutive_errors = 0
            
            logger.info(f"Connected to {self.process_name} (PID: {target_process.info['pid']})")
            return True
            
        except Exception as e:
            self.connected = False
            self.connection_attempts += 1
            self.last_connection_attempt = current_time
            
            logger.debug(f"Connection attempt {self.connection_attempts} failed: {e}")
            
            if self.connection_attempts >= self.max_connection_attempts:
                logger.error(f"Failed to connect after {self.max_connection_attempts} attempts")
            
            return False

    def read_pointer_chain(self, offset_chain: List[int]) -> int:
        """
        Read value from pointer chain with error handling
        
        Args:
            offset_chain: List of memory offsets to follow
            
        Returns:
            Value at end of pointer chain, or 0 if error
        """
        if not self.connected or not self.pm:
            return 0
        
        try:
            # Start with base address + base offset
            current_address = self.pm.read_uint(self.base_address + self.base_offset)
            
            # Follow the pointer chain
            for i, offset in enumerate(offset_chain[:-1]):
                current_address = self.pm.read_uint(current_address + offset)
                
                # Add small random delay to avoid detection
                if i % 2 == 0:  # Only delay every other read
                    time.sleep(random.uniform(0.001, 0.003))
            
            # Read final value
            final_address = current_address + offset_chain[-1]
            value = self.pm.read_int(final_address)
            
            # Reset error counter on successful read
            self.consecutive_errors = 0
            
            return value
            
        except Exception as e:
            self.consecutive_errors += 1
            
            # Log error only occasionally to avoid spam
            if self.consecutive_errors <= 3 or self.consecutive_errors % 10 == 0:
                logger.debug(f"Pointer chain read error (attempt {self.consecutive_errors}): {e}")
            
            # Disconnect if too many consecutive errors
            if self.consecutive_errors >= self.max_consecutive_errors:
                logger.warning("Too many consecutive memory errors - disconnecting")
                self.disconnect()
            
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Get current player stats with caching and validation
        
        Returns:
            Dictionary containing HP, DS, and connection status
        """
        current_time = time.time()
        
        # Return cached stats if still valid
        if (self.last_valid_stats and 
            current_time - self.last_stats_update < self.stats_cache_duration):
            return self.last_valid_stats
        
        # Default stats for when not connected
        default_stats = {
            'hp': 1000,
            'ds': 500,
            'max_hp': 1000,
            'max_ds': 500,
            'hp_pct': 100.0,
            'ds_pct': 100.0,
            'connected': False
        }
        
        if not self.connected:
            return self.last_valid_stats or default_stats
        
        try:
            # Read all values
            hp = self.read_pointer_chain(self.offsets['hp'])
            max_hp = self.read_pointer_chain(self.offsets['max_hp'])
            ds = self.read_pointer_chain(self.offsets['ds'])
            max_ds = self.read_pointer_chain(self.offsets['max_ds'])
            
            # Validate the values
            if self._validate_stats(hp, max_hp, ds, max_ds):
                # Calculate percentages
                hp_pct = (hp / max_hp * 100) if max_hp > 0 else 0
                ds_pct = (ds / max_ds * 100) if max_ds > 0 else 0
                
                stats = {
                    'hp': hp,
                    'ds': ds,
                    'max_hp': max_hp,
                    'max_ds': max_ds,
                    'hp_pct': hp_pct,
                    'ds_pct': ds_pct,
                    'connected': True
                }
                
                # Cache the valid stats
                self.last_valid_stats = stats
                self.last_stats_update = current_time
                
                return stats
            else:
                logger.debug(f"Invalid stats read: HP={hp}/{max_hp}, DS={ds}/{max_ds}")
                
        except Exception as e:
            logger.debug(f"Error reading stats: {e}")
        
        # Return last valid stats or defaults
        return self.last_valid_stats or default_stats

    def _validate_stats(self, hp: int, max_hp: int, ds: int, max_ds: int) -> bool:
        """
        Validate that stat values are reasonable
        
        Args:
            hp, max_hp, ds, max_ds: Stat values to validate
            
        Returns:
            True if values seem valid, False otherwise
        """
        # Basic range checks
        if not all(0 <= v <= 50000 for v in (hp, max_hp, ds, max_ds)):
            return False
        
        # Values should be positive
        if not all(v > 0 for v in (max_hp, max_ds)):
            return False
        
        # Current values shouldn't exceed max by more than 10%
        if hp > max_hp * 1.1 or ds > max_ds * 1.1:
            return False
        
        # Max values should be reasonable minimums
        if max_hp < 100 or max_ds < 50:
            return False
        
        return True

    def update_addresses(self, new_base_offset: str) -> bool:
        """
        Update base memory offset
        
        Args:
            new_base_offset: New base offset as hex string
            
        Returns:
            True if successfully updated, False otherwise
        """
        try:
            # Convert hex string to integer
            if isinstance(new_base_offset, str):
                if new_base_offset.startswith('0x'):
                    new_offset = int(new_base_offset, 16)
                else:
                    new_offset = int(new_base_offset, 16)
            else:
                new_offset = int(new_base_offset)
            
            old_offset = self.base_offset
            self.base_offset = new_offset
            
            logger.info(f"Updated base offset from {hex(old_offset)} to {hex(new_offset)}")
            
            # Clear cached stats since addresses changed
            self.last_valid_stats = None
            
            return True
            
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid base offset format: {new_base_offset} - {e}")
            return False

    def disconnect(self) -> None:
        """Safely disconnect from game process"""
        if self.pm:
            try:
                self.pm.close_process()
            except:
                pass
            finally:
                self.pm = None
        
        self.connected = False
        self.consecutive_errors = 0
        logger.debug("Disconnected from game process")

    def cleanup(self) -> None:
        """Clean up resources"""
        self.disconnect()
        self.last_valid_stats = None

    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get information about the current connection
        
        Returns:
            Dictionary with connection details
        """
        info = {
            'connected': self.connected,
            'process_name': self.process_name,
            'base_offset': hex(self.base_offset),
            'connection_attempts': self.connection_attempts,
            'consecutive_errors': self.consecutive_errors,
            'pymem_available': PYMEM_AVAILABLE
        }
        
        if self.connected and self.pm:
            try:
                info.update({
                    'process_id': self.pm.process_id,
                    'base_address': hex(self.base_address) if self.base_address else None
                })
            except:
                pass
        
        return info

    def test_connection(self) -> Dict[str, Any]:
        """
        Test the memory connection and return diagnostic info
        
        Returns:
            Dictionary with test results
        """
        result = {
            'success': False,
            'error': None,
            'stats': None,
            'connection_info': self.get_connection_info()
        }
        
        try:
            if not self.connected:
                if not self.connect():
                    result['error'] = "Failed to connect to game process"
                    return result
            
            # Try to read stats
            stats = self.get_stats()
            
            if stats['connected']:
                result['success'] = True
                result['stats'] = stats
            else:
                result['error'] = "Connected but unable to read valid stats"
                
        except Exception as e:
            result['error'] = f"Test failed with exception: {e}"
        
        return result
