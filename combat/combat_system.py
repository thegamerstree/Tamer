"""
Advanced combat system with intelligent targeting and combo execution
"""

import time
import random
import threading
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from utils.logger import Logger
from config.constants import COMBAT_COMBOS, TIMING_RANGES

class CombatState(Enum):
    """Combat system states"""
    IDLE = "idle"
    SEEKING = "seeking"  
    ENGAGING = "engaging"
    RETREATING = "retreating"
    COOLDOWN = "cooldown"

@dataclass
class Target:
    """Target information"""
    entity_type: str
    x: int
    y: int
    distance: float
    confidence: float
    priority: int
    last_seen: float
    health_estimate: float = 100.0
    threat_level: int = 1
    
class TargetManager:
    """Manages target selection and tracking"""
    
    def __init__(self, combat_system):
        self.combat_system = combat_system
        self.logger = Logger()
        self.current_target = None
        self.target_history = []
        self.max_history = 20
        self.target_lock_duration = 3.0
        self.target_lost_timeout = 2.0
        
    def update_targets(self, detected_entities: List[Any]) -> Optional[Target]:
        """Update target list and select best target"""
        current_time = time.time()
        
        # Convert detected entities to targets
        available_targets = []
        for entity in detected_entities:
            target = Target(
                entity_type=entity.entity_type,
                x=entity.x,
                y=entity.y,
                distance=entity.distance_from_center,
                confidence=entity.confidence,
                priority=self._get_target_priority(entity.entity_type),
                last_seen=current_time
            )
            available_targets.append(target)
        
        # Apply target filters
        filtered_targets = self._filter_targets(available_targets)
        
        # Select best target
        best_target = self._select_best_target(filtered_targets)
        
        # Update current target
        if best_target:
            if (self.current_target is None or 
                self._should_switch_target(best_target)):
                self._switch_target(best_target)
        elif self.current_target:
            # Check if current target is lost
            if current_time - self.current_target.last_seen > self.target_lost_timeout:
                self.logger.target(f"Lost target: {self.current_target.entity_type}")
                self.current_target = None
        
        return self.current_target
    
    def _get_target_priority(self, entity_type: str) -> int:
        """Get priority for entity type (lower = higher priority)"""
        priority_map = {
            'boss_nameplate': 1,
            'red_hp_bar': 2,
            'enemy_nameplate': 3,
            'yellow_nameplate': 4,
            'friendly_nameplate': 10
        }
        return priority_map.get(entity_type, 5)
    
    def _filter_targets(self, targets: List[Target]) -> List[Target]:
        """Filter targets based on configuration"""
        config = self.combat_system.bot_engine.app.config_manager.combat
        
        # Filter by avoid list
        avoid_list = [name.strip().lower() for name in config.avoid_digimon.split(',') if name.strip()]
        if avoid_list:
            targets = [t for t in targets if not any(avoid in t.entity_type.lower() for avoid in avoid_list)]
        
        # Filter by distance (reasonable engagement range)
        max_distance = 400
        targets = [t for t in targets if t.distance <= max_distance]
        
        # Filter by confidence
        min_confidence = 0.4
        targets = [t for t in targets if t.confidence >= min_confidence]
        
        return targets
    
    def _select_best_target(self, targets: List[Target]) -> Optional[Target]:
        """Select the best target from available targets"""
        if not targets:
            return None
        
        # Score targets
        scored_targets = []
        for target in targets:
            score = self._calculate_target_score(target)
            scored_targets.append((score, target))
        
        # Sort by score (highest first)
        scored_targets.sort(reverse=True)
        
        return scored_targets[0][1] if scored_targets else None
    
    def _calculate_target_score(self, target: Target) -> float:
        """Calculate target selection score"""
        score = 0.0
        
        # Priority score (higher priority = higher score)
        priority_score = 100 - (target.priority * 10)
        score += priority_score
        
        # Distance score (closer = higher score)
        max_distance = 400
        distance_score = (max_distance - target.distance) / max_distance * 50
        score += distance_score
        
        # Confidence score
        confidence_score = target.confidence * 30
        score += confidence_score
        
        # Continuity bonus (prefer current target)
        if (self.current_target and 
            target.entity_type == self.current_target.entity_type and
            abs(target.x - self.current_target.x) < 50 and
            abs(target.y - self.current_target.y) < 50):
            score += 25
        
        return score
    
    def _should_switch_target(self, new_target: Target) -> bool:
        """Determine if we should switch to a new target"""
        if not self.current_target:
            return True
        
        current_time = time.time()
        
        # Don't switch if we just locked onto current target
        if current_time - self.current_target.last_seen < self.target_lock_duration:
            # Only switch for much higher priority targets
            if new_target.priority < self.current_target.priority - 1:
                return True
            return False
        
        # Switch if new target is significantly better
        current_score = self._calculate_target_score(self.current_target)
        new_score = self._calculate_target_score(new_target)
        
        return new_score > current_score * 1.2  # 20% better
    
    def _switch_target(self, new_target: Target):
        """Switch to a new target"""
        if self.current_target:
            self.target_history.append(self.current_target)
            if len(self.target_history) > self.max_history:
                self.target_history.pop(0)
        
        self.current_target = new_target
        self.logger.target(f"Targeting: {new_target.entity_type} at ({new_target.x}, {new_target.y})")

