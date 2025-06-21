import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
import time
from typing import List, Dict, Any, Optional
from PIL import Image, ImageTk
import math

from business.game_manager import GameManager
from business.models import Player, PlayerType, GameState, CellType
from business.events import EventObserver

class GameGUI(EventObserver):
    """游戏主界面"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("大富翁游戏")
        self.root.geometry("1200x800")
        self.root.resizable(True, True)
        
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
        
        # 控制按钮框架
        control_frame = ttk.Frame(left_frame)
        control_frame.pack(fill=tk.X, pady=10)
        
        # 骰子按钮
        self.roll_button = ttk.Button(control_frame, text="投掷骰子", 
                                     command=self._roll_dice, state=tk.DISABLED)
        self.roll_button.pack(side=tk.LEFT, padx=5)
        
        # 购买按钮
        self.buy_button = ttk.Button(control_frame, text="购买房产", 
                                    command=self._buy_property, state=tk.DISABLED)
        self.buy_button.pack(side=tk.LEFT, padx=5)
        
        # 升级按钮
        self.upgrade_button = ttk.Button(control_frame, text="升级房产", 
                                        command=self._upgrade_property, state=tk.DISABLED)
        self.upgrade_button.pack(side=tk.LEFT, padx=5)
        
        # 结束回合按钮
        self.end_turn_button = ttk.Button(control_frame, text="结束回合", 
                                         command=self._end_turn, state=tk.DISABLED)
        self.end_turn_button.pack(side=tk.LEFT, padx=5)
        
        # 右侧信息面板
        right_frame = ttk.Frame(main_frame, width=300)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        right_frame.pack_propagate(False)
        
        # 玩家信息
        self._create_player_info_panel(right_frame)
        
        # 游戏信息
        self._create_game_info_panel(right_frame)
        
        # 日志面板
        self._create_log_panel(right_frame)
        
        # 初始化游戏板
        self._draw_board()
    
    def _create_player_info_panel(self, parent):
        """创建玩家信息面板"""
        player_frame = ttk.LabelFrame(parent, text="玩家信息")
        player_frame.pack(fill=tk.X, pady=5)
        
        # 玩家列表
        self.player_tree = ttk.Treeview(player_frame, columns=('money', 'properties', 'position'), 
                                       show='tree headings', height=6)
        self.player_tree.heading('#0', text='玩家')
        self.player_tree.heading('money', text='金钱')
        self.player_tree.heading('properties', text='房产数')
        self.player_tree.heading('position', text='位置')
        
        self.player_tree.column('#0', width=80)
        self.player_tree.column('money', width=80)
        self.player_tree.column('properties', width=60)
        self.player_tree.column('position', width=60)
        
        self.player_tree.pack(fill=tk.X, padx=5, pady=5)
        
        # 添加玩家按钮
        button_frame = ttk.Frame(player_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="添加人类玩家", 
                  command=self._add_human_player).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="添加AI玩家", 
                  command=self._add_ai_player).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="开始游戏", 
                  command=self._start_game).pack(side=tk.LEFT, padx=2)
    
    def _create_game_info_panel(self, parent):
        """创建游戏信息面板"""
        info_frame = ttk.LabelFrame(parent, text="游戏信息")
        info_frame.pack(fill=tk.X, pady=5)
        
        # 当前玩家
        self.current_player_label = ttk.Label(info_frame, text="当前玩家: 无")
        self.current_player_label.pack(anchor=tk.W, padx=5, pady=2)
        
        # 回合数
        self.turn_label = ttk.Label(info_frame, text="回合数: 0")
        self.turn_label.pack(anchor=tk.W, padx=5, pady=2)
        
        # 骰子结果
        self.dice_label = ttk.Label(info_frame, text="骰子: -")
        self.dice_label.pack(anchor=tk.W, padx=5, pady=2)
        
        # 当前位置信息
        self.position_label = ttk.Label(info_frame, text="位置: -")
        self.position_label.pack(anchor=tk.W, padx=5, pady=2)
    
    def _create_log_panel(self, parent):
        """创建日志面板"""
        log_frame = ttk.LabelFrame(parent, text="游戏日志")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 日志文本框
        self.log_text = tk.Text(log_frame, height=10, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
    
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
                self.canvas.create_polygon(x+5, y+30, x+25, y+40, x+5, y+50,
                                         fill='#FFD700', outline='#000000', width=2)
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
            
            # 显示房产等级 - 改进的视觉效果
            if cell.owner_id is not None and cell.cell_type == CellType.PROPERTY:
                level_text = "★" * cell.level.value if cell.level.value > 0 else "○"
                # 添加背景圆圈
                self.canvas.create_oval(x + 2, y + 2, x + 18, y + 18, 
                                       fill='#FFFFFF', outline='#000000', width=1)
                self.canvas.create_text(x + 10, y + 10, text=level_text, 
                                      font=('Arial', 8, 'bold'), anchor=tk.CENTER, fill='#FF0000')
            
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
        
        # 将基于0的索引转换为基于1的位置
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
            
            # 获取玩家位置
            cells_per_side = len(self.game_manager.map_cells) // 4
            board_size = self.canvas_size - 100
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
    
    def _add_human_player(self):
        """添加人类玩家"""
        if len(self.game_manager.players) >= self.game_manager.config.max_players:
            messagebox.showwarning("警告", f"玩家数量不能超过{self.game_manager.config.max_players}人")
            return
        
        name = simpledialog.askstring("添加玩家", "请输入玩家姓名:")
        if name:
            try:
                player = self.game_manager.create_player(name, PlayerType.HUMAN)
                self._update_player_list()
                self._log(f"添加人类玩家: {name}")
            except ValueError as e:
                messagebox.showerror("错误", str(e))
    
    def _add_ai_player(self):
        """添加AI玩家"""
        if len(self.game_manager.players) >= self.game_manager.config.max_players:
            messagebox.showwarning("警告", f"玩家数量不能超过{self.game_manager.config.max_players}人")
            return
        
        # 选择AI难度
        difficulty_window = tk.Toplevel(self.root)
        difficulty_window.title("选择AI难度")
        difficulty_window.geometry("300x200")
        difficulty_window.transient(self.root)
        difficulty_window.grab_set()
        
        selected_difficulty = tk.StringVar(value="medium")
        
        ttk.Label(difficulty_window, text="请选择AI难度:").pack(pady=10)
        
        ttk.Radiobutton(difficulty_window, text="简单", variable=selected_difficulty, 
                       value="easy").pack(pady=5)
        ttk.Radiobutton(difficulty_window, text="中等", variable=selected_difficulty, 
                       value="medium").pack(pady=5)
        ttk.Radiobutton(difficulty_window, text="困难", variable=selected_difficulty, 
                       value="hard").pack(pady=5)
        
        def confirm():
            name = f"AI玩家{len(self.game_manager.players) + 1}"
            try:
                player = self.game_manager.create_player(name, PlayerType.AI, 
                                                        ai_difficulty=selected_difficulty.get())
                self._update_player_list()
                self._log(f"添加AI玩家: {name} (难度: {selected_difficulty.get()})")
                difficulty_window.destroy()
            except ValueError as e:
                messagebox.showerror("错误", str(e))
        
        ttk.Button(difficulty_window, text="确定", command=confirm).pack(pady=10)
        ttk.Button(difficulty_window, text="取消", 
                  command=difficulty_window.destroy).pack(pady=5)
    
    def _start_game(self):
        """开始游戏"""
        if len(self.game_manager.players) < 2:
            messagebox.showwarning("警告", "至少需要2个玩家才能开始游戏")
            return
        
        if self.game_manager.start_game():
            self._update_ui_state()
            self._update_game_info()
            self._draw_board()
            self._log("游戏开始！")
        else:
            messagebox.showerror("错误", "游戏开始失败")
    
    def _roll_dice(self):
        """投掷骰子"""
        current_player = self.game_manager.get_current_player()
        if not current_player:
            return
        
        # 检查是否在监狱
        if current_player.is_in_jail:
            if not current_player.try_leave_jail():
                self._log(f"{current_player.name} 仍在监狱中，剩余 {current_player.jail_turns} 回合")
                self._end_turn()
                return
            else:
                self._log(f"{current_player.name} 出狱了！")
        
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
                self._log(f"可以购买 {result['cell'].name}，价格: {result['price']}")
            else:
                self._log(f"资金不足，无法购买 {result['cell'].name}")
        
        elif result_type == "upgrade_option":
            if result["can_upgrade"]:
                self.upgrade_button.config(state=tk.NORMAL)
                self._log(f"可以升级 {result['cell'].name}，费用: {result['upgrade_cost']}")
            else:
                self._log(f"无法升级 {result['cell'].name}")
        
        elif result_type == "rent_paid":
            self._log(f"支付租金 {result['rent']} 给 {result['owner']}")
        
        elif result_type == "chance_event" or result_type == "misfortune_event":
            event_result = result["event_result"]
            self._show_event_dialog(event_result)
        
        elif result_type == "tax_paid":
            self._log(f"缴纳{result['tax_type']} {result['tax_amount']} 金币")
        
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
                    self._log(f"AI {current_player.name} 购买了 {cell.name}")
                    self._update_player_list()
                    self._draw_board()
        
        elif cell.owner_id == current_player.id and cell.can_upgrade():
            # 升级决策
            upgrade_position = ai_player.make_upgrade_decision(self.game_manager.map_cells)
            if upgrade_position == cell.position:
                if self.game_manager.upgrade_property(current_player, cell):
                    self._log(f"AI {current_player.name} 升级了 {cell.name}")
                    self._update_player_list()
                    self._draw_board()
        
        # 延迟结束回合
        self.root.after(1500, self._end_turn)
    
    def _end_turn(self):
        """结束回合"""
        # 检查破产
        current_player = self.game_manager.get_current_player()
        if current_player and current_player.check_bankruptcy():
            self._log(f"{current_player.name} 破产了！")
            self._update_player_list()
        
        # 切换到下一个玩家
        if self.game_manager.next_turn():
            self._update_ui_state()
            self._update_game_info()
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
    
    def _update_ui_state(self):
        """更新UI状态"""
        game_state = self.game_manager.game_state
        current_player = self.game_manager.get_current_player()
        
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
            self.current_player_label.config(text=f"当前玩家: {current_player.name}")
            
            cell = self.game_manager.get_cell_at_position(current_player.position)
            position_text = f"位置: {cell.name}" if cell else "位置: 未知"
            self.position_label.config(text=position_text)
        else:
            self.current_player_label.config(text="当前玩家: 无")
            self.position_label.config(text="位置: -")
        
        self.turn_label.config(text=f"回合数: {self.game_manager.turn_count}")
    
    def _log(self, message: str):
        """添加日志"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
    
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
    
    def _save_game(self):
        """保存游戏"""
        if self.game_manager.game_state == GameState.WAITING:
            messagebox.showwarning("警告", "游戏尚未开始，无法保存")
            return
        
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
        message = event_result.get("message", "")
        if message:
            self._log(message)
        
        # 更新玩家信息
        self._update_player_list()
    
    def _on_closing(self):
        """关闭程序"""
        if messagebox.askokcancel("退出", "确定要退出游戏吗？"):
            self.game_manager.db_manager.close()
            self.root.destroy()
    
    def run(self):
        """运行游戏"""
        self.root.mainloop()