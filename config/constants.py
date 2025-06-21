"""
Game constants and mappings for GDMO
"""

# Virtual Key Codes for keyboard input
VK_CODES = {
    # Numbers
    '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34, '5': 0x35,
    '6': 0x36, '7': 0x37, '8': 0x38, '9': 0x39, '0': 0x30,
    
    # Function Keys
    'F1': 0x70, 'F2': 0x71, 'F3': 0x72, 'F4': 0x73,
    'F5': 0x74, 'F6': 0x75, 'F7': 0x76, 'F8': 0x77,
    'F9': 0x78, 'F10': 0x79, 'F11': 0x7A, 'F12': 0x7B,
    
    # Movement Keys
    'W': 0x57, 'A': 0x41, 'S': 0x53, 'D': 0x44,
    
    # Special Keys
    'TAB': 0x09, 'SPACE': 0x20, 'ENTER': 0x0D, 'ESC': 0x1B,
    'SHIFT': 0x10, 'CTRL': 0x11, 'ALT': 0x12,
    
    # Arrow Keys
    'UP': 0x26, 'DOWN': 0x28, 'LEFT': 0x25, 'RIGHT': 0x27,
    
    # Additional Keys
    'INSERT': 0x2D, 'DELETE': 0x2E, 'HOME': 0x24, 'END': 0x23,
    'PAGEUP': 0x21, 'PAGEDOWN': 0x22
}

# Color ranges for Digimon detection in HSV
DIGIMON_COLOR_PROFILES = {
    'boss_nameplate': {
        'colors': [
            ([15, 100, 100], [25, 255, 255]),  # Orange/Gold range
            ([80, 100, 100], [100, 255, 255])  # Green range
        ],
        'min_area': 80,
        'max_area': 8000,
        'priority': 1
    },
    'red_hp_bar': {
        'colors': [
            ([0, 120, 120], [10, 255, 255]),   # Red range 1
            ([170, 120, 120], [180, 255, 255]) # Red range 2
        ],
        'min_area': 30,
        'max_area': 3000,
        'priority': 2
    },
    'enemy_nameplate': {
        'colors': [
            ([100, 100, 100], [130, 255, 255]), # Blue range
            ([95, 80, 80], [135, 255, 255])     # Extended blue
        ],
        'min_area': 50,
        'max_area': 5000,
        'priority': 3
    },
    'yellow_nameplate': {
        'colors': [
            ([20, 100, 100], [30, 255, 255])   # Yellow range
        ],
        'min_area': 60,
        'max_area': 6000,
        'priority': 4
    },
    'friendly_nameplate': {
        'colors': [
            ([60, 100, 100], [80, 255, 255])   # Green range
        ],
        'min_area': 40,
        'max_area': 4000,
        'priority': 5
    },
    'item_drop': {
        'colors': [
            ([40, 150, 150], [60, 255, 255])   # Item glow
        ],
        'min_area': 20,
        'max_area': 1000,
        'priority': 6
    }
}

# Memory offsets for different game data (USER NEEDS TO CONFIGURE)
MEMORY_OFFSETS = {
    'base_offset': 0x0072FF80,  # Default - needs to be found by user
    'player_stats': {
        # These need to be found by the user using memory scanners
        # Example format: 'hp': [offset1, offset2, offset3, etc]
        'hp': [],       # User needs to find HP memory address chain
        'max_hp': [],   # User needs to find Max HP memory address chain  
        'ds': [],       # User needs to find DS memory address chain
        'max_ds': [],   # User needs to find Max DS memory address chain
        'level': [],    # User needs to find Level memory address chain
        'exp': []       # User needs to find EXP memory address chain
    },
    'digimon_stats': {
        # Digimon partner stats - also need to be found by user
        'hp': [],
        'max_hp': [],
        'ds': [],
        'max_ds': [],
        'level': []
    },
    'position': {
        # Player position coordinates - need to be found by user
        'x': [],
        'y': [],
        'z': []
    },
    'game_state': {
        # Game state flags - need to be found by user
        'in_combat': [],
        'loading': [],
        'connected': []
    }
}

