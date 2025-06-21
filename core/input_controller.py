"""
Fixed Input Controller for GDMO Bot
Handles keyboard input with proper thread safety and error handling
"""

import time
import threading
import logging
from typing import Dict, Set, Optional

logger = logging.getLogger(__name__)

# Check for win32api availability
WIN32_AVAILABLE = False
try:
    import win32api
    WIN32_AVAILABLE = True
except ImportError:
    logger.warning("win32api not available - input features disabled")


class InputController:
    """Enhanced input controller with thread safety and error handling"""
    
    # Virtual key codes for common keys
    VK_CODES = {
        # Numbers
        **{str(i): 0x30 + i for i in range(0, 10)},
        # Function keys
        **{f"F{i}": 0x6F + i for i in range(1, 13)},
        # Movement keys
        "W": 0x57, "A": 0x41, "S": 0x53, "D": 0x44,
        # Special keys
        "TAB": 0x09, "SPACE": 0x20, "SHIFT": 0x10,
        "CTRL": 0x11, "ALT": 0x12, "ENTER": 0x0D,
        "ESC": 0x1B, "BACKSPACE": 0x08, "DELETE": 0x2E,
        # Arrow keys
        "UP": 0x26, "DOWN": 0x28, "LEFT": 0x25, "RIGHT": 0x27,
    }
    
    def __init__(self):
        self.held_keys: Set[str] = set()
        self.hold_threads: Dict[str, threading.Thread] = {}
        self.lock = threading.RLock()  # Use RLock for nested locking
        self.enabled = WIN32_AVAILABLE
        self.key_press_delay = 0.05  # Default delay between key press/release
        self.hold_check_interval = 0.01  # How often to check if we should stop holding
        
        # Statistics
        self.stats = {
            'total_taps': 0,
            'total_holds': 0,
            'active_holds': 0,
            'errors': 0
        }
        
        if not WIN32_AVAILABLE:
            logger.error("win32api not available - input controller disabled")

    def is_valid_key(self, key: str) -> bool:
        """
        Check if a key is valid and supported
        
        Args:
            key: Key name to check
            
        Returns:
            True if key is valid, False otherwise
        """
        return key.upper() in self.VK_CODES

    def get_vk_code(self, key: str) -> Optional[int]:
        """
        Get virtual key code for a key name
        
        Args:
            key: Key name
            
        Returns:
            Virtual key code or None if invalid
        """
        return self.VK_CODES.get(key.upper())

    def tap(self, key: str, delay: Optional[float] = None) -> bool:
        """
        Tap a key (press and release)
        
        Args:
            key: Key to tap
            delay: Optional custom delay between press and release
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            logger.debug("Input controller disabled")
            return False
        
        if delay is None:
            delay = self.key_press_delay
        
        vk_code = self.get_vk_code(key)
        if not vk_code:
            logger.warning(f"Invalid key for tap: {key}")
            return False
        
        try:
            with self.lock:
                # Make sure key isn't currently being held
                if key.upper() in self.held_keys:
                    logger.warning(f"Cannot tap {key} - currently being held")
                    return False
                
                # Press key
                win32api.keybd_event(vk_code, 0, 0, 0)
                time.sleep(delay)
                # Release key
                win32api.keybd_event(vk_code, 0, 2, 0)  # 2 = KEYEVENTF_KEYUP
                
                self.stats['total_taps'] += 1
                logger.debug(f"Tapped key: {key}")
                return True
                
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Error tapping key {key}: {e}")
            return False

    def hold(self, key: str, duration: float = 0.4) -> bool:
        """
        Hold a key for a specific duration
        
        Args:
            key: Key to hold
            duration: How long to hold the key
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            logger.debug("Input controller disabled")
            return False
        
        vk_code = self.get_vk_code(key)
        if not vk_code:
            logger.warning(f"Invalid key for hold: {key}")
            return False
        
        try:
            with self.lock:
                # Make sure key isn't currently being held
                if key.upper() in self.held_keys:
                    logger.warning(f"Cannot hold {key} - already being held")
                    return False
                
                # Press key
                win32api.keybd_event(vk_code, 0, 0, 0)
                time.sleep(duration)
                # Release key
                win32api.keybd_event(vk_code, 0, 2, 0)
                
                self.stats['total_holds'] += 1
                logger.debug(f"Held key {key} for {duration}s")
                return True
                
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Error holding key {key}: {e}")
            return False

    def start_hold(self, key: str) -> bool:
        """
        Start holding a key indefinitely until stop_hold is called
        
        Args:
            key: Key to start holding
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            logger.debug("Input controller disabled")
            return False
        
        key_upper = key.upper()
        vk_code = self.get_vk_code(key_upper)
        if not vk_code:
            logger.warning(f"Invalid key for start_hold: {key}")
            return False
        
        with self.lock:
            # Stop any existing hold for this key
            if key_upper in self.held_keys:
                self.stop_hold(key_upper)
            
            try:
                # Add to held keys set
                self.held_keys.add(key_upper)
                
                def hold_loop():
                    """Thread function to maintain key hold"""
                    try:
                        # Press key down
                        win32api.keybd_event(vk_code, 0, 0, 0)
                        logger.debug(f"Started holding key: {key_upper}")
                        
                        # Keep checking if we should continue holding
                        while key_upper in self.held_keys:
                            time.sleep(self.hold_check_interval)
                        
                        # Release key
                        win32api.keybd_event(vk_code, 0, 2, 0)
                        logger.debug(f"Stopped holding key: {key_upper}")
                        
                    except Exception as e:
                        logger.error(f"Error in hold loop for {key_upper}: {e}")
                        self.stats['errors'] += 1
                    finally:
                        # Ensure key is removed from held set
                        with self.lock:
                            self.held_keys.discard(key_upper)
                            if key_upper in self.hold_threads:
                                del self.hold_threads[key_upper]
                
                # Start the hold thread
                hold_thread = threading.Thread(
                    target=hold_loop,
                    name=f"Hold-{key_upper}",
                    daemon=True
                )
                self.hold_threads[key_upper] = hold_thread
                hold_thread.start()
                
                self.stats['active_holds'] += 1
                return True
                
            except Exception as e:
                # Clean up on error
                self.held_keys.discard(key_upper)
                self.stats['errors'] += 1
                logger.error(f"Error starting hold for {key}: {e}")
                return False

    def stop_hold(self, key: Optional[str] = None) -> bool:
        """
        Stop holding a key or all keys
        
        Args:
            key: Specific key to stop holding, or None to stop all
            
        Returns:
            True if successful, False otherwise
        """
        with self.lock:
            try:
                if key is None:
                    # Stop all held keys
                    keys_to_stop = list(self.held_keys)
                    for held_key in keys_to_stop:
                        self._stop_single_key(held_key)
                    logger.debug("Stopped holding all keys")
                else:
                    # Stop specific key
                    key_upper = key.upper()
                    self._stop_single_key(key_upper)
                    logger.debug(f"Stopped holding key: {key_upper}")
                
                return True
                
            except Exception as e:
                self.stats['errors'] += 1
                logger.error(f"Error stopping hold: {e}")
                return False

    def _stop_single_key(self, key_upper: str) -> None:
        """
        Internal method to stop holding a single key
        
        Args:
            key_upper: Uppercase key name to stop holding
        """
        if key_upper in self.held_keys:
            # Remove from held keys set (this will stop the hold loop)
            self.held_keys.discard(key_upper)
            self.stats['active_holds'] = max(0, self.stats['active_holds'] - 1)
            
            # Wait for thread to finish
            if key_upper in self.hold_threads:
                thread = self.hold_threads[key_upper]
                thread.join(timeout=0.5)  # Wait up to 500ms
                
                if thread.is_alive():
                    logger.warning(f"Hold thread for {key_upper} did not terminate cleanly")
                else:
                    del self.hold_threads[key_upper]

    def emergency_release_all(self) -> None:
        """
        Emergency function to release all held keys immediately
        This bypasses normal cleanup for critical situations
        """
        if not self.enabled:
            return
        
        try:
            with self.lock:
                # Try to release all currently held keys
                for key_upper in list(self.held_keys):
                    vk_code = self.get_vk_code(key_upper)
                    if vk_code:
                        try:
                            win32api.keybd_event(vk_code, 0, 2, 0)  # Release
                        except:
                            pass
                
                # Clear all tracking
                self.held_keys.clear()
                self.hold_threads.clear()
                self.stats['active_holds'] = 0
                
                logger.info("Emergency release of all keys completed")
                
        except Exception as e:
            logger.error(f"Error in emergency release: {e}")

    def get_held_keys(self) -> Set[str]:
        """
        Get set of currently held keys
        
        Returns:
            Set of key names currently being held
        """
        with self.lock:
            return self.held_keys.copy()

    def is_holding(self, key: str) -> bool:
        """
        Check if a specific key is currently being held
        
        Args:
            key: Key to check
            
        Returns:
            True if key is being held, False otherwise
        """
        with self.lock:
            return key.upper() in self.held_keys

    def get_stats(self) -> Dict[str, int]:
        """
        Get input controller statistics
        
        Returns:
            Dictionary with usage statistics
        """
        with self.lock:
            return self.stats.copy()

    def cleanup(self) -> None:
        """Clean up all resources and stop all key holds"""
        logger.info("Cleaning up input controller...")
        
        # Emergency release all keys
        self.emergency_release_all()
        
        # Wait for all threads to finish
        for key, thread in list(self.hold_threads.items()):
            try:
                thread.join(timeout=1.0)
                if thread.is_alive():
                    logger.warning(f"Thread for {key} did not terminate within timeout")
            except:
                pass
        
        # Clear all data
        with self.lock:
            self.held_keys.clear()
            self.hold_threads.clear()
            self.stats['active_holds'] = 0
        
        logger.info("Input controller cleanup completed")

    def __del__(self):
        """Destructor to ensure cleanup on object deletion"""
        try:
            self.cleanup()
        except:
            pass


# Global instance for backward compatibility
_global_controller = None

def get_controller() -> InputController:
    """Get the global input controller instance"""
    global _global_controller
    if _global_controller is None:
        _global_controller = InputController()
    return _global_controller

# Backward compatibility functions
def tap(key: str, delay: float = 0.05) -> bool:
    """Backward compatibility wrapper for tap"""
    return get_controller().tap(key, delay)

def hold(key: str, duration: float = 0.4) -> bool:
    """Backward compatibility wrapper for hold"""
    return get_controller().hold(key, duration)

def start_hold(key: str) -> bool:
    """Backward compatibility wrapper for start_hold"""
    return get_controller().start_hold(key)

def stop_hold(key: Optional[str] = None) -> bool:
    """Backward compatibility wrapper for stop_hold"""
    return get_controller().stop_hold(key)

def cleanup() -> None:
    """Backward compatibility wrapper for cleanup"""
    get_controller().cleanup()
