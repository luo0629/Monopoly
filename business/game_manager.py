import random
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import threading

from .models import (
    Player, MapCell, GameState, GameConfig, PlayerType, 
    CellType, PropertyLevel
)
from .events import EventProcessor, EventSubject
from .ai_strategy import AIPlayer, AIStrategyFactory
from data_access.database_manager import DatabaseManager

class GameManager(EventSubject):
    """游戏管理器 - 单例模式"""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(GameManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            super().__init__()
            self.db_manager = DatabaseManager()
            self.config = self._load_config()
            self.players: List[Player] = []
            self.ai_players: Dict[int, AIPlayer] = {}
            self.map_cells: List[MapCell] = []
            self.current_player_index = 0
            self.game_state = GameState.WAITING
            self.turn_count = 0
            self.event_processor = EventProcessor()
            self.game_log: List[str] = []
            self.special_effects: Dict[int, Dict[str, Any]] = {}  # 玩家特殊效果
            self.last_dice_result: Optional[Tuple[int, int, int]] = None  # 最后一次骰子结果
            self.initialized = True
            self._load_map_data()
    
    def _load_config(self) -> GameConfig:
        """从数据库加载游戏配置"""
        try:
            # 从数据库获取配置值
            config_data = {}
            config_keys = [
                'initial_money', 'start_bonus', 'jail_fine', 'tax_rate', 
                'max_players', 'board_size', 'jail_position', 'hospital_position',
                'tax_office_position', 'jail_turns', 'hospital_fee', 'min_players',
                'dice_count', 'dice_sides'
            ]
            
            for key in config_keys:
                value = self.db_manager.get_config(key)
                if value is not None:
                    # 根据键名转换数据类型
                    if key in ['tax_rate', 'game_speed']:
                        config_data[key] = float(value)
                    elif key in ['enable_sound', 'animation_enabled']:
                        config_data[key] = value.lower() == 'true'
                    else:
                        config_data[key] = int(value)
            
            return GameConfig.from_dict(config_data)
        except Exception as e:
            print(f"加载配置失败，使用默认配置: {e}")
            return GameConfig()
    
    def _load_map_data(self):
        """从数据库加载地图数据"""
        map_data = self.db_manager.get_map_data()
        self.map_cells = []
        
        for cell_data in map_data:
            cell = MapCell(
                id=cell_data['id'],
                position=cell_data['position'],
                name=cell_data['name'],
                cell_type=CellType(cell_data['type']),
                price=cell_data['price'],
                rent_base=cell_data['rent_base'],
                upgrade_cost=cell_data['upgrade_cost'],
                description=cell_data['description']
            )
            self.map_cells.append(cell)
        
        # 按位置排序
        self.map_cells.sort(key=lambda x: x.position)
    
    def create_player(self, name: str, player_type: PlayerType, 
                     avatar: str = "default", ai_difficulty: str = "medium") -> Player:
        """创建玩家"""
        if len(self.players) >= self.config.max_players:
            raise ValueError(f"玩家数量不能超过 {self.config.max_players} 人")
        
        player_id = len(self.players) + 1
        player = Player(
            id=player_id,
            name=name,
            player_type=player_type,
            money=self.config.initial_money,
            avatar=avatar
        )
        
        self.players.append(player)
        
        # 如果是AI玩家，创建AI控制器
        if player_type == PlayerType.AI:
            ai_player = AIPlayer(player, ai_difficulty)
            self.ai_players[player_id] = ai_player
        
        self._log(f"玩家 {name} 加入游戏")
        return player
    
    def start_game(self) -> bool:
        """开始游戏"""
        if len(self.players) < 2:
            return False
        
        self.game_state = GameState.PLAYING
        self.current_player_index = 0
        self.turn_count = 1
        
        # 随机决定开始顺序
        random.shuffle(self.players)
        
        self._log("游戏开始！")
        self._log(f"玩家顺序: {', '.join([p.name for p in self.players])}")
        
        return True
    
    def get_current_player(self) -> Optional[Player]:
        """获取当前玩家"""
        if not self.players or self.game_state != GameState.PLAYING:
            return None
        return self.players[self.current_player_index]
    
    def roll_dice(self) -> Tuple[int, int, int]:
        """投掷骰子，返回(骰子1, 骰子2, 总和)"""
        dice1 = random.randint(1, 6)
        dice2 = random.randint(1, 6)
        total = dice1 + dice2
        # 保存最后一次骰子结果
        self.last_dice_result = (dice1, dice2, total)
        return dice1, dice2, total
    
    def move_player(self, player: Player, steps: int) -> Dict[str, Any]:
        """移动玩家"""
        old_position = player.position
        passed_start = player.move(steps, len(self.map_cells))
        
        result = {
            "player": player,
            "old_position": old_position,
            "new_position": player.position,
            "passed_start": passed_start,
            "start_bonus": 0
        }
        
        # 经过起点获得奖励
        if passed_start:
            player.add_money(self.config.start_bonus)
            result["start_bonus"] = self.config.start_bonus
            self._log(f"{player.name} 经过起点，获得 {self.config.start_bonus} 金币")
        
        return result
    
    def get_cell_at_position(self, position: int) -> Optional[MapCell]:
        """获取指定位置的地图格子"""
        # 玩家位置从0开始，地图位置从1开始，需要转换
        map_position = position + 1
        for cell in self.map_cells:
            if cell.position == map_position:
                return cell
        return None
    
    def process_landing(self, player: Player) -> Dict[str, Any]:
        """处理玩家落地事件"""
        cell = self.get_cell_at_position(player.position)
        if not cell:
            return {"type": "error", "message": "无效位置"}
        
        result = {
            "type": "landing",
            "player": player,
            "cell": cell,
            "actions": []
        }
        
        # 根据格子类型处理
        if cell.cell_type == CellType.START:
            result["actions"].append("到达起点")
        
        elif cell.cell_type == CellType.PROPERTY:
            result.update(self._handle_property_landing(player, cell))
        
        elif cell.cell_type == CellType.AIRPORT:
            result.update(self._handle_airport_landing(player, cell))
        
        elif cell.cell_type == CellType.UTILITY:
            result.update(self._handle_utility_landing(player, cell))
        
        elif cell.cell_type == CellType.LANDMARK:
            result.update(self._handle_landmark_landing(player, cell))
        
        elif cell.cell_type == CellType.CHANCE:
            result.update(self._handle_chance_landing(player))
        
        elif cell.cell_type == CellType.MISFORTUNE:
            result.update(self._handle_misfortune_landing(player))
        
        elif cell.cell_type == CellType.TAX:
            result.update(self._handle_tax_landing(player, cell))
        
        elif cell.cell_type == CellType.GO_TO_JAIL:
            result.update(self._handle_go_to_jail(player))
        
        elif cell.cell_type == CellType.JAIL:
            result["actions"].append("探监")
        
        elif cell.cell_type == CellType.FREE_PARKING:
            result["actions"].append("免费停车")
        
        return result
    
    def _handle_property_landing(self, player: Player, cell: MapCell) -> Dict[str, Any]:
        """处理房产格子"""
        if cell.owner_id is None:
            # 无主房产，可以购买
            return {
                "type": "purchase_option",
                "can_purchase": player.money >= cell.price,
                "price": cell.price
            }
        elif cell.owner_id == player.id:
            # 自己的房产，可以升级
            return {
                "type": "upgrade_option",
                "can_upgrade": cell.can_upgrade() and player.money >= cell.upgrade_cost,
                "upgrade_cost": cell.upgrade_cost
            }
        else:
            # 别人的房产，需要付租金
            rent = cell.get_rent()
            # 检查是否有免租卡
            if "免租卡" in player.items:
                player.items.remove("免租卡")
                return {
                    "type": "rent_免除",
                    "message": "使用免租卡，免除租金"
                }
            
            player.spend_money(rent)
            owner = self.get_player_by_id(cell.owner_id)
            if owner:
                owner.add_money(rent)
            
            return {
                "type": "rent_paid",
                "rent": rent,
                "owner": owner.name if owner else "未知"
            }
    
    def _handle_airport_landing(self, player: Player, cell: MapCell) -> Dict[str, Any]:
        """处理机场格子"""
        return self._handle_property_landing(player, cell)
    
    def _handle_utility_landing(self, player: Player, cell: MapCell) -> Dict[str, Any]:
        """处理公用事业格子"""
        return self._handle_property_landing(player, cell)
    
    def _handle_landmark_landing(self, player: Player, cell: MapCell) -> Dict[str, Any]:
        """处理地标格子"""
        return self._handle_property_landing(player, cell)
    
    def _handle_chance_landing(self, player: Player) -> Dict[str, Any]:
        """处理幸运格子"""
        event = self.event_processor.get_random_chance_event()
        event_result = self.event_processor.process_event(event, player, self.players)
        
        # 通知观察者
        self.notify(event_result)
        
        return {
            "type": "chance_event",
            "event_result": event_result
        }
    
    def _handle_misfortune_landing(self, player: Player) -> Dict[str, Any]:
        """处理不幸格子"""
        event = self.event_processor.get_random_misfortune_event()
        event_result = self.event_processor.process_event(event, player, self.players)
        
        # 通知观察者
        self.notify(event_result)
        
        return {
            "type": "misfortune_event",
            "event_result": event_result
        }
    
    def _handle_tax_landing(self, player: Player, cell: MapCell) -> Dict[str, Any]:
        """处理税务格子"""
        if "所得税" in cell.name:
            tax_amount = 200
        elif "奢侈税" in cell.name:
            tax_amount = 100
        else:
            tax_amount = int(player.money * self.config.tax_rate)
        
        player.spend_money(tax_amount)
        
        return {
            "type": "tax_paid",
            "tax_amount": tax_amount,
            "tax_type": cell.name
        }
    
    def _handle_go_to_jail(self, player: Player) -> Dict[str, Any]:
        """处理进监狱"""
        player.go_to_jail()
        message = f"{player.name} 被送进监狱，需要等待 {player.jail_turns} 回合"
        self._log(message)
        self.notify({"message": message})
        
        return {
            "type": "go_to_jail",
            "message": message
        }
    
    def purchase_property(self, player: Player, cell: MapCell) -> bool:
        """购买房产"""
        if cell.owner_id is not None:
            return False
        
        # 检查是否有折扣效果
        discount = 1.0
        if player.id in self.special_effects:
            effects = self.special_effects[player.id]
            if "property_discount" in effects:
                discount = effects["property_discount"]
                del self.special_effects[player.id]["property_discount"]
        
        final_price = int(cell.price * discount)
        
        if player.buy_property(cell.position, final_price):
            cell.owner_id = player.id
            message = f"{player.name} 购买了 {cell.name}，花费 {final_price} 金币"
            self._log(message)
            # 通知界面更新日志
            self.notify({"message": message, "type": "purchase"})
            return True
        
        return False
    
    def upgrade_property(self, player: Player, cell: MapCell) -> bool:
        """升级房产"""
        if cell.owner_id != player.id or not cell.can_upgrade():
            return False
        
        upgrade_cost = cell.upgrade()
        if upgrade_cost > 0 and player.spend_money(upgrade_cost):
            message = f"{player.name} 升级了 {cell.name}，花费 {upgrade_cost} 金币"
            self._log(message)
            # 通知界面更新日志
            self.notify({"message": message, "type": "upgrade"})
            return True
        
        return False
    
    def get_player_by_id(self, player_id: int) -> Optional[Player]:
        """根据ID获取玩家"""
        for player in self.players:
            if player.id == player_id:
                return player
        return None
    
    def next_turn(self) -> bool:
        """切换到下一个玩家"""
        if self.game_state != GameState.PLAYING:
            return False
        
        # 检查游戏是否结束
        active_players = [p for p in self.players if not p.is_bankrupt]
        if len(active_players) <= 1:
            self.game_state = GameState.FINISHED
            if active_players:
                self._log(f"游戏结束！{active_players[0].name} 获胜！")
            return False
        
        # 切换到下一个未破产的玩家
        attempts = 0
        while attempts < len(self.players):
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
            current_player = self.players[self.current_player_index]
            
            if not current_player.is_bankrupt:
                if self.current_player_index == 0:
                    self.turn_count += 1
                return True
            
            attempts += 1
        
        return False
    
    def handle_ai_turn(self, player: Player) -> List[Dict[str, Any]]:
        """处理AI玩家回合"""
        if player.id not in self.ai_players:
            return []
        
        ai_player = self.ai_players[player.id]
        actions = []
        
        # AI在监狱中的决策
        if player.is_in_jail:
            jail_action = ai_player.make_jail_decision()
            if jail_action == "pay":
                if player.try_leave_jail(pay_fine=True):
                    message = f"{player.name} 付费出狱"
                    self._log(message)
                    self.notify({"message": message})
                    actions.append({"type": "jail_pay", "message": message})
            elif jail_action == "use_item" and "免狱卡" in player.items:
                player.items.remove("免狱卡")
                player.try_leave_jail()
                message = f"{player.name} 使用免狱卡出狱"
                self._log(message)
                self.notify({"message": message})
                actions.append({"type": "jail_item", "message": message})
            elif jail_action == "wait":
                if not player.try_leave_jail():
                    message = f"{player.name} 在监狱中等待，剩余 {player.jail_turns} 回合"
                    self._log(message)
                    self.notify({"message": message})
                    actions.append({"type": "jail_wait", "message": message})
                else:
                    message = f"{player.name} 监狱期满，自动出狱！"
                    self._log(message)
                    self.notify({"message": message})
                    actions.append({"type": "jail_release", "message": message})
        
        # AI交易决策
        trade_decision = ai_player.make_trade_decision(self.players, self.map_cells)
        if trade_decision:
            actions.append({"type": "trade_attempt", "decision": trade_decision})
        
        return actions
    
    def save_game(self, save_name: str) -> bool:
        """保存游戏"""
        game_data = {
            "config": self.config.to_dict(),
            "players": [p.to_dict() for p in self.players],
            "map_cells": [c.to_dict() for c in self.map_cells],
            "current_player_index": self.current_player_index,
            "game_state": self.game_state.value,
            "turn_count": self.turn_count,
            "ai_players": {str(k): v.get_difficulty() for k, v in self.ai_players.items()},
            "special_effects": self.special_effects,
            "save_timestamp": datetime.now().isoformat()
        }
        
        return self.db_manager.save_game(save_name, json.dumps(game_data))
    
    def load_game(self, save_name: str) -> bool:
        """加载游戏"""
        game_data_str = self.db_manager.load_game(save_name)
        if not game_data_str:
            return False
        
        try:
            game_data = json.loads(game_data_str)
            
            # 恢复配置
            self.config = GameConfig.from_dict(game_data["config"])
            
            # 恢复玩家
            self.players = [Player.from_dict(p) for p in game_data["players"]]
            
            # 恢复地图
            self.map_cells = [MapCell.from_dict(c) for c in game_data["map_cells"]]
            
            # 恢复游戏状态
            self.current_player_index = game_data["current_player_index"]
            self.game_state = GameState(game_data["game_state"])
            self.turn_count = game_data["turn_count"]
            self.special_effects = game_data.get("special_effects", {})
            
            # 恢复AI玩家
            self.ai_players = {}
            ai_data = game_data.get("ai_players", {})
            for player in self.players:
                if player.player_type == PlayerType.AI:
                    difficulty = ai_data.get(str(player.id), "medium")
                    self.ai_players[player.id] = AIPlayer(player, difficulty)
            
            self._log(f"游戏 '{save_name}' 加载成功")
            return True
            
        except (json.JSONDecodeError, KeyError) as e:
            self._log(f"加载游戏失败: {e}")
            return False
    
    def _log(self, message: str):
        """记录游戏日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.game_log.append(log_entry)
        print(log_entry)  # 同时输出到控制台
    
    def get_game_log(self) -> List[str]:
        """获取游戏日志"""
        return self.game_log.copy()
    
    def get_game_state_dict(self) -> Dict[str, Any]:
        """获取游戏状态字典"""
        return {
            "players": [p.to_dict() for p in self.players],
            "current_player": self.current_player_index,
            "game_state": self.game_state.value,
            "turn_count": self.turn_count,
            "map_cells": [c.to_dict() for c in self.map_cells]
        }
    
    def reset_game(self):
        """重置游戏"""
        self.players.clear()
        self.ai_players.clear()
        self.current_player_index = 0
        self.game_state = GameState.WAITING
        self.turn_count = 0
        self.game_log.clear()
        self.special_effects.clear()
        self._load_map_data()  # 重新加载地图数据
        self._log("游戏已重置")