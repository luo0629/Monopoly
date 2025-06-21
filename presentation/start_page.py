import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict
from business.models import PlayerType
from business.game_state_manager import GameStateManager
from business.game_manager import GameManager

class StartPage:
    """游戏开始页面 - 简化版本"""
    
    def __init__(self, on_start_game_callback, on_load_game_callback=None):
        self.root = tk.Tk()
        self.root.title("大富翁游戏")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        # 回调函数
        self.on_start_game = on_start_game_callback
        self.on_load_game = on_load_game_callback
        
        # 存档管理器
        from business.game_manager import GameManager
        temp_game_manager = GameManager()
        self.state_manager = GameStateManager(temp_game_manager)
        
        # 创建界面
        self._create_widgets()
        
        # 居中显示窗口
        self._center_window()
        
        # 绑定关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def run(self):
        """运行开始页面"""
        self.root.mainloop()
    
    def _center_window(self):
        """将窗口居中显示"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def _create_widgets(self):
        """创建界面组件"""
        # 主容器
        main_frame = ttk.Frame(self.root, padding=40)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="🎮 大富翁游戏", 
                               font=("Arial", 28, "bold"))
        title_label.pack(pady=(0, 20))
        
        subtitle_label = ttk.Label(main_frame, text="青岛主题大富翁游戏", 
                                  font=("Arial", 14))
        subtitle_label.pack(pady=(0, 50))
        
        # 按钮容器
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)
        
        # 新游戏按钮
        new_game_btn = ttk.Button(button_frame, text="🚀 新游戏", 
                                 command=self._show_new_game_setup,
                                 style="Accent.TButton")
        new_game_btn.pack(pady=10, ipadx=30, ipady=10)
        new_game_btn.configure(width=20)
        
        # 读取存档按钮
        load_game_btn = ttk.Button(button_frame, text="📁 读取存档", 
                                  command=self._show_load_game_dialog)
        load_game_btn.pack(pady=10, ipadx=30, ipady=10)
        load_game_btn.configure(width=20)
        
        # 退出按钮
        exit_btn = ttk.Button(button_frame, text="❌ 退出游戏", 
                             command=self._on_closing)
        exit_btn.pack(pady=(30, 0), ipadx=20, ipady=5)
        exit_btn.configure(width=20)
    
    def _show_new_game_setup(self):
        """显示新游戏设置页面"""
        # 创建新游戏设置窗口
        setup_window = NewGameSetupWindow(self.root, self.on_start_game)
        setup_window.show()
    
    def _show_load_game_dialog(self):
        """显示读取存档对话框"""
        try:
            # 获取存档列表
            saves = self.state_manager.get_save_list(include_auto_saves=False)
            
            if not saves:
                messagebox.showinfo("提示", "暂无可用存档")
                return
            
            # 创建存档选择窗口
            load_window = LoadGameWindow(self.root, saves, self._load_selected_save)
            load_window.show()
            
        except Exception as e:
            messagebox.showerror("错误", f"获取存档列表失败: {e}")
    
    def _load_selected_save(self, save_name):
        """加载选中的存档"""
        if self.on_load_game:
            # 关闭开始页面
            self.root.destroy()
            # 调用加载游戏回调
            self.on_load_game(save_name)
        else:
            messagebox.showerror("错误", "加载游戏功能未配置")
    
    def _on_closing(self):
        """窗口关闭事件"""
        self.root.quit()
        self.root.destroy()
    
    def show(self):
        """显示开始页面"""
        self.root.mainloop()


class NewGameSetupWindow:
    """新游戏设置窗口"""
    
    def __init__(self, parent, on_start_game_callback):
        self.parent = parent
        self.on_start_game = on_start_game_callback
        
        self.window = tk.Toplevel(parent)
        self.window.title("新游戏设置")
        self.window.geometry("700x500")
        self.window.resizable(False, False)
        self.window.transient(parent)
        self.window.grab_set()
        
        # 玩家配置列表
        self.player_configs = []
        
        # 初始金币设置
        self.initial_money_var = tk.IntVar(value=15000)
        
        # 创建界面
        self._create_widgets()
        
        # 居中显示
        self._center_window()
        
        # 绑定关闭事件
        self.window.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _center_window(self):
        """将窗口居中显示"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")
    
    def _create_widgets(self):
        """创建界面组件"""
        # 主容器
        main_frame = ttk.Frame(self.window, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="🎮 新游戏设置", 
                               font=("Arial", 20, "bold"))
        title_label.pack(pady=(0, 20))
        
        # 玩家设置区域
        player_frame = ttk.LabelFrame(main_frame, text="👥 玩家设置", padding=15)
        player_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # 玩家数量设置
        count_frame = ttk.Frame(player_frame)
        count_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(count_frame, text="玩家数量:").pack(side=tk.LEFT)
        self.player_count_var = tk.IntVar(value=2)
        player_count_spinbox = ttk.Spinbox(count_frame, from_=2, to=6, 
                                          textvariable=self.player_count_var,
                                          width=10, command=self._update_player_list)
        player_count_spinbox.pack(side=tk.LEFT, padx=(10, 0))
        
        # 初始金币设置
        money_frame = ttk.Frame(player_frame)
        money_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(money_frame, text="初始金币:").pack(side=tk.LEFT)
        money_spinbox = ttk.Spinbox(money_frame, from_=5000, to=50000, increment=1000,
                                   textvariable=self.initial_money_var, width=10)
        money_spinbox.pack(side=tk.LEFT, padx=(10, 0))
        ttk.Label(money_frame, text="元").pack(side=tk.LEFT, padx=(5, 0))
        
        # 玩家列表容器
        self.players_container = ttk.Frame(player_frame)
        self.players_container.pack(fill=tk.BOTH, expand=True)
        
        # 初始化玩家列表
        self._update_player_list()
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        # 开始游戏按钮
        start_button = ttk.Button(button_frame, text="🚀 开始游戏", 
                                 command=self._start_game,
                                 style="Accent.TButton")
        start_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        # 返回按钮
        back_button = ttk.Button(button_frame, text="⬅️ 返回", 
                                command=self._on_closing)
        back_button.pack(side=tk.RIGHT)
    
    def _update_player_list(self):
        """更新玩家列表"""
        # 清空现有的玩家配置组件
        for widget in self.players_container.winfo_children():
            widget.destroy()
        
        self.player_configs.clear()
        
        # 创建新的玩家配置组件
        player_count = self.player_count_var.get()
        
        for i in range(player_count):
            self._create_player_config(i)
    
    def _create_player_config(self, index):
        """创建单个玩家配置组件"""
        # 玩家配置框架
        player_frame = ttk.Frame(self.players_container)
        player_frame.pack(fill=tk.X, pady=5)
        
        # 玩家标签
        label = ttk.Label(player_frame, text=f"玩家 {index + 1}:", width=8)
        label.pack(side=tk.LEFT)
        
        # 玩家姓名输入
        name_var = tk.StringVar(value=f"玩家{index + 1}")
        name_entry = ttk.Entry(player_frame, textvariable=name_var, width=15)
        name_entry.pack(side=tk.LEFT, padx=(5, 10))
        
        # 玩家类型选择
        type_label = ttk.Label(player_frame, text="类型:")
        type_label.pack(side=tk.LEFT)
        
        type_var = tk.StringVar(value="人类" if index == 0 else "AI")
        type_combo = ttk.Combobox(player_frame, textvariable=type_var, 
                                 values=["人类", "AI"], width=8, state="readonly")
        type_combo.pack(side=tk.LEFT, padx=(5, 10))
        
        # AI难度选择
        difficulty_label = ttk.Label(player_frame, text="难度:")
        difficulty_var = tk.StringVar(value="简单")
        difficulty_combo = ttk.Combobox(player_frame, textvariable=difficulty_var,
                                       values=["简单", "中等", "困难"], width=8, state="readonly")
        
        def on_type_change(*args):
            if type_var.get() == "AI":
                difficulty_label.pack(side=tk.LEFT)
                difficulty_combo.pack(side=tk.LEFT, padx=(5, 0))
            else:
                difficulty_label.pack_forget()
                difficulty_combo.pack_forget()
        
        type_var.trace('w', on_type_change)
        on_type_change()  # 初始化显示状态
        
        # 保存配置
        config = {
            'name_var': name_var,
            'type_var': type_var,
            'difficulty_var': difficulty_var
        }
        self.player_configs.append(config)
    
    def _start_game(self):
        """开始游戏"""
        # 验证玩家配置
        players_data = []
        names_used = set()
        
        for i, config in enumerate(self.player_configs):
            name = config['name_var'].get().strip()
            player_type = config['type_var'].get()
            difficulty = config['difficulty_var'].get()
            
            # 验证玩家姓名
            if not name:
                messagebox.showerror("错误", f"请输入玩家 {i + 1} 的姓名")
                return
            
            if name in names_used:
                messagebox.showerror("错误", f"玩家姓名 '{name}' 重复，请使用不同的姓名")
                return
            
            names_used.add(name)
            
            # 转换玩家类型
            if player_type == "人类":
                player_type_enum = PlayerType.HUMAN
            else:
                player_type_enum = PlayerType.AI
            
            players_data.append({
                'name': name,
                'type': player_type_enum,
                'difficulty': difficulty if player_type == "AI" else None
            })
        
        # 获取初始金币设置
        initial_money = self.initial_money_var.get()
        
        # 关闭设置窗口和主窗口
        self.window.destroy()
        self.parent.destroy()
        
        # 调用回调函数启动游戏
        self.on_start_game(players_data, initial_money)
    
    def _on_closing(self):
        """处理窗口关闭事件"""
        self.window.destroy()
    
    def show(self):
        """显示窗口"""
        self.window.deiconify()
        self.window.lift()
        self.window.focus_force()


