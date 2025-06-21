"""
Verify all module imports work correctly
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test all module imports"""
    print("🧪 Testing module imports...")
    
    # Test config imports
    try:
        from config.settings import ConfigManager
        from config.constants import VK_CODES
        print("✅ Config modules imported successfully")
    except ImportError as e:
        print(f"❌ Config import failed: {e}")
    
    # Test utils imports
    try:
        from utils.logger import Logger
        print("✅ Utils modules imported successfully")
    except ImportError as e:
        print(f"❌ Utils import failed: {e}")
    
    # Test core imports
    try:
        from core.memory_reader import MemoryReader
        from core.input_controller import InputController
        from core.detection import DigimonDetector
        from core.bot_engine import BotEngine
        print("✅ Core modules imported successfully")
    except ImportError as e:
        print(f"❌ Core import failed: {e}")
    
    # Test combat imports
    try:
        from combat.combat_system import CombatSystem
        from combat.healing_system import HealingSystem
        print("✅ Combat modules imported successfully")
    except ImportError as e:
        print(f"❌ Combat import failed: {e}")
    
    # Test movement imports
    try:
        from movement.pathfinding import PathfindingSystem
        print("✅ Movement modules imported successfully")
    except ImportError as e:
        print(f"❌ Movement import failed: {e}")
    
    # Test anti-detection imports
    try:
        from anti_detection.timing_system import TimingSystem
        print("✅ Anti-detection modules imported successfully")
    except ImportError as e:
        print(f"❌ Anti-detection import failed: {e}")
    
    # Test GUI imports
    try:
        from gui.main_window import MainWindow
        print("✅ GUI modules imported successfully")
    except ImportError as e:
        print(f"❌ GUI import failed: {e}")
    
    print("\n🎯 Import test completed!")

if __name__ == "__main__":
    test_imports()