class ComboManager:
    """Manages combat combos and skill rotations"""
    
    def __init__(self, combat_system):
        self.combat_system = combat_system
        self.logger = Logger()
        self.available_combos = COMBAT_COMBOS.copy()
        self.combo_cooldowns = {}
        self.last_combo_time = 0
        self.combo_success_rate = {}
        
    def get_available_combo(self) -> Optional[Dict]:
        """Get an available combo to execute"""
        current_time = time.time()
        config = self.combat_system.bot_engine.app.config_manager.combat
        
        if not config.combo_enabled:
            return None
        
        # Check global combo cooldown
        if current_time - self.last_combo_time < 5.0:
            return None
        
        # Find available combos
        available = []
        for combo_name, combo_data in self.available_combos.items():
            # Check combo-specific cooldown
            last_used = self.combo_cooldowns.get(combo_name, 0)
            if current_time - last_used >= combo_data['cooldown']:
                # Check success rate
                success_rate = self.combo_success_rate.get(combo_name, combo_data['success_rate'])
                if random.random() < success_rate:
                    available.append((combo_name, combo_data))
        
        if not available:
            return None
        
        # Select combo based on situation
        return self._select_situational_combo(available)
    
    def _select_situational_combo(self, available_combos: List[Tuple[str, Dict]]) -> Optional[Dict]:
        """Select best combo based on current situation"""
        if not available_combos:
            return None
        
        # Get current game state
        game_state = self.combat_system.bot_engine.get_current_game_state()
        player_hp = game_state.player_stats.get('hp_pct', 100)
        
        # Situational scoring
        scored_combos = []
        for combo_name, combo_data in available_combos:
            score = combo_data['success_rate'] * 100
            
            # Prefer aggressive combos when healthy
            if player_hp > 70:
                if 'power' in combo_name.lower() or 'ultimate' in combo_name.lower():
                    score += 30
            
            # Prefer defensive combos when low health
            elif player_hp < 40:
                if 'defensive' in combo_name.lower():
                    score += 40
                else:
                    score -= 20
            
            # Quick combos when in danger
            if player_hp < 25:
                if 'quick' in combo_name.lower():
                    score += 50
            
            scored_combos.append((score, combo_name, combo_data))
        
        # Select highest scored combo
        scored_combos.sort(reverse=True)
        _, combo_name, combo_data = scored_combos[0]
        
        return {'name': combo_name, **combo_data}
    
    def execute_combo(self, combo: Dict) -> bool:
        """Execute a combat combo"""
        current_time = time.time()
        combo_name = combo['name']
        
        try:
            self.logger.combat(f"Executing combo: {combo_name}")
            
            # Record combo start
            self.last_combo_time = current_time
            self.combo_cooldowns[combo_name] = current_time
            
            # Execute combo sequence
            success = self._execute_combo_sequence(combo['sequence'])
            
            # Update success rate
            if combo_name not in self.combo_success_rate:
                self.combo_success_rate[combo_name] = combo['success_rate']
            
            if success:
                # Increase success rate slightly
                self.combo_success_rate[combo_name] = min(1.0, self.combo_success_rate[combo_name] + 0.02)
                self.logger.combat(f"Combo {combo_name} executed successfully")
            else:
                # Decrease success rate
                self.combo_success_rate[combo_name] = max(0.1, self.combo_success_rate[combo_name] - 0.05)
                self.logger.error(f"Combo {combo_name} failed")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Combo execution error: {e}")
            return False
    
    def _execute_combo_sequence(self, sequence: List[Dict]) -> bool:
        """Execute the individual steps of a combo"""
        input_controller = self.combat_system.bot_engine.input_controller
        
        try:
            for i, step in enumerate(sequence):
                step_type = step['type']
                delay = step.get('delay', 0.2)
                
                # Add human-like variance to delays
                actual_delay = delay * random.uniform(0.8, 1.2)
                
                if step_type == 'tab':
                    input_controller.tap('TAB')
                elif step_type == 'attack':
                    attack_key = self.combat_system.bot_engine.app.config_manager.combat.attack_key
                    input_controller.tap(attack_key)
                elif step_type == 'special':
                    special_key = step.get('key', 'F1')
                    input_controller.tap(special_key)
                elif step_type == 'movement':
                    move_key = step.get('key', 'W')
                    move_duration = step.get('duration', 0.5)
                    input_controller.hold(move_key, move_duration)
                
                # Wait between steps (except for last step)
                if i < len(sequence) - 1:
                    time.sleep(actual_delay)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Combo sequence error: {e}")
            return False

