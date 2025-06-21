"""
GDMO TamerBot v10.0 - Main Entry Point (Fixed Version)
Multi-threaded, modular bot with advanced anti-detection
"""

import sys
import os
import threading
import tkinter as tk
import time
from pathlib import Path
import signal
import ctypes

def is_admin():
    """Check if running with administrator privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """Restart the script with administrator privileges"""
    try:
        # Get the current script path
        script_path = os.path.abspath(sys.argv[0])
        
        # Parameters for ShellExecute
        params = ' '.join(sys.argv[1:]) if len(sys.argv) > 1 else ''
        
        # Request admin privileges and restart
        ctypes.windll.shell32.ShellExecuteW(
            None, 
            "runas", 
            sys.executable, 
            f'"{script_path}" {params}', 
            None, 
            1
        )
        
        # Exit current instance
        sys.exit(0)
        
    except Exception as e:
        print(f"Failed to restart as administrator: {e}")
        print("Please manually run this script as administrator.")
        input("Press Enter to exit...")
        sys.exit(1)

# Add project root to path BEFORE any local imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class TamerBot:
    def __init__(self):
        # Check admin privileges and auto-elevate if needed
        if not is_admin():
            print("🔐 Administrator privileges required!")
            print("🚀 Attempting to restart with admin privileges...")
            print("💡 You may see a UAC prompt - click 'Yes' to continue")
            time.sleep(2)  # Give user time to read the message
            run_as_admin()
        
        # Import modules only after admin check and path setup
        try:
            self.import_modules()
            self.initialize_components()
        except ImportError as e:
            self.handle_import_error(e)
        except Exception as e:
            self.handle_general_error(e)
    
    def import_modules(self):
        """Import all required modules with error handling"""
        print("📦 Loading modules...")
        
        # Core modules
        try:
            from utils.logger import Logger
            self.logger = Logger()
            self.logger.info("Logger initialized")
        except ImportError as e:
            print(f"❌ Failed to import logger: {e}")
            self.create_fallback_logger()
        
        try:
            from config.settings import ConfigManager
            self.config_manager = ConfigManager()
            self.logger.info("Configuration manager loaded")
        except ImportError as e:
            self.logger.error(f"Failed to import config manager: {e}")
            self.create_fallback_config()
        
        try:
            from core.bot_engine import BotEngine
            self.bot_engine_class = BotEngine
            self.logger.info("Bot engine loaded")
        except ImportError as e:
            self.logger.error(f"Failed to import bot engine: {e}")
            try:
                # Try simple bot engine fallback
                from core.simple_bot_engine import BotEngine
                self.bot_engine_class = BotEngine
                self.logger.info("Simple bot engine loaded as fallback")
            except ImportError as e2:
                self.logger.error(f"Failed to import simple bot engine: {e2}")
                self.bot_engine_class = None
    
    def create_fallback_logger(self):
        """Create a simple fallback logger"""
        class FallbackLogger:
            def info(self, msg): print(f"INFO: {msg}")
            def error(self, msg): print(f"ERROR: {msg}")
            def warning(self, msg): print(f"WARNING: {msg}")
            def debug(self, msg): print(f"DEBUG: {msg}")
        
        self.logger = FallbackLogger()
    
    def create_fallback_config(self):
        """Create fallback configuration"""
        class FallbackConfig:
            def __init__(self):
                self.loaded = False
        
        self.config_manager = FallbackConfig()
    
    def initialize_components(self):
        """Initialize GUI and bot components"""
        self.logger.info("Initializing components...")
        
        # Initialize GUI first (but don't connect to bot_engine yet)
        self.root = tk.Tk()
        
        # Always create SOME kind of bot engine BEFORE GUI setup
        self.bot_engine = None
        
        if self.bot_engine_class:
            try:
                self.bot_engine = self.bot_engine_class(self)
                self.logger.info("Bot engine initialized")
            except Exception as e:
                self.logger.error(f"Bot engine initialization failed: {e}")
                self.bot_engine = self.create_fallback_bot_engine()
        else:
            self.logger.warning("No bot engine class available - creating fallback")
            self.bot_engine = self.create_fallback_bot_engine()
        
        # NOW setup GUI with working bot_engine
        self.setup_gui()
        
        # Setup signal handlers
        self.setup_signal_handlers()
        
        self.logger.info("TamerBot v10.0 initialized successfully")
    
    def create_fallback_bot_engine(self):
        """Create a minimal fallback bot engine"""
        app = self  # Capture self reference
        
        class FallbackBotEngine:
            def __init__(self, main_app):
                self.app = main_app
                self.running = False
                self.paused = False
                self.memory = FallbackMemory(main_app)
                self.detector = FallbackDetector(main_app)
                
            def start(self):
                self.running = True
                self.app.log_message("✅ Fallback bot started (limited functionality)")
                return True
                
            def stop(self):
                self.running = False
                self.app.log_message("🛑 Fallback bot stopped")
                
            def pause(self):
                self.paused = True
                
            def resume(self):
                self.paused = False
        
        class FallbackMemory:
            def __init__(self, main_app):
                self.app = main_app
                self.connected = False
                print("✅ FallbackMemory created")  # Debug
                
            def connect(self):
                self.app.log_message("🔗 Fallback memory: Checking for game...")
                try:
                    import psutil
                    found_gdmo = False
                    for proc in psutil.process_iter(['name']):
                        proc_name = proc.info['name'].lower()
                        if any(game in proc_name for game in ['gdmo', 'digimon', 'dmo']):
                            self.connected = True
                            found_gdmo = True
                            self.app.log_message(f"✅ Found game process: {proc.info['name']}")
                            break
                    
                    if not found_gdmo:
                        self.app.log_message("❌ No game process found")
                        # List some running processes for debugging
                        try:
                            processes = [p.info['name'] for p in psutil.process_iter(['name']) if p.info['name']]
                            game_like = [p for p in processes if any(x in p.lower() for x in ['game', 'dmo', 'digi'])]
                            if game_like:
                                self.app.log_message(f"🔍 Found game-like processes: {', '.join(game_like[:5])}")
                        except:
                            pass
                    
                    return self.connected
                except ImportError:
                    self.app.log_message("❌ Cannot check processes (psutil not installed)")
                    self.app.log_message("💡 Install with: pip install psutil")
                    return False
                except Exception as e:
                    self.app.log_message(f"❌ Process check error: {e}")
                    return False
                    
            def test_connection(self):
                if self.connected:
                    return True, {
                        "status": "Connected via fallback", 
                        "process": "Game process found",
                        "method": "Process scanning"
                    }
                else:
                    return False, {
                        "error": "No game process detected",
                        "suggestion": "Make sure GDMO is running"
                    }
                    
            def update_base_address(self, address):
                self.app.log_message(f"📝 Fallback: Updated base address to {address}")
                self.app.log_message("💡 Note: This is stored but not used in fallback mode")
        
        class FallbackDetector:
            def __init__(self, main_app):
                self.app = main_app
                self.detected_windows = []
                self.game_window_region = None
                
            def setup_game_window(self):
                self.app.log_message("🔍 Fallback detector: Scanning windows...")
                try:
                    import win32gui
                    windows = []
                    
                    def enum_callback(hwnd, windows):
                        if win32gui.IsWindowVisible(hwnd):
                            title = win32gui.GetWindowText(hwnd)
                            if any(keyword in title.lower() for keyword in ['gdmo', 'digimon', 'digital']):
                                rect = win32gui.GetWindowRect(hwnd)
                                windows.append((title, rect, "GDMO.exe"))
                                self.detected_windows.append((hwnd, title, rect, "GDMO.exe"))
                        return True
                    
                    win32gui.EnumWindows(enum_callback, windows)
                    
                    if windows:
                        self.app.log_message(f"✅ Found {len(windows)} game window(s)")
                        return True, windows
                    else:
                        self.app.log_message("❌ No game windows found")
                        return False, []
                except ImportError:
                    self.app.log_message("❌ Cannot scan windows (missing win32gui)")
                    return False, []
                except Exception as e:
                    self.app.log_message(f"❌ Window scan error: {e}")
                    return False, []
                    
            def set_game_window_by_hwnd(self, hwnd):
                try:
                    import win32gui
                    title = win32gui.GetWindowText(hwnd)
                    rect = win32gui.GetWindowRect(hwnd)
                    self.game_window_region = rect
                    self.app.log_message(f"✅ Selected window: {title}")
                    return True, title
                except Exception as e:
                    self.app.log_message(f"❌ Window selection failed: {e}")
                    return False, str(e)
        
        return FallbackBotEngine(self)
    
    def setup_gui(self):
        """Setup the main GUI"""
        try:
            # Try to import custom GUI
            from gui.main_window import MainWindow
            # Pass the app reference so GUI can access bot_engine
            self.gui = MainWindow(self.root, self)
            self.logger.info("Custom GUI loaded successfully")
        except ImportError as e:
            # Fallback to basic GUI
            self.logger.warning(f"Custom GUI not available ({e}), using basic interface")
            self.setup_basic_gui()
        except Exception as e:
            self.logger.error(f"GUI setup error: {e}")
            self.setup_basic_gui()
    
    def setup_basic_gui(self):
        """Setup basic fallback GUI"""
        self.root.title("⚡ GDMO TamerBot v10.0")
        self.root.geometry("800x600")
        self.root.configure(bg='#0a0f1a')
        
        # Main frame
        main_frame = tk.Frame(self.root, bg='#0a0f1a')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(main_frame, text="⚡ GDMO TAMERBOT v10.0 ⚡", 
                              font=('Arial Black', 16, 'bold'), 
                              fg='#ff7b00', bg='#0a0f1a')
        title_label.pack(pady=20)
        
        # Status
        self.status_label = tk.Label(main_frame, text="🔴 Bot Offline", 
                                    font=('Arial', 12, 'bold'), 
                                    fg='#ff3366', bg='#0a0f1a')
        self.status_label.pack(pady=10)
        
        # Control buttons
        button_frame = tk.Frame(main_frame, bg='#0a0f1a')
        button_frame.pack(pady=20)
        
        self.start_btn = tk.Button(button_frame, text="🚀 START", 
                                  command=self.start_bot,
                                  font=('Arial', 12, 'bold'), 
                                  bg='#00ff88', fg='black',
                                  width=10)
        self.start_btn.pack(side='left', padx=10)
        
        self.stop_btn = tk.Button(button_frame, text="🛑 STOP", 
                                 command=self.stop_bot,
                                 font=('Arial', 12, 'bold'), 
                                 bg='#ff3366', fg='white',
                                 width=10, state='disabled')
        self.stop_btn.pack(side='left', padx=10)
        
        # Info text
        info_text = tk.Text(main_frame, height=15, width=80,
                           font=('Consolas', 10),
                           bg='#1a2332', fg='#ffffff')
        info_text.pack(pady=20, fill='both', expand=True)
        
        # Add some helpful info
        info_content = """
