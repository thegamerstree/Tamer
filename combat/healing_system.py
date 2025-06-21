"""
Enhanced Healing System for GDMO Bot
Improved version with better logic and error handling
"""

import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class HealingItem:
    """Data class for healing item configuration"""
    name: str
    key: str
    enabled: bool
    threshold: int
    item_type: str  # 'hp' or 'ds'
    priority: int = 0  # Higher = more priority


@dataclass
class HealingConfig:
    """Configuration for healing system"""
    combat_heal_delay: float = 2.5
    normal_heal_delay: float = 1.5
    emergency_multiplier: float = 0.8
    health_check_interval: float = 0.5
    max_heal_attempts: int = 3
    overheal_protection: int = 5
    item_cooldown: float = 2.0
    panic_threshold: int = 15
    smart_prediction: bool = True
    emergency_threshold: int = 25


class EnhancedHealing:
    """Enhanced healing system with improved logic and safety"""
    
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.config = HealingConfig()
        
        # Timing tracking
        self.last_heal_attempt = {'hp': 0, 'ds': 0}
        self.last_stats = {'hp_pct': 100, 'ds_pct': 100}
        self.healing_cooldowns = {}
        
        # Statistics and state
        self.failed_heals = {'hp': 0, 'ds': 0}
        self.healing_in_progress = False
        self.total_heals_used = {'hp': 0, 'ds': 0}
        self.emergency_heals = 0
        
        # Health trend analysis
        self.health_history = []
        self.max_health_history = 10
        
        logger.info("Enhanced healing system initialized")

    def update_config(self, **kwargs) -> None:
        """Update healing configuration"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                logger.debug(f"Updated healing config: {key} = {value}")

    def add_health_sample(self, hp_pct: float, ds_pct: float) -> None:
        """Add health sample for trend analysis"""
        current_time = time.time()
        sample = {
            'time': current_time,
            'hp_pct': hp_pct,
            'ds_pct': ds_pct
        }
        
        self.health_history.append(sample)
        
        # Keep only recent history
        while len(self.health_history) > self.max_health_history:
            self.health_history.pop(0)

    def get_health_trend(self, stat_type: str) -> float:
        """
        Calculate health trend (positive = gaining, negative = losing)
        
        Args:
            stat_type: 'hp' or 'ds'
            
        Returns:
            Trend value in percentage points per second
        """
        if len(self.health_history) < 2:
            return 0.0
        
        recent_samples = self.health_history[-3:]  # Use last 3 samples
        if len(recent_samples) < 2:
            return 0.0
        
        first_sample = recent_samples[0]
        last_sample = recent_samples[-1]
        
        time_diff = last_sample['time'] - first_sample['time']
        if time_diff <= 0:
            return 0.0
        
        stat_key = f'{stat_type}_pct'
        value_diff = last_sample[stat_key] - first_sample[stat_key]
        
        return value_diff / time_diff

    def get_available_healing_items(self, stat_type: str) -> List[HealingItem]:
        """
        Get available healing items for HP or DS
        
        Args:
            stat_type: 'hp' or 'ds'
            
        Returns:
            List of available healing items
        """
        available_items = []
        current_time = time.time()
        
        # Get items from bot configuration
        for name, data in self.bot.heal_items.items():
            if not data['enabled'].get():
                continue
            
            # Filter by type
            if stat_type == 'hp' and 'Recovery' not in name:
                continue
            if stat_type == 'ds' and 'Energy' not in name:
                continue
            
            key = data['key'].get().upper().strip()
            if not key or not self.bot.input_controller.is_valid_key(key):
                continue
            
            # Check cooldown
            if key in self.healing_cooldowns:
                time_since_use = current_time - self.healing_cooldowns[key]
                if time_since_use < self.config.item_cooldown:
                    continue
            
            # Create healing item object
            item = HealingItem(
                name=name,
                key=key,
                enabled=data['enabled'].get(),
                threshold=data['threshold'].get(),
                item_type=stat_type,
                priority=self._calculate_item_priority(name, data['threshold'].get())
            )
            
            available_items.append(item)
        
        # Sort by priority (higher priority first)
        available_items.sort(key=lambda x: x.priority, reverse=True)
        
        return available_items

    def _calculate_item_priority(self, item_name: str, threshold: int) -> int:
        """Calculate priority for healing item"""
        base_priority = 100
        
        # Emergency items get higher priority
        if 'Mega' in item_name:
            base_priority += 300
        elif 'Hi-' in item_name:
            base_priority += 200
        elif 'Recovery' in item_name or 'Energy' in item_name:
            base_priority += 100
        
        # Lower threshold = higher emergency priority
        threshold_priority = (100 - threshold) * 2
        
        return base_priority + threshold_priority

    def get_best_healing_item(self, current_pct: float, stat_type: str) -> Optional[HealingItem]:
        """
        Get the best healing item for current situation
        
        Args:
            current_pct: Current HP or DS percentage
            stat_type: 'hp' or 'ds'
            
        Returns:
            Best healing item or None
        """
        available_items = self.get_available_healing_items(stat_type)
        
        if not available_items:
            return None
        
        # Filter items based on current percentage and overheal protection
        suitable_items = []
        
        for item in available_items:
            # Skip if we're too healthy for this item
            if current_pct > item.threshold + self.config.overheal_protection:
                continue
            
            # Calculate item score
            score = self._calculate_item_score(item, current_pct, stat_type)
            suitable_items.append((item, score))
        
        if not suitable_items:
            return None
        
        # Sort by score and return best item
        suitable_items.sort(key=lambda x: x[1], reverse=True)
        best_item, best_score = suitable_items[0]
        
        logger.debug(f"Selected {best_item.name} (score: {best_score:.1f}) for {stat_type}")
        return best_item

    def _calculate_item_score(self, item: HealingItem, current_pct: float, stat_type: str) -> float:
        """Calculate scoring for healing item selection"""
        score = 0.0
        
        # Base score from priority
        score += item.priority
        
        # Emergency bonus
        if current_pct <= self.config.panic_threshold:
            score += 500
        elif current_pct <= self.config.emergency_threshold:
            score += 300
        
        # Threshold matching (closer threshold = better)
        threshold_diff = abs(item.threshold - current_pct)
        score += max(0, 100 - threshold_diff)
        
        # Health trend consideration
        if self.config.smart_prediction:
            trend = self.get_health_trend(stat_type)
            if trend < -5:  # Rapidly losing health
                score += 200
            elif trend < -2:  # Slowly losing health
                score += 100
        
        # Avoid overheal penalty
        potential_overheal = max(0, item.threshold - current_pct)
        score -= potential_overheal * 2
        
        return score

    def should_heal_now(self, stats: Dict[str, Any], stat_type: str) -> Tuple[bool, str]:
        """
        Determine if healing is needed now
        
        Args:
            stats: Current player stats
            stat_type: 'hp' or 'ds'
            
        Returns:
            Tuple of (should_heal, reason)
        """
        current_time = time.time()
        current_pct = stats[f'{stat_type}_pct']
        
        # Check if we're already at full health
        if current_pct >= 100 - self.config.overheal_protection:
            return False, "Near full"
        
        # Check timing constraints
        last_heal_time = self.last_heal_attempt[stat_type]
        min_delay = self._get_min_heal_delay()
        
        if current_time - last_heal_time < min_delay:
            remaining = min_delay - (current_time - last_heal_time)
            return False, f"Cooldown ({remaining:.1f}s)"
        
        # Emergency healing (always allow)
        if current_pct <= self.config.panic_threshold:
            return True, "PANIC"
        
        # Emergency threshold
        if current_pct <= self.config.emergency_threshold:
            return True, "EMERGENCY"
        
        # Smart prediction based on health trend
        if self.config.smart_prediction:
            trend = self.get_health_trend(stat_type)
            if trend < -10:  # Very rapid health loss
                return True, "Rapid decline"
            elif trend < -5 and current_pct < 70:  # Moderate loss at moderate health
                return True, "Declining health"
        
        # Check if we have a suitable item for current threshold
        best_item = self.get_best_healing_item(current_pct, stat_type)
        if best_item and current_pct <= best_item.threshold:
            return True, f"Threshold ({best_item.threshold}%)"
        
        return False, "No need"

    def _get_min_heal_delay(self) -> float:
        """Get minimum delay between heals based on combat state"""
        # Check if in combat (you may need to adjust this based on your bot's combat detection)
        in_combat = getattr(self.bot, 'target_locked', False) or \
                   getattr(self.bot, 'hunting_state', 'idle') == 'engaging'
        
        if in_combat:
            return self.config.combat_heal_delay * self.config.emergency_multiplier
        else:
            return self.config.normal_heal_delay

    def execute_healing(self, item: HealingItem, stats: Dict[str, Any], reason: str) -> bool:
        """
        Execute healing with the specified item
        
        Args:
            item: Healing item to use
            stats: Current player stats
            reason: Reason for healing
            
        Returns:
            True if successful, False otherwise
        """
        current_time = time.time()
        current_pct = stats[f'{item.item_type}_pct']
        
        self.healing_in_progress = True
        
        try:
            # Stop any current movement
            if hasattr(self.bot, 'input_controller'):
                self.bot.input_controller.stop_hold()
            
            # Small delay for safety
            time.sleep(0.1)
            
            # Use the healing item
            success = self.bot.input_controller.tap(item.key)
            
            if success:
                # Update tracking
                self.healing_cooldowns[item.key] = current_time
                self.last_heal_attempt[item.item_type] = current_time
                self.total_heals_used[item.item_type] += 1
                
                # Update bot stats if available
                if hasattr(self.bot, 'stats') and 'heals' in self.bot.stats:
                    self.bot.stats['heals'] += 1
                
                if hasattr(self.bot, 'last_heal'):
                    self.bot.last_heal = current_time
                
                # Track emergency heals
                if current_pct <= self.config.emergency_threshold:
                    self.emergency_heals += 1
                
                # Reset failed heal counter
                self.failed_heals[item.item_type] = 0
                
                # Log the heal
                log_msg = f"✚ {item.name} ({item.key}) | {current_pct:.1f}% | {reason}"
                if hasattr(self.bot, 'log'):
                    self.bot.log(log_msg, "🏥")
                else:
                    logger.info(log_msg)
                
                return True
            else:
                raise Exception("Failed to send key input")
                
        except Exception as e:
            self.failed_heals[item.item_type] += 1
            error_msg = f"Heal failed: {e}"
            
            if hasattr(self.bot, 'log'):
                self.bot.log(error_msg, "❌")
            else:
                logger.error(error_msg)
            
            return False
            
        finally:
            self.healing_in_progress = False

    def check_enhanced_healing(self, current_time: Optional[float] = None) -> None:
        """
        Main healing check function - call this regularly
        
        Args:
            current_time: Current time (will use time.time() if None)
        """
        if current_time is None:
            current_time = time.time()
        
        # Skip if healing disabled or already in progress
        if not getattr(self.bot.config, 'smart_healing', {}).get() or self.healing_in_progress:
            return
        
        # Get current stats
        try:
            if hasattr(self.bot, 'memory') and hasattr(self.bot.config, 'use_memory'):
                if self.bot.config['use_memory'].get():
                    stats = self.bot.memory.get_stats()
                else:
                    stats = self._get_default_stats()
            else:
                stats = self._get_default_stats()
        except Exception as e:
            logger.error(f"Error getting stats for healing: {e}")
            return
        
        # Skip if not connected to memory when required
        if not stats.get('connected', False) and getattr(self.bot.config, 'use_memory', {}).get():
            return
        
        # Add to health history
        self.add_health_sample(stats['hp_pct'], stats['ds_pct'])
        
        # Determine healing priorities
        healing_actions = []
        
        for stat_type in ['hp', 'ds']:
            should_heal, reason = self.should_heal_now(stats, stat_type)
            
            if should_heal:
                best_item = self.get_best_healing_item(stats[f'{stat_type}_pct'], stat_type)
                
                if best_item:
                    # Calculate priority (lower = more urgent)
                    priority = 1 if stats[f'{stat_type}_pct'] <= self.config.panic_threshold else \
                              2 if stats[f'{stat_type}_pct'] <= self.config.emergency_threshold else 3
                    
                    healing_actions.append((priority, stat_type, best_item, reason))
        
        # Execute most urgent healing
        if healing_actions:
            # Sort by priority (most urgent first)
            healing_actions.sort(key=lambda x: x[0])
            priority, stat_type, item, reason = healing_actions[0]
            
            success = self.execute_healing(item, stats, reason)
            
            if not success:
                self.failed_heals[stat_type] += 1
                
                # Log if too many failures
                if self.failed_heals[stat_type] >= self.config.max_heal_attempts:
                    error_msg = f"Max {stat_type.upper()} heal attempts reached ({self.config.max_heal_attempts})"
                    if hasattr(self.bot, 'log'):
                        self.bot.log(error_msg, "❌")
                    else:
                        logger.warning(error_msg)
        
        # Update last stats for next iteration
        self.last_stats = {'hp_pct': stats['hp_pct'], 'ds_pct': stats['ds_pct']}

    def _get_default_stats(self) -> Dict[str, Any]:
        """Get default stats when memory reading is unavailable"""
        return {
            'hp': 1000,
            'ds': 500,
            'max_hp': 1000,
            'max_ds': 500,
            'hp_pct': 100.0,
            'ds_pct': 100.0,
            'connected': False
        }

    def get_healing_status(self) -> Dict[str, Any]:
        """
        Get comprehensive healing system status
        
        Returns:
            Dictionary with detailed healing status
        """
        current_time = time.time()
        
        status = {
            'enabled': getattr(self.bot.config, 'smart_healing', {}).get(),
            'healing_in_progress': self.healing_in_progress,
            'available_items': {'hp': [], 'ds': []},
            'cooldowns': {},
            'next_heal_available': {'hp': 0, 'ds': 0},
            'failed_heals': self.failed_heals.copy(),
            'total_heals_used': self.total_heals_used.copy(),
            'emergency_heals': self.emergency_heals,
            'health_trend': {},
            'config': {
                'combat_delay': self.config.combat_heal_delay,
                'normal_delay': self.config.normal_heal_delay,
                'item_cooldown': self.config.item_cooldown,
                'panic_threshold': self.config.panic_threshold,
                'overheal_protection': self.config.overheal_protection
            }
        }
        
        # Get available items
        for stat_type in ['hp', 'ds']:
            items = self.get_available_healing_items(stat_type)
            status['available_items'][stat_type] = [item.name for item in items]
            
            # Calculate next heal availability
            last_attempt = self.last_heal_attempt[stat_type]
            min_delay = self._get_min_heal_delay()
            time_remaining = max(0, min_delay - (current_time - last_attempt))
            status['next_heal_available'][stat_type] = time_remaining
            
            # Get health trend
            status['health_trend'][stat_type] = self.get_health_trend(stat_type)
        
        # Get item cooldowns
        for key, last_used in self.healing_cooldowns.items():
            remaining = max(0, self.config.item_cooldown - (current_time - last_used))
            if remaining > 0:
                status['cooldowns'][key] = remaining
        
        return status

    def reset_statistics(self) -> None:
        """Reset healing statistics"""
        self.failed_heals = {'hp': 0, 'ds': 0}
        self.total_heals_used = {'hp': 0, 'ds': 0}
        self.emergency_heals = 0
        self.health_history.clear()
        logger.info("Healing statistics reset")

    def cleanup(self) -> None:
        """Clean up healing system resources"""
        self.healing_in_progress = False
        self.health_history.clear()
        self.healing_cooldowns.clear()
        logger.info("Healing system cleanup completed")
