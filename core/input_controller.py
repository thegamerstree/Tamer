"""
Advanced input control system with anti-detection timing
"""

import time
import random
import threading
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import win32api
import win32con

from config.constants import VK_CODES, TIMING_RANGES
from utils.logger import Logger

@dataclass
class KeyPress:
    """Represents a key press event"""
    key: str
    duration: float
    timestamp: float
    press_type: str  # 'tap', 'hold', 'hold_start', 'hold_end'

class InputController:
    """Advanced input controller with human-like timing and anti-detection"""
    
    def __init__(self):
        self.logger = Logger()
        self.held_keys = set()
        self.hold_threads = {}
        self.key_states = {}
        self.lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Timing and anti-detection
        self.key_history = []
        self.max_history = 100
        self.last_key_time = {}
        self.key_cooldowns = {}
        
        # Performance tracking
        self.total_inputs = 0
        self.failed_inputs = 0
        self.active_holds = 0
        
        # Human behavior simulation
        self.fatigue_factor = 1.0
        self.session_start = time.time()
        
    def tap(self, key: str, duration: Optional[float] = None, human_timing: bool = True) -> bool:
        """
        Tap a key with optional human-like timing
        
        Args:
            key: Key to press
            duration: How long to hold the key (auto-calculated if None)
            human_timing: Whether to apply human-like variance
        """
        if not self._validate_key(key):
            self.logger.error(f"Invalid key: {key}")
            return False
        
        # Calculate duration with human-like variance
        if duration is None:
            base_duration = random.uniform(0.03, 0.08)
            if human_timing:
                variance = random.gauss(1.0, 0.15)
                duration = max(0.02, base_duration * variance)
            else:
                duration = base_duration
        
        try:
            vk_code = VK_CODES.get(key.upper())
            if not vk_code:
                self.logger.error(f"No VK code for key: {key}")
                return False
            
            # Pre-press delay for human-like timing
            if human_timing:
                pre_delay = random.uniform(0.01, 0.03)
                time.sleep(pre_delay)
            
            # Press key
            win32api.keybd_event(vk_code, 0, 0, 0)
            
            # Hold duration
            time.sleep(duration)
            
            # Release key
            win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
            
            # Record the key press
            self._record_key_press(KeyPress(key, duration, time.time(), 'tap'))
            
            self.total_inputs += 1
            return True
            
        except Exception as e:
            self.failed_inputs += 1
            self.logger.error(f"Failed to tap key {key}: {e}")
            return False
    
    def hold(self, key: str, duration: float, human_timing: bool = True) -> bool:
        """
        Hold a key for a specific duration
        
        Args:
            key: Key to hold
            duration: How long to hold the key
            human_timing: Whether to apply human-like variance
        """
        if not self._validate_key(key):
            return False
        
        # Apply human timing variance
        if human_timing:
            variance = random.gauss(1.0, 0.1)
            duration = max(0.1, duration * variance)
            
            # Add micro-adjustments during long holds
            if duration > 2.0:
                micro_adjustments = random.randint(1, 3)
                adjustment_variance = duration * 0.05
                duration += random.uniform(-adjustment_variance, adjustment_variance)
        
        try:
            vk_code = VK_CODES.get(key.upper())
            if not vk_code:
                return False
            
            # Press key
            win32api.keybd_event(vk_code, 0, 0, 0)
            
            # Hold for duration
            time.sleep(duration)
            
            # Release key
            win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
            
            # Record the key press
            self._record_key_press(KeyPress(key, duration, time.time(), 'hold'))
            
            self.total_inputs += 1
            return True
            
        except Exception as e:
            self.failed_inputs += 1
            self.logger.error(f"Failed to hold key {key}: {e}")
            return False
    
    def start_hold(self, key: str) -> bool:
        """
        Start holding a key indefinitely until stop_hold is called
        
        Args:
            key: Key to start holding
        """
        if not self._validate_key(key):
            return False
        
        with self.lock:
            # Stop any existing hold for this key
            if key in self.held_keys:
                self.stop_hold(key)
            
            try:
                vk_code = VK_CODES.get(key.upper())
                if not vk_code:
                    return False
                
                # Add to held keys set
                self.held_keys.add(key)
                self.active_holds += 1
                
                def hold_loop():
                    """Loop to maintain key hold"""
                    try:
                        # Initial key press
                        win32api.keybd_event(vk_code, 0, 0, 0)
                        
                        # Keep key pressed while in held_keys
                        while key in self.held_keys:
                            time.sleep(0.01)  # Small sleep to prevent CPU spinning
                        
                        # Release key when done
                        win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
                        
                    except Exception as e:
                        self.logger.error(f"Error in hold loop for {key}: {e}")
                    finally:
                        # Ensure key is released and removed from sets
                        try:
                            win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
                        except:
                            pass
                        
                        with self.lock:
                            self.held_keys.discard(key)
                            self.hold_threads.pop(key, None)
                            self.active_holds = max(0, self.active_holds - 1)
                
                # Start hold thread
                hold_thread = threading.Thread(target=hold_loop, daemon=True)
                self.hold_threads[key] = hold_thread
                hold_thread.start()
                
                # Record the key press start
                self._record_key_press(KeyPress(key, 0, time.time(), 'hold_start'))
                
                return True
                
            except Exception as e:
                self.failed_inputs += 1
                self.logger.error(f"Failed to start hold for {key}: {e}")
                return False
    
    def stop_hold(self, key: Optional[str] = None) -> bool:
        """
        Stop holding a key or all keys
        
        Args:
            key: Specific key to stop holding, or None to stop all
        """
        with self.lock:
            try:
                if key:
                    # Stop specific key
                    if key in self.held_keys:
                        self.held_keys.remove(key)
                        
                        # Wait for thread to finish
                        if key in self.hold_threads:
                            thread = self.hold_threads[key]
                            thread.join(timeout=0.1)
                            
                            if thread.is_alive():
                                self.logger.warning(f"Hold thread for {key} did not terminate cleanly")
                        
                        # Record the key release
                        self._record_key_press(KeyPress(key, 0, time.time(), 'hold_end'))
                        
                        return True
                else:
                    # Stop all keys
                    keys_to_stop = list(self.held_keys)
                    for held_key in keys_to_stop:
                        self.stop_hold(held_key)
                    
                    return True
                    
            except Exception as e:
                self.logger.error(f"Failed to stop hold for {key}: {e}")
                return False
    
    def stop_all_inputs(self):
        """Emergency stop all inputs"""
        with self.lock:
            try:
                # Stop all held keys
                self.stop_hold()
                
                # Clear all states
                self.held_keys.clear()
                self.hold_threads.clear()
                self.active_holds = 0
                
                # Emergency release all possible keys
                for vk_code in VK_CODES.values():
                    try:
                        win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
                    except:
                        pass
                
                self.logger.info("All inputs stopped")
                
            except Exception as e:
                self.logger.error(f"Error stopping all inputs: {e}")
    
    def smart_key_sequence(self, keys: List[str], timing_type: str = 'normal') -> bool:
        """
        Execute a sequence of keys with intelligent timing
        
        Args:
            keys: List of keys to press in sequence
            timing_type: Type of timing ('fast', 'normal', 'slow', 'combat')
        """
        if not keys:
            return False
        
        timing_config = TIMING_RANGES.get(timing_type, TIMING_RANGES['attack'])
        
        try:
            for i, key in enumerate(keys):
                # Calculate inter-key delay
                if i > 0:
                    base_delay = random.uniform(0.1, 0.3)
                    
                    # Adjust based on timing type
                    if timing_type == 'fast':
                        base_delay *= 0.5
                    elif timing_type == 'slow':
                        base_delay *= 2.0
                    elif timing_type == 'combat':
                        base_delay *= 1.5
                    
                    # Add human variance
                    variance = random.gauss(1.0, 0.2)
                    delay = max(0.05, base_delay * variance)
                    
                    time.sleep(delay)
                
                # Press the key
                key_duration = random.uniform(0.03, 0.08)
                if not self.tap(key, key_duration, human_timing=True):
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to execute key sequence: {e}")
            return False
    
    def is_key_held(self, key: str) -> bool:
        """Check if a key is currently being held"""
        return key in self.held_keys
    
    def get_held_keys(self) -> List[str]:
        """Get list of currently held keys"""
        return list(self.held_keys)
    
    def _validate_key(self, key: str) -> bool:
        """Validate that a key is supported"""
        if not key or not isinstance(key, str):
            return False
        return key.upper() in VK_CODES
    
    def _record_key_press(self, key_press: KeyPress):
        """Record a key press for analysis and anti-detection"""
        self.key_history.append(key_press)
        
        # Maintain history size
        if len(self.key_history) > self.max_history:
            self.key_history.pop(0)
        
        # Update last key time
        self.last_key_time[key_press.key] = key_press.timestamp
    
    def get_key_statistics(self) -> Dict[str, any]:
        """Get statistics about key usage"""
        if not self.key_history:
            return {}
        
        # Count key usage
        key_counts = {}
        total_duration = 0
        
        for key_press in self.key_history:
            key = key_press.key
            key_counts[key] = key_counts.get(key, 0) + 1
            total_duration += key_press.duration
        
        # Calculate timing statistics
        recent_timings = [kp.duration for kp in self.key_history[-20:]]
        avg_timing = sum(recent_timings) / len(recent_timings) if recent_timings else 0
        
        # Calculate variance (for anti-detection analysis)
        if len(recent_timings) > 1:
            variance = sum((t - avg_timing) ** 2 for t in recent_timings) / len(recent_timings)
        else:
            variance = 0
        
        return {
            'total_inputs': self.total_inputs,
            'failed_inputs': self.failed_inputs,
            'success_rate': (self.total_inputs - self.failed_inputs) / max(1, self.total_inputs),
            'active_holds': self.active_holds,
            'key_counts': key_counts,
            'avg_timing': avg_timing,
            'timing_variance': variance,
            'held_keys': list(self.held_keys),
            'session_duration': time.time() - self.session_start
        }
    
    def apply_fatigue_factor(self):
        """Apply fatigue factor to timing (for realism)"""
        session_duration = time.time() - self.session_start
        
        # Increase fatigue over time (every 30 minutes)
        base_fatigue = 1.0 + (session_duration / 1800) * 0.1
        
        # Add random variance
        random_factor = random.uniform(0.95, 1.05)
        
        self.fatigue_factor = min(1.5, base_fatigue * random_factor)
    
    def get_adaptive_delay(self, action_type: str) -> float:
        """Get adaptive delay based on action type and current state"""
        base_config = TIMING_RANGES.get(action_type, TIMING_RANGES['attack'])
        
        # Base delay
        base_delay = random.uniform(base_config['min'], base_config['max'])
        
        # Apply fatigue
        base_delay *= self.fatigue_factor
        
        # Add human reaction time
        reaction_time = random.uniform(base_config['human_min'], base_config['human_max'])
        
        # Calculate total delay
        total_delay = base_delay + reaction_time
        
        # Add variance
        variance = random.gauss(1.0, base_config['variance'])
        total_delay *= max(0.5, min(2.0, variance))
        
        return total_delay
    
    def cleanup(self):
        """Clean up resources and stop all inputs"""
        try:
            self.stop_all_inputs()
            self.executor.shutdown(wait=True)
            self.logger.info("Input controller cleaned up")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

