from enum import Enum
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json

class PlayerType(Enum):
    """玩家类型枚举"""
    HUMAN = "human"
    AI = "ai"

class CellType(Enum):
    """地图格子类型枚举"""
    START = "start"              # 起点
    PROPERTY = "property"        # 房产
    CHANCE = "chance"            # 幸运
    MISFORTUNE = "misfortune"    # 不幸
    TAX = "tax"                  # 税务
    JAIL = "jail"                # 监狱
    GO_TO_JAIL = "go_to_jail"    # 进监狱
    FREE_PARKING = "free_parking" # 免费停车
    AIRPORT = "airport"          # 机场
    UTILITY = "utility"          # 公用事业
    LANDMARK = "landmark"        # 地标
    HOSPITAL = "hospital"        # 医院
    LUXURY_TAX = "luxury_tax"    # 奢侈税

class PropertyLevel(Enum):
    """房产等级枚举"""
    EMPTY = 0      # 空地
    HOUSE_1 = 1    # 1级房屋
    HOUSE_2 = 2    # 2级房屋
    HOUSE_3 = 3    # 3级房屋
    HOTEL = 4      # 酒店

class GameState(Enum):
    """游戏状态枚举"""
    WAITING = "waiting"          # 等待开始
    PLAYING = "playing"          # 游戏中
    PAUSED = "paused"            # 暂停
    FINISHED = "finished"        # 结束

@dataclass
class Player:
    """玩家类"""
    id: int
    name: str
    player_type: PlayerType
    money: int = 15000
    position: int = 0
    avatar: str = "default"
    is_in_jail: bool = False
    jail_turns: int = 0
    is_bankrupt: bool = False
    properties: List[int] = field(default_factory=list)
    items: List[str] = field(default_factory=list)
    
    def move(self, steps: int, board_size: int = 36):
        """移动玩家"""
        old_position = self.position
        self.position = (self.position + steps) % board_size
        # 检查是否经过起点
        return self.position < old_position or (old_position + steps >= board_size)
    
    def add_money(self, amount: int):
        """增加金钱"""
        self.money += amount
    
    def spend_money(self, amount: int) -> bool:
        """花费金钱"""
        if self.money >= amount:
            self.money -= amount
            return True
        return False
    
    def buy_property(self, property_id: int, price: int) -> bool:
        """购买房产"""
        if self.spend_money(price):
            self.properties.append(property_id)
            return True
        return False
    
    def sell_property(self, property_id: int, price: int):
        """出售房产"""
        if property_id in self.properties:
            self.properties.remove(property_id)
            self.add_money(price)
    
    def go_to_jail(self):
        """进监狱"""
        self.is_in_jail = True
        self.jail_turns = 3
        self.position = 9  # 监狱位置（玩家位置从0开始，监狱是地图位置10，对应玩家位置9）
    
    def try_leave_jail(self, pay_fine: bool = False) -> bool:
        """尝试出狱"""
        if not self.is_in_jail:
            return True
        
        if pay_fine and self.spend_money(500):
            self.is_in_jail = False
            self.jail_turns = 0
            return True
        
        self.jail_turns -= 1
        if self.jail_turns <= 0:
            self.is_in_jail = False
            return True
        
        return False
    
    def check_bankruptcy(self) -> bool:
        """检查是否破产"""
        if self.money < 0:
            self.is_bankrupt = True
        return self.is_bankrupt
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'player_type': self.player_type.value,
            'money': self.money,
            'position': self.position,
            'avatar': self.avatar,
            'is_in_jail': self.is_in_jail,
            'jail_turns': self.jail_turns,
            'is_bankrupt': self.is_bankrupt,
            'properties': self.properties,
            'items': self.items
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Player':
        """从字典创建玩家"""
        return cls(
            id=data['id'],
            name=data['name'],
            player_type=PlayerType(data['player_type']),
            money=data['money'],
            position=data['position'],
            avatar=data['avatar'],
            is_in_jail=data['is_in_jail'],
            jail_turns=data['jail_turns'],
            is_bankrupt=data['is_bankrupt'],
            properties=data['properties'],
            items=data['items']
        )

@dataclass
class MapCell:
    """地图格子类"""
    id: int
    position: int
    name: str
    cell_type: CellType
    price: int = 0
    rent_base: int = 0
    upgrade_cost: int = 0
    description: str = ""
    owner_id: Optional[int] = None
    level: PropertyLevel = PropertyLevel.EMPTY
    
    def get_rent(self) -> int:
        """获取租金"""
        if self.cell_type not in [CellType.PROPERTY, CellType.AIRPORT, CellType.LANDMARK]:
            return 0
        
        base_rent = self.rent_base
        if self.level == PropertyLevel.EMPTY:
            return base_rent
        elif self.level == PropertyLevel.HOUSE_1:
            return base_rent * 2
        elif self.level == PropertyLevel.HOUSE_2:
            return base_rent * 4
        elif self.level == PropertyLevel.HOUSE_3:
            return base_rent * 8
        elif self.level == PropertyLevel.HOTEL:
            return base_rent * 16
        
        return base_rent
    
    def can_upgrade(self) -> bool:
        """是否可以升级"""
        return (self.cell_type == CellType.PROPERTY and 
                self.owner_id is not None and 
                self.level.value < PropertyLevel.HOTEL.value)
    
    def get_upgrade_cost(self) -> int:
        """获取升级费用"""
        return self.upgrade_cost
    
    def upgrade(self) -> int:
        """升级房产，返回升级费用"""
        if self.can_upgrade():
            self.level = PropertyLevel(self.level.value + 1)
            return self.upgrade_cost
        return 0
    
    def reset_ownership(self):
        """重置所有权"""
        self.owner_id = None
        self.level = PropertyLevel.EMPTY
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'position': self.position,
            'name': self.name,
            'cell_type': self.cell_type.value,
            'price': self.price,
            'rent_base': self.rent_base,
            'upgrade_cost': self.upgrade_cost,
            'description': self.description,
            'owner_id': self.owner_id,
            'level': self.level.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MapCell':
        """从字典创建地图格子"""
        return cls(
            id=data['id'],
            position=data['position'],
            name=data['name'],
            cell_type=CellType(data['cell_type']),
            price=data['price'],
            rent_base=data['rent_base'],
            upgrade_cost=data['upgrade_cost'],
            description=data['description'],
            owner_id=data['owner_id'],
            level=PropertyLevel(data['level'])
        )

