import time
import random
import logging
import psutil

logger = logging.getLogger(__name__)

PYMEM_AVAILABLE = False
try:
    import pymem
    PYMEM_AVAILABLE = True
except ImportError:
    logger.warning("Pymem not available - memory features disabled")

class MemoryReader:
    def __init__(self, process_name: str = "GDMO.exe"):
        self.process_name = process_name
        self.pm = None
        self.connected = False
        self.base_address = None
        self.base_offset = 0x0072FF80
        self.offsets = {
            'hp': [0x40, 0, 4, 8, 0x14, 0xAC, 0x80],
            'max_hp': [0x40, 0, 4, 8, 0x14, 0xAC, 0x74],
            'ds': [0x40, 0, 4, 8, 0x14, 0xAC, 0x84],
            'max_ds': [0x40, 0, 4, 8, 0x14, 0xAC, 0x78]
        }
        self.last_valid_stats = None

    def connect(self):
        if not PYMEM_AVAILABLE:
            logger.error("Pymem not available. MemoryReader will not function.")
            self.connected = False
            self.base_address = None
            return False
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and proc.info['name'].lower() == self.process_name.lower():
                try:
                    self.pm = pymem.Pymem(self.process_name)
                    self.base_address = self.pm.base_address + self.base_offset
                    self.connected = True
                    logger.info(f"Connected to {self.process_name} at base {hex(self.base_address)}")
                    return True
                except Exception as e:
                    logger.error(f"Failed to connect to {self.process_name}: {e}")
                    self.connected = False
                    self.base_address = None
                    return False
        logger.warning(f"Process {self.process_name} not found.")
        self.connected = False
        self.base_address = None
        return False

    def disconnect(self):
        if self.pm:
            try:
                self.pm.close_process()
            except Exception:
                pass
        self.pm = None
        self.connected = False
        self.base_address = None
        logger.info("Disconnected from process memory.")

    def update_addresses(self, base_offset):
        # Accept int or hex str
        if isinstance(base_offset, str):
            try:
                self.base_offset = int(base_offset, 16) if base_offset.startswith('0x') else int(base_offset)
            except Exception as e:
                logger.error(f'Invalid base_offset value: {base_offset} ({e})')
                return
        else:
            self.base_offset = base_offset
        # Always update base_address if connected
        if self.pm and self.connected:
            try:
                self.base_address = self.pm.base_address + self.base_offset
            except Exception as e:
                logger.error(f"Failed to update base_address: {e}")
                self.base_address = None

    update_base_address = update_addresses  # Alias for GUI compatibility

    def _read_pointer_chain(self, base, offsets):
        try:
            if not base or base == 0:
                return 0
            addr = base
            for off in offsets[:-1]:
                addr = self.pm.read_int(addr + off)
                if not addr or addr == 0:
                    return 0
            return self.pm.read_int(addr + offsets[-1])
        except Exception:
            return 0

    def get_stats(self):
        # Return default if not connected
        if not self.connected or not self.pm or not self.base_address:
            return {'hp': 1000, 'ds': 500, 'max_hp': 1000, 'max_ds': 500, 'hp_pct': 100.0, 'ds_pct': 100.0, 'connected': False}
        hp, max_hp = self._read_pointer_chain(self.base_address, self.offsets['hp']), self._read_pointer_chain(self.base_address, self.offsets['max_hp'])
        ds, max_ds = self._read_pointer_chain(self.base_address, self.offsets['ds']), self._read_pointer_chain(self.base_address, self.offsets['max_ds'])
        # Validity check: all values must be >0 and not ridiculously high
        if all(0 < v <= 50000 for v in (hp, max_hp, ds, max_ds)) and hp <= max_hp * 1.1 and ds <= max_ds * 1.1:
            stats = {
                'hp': hp,
                'ds': ds,
                'max_hp': max_hp,
                'max_ds': max_ds,
                'hp_pct': (hp / max_hp) * 100 if max_hp else 0,
                'ds_pct': (ds / max_ds) * 100 if max_ds else 0,
                'connected': True
            }
            self.last_valid_stats = stats
            return stats
        # Fallback
        return self.last_valid_stats if self.last_valid_stats else {
            'hp': 1000, 'ds': 500, 'max_hp': 1000, 'max_ds': 500,
            'hp_pct': 100.0, 'ds_pct': 100.0, 'connected': False
        }

    def get_current_state(self):
        return self.get_stats()

    def test_connection(self):
        if not self.connected:
            self.connect()
        stats = self.get_stats()
        if stats.get("connected", False):
            return True, "Memory connected and stats read successfully"
        else:
            return False, "Failed to connect or read stats"
