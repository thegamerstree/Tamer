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
        # if not is_admin():
        #     print("🔐 Administrator privileges required!")
        #     print("🚀 Attempting to restart with admin privileges...")
        #     print("💡 You may see a UAC prompt - click 'Yes' to continue")
        #     time.sleep(2)  # Give user time to read the message
        #     run_as_admin()
        
        # Import modules only after admin check and path setup
        self.import_modules()
        self.initialize_components()
    
    def import_modules(self):
        """Import all required modules"""
        print("📦 Loading modules...")
        
        # Core modules
        from utils.logger import Logger
        self.logger = Logger()
        self.logger.info("Logger initialized")
        
        from config.settings import ConfigManager
        self.config_manager = ConfigManager()
        self.logger.info("Configuration manager loaded")
        
        from core.bot_engine import BotEngine
        self.bot_engine_class = BotEngine
        self.logger.info("Bot engine loaded")

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
                # If the main bot engine fails, we might want to exit or show an error.
                # For now, we'll let it proceed, and setup_gui will handle if bot_engine is None.
                self.bot_engine = None
        else:
            # This case should ideally not be reached if imports are guaranteed.
            self.logger.error("Bot engine class not available after imports.")
            self.bot_engine = None
        
        # NOW setup GUI with working bot_engine
        self.setup_gui()
        
        # Setup signal handlers
        self.setup_signal_handlers()
        
        self.logger.info("TamerBot v10.0 initialized successfully")

    def setup_gui(self):
        """Setup the main GUI"""
        # Try to import custom GUI
        from gui.main_window import MainWindow
        # Pass the app reference so GUI can access bot_engine
        self.gui = MainWindow(self.root, self)
        self.logger.info("Custom GUI loaded successfully")

    def start_bot(self):
        """Start the bot"""
        try:
            if hasattr(self, 'bot_engine') and self.bot_engine:
                success = self.bot_engine.start()
                if success:
                    # GUI should observe bot_engine state and update itself
                    self.logger.info("Bot started successfully via TamerBot class!")
                else:
                    self.logger.error("Failed to start bot engine via TamerBot class")
            else:
                self.logger.error("Bot engine not available - cannot start")
        except Exception as e:
            self.logger.error(f"Error starting bot: {e}")
    
    def stop_bot(self):
        """Stop the bot"""
        try:
            if hasattr(self, 'bot_engine') and self.bot_engine:
                self.bot_engine.stop()
            # GUI should observe bot_engine state and update itself
            self.logger.info("Bot stopped via TamerBot class")
        except Exception as e:
            self.logger.error(f"Error stopping bot: {e}")

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