# Default healing items configuration
DEFAULT_HEALING_ITEMS = {
    'Recovery Floppy': {
        'key': '1',
        'threshold': 70,
        'type': 'hp',
        'priority': 3,
        'cooldown': 2.0,
        'cost': 50
    },
    'Hi-Recovery Disk': {
        'key': '2',
        'threshold': 50,
        'type': 'hp',
        'priority': 2,
        'cooldown': 2.0,
        'cost': 150
    },
    'Mega Recovery HD': {
        'key': '3',
        'threshold': 25,
        'type': 'hp',
        'priority': 1,
        'cooldown': 2.0,
        'cost': 500
    },
    'Energy Floppy': {
        'key': '4',
        'threshold': 70,
        'type': 'ds',
        'priority': 3,
        'cooldown': 2.0,
        'cost': 40
    },
    'Hi-Energy Disk': {
        'key': '5',
        'threshold': 50,
        'type': 'ds',
        'priority': 2,
        'cooldown': 2.0,
        'cost': 120
    },
    'Mega Energy HD': {
        'key': '6',
        'threshold': 25,
        'type': 'ds',
        'priority': 1,
        'cooldown': 2.0,
        'cost': 400
    }
}

# Default skill configurations
DEFAULT_SKILLS = {
    'F1': {'cooldown': 2.0, 'usage_chance': 80.0, 'combo_starter': True},
    'F2': {'cooldown': 4.0, 'usage_chance': 70.0, 'combo_starter': False},
    'F3': {'cooldown': 6.0, 'usage_chance': 60.0, 'combo_starter': False},
    'F4': {'cooldown': 8.0, 'usage_chance': 50.0, 'combo_starter': False},
    'F5': {'cooldown': 10.0, 'usage_chance': 40.0, 'combo_starter': False},
    'F6': {'cooldown': 12.0, 'usage_chance': 30.0, 'combo_starter': False},
    'F7': {'cooldown': 15.0, 'usage_chance': 25.0, 'combo_starter': False},
    'F8': {'cooldown': 20.0, 'usage_chance': 20.0, 'combo_starter': False}
}

