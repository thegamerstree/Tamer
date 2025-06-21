"""
Core bot engine that orchestrates all subsystems
"""

import time
import threading
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass
import queue

from core.memory_reader import MemoryReader
from core.detection import DigimonDetector
from core.input_controller import InputController
from utils.logger import Logger

@dataclass
class GameState:
    """Current game state information"""
    timestamp: float
    in_game: bool = False
    player_stats: Dict[str, Any] = None
    digimon_stats: Dict[str, Any] = None
    detected_entities: List[Any] = None
    window_active: bool = False
    in_combat: bool = False
    loading: bool = False
    position: Dict[str, float] = None
    
    def __post_init__(self):
        if self.player_stats is None:
            self.player_stats = {}
        if self.digimon_stats is None:
            self.digimon_stats = {}
        if self.detected_entities is None:
            self.detected_entities = []
        if self.position is None:
            self.position = {'x': 0, 'y': 0, 'z': 0}

class BotEngine:
    """Main bot engine that coordinates all subsystems"""
    
    def __init__(self, main_app):
        self.app = main_app
        self.logger = Logger()
        
        # Engine state
        self.running = False
        self.paused = False
        self.initialized = False
        
        # Core systems
        self.memory = None
        self.detector = None
        self.input_controller = None
        
        # Subsystems (will be initialized by importing modules)
        self.combat_system = None
        self.healing_system = None
        self.pathfinding = None
        self.timing_system = None
        
        # Threading and execution
        self.executor = ThreadPoolExecutor(max_workers=6)
        self.main_thread = None
        self.system_threads = {}
        
        # State management
        self.current_game_state = GameState(timestamp=time.time())
        self.state_lock = threading.Lock()
        self.state_queue = queue.Queue(maxsize=10)
        
        # Performance monitoring
        self.performance_metrics = {
            'loop_times': [],
            'memory_reads': 0,
            'detections': 0,
            'actions': 0,
            'errors': 0,
            'start_time': 0
        }
        
        # System health monitoring
        self.health_check_interval = 5.0
        self.last_health_check = 0
        self.system_health = {}
        
        # Configuration
        self.target_fps = 20
        self.target_loop_time = 1.0 / self.target_fps
        
        self.logger.info("Bot engine initialized")
    
    def initialize_systems(self) -> bool:
        """Initialize all bot systems"""
        try:
            self.logger.info("Initializing bot systems...")
            
            # Initialize core systems
            self.memory = MemoryReader(self.app.config_manager.memory)
            self.detector = DigimonDetector()
            self.input_controller = InputController()
            
            # Test core systems
            if not self._test_core_systems():
                self.logger.error("Core system tests failed")
                return False
            
            # Initialize subsystems
            success = self._initialize_subsystems()
            if not success:
                self.logger.error("Subsystem initialization failed")
                return False
            
            # Initialize health monitoring
            self._initialize_health_monitoring()
            
            self.initialized = True
            self.logger.info("All systems initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"System initialization failed: {e}")
            return False
    
    def _test_core_systems(self) -> bool:
        """Test core systems functionality"""
        try:
            # Test memory system
            if self.app.config_manager.memory.use_memory:
                memory_connected = self.memory.connect()
                if not memory_connected:
                    self.logger.warning("Memory system failed to connect")
            
            # Test detection system
            detection_initialized = self.detector.initialize()
            if not detection_initialized:
                self.logger.warning("Detection system failed to initialize")
            
            # Test input controller
            input_stats = self.input_controller.get_key_statistics()
            if input_stats is None:
                self.logger.warning("Input controller test failed")
            
            self.logger.info("Core system tests completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Core system test error: {e}")
            return False
    
    def _initialize_subsystems(self) -> bool:
        """Initialize subsystems with lazy imports"""
        try:
            # Import and initialize combat system
            from combat.combat_system import CombatSystem
            self.combat_system = CombatSystem(self)
            if not self.combat_system.initialize():
                self.logger.error("Combat system initialization failed")
                return False
            
            # Import and initialize healing system
            from combat.healing_system import HealingSystem
            self.healing_system = HealingSystem(self)
            if not self.healing_system.initialize():
                self.logger.error("Healing system initialization failed")
                return False
            
            # Import and initialize pathfinding
            from movement.pathfinding import PathfindingSystem
            self.pathfinding = PathfindingSystem(self)
            if not self.pathfinding.initialize():
                self.logger.error("Pathfinding system initialization failed")
                return False
            
            # Import and initialize timing system
            from anti_detection.timing_system import TimingSystem
            self.timing_system = TimingSystem(self)
            if not self.timing_system.initialize():
                self.logger.error("Timing system initialization failed")
                return False
            
            return True
            
        except ImportError as e:
            self.logger.error(f"Failed to import subsystem: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Subsystem initialization error: {e}")
            return False
    
    def _initialize_health_monitoring(self):
        """Initialize system health monitoring"""
        self.system_health = {
            'memory': {'status': 'unknown', 'last_check': 0, 'errors': 0},
            'detection': {'status': 'unknown', 'last_check': 0, 'errors': 0},
            'input': {'status': 'unknown', 'last_check': 0, 'errors': 0},
            'combat': {'status': 'unknown', 'last_check': 0, 'errors': 0},
            'healing': {'status': 'unknown', 'last_check': 0, 'errors': 0},
            'pathfinding': {'status': 'unknown', 'last_check': 0, 'errors': 0},
            'timing': {'status': 'unknown', 'last_check': 0, 'errors': 0}
        }
    
    def start(self) -> bool:
        """Start the bot engine"""
        if self.running:
            self.logger.warning("Bot engine is already running")
            return False
        
        if not self.initialized:
            if not self.initialize_systems():
                return False
        
        try:
            self.running = True
            self.paused = False
            self.performance_metrics['start_time'] = time.time()
            
            # Start main bot thread
            self.main_thread = threading.Thread(target=self._main_loop, daemon=True)
            self.main_thread.start()
            
            # Start health monitoring thread
            health_thread = threading.Thread(target=self._health_monitoring_loop, daemon=True)
            health_thread.start()
            self.system_threads['health'] = health_thread
            
            self.logger.info("Bot engine started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start bot engine: {e}")
            self.running = False
            return False
    
    def stop(self):
        """Stop the bot engine"""
        if not self.running:
            return
        
        self.logger.info("Stopping bot engine...")
        
        try:
            # Stop main loop
            self.running = False
            
            # Stop all inputs immediately
            if self.input_controller:
                self.input_controller.stop_all_inputs()
            
            # Wait for main thread to finish
            if self.main_thread and self.main_thread.is_alive():
                self.main_thread.join(timeout=5)
                if self.main_thread.is_alive():
                    self.logger.warning("Main thread did not terminate cleanly")
            
            # Stop subsystems
            self._stop_subsystems()
            
            # Cleanup core systems
            self._cleanup_core_systems()
            
            # Shutdown executor
            self.executor.shutdown(wait=True)
            
            self.logger.info("Bot engine stopped")
            
        except Exception as e:
            self.logger.error(f"Error during bot engine shutdown: {e}")
    
    def pause(self):
        """Pause bot operations"""
        if not self.running:
            return
        
        self.paused = True
        
        # Stop all inputs
        if self.input_controller:
            self.input_controller.stop_all_inputs()
        
        # Pause subsystems
        if self.combat_system:
            self.combat_system.pause()
        if self.healing_system:
            self.healing_system.pause()
        if self.pathfinding:
            self.pathfinding.pause()
        
        self.logger.info("Bot engine paused")
    
    def resume(self):
        """Resume bot operations"""
        if not self.running or not self.paused:
            return
        
        self.paused = False
        
        # Resume subsystems
        if self.combat_system:
            self.combat_system.resume()
        if self.healing_system:
            self.healing_system.resume()
        if self.pathfinding:
            self.pathfinding.resume()
        
        self.logger.info("Bot engine resumed")
    
    def _main_loop(self):
        """Main bot execution loop"""
        self.logger.info("Main bot loop started")
        
        while self.running:
            try:
                loop_start = time.time()
                
                if not self.paused:
                    # Update game state
                    self._update_game_state()
                    
                    # Execute bot logic
                    self._execute_bot_cycle()
                    
                    # Update performance metrics
                    self.performance_metrics['actions'] += 1
                
                # Calculate loop timing
                loop_time = time.time() - loop_start
                self.performance_metrics['loop_times'].append(loop_time)
                
                # Maintain consistent loop timing
                if loop_time < self.target_loop_time:
                    time.sleep(self.target_loop_time - loop_time)
                
                # Limit performance history
                if len(self.performance_metrics['loop_times']) > 100:
                    self.performance_metrics['loop_times'].pop(0)
                
            except Exception as e:
                self.performance_metrics['errors'] += 1
                self.logger.error(f"Main loop error: {e}")
                time.sleep(1)  # Prevent spam on persistent errors
        
        self.logger.info("Main bot loop ended")
    
    def _update_game_state(self):
        """Update current game state"""
        try:
            current_time = time.time()
            
            # Get memory data
            memory_data = {}
            if self.memory and self.app.config_manager.memory.use_memory:
                memory_data = self.memory.get_current_state()
                self.performance_metrics['memory_reads'] += 1
            
            # Get detection data
            detection_data = {'entities': [], 'window_active': False}
            if self.detector:
                entities = self.detector.detect_entities()
                detection_data = {
                    'entities': entities,
                    'window_active': self.detector.game_window_region is not None
                }
                if entities:
                    self.performance_metrics['detections'] += 1
            
            # Create new game state
            new_state = GameState(
                timestamp=current_time,
                in_game=memory_data.get('connected', False),
                player_stats=memory_data.get('stats', {}),
                digimon_stats=memory_data.get('digimon', {}),
                detected_entities=detection_data.get('entities', []),
                window_active=detection_data.get('window_active', False),
                in_combat=memory_data.get('stats', {}).get('in_combat', False),
                loading=memory_data.get('stats', {}).get('loading', False),
                position=memory_data.get('position', {'x': 0, 'y': 0, 'z': 0})
            )
            
            # Update current state thread-safely
            with self.state_lock:
                self.current_game_state = new_state
                
                # Add to state queue for subsystems
                try:
                    self.state_queue.put_nowait(new_state)
                except queue.Full:
                    # Remove oldest state if queue is full
                    try:
                        self.state_queue.get_nowait()
                        self.state_queue.put_nowait(new_state)
                    except queue.Empty:
                        pass
            
        except Exception as e:
            self.logger.error(f"Game state update error: {e}")
    
    def _execute_bot_cycle(self):
        """Execute one complete bot cycle"""
        try:
            current_time = time.time()
            
            with self.state_lock:
                game_state = self.current_game_state
            
            # Skip if not in game
            if not game_state.in_game and self.app.config_manager.memory.use_memory:
                return
            
            # Execute subsystems in priority order
            # 1. Healing (highest priority)
            if self.healing_system:
                self.healing_system.update(current_time, game_state)
            
            # 2. Combat
            if self.combat_system:
                self.combat_system.update(current_time, game_state)
            
            # 3. Movement/Pathfinding
            if self.pathfinding:
                self.pathfinding.update(current_time, game_state)
            
            # 4. Anti-detection measures
            if self.timing_system:
                self.timing_system.update(current_time, game_state)
            
        except Exception as e:
            self.logger.error(f"Bot cycle execution error: {e}")
    
    def _health_monitoring_loop(self):
        """Health monitoring loop for all systems"""
        while self.running:
            try:
                current_time = time.time()
                
                if current_time - self.last_health_check > self.health_check_interval:
                    self._perform_health_checks()
                    self.last_health_check = current_time
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                self.logger.error(f"Health monitoring error: {e}")
                time.sleep(5)
    
    def _perform_health_checks(self):
        """Perform health checks on all systems"""
        try:
            current_time = time.time()
            
            # Check memory system
            if self.memory:
                try:
                    stats = self.memory.get_performance_metrics()
                    if stats['error_rate'] > 0.5:  # More than 50% errors
                        self.system_health['memory']['status'] = 'degraded'
                        self.system_health['memory']['errors'] += 1
                    else:
                        self.system_health['memory']['status'] = 'healthy'
                except:
                    self.system_health['memory']['status'] = 'error'
                    self.system_health['memory']['errors'] += 1
                
                self.system_health['memory']['last_check'] = current_time
            
            # Check detection system
            if self.detector:
                try:
                    stats = self.detector.get_detection_statistics()
                    if stats['success_rate'] < 0.3:  # Less than 30% success
                        self.system_health['detection']['status'] = 'degraded'
                    else:
                        self.system_health['detection']['status'] = 'healthy'
                except:
                    self.system_health['detection']['status'] = 'error'
                    self.system_health['detection']['errors'] += 1
                
                self.system_health['detection']['last_check'] = current_time
            
            # Check input system
            if self.input_controller:
                try:
                    stats = self.input_controller.get_key_statistics()
                    if stats['success_rate'] < 0.8:  # Less than 80% success
                        self.system_health['input']['status'] = 'degraded'
                    else:
                        self.system_health['input']['status'] = 'healthy'
                except:
                    self.system_health['input']['status'] = 'error'
                    self.system_health['input']['errors'] += 1
                
                self.system_health['input']['last_check'] = current_time
            
            # Check subsystems
            for system_name, system in [
                ('combat', self.combat_system),
                ('healing', self.healing_system),
                ('pathfinding', self.pathfinding),
                ('timing', self.timing_system)
            ]:
                if system and hasattr(system, 'get_health_status'):
                    try:
                        health = system.get_health_status()
                        self.system_health[system_name]['status'] = health.get('status', 'unknown')
                        self.system_health[system_name]['last_check'] = current_time
                    except:
                        self.system_health[system_name]['status'] = 'error'
                        self.system_health[system_name]['errors'] += 1
            
            # Log degraded systems
            degraded_systems = [
                name for name, health in self.system_health.items() 
                if health['status'] in ['degraded', 'error']
            ]
            
            if degraded_systems:
                self.logger.warning(f"Degraded systems: {', '.join(degraded_systems)}")
            
        except Exception as e:
            self.logger.error(f"Health check error: {e}")
    
    def _stop_subsystems(self):
        """Stop all subsystems"""
        try:
            subsystems = [
                ('combat', self.combat_system),
                ('healing', self.healing_system),
                ('pathfinding', self.pathfinding),
                ('timing', self.timing_system)
            ]
            
            for name, system in subsystems:
                if system and hasattr(system, 'stop'):
                    try:
                        system.stop()
                        self.logger.info(f"{name} system stopped")
                    except Exception as e:
                        self.logger.error(f"Error stopping {name} system: {e}")
            
        except Exception as e:
            self.logger.error(f"Error stopping subsystems: {e}")
    
    def _cleanup_core_systems(self):
        """Cleanup core systems"""
        try:
            if self.input_controller:
                self.input_controller.cleanup()
            
            if self.detector:
                self.detector.cleanup()
            
            if self.memory:
                self.memory.disconnect()
            
            self.logger.info("Core systems cleaned up")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up core systems: {e}")
    
    def get_current_game_state(self) -> GameState:
        """Get current game state thread-safely"""
        with self.state_lock:
            return self.current_game_state
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        current_time = time.time()
        uptime = current_time - self.performance_metrics['start_time'] if self.performance_metrics['start_time'] > 0 else 0
        
        # Calculate average loop time
        avg_loop_time = 0
        fps = 0
        if self.performance_metrics['loop_times']:
            recent_times = self.performance_metrics['loop_times'][-50:]  # Last 50 loops
            avg_loop_time = sum(recent_times) / len(recent_times)
            fps = 1.0 / avg_loop_time if avg_loop_time > 0 else 0
        
        return {
            'running': self.running,
            'paused': self.paused,
            'uptime': uptime,
            'fps': fps,
            'avg_loop_time': avg_loop_time,
            'target_fps': self.target_fps,
            'memory_reads': self.performance_metrics['memory_reads'],
            'detections': self.performance_metrics['detections'],
            'actions': self.performance_metrics['actions'],
            'errors': self.performance_metrics['errors'],
            'system_health': self.system_health
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        try:
            status = {
                'engine': {
                    'running': self.running,
                    'paused': self.paused,
                    'initialized': self.initialized
                },
                'core_systems': {},
                'subsystems': {},
                'performance': self.get_performance_metrics(),
                'health': self.system_health
            }
            
            # Core systems status
            if self.memory:
                status['core_systems']['memory'] = self.memory.get_performance_metrics()
            
            if self.detector:
                status['core_systems']['detection'] = self.detector.get_detection_statistics()
            
            if self.input_controller:
                status['core_systems']['input'] = self.input_controller.get_key_statistics()
            
            # Subsystems status
            subsystems = [
                ('combat', self.combat_system),
                ('healing', self.healing_system),
                ('pathfinding', self.pathfinding),
                ('timing', self.timing_system)
            ]
            
            for name, system in subsystems:
                if system and hasattr(system, 'get_status'):
                    try:
                        status['subsystems'][name] = system.get_status()
                    except:
                        status['subsystems'][name] = {'status': 'error'}
            
            return status
            
        except Exception as e:
            self.logger.error(f"Error getting system status: {e}")
            return {'error': str(e)}
    
    def emergency_stop(self):
        """Emergency stop all operations immediately"""
        self.logger.warning("Emergency stop initiated")
        
        try:
            # Immediately stop all inputs
            if self.input_controller:
                self.input_controller.stop_all_inputs()
            
            # Stop main operations
            self.running = False
            self.paused = True
            
            # Stop subsystems
            if self.combat_system and hasattr(self.combat_system, 'emergency_stop'):
                self.combat_system.emergency_stop()
            
            if self.healing_system and hasattr(self.healing_system, 'emergency_stop'):
                self.healing_system.emergency_stop()
            
            if self.pathfinding and hasattr(self.pathfinding, 'emergency_stop'):
                self.pathfinding.emergency_stop()
            
            self.logger.warning("Emergency stop completed")
            
        except Exception as e:
            self.logger.error(f"Error during emergency stop: {e}")
    
    def restart_subsystem(self, subsystem_name: str) -> bool:
        """Restart a specific subsystem"""
        try:
            self.logger.info(f"Restarting {subsystem_name} subsystem")
            
            if subsystem_name == 'memory' and self.memory:
                self.memory.disconnect()
                return self.memory.connect()
            
            elif subsystem_name == 'detection' and self.detector:
                self.detector.cleanup()
                return self.detector.initialize()
            
            elif subsystem_name == 'combat' and self.combat_system:
                if hasattr(self.combat_system, 'restart'):
                    return self.combat_system.restart()
                else:
                    # Reinitialize if restart method not available
                    from combat.combat_system import CombatSystem
                    self.combat_system = CombatSystem(self)
                    return self.combat_system.initialize()
            
            elif subsystem_name == 'healing' and self.healing_system:
                if hasattr(self.healing_system, 'restart'):
                    return self.healing_system.restart()
                else:
                    from combat.healing_system import HealingSystem
                    self.healing_system = HealingSystem(self)
                    return self.healing_system.initialize()
            
            elif subsystem_name == 'pathfinding' and self.pathfinding:
                if hasattr(self.pathfinding, 'restart'):
                    return self.pathfinding.restart()
                else:
                    from movement.pathfinding import PathfindingSystem
                    self.pathfinding = PathfindingSystem(self)
                    return self.pathfinding.initialize()
            
            elif subsystem_name == 'timing' and self.timing_system:
                if hasattr(self.timing_system, 'restart'):
                    return self.timing_system.restart()
                else:
                    from anti_detection.timing_system import TimingSystem
                    self.timing_system = TimingSystem(self)
                    return self.timing_system.initialize()
            
            else:
                self.logger.error(f"Unknown subsystem: {subsystem_name}")
                return False
            
        except Exception as e:
            self.logger.error(f"Failed to restart {subsystem_name}: {e}")
            return False
    
    def adjust_performance(self, target_fps: int):
        """Adjust bot performance target"""
        if 1 <= target_fps <= 60:
            self.target_fps = target_fps
            self.target_loop_time = 1.0 / target_fps
            self.logger.info(f"Performance target adjusted to {target_fps} FPS")
        else:
            self.logger.error(f"Invalid FPS target: {target_fps}")
    
    def get_state_queue(self) -> queue.Queue:
        """Get state queue for subsystems"""
        return self.state_queue