@dataclass
class GameEvent:
    """游戏事件类"""
    event_type: str
    title: str
    description: str
    effect: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_type': self.event_type,
            'title': self.title,
            'description': self.description,
            'effect': self.effect
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameEvent':
        return cls(
            event_type=data['event_type'],
            title=data['title'],
            description=data['description'],
            effect=data['effect']
        )

@dataclass
class GameConfig:
    """游戏配置类"""
    initial_money: int = 15000
    start_bonus: int = 200
    jail_fine: int = 500
    tax_rate: float = 0.1
    max_players: int = 6
    board_size: int = 37
    jail_position: int = 10
    hospital_position: int = 20
    tax_office_position: int = 30
    jail_turns: int = 3
    hospital_fee: int = 1000
    min_players: int = 2
    dice_count: int = 2
    dice_sides: int = 6
    auto_save_interval: int = 300
    max_save_slots: int = 10
    enable_sound: bool = True
    animation_enabled: bool = True
    game_speed: float = 1.0
    bankruptcy_threshold: int = 0
    property_mortgage_rate: float = 0.5
    hotel_limit: int = 4
    house_limit: int = 32
    auction_enabled: bool = True
    trading_enabled: bool = True
    time_limit_per_turn: int = 300
    sound_enabled: bool = True
    difficulty_level: str = "medium"
    language: str = "zh_CN"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'initial_money': self.initial_money,
            'start_bonus': self.start_bonus,
            'jail_fine': self.jail_fine,
            'tax_rate': self.tax_rate,
            'max_players': self.max_players,
            'board_size': self.board_size,
            'jail_position': self.jail_position,
            'hospital_position': self.hospital_position,
            'tax_office_position': self.tax_office_position,
            'jail_turns': self.jail_turns,
            'hospital_fee': self.hospital_fee,
            'min_players': self.min_players,
            'dice_count': self.dice_count,
            'dice_sides': self.dice_sides,
            'auto_save_interval': self.auto_save_interval,
            'max_save_slots': self.max_save_slots,
            'enable_sound': self.enable_sound,
            'animation_enabled': self.animation_enabled,
            'game_speed': self.game_speed,
            'bankruptcy_threshold': self.bankruptcy_threshold,
            'property_mortgage_rate': self.property_mortgage_rate,
            'hotel_limit': self.hotel_limit,
            'house_limit': self.house_limit,
            'auction_enabled': self.auction_enabled,
            'trading_enabled': self.trading_enabled,
            'time_limit_per_turn': self.time_limit_per_turn,
            'sound_enabled': self.sound_enabled,
            'difficulty_level': self.difficulty_level,
            'language': self.language
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameConfig':
        return cls(
            initial_money=data.get('initial_money', 15000),
            start_bonus=data.get('start_bonus', 200),
            jail_fine=data.get('jail_fine', 500),
            tax_rate=data.get('tax_rate', 0.1),
            max_players=data.get('max_players', 6),
            board_size=data.get('board_size', 37),
            jail_position=data.get('jail_position', 10),
            hospital_position=data.get('hospital_position', 20),
            tax_office_position=data.get('tax_office_position', 30),
            jail_turns=data.get('jail_turns', 3),
            hospital_fee=data.get('hospital_fee', 1000),
            min_players=data.get('min_players', 2),
            dice_count=data.get('dice_count', 2),
            dice_sides=data.get('dice_sides', 6),
            auto_save_interval=data.get('auto_save_interval', 300),
            max_save_slots=data.get('max_save_slots', 10),
            enable_sound=data.get('enable_sound', True),
            animation_enabled=data.get('animation_enabled', True),
            game_speed=data.get('game_speed', 1.0),
            bankruptcy_threshold=data.get('bankruptcy_threshold', 0),
            property_mortgage_rate=data.get('property_mortgage_rate', 0.5),
            hotel_limit=data.get('hotel_limit', 4),
            house_limit=data.get('house_limit', 32),
            auction_enabled=data.get('auction_enabled', True),
            trading_enabled=data.get('trading_enabled', True),
            time_limit_per_turn=data.get('time_limit_per_turn', 300),
            sound_enabled=data.get('sound_enabled', True),
            difficulty_level=data.get('difficulty_level', 'medium'),
            language=data.get('language', 'zh_CN')
        )