🎮 GDMO TamerBot v10.0 - Basic Mode

📋 Status: Ready to start
🔧 Mode: Simplified interface (some modules missing)

🚀 Getting Started:
1. Make sure GDMO is running
2. Click START to begin botting
3. Monitor the log output below

📝 Module Status:
"""
        # Check module availability
        modules_status = {
            'Logger': hasattr(self, 'logger'),
            'Config Manager': hasattr(self, 'config_manager') and self.config_manager.loaded if hasattr(self.config_manager, 'loaded') else False,
            'Bot Engine': self.bot_engine is not None,
            'Custom GUI': False  # We're using basic GUI
        }
        
        for module, status in modules_status.items():
            status_icon = "✅" if status else "❌"
            info_content += f"{status_icon} {module}\n"
        
        info_content += "\n📖 Logs will appear here when bot is running..."
        
        info_text.insert('1.0', info_content)
        info_text.config(state='disabled')
        
        self.log_display = info_text
    
    def start_bot(self):
        """Start the bot"""
        try:
            if hasattr(self, 'bot_engine') and self.bot_engine:
                success = self.bot_engine.start()
                if success:
                    self.status_label.config(text="🟢 Bot Running", fg='#00ff88')
                    self.start_btn.config(state='disabled')
                    self.stop_btn.config(state='normal')
                    self.log_message("Bot started successfully!")
                else:
                    self.log_message("Failed to start bot engine")
            else:
                self.log_message("Bot engine not available - cannot start")
                self.log_message("Note: Some modules may be missing")
        except Exception as e:
            self.log_message(f"Error starting bot: {e}")
    
    def stop_bot(self):
        """Stop the bot"""
        try:
            if hasattr(self, 'bot_engine') and self.bot_engine:
                self.bot_engine.stop()
            
            self.status_label.config(text="🔴 Bot Offline", fg='#ff3366')
            self.start_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
            self.log_message("Bot stopped")
        except Exception as e:
            self.log_message(f"Error stopping bot: {e}")
    
    def log_message(self, message):
        """Add message to log display"""
        try:
            timestamp = time.strftime("[%H:%M:%S]")
            log_entry = f"{timestamp} {message}\n"
            
            self.log_display.config(state='normal')
            self.log_display.insert('end', log_entry)
            self.log_display.see('end')
            self.log_display.config(state='disabled')
        except:
            print(f"{timestamp} {message}")
    
    def setup_signal_handlers(self):
        """Setup graceful shutdown handlers"""
        try:
            signal.signal(signal.SIGINT, self.graceful_shutdown)
            signal.signal(signal.SIGTERM, self.graceful_shutdown)
        except Exception as e:
            self.logger.warning(f"Could not setup signal handlers: {e}")
        
    def graceful_shutdown(self, signum=None, frame=None):
        """Handle graceful shutdown"""
        self.logger.info("Initiating graceful shutdown...")
        
        try:
            # Stop bot engine
            if hasattr(self, 'bot_engine') and self.bot_engine:
                self.bot_engine.stop()
            
            # Save configurations
            if hasattr(self, 'config_manager') and hasattr(self.config_manager, 'save_all_configs'):
                self.config_manager.save_all_configs()
            
            # Close GUI
            if hasattr(self, 'root'):
                self.root.quit()
                
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
        finally:
            self.logger.info("Shutdown complete")
    
    def handle_import_error(self, error):
        """Handle import errors gracefully"""
        missing_module = str(error).split("'")[1] if "'" in str(error) else "unknown"
        
        print(f"\n❌ Import Error: {error}")
        print(f"\n🔧 Missing module: {missing_module}")
        print(f"\n💡 Solutions:")
        print(f"   1. Install missing dependencies:")
        print(f"      pip install {missing_module}")
        print(f"   2. Check if all files are in correct folders")
        print(f"   3. Verify __init__.py files exist in all folders")
        
        # Try to continue with basic functionality
        print(f"\n🚀 Attempting to continue with basic functionality...")
        self.create_fallback_logger()
        self.create_fallback_config()
    
    def handle_general_error(self, error):
        """Handle general initialization errors"""
        print(f"\n❌ Initialization Error: {error}")
        print(f"\n💡 This might be due to:")
        print(f"   1. Missing dependencies")
        print(f"   2. Incorrect file structure")
        print(f"   3. Permission issues")
        
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    def run(self):
        """Start the bot application"""
        try:
            self.logger.info("Starting GDMO TamerBot v10.0")
            self.root.protocol("WM_DELETE_WINDOW", self.graceful_shutdown)
            
            # Show splash screen
            self.show_splash_screen()
            
            # Start main GUI
            self.root.mainloop()
            
        except KeyboardInterrupt:
            self.logger.info("Interrupted by user")
        except Exception as e:
            self.logger.error(f"Critical error: {e}")
        finally:
            self.graceful_shutdown()
    
    def show_splash_screen(self):
        """Show loading splash screen"""
        splash = tk.Toplevel(self.root)
        splash.title("GDMO TamerBot")
        splash.geometry("400x200")
        splash.configure(bg='#0a0f1a')
        
        # Center the splash screen
        splash.update_idletasks()
        x = (splash.winfo_screenwidth() // 2) - (400 // 2)
        y = (splash.winfo_screenheight() // 2) - (200 // 2)
        splash.geometry(f"400x200+{x}+{y}")
        
        # Remove window decorations
        splash.overrideredirect(True)
        
        # Add content
        tk.Label(splash, text="⚡ GDMO TAMERBOT v10.0 ⚡", 
                font=('Arial Black', 16, 'bold'), 
                fg='#ff7b00', bg='#0a0f1a').pack(pady=30)
        
        tk.Label(splash, text="Advanced Multi-Threading Bot", 
                font=('Arial', 12), 
                fg='#00d4ff', bg='#0a0f1a').pack()
        
        tk.Label(splash, text="Loading modules...", 
                font=('Arial', 10), 
                fg='#ffffff', bg='#0a0f1a').pack(pady=20)
        
        # Progress bar simulation
        progress_frame = tk.Frame(splash, bg='#0a0f1a')
        progress_frame.pack(pady=20)
        
        canvas = tk.Canvas(progress_frame, width=300, height=20, bg='#1a2332', highlightthickness=0)
        canvas.pack()
        
        def animate_progress():
            for i in range(101):
                canvas.delete("progress")
                canvas.create_rectangle(0, 0, i * 3, 20, fill='#ff7b00', tags="progress")
                splash.update()
                if i < 50:
                    threading.Event().wait(0.02)
                else:
                    threading.Event().wait(0.01)
        
        # Run progress animation
        animate_progress()
        
        # Close splash after loading
        splash.after(500, splash.destroy)

def main():
    """Main entry point"""
    try:
        app = TamerBot()
        app.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        input("Press Enter to exit...")
        sys.exit(1)

if __name__ == "__main__":
    main()