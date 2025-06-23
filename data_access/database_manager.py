import sqlite3
import os
import json
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
    
    def _load_map_from_json(self) -> List[tuple]:
        """从JSON配置文件加载地图数据"""
        try:
            json_path = os.path.join(os.path.dirname(self.db_path), 'default_map.json')
            with open(json_path, 'r', encoding='utf-8') as f:
                map_config = json.load(f)
            
            map_data = []
            for cell in map_config['cells']:
                map_data.append((
                    cell['position'],
                    cell['name'],
                    cell['type'],
                    cell['price'],
                    cell['rent'],
                    cell['upgrade_cost'],
                    cell['description']
                ))
            
            return map_data
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            print(f"加载地图配置文件失败: {e}")
            # 如果配置文件加载失败，返回基本的起点数据
            return [(0, '起点', 'start', 0, 0, 0, '游戏起始位置')]
    
    def _insert_default_data(self):
        """插入默认游戏数据"""
        cursor = self.connection.cursor()
        
        # 检查是否已有地图数据
        cursor.execute('SELECT COUNT(*) FROM game_map')
        if cursor.fetchone()[0] == 0:
            # 从JSON配置文件加载地图数据
            map_data = self._load_map_from_json()
            
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
        """保存游戏 - 如果存档已存在则覆盖"""
        try:
            # 检查是否已存在同名存档
            existing = self.execute_query(
                'SELECT id FROM game_saves WHERE save_name = ?',
                (save_name,)
            )
            
            if existing:
                # 存档已存在，更新现有记录
                self.execute_update(
                    'UPDATE game_saves SET game_data = ?, save_date = CURRENT_TIMESTAMP WHERE save_name = ?',
                    (game_data, save_name)
                )
            else:
                # 存档不存在，插入新记录
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
    
    def delete_save(self, save_name: str) -> bool:
        """删除存档"""
        try:
            self.execute_update(
                'DELETE FROM game_saves WHERE save_name = ?',
                (save_name,)
            )
            return True
        except sqlite3.Error as e:
            print(f"删除存档失败: {e}")
            return False
    
    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            self.connection = None