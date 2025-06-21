"""
Centralized configuration management with validation and persistence
"""

import json
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict, field
from pathlib import Path
import threading

@dataclass
class CombatConfig:
    """Combat system configuration"""
    attack_key: str = "1"
    pickup_key: str = "4"
    attack_cooldown: float = 2.5
    auto_pickup: bool = True
    target_priority: str = "boss_nameplate,red_hp_bar,enemy_nameplate,yellow_nameplate"
    avoid_digimon: str = ""
    emergency_retreat: bool = True
    retreat_hp_threshold: int = 15
    combo_enabled: bool = True
    combo_chance: float = 0.2
    aggressive_mode: bool = False
    defensive_mode: bool = False
    auto_target: bool = True
    target_switching: bool = True
    
@dataclass
class HealingConfig:
    """Healing system configuration"""
    smart_healing: bool = True
    emergency_healing: bool = True
    combat_heal_delay: float = 2.5
    normal_heal_delay: float = 1.5
    panic_threshold: int = 15
    overheal_protection: int = 5
    prediction_enabled: bool = True
    adaptive_thresholds: bool = True
    health_monitoring: bool = True
    auto_potion_buy: bool = False
    
@dataclass
class HealingItem:
    """Individual healing item configuration"""
    key: str = "1"
    enabled: bool = True
    threshold: int = 70
    item_type: str = "hp"  # hp or ds
    priority: int = 1
    cooldown: float = 2.0
    
@dataclass
class SkillConfig:
    """Skill/Special attack configuration"""
    enabled: bool = True
    cooldown: float = 2.0
    usage_chance: float = 70.0
    combat_only: bool = True
    emergency_use: bool = False
    combo_starter: bool = False

@dataclass
class MovementConfig:
    """Movement and pathfinding configuration"""
    auto_move: bool = True
    movement_interval: float = 8.0
    exploration_pattern: str = "Random"
    smart_positioning: bool = True
    avoid_obstacles: bool = True
    return_to_spawn: bool = False
    patrol_radius: int = 100
    movement_speed: str = "Normal"  # Slow, Normal, Fast
    stuck_detection: bool = True
    pathfinding_enabled: bool = True
    
@dataclass
class AntiDetectionConfig:
    """Anti-detection system configuration"""
    human_timing: bool = True
    pattern_randomization: bool = True
    break_system: bool = True
    adaptive_delays: bool = True
    stealth_mode: bool = False
    detection_sensitivity: float = 0.7
    behavioral_variance: float = 0.3
    session_breaks: bool = True
    micro_breaks: bool = True
    fatigue_simulation: bool = True
    attention_simulation: bool = True
    
@dataclass
class MemoryConfig:
    """Memory reading configuration"""
    use_memory: bool = True
    process_name: str = "GDMO.exe"
    base_offset: str = "0x0072FF80"
    auto_reconnect: bool = True
    validation_enabled: bool = True
    read_interval: float = 0.1
    connection_timeout: int = 5
    retry_attempts: int = 3
    
@dataclass
class DetectionConfig:
    """Computer vision detection configuration"""
    enabled: bool = True
    detection_interval: float = 0.1
    confidence_threshold: float = 0.6
    max_detection_distance: int = 500
    roi_optimization: bool = True
    multi_threading: bool = True
    color_profiles: Dict[str, Any] = field(default_factory=dict)
    
@dataclass
class GUIConfig:
    """GUI configuration"""
    theme: str = "Dark"
    window_size: str = "950x850"
    always_on_top: bool = False
    minimize_to_tray: bool = True
    auto_save_interval: int = 300  # seconds
    log_max_lines: int = 1000
    real_time_updates: bool = True
    
@dataclass
class SecurityConfig:
    """Security and privacy configuration"""
    encrypt_settings: bool = False
    secure_memory: bool = True
    anti_debugging: bool = False
    process_hiding: bool = False
    network_isolation: bool = True
    log_encryption: bool = False

