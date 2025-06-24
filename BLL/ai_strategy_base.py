from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from Model.models import Player, MapCell

class AIStrategy(ABC):
    """AI策略接口 - 策略模式"""
    
    @abstractmethod
    def decide_purchase(self, player: Player, cell: MapCell, game_state: Dict[str, Any]) -> bool:
        """决定是否购买房产"""
        pass
    
    @abstractmethod
    def decide_upgrade(self, player: Player, properties: List[MapCell]) -> Optional[int]:
        """决定升级哪个房产"""
        pass
    
    @abstractmethod
    def decide_jail_action(self, player: Player) -> str:
        """决定在监狱中的行动：'pay', 'wait', 'use_item'"""
        pass
    
    @abstractmethod
    def decide_trade(self, player: Player, other_players: List[Player], 
                    properties: List[MapCell]) -> Optional[Dict[str, Any]]:
        """决定是否进行交易"""
        pass
class AIStrategyFactory:
    """AI策略工厂 -抽象工厂模式"""
    
    @staticmethod
    def create_strategy(difficulty: str, game_mode: str = "standard") -> AIStrategy:
        """根据难度和游戏模式创建AI策略"""
        from .abstract_factory import GameFactoryManager
        
        # 使用抽象工厂模式
        factory = GameFactoryManager.get_factory(game_mode)
        return factory.create_ai_strategy(difficulty)

class AIPlayer:
    """AI玩家控制器"""
    
    def __init__(self, player: Player, difficulty: str = "medium"):
        self.player = player
        self.strategy = AIStrategyFactory.create_strategy(difficulty)
        self.difficulty = difficulty
    
    def make_purchase_decision(self, cell: MapCell, game_state: Dict[str, Any]) -> bool:
        """做出购买决策"""
        return self.strategy.decide_purchase(self.player, cell, game_state)
    
    def make_upgrade_decision(self, properties: List[MapCell]) -> Optional[int]:
        """做出升级决策"""
        return self.strategy.decide_upgrade(self.player, properties)
    
    def make_jail_decision(self) -> str:
        """做出监狱行动决策"""
        return self.strategy.decide_jail_action(self.player)
    
    def make_trade_decision(self, other_players: List[Player], 
                          properties: List[MapCell]) -> Optional[Dict[str, Any]]:
        """做出交易决策"""
        return self.strategy.decide_trade(self.player, other_players, properties)
    
    def get_difficulty(self) -> str:
        """获取AI难度"""
        return self.difficulty