class LoadGameWindow:
    """读取存档窗口"""
    
    def __init__(self, parent, saves, on_load_callback):
        self.parent = parent
        self.saves = saves
        self.on_load = on_load_callback
        
        # 获取状态管理器用于删除存档
        from business.game_manager import GameManager
        from business.game_state_manager import GameStateManager
        temp_game_manager = GameManager()
        self.state_manager = GameStateManager(temp_game_manager)
        
        self.window = tk.Toplevel(parent)
        self.window.title("📁 读取存档")
        self.window.geometry("650x500")
        self.window.resizable(False, False)
        self.window.transient(parent)
        self.window.grab_set()
        
        # 设置窗口背景色
        self.window.configure(bg='#f0f0f0')
        
        # 配置样式
        self._configure_styles()
        
        # 创建界面
        self._create_widgets()
        
        # 居中显示
        self._center_window()
        
        # 绑定关闭事件
        self.window.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _center_window(self):
        """将窗口居中显示"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")
    
    def _configure_styles(self):
        """配置界面样式"""
        style = ttk.Style()
        
        # 配置按钮样式
        style.configure('Load.TButton',
                       font=('Microsoft YaHei', 11, 'bold'),
                       foreground='white',
                       background='#4CAF50',
                       borderwidth=0,
                       focuscolor='none',
                       padding=(20, 10))
        
        style.configure('Cancel.TButton',
                       font=('Microsoft YaHei', 11),
                       foreground='#666666',
                       background='#e0e0e0',
                       borderwidth=0,
                       focuscolor='none',
                       padding=(20, 10))
        
        # 配置框架样式
        style.configure('Card.TFrame',
                       background='white',
                       relief='solid',
                       borderwidth=1)
    
    def _create_widgets(self):
        """创建界面组件"""
        # 主容器
        main_frame = tk.Frame(self.window, bg='#f0f0f0', padx=30, pady=30)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题区域
        title_frame = tk.Frame(main_frame, bg='#f0f0f0')
        title_frame.pack(fill=tk.X, pady=(0, 25))
        
        # 标题图标和文字
        title_label = tk.Label(title_frame, 
                              text="📁 选择存档文件", 
                              font=("Microsoft YaHei", 18, "bold"),
                              fg="#2c3e50",
                              bg="#f0f0f0")
        title_label.pack()
        
        # 副标题
        subtitle_label = tk.Label(title_frame,
                                 text="请从下方列表中选择要加载的游戏存档",
                                 font=("Microsoft YaHei", 10),
                                 fg="#7f8c8d",
                                 bg="#f0f0f0")
        subtitle_label.pack(pady=(5, 0))
        
        # 存档列表卡片容器
        card_frame = tk.Frame(main_frame, bg='white', relief='solid', borderwidth=1)
        card_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 25))
        
        # 列表标题
        list_title_frame = tk.Frame(card_frame, bg='#ecf0f1', height=40)
        list_title_frame.pack(fill=tk.X)
        list_title_frame.pack_propagate(False)
        
        list_title_label = tk.Label(list_title_frame,
                                   text="💾 存档列表",
                                   font=("Microsoft YaHei", 12, "bold"),
                                   fg="#34495e",
                                   bg="#ecf0f1")
        list_title_label.pack(pady=10)
        
        # 存档列表容器（带滚动）
        list_container = tk.Frame(card_frame, bg='white', padx=15, pady=15)
        list_container.pack(fill=tk.BOTH, expand=True)
        
        # 创建列表框和滚动条
        self.save_listbox = tk.Listbox(list_container, 
                                      font=("Microsoft YaHei", 11),
                                      bg='white',
                                      fg='#2c3e50',
                                      selectbackground='#3498db',
                                      selectforeground='white',
                                      borderwidth=0,
                                      highlightthickness=1,
                                      highlightcolor='#3498db',
                                      activestyle='none')
        
        scrollbar = ttk.Scrollbar(list_container, orient=tk.VERTICAL, command=self.save_listbox.yview)
        self.save_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.save_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        
        # 填充存档列表
        if not self.saves:
            self.save_listbox.insert(tk.END, "暂无可用存档")
            self.save_listbox.config(state='disabled')
        else:
            for i, save in enumerate(self.saves):
                save_name = save.get('save_name', '未知存档')
                save_date = save.get('save_date', save.get('save_time', '未知时间'))
                # 格式化显示文本
                display_text = f"🎮 {save_name}\n📅 {save_date}"
                self.save_listbox.insert(tk.END, display_text)
                
                # 为奇偶行设置不同背景色（通过选择模拟）
                if i % 2 == 1:
                    self.save_listbox.itemconfig(i, {'bg': '#f8f9fa'})
        
        # 按钮区域
        button_frame = tk.Frame(main_frame, bg='#f0f0f0')
        button_frame.pack(fill=tk.X)
        
        # 按钮容器（居中对齐）
        button_container = tk.Frame(button_frame, bg='#f0f0f0')
        button_container.pack()
        
        # 取消按钮
        cancel_button = tk.Button(button_container, 
                                 text="❌ 取消",
                                 font=("Microsoft YaHei", 11),
                                 fg="#666666",
                                 bg="#e0e0e0",
                                 activebackground="#d0d0d0",
                                 activeforeground="#555555",
                                 borderwidth=0,
                                 padx=20,
                                 pady=12,
                                 cursor="hand2",
                                 command=self._on_closing)
        cancel_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 删除按钮
        delete_button = tk.Button(button_container, 
                                 text="🗑️ 删除存档",
                                 font=("Microsoft YaHei", 11),
                                 fg="white",
                                 bg="#f44336",
                                 activebackground="#d32f2f",
                                 activeforeground="white",
                                 borderwidth=0,
                                 padx=20,
                                 pady=12,
                                 cursor="hand2",
                                 command=self._delete_selected)
        delete_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 加载按钮
        load_button = tk.Button(button_container, 
                               text="📂 加载存档",
                               font=("Microsoft YaHei", 11, "bold"),
                               fg="white",
                               bg="#4CAF50",
                               activebackground="#45a049",
                               activeforeground="white",
                               borderwidth=0,
                               padx=20,
                               pady=12,
                               cursor="hand2",
                               command=self._load_selected)
        load_button.pack(side=tk.LEFT)
        
        # 绑定双击事件
        self.save_listbox.bind('<Double-Button-1>', lambda e: self._load_selected())
        
        # 绑定键盘事件
        self.save_listbox.bind('<Return>', lambda e: self._load_selected())
        self.save_listbox.bind('<Delete>', lambda e: self._delete_selected())
        self.window.bind('<Escape>', lambda e: self._on_closing())
    
    def _load_selected(self):
        """加载选中的存档"""
        if not self.saves:  # 如果没有存档
            messagebox.showinfo("提示", "暂无可用存档")
            return
            
        selection = self.save_listbox.curselection()
        if not selection:
            messagebox.showwarning("⚠️ 警告", "请先选择一个存档文件")
            return
        
        index = selection[0]
        save_data = self.saves[index]
        save_name = save_data.get('save_name', '未知存档')
        
        # 确认对话框
        result = messagebox.askyesno("🎮 确认加载", 
                                   f"确定要加载存档 '{save_name}' 吗？\n\n当前游戏进度将会丢失。")
        if not result:
            return
        
        # 关闭窗口
        self.window.destroy()
        
        # 调用加载回调
        self.on_load(save_name)
    
    def _delete_selected(self):
        """删除选中的存档"""
        if not self.saves:  # 如果没有存档
            messagebox.showinfo("提示", "暂无可用存档")
            return
            
        selection = self.save_listbox.curselection()
        if not selection:
            messagebox.showwarning("⚠️ 警告", "请先选择要删除的存档文件")
            return
        
        index = selection[0]
        save_data = self.saves[index]
        save_name = save_data.get('save_name', '未知存档')
        
        # 确认删除对话框
        result = messagebox.askyesno("🗑️ 确认删除", 
                                   f"确定要删除存档 '{save_name}' 吗？\n\n此操作无法撤销！")
        if not result:
            return
        
        # 执行删除
        if self.state_manager.delete_save(save_name):
            messagebox.showinfo("✅ 删除成功", f"存档 '{save_name}' 已成功删除")
            
            # 刷新存档列表
            self._refresh_save_list()
        else:
            messagebox.showerror("❌ 删除失败", f"删除存档 '{save_name}' 失败，请重试")
    
    def _refresh_save_list(self):
        """刷新存档列表"""
        try:
            # 重新获取存档列表
            from business.game_state_manager import GameStateManager
            from business.game_manager import GameManager
            temp_game_manager = GameManager()
            temp_state_manager = GameStateManager(temp_game_manager)
            self.saves = temp_state_manager.get_save_list()
            
            # 清空列表
            self.save_listbox.delete(0, tk.END)
            
            # 重新填充
            if not self.saves:
                self.save_listbox.insert(tk.END, "暂无可用存档")
                self.save_listbox.config(state='disabled')
            else:
                self.save_listbox.config(state='normal')
                for i, save in enumerate(self.saves):
                    save_name = save.get('save_name', '未知存档')
                    save_date = save.get('save_date', save.get('save_time', '未知时间'))
                    # 格式化显示文本
                    display_text = f"🎮 {save_name}\n📅 {save_date}"
                    self.save_listbox.insert(tk.END, display_text)
                    
                    # 为奇偶行设置不同背景色
                    if i % 2 == 1:
                        self.save_listbox.itemconfig(i, {'bg': '#f8f9fa'})
        except Exception as e:
            messagebox.showerror("错误", f"刷新存档列表失败: {str(e)}")
    
    def _on_closing(self):
        """窗口关闭事件"""
        self.window.destroy()
    
    def show(self):
        """显示窗口"""
        self.window.wait_window()