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
    def __init__(self, app):
        self.app = app

        # PATCH: Proper MemoryReader initialization and config support
        proc_name = getattr(self.app.config_manager.memory, 'process_name', 'GDMO.exe')
        self.memory = MemoryReader(proc_name)
        base_offset = getattr(self.app.config_manager.memory, 'base_offset', '0x0072FF80')
        if hasattr(self.memory, "update_addresses"):
            self.memory.update_addresses(base_offset)
        # END PATCH

        self.detector = DigimonDetector()
        self.input_ctrl = InputController()
        self.logger = Logger("BotEngine")
        self.state_queue = queue.Queue(maxsize=10)
        self._main_thread = None
        self._running = False
        self._lock = threading.Lock()

    def start(self):
        if self._main_thread and self._main_thread.is_alive():
            return
        self._running = True
        self._main_thread = threading.Thread(target=self._main_loop, daemon=True)
        self._main_thread.start()

    def stop(self):
        self._running = False
        if self._main_thread:
            self._main_thread.join(timeout=2)

    def _main_loop(self):
        while self._running:
            try:
                config = self.app.config_manager
                game_state = self._update_game_state(config, GameState(timestamp=time.time()))
                self._execute_bot_cycle(config, game_state)
                time.sleep(0.05)
            except Exception as ex:
                self.logger.error(f"Main loop error: {ex}")
                time.sleep(1)

    def _update_game_state(self, config, game_state):
        # PATCH: Use get_stats instead of get_current_state
        memory_data = self.memory.get_stats() if self.memory and config.memory.use_memory else {}
        # END PATCH

        game_state.player_stats = memory_data.get("player_stats", {})
        game_state.digimon_stats = memory_data.get("digimon_stats", {})
        game_state.in_game = memory_data.get("connected", False)
        game_state.detected_entities = self.detector.detect()
        game_state.window_active = True  # You should replace with actual window active detection
        # Add more game state updates here if needed
        return game_state

    def _execute_bot_cycle(self, config, game_state):
        # (skip check removed for robust farming with or without memory connection)
        # If you want to restore a check, add it here.
        if not game_state.window_active:
            return

        # Example: Only engage if in game or if memory is not being used
        # Add actual farming/logic code here
        if game_state.in_game or not config.memory.use_memory:
            # Simulate actions: move, attack, heal, etc.
            detected = game_state.detected_entities
            if detected:
                self.logger.info(f"Detected {len(detected)} entities, first: {detected[0]}")
                # Call your attack/move/heal functions here
            else:
                self.logger.info("No entities detected.")

    # You may have more methods in the original file. Add them below.