class CombatSystem:
    """Main combat system coordinating all combat activities"""
    
    def __init__(self, bot_engine):
        self.bot_engine = bot_engine
        self.logger = Logger()
        
        # Combat state
        self.state = CombatState.IDLE
        self.last_state_change = time.time()
        self.state_history = []
        
        # Subsystems
        self.target_manager = TargetManager(self)
        self.combo_manager = ComboManager(self)
        
        # Timing and cooldowns
        self.last_attack_time = 0
        self.last_pickup_time = 0
        self.last_target_search = 0
        self.attack_sequence_count = 0
        
        # Performance tracking
        self.combat_stats = {
            'attacks': 0,
            'combos': 0,
            'pickups': 0,
            'targets_engaged': 0,
            'session_start': time.time()
        }
        
        # Configuration cache
        self._config_cache = None
        self._config_cache_time = 0
        
        # Thread safety
        self.lock = threading.Lock()
        
    def initialize(self) -> bool:
        """Initialize the combat system"""
        try:
            self.logger.system("Initializing combat system")
            return True
        except Exception as e:
            self.logger.error(f"Combat system initialization failed: {e}")
            return False
    
    def update(self, current_time: float, game_state: Any):
        """Main combat system update"""
        with self.lock:
            try:
                # Update configuration cache
                self._update_config_cache()
                
                # Update target manager
                current_target = self.target_manager.update_targets(game_state.detected_entities)
                
                # State machine
                self._update_combat_state(current_time, game_state, current_target)
                
                # Execute actions based on state
                self._execute_combat_actions(current_time, game_state, current_target)
                
            except Exception as e:
                self.logger.error(f"Combat system update error: {e}")
    
    def _update_config_cache(self):
        """Update configuration cache"""
        current_time = time.time()
        if current_time - self._config_cache_time > 5.0:  # Cache for 5 seconds
            self._config_cache = self.bot_engine.app.config_manager.combat
            self._config_cache_time = current_time
    
    def _update_combat_state(self, current_time: float, game_state: Any, current_target: Optional[Any]):
        """Update combat state machine"""
        old_state = self.state
        
        # State transitions
        if self.state == CombatState.IDLE:
            if current_target:
                self.state = CombatState.SEEKING
        
        elif self.state == CombatState.SEEKING:
            if not current_target:
                self.state = CombatState.IDLE
            elif current_target.distance < 100:  # Close enough to engage
                self.state = CombatState.ENGAGING
        
        elif self.state == CombatState.ENGAGING:
            if not current_target:
                self.state = CombatState.COOLDOWN
            elif current_target.distance > 200:  # Target moved away
                self.state = CombatState.SEEKING
            elif self._should_retreat(game_state):
                self.state = CombatState.RETREATING
        
        elif self.state == CombatState.RETREATING:
            if self._is_safe(game_state):
                self.state = CombatState.COOLDOWN
        
        elif self.state == CombatState.COOLDOWN:
            if current_time - self.last_state_change > 2.0:  # 2 second cooldown
                self.state = CombatState.IDLE
        
        # Log state changes
        if old_state != self.state:
            self.last_state_change = current_time
            self.state_history.append((old_state, self.state, current_time))
            if len(self.state_history) > 20:
                self.state_history.pop(0)
            
            self.logger.combat(f"State: {old_state.value} → {self.state.value}")
    
    def _should_retreat(self, game_state: Any) -> bool:
        """Determine if we should retreat"""
        if not self._config_cache.emergency_retreat:
            return False
        
        player_hp = game_state.player_stats.get('hp_pct', 100)
        return player_hp <= self._config_cache.retreat_hp_threshold
    
    def _is_safe(self, game_state: Any) -> bool:
        """Determine if we're in a safe state"""
        player_hp = game_state.player_stats.get('hp_pct', 100)
        return player_hp > self._config_cache.retreat_hp_threshold + 10  # 10% buffer
    
    def _execute_combat_actions(self, current_time: float, game_state: Any, current_target: Optional[Any]):
        """Execute actions based on current state"""
        if self.state == CombatState.SEEKING:
            self._handle_seeking(current_time, current_target)
        
        elif self.state == CombatState.ENGAGING:
            self._handle_engaging(current_time, game_state, current_target)
        
        elif self.state == CombatState.RETREATING:
            self._handle_retreating(current_time)
    
    def _handle_seeking(self, current_time: float, target: Optional[Any]):
        """Handle seeking state - moving toward target"""
        if not target:
            return
        
        # Calculate movement direction
        detector = self.bot_engine.detector
        if detector and detector.game_window_region:
            directions = detector.get_movement_direction(target.x, target.y)
            
            if directions:
                # Move toward target
                movement_key = directions[0]  # Use primary direction
                move_duration = random.uniform(0.3, 0.8)
                
                self.bot_engine.input_controller.hold(movement_key, move_duration)
                self.logger.move(f"Moving {movement_key} toward {target.entity_type}")
    
    def _handle_engaging(self, current_time: float, game_state: Any, target: Optional[Any]):
        """Handle engaging state - active combat"""
        if not target:
            return
        
        # Check attack cooldown
        attack_cooldown = self._config_cache.attack_cooldown
        if current_time - self.last_attack_time < attack_cooldown:
            return
        
        # Decide between normal attack and combo
        should_combo = (self._config_cache.combo_enabled and 
                       random.random() < self._config_cache.combo_chance and
                       self.attack_sequence_count > 2)
        
        if should_combo:
            combo = self.combo_manager.get_available_combo()
            if combo:
                success = self.combo_manager.execute_combo(combo)
                if success:
                    self.combat_stats['combos'] += 1
                    self.attack_sequence_count = 0
                    self.last_attack_time = current_time
                    return
        
        # Execute normal attack sequence
        self._execute_attack_sequence(current_time)
    
    def _execute_attack_sequence(self, current_time: float):
        """Execute normal attack sequence"""
        input_controller = self.bot_engine.input_controller
        
        try:
            # Target selection
            input_controller.tap('TAB')
            time.sleep(random.uniform(0.15, 0.3))
            
            # Primary attack
            attack_key = self._config_cache.attack_key
            input_controller.tap(attack_key)
            
            # Random skill usage
            if random.random() < 0.3:  # 30% chance
                self._use_random_skill()
            
            # Auto pickup
            if self._config_cache.auto_pickup:
                time.sleep(random.uniform(0.2, 0.5))
                pickup_key = self._config_cache.pickup_key
                input_controller.tap(pickup_key)
                self.combat_stats['pickups'] += 1
                self.last_pickup_time = current_time
            
            # Update stats
            self.combat_stats['attacks'] += 1
            self.attack_sequence_count += 1
            self.last_attack_time = current_time
            
            self.logger.combat(f"Attack sequence #{self.attack_sequence_count}")
            
        except Exception as e:
            self.logger.error(f"Attack sequence error: {e}")
    
    def _use_random_skill(self):
        """Use a random available skill"""
        try:
            skills = self.bot_engine.app.config_manager.skills
            available_skills = [key for key, config in skills.items() if config.enabled]
            
            if available_skills:
                skill_key = random.choice(available_skills)
                self.bot_engine.input_controller.tap(skill_key)
                self.logger.skill(f"Used skill {skill_key}")
                
        except Exception as e:
            self.logger.error(f"Skill usage error: {e}")
    
    def _handle_retreating(self, current_time: float):
        """Handle retreating state - moving away from danger"""
        # Move backward
        retreat_duration = random.uniform(1.0, 2.0)
        self.bot_engine.input_controller.hold('S', retreat_duration)
        self.logger.move("Retreating from combat")
    
    def get_status(self) -> Dict[str, Any]:
        """Get combat system status"""
        current_time = time.time()
        uptime = current_time - self.combat_stats['session_start']
        
        return {
            'state': self.state.value,
            'current_target': self.target_manager.current_target.entity_type if self.target_manager.current_target else None,
            'attacks': self.combat_stats['attacks'],
            'combos': self.combat_stats['combos'],
            'pickups': self.combat_stats['pickups'],
            'targets_engaged': self.combat_stats['targets_engaged'],
            'uptime': uptime,
            'attacks_per_minute': (self.combat_stats['attacks'] / max(1, uptime)) * 60,
            'last_attack': current_time - self.last_attack_time,
            'attack_sequence_count': self.attack_sequence_count
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get system health status"""
        return {
            'status': 'healthy',
            'errors': 0,
            'last_update': time.time()
        }
    
    def pause(self):
        """Pause combat system"""
        self.logger.system("Combat system paused")
    
    def resume(self):
        """Resume combat system"""
        self.logger.system("Combat system resumed")
    
    def stop(self):
        """Stop combat system"""
        self.logger.system("Combat system stopped")
    
    def emergency_stop(self):
        """Emergency stop all combat actions"""
        self.bot_engine.input_controller.stop_all_inputs()
        self.state = CombatState.IDLE
        self.logger.system("Combat emergency stop")