class ConfigValidator:
    """Validates configuration values"""
    
    @staticmethod
    def validate_key(key: str) -> bool:
        """Validate keyboard key"""
        valid_keys = [str(i) for i in range(1, 10)] + [f"F{i}" for i in range(1, 13)]
        valid_keys.extend(['W', 'A', 'S', 'D', 'TAB', 'SPACE'])
        return key.upper() in valid_keys
    
    @staticmethod
    def validate_percentage(value: float) -> bool:
        """Validate percentage value (0-100)"""
        return 0 <= value <= 100
    
    @staticmethod
    def validate_positive_number(value: float) -> bool:
        """Validate positive number"""
        return value > 0
    
    @staticmethod
    def validate_combat_config(config: CombatConfig) -> List[str]:
        """Validate combat configuration"""
        errors = []
        
        if not ConfigValidator.validate_key(config.attack_key):
            errors.append(f"Invalid attack key: {config.attack_key}")
            
        if not ConfigValidator.validate_key(config.pickup_key):
            errors.append(f"Invalid pickup key: {config.pickup_key}")
            
        if not ConfigValidator.validate_positive_number(config.attack_cooldown):
            errors.append("Attack cooldown must be positive")
            
        if not ConfigValidator.validate_percentage(config.retreat_hp_threshold):
            errors.append("Retreat HP threshold must be 0-100")
            
        return errors
    
    @staticmethod
    def validate_healing_config(config: HealingConfig) -> List[str]:
        """Validate healing configuration"""
        errors = []
        
        if not ConfigValidator.validate_positive_number(config.combat_heal_delay):
            errors.append("Combat heal delay must be positive")
            
        if not ConfigValidator.validate_positive_number(config.normal_heal_delay):
            errors.append("Normal heal delay must be positive")
            
        if not ConfigValidator.validate_percentage(config.panic_threshold):
            errors.append("Panic threshold must be 0-100")
            
        return errors