class InputSequenceBuilder:
    """Builder for complex input sequences"""
    
    def __init__(self, controller: InputController):
        self.controller = controller
        self.sequence = []
    
    def add_tap(self, key: str, duration: Optional[float] = None):
        """Add a tap to the sequence"""
        self.sequence.append(('tap', key, duration))
        return self
    
    def add_hold(self, key: str, duration: float):
        """Add a hold to the sequence"""
        self.sequence.append(('hold', key, duration))
        return self
    
    def add_delay(self, duration: float):
        """Add a delay to the sequence"""
        self.sequence.append(('delay', None, duration))
        return self
    
    def add_smart_delay(self, action_type: str):
        """Add an adaptive delay based on action type"""
        self.sequence.append(('smart_delay', action_type, None))
        return self
    
    def execute(self, human_timing: bool = True) -> bool:
        """Execute the built sequence"""
        try:
            for action_type, key, duration in self.sequence:
                if action_type == 'tap':
                    if not self.controller.tap(key, duration, human_timing):
                        return False
                elif action_type == 'hold':
                    if not self.controller.hold(key, duration, human_timing):
                        return False
                elif action_type == 'delay':
                    if human_timing:
                        # Add variance to delays
                        variance = random.gauss(1.0, 0.1)
                        actual_duration = max(0.01, duration * variance)
                    else:
                        actual_duration = duration
                    time.sleep(actual_duration)
                elif action_type == 'smart_delay':
                    delay = self.controller.get_adaptive_delay(key)  # key contains action_type here
                    time.sleep(delay)
            
            return True
            
        except Exception as e:
            self.controller.logger.error(f"Failed to execute sequence: {e}")
            return False
    
    def clear(self):
        """Clear the sequence"""
        self.sequence = []
        return self