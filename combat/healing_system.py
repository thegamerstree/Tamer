"""
Advanced healing system with predictive healing and smart item management
"""

import time
import random
import threading
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from utils.logger import Logger

class HealingUrgency(Enum):
    """Healing urgency levels"""
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    EMERGENCY = 4

@dataclass
class HealingItem:
    """Healing item configuration"""
    name: str
    key: str
    threshold: int
    item_type: str  # 'hp' or 'ds'
    priority: int
    cooldown: float
    last_used: float = 0
    success_count: int = 0
    failure_count: int = 0
    
    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 1.0

@dataclass
class HealthTrend:
    """Health trend analysis"""
    hp_trend: float  # HP change per second
    ds_trend: float  # DS change per second
    prediction_accuracy: float
    last_update: float

class PredictiveAnalyzer:
    """Analyzes health trends to predict healing needs"""
    
    def __init__(self):
        self.health_history = []
        self.max_history = 50
        self.trend_window = 10  # Analyze last 10 data points
        self.last_prediction = None
        
    def update(self, hp_pct: float, ds_pct: float) -> HealthTrend:
        """Update health history and calculate trends"""
        current_time = time.time()
        
        # Add current data point
        self.health_history.append({
            'time': current_time,
            'hp_pct': hp_pct,
            'ds_pct': ds_pct
        })
        
        # Maintain history size
        if len(self.health_history) > self.max_history:
            self.health_history.pop(0)
        
        # Calculate trends
        hp_trend, ds_trend = self._calculate_trends()
        
        # Calculate prediction accuracy
        accuracy = self._calculate_prediction_accuracy()
        
        trend = HealthTrend(
            hp_trend=hp_trend,
            ds_trend=ds_trend,
            prediction_accuracy=accuracy,
            last_update=current_time
        )
        
        self.last_prediction = trend
        return trend
    
    def _calculate_trends(self) -> Tuple[float, float]:
        """Calculate HP and DS trends (change per second)"""
        if len(self.health_history) < 2:
            return 0.0, 0.0
        
        # Use recent data points for trend analysis
        recent_data = self.health_history[-self.trend_window:]
        if len(recent_data) < 2:
            recent_data = self.health_history
        
        # Calculate linear regression for trends
        hp_trend = self._linear_trend([d['hp_pct'] for d in recent_data],
                                     [d['time'] for d in recent_data])
        ds_trend = self._linear_trend([d['ds_pct'] for d in recent_data],
                                     [d['time'] for d in recent_data])
        
        return hp_trend, ds_trend
    
    def _linear_trend(self, y_values: List[float], x_values: List[float]) -> float:
        """Calculate linear trend (slope)"""
        if len(y_values) < 2:
            return 0.0
        
        n = len(y_values)
        x_mean = sum(x_values) / n
        y_mean = sum(y_values) / n
        
        numerator = sum((x_values[i] - x_mean) * (y_values[i] - y_mean) for i in range(n))
        denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))
        
        return numerator / denominator if denominator != 0 else 0.0
    
    def _calculate_prediction_accuracy(self) -> float:
        """Calculate how accurate our predictions have been"""
        # Simplified accuracy calculation
        # In a real implementation, this would track prediction vs actual outcomes
        if len(self.health_history) < 5:
            return 0.5  # Default accuracy
        
        # For now, return a value based on trend stability
        recent_hp = [d['hp_pct'] for d in self.health_history[-5:]]
        hp_variance = self._calculate_variance(recent_hp)
        
        # Lower variance = higher accuracy
        accuracy = max(0.1, 1.0 - (hp_variance / 100))
        return min(0.9, accuracy)
    
    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of values"""
        if not values:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance
    
    def predict_health_in_seconds(self, seconds: float) -> Tuple[float, float]:
        """Predict HP and DS percentages after given seconds"""
        if not self.health_history or not self.last_prediction:
            return 100.0, 100.0
        
        current_data = self.health_history[-1]
        predicted_hp = current_data['hp_pct'] + (self.last_prediction.hp_trend * seconds)
        predicted_ds = current_data['ds_pct'] + (self.last_prediction.ds_trend * seconds)
        
        # Clamp values
        predicted_hp = max(0, min(100, predicted_hp))
        predicted_ds = max(0, min(100, predicted_ds))
        
        return predicted_hp, predicted_ds

class SmartHealingManager:
    """Manages intelligent healing decisions"""
    
    def __init__(self, healing_system):
        self.healing_system = healing_system
        self.logger = Logger()
        self.predictive_analyzer = PredictiveAnalyzer()
        
        # Healing configuration
        self.base_config = {
            'emergency_threshold': 15,
            'panic_threshold': 25,
            'comfort_threshold': 60,
            'overheal_protection': 5,
            'combat_delay_multiplier': 1.5,
            'prediction_window': 3.0  # Predict 3 seconds ahead
        }
        
        # State tracking
        self.last_healing_decision = {}
        self.healing_efficiency = {}
        
    def analyze_healing_need(self, hp_pct: float, ds_pct: float, 
                           in_combat: bool) -> Tuple[HealingUrgency, HealingUrgency]:
        """Analyze healing needs for HP and DS"""
        
        # Update predictive analysis
        trend = self.predictive_analyzer.update(hp_pct, ds_pct)
        
        # Predict future health
        prediction_time = self.base_config['prediction_window']
        if in_combat:
            prediction_time *= 1.5  # Look further ahead in combat
        
        predicted_hp, predicted_ds = self.predictive_analyzer.predict_health_in_seconds(prediction_time)
        
        # Analyze HP urgency
        hp_urgency = self._calculate_urgency(hp_pct, predicted_hp, 'hp', trend.hp_trend, in_combat)
        
        # Analyze DS urgency
        ds_urgency = self._calculate_urgency(ds_pct, predicted_ds, 'ds', trend.ds_trend, in_combat)
        
        return hp_urgency, ds_urgency
    
    def _calculate_urgency(self, current_pct: float, predicted_pct: float, 
                          stat_type: str, trend: float, in_combat: bool) -> HealingUrgency:
        """Calculate healing urgency for a specific stat"""
        
        # Emergency thresholds
        emergency_threshold = self.base_config['emergency_threshold']
        panic_threshold = self.base_config['panic_threshold']
        comfort_threshold = self.base_config['comfort_threshold']
        
        # Adjust thresholds for DS (usually lower priority)
        if stat_type == 'ds':
            emergency_threshold = max(10, emergency_threshold - 5)
            panic_threshold = max(15, panic_threshold - 10)
            comfort_threshold = max(40, comfort_threshold - 20)
        
        # Check current state
        if current_pct <= emergency_threshold:
            return HealingUrgency.EMERGENCY
        
        # Check predicted state (preventive healing)
        if predicted_pct <= emergency_threshold:
            return HealingUrgency.HIGH
        
        if current_pct <= panic_threshold:
            return HealingUrgency.HIGH
        
        if predicted_pct <= panic_threshold:
            return HealingUrgency.MEDIUM
        
        # Check if rapidly declining
        if trend < -5.0 and in_combat:  # Losing more than 5% per second
            if current_pct <= comfort_threshold:
                return HealingUrgency.MEDIUM
            else:
                return HealingUrgency.LOW
        
        # Standard threshold checking
        if current_pct <= comfort_threshold:
            return HealingUrgency.LOW
        
        return HealingUrgency.NONE
    
    def select_optimal_healing_item(self, urgency: HealingUrgency, 
                                  stat_type: str, current_pct: float) -> Optional[HealingItem]:
        """Select the optimal healing item based on urgency and efficiency"""
        
        available_items = self._get_available_items(stat_type)
        if not available_items:
            return None
        
        # Filter by urgency and current health
        suitable_items = []
        for item in available_items:
            # Check if item threshold is appropriate
            if urgency == HealingUrgency.EMERGENCY:
                # Use any available item in emergency
                suitable_items.append(item)
            elif urgency == HealingUrgency.HIGH:
                # Use medium/high priority items
                if item.priority <= 2 or current_pct <= item.threshold + 10:
                    suitable_items.append(item)
            elif urgency in [HealingUrgency.MEDIUM, HealingUrgency.LOW]:
                # Use appropriate threshold items
                if current_pct <= item.threshold + self.base_config['overheal_protection']:
                    suitable_items.append(item)
        
        if not suitable_items:
            return None
        
        # Score items based on efficiency and situation
        scored_items = []
        for item in suitable_items:
            score = self._calculate_item_score(item, urgency, current_pct)
            scored_items.append((score, item))
        
        # Select highest scored item
        scored_items.sort(reverse=True)
        return scored_items[0][1]
    
    def _get_available_items(self, stat_type: str) -> List[HealingItem]:
        """Get available healing items for stat type"""
        current_time = time.time()
        items = []
        
        for name, item_config in self.healing_system.bot_engine.app.config_manager.healing_items.items():
            if not item_config.enabled:
                continue
            
            # Check if item is for correct stat type
            item_stat_type = 'hp' if 'recovery' in name.lower() else 'ds'
            if item_stat_type != stat_type:
                continue
            
            # Create HealingItem object
            item = HealingItem(
                name=name,
                key=item_config.key,
                threshold=item_config.threshold,
                item_type=item_stat_type,
                priority=item_config.priority,
                cooldown=item_config.cooldown,
                last_used=self.last_healing_decision.get(name, 0)
            )
            
            # Check cooldown
            if current_time - item.last_used >= item.cooldown:
                items.append(item)
        
        return items
    
    def _calculate_item_score(self, item: HealingItem, urgency: HealingUrgency, 
                            current_pct: float) -> float:
        """Calculate item selection score"""
        score = 0.0
        
        # Base score from success rate
        score += item.success_rate * 100
        
        # Priority bonus (lower priority number = higher score)
        priority_score = 50 - (item.priority * 10)
        score += priority_score
        
        # Threshold matching bonus
        threshold_diff = abs(item.threshold - current_pct)
        threshold_score = max(0, 30 - threshold_diff)
        score += threshold_score
        
        # Urgency multipliers
        if urgency == HealingUrgency.EMERGENCY:
            score *= 2.0
        elif urgency == HealingUrgency.HIGH:
            score *= 1.5
        
        # Avoid overheal penalty
        overheal_amount = max(0, item.threshold - current_pct - 10)
        score -= overheal_amount
        
        return score

class HealingSystem:
    """Main healing system coordinating all healing activities"""
    
    def __init__(self, bot_engine):
        self.bot_engine = bot_engine
        self.logger = Logger()
        
        # Healing manager
        self.smart_manager = SmartHealingManager(self)
        
        # State tracking
        self.last_healing_attempt = {'hp': 0, 'ds': 0}
        self.healing_in_progress = False
        self.healing_stats = {
            'total_heals': 0,
            'successful_heals': 0,
            'emergency_heals': 0,
            'preventive_heals': 0,
            'session_start': time.time()
        }
        
        # Configuration cache
        self._config_cache = None
        self._config_cache_time = 0
        
        # Thread safety
        self.lock = threading.Lock()
        
    def initialize(self) -> bool:
        """Initialize the healing system"""
        try:
            self.logger.system("Initializing healing system")
            return True
        except Exception as e:
            self.logger.error(f"Healing system initialization failed: {e}")
            return False
    
    def update(self, current_time: float, game_state: Any):
        """Main healing system update"""
        with self.lock:
            try:
                # Skip if healing disabled
                if not self._get_config().smart_healing:
                    return
                
                # Skip if currently healing
                if self.healing_in_progress:
                    return
                
                # Get current health stats
                hp_pct = game_state.player_stats.get('hp_pct', 100)
                ds_pct = game_state.player_stats.get('ds_pct', 100)
                in_combat = game_state.in_combat
                
                # Analyze healing needs
                hp_urgency, ds_urgency = self.smart_manager.analyze_healing_need(
                    hp_pct, ds_pct, in_combat
                )
                
                # Determine healing priorities
                healing_actions = self._prioritize_healing_actions(
                    hp_urgency, ds_urgency, hp_pct, ds_pct, current_time, in_combat
                )
                
                # Execute highest priority healing
                if healing_actions:
                    self._execute_healing_action(healing_actions[0], current_time)
                
            except Exception as e:
                self.logger.error(f"Healing system update error: {e}")
    
    def _get_config(self):
        """Get cached configuration"""
        current_time = time.time()
        if current_time - self._config_cache_time > 5.0:
            self._config_cache = self.bot_engine.app.config_manager.healing
            self._config_cache_time = current_time
        return self._config_cache
    
    def _prioritize_healing_actions(self, hp_urgency: HealingUrgency, ds_urgency: HealingUrgency,
                                  hp_pct: float, ds_pct: float, current_time: float,
                                  in_combat: bool) -> List[Dict]:
        """Prioritize healing actions based on urgency and timing"""
        actions = []
        
        # Check HP healing
        if hp_urgency != HealingUrgency.NONE:
            if self._should_heal_now('hp', hp_urgency, current_time, in_combat):
                hp_item = self.smart_manager.select_optimal_healing_item(
                    hp_urgency, 'hp', hp_pct
                )
                if hp_item:
                    priority = self._get_action_priority(hp_urgency)
                    actions.append({
                        'type': 'hp',
                        'item': hp_item,
                        'urgency': hp_urgency,
                        'priority': priority
                    })
        
        # Check DS healing
        if ds_urgency != HealingUrgency.NONE:
            if self._should_heal_now('ds', ds_urgency, current_time, in_combat):
                ds_item = self.smart_manager.select_optimal_healing_item(
                    ds_urgency, 'ds', ds_pct
                )
                if ds_item:
                    priority = self._get_action_priority(ds_urgency)
                    actions.append({
                        'type': 'ds',
                        'item': ds_item,
                        'urgency': ds_urgency,
                        'priority': priority
                    })
        
        # Sort by priority (higher priority first)
        actions.sort(key=lambda x: x['priority'], reverse=True)
        
        return actions
    
    def _should_heal_now(self, stat_type: str, urgency: HealingUrgency, 
                        current_time: float, in_combat: bool) -> bool:
        """Determine if we should heal now based on timing constraints"""
        config = self._get_config()
        
        # Check urgency override
        if urgency == HealingUrgency.EMERGENCY:
            return True
        
        # Check timing constraints
        last_heal = self.last_healing_attempt.get(stat_type, 0)
        base_delay = config.normal_heal_delay
        
        if in_combat:
            base_delay = config.combat_heal_delay
        
        # Adjust delay based on urgency
        if urgency == HealingUrgency.HIGH:
            base_delay *= 0.7
        elif urgency == HealingUrgency.MEDIUM:
            base_delay *= 1.0
        elif urgency == HealingUrgency.LOW:
            base_delay *= 1.3
        
        return current_time - last_heal >= base_delay
    
    def _get_action_priority(self, urgency: HealingUrgency) -> int:
        """Get action priority based on urgency"""
        priority_map = {
            HealingUrgency.EMERGENCY: 100,
            HealingUrgency.HIGH: 80,
            HealingUrgency.MEDIUM: 60,
            HealingUrgency.LOW: 40,
            HealingUrgency.NONE: 0
        }
        return priority_map.get(urgency, 0)
    
    def _execute_healing_action(self, action: Dict, current_time: float):
        """Execute a healing action"""
        try:
            self.healing_in_progress = True
            
            item = action['item']
            stat_type = action['type']
            urgency = action['urgency']
            
            self.logger.heal(f"Using {item.name} for {stat_type.upper()} "
                           f"(Urgency: {urgency.name})")
            
            # Stop any current movement
            self.bot_engine.input_controller.stop_all_inputs()
            
            # Add pre-healing delay for realism
            if urgency != HealingUrgency.EMERGENCY:
                pre_delay = random.uniform(0.1, 0.3)
                time.sleep(pre_delay)
            
            # Execute healing
            success = self._use_healing_item(item)
            
            # Update statistics
            self._update_healing_stats(item, success, urgency)
            
            # Record timing
            self.last_healing_attempt[stat_type] = current_time
            self.smart_manager.last_healing_decision[item.name] = current_time
            
            if success:
                self.logger.heal(f"Successfully used {item.name}")
            else:
                self.logger.error(f"Failed to use {item.name}")
            
        except Exception as e:
            self.logger.error(f"Healing execution error: {e}")
        finally:
            self.healing_in_progress = False
    
    def _use_healing_item(self, item: HealingItem) -> bool:
        """Use a healing item"""
        try:
            # Validate key
            if not item.key or item.key not in self.bot_engine.input_controller.VK_CODES:
                self.logger.error(f"Invalid healing key: {item.key}")
                return False
            
            # Press the healing key
            success = self.bot_engine.input_controller.tap(item.key)
            
            # Add post-healing delay
            post_delay = random.uniform(0.2, 0.5)
            time.sleep(post_delay)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error using healing item {item.name}: {e}")
            return False
    
    def _update_healing_stats(self, item: HealingItem, success: bool, urgency: HealingUrgency):
        """Update healing statistics"""
        self.healing_stats['total_heals'] += 1
        
        if success:
            self.healing_stats['successful_heals'] += 1
            item.success_count += 1
        else:
            item.failure_count += 1
        
        if urgency == HealingUrgency.EMERGENCY:
            self.healing_stats['emergency_heals'] += 1
        elif urgency in [HealingUrgency.HIGH, HealingUrgency.MEDIUM]:
            self.healing_stats['preventive_heals'] += 1
        
        # Update efficiency tracking
        item_name = item.name
        if item_name not in self.smart_manager.healing_efficiency:
            self.smart_manager.healing_efficiency[item_name] = {
                'uses': 0,
                'successes': 0,
                'avg_response_time': 0.0
            }
        
        efficiency = self.smart_manager.healing_efficiency[item_name]
        efficiency['uses'] += 1
        if success:
            efficiency['successes'] += 1
    
    def get_healing_status(self) -> Dict[str, Any]:
        """Get current healing system status"""
        current_time = time.time()
        
        # Get available items by type
        hp_items = self.smart_manager._get_available_items('hp')
        ds_items = self.smart_manager._get_available_items('ds')
        
        # Get cooldown status
        cooldowns = {}
        for stat_type in ['hp', 'ds']:
            last_heal = self.last_healing_attempt.get(stat_type, 0)
            config = self._get_config()
            base_delay = config.normal_heal_delay
            remaining = max(0, base_delay - (current_time - last_heal))
            cooldowns[stat_type] = remaining
        
        # Get prediction info
        trend = self.smart_manager.predictive_analyzer.last_prediction
        
        return {
            'healing_enabled': self._get_config().smart_healing,
            'healing_in_progress': self.healing_in_progress,
            'available_hp_items': len(hp_items),
            'available_ds_items': len(ds_items),
            'cooldowns': cooldowns,
            'total_heals': self.healing_stats['total_heals'],
            'success_rate': (self.healing_stats['successful_heals'] / 
                           max(1, self.healing_stats['total_heals'])),
            'emergency_heals': self.healing_stats['emergency_heals'],
            'preventive_heals': self.healing_stats['preventive_heals'],
            'prediction_accuracy': trend.prediction_accuracy if trend else 0.0,
            'hp_trend': trend.hp_trend if trend else 0.0,
            'ds_trend': trend.ds_trend if trend else 0.0
        }
    
    def get_detailed_item_status(self) -> Dict[str, Any]:
        """Get detailed status of all healing items"""
        items_status = {}
        current_time = time.time()
        
        for name, item_config in self.bot_engine.app.config_manager.healing_items.items():
            last_used = self.smart_manager.last_healing_decision.get(name, 0)
            cooldown_remaining = max(0, item_config.cooldown - (current_time - last_used))
            
            efficiency = self.smart_manager.healing_efficiency.get(name, {
                'uses': 0, 'successes': 0, 'avg_response_time': 0.0
            })
            
            success_rate = (efficiency['successes'] / max(1, efficiency['uses'])) * 100
            
            items_status[name] = {
                'enabled': item_config.enabled,
                'key': item_config.key,
                'threshold': item_config.threshold,
                'type': item_config.item_type,
                'priority': item_config.priority,
                'cooldown_remaining': cooldown_remaining,
                'total_uses': efficiency['uses'],
                'success_rate': success_rate,
                'available': cooldown_remaining == 0 and item_config.enabled
            }
        
        return items_status
    
    def force_heal(self, stat_type: str) -> bool:
        """Force immediate healing for testing purposes"""
        try:
            self.logger.heal(f"Force healing {stat_type.upper()}")
            
            # Get best available item
            current_pct = 50  # Assume 50% for testing
            urgency = HealingUrgency.HIGH
            
            item = self.smart_manager.select_optimal_healing_item(
                urgency, stat_type, current_pct
            )
            
            if not item:
                self.logger.error(f"No {stat_type} healing items available")
                return False
            
            # Execute healing
            action = {
                'type': stat_type,
                'item': item,
                'urgency': urgency,
                'priority': 100
            }
            
            self._execute_healing_action(action, time.time())
            return True
            
        except Exception as e:
            self.logger.error(f"Force heal error: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get healing system status"""
        return self.get_healing_status()
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get system health status"""
        return {
            'status': 'healthy',
            'errors': 0,
            'last_update': time.time()
        }
    
    def pause(self):
        """Pause healing system"""
        self.logger.system("Healing system paused")
    
    def resume(self):
        """Resume healing system"""
        self.logger.system("Healing system resumed")
    
    def stop(self):
        """Stop healing system"""
        self.logger.system("Healing system stopped")
    
    def emergency_stop(self):
        """Emergency stop healing system"""
        self.healing_in_progress = False
        self.logger.system("Healing emergency stop")