class ConfigManager:
    """Main configuration manager"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self._lock = threading.Lock()
        
        # Initialize all configurations
        self.combat = CombatConfig()
        self.healing = HealingConfig()
        self.movement = MovementConfig()
        self.anti_detection = AntiDetectionConfig()
        self.memory = MemoryConfig()
        self.detection = DetectionConfig()
        self.gui = GUIConfig()
        self.security = SecurityConfig()
        
        # Healing items configuration
        self.healing_items = {
            'Recovery Floppy': HealingItem('1', True, 70, 'hp', 3),
            'Hi-Recovery Disk': HealingItem('2', True, 50, 'hp', 2),
            'Mega Recovery HD': HealingItem('3', True, 25, 'hp', 1),
            'Energy Floppy': HealingItem('4', True, 70, 'ds', 3),
            'Hi-Energy Disk': HealingItem('5', True, 50, 'ds', 2),
            'Mega Energy HD': HealingItem('6', True, 25, 'ds', 1)
        }
        
        # Skills configuration
        self.skills = {
            f'F{i}': SkillConfig(
                enabled=(i <= 3),
                cooldown=float(i * 2.0),
                usage_chance=70.0 if i <= 3 else 30.0
            ) for i in range(1, 9)
        }
        
        # Load existing configs
        self.load_all_configs()
        
    def save_config(self, config_name: str, config_obj: Any) -> bool:
        """Save a specific configuration"""
        with self._lock:
            try:
                config_path = self.config_dir / f"{config_name}.json"
                
                # Convert dataclass to dict if needed
                if hasattr(config_obj, '__dataclass_fields__'):
                    data = asdict(config_obj)
                elif isinstance(config_obj, dict):
                    data = config_obj
                else:
                    data = config_obj.__dict__
                
                with open(config_path, 'w') as f:
                    json.dump(data, f, indent=2)
                    
                return True
                
            except Exception as e:
                print(f"Failed to save {config_name}: {e}")
                return False
            
    def load_config(self, config_name: str, config_class) -> Any:
        """Load a specific configuration"""
        try:
            config_path = self.config_dir / f"{config_name}.json"
            
            if config_path.exists():
                with open(config_path, 'r') as f:
                    data = json.load(f)
                    
                # Handle dataclass
                if hasattr(config_class, '__dataclass_fields__'):
                    return config_class(**data)
                else:
                    return data
                    
            return config_class() if hasattr(config_class, '__dataclass_fields__') else {}
            
        except Exception as e:
            print(f"Failed to load {config_name}: {e}")
            return config_class() if hasattr(config_class, '__dataclass_fields__') else {}
            
    def save_all_configs(self):
        """Save all configurations"""
        configs = {
            'combat': self.combat,
            'healing': self.healing,
            'movement': self.movement,
            'anti_detection': self.anti_detection,
            'memory': self.memory,
            'detection': self.detection,
            'gui': self.gui,
            'security': self.security,
            'healing_items': self.healing_items,
            'skills': self.skills
        }
        
        success_count = 0
        for name, config in configs.items():
            if self.save_config(name, config):
                success_count += 1
                
        return success_count == len(configs)
        
    def load_all_configs(self):
        """Load all configurations"""
        try:
            self.combat = self.load_config('combat', CombatConfig)
            self.healing = self.load_config('healing', HealingConfig)
            self.movement = self.load_config('movement', MovementConfig)
            self.anti_detection = self.load_config('anti_detection', AntiDetectionConfig)
            self.memory = self.load_config('memory', MemoryConfig)
            self.detection = self.load_config('detection', DetectionConfig)
            self.gui = self.load_config('gui', GUIConfig)
            self.security = self.load_config('security', SecurityConfig)
            
            # Load complex configs
            healing_items_data = self.load_config('healing_items', dict)
            if healing_items_data:
                for name, item_data in healing_items_data.items():
                    if isinstance(item_data, dict):
                        self.healing_items[name] = HealingItem(**item_data)
                        
            skills_data = self.load_config('skills', dict)
            if skills_data:
                for skill, skill_data in skills_data.items():
                    if isinstance(skill_data, dict):
                        self.skills[skill] = SkillConfig(**skill_data)
                        
        except Exception as e:
            print(f"Error loading configs: {e}")
            
    def validate_all_configs(self) -> Dict[str, List[str]]:
        """Validate all configurations and return errors"""
        all_errors = {}
        
        combat_errors = ConfigValidator.validate_combat_config(self.combat)
        if combat_errors:
            all_errors['combat'] = combat_errors
            
        healing_errors = ConfigValidator.validate_healing_config(self.healing)
        if healing_errors:
            all_errors['healing'] = healing_errors
            
        return all_errors
    
    def reset_to_defaults(self, config_name: str = None):
        """Reset configuration(s) to defaults"""
        if config_name:
            if config_name == 'combat':
                self.combat = CombatConfig()
            elif config_name == 'healing':
                self.healing = HealingConfig()
            elif config_name == 'movement':
                self.movement = MovementConfig()
            elif config_name == 'anti_detection':
                self.anti_detection = AntiDetectionConfig()
            elif config_name == 'memory':
                self.memory = MemoryConfig()
            elif config_name == 'detection':
                self.detection = DetectionConfig()
            elif config_name == 'gui':
                self.gui = GUIConfig()
            elif config_name == 'security':
                self.security = SecurityConfig()
        else:
            # Reset all
            self.__init__(str(self.config_dir))
            
    def export_config(self, filepath: str) -> bool:
        """Export all configurations to a file"""
        try:
            all_configs = {
                'combat': asdict(self.combat),
                'healing': asdict(self.healing),
                'movement': asdict(self.movement),
                'anti_detection': asdict(self.anti_detection),
                'memory': asdict(self.memory),
                'detection': asdict(self.detection),
                'gui': asdict(self.gui),
                'security': asdict(self.security),
                'healing_items': {k: asdict(v) for k, v in self.healing_items.items()},
                'skills': {k: asdict(v) for k, v in self.skills.items()}
            }
            
            with open(filepath, 'w') as f:
                json.dump(all_configs, f, indent=2)
                
            return True
            
        except Exception as e:
            print(f"Export failed: {e}")
            return False
            
    def import_config(self, filepath: str) -> bool:
        """Import configurations from a file"""
        try:
            with open(filepath, 'r') as f:
                all_configs = json.load(f)
                
            # Import each configuration
            if 'combat' in all_configs:
                self.combat = CombatConfig(**all_configs['combat'])
            if 'healing' in all_configs:
                self.healing = HealingConfig(**all_configs['healing'])
            if 'movement' in all_configs:
                self.movement = MovementConfig(**all_configs['movement'])
            if 'anti_detection' in all_configs:
                self.anti_detection = AntiDetectionConfig(**all_configs['anti_detection'])
            if 'memory' in all_configs:
                self.memory = MemoryConfig(**all_configs['memory'])
            if 'detection' in all_configs:
                self.detection = DetectionConfig(**all_configs['detection'])
            if 'gui' in all_configs:
                self.gui = GUIConfig(**all_configs['gui'])
            if 'security' in all_configs:
                self.security = SecurityConfig(**all_configs['security'])
                
            # Import healing items
            if 'healing_items' in all_configs:
                for name, item_data in all_configs['healing_items'].items():
                    self.healing_items[name] = HealingItem(**item_data)
                    
            # Import skills
            if 'skills' in all_configs:
                for skill, skill_data in all_configs['skills'].items():
                    self.skills[skill] = SkillConfig(**skill_data)
                    
            return True
            
        except Exception as e:
            print(f"Import failed: {e}")
            return False
            
    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of current configuration"""
        return {
            'combat': {
                'attack_key': self.combat.attack_key,
                'cooldown': self.combat.attack_cooldown,
                'auto_pickup': self.combat.auto_pickup
            },
            'healing': {
                'smart_healing': self.healing.smart_healing,
                'panic_threshold': self.healing.panic_threshold,
                'enabled_items': len([item for item in self.healing_items.values() if item.enabled])
            },
            'movement': {
                'auto_move': self.movement.auto_move,
                'pattern': self.movement.exploration_pattern,
                'smart_positioning': self.movement.smart_positioning
            },
            'anti_detection': {
                'human_timing': self.anti_detection.human_timing,
                'stealth_mode': self.anti_detection.stealth_mode,
                'break_system': self.anti_detection.break_system
            },
            'memory': {
                'enabled': self.memory.use_memory,
                'process': self.memory.process_name,
                'auto_reconnect': self.memory.auto_reconnect
            }
        }