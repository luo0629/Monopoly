import sqlite3
import os
from typing import Optional, List, Dict, Any
import threading

class DatabaseManager:
    """数据库管理器 - 单例模式"""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.db_path = 'data/monopoly.db'
            self.connection = None
            self.initialized = True
            self._ensure_data_directory()
            self._initialize_database()
    
    def _ensure_data_directory(self):
        """确保数据目录存在"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def _initialize_database(self):
        """初始化数据库表结构"""
        self._connect()
        self._create_tables()
        self._insert_default_data()
    
    def connect(self):
        """公共连接方法"""
        try:
            self._connect()
            return True
        except Exception as e:
            print(f"连接失败: {e}")
            return False
    
    def _connect(self):
        """连接数据库"""
        try:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
        except sqlite3.Error as e:
            print(f"数据库连接错误: {e}")
            raise
    
    def _create_tables(self):
        """创建数据库表"""
        cursor = self.connection.cursor()
        
        # 游戏地图表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_map (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                position INTEGER NOT NULL,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                price INTEGER DEFAULT 0,
                rent_base INTEGER DEFAULT 0,
                upgrade_cost INTEGER DEFAULT 0,
                description TEXT
            )
        ''')
        
        # 游戏存档表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_saves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                save_name TEXT NOT NULL,
                save_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                game_data TEXT NOT NULL
            )
        ''')
        
        # 玩家记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS player_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_name TEXT NOT NULL,
                games_played INTEGER DEFAULT 0,
                games_won INTEGER DEFAULT 0,
                total_money_earned INTEGER DEFAULT 0,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 游戏配置表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                description TEXT
            )
        ''')
        
        self.connection.commit()
    
    def _insert_default_data(self):
        """插入默认游戏数据"""
        cursor = self.connection.cursor()
        
        # 检查是否已有地图数据
        cursor.execute('SELECT COUNT(*) FROM game_map')
        if cursor.fetchone()[0] == 0:
            # 插入默认地图数据
            map_data = [
                (0, '起点', 'start', 0, 0, 0, '经过起点获得200金币'),
                (1, '台北', 'property', 600, 50, 300, '台湾首都'),
                (2, '幸运', 'chance', 0, 0, 0, '抽取幸运卡'),
                (3, '台中', 'property', 600, 50, 300, '台湾中部城市'),
                (4, '所得税', 'tax', 0, 0, 0, '缴纳所得税200金币'),
                (5, '高雄机场', 'airport', 2000, 250, 1000, '机场'),
                (6, '高雄', 'property', 1000, 90, 500, '台湾南部大城'),
                (7, '不幸', 'misfortune', 0, 0, 0, '抽取不幸卡'),
                (8, '花莲', 'property', 1000, 90, 500, '台湾东部城市'),
                (9, '宜兰', 'property', 1200, 100, 600, '台湾东北部城市'),
                (10, '监狱', 'jail', 0, 0, 0, '监狱/探监'),
                (11, '澎湖', 'property', 1400, 110, 700, '台湾离岛'),
                (12, '电力公司', 'utility', 1500, 0, 0, '公用事业'),
                (13, '金门', 'property', 1400, 110, 700, '台湾外岛'),
                (14, '马祖', 'property', 1600, 120, 800, '台湾外岛'),
                (15, '桃园机场', 'airport', 2000, 250, 1000, '国际机场'),
                (16, '新竹', 'property', 1800, 140, 900, '科技城市'),
                (17, '幸运', 'chance', 0, 0, 0, '抽取幸运卡'),
                (18, '苗栗', 'property', 1800, 140, 900, '台湾西北部城市'),
                (19, '彰化', 'property', 2000, 150, 1000, '台湾中部城市'),
                (20, '免费停车', 'free_parking', 0, 0, 0, '免费停车场'),
                (21, '云林', 'property', 2200, 180, 1100, '农业县市'),
                (22, '不幸', 'misfortune', 0, 0, 0, '抽取不幸卡'),
                (23, '嘉义', 'property', 2200, 180, 1100, '台湾中南部城市'),
                (24, '台南', 'property', 2400, 200, 1200, '古都'),
                (25, '小港机场', 'airport', 2000, 250, 1000, '高雄机场'),
                (26, '屏东', 'property', 2600, 220, 1300, '台湾最南端'),
                (27, '台东', 'property', 2600, 220, 1300, '台湾东南部'),
                (28, '自来水公司', 'utility', 1500, 0, 0, '公用事业'),
                (29, '基隆', 'property', 2800, 240, 1400, '北部港口城市'),
                (30, '进监狱', 'go_to_jail', 0, 0, 0, '直接进监狱'),
                (31, '南投', 'property', 3000, 260, 1500, '台湾中部山区'),
                (32, '新北', 'property', 3000, 260, 1500, '台北周边城市'),
                (33, '幸运', 'chance', 0, 0, 0, '抽取幸运卡'),
                (34, '桃园', 'property', 3200, 280, 1600, '台湾西北部城市'),
                (35, '奢侈税', 'tax', 0, 0, 0, '缴纳奢侈税100金币'),
                (36, '台北101', 'landmark', 4000, 500, 2000, '台北地标建筑'),
            ]
            
            cursor.executemany('''
                INSERT INTO game_map (position, name, type, price, rent_base, upgrade_cost, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', map_data)
        
        # 插入默认配置
        config_data = [
            ('initial_money', '15000', '玩家初始资金'),
            ('start_bonus', '200', '经过起点奖励'),
            ('jail_fine', '500', '出狱罚金'),
            ('tax_rate', '0.1', '税率'),
            ('max_players', '6', '最大玩家数'),
        ]
        
        for key, value, desc in config_data:
            cursor.execute('''
                INSERT OR IGNORE INTO game_config (key, value, description)
                VALUES (?, ?, ?)
            ''', (key, value, desc))
        
        self.connection.commit()
    
    def execute_query(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """执行查询语句"""
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """执行更新语句"""
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        self.connection.commit()
        return cursor.rowcount
    
    def get_map_data(self) -> List[Dict[str, Any]]:
        """获取地图数据"""
        rows = self.execute_query('SELECT * FROM game_map ORDER BY position')
        return [dict(row) for row in rows]
    
    def save_game(self, save_name: str, game_data: str) -> bool:
        """保存游戏"""
        try:
            self.execute_update(
                'INSERT INTO game_saves (save_name, game_data) VALUES (?, ?)',
                (save_name, game_data)
            )
            return True
        except sqlite3.Error as e:
            print(f"保存游戏失败: {e}")
            return False
    
    def load_game(self, save_name: str) -> Optional[str]:
        """加载游戏"""
        rows = self.execute_query(
            'SELECT game_data FROM game_saves WHERE save_name = ? ORDER BY save_date DESC LIMIT 1',
            (save_name,)
        )
        return rows[0]['game_data'] if rows else None
    
    def get_save_list(self) -> List[Dict[str, Any]]:
        """获取存档列表"""
        rows = self.execute_query(
            'SELECT save_name, save_date FROM game_saves ORDER BY save_date DESC'
        )
        return [dict(row) for row in rows]
    
    def get_config(self, key: str) -> Optional[str]:
        """获取配置值"""
        rows = self.execute_query('SELECT value FROM game_config WHERE key = ?', (key,))
        return rows[0]['value'] if rows else None
    
    def update_config(self, key: str, value: str) -> bool:
        """更新配置"""
        try:
            self.execute_update(
                'UPDATE game_config SET value = ? WHERE key = ?',
                (value, key)
            )
            return True
        except sqlite3.Error as e:
            print(f"更新配置失败: {e}")
            return False
    
    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            self.connection = None