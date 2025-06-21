"""
Anti-detection timing system
"""

import time
import random
import threading
from typing import Dict
from utils.logger import Logger

class TimingSystem:
    """Anti-detection timing and behavior system"""
    
    def __init__(self, bot_engine):
        self.bot_engine = bot_engine
        self.logger = Logger()
        self.session_start = time.time()
        self.last_break = 0
        self.break_interval = random.uniform(1800, 3600)  # 30-60 minutes
        
        # Human-like timing
        self.fatigue_factor = 1.0
        self.attention_factor = 1.0
        
    def initialize(self) -> bool:
        """Initialize timing system"""
        try:
            self.logger.system("Anti-detection timing system initialized")
            return True
        except Exception as e:
            self.logger.error(f"Timing system initialization failed: {e}")
            return False
    
    def update(self, current_time: float, game_state=None):
        """Update timing system"""
        try:
            # Update fatigue over time
            session_duration = current_time - self.session_start
            self.fatigue_factor = 1.0 + (session_duration / 3600) * 0.1  # 10% slower per hour
            
            # Check for break time
            if current_time - self.last_break > self.break_interval:
                self.take_break()
                
        except Exception as e:
            self.logger.error(f"Timing system error: {e}")
    
    def take_break(self):
        """Take a random break"""
        break_duration = random.uniform(30, 300)  # 30 seconds to 5 minutes
        self.logger.break_time(f"Taking break for {break_duration/60:.1f} minutes")
        
        # Pause bot activities
        if hasattr(self.bot_engine, 'pause'):
            self.bot_engine.pause()
            
        # Schedule resume
        threading.Timer(break_duration, self.resume_from_break).start()
        
        self.last_break = time.time()
        self.break_interval = random.uniform(1800, 3600)  # Next break in 30-60 min
    
    def resume_from_break(self):
        """Resume from break"""
        self.logger.break_time("Resuming from break")
        if hasattr(self.bot_engine, 'resume'):
            self.bot_engine.resume()
    
    def get_human_delay(self, base_delay: float) -> float:
        """Get human-like delay"""
        # Apply fatigue and attention factors
        delay = base_delay * self.fatigue_factor * self.attention_factor
        
        # Add random variance
        variance = random.gauss(1.0, 0.1)
        delay *= max(0.5, min(2.0, variance))
        
        return delay
    
    def get_status(self) -> Dict:
        """Get timing system status"""
        return {
            'fatigue_factor': self.fatigue_factor,
            'attention_factor': self.attention_factor,
            'next_break': self.break_interval - (time.time() - self.last_break),
            'session_duration': time.time() - self.session_start
        }
    
    def get_health_status(self) -> Dict:
        """Get system health status"""
        return {
            'status': 'healthy',
            'errors': 0,
            'last_update': time.time()
        }
    
    def pause(self):
        """Pause timing system"""
        self.logger.system("Timing system paused")
    
    def resume(self):
        """Resume timing system"""
        self.logger.system("Timing system resumed")
    
    def stop(self):
        """Stop timing system"""
        self.logger.system("Timing system stopped")