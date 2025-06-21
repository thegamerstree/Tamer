"""
Main GUI window with the original cool interface
"""

import tkinter as tk
from tkinter import ttk, messagebox
import time
import threading
from typing import Dict, Any

class MainWindow:
    """Main GUI window with all the original features"""
    
    def __init__(self, root, app):
        self.root = root
        self.app = app
        self.logger = app.logger
        
        # Colors from original design
        self.colors = {
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
        }
        
        # Status variables
        self.status_vars = {
            'bot_status': tk.StringVar(value='🔴 Offline'),
            'connection_status': tk.StringVar(value='🌐 Disconnected'),
            'hp_text': tk.StringVar(value='Tamer HP: ?'),
            'ds_text': tk.StringVar(value='Digi-Soul: ?')
        }
        
        # Target variable
        self.target_digimon_name = tk.StringVar(value="")
        
        # Stats display text
        self.last_stats_text = ""
        self.last_dashboard_update = 0
        
        self.build_gui()
        
    def build_gui(self):
        """Build the main GUI interface"""
        self.root.title("⚡ GDMO TamerBot v10.0")
        self.root.geometry("950x850")
        self.root.configure(bg=self.colors['bg'])
        self.root.resizable(False, False)
        
        # Main frame
        main_frame = tk.Frame(self.root, bg=self.colors['bg'])
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Header
        self.create_header(main_frame)
        
        # Control panel
        self.create_control_panel(main_frame)
        
        # Notebook with tabs
        self.create_notebook(main_frame)
        
        # Start update loop
        self.start_gui_updates()
        
    def create_header(self, parent):
        """Create the header section"""
        header = tk.LabelFrame(parent, text="⚡ GDMO TAMERBOT v10.0 ⚡", 
                              font=('Arial Black', 14, 'bold'), 
                              fg='white', bg=self.colors['primary'])
        header.pack(fill='x', pady=(0, 10))
        
    def create_control_panel(self, parent):
        """Create the control panel"""
        control = tk.LabelFrame(parent, text="🎮 Control", 
                               font=('Arial', 11, 'bold'), 
                               fg=self.colors['secondary'], bg=self.colors['bg'])
        control.pack(fill='x', pady=(0, 10))
        
        # Status frame
        status_frame = tk.Frame(control, bg=self.colors['bg'])
        status_frame.pack(fill='x', padx=10, pady=8)
        
        tk.Label(status_frame, text="Status:", font=('Arial', 10, 'bold'), 
                fg=self.colors['text'], bg=self.colors['bg']).grid(row=0, column=0, sticky='w')
        
        self.status_label = tk.Label(status_frame, textvariable=self.status_vars['bot_status'], 
                                    font=('Arial', 10, 'bold'), 
                                    fg=self.colors['danger'], bg=self.colors['bg'])
        self.status_label.grid(row=0, column=1, padx=8, sticky='w')
        
        tk.Label(status_frame, text="Memory:", font=('Arial', 10, 'bold'), 
                fg=self.colors['text'], bg=self.colors['bg']).grid(row=0, column=2, sticky='w', padx=(15, 0))
        
        self.conn_label = tk.Label(status_frame, textvariable=self.status_vars['connection_status'], 
                                  font=('Arial', 10, 'bold'), 
                                  fg=self.colors['danger'], bg=self.colors['bg'])
        self.conn_label.grid(row=0, column=3, padx=8, sticky='w')
        
        # Target frame
        target_frame = tk.Frame(control, bg=self.colors['bg'])
        target_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(target_frame, text="🎯 Target:", font=('Arial', 10, 'bold'), 
                fg=self.colors['text'], bg=self.colors['bg']).pack(side='left')
        
        tk.Entry(target_frame, textvariable=self.target_digimon_name, 
                font=('Arial', 10), width=25, 
                bg=self.colors['card'], fg=self.colors['text']).pack(side='left', padx=8)
        
        # Button frame
        button_frame = tk.Frame(control, bg=self.colors['bg'])
        button_frame.pack(pady=8)
        
        self.start_btn = tk.Button(button_frame, text="🚀 START", command=self.start_bot, 
                                  font=('Arial', 10, 'bold'), 
                                  bg=self.colors['success'], fg='white')
        self.start_btn.pack(side='left', padx=5)
        
        self.stop_btn = tk.Button(button_frame, text="🛑 STOP", command=self.stop_bot, 
                                 state='disabled', font=('Arial', 10, 'bold'), 
                                 bg=self.colors['danger'], fg='white')
        self.stop_btn.pack(side='left', padx=5)
        
        self.pause_btn = tk.Button(button_frame, text="⏸️ PAUSE", command=self.toggle_pause, 
                                  state='disabled', font=('Arial', 10, 'bold'), 
                                  bg=self.colors['secondary'], fg='white')
        self.pause_btn.pack(side='left', padx=5)
        
        tk.Button(button_frame, text="💾", command=self.save_settings, 
                 font=('Arial', 10, 'bold'), 
                 bg=self.colors['primary'], fg='white').pack(side='left', padx=3)
        
    def create_notebook(self, parent):
        """Create the notebook with tabs"""
        # Style the notebook
        style = ttk.Style()
        style.configure('TNotebook', background=self.colors['bg'])
        style.configure('TNotebook.Tab', padding=[12, 6], font=('Arial', 9, 'bold'))
        
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill='both', expand=True)
        
        # Create tabs
        self.create_dashboard_tab()
        self.create_combat_tab()
        self.create_healing_tab()
        self.create_memory_tab()
        self.create_scanner_tab()
        self.create_logs_tab()
        
    def create_dashboard_tab(self):
        """Create the dashboard tab"""
        tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(tab, text="📊 Dashboard")
        
        # Life frame
        life_frame = tk.LabelFrame(tab, text="🏥 Life", 
                                  font=('Arial', 10, 'bold'), 
                                  fg=self.colors['success'], bg=self.colors['bg'])
        life_frame.pack(fill='x', padx=8, pady=8)
        
        # HP frame
        hp_frame = tk.Frame(life_frame, bg=self.colors['bg'])
        hp_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(hp_frame, text="❤️ HP:", font=('Arial', 10, 'bold'), 
                fg='#ff4757', bg=self.colors['bg']).pack(side='left')
        
        self.hp_progress = ttk.Progressbar(hp_frame, length=250, mode='determinate')
        self.hp_progress.pack(side='left', padx=10, fill='x', expand=True)
        
        tk.Label(hp_frame, textvariable=self.status_vars['hp_text'], 
                font=('Arial', 9), fg=self.colors['text'], 
                bg=self.colors['bg']).pack(side='left', padx=5)
        
        # DS frame
        ds_frame = tk.Frame(life_frame, bg=self.colors['bg'])
        ds_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(ds_frame, text="💙 DS:", font=('Arial', 10, 'bold'), 
                fg='#3742fa', bg=self.colors['bg']).pack(side='left')
        
        self.ds_progress = ttk.Progressbar(ds_frame, length=250, mode='determinate')
        self.ds_progress.pack(side='left', padx=10, fill='x', expand=True)
        
        tk.Label(ds_frame, textvariable=self.status_vars['ds_text'], 
                font=('Arial', 9), fg=self.colors['text'], 
                bg=self.colors['bg']).pack(side='left', padx=5)
        
        # Stats display
        self.stats_display = tk.Text(tab, height=15, font=('Consolas', 9), 
                                    bg=self.colors['card'], fg=self.colors['text'])
        self.stats_display.pack(fill='both', expand=True, padx=8, pady=8)
        
    def create_combat_tab(self):
        """Create the combat configuration tab"""
        tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(tab, text="⚔️ Combat")
        
        config_frame = tk.Frame(tab, bg=self.colors['bg'])
        config_frame.pack(padx=15, pady=15)
        
        # Create combat configuration widgets
        combat_labels = [
            ("Attack Key:", "attack_key"),
            ("Pickup Key:", "pickup_key"), 
            ("Cooldown:", "attack_cooldown"),
            ("Avoid List:", "avoid_digimon"),
            ("Target Priority:", "target_priority")
        ]
        
        self.combat_vars = {}
        for i, (label, var_name) in enumerate(combat_labels):
            tk.Label(config_frame, text=label, font=('Arial', 9), 
                    fg=self.colors['text'], bg=self.colors['bg']).grid(row=i, column=0, sticky='w', pady=2)
            
            self.combat_vars[var_name] = tk.StringVar(value="1" if "key" in var_name else "")
            tk.Entry(config_frame, textvariable=self.combat_vars[var_name], 
                    width=15, font=('Arial', 9), 
                    bg=self.colors['card'], fg=self.colors['text']).grid(row=i, column=1, padx=8, pady=2)
            
        # Combat options
        options_frame = tk.Frame(tab, bg=self.colors['bg'])
        options_frame.pack(padx=15, pady=10)
        
        self.combat_options = {}
        options = [
            ("🧠 Memory", "use_memory"),
            ("🚶 Auto Move", "auto_move"), 
            ("💎 Auto Pickup", "auto_pickup"),
            ("🎯 Target Seeking", "target_seeking"),
            ("🏃 Smooth Hunting", "smooth_hunting")
        ]
        
        for text, var_name in options:
            self.combat_options[var_name] = tk.BooleanVar(value=True)
            tk.Checkbutton(options_frame, text=text, variable=self.combat_options[var_name], 
                          font=('Arial', 9), fg=self.colors['text'], 
                          bg=self.colors['bg'], selectcolor=self.colors['primary']).pack(anchor='w', pady=1)
        
    def create_healing_tab(self):
        """Create the healing configuration tab"""
        tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(tab, text="🏥 Healing")
        
        # Healing items frame
        items_frame = tk.LabelFrame(tab, text="💊 Healing Items", 
                                   font=('Arial', 10, 'bold'), 
                                   fg=self.colors['danger'], bg=self.colors['bg'])
        items_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(items_frame, text="Item | Key | Threshold | Enabled", 
                font=('Arial', 9, 'bold'), fg=self.colors['text'], 
                bg=self.colors['bg']).pack(pady=5)
        
        # Healing items
        self.healing_items = {}
        healing_items = [
            ("Recovery Floppy", "1", 70),
            ("Hi-Recovery Disk", "2", 50),
            ("Mega Recovery HD", "3", 25),
            ("Energy Floppy", "4", 70),
            ("Hi-Energy Disk", "5", 50),
            ("Mega Energy HD", "6", 25)
        ]
        
        for name, default_key, default_threshold in healing_items:
            item_frame = tk.Frame(items_frame, bg=self.colors['bg'])
            item_frame.pack(fill='x', padx=10, pady=2)
            
            color = self.colors['danger'] if 'Recovery' in name else self.colors['secondary']
            
            tk.Label(item_frame, text=name[:15], width=15, 
                    font=('Arial', 8), fg=color, bg=self.colors['bg']).pack(side='left')
            
            self.healing_items[name] = {
                'key': tk.StringVar(value=default_key),
                'threshold': tk.IntVar(value=default_threshold),
                'enabled': tk.BooleanVar(value=True)
            }
            
            tk.Entry(item_frame, textvariable=self.healing_items[name]['key'], 
                    width=3, font=('Arial', 8), 
                    bg=self.colors['card'], fg=self.colors['text']).pack(side='left', padx=5)
            
            tk.Entry(item_frame, textvariable=self.healing_items[name]['threshold'], 
                    width=3, font=('Arial', 8), 
                    bg=self.colors['card'], fg=self.colors['text']).pack(side='left', padx=5)
            
            tk.Checkbutton(item_frame, variable=self.healing_items[name]['enabled'], 
                          bg=self.colors['bg'], selectcolor=self.colors['success']).pack(side='left', padx=5)
        
        # Healing status
        status_frame = tk.LabelFrame(tab, text="📊 Status", 
                                    font=('Arial', 10, 'bold'), 
                                    fg=self.colors['primary'], bg=self.colors['bg'])
        status_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.healing_status_display = tk.Text(status_frame, height=8, 
                                             font=('Consolas', 8), 
                                             bg=self.colors['card'], fg=self.colors['text'])
        self.healing_status_display.pack(fill='both', expand=True, padx=10, pady=10)
        
    def create_memory_tab(self):
        """Create the memory tab"""
        tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(tab, text="🧠 Memory")
        
        # Memory configuration
        addr_frame = tk.Frame(tab, bg=self.colors['bg'])
        addr_frame.pack(padx=15, pady=15)
        
        tk.Label(addr_frame, text="Base Pointer:", font=('Arial', 10, 'bold'), 
                fg=self.colors['text'], bg=self.colors['bg']).pack(side='left')
        
        self.memory_offset = tk.StringVar(value="0x0072FF80")
        tk.Entry(addr_frame, textvariable=self.memory_offset, width=20, 
                font=('Consolas', 9), bg=self.colors['card'], 
                fg=self.colors['text']).pack(side='left', padx=10)
        
        # Memory buttons
        btn_frame = tk.Frame(tab, bg=self.colors['bg'])
        btn_frame.pack(pady=10)
        
        buttons = [
            ("🔗 Connect", self.connect_memory, self.colors['success']),
            ("✅ Apply", self.update_memory_addresses, self.colors['secondary']),
            ("🧪 Test", self.test_memory, self.colors['primary'])
        ]
        
        for text, command, color in buttons:
            tk.Button(btn_frame, text=text, command=command, 
                     font=('Arial', 9, 'bold'), bg=color, fg='white').pack(side='left', padx=5)
        
    def create_scanner_tab(self):
        """Create the scanner tab"""
        tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(tab, text="🔍 Scanner")
        
        self.detection_status = tk.StringVar(value="❌ Scanner Offline")
        tk.Label(tab, textvariable=self.detection_status, 
                font=('Arial', 11, 'bold'), fg=self.colors['danger'], 
                bg=self.colors['bg']).pack(pady=8)
        
        self.active_window_var = tk.StringVar(value="No GDMO window selected")
        tk.Label(tab, textvariable=self.active_window_var, 
                font=('Arial', 9), fg=self.colors['secondary'], 
                bg=self.colors['bg']).pack(pady=5)
        
        # Window list
        self.window_listbox = tk.Listbox(tab, height=6, font=('Arial', 9), 
                                        bg=self.colors['card'], fg=self.colors['text'])
        self.window_listbox.pack(fill='both', expand=True, padx=8, pady=8)
        
        # Scanner buttons
        btn_frame = tk.Frame(tab, bg=self.colors['bg'])
        btn_frame.pack(pady=8)
        
        scanner_buttons = [
            ("🔄 Auto", self.auto_detect, self.colors['success']),
            ("👆 Manual", self.manual_detection_setup, self.colors['secondary']),
            ("✅ Select", self.select_window, self.colors['primary'])
        ]
        
        for text, command, color in scanner_buttons:
            tk.Button(btn_frame, text=text, command=command, 
                     font=('Arial', 9, 'bold'), bg=color, fg='white').pack(side='left', padx=5)
        
    def create_logs_tab(self):
        """Create the logs tab"""
        tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(tab, text="📜 Logs")
        
        # Log controls
        controls_frame = tk.Frame(tab, bg=self.colors['bg'])
        controls_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Button(controls_frame, text="🗑️ Clear", command=self.clear_logs, 
                 font=('Arial', 9, 'bold'), bg=self.colors['danger'], 
                 fg='white').pack(side='left', padx=5)
        
        # Log display
        self.log_display = tk.Text(tab, font=('Consolas', 8), wrap='word', 
                                  bg=self.colors['card'], fg=self.colors['text'])
        self.log_display.pack(fill='both', expand=True, padx=10, pady=5)
        
    # Button event handlers
    def start_bot(self):
        """Start the bot"""
        try:
            if hasattr(self.app, 'bot_engine') and self.app.bot_engine:
                success = self.app.bot_engine.start()
                if success:
                    self.status_vars['bot_status'].set('🟢 Running')
                    self.status_label.config(fg=self.colors['success'])
                    self.start_btn.config(state='disabled')
                    self.stop_btn.config(state='normal')
                    self.pause_btn.config(state='normal')
                    self.log_message("Bot started successfully!")
                else:
                    self.log_message("Failed to start bot engine")
            else:
                self.log_message("Bot engine not available - running in GUI-only mode")
                # Update GUI to show "running" even in GUI-only mode
                self.status_vars['bot_status'].set('🟡 GUI Only')
                self.status_label.config(fg=self.colors['warning'])
                self.start_btn.config(state='disabled')
                self.stop_btn.config(state='normal')
        except Exception as e:
            self.log_message(f"Error starting bot: {e}")
            
    def stop_bot(self):
        """Stop the bot"""
        try:
            if hasattr(self.app, 'bot_engine') and self.app.bot_engine:
                self.app.bot_engine.stop()
                
            self.status_vars['bot_status'].set('🔴 Offline')
            self.status_label.config(fg=self.colors['danger'])
            self.start_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
            self.pause_btn.config(state='disabled')
            self.log_message("Bot stopped")
        except Exception as e:
            self.log_message(f"Error stopping bot: {e}")
        
    def toggle_pause(self):
        """Toggle pause state"""
        try:
            if hasattr(self.app, 'bot_engine') and self.app.bot_engine:
                if hasattr(self.app.bot_engine, 'paused') and self.app.bot_engine.paused:
                    self.app.bot_engine.resume()
                    self.status_vars['bot_status'].set('🟢 Running')
                    self.status_label.config(fg=self.colors['success'])
                    self.pause_btn.config(text='⏸️ PAUSE')
                    self.log_message("Bot resumed")
                else:
                    self.app.bot_engine.pause()
                    self.status_vars['bot_status'].set('🟡 Paused')
                    self.status_label.config(fg=self.colors['warning'])
                    self.pause_btn.config(text='▶️ RESUME')
                    self.log_message("Bot paused")
            else:
                self.log_message("Bot engine not available for pause/resume")
        except Exception as e:
            self.log_message(f"Error toggling pause: {e}")
        
    def save_settings(self):
        """Save current settings"""
        try:
            if hasattr(self.app, 'config_manager') and self.app.config_manager:
                # Save combat settings
                if hasattr(self.app.config_manager, 'combat'):
                    for var_name, tk_var in self.combat_vars.items():
                        if hasattr(self.app.config_manager.combat, var_name):
                            setattr(self.app.config_manager.combat, var_name, tk_var.get())
                
                # Save healing settings
                if hasattr(self.app.config_manager, 'healing_items'):
                    for item_name, item_vars in self.healing_items.items():
                        if item_name in self.app.config_manager.healing_items:
                            item_config = self.app.config_manager.healing_items[item_name]
                            item_config.key = item_vars['key'].get()
                            item_config.threshold = item_vars['threshold'].get()
                            item_config.enabled = item_vars['enabled'].get()
                
                # Save target name
                # Store target name somewhere accessible
                
                self.app.config_manager.save_all_configs()
                self.log_message("✅ Settings saved successfully!")
            else:
                self.log_message("❌ Config manager not available")
        except Exception as e:
            self.log_message(f"❌ Failed to save settings: {e}")
            
    # Memory tab handlers
    def connect_memory(self):
        """Connect to memory"""
        try:
            self.log_message("🔗 Attempting memory connection...")
            self.log_message(f"🔍 Debug: bot_engine exists: {hasattr(self.app, 'bot_engine')}")
            self.log_message(f"🔍 Debug: bot_engine is not None: {self.app.bot_engine is not None}")
            
            if hasattr(self.app, 'bot_engine') and self.app.bot_engine is not None:
                self.log_message(f"🔍 Debug: bot_engine has memory: {hasattr(self.app.bot_engine, 'memory')}")
                self.log_message(f"🔍 Debug: memory is not None: {self.app.bot_engine.memory is not None}")
                self.log_message(f"🔍 Debug: memory type: {type(self.app.bot_engine.memory)}")
                
                if hasattr(self.app.bot_engine, 'memory') and self.app.bot_engine.memory is not None:
                    success = self.app.bot_engine.memory.connect()
                    if success:
                        self.status_vars['connection_status'].set('🌍 Connected')
                        self.conn_label.config(fg=self.colors['success'])
                        self.log_message("✅ Memory connected successfully!")
                    else:
                        self.status_vars['connection_status'].set('🌐 Failed')
                        self.conn_label.config(fg=self.colors['danger'])
                        self.log_message("❌ Memory connection failed")
                else:
                    self.log_message("❌ Memory system not available")
            else:
                self.log_message("❌ Bot engine not available")
                self.log_message("💡 Try restarting the application")
        except Exception as e:
            self.log_message(f"❌ Memory connection error: {e}")
            import traceback
            self.log_message(f"🔍 Debug traceback: {traceback.format_exc()}")
        
    def update_memory_addresses(self):
        """Update memory addresses"""
        try:
            new_offset = self.memory_offset.get()
            self.log_message(f"📝 Updating memory offset to: {new_offset}")
            
            if hasattr(self.app, 'bot_engine') and self.app.bot_engine is not None:
                if hasattr(self.app.bot_engine, 'memory') and self.app.bot_engine.memory is not None:
                    self.app.bot_engine.memory.update_base_address(new_offset)
                    self.log_message("✅ Memory addresses updated")
                else:
                    self.log_message("❌ Memory system not available")
            else:
                self.log_message("❌ Bot engine not available")
        except Exception as e:
            self.log_message(f"❌ Failed to update memory addresses: {e}")
        
    def test_memory(self):
        """Test memory connection"""
        try:
            self.log_message("🧪 Testing memory connection...")
            
            if hasattr(self.app, 'bot_engine') and self.app.bot_engine is not None:
                if hasattr(self.app.bot_engine, 'memory') and self.app.bot_engine.memory is not None:
                    success, info = self.app.bot_engine.memory.test_connection()
                    if success:
                        msg = f"✅ Memory Test Successful\n"
                        for key, value in info.items():
                            msg += f"{key}: {value}\n"
                        messagebox.showinfo("Memory Test", msg)
                        self.log_message("✅ Memory test passed!")
                    else:
                        error_msg = info.get('error', 'Unknown error')
                        messagebox.showerror("Memory Test", f"❌ Memory test failed:\n{error_msg}")
                        self.log_message(f"❌ Memory test failed: {error_msg}")
                else:
                    self.log_message("❌ Memory system not available")
                    messagebox.showwarning("Memory Test", "Memory system not available")
            else:
                self.log_message("❌ Bot engine not available")
                messagebox.showwarning("Memory Test", "Bot engine not available")
        except Exception as e:
            self.log_message(f"❌ Memory test error: {e}")
            messagebox.showerror("Memory Test", f"Error: {e}")

    # Scanner tab handlers  
    def auto_detect(self):
        """Auto detect game window"""
        try:
            self.log_message("🔍 Auto-detecting GDMO windows...")
            
            if hasattr(self.app, 'bot_engine') and self.app.bot_engine:
                if hasattr(self.app.bot_engine, 'detector'):
                    success, windows = self.app.bot_engine.detector.setup_game_window()
                    
                    # Clear and populate window list
                    self.window_listbox.delete(0, tk.END)
                    for title, rect, proc_name in windows:
                        display_text = f"{title[:30]} | {proc_name}"
                        self.window_listbox.insert(tk.END, display_text)
                    
                    if success:
                        self.detection_status.set("✅ Scanner Online")
                        self.active_window_var.set(f"🎮 {windows[0][0][:40]}" if windows else "No window")
                        self.log_message(f"✅ Found {len(windows)} GDMO window(s)")
                    else:
                        self.detection_status.set("❌ No Windows Found")
                        self.active_window_var.set("❌ No GDMO windows detected")
                        self.log_message("❌ No GDMO windows found")
                else:
                    self.log_message("❌ Detection system not available")
            else:
                self.log_message("❌ Bot engine not available")
        except Exception as e:
            self.log_message(f"❌ Auto-detection error: {e}")
        
    def manual_detection_setup(self):
        """Setup manual detection"""
        try:
            self.log_message("👆 Manual detection: Click GDMO window in 5 seconds...")
            
            if hasattr(self.app, 'bot_engine') and self.app.bot_engine:
                if hasattr(self.app.bot_engine, 'detector'):
                    # Schedule the manual detection
                    self.root.after(5000, self.finalize_manual_setup)
                else:
                    self.log_message("❌ Detection system not available")
            else:
                self.log_message("❌ Bot engine not available")
        except Exception as e:
            self.log_message(f"❌ Manual detection error: {e}")
    
    def finalize_manual_setup(self):
        """Finalize manual window selection"""
        try:
            import win32gui
            hwnd = win32gui.GetForegroundWindow()
            if hwnd:
                if hasattr(self.app, 'bot_engine') and self.app.bot_engine:
                    if hasattr(self.app.bot_engine, 'detector'):
                        success, title = self.app.bot_engine.detector.set_game_window_by_hwnd(hwnd)
                        if success:
                            self.detection_status.set("✅ Scanner Online")
                            self.active_window_var.set(f"🎮 {title[:40]}")
                            self.log_message(f"✅ Manual setup successful: {title[:25]}")
                            # Refresh the auto-detection to show the window in list
                            self.auto_detect()
                        else:
                            self.detection_status.set("❌ Invalid Window")
                            self.log_message("❌ Manual setup failed - invalid window")
        except Exception as e:
            self.log_message(f"❌ Manual setup error: {e}")
        
    def select_window(self):
        """Select game window from list"""
        try:
            selection = self.window_listbox.curselection()
            if not selection:
                self.log_message("❌ No window selected from list")
                return
            
            index = selection[0]
            self.log_message(f"📱 Selecting window #{index + 1}")
            
            if hasattr(self.app, 'bot_engine') and self.app.bot_engine:
                if hasattr(self.app.bot_engine, 'detector'):
                    if hasattr(self.app.bot_engine.detector, 'detected_windows'):
                        if index < len(self.app.bot_engine.detector.detected_windows):
                            hwnd, title, rect, proc_name = self.app.bot_engine.detector.detected_windows[index]
                            success, selected_title = self.app.bot_engine.detector.set_game_window_by_hwnd(hwnd)
                            if success:
                                self.detection_status.set("✅ Scanner Online")
                                self.active_window_var.set(f"🎮 {selected_title[:40]}")
                                self.log_message(f"✅ Selected: {selected_title[:25]}")
                            else:
                                self.log_message("❌ Window selection failed")
                        else:
                            self.log_message(f"❌ Invalid window index: {index}")
                    else:
                        self.log_message("❌ No detected windows available")
                else:
                    self.log_message("❌ Detection system not available")
            else:
                self.log_message("❌ Bot engine not available")
        except Exception as e:
            self.log_message(f"❌ Window selection error: {e}")
        
    def clear_logs(self):
        """Clear the log display"""
        self.log_display.delete(1.0, tk.END)
        self.log_message("🗑️ Logs cleared")
    
    def log_message(self, message):
        """Add message to log display"""
        try:
            timestamp = time.strftime("[%H:%M:%S]")
            log_entry = f"{timestamp} {message}\n"
            
            self.log_display.config(state='normal')
            self.log_display.insert('end', log_entry)
            self.log_display.see('end')
            self.log_display.config(state='disabled')
            
            # Also log to main app if available
            if hasattr(self.app, 'log_message'):
                self.app.log_message(message)
        except Exception as e:
            print(f"Log error: {e}")
            print(f"{time.strftime('[%H:%M:%S]')} {message}")
        
    def start_gui_updates(self):
        """Start the GUI update loop"""
        self.update_dashboard()
        self.root.after(500, self.start_gui_updates)  # Update every 500ms
        
    def update_dashboard(self):
        """Update the dashboard with current stats"""
        try:
            # Update progress bars
            self.hp_progress['value'] = 75  # Example values
            self.ds_progress['value'] = 85
            
            # Update stats text
            uptime = time.strftime("%H:%M:%S", time.gmtime(time.time() - getattr(self.app, 'start_time', time.time())))
            
            stats_text = f"""⚡ TAMERBOT v10.0 ⚡
{'='*45}
Uptime: {uptime}
Target: {self.target_digimon_name.get() or 'Any Digimon'}
State: READY
{'='*45}
⚔️ COMBAT
Battles: 0 | Skills: 0
💊 SUPPORT  
Heals: 0 | Pickups: 0 | Moves: 0
{'='*45}
🎯 Last: None
{'='*45}
❤️ {self.status_vars['hp_text'].get()}
💙 {self.status_vars['ds_text'].get()}
{'='*45}
Memory: {self.status_vars['connection_status'].get()}"""
            
            if stats_text != self.last_stats_text:
                self.stats_display.delete(1.0, tk.END)
                self.stats_display.insert(1.0, stats_text)
                self.last_stats_text = stats_text
                
        except Exception as e:
            pass  # Ignore update errors