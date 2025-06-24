import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
import time
from typing import List, Dict, Any, Optional
from PIL import Image, ImageTk
import math

from BLL.game_manager import GameManager
from Model.models import Player, PlayerType, GameState, CellType
from BLL.events import EventObserver

class GameGUI(EventObserver):
    """游戏主界面"""
    
    def __init__(self, players_data=None, initial_money=15000):
        self.root = tk.Tk()
        self.root.title("大富翁游戏")
        self.root.geometry("1200x800")
        self.root.resizable(True, True)
        
        # 玩家配置数据
        self.players_data = players_data or []
        # 初始金币设置
        self.initial_money = initial_money
        
        # 游戏管理器
        self.game_manager = GameManager()
        self.game_manager.attach(self)  # 注册为观察者
        
        # 界面变量
        self.canvas_size = 800  # 增加画布大小以容纳所有格子
        self.cell_size = 72     # 适当减小格子大小以优化布局
        self.player_colors = ['red', 'blue', 'green', 'yellow', 'purple', 'orange']
        self.player_positions = {}  # 玩家在界面上的位置
        
        # 创建界面
        self._create_widgets()
        self._create_menu()
        
        # 如果有玩家数据，自动开始游戏
        if self.players_data:
            self.root.after(100, self._auto_start_game)
        
        # 绑定事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 游戏菜单
        game_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="游戏", menu=game_menu)
        game_menu.add_command(label="新游戏", command=self._new_game)
        game_menu.add_command(label="保存游戏", command=self._save_game)
        game_menu.add_command(label="加载游戏", command=self._load_game)
        game_menu.add_separator()
        game_menu.add_command(label="退出", command=self._on_closing)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="游戏规则", command=self._show_rules)
        help_menu.add_command(label="关于", command=self._show_about)
    
    def _create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左侧游戏板
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 游戏板画布
        self.canvas = tk.Canvas(left_frame, width=self.canvas_size, height=self.canvas_size, 
                               bg='lightgreen', relief=tk.RAISED, borderwidth=2)
        self.canvas.pack(pady=10)
        
        # 移除控制按钮框架（按钮已移动到右侧面板）
        
        # 右侧信息面板 - 增加宽度以容纳完整的玩家信息
        right_frame = ttk.Frame(main_frame, width=400)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        right_frame.pack_propagate(False)
        
        # 玩家信息
        self._create_player_info_panel(right_frame)
        
        # 游戏信息
        self._create_game_info_panel(right_frame)
        
        # 控制按钮面板
        self._create_control_panel(right_frame)
        
        # 日志面板
        self._create_log_panel(right_frame)
        
        # 初始化游戏板
        self._draw_board()
    
    def _create_control_panel(self, parent):
        """创建控制按钮面板"""
        control_frame = ttk.LabelFrame(parent, text="🎮 游戏控制", padding=10)
        control_frame.pack(fill=tk.X, pady=5)
        
        # 创建按钮容器 - 使用网格布局
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X)
        
        # 骰子按钮
        self.roll_button = ttk.Button(button_frame, text="🎲 投掷骰子", 
                                     command=self._roll_dice, state=tk.DISABLED)
        self.roll_button.pack(fill=tk.X, pady=2)
        
        # 购买按钮
        self.buy_button = ttk.Button(button_frame, text="🏠 购买房产", 
                                    command=self._buy_property, state=tk.DISABLED)
        self.buy_button.pack(fill=tk.X, pady=2)
        
        # 升级按钮
        self.upgrade_button = ttk.Button(button_frame, text="⬆️ 升级房产", 
                                        command=self._upgrade_property, state=tk.DISABLED)
        self.upgrade_button.pack(fill=tk.X, pady=2)
        
        # 结束回合按钮
        self.end_turn_button = ttk.Button(button_frame, text="✅ 结束回合", 
                                         command=self._end_turn, state=tk.DISABLED)
        self.end_turn_button.pack(fill=tk.X, pady=2)
        
        # 撤销/重做按钮框架
        undo_redo_frame = ttk.Frame(button_frame)
        undo_redo_frame.pack(fill=tk.X, pady=2)
        
        # 撤销按钮
        self.undo_button = ttk.Button(undo_redo_frame, text="↶ 撤销", 
                                     command=self._undo_action, state=tk.DISABLED)
        self.undo_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 1))
        
        # 重做按钮
        self.redo_button = ttk.Button(undo_redo_frame, text="↷ 重做", 
                                     command=self._redo_action, state=tk.DISABLED)
        self.redo_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(1, 0))
    
    def _create_player_info_panel(self, parent):
        """创建玩家信息面板"""
        player_frame = ttk.LabelFrame(parent, text="🎮 玩家信息", padding=10)
        player_frame.pack(fill=tk.X, pady=5)
        
        # 创建玩家列表容器
        tree_frame = ttk.Frame(player_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 玩家列表 - 增强样式，设置最小宽度
        self.player_tree = ttk.Treeview(tree_frame, columns=('money', 'properties', 'position'), 
                                       show='tree headings', height=6)
        # 设置Treeview的最小宽度以确保所有列都能完整显示
        self.player_tree.configure(selectmode='extended')
        
        # 设置列标题和样式
        self.player_tree.heading('#0', text='👤 玩家', anchor='w')
        self.player_tree.heading('money', text='💰 金钱', anchor='center')
        self.player_tree.heading('properties', text='🏠 房产', anchor='center')
        self.player_tree.heading('position', text='📍 位置', anchor='center')
        
        # 优化列宽 - 增加金钱列宽度以显示完整信息
        self.player_tree.column('#0', width=80, minwidth=70)
        self.player_tree.column('money', width=100, minwidth=90, anchor='center')
        self.player_tree.column('properties', width=60, minwidth=50, anchor='center')
        self.player_tree.column('position', width=100, minwidth=80, anchor='center')
        
        # 添加滚动条
        tree_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.player_tree.yview)
        self.player_tree.configure(yscrollcommand=tree_scrollbar.set)
        
        self.player_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 添加玩家按钮 - 改进布局
        button_frame = ttk.Frame(player_frame)
        button_frame.pack(fill=tk.X, pady=(5, 0))
        
        # 游戏控制按钮已移至开始页面
        # 此处保留其他游戏控制功能的扩展空间
    
    def _create_game_info_panel(self, parent):
        """创建游戏信息面板"""
        info_frame = ttk.LabelFrame(parent, text="📊 游戏信息", padding=10)
        info_frame.pack(fill=tk.X, pady=5)
        
        # 创建信息网格布局
        info_grid = ttk.Frame(info_frame)
        info_grid.pack(fill=tk.X)
        
        # 当前玩家信息 - 突出显示
        current_player_frame = ttk.Frame(info_grid, relief='solid', borderwidth=1)
        current_player_frame.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Label(current_player_frame, text="🎯 当前玩家", 
                 font=('微软雅黑', 9, 'bold')).pack(anchor=tk.W, padx=8, pady=(5, 2))
        self.current_player_label = ttk.Label(current_player_frame, text="无", 
                                            font=('微软雅黑', 10), foreground='#2E8B57')
        self.current_player_label.pack(anchor=tk.W, padx=15, pady=(0, 5))
        
        # 游戏状态信息
        status_frame = ttk.Frame(info_grid)
        status_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 左列
        left_col = ttk.Frame(status_frame)
        left_col.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(left_col, text="🔄 回合数:", font=('微软雅黑', 8)).pack(anchor=tk.W, pady=1)
        self.turn_label = ttk.Label(left_col, text="0", font=('微软雅黑', 9, 'bold'), 
                                   foreground='#4169E1')
        self.turn_label.pack(anchor=tk.W, padx=10, pady=(0, 5))
        
        ttk.Label(left_col, text="🎲 骰子:", font=('微软雅黑', 8)).pack(anchor=tk.W, pady=1)
        self.dice_label = ttk.Label(left_col, text="-", font=('微软雅黑', 9, 'bold'), 
                                   foreground='#FF6347')
        self.dice_label.pack(anchor=tk.W, padx=10)
        
        # 右列
        right_col = ttk.Frame(status_frame)
        right_col.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        ttk.Label(right_col, text="📍 当前位置:", font=('微软雅黑', 8)).pack(anchor=tk.W, pady=1)
        self.position_label = ttk.Label(right_col, text="-", font=('微软雅黑', 9, 'bold'), 
                                       foreground='#8A2BE2')
        self.position_label.pack(anchor=tk.W, padx=10, pady=(0, 5))
        
        # 游戏状态指示器
        ttk.Label(right_col, text="⚡ 状态:", font=('微软雅黑', 8)).pack(anchor=tk.W, pady=1)
        self.game_status_label = ttk.Label(right_col, text="等待开始", font=('微软雅黑', 9, 'bold'), 
                                          foreground='#FF8C00')
        self.game_status_label.pack(anchor=tk.W, padx=10)
    
    def _create_log_panel(self, parent):
        """创建日志面板"""
        log_frame = ttk.LabelFrame(parent, text="📝 游戏日志", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 日志控制栏
        control_frame = ttk.Frame(log_frame)
        control_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 日志级别过滤
        ttk.Label(control_frame, text="显示:", font=('微软雅黑', 8)).pack(side=tk.LEFT, padx=(0, 5))
        
        self.log_filter_var = tk.StringVar(value="全部")
        filter_combo = ttk.Combobox(control_frame, textvariable=self.log_filter_var, 
                                   values=["全部", "重要", "交易", "移动", "系统"], 
                                   width=8, state="readonly")
        filter_combo.pack(side=tk.LEFT, padx=(0, 10))
        filter_combo.bind('<<ComboboxSelected>>', self._filter_logs)
        
        # 清空日志按钮
        clear_btn = ttk.Button(control_frame, text="🗑️ 清空", width=8,
                              command=self._clear_logs)
        clear_btn.pack(side=tk.RIGHT, padx=(5, 5))
        
        # 导出日志按钮
        export_btn = ttk.Button(control_frame, text="💾 导出", width=8,
                               command=self._export_logs)
        export_btn.pack(side=tk.RIGHT)
        
        # 创建文本框和滚动条
        text_frame = ttk.Frame(log_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(text_frame, height=12, state=tk.DISABLED, wrap=tk.WORD,
                               font=('Consolas', 9), bg='#f8f9fa', fg='#333333',
                               selectbackground='#007acc', selectforeground='white')
        
        # 垂直滚动条
        v_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=v_scrollbar.set)
        
        # 水平滚动条
        h_scrollbar = ttk.Scrollbar(text_frame, orient=tk.HORIZONTAL, command=self.log_text.xview)
        self.log_text.configure(xscrollcommand=h_scrollbar.set)
        
        # 布局
        self.log_text.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)
        
        # 配置日志文本标签样式
        self.log_text.tag_configure('info', foreground='#0066cc')
        self.log_text.tag_configure('warning', foreground='#ff8c00', font=('Consolas', 9, 'bold'))
        self.log_text.tag_configure('error', foreground='#dc3545', font=('Consolas', 9, 'bold'))
        self.log_text.tag_configure('success', foreground='#28a745', font=('Consolas', 9, 'bold'))
        self.log_text.tag_configure('trade', foreground='#6f42c1', font=('Consolas', 9, 'italic'))
        self.log_text.tag_configure('move', foreground='#17a2b8')
        self.log_text.tag_configure('timestamp', foreground='#6c757d', font=('Consolas', 8))
        
        # 存储所有日志用于过滤
        self.all_logs = []
    
    def _draw_board(self):
        """绘制游戏板"""
        self.canvas.delete("all")
        
        # 绘制豪华渐变背景
        self._draw_gradient_background()
        
        # 绘制装饰性边框
        border_width = 8
        self.canvas.create_rectangle(border_width//2, border_width//2, 
                                   self.canvas_size - border_width//2, 
                                   self.canvas_size - border_width//2,
                                   fill='', outline='#8B4513', width=border_width)
        
        # 绘制内部装饰边框
        inner_border = border_width + 4
        self.canvas.create_rectangle(inner_border, inner_border, 
                                   self.canvas_size - inner_border, 
                                   self.canvas_size - inner_border,
                                   fill='', outline='#FFD700', width=2)
        
        # 绘制地图格子
        cells = self.game_manager.map_cells
        if not cells:
            return

        total_cells = len(cells)
        # 统一边距计算：边框(8) + 内边框间距(4) + 额外间距(8) = 20px 每边
        border_offset = 20
        board_size = self.canvas_size - (border_offset * 2)
        
        # 计算每边的格子数（不包括角落格子重复计算）
        # 40个格子的标准布局：每边10个格子，角落格子不重复计算
        cells_per_side = 10
        
        for i, cell in enumerate(cells):
            x, y = self._get_cell_position(i, cells_per_side, board_size)
            
            # 绘制格子 - 豪华大富翁样式
            color = self._get_cell_color(cell.cell_type)
            
            # 绘制深层阴影效果
            shadow_offset = 3
            self.canvas.create_rectangle(x + shadow_offset, y + shadow_offset, 
                                       x + self.cell_size + shadow_offset, 
                                       y + self.cell_size + shadow_offset,
                                       fill='#404040', outline='', width=0)
            
            # 绘制主格子 - 加强边框
            rect = self.canvas.create_rectangle(x, y, x + self.cell_size, y + self.cell_size,
                                              fill=color, outline='#1C1C1C', width=3)
            
            # 绘制渐变效果 - 顶部高光
            highlight_color = self._get_highlight_color(color)
            self.canvas.create_rectangle(x + 2, y + 2, x + self.cell_size - 2, y + 8,
                                       fill=highlight_color, outline='', width=0)
            
            # 绘制内边框装饰 - 金色边框
            self.canvas.create_rectangle(x + 4, y + 4, x + self.cell_size - 4, y + self.cell_size - 4,
                                       fill='', outline='#FFD700', width=1)
            
            # 绘制角落装饰
            corner_size = 6
            self.canvas.create_rectangle(x + 2, y + 2, x + corner_size, y + corner_size,
                                       fill='#FFD700', outline='#B8860B', width=1)
            self.canvas.create_rectangle(x + self.cell_size - corner_size, y + 2, 
                                       x + self.cell_size - 2, y + corner_size,
                                       fill='#FFD700', outline='#B8860B', width=1)
            
            # 特殊格子的额外装饰
            if cell.cell_type == CellType.START:
                # 绘制大型起点标识背景
                self.canvas.create_rectangle(x+2, y+2, x+self.cell_size-2, y+25,
                                           fill='#FF4500', outline='#8B0000', width=2)
                # 绘制"起点"大字
                self.canvas.create_text(x+self.cell_size//2, y+13, text="起点", 
                                       font=('微软雅黑', 14, 'bold'), fill='#FFFFFF')
                
                # 绘制GO箭头
                self.canvas.create_text(x+35, y+40, text="GO", 
                                       font=('Arial', 12, 'bold'), fill='#000000')
                
                # 绘制钱币图标
                self.canvas.create_oval(x+50, y+32, x+65, y+47, 
                                       fill='#FFD700', outline='#000000', width=2)
                self.canvas.create_text(x+57, y+39, text="$", 
                                       font=('Arial', 10, 'bold'), fill='#000000')
                
                # 绘制奖励金额
                self.canvas.create_text(x+self.cell_size//2, y+60, text="领取200元", 
                                       font=('微软雅黑', 8), fill='#000000')
            elif cell.cell_type == CellType.CHANCE:
                # 绘制机会卡片样式
                self.canvas.create_rectangle(x+5, y+5, x+15, y+15,
                                           fill='#FFFFFF', outline='#000000', width=2)
                self.canvas.create_text(x+10, y+10, text="?", 
                                       font=('Arial', 8, 'bold'), fill='#FF6B35')
                self.canvas.create_text(x+25, y+10, text="机会", 
                                       font=('微软雅黑', 8), fill='#FFFFFF')
            elif cell.cell_type == CellType.MISFORTUNE:
                # 绘制命运卡片样式
                self.canvas.create_rectangle(x+5, y+5, x+15, y+15,
                                           fill='#FFFFFF', outline='#000000', width=2)
                self.canvas.create_text(x+10, y+10, text="!", 
                                       font=('Arial', 8, 'bold'), fill='#FF0000')
                self.canvas.create_text(x+25, y+10, text="命运", 
                                       font=('微软雅黑', 8), fill='#FFFFFF')
            elif cell.cell_type == CellType.JAIL:
                # 绘制监狱图标
                self.canvas.create_rectangle(x+5, y+5, x+15, y+15,
                                           fill='#696969', outline='#000000', width=2)
                # 绘制栅栏
                for bar_x in range(x+7, x+19, 3):
                    self.canvas.create_line(bar_x, y+7, bar_x, y+18, 
                                          fill='#000000', width=1)
                self.canvas.create_text(x+30, y+12, text="监狱", 
                                       font=('微软雅黑', 8), fill='#000000')
            elif cell.cell_type == CellType.TAX:
                # 绘制税收图标
                self.canvas.create_polygon(x+5, y+15, x+10, y+5, x+15, y+15,
                                         fill='#FF0000', outline='#000000', width=2)
                self.canvas.create_text(x+25, y+10, text="税收", 
                                       font=('微软雅黑', 8), fill='#000000')
            
            # 绘制格子名称 - 改进的文字布局
            text_x = x + self.cell_size // 2
            text_y = y + self.cell_size // 2
            
            # 根据格子类型调整文字颜色
            text_color = '#000000' if cell.cell_type not in [CellType.JAIL, CellType.GO_TO_JAIL] else '#FFFFFF'
            
            # 分行显示长文本
            name = cell.name
            if len(name) > 4:
                lines = [name[i:i+4] for i in range(0, len(name), 4)]
                for j, line in enumerate(lines[:2]):  # 最多显示2行
                    self.canvas.create_text(text_x, text_y - 10 + j * 12, 
                                          text=line, font=('微软雅黑', 9, 'bold'), 
                                          anchor=tk.CENTER, fill=text_color)
            else:
                self.canvas.create_text(text_x, text_y, text=name, 
                                      font=('微软雅黑', 10, 'bold'), 
                                      anchor=tk.CENTER, fill=text_color)
            
            # 显示房产所有权和等级 - 改进的视觉效果
            if cell.owner_id is not None and cell.cell_type in [CellType.PROPERTY, CellType.AIRPORT, CellType.UTILITY, CellType.LANDMARK]:
                # 获取玩家颜色
                owner = self.game_manager.get_player_by_id(cell.owner_id)
                if owner:
                    player_index = self.game_manager.players.index(owner)
                    owner_color = self.player_colors[player_index % len(self.player_colors)]
                    
                    # 绘制玩家颜色边框表示所有权
                    self.canvas.create_rectangle(x + 1, y + 1, x + self.cell_size - 1, y + self.cell_size - 1,
                                                fill='', outline=owner_color, width=4)
                    
                    # 在左上角绘制玩家颜色标识
                    self.canvas.create_rectangle(x + 3, y + 3, x + 20, y + 20,
                                                fill=owner_color, outline='#000000', width=2)
                    
                    # 在颜色标识中显示玩家名称首字母
                    initial = owner.name[0] if owner.name else '?'
                    self.canvas.create_text(x + 11, y + 11, text=initial,
                                          font=('Arial', 10, 'bold'), anchor=tk.CENTER, fill='white')
                    
                    # 显示房产等级（仅限房产类型）- 根据购买者区分样式
                    if cell.cell_type == CellType.PROPERTY and hasattr(cell, 'level'):
                        level_text = "★" * cell.level.value if cell.level.value > 0 else "○"
                        
                        # 根据玩家颜色定制房屋等级样式
                        level_bg_color = owner_color
                        level_border_color = self._get_darker_color(owner_color)
                        level_text_color = '#FFFFFF' if self._is_dark_color(owner_color) else '#000000'
                        
                        # 现代化圆角矩形背景
                        self.canvas.create_rectangle(x + self.cell_size - 22, y + 2, x + self.cell_size - 2, y + 18,
                                                    fill=level_bg_color, outline=level_border_color, width=2)
                        # 添加内部高光效果
                        self.canvas.create_rectangle(x + self.cell_size - 20, y + 4, x + self.cell_size - 4, y + 8,
                                                    fill=self._get_lighter_color(owner_color), outline='', width=0)
                        
                        self.canvas.create_text(x + self.cell_size - 12, y + 10, text=level_text,
                                              font=('Arial', 8, 'bold'), anchor=tk.CENTER, fill=level_text_color)
            
            # 显示价格信息（仅房产类格子）- 增强可见性
            if cell.price > 0 and cell.cell_type in [CellType.PROPERTY, CellType.AIRPORT, CellType.LANDMARK]:
                price_text = f'${cell.price}'
                # 添加价格背景框
                price_bg_x1 = x + 5
                price_bg_y1 = y + self.cell_size - 18
                price_bg_x2 = x + self.cell_size - 5
                price_bg_y2 = y + self.cell_size - 4
                self.canvas.create_rectangle(price_bg_x1, price_bg_y1, price_bg_x2, price_bg_y2,
                                           fill='#FFFF99', outline='#FFD700', width=1)
                # 显示价格文字
                self.canvas.create_text(x + self.cell_size // 2, y + self.cell_size - 11, 
                                      text=price_text, font=('Arial', 9, 'bold'), 
                                      anchor=tk.CENTER, fill='#8B4513')
            
            # 绑定点击事件
            self.canvas.tag_bind(rect, "<Button-1>", 
                               lambda e, pos=i: self._on_cell_click(pos))
        
        # 绘制玩家
        self._draw_players()
        
        # 绘制中央区域的游戏信息
        self._draw_center_info()
    
    def _draw_center_info(self):
        """在地图中央显示游戏基本信息"""
        # 计算中央区域
        center_x = self.canvas_size // 2
        center_y = self.canvas_size // 2
        
        # 创建背景圆形
        radius = 150
        self.canvas.create_oval(center_x - radius, center_y - radius, 
                               center_x + radius, center_y + radius,
                               fill='#F5F5DC', outline='#FFD700', width=3)
        
        # 显示游戏名称
        self.canvas.create_text(center_x, center_y - 60, text="大富翁", 
                               font=('微软雅黑', 36, 'bold'), fill='#8B4513')
        
        # 显示当前角色
        current_player = self.game_manager.get_current_player()
        if current_player:
            player_text = f"当前角色: {current_player.name}"
            player_color = self.player_colors[self.game_manager.players.index(current_player) % len(self.player_colors)]
            
            # 创建角色信息背景
            self.canvas.create_rectangle(center_x - 120, center_y - 10, 
                                       center_x + 120, center_y + 20,
                                       fill='#FFFFFF', outline=player_color, width=2)
            
            self.canvas.create_text(center_x, center_y + 5, text=player_text, 
                                   font=('微软雅黑', 14), fill=player_color)
        
        # 显示回合数
        turn_text = f"回合数: {self.game_manager.turn_count}"
        self.canvas.create_rectangle(center_x - 80, center_y + 40, 
                                   center_x + 80, center_y + 70,
                                   fill='#FFFFFF', outline='#4169E1', width=2)
        self.canvas.create_text(center_x, center_y + 55, text=turn_text, 
                               font=('微软雅黑', 14), fill='#4169E1')
    
    def _get_cell_position(self, index: int, cells_per_side: int, board_size: int) -> tuple:
        """获取格子在画布上的位置"""
        # 调整基础偏移量以适应装饰边框
        border_offset = 20  # 8px边框 + 4px内边框 + 8px间距
        base_x, base_y = border_offset, border_offset
        
        # 调整board_size以适应新的边框
        adjusted_board_size = board_size - (border_offset * 2)
        
        # 标准36格大富翁布局（每边10个格子，角落格子属于两边）：
        # 右下角（起点）：位置1（索引0）
        # 下边：位置1-9（索引0-8）(9个格子，不包括角落)
        # 左下角（监狱）：位置10（索引9）
        # 左边：位置10-18（索引9-17）(9个格子，不包括角落)
        # 左上角（免费停车）：位置19（索引18）
        # 上边：位置19-27（索引18-26）(9个格子，不包括角落)
        # 右上角（进监狱）：位置28（索引27）
        # 右边：位置28-36（索引27-35）(9个格子，不包括角落)
        
        # 玩家位置从0开始，地图位置从1开始，需要转换
        # 位置0对应地图位置1（起点）
        position = index + 1
        
            
        if position == 1:  # 右下角（起点）
            x = base_x + adjusted_board_size - self.cell_size
            y = base_y + adjusted_board_size - self.cell_size
            return x, y
        elif 1 < position <= 9:  # 下边 (2-9)
            x = base_x + adjusted_board_size - self.cell_size - ((position - 1) * self.cell_size)
            y = base_y + adjusted_board_size - self.cell_size
            return x, y
        elif position == 10:  # 左下角（监狱）
            x = base_x
            y = base_y + adjusted_board_size - self.cell_size
            return x, y
        elif 10 < position <= 18:  # 左边 (11-18)
            x = base_x
            y = base_y + adjusted_board_size - self.cell_size - ((position - 10) * self.cell_size)
            return x, y
        elif position == 19:  # 左上角（免费停车）
            x = base_x
            y = base_y
            return x, y
        elif 19 < position <= 27:  # 上边 (20-27)
            x = base_x + ((position - 19) * self.cell_size)
            y = base_y
            return x, y
        elif position == 28:  # 右上角（进监狱）
            x = base_x + adjusted_board_size - self.cell_size
            y = base_y
            return x, y
        elif 28 < position <= 36:  # 右边 (29-35)
            x = base_x + adjusted_board_size - self.cell_size
            y = base_y + ((position - 28) * self.cell_size)
            return x, y
        else:
            # 默认返回起点位置
            x = base_x + adjusted_board_size - self.cell_size
            y = base_y + adjusted_board_size - self.cell_size
            return x, y
    
    def _get_cell_color(self, cell_type: CellType) -> str:
        """获取格子颜色 - 豪华大富翁配色方案"""
        colors = {
            CellType.START: '#FFD700',      # 金色 - 起点
            CellType.PROPERTY: '#4169E1',   # 皇家蓝 - 房产
            CellType.AIRPORT: '#FF4500',    # 橙红色 - 机场
            CellType.UTILITY: '#C0C0C0',    # 银色 - 公用事业
            CellType.LANDMARK: '#8A2BE2',   # 蓝紫色 - 地标
            CellType.CHANCE: '#FF69B4',     # 热粉色 - 机会
            CellType.MISFORTUNE: '#FF8C00', # 深橙色 - 命运
            CellType.TAX: '#B22222',        # 火砖红 - 税务
            CellType.JAIL: '#708090',       # 石板灰 - 监狱
            CellType.GO_TO_JAIL: '#2F4F4F', # 暗石板灰 - 进监狱
            CellType.FREE_PARKING: '#FFD700' # 金色 - 免费停车
        }
        return colors.get(cell_type, '#FFFFFF')
    
    def _get_highlight_color(self, base_color: str) -> str:
        """获取高光颜色 - 用于渐变效果"""
        # 将十六进制颜色转换为RGB，然后增加亮度
        hex_color = base_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        # 增加亮度（最大255）
        highlight_rgb = tuple(min(255, int(c * 1.3)) for c in rgb)
        
        # 转换回十六进制
        return '#{:02x}{:02x}{:02x}'.format(*highlight_rgb)
    
    def _draw_gradient_background(self):
        """绘制渐变背景"""
        # 创建从浅色到深色的渐变效果
        steps = 50
        for i in range(steps):
            # 计算渐变颜色
            ratio = i / steps
            # 从浅米色到深米色的渐变
            r = int(245 - ratio * 30)  # 245 -> 215
            g = int(245 - ratio * 35)  # 245 -> 210
            b = int(220 - ratio * 40)  # 220 -> 180
            
            color = '#{:02x}{:02x}{:02x}'.format(r, g, b)
            
            # 绘制渐变条带
            y1 = i * (self.canvas_size // steps)
            y2 = (i + 1) * (self.canvas_size // steps)
            
            self.canvas.create_rectangle(0, y1, self.canvas_size, y2,
                                       fill=color, outline=color)
    
    def _draw_players(self):
        """绘制玩家"""
        # 清除之前的玩家图标
        self.canvas.delete("player")
        
        for i, player in enumerate(self.game_manager.players):
            if player.is_bankrupt:
                continue
            
            # 获取玩家位置 - 使用与_draw_board相同的参数
            cells_per_side = 10  # 标准大富翁布局每边10个格子
            border_offset = 20
            board_size = self.canvas_size - (border_offset * 2)
            cell_x, cell_y = self._get_cell_position(player.position, cells_per_side, board_size)
            
            # 计算玩家在格子内的偏移
            offset_x = (i % 2) * 20 + 10
            offset_y = (i // 2) * 20 + 10
            
            player_x = cell_x + offset_x
            player_y = cell_y + offset_y
            
            # 绘制玩家图标 - 3D效果
            color = self.player_colors[i % len(self.player_colors)]
            
            # 如果在监狱，显示特殊标记
            if player.is_in_jail:
                # 绘制监狱栅栏效果
                self.canvas.create_rectangle(player_x-10, player_y-10, player_x+10, player_y+10,
                                           fill='#696969', outline='#000000', width=2, tags="player")
                # 绘制栅栏
                for bar_x in range(player_x-8, player_x+9, 4):
                    self.canvas.create_line(bar_x, player_y-8, bar_x, player_y+8, 
                                          fill='#000000', width=2, tags="player")
                self.canvas.create_text(player_x, player_y, text="囚", 
                                      font=('微软雅黑', 8, 'bold'), fill='#FFFFFF', tags="player")
            else:
                # 绘制阴影
                self.canvas.create_oval(player_x-7, player_y-7, player_x+9, player_y+9,
                                      fill='#808080', outline='', tags="player")
                # 绘制主体
                self.canvas.create_oval(player_x-8, player_y-8, player_x+8, player_y+8,
                                      fill=color, outline='#000000', width=2, tags="player")
                # 绘制高光效果
                self.canvas.create_oval(player_x-6, player_y-6, player_x-2, player_y-2,
                                      fill='#FFFFFF', outline='', tags="player")
                # 绘制玩家编号
                self.canvas.create_text(player_x, player_y+1, text=str(player.id), 
                                      font=('Arial', 8, 'bold'), fill='#FFFFFF', tags="player")
                # 绘制玩家名称（在图标下方）
                self.canvas.create_text(player_x, player_y+18, text=player.name[:3], 
                                      font=('微软雅黑', 6), fill='#000000', tags="player")
    
    def _on_cell_click(self, position: int):
        """处理格子点击事件"""
        cell = self.game_manager.get_cell_at_position(position)
        if cell:
            info = f"位置: {cell.position}\n名称: {cell.name}\n类型: {cell.cell_type.value}"
            if cell.price > 0:
                info += f"\n价格: {cell.price}"
            if cell.rent_base > 0:
                info += f"\n基础租金: {cell.rent_base}"
            if cell.owner_id:
                owner = self.game_manager.get_player_by_id(cell.owner_id)
                info += f"\n所有者: {owner.name if owner else '未知'}"
            info += f"\n描述: {cell.description}"
            
            messagebox.showinfo("格子信息", info)

    
    def _roll_dice(self):
        """投掷骰子"""
        current_player = self.game_manager.get_current_player()
        if not current_player:
            return
        
        # 检查是否在监狱
        if current_player.is_in_jail:
            if not current_player.try_leave_jail():
                self._log(f"{current_player.name} 仍在监狱中，剩余 {current_player.jail_turns} 回合", 'warning')
                self._end_turn()
                return
            else:
                self._log(f"{current_player.name} 出狱了！", 'success')
        
        # 投掷骰子
        dice1, dice2, total = self.game_manager.roll_dice()
        self.dice_label.config(text=f"骰子: {dice1} + {dice2} = {total}")
        
        # 移动玩家
        move_result = self.game_manager.move_player(current_player, total)
        
        # 处理落地事件
        landing_result = self.game_manager.process_landing(current_player)
        
        # 更新界面
        self._draw_board()
        self._update_player_list()
        self._update_game_info()
        
        # 处理落地结果
        self._handle_landing_result(landing_result)
        
        # 如果是AI玩家，自动处理
        if current_player.player_type == PlayerType.AI:
            self.root.after(1000, self._handle_ai_actions)
        
        # 禁用骰子按钮
        self.roll_button.config(state=tk.DISABLED)
    
    def _handle_landing_result(self, result: Dict[str, Any]):
        """处理落地结果"""
        result_type = result.get("type")
        
        if result_type == "purchase_option":
            if result["can_purchase"]:
                self.buy_button.config(state=tk.NORMAL)
                self._log(f"可以购买 {result['cell'].name}，价格: {result['price']}", 'trade')
            else:
                self._log(f"资金不足，无法购买 {result['cell'].name}", 'warning')
        
        elif result_type == "upgrade_option":
            if result["can_upgrade"]:
                self.upgrade_button.config(state=tk.NORMAL)
                self._log(f"可以升级 {result['cell'].name}，费用: {result['upgrade_cost']}", 'trade')
            else:
                self._log(f"无法升级 {result['cell'].name}", 'warning')
        
        elif result_type == "rent_paid":
            self._log(f"支付租金 {result['rent']} 给 {result['owner']}", 'trade')
        
        elif result_type == "chance_event" or result_type == "misfortune_event":
            event_result = result["event_result"]
            self._show_event_dialog(event_result)
        
        elif result_type == "tax_paid":
            self._log(f"缴纳{result['tax_type']} {result['tax_amount']} 金币", 'trade')
        
        elif result_type == "go_to_jail":
            self._log(result["message"])
        
        # 启用结束回合按钮
        self.end_turn_button.config(state=tk.NORMAL)
    
    def _show_event_dialog(self, event_result: Dict[str, Any]):
        """显示事件对话框"""
        event = event_result["event"]
        effects = event_result.get("effects", [])
        
        message = f"{event.title}\n\n{event.description}\n\n"
        if effects:
            message += "效果:\n" + "\n".join(effects)
        
        messagebox.showinfo("事件", message)
    
    def _buy_property(self):
        """购买房产"""
        current_player = self.game_manager.get_current_player()
        if not current_player:
            return
        
        cell = self.game_manager.get_cell_at_position(current_player.position)
        if cell and self.game_manager.purchase_property(current_player, cell):
            self._update_player_list()
            self._draw_board()
            self.buy_button.config(state=tk.DISABLED)
        else:
            messagebox.showerror("错误", "购买失败")
    
    def _upgrade_property(self):
        """升级房产"""
        current_player = self.game_manager.get_current_player()
        if not current_player:
            return
        
        cell = self.game_manager.get_cell_at_position(current_player.position)
        if cell and self.game_manager.upgrade_property(current_player, cell):
            self._update_player_list()
            self._draw_board()
            self.upgrade_button.config(state=tk.DISABLED)
        else:
            messagebox.showerror("错误", "升级失败")
    
    def _handle_ai_actions(self):
        """处理AI行动"""
        current_player = self.game_manager.get_current_player()
        if not current_player or current_player.player_type != PlayerType.AI:
            return
        
        # 获取当前位置的格子
        cell = self.game_manager.get_cell_at_position(current_player.position)
        if not cell:
            self._end_turn()
            return
        
        ai_player = self.game_manager.ai_players.get(current_player.id)
        if not ai_player:
            self._end_turn()
            return
        
        # AI决策
        if cell.owner_id is None and cell.cell_type in [CellType.PROPERTY, CellType.AIRPORT, CellType.UTILITY, CellType.LANDMARK]:
            # 购买决策
            if ai_player.make_purchase_decision(cell, self.game_manager.get_game_state_dict()):
                if self.game_manager.purchase_property(current_player, cell):
                    self._update_player_list()
                    self._draw_board()
        
        elif cell.owner_id == current_player.id and cell.can_upgrade():
            # 升级决策
            upgrade_position = ai_player.make_upgrade_decision(self.game_manager.map_cells)
            if upgrade_position == cell.position:
                if self.game_manager.upgrade_property(current_player, cell):
                    self._update_player_list()
                    self._draw_board()
        
        # 延迟结束回合
        self.root.after(1500, self._end_turn)
    
    def _end_turn(self):
        """结束回合"""
        # 检查破产
        current_player = self.game_manager.get_current_player()
        if current_player and current_player.check_bankruptcy():
            self._log(f"{current_player.name} 破产了！", 'error')
            self._update_player_list()
        
        # 切换到下一个玩家
        if self.game_manager.next_turn():
            # 立即更新UI显示新的当前玩家
            self._update_game_info()
            self._update_player_list()
            self._draw_board()  # 重绘棋盘以突出显示新的当前玩家
            self._update_ui_state()
        else:
            # 游戏结束
            self._game_over()
    
    def _game_over(self):
        """游戏结束"""
        active_players = [p for p in self.game_manager.players if not p.is_bankrupt]
        if active_players:
            winner = active_players[0]
            messagebox.showinfo("游戏结束", f"恭喜 {winner.name} 获胜！")
        else:
            messagebox.showinfo("游戏结束", "游戏结束")
        
        self._update_ui_state()
    
    def _undo_action(self):
        """撤销操作"""
        result = self.game_manager.undo_last_action()
        if result.get("success", False):
            self._log(f"撤销操作: {result.get('message', '操作已撤销')}", 'info')
            self._update_player_list()
            self._draw_board()
            self._update_game_info()
            
            # 只有撤销移动命令（掷骰子）时才重新启用掷骰子按钮
            command_type = result.get("command_type")
            if command_type == "MovePlayerCommand":
                self._update_ui_state()
        else:
            self._log(f"撤销失败: {result.get('message', '没有可撤销的操作')}", 'warning')
        
        self._update_undo_redo_buttons()
    
    def _redo_action(self):
        """重做操作"""
        result = self.game_manager.redo_last_action()
        if result.get("success", False):
            self._log(f"重做操作: {result.get('message', '操作已重做')}", 'info')
            self._update_player_list()
            self._draw_board()
            self._update_game_info()
            
            # 只有重做移动命令（掷骰子）时才重新启用掷骰子按钮
            command_type = result.get("command_type")
            if command_type == "MovePlayerCommand":
                self._update_ui_state()
        else:
            self._log(f"重做失败: {result.get('message', '没有可重做的操作')}", 'warning')
        
        self._update_undo_redo_buttons()
    
    def _update_undo_redo_buttons(self):
        """更新撤销/重做按钮状态"""
        if self.game_manager.can_undo():
            self.undo_button.config(state=tk.NORMAL)
        else:
            self.undo_button.config(state=tk.DISABLED)
        
        if self.game_manager.can_redo():
            self.redo_button.config(state=tk.NORMAL)
        else:
            self.redo_button.config(state=tk.DISABLED)
    
    def _update_ui_state(self):
        """更新UI状态"""
        game_state = self.game_manager.game_state
        current_player = self.game_manager.get_current_player()
        
        # 更新撤销/重做按钮状态
        self._update_undo_redo_buttons()
        
        if game_state == GameState.PLAYING and current_player:
            # 游戏进行中
            if current_player.player_type == PlayerType.HUMAN:
                self.roll_button.config(state=tk.NORMAL)
            else:
                self.roll_button.config(state=tk.DISABLED)
                # AI自动投掷骰子
                self.root.after(1000, self._roll_dice)
        else:
            # 游戏未开始或已结束
            self.roll_button.config(state=tk.DISABLED)
        
        self.buy_button.config(state=tk.DISABLED)
        self.upgrade_button.config(state=tk.DISABLED)
        self.end_turn_button.config(state=tk.DISABLED)
    
    def _update_player_list(self):
        """更新玩家列表"""
        # 清空列表
        for item in self.player_tree.get_children():
            self.player_tree.delete(item)
        
        # 添加玩家
        for player in self.game_manager.players:
            status = "💀" if player.is_bankrupt else ("🔒" if player.is_in_jail else "")
            player_name = f"{status}{player.name}"
            
            cell = self.game_manager.get_cell_at_position(player.position)
            position_name = cell.name if cell else "未知"
            
            self.player_tree.insert('', 'end', text=player_name,
                                  values=(f"${player.money}", len(player.properties), position_name))
    
    def _update_game_info(self):
        """更新游戏信息"""
        current_player = self.game_manager.get_current_player()
        if current_player:
            self.current_player_label.config(text=f"{current_player.name}")
            
            # 更新游戏状态
            if hasattr(self, 'game_status_label'):
                self.game_status_label.config(text="游戏进行中", foreground='#28a745')
            
            cell = self.game_manager.get_cell_at_position(current_player.position)
            if cell:
                position_text = f"{current_player.position} - {cell.name}"
                # 根据格子类型设置颜色
                if hasattr(cell, 'cell_type'):
                    if cell.cell_type == 'property':
                        self.position_label.config(text=position_text, foreground='#8A2BE2')
                    elif cell.cell_type == 'special':
                        self.position_label.config(text=position_text, foreground='#FF6347')
                    else:
                        self.position_label.config(text=position_text, foreground='#17a2b8')
                else:
                    self.position_label.config(text=position_text, foreground='#8A2BE2')
            else:
                self.position_label.config(text=f"{current_player.position} - 未知", foreground='#dc3545')
        else:
            self.current_player_label.config(text="无")
            self.position_label.config(text="-")
            if hasattr(self, 'game_status_label'):
                self.game_status_label.config(text="等待开始", foreground='#FF8C00')
        
        self.turn_label.config(text=f"{self.game_manager.turn_count}")
        
        # 更新骰子显示
        if hasattr(self.game_manager, 'last_dice_result') and self.game_manager.last_dice_result:
            dice1, dice2, total = self.game_manager.last_dice_result
            dice_text = f"骰子: {dice1} + {dice2} = {total}"
            if total == 12:  # 双6
                dice_text += " 🎉"
            elif dice1 == dice2:  # 双数
                dice_text += " 🎲"
            self.dice_label.config(text=dice_text)
        else:
            self.dice_label.config(text="骰子: -")
    
    def _log(self, message, log_type='info'):
        """添加日志消息"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        # 存储日志用于过滤
        log_entry = {
            'timestamp': timestamp,
            'message': message,
            'type': log_type
        }
        self.all_logs.append(log_entry)
        
        # 显示日志
        self._display_log_entry(log_entry)
    
    def _display_log_entry(self, log_entry):
        """显示单条日志"""
        self.log_text.config(state=tk.NORMAL)
        
        # 插入时间戳
        self.log_text.insert(tk.END, f"[{log_entry['timestamp']}] ", 'timestamp')
        
        # 根据类型添加图标和样式
        icons = {
            'info': '💬 ',
            'warning': '⚠️ ',
            'error': '❌ ',
            'success': '✅ ',
            'trade': '💰 ',
            'move': '🚶 ',
            'system': '⚙️ '
        }
        
        icon = icons.get(log_entry['type'], '📝 ')
        self.log_text.insert(tk.END, icon + log_entry['message'] + '\n', log_entry['type'])
        
        self.log_text.config(state=tk.DISABLED)
        self.log_text.see(tk.END)
    
    def _filter_logs(self, event=None):
        """过滤日志显示"""
        filter_type = self.log_filter_var.get()
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        
        for log_entry in self.all_logs:
            if filter_type == "全部":
                self._display_log_entry(log_entry)
            elif filter_type == "重要" and log_entry['type'] in ['warning', 'error', 'success']:
                self._display_log_entry(log_entry)
            elif filter_type == "交易" and log_entry['type'] == 'trade':
                self._display_log_entry(log_entry)
            elif filter_type == "移动" and log_entry['type'] == 'move':
                self._display_log_entry(log_entry)
            elif filter_type == "系统" and log_entry['type'] == 'system':
                self._display_log_entry(log_entry)
        
        self.log_text.config(state=tk.DISABLED)
    
    def _clear_logs(self):
        """清空日志"""
        import tkinter.messagebox as msgbox
        if msgbox.askyesno("确认", "确定要清空所有日志吗？"):
            self.all_logs.clear()
            self.log_text.config(state=tk.NORMAL)
            self.log_text.delete(1.0, tk.END)
            self.log_text.config(state=tk.DISABLED)
            self._log("日志已清空", 'system')
    
    def _export_logs(self):
        """导出日志到文件"""
        import tkinter.filedialog as filedialog
        import datetime
        
        if not self.all_logs:
            import tkinter.messagebox as msgbox
            msgbox.showwarning("警告", "没有日志可以导出！")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
            title="导出游戏日志"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"大富翁游戏日志\n")
                    f.write(f"导出时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 50 + "\n\n")
                    
                    for log_entry in self.all_logs:
                        f.write(f"[{log_entry['timestamp']}] [{log_entry['type'].upper()}] {log_entry['message']}\n")
                
                import tkinter.messagebox as msgbox
                msgbox.showinfo("成功", f"日志已导出到: {filename}")
                self._log(f"日志已导出到: {filename}", 'system')
            except Exception as e:
                import tkinter.messagebox as msgbox
                msgbox.showerror("错误", f"导出失败: {str(e)}")
                self._log(f"日志导出失败: {str(e)}", 'error')
    
    def add_log_message(self, sender: str, message: str):
        """添加日志消息"""
        formatted_message = f"[{sender}] {message}"
        self._log(formatted_message)
    
    def _new_game(self):
        """新游戏"""
        if messagebox.askyesno("新游戏", "确定要开始新游戏吗？当前进度将丢失。"):
            self.game_manager.reset_game()
            self._update_player_list()
            self._update_game_info()
            self._draw_board()
            self.log_text.delete(1.0, tk.END)
            self._update_ui_state()
    
    def _auto_start_game(self):
        """自动开始游戏（从开始页面传入玩家数据）"""
        try:
            # 重置游戏状态
            self.game_manager.reset_game()
            
            # 更新游戏配置中的初始金币
            self.game_manager.config.initial_money = self.initial_money
            
            # 添加玩家
            for player_data in self.players_data:
                self.game_manager.create_player(
                    name=player_data['name'],
                    player_type=player_data['type']
                )
            
            # 开始游戏
            self.game_manager.start_game()
            
            # 更新界面
            self._update_player_list()
            self._update_game_info()
            self._draw_board()
            self.log_text.delete(1.0, tk.END)
            self._update_ui_state()
            
            # 添加欢迎消息
            self._log("游戏开始！")
            for player_data in self.players_data:
                self._log(f"玩家 {player_data['name']} ({player_data['type']}) 加入游戏")
                
        except Exception as e:
            messagebox.showerror("错误", f"启动游戏失败: {str(e)}")
    
    def _save_game(self):
        """保存游戏"""
        if self.game_manager.game_state == GameState.WAITING:
            messagebox.showwarning("警告", "游戏尚未开始，无法保存")
            return
        
        # 如果有上次保存的名称，询问是否快速保存
        if self.game_manager.last_save_name:
            result = messagebox.askyesnocancel(
                "保存游戏", 
                f"是否覆盖保存到 '{self.game_manager.last_save_name}'？\n\n是：覆盖保存\n否：另存为新存档\n取消：不保存"
            )
            
            if result is True:  # 用户选择"是" - 快速保存
                if self.game_manager.quick_save():
                    messagebox.showinfo("成功", f"游戏已保存到 '{self.game_manager.last_save_name}'")
                else:
                    messagebox.showerror("错误", "快速保存失败")
                return
            elif result is False:  # 用户选择"否" - 另存为
                pass  # 继续执行下面的输入存档名称逻辑
            else:  # 用户选择"取消"
                return
        
        # 询问存档名称（首次保存或用户选择另存为）
        save_name = simpledialog.askstring("保存游戏", "请输入存档名称:")
        if save_name:
            if self.game_manager.save_game(save_name):
                messagebox.showinfo("成功", "游戏保存成功")
            else:
                messagebox.showerror("错误", "游戏保存失败")
    
    def _load_game(self):
        """加载游戏"""
        # 获取存档列表
        saves = self.game_manager.db_manager.get_save_list()
        if not saves:
            messagebox.showinfo("提示", "没有找到存档")
            return
        
        # 创建选择对话框
        load_window = tk.Toplevel(self.root)
        load_window.title("加载游戏")
        load_window.geometry("400x300")
        load_window.transient(self.root)
        load_window.grab_set()
        
        ttk.Label(load_window, text="请选择要加载的存档:").pack(pady=10)
        
        # 存档列表
        save_listbox = tk.Listbox(load_window)
        save_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        for save in saves:
            save_listbox.insert(tk.END, f"{save['save_name']} ({save['save_date']})")
        
        def load_selected():
            selection = save_listbox.curselection()
            if selection:
                save_name = saves[selection[0]]['save_name']
                if self.game_manager.load_game(save_name):
                    self._update_player_list()
                    self._update_game_info()
                    self._draw_board()
                    self._update_ui_state()
                    messagebox.showinfo("成功", "游戏加载成功")
                    load_window.destroy()
                else:
                    messagebox.showerror("错误", "游戏加载失败")
        
        button_frame = ttk.Frame(load_window)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="加载", command=load_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=load_window.destroy).pack(side=tk.LEFT, padx=5)
    
    def _show_rules(self):
        """显示游戏规则"""
        rules = """
大富翁游戏规则：

1. 玩家轮流投掷骰子，按点数前进
2. 落在空地可以购买房产
3. 落在别人的房产需要支付租金
4. 落在自己的房产可以升级
5. 落在幸运格子获得好处
6. 落在不幸格子遭受损失
7. 落在税务格子需要缴税
8. 经过起点获得200金币
9. 金钱为负数时破产出局
10. 最后剩余的玩家获胜
        """
        messagebox.showinfo("游戏规则", rules)
    
    def _show_about(self):
        """显示关于信息"""
        about = """
大富翁游戏 v1.0

基于Python开发的桌面大富翁游戏
采用三层架构和多种设计模式
支持人类玩家和AI玩家

开发语言: Python
界面框架: Tkinter
数据库: SQLite
        """
        messagebox.showinfo("关于", about)
    
    def on_event_triggered(self, event_result: Dict[str, Any]):
        """事件观察者回调"""
        # 在主线程中更新UI
        self.root.after(0, lambda: self._handle_event_notification(event_result))
    
    def _handle_event_notification(self, event_result: Dict[str, Any]):
        """处理事件通知"""
        # 添加类型检查和调试信息
        if not isinstance(event_result, dict):
            print(f"错误：event_result不是字典类型，而是 {type(event_result)}，值为: {event_result}")
            # 如果是字符串，将其转换为字典格式
            if isinstance(event_result, str):
                event_result = {"message": event_result}
            else:
                return
        
        message = event_result.get("message", "")
        if message:
            self._log(message)
        
        # 更新玩家信息
        self._update_player_list()
    
    def _on_closing(self):
        """关闭程序"""
        self.game_manager.db_manager.close()
        self.root.destroy()
    
    def restore_from_loaded_game(self):
        """从加载的游戏中恢复界面状态"""
        try:
            # 更新玩家列表
            self._update_player_list()
            
            # 更新游戏信息
            self._update_game_info()
            
            # 重绘游戏板
            self._draw_board()
            
            # 更新UI状态
            self._update_ui_state()
            
            # 如果游戏正在进行，启用相关按钮
            if self.game_manager.game_state == GameState.PLAYING:
                self.roll_button.config(state=tk.NORMAL)
                self.end_turn_button.config(state=tk.NORMAL)
                
            print("游戏状态恢复完成")
        except Exception as e:
            print(f"恢复游戏状态时出错: {e}")
            self._log(f"恢复游戏状态失败: {str(e)}")
    
    def _get_darker_color(self, color: str) -> str:
        """获取更深的颜色"""
        try:
            # 移除#号
            color = color.lstrip('#')
            # 转换为RGB
            r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
            # 降低亮度
            r = max(0, int(r * 0.7))
            g = max(0, int(g * 0.7))
            b = max(0, int(b * 0.7))
            return f'#{r:02x}{g:02x}{b:02x}'
        except:
            return '#000000'
    
    def _get_lighter_color(self, color: str) -> str:
        """获取更浅的颜色"""
        try:
            # 移除#号
            color = color.lstrip('#')
            # 转换为RGB
            r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
            # 提高亮度
            r = min(255, int(r + (255 - r) * 0.5))
            g = min(255, int(g + (255 - g) * 0.5))
            b = min(255, int(b + (255 - b) * 0.5))
            return f'#{r:02x}{g:02x}{b:02x}'
        except:
            return '#FFFFFF'
    
    def _is_dark_color(self, color: str) -> bool:
        """判断颜色是否为深色"""
        try:
            # 移除#号
            color = color.lstrip('#')
            # 转换为RGB
            r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
            # 计算亮度
            brightness = (r * 299 + g * 587 + b * 114) / 1000
            return brightness < 128
        except:
            return True
    
    def run(self):
        """运行游戏"""
        self.root.mainloop()
