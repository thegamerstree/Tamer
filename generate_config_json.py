import json

DEFAULT_HEALING_ITEMS = {
    'Recovery Floppy': {
        'key': '1', 'enabled': True, 'threshold': 70, 'item_type': 'hp', 'priority': 3, 'cooldown': 2.0
    },
    'Hi-Recovery Disk': {
        'key': '2', 'enabled': True, 'threshold': 50, 'item_type': 'hp', 'priority': 2, 'cooldown': 2.0
    },
    'Mega Recovery HD': {
        'key': '3', 'enabled': True, 'threshold': 25, 'item_type': 'hp', 'priority': 1, 'cooldown': 2.0
    },
    'Energy Floppy': {
        'key': '4', 'enabled': True, 'threshold': 70, 'item_type': 'ds', 'priority': 3, 'cooldown': 2.0
    },
    'Hi-Energy Disk': {
        'key': '5', 'enabled': True, 'threshold': 50, 'item_type': 'ds', 'priority': 2, 'cooldown': 2.0
    },
    'Mega Energy HD': {
        'key': '6', 'enabled': True, 'threshold': 25, 'item_type': 'ds', 'priority': 1, 'cooldown': 2.0
    }
}

DEFAULT_SKILLS = {
    f'F{i}': {'enabled': (i <= 3), 'cooldown': float(i * 2.0), 'usage_chance': 70.0 if i <= 3 else 30.0, 'combat_only': True, 'emergency_use': False, 'combo_starter': (i==1)}
    for i in range(1, 9)
}

with open('config/healing_items.json', 'w') as f:
    json.dump(DEFAULT_HEALING_ITEMS, f, indent=2)

with open('config/skills.json', 'w') as f:
    json.dump(DEFAULT_SKILLS, f, indent=2)

print("Generated default config JSON files.")
