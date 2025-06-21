"""
Core systems module for GDMO TamerBot
"""

try:
    from .memory_reader import MemoryReader, MemoryStats, DigimonStats
except ImportError as e:
    print(f"Warning: Memory reader not available: {e}")
    MemoryReader = None
    MemoryStats = None
    DigimonStats = None

try:
    from .input_controller import InputController, InputSequenceBuilder
except ImportError as e:
    print(f"Warning: Input controller not available: {e}")
    InputController = None
    InputSequenceBuilder = None

try:
    from .detection import DigimonDetector, DetectedEntity
except ImportError as e:
    print(f"Warning: Detection system not available: {e}")
    DigimonDetector = None
    DetectedEntity = None

try:
    from .bot_engine import BotEngine, GameState
except ImportError as e:
    print(f"Warning: Bot engine not available: {e}")
    BotEngine = None
    GameState = None

__all__ = [
    'MemoryReader',
    'MemoryStats', 
    'DigimonStats',
    'InputController',
    'InputSequenceBuilder',
    'DigimonDetector',
    'DetectedEntity', 
    'BotEngine',
    'GameState'
]