# Movement patterns
MOVEMENT_PATTERNS = {
    'Random': {
        'description': 'Random directional movement',
        'directions': ['W', 'A', 'S', 'D'],
        'weights': [1.0, 1.0, 1.0, 1.0],
        'duration_range': (0.5, 2.0)
    },
    'Circular': {
        'description': 'Circular patrol pattern',
        'directions': ['W', 'D', 'S', 'A'],
        'weights': [1.0, 1.0, 1.0, 1.0],
        'duration_range': (1.0, 1.5)
    },
    'Figure8': {
        'description': 'Figure-8 exploration pattern',
        'directions': ['W', 'A', 'S', 'D', 'W', 'D', 'S', 'A'],
        'weights': [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
        'duration_range': (0.8, 1.2)
    },
    'Aggressive': {
        'description': 'Forward-focused aggressive movement',
        'directions': ['W', 'A', 'D'],
        'weights': [2.0, 1.0, 1.0],
        'duration_range': (0.3, 1.0)
    },
    'Defensive': {
        'description': 'Backward-focused defensive movement',
        'directions': ['S', 'A', 'D'],
        'weights': [2.0, 1.0, 1.0],
        'duration_range': (1.0, 2.5)
    }
}

# Game window detection patterns
WINDOW_DETECTION_PATTERNS = [
    "Digital World",
    "GDMO",
    "Digimon Masters Online",
    "DigimonMasters",
    "KDMO"
]

# Process names to search for
GAME_PROCESSES = [
    "GDMO.exe",
    "KDMO.exe",
    "DigimonMasters.exe",
    "DMO.exe"
]

# Anti-detection timing ranges
TIMING_RANGES = {
    'attack': {
        'min': 0.8,
        'max': 3.5,
        'variance': 0.4,
        'human_min': 0.15,
        'human_max': 0.8
    },
    'heal': {
        'min': 0.3,
        'max': 1.2,
        'variance': 0.2,
        'human_min': 0.1,
        'human_max': 0.5
    },
    'movement': {
        'min': 0.1,
        'max': 0.6,
        'variance': 0.15,
        'human_min': 0.05,
        'human_max': 0.3
    },
    'special': {
        'min': 1.0,
        'max': 4.0,
        'variance': 0.5,
        'human_min': 0.2,
        'human_max': 1.0
    },
    'pickup': {
        'min': 0.2,
        'max': 1.0,
        'variance': 0.3,
        'human_min': 0.1,
        'human_max': 0.4
    }
}

# Break system configuration
BREAK_SYSTEM = {
    'micro_breaks': {
        'min_duration': 2.0,
        'max_duration': 8.0,
        'probability': 0.02,
        'messages': [
            "Taking micro-break",
            "Brief pause",
            "Moment of rest",
            "Quick break"
        ]
    },
    'session_breaks': {
        'min_interval': 2700,
        'max_interval': 5400,
        'min_duration': 300,
        'max_duration': 900,
        'messages': [
            "Session break time",
            "Taking extended break",
            "Rest period",
            "Long break"
        ]
    },
    'fatigue_breaks': {
        'trigger_duration': 3600,
        'min_duration': 600,
        'max_duration': 1800,
        'fatigue_multiplier': 1.5,
        'messages': [
            "Fatigue break",
            "Rest for fatigue",
            "Extended rest",
            "Recovery break"
        ]
    }
}

# Combat combo sequences
COMBAT_COMBOS = {
    'basic_assault': {
        'name': 'Basic Assault',
        'sequence': [
            {'type': 'tab', 'delay': 0.2},
            {'type': 'attack', 'delay': 0.3},
            {'type': 'special', 'key': 'F1', 'delay': 0.5}
        ],
        'cooldown': 8.0,
        'success_rate': 0.9
    },
    'power_strike': {
        'name': 'Power Strike',
        'sequence': [
            {'type': 'tab', 'delay': 0.2},
            {'type': 'special', 'key': 'F2', 'delay': 0.4},
            {'type': 'attack', 'delay': 0.3},
            {'type': 'attack', 'delay': 0.4}
        ],
        'cooldown': 12.0,
        'success_rate': 0.8
    },
    'quick_burst': {
        'name': 'Quick Burst',
        'sequence': [
            {'type': 'attack', 'delay': 0.2},
            {'type': 'special', 'key': 'F1', 'delay': 0.3},
            {'type': 'special', 'key': 'F3', 'delay': 0.4}
        ],
        'cooldown': 10.0,
        'success_rate': 0.85
    },
    'defensive_counter': {
        'name': 'Defensive Counter',
        'sequence': [
            {'type': 'movement', 'key': 'S', 'delay': 0.5},
            {'type': 'special', 'key': 'F4', 'delay': 0.3},
            {'type': 'attack', 'delay': 0.2}
        ],
        'cooldown': 15.0,
        'success_rate': 0.75
    },
    'ultimate_combo': {
        'name': 'Ultimate Combo',
        'sequence': [
            {'type': 'tab', 'delay': 0.2},
            {'type': 'special', 'key': 'F1', 'delay': 0.3},
            {'type': 'special', 'key': 'F2', 'delay': 0.4},
            {'type': 'attack', 'delay': 0.3},
            {'type': 'special', 'key': 'F3', 'delay': 0.5}
        ],
        'cooldown': 20.0,
        'success_rate': 0.7
    }
}

# GUI color schemes
COLOR_SCHEMES = {
    'dark': {
        'bg': '#0a0f1a',
        'card': '#1a2332',
        'primary': '#ff7b00',
        'secondary': '#00d4ff',
        'success': '#00ff88',
        'danger': '#ff3366',
        'warning': '#ffaa00',
        'legendary': '#9966ff',
        'text': '#ffffff',
        'text_dim': '#b8c5d6',
        'border': '#334455'
    },
    'light': {
        'bg': '#f8f9fa',
        'card': '#ffffff',
        'primary': '#007bff',
        'secondary': '#6c757d',
        'success': '#28a745',
        'danger': '#dc3545',
        'warning': '#ffc107',
        'legendary': '#6f42c1',
        'text': '#212529',
        'text_dim': '#6c757d',
        'border': '#dee2e6'
    },
    'cyberpunk': {
        'bg': '#0d1117',
        'card': '#161b22',
        'primary': '#ff00ff',
        'secondary': '#00ffff',
        'success': '#00ff00',
        'danger': '#ff0040',
        'warning': '#ffff00',
        'legendary': '#8a2be2',
        'text': '#f0f6fc',
        'text_dim': '#8b949e',
        'border': '#30363d'
    }
}

# Detection confidence thresholds
DETECTION_THRESHOLDS = {
    'minimum_confidence': 0.3,
    'good_confidence': 0.6,
    'excellent_confidence': 0.8,
    'area_variance_threshold': 0.2,
    'position_stability_threshold': 10,
    'color_consistency_threshold': 0.15
}

# Performance optimization settings
PERFORMANCE_SETTINGS = {
    'max_fps': 60,
    'target_loop_time': 0.016,
    'memory_read_interval': 0.1,
    'detection_interval': 0.05,
    'gui_update_interval': 0.5,
    'max_detection_history': 100,
    'max_timing_history': 50,
    'thread_pool_size': 4
}

# Error codes and messages
ERROR_CODES = {
    'MEMORY_CONNECTION_FAILED': {
        'code': 1001,
        'message': 'Failed to connect to game memory',
        'solution': 'Ensure game is running and bot has admin privileges'
    },
    'INVALID_GAME_PROCESS': {
        'code': 1002,
        'message': 'Game process not found',
        'solution': 'Start the game and try again'
    },
    'DETECTION_SYSTEM_FAILED': {
        'code': 2001,
        'message': 'Computer vision system failed to initialize',
        'solution': 'Check OpenCV installation and camera permissions'
    },
    'WINDOW_NOT_FOUND': {
        'code': 2002,
        'message': 'Game window not detected',
        'solution': 'Ensure game window is visible and not minimized'
    },
    'INPUT_SYSTEM_ERROR': {
        'code': 3001,
        'message': 'Input system error',
        'solution': 'Run as administrator and check keyboard permissions'
    },
    'CONFIG_VALIDATION_ERROR': {
        'code': 4001,
        'message': 'Configuration validation failed',
        'solution': 'Check configuration values and reset to defaults if needed'
    }
}

# Plugin system constants
PLUGIN_SYSTEM = {
    'plugin_directory': 'plugins',
    'plugin_extension': '.py',
    'required_methods': ['initialize', 'update', 'cleanup'],
    'optional_methods': ['on_start', 'on_stop', 'on_pause', 'on_resume'],
    'max_plugins': 10,
    'plugin_timeout': 5.0
}

# API endpoints for updates and telemetry (if enabled)
API_ENDPOINTS = {
    'update_check': 'https://api.example.com/bot/update-check',
    'telemetry': 'https://api.example.com/bot/telemetry',
    'error_reporting': 'https://api.example.com/bot/error-report'
}

# Version information
VERSION_INFO = {
    'major': 10,
    'minor': 0,
    'patch': 0,
    'build': 1,
    'version_string': '10.0.0.1',
    'codename': 'Omega',
    'release_date': '2024-01-01'
}