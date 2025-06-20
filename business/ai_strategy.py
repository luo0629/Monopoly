import random
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from .models import Player, MapCell, CellType, PropertyLevel

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

class EasyAIStrategy(AIStrategy):
    """简单AI策略 - 保守型"""
    
    def decide_purchase(self, player: Player, cell: MapCell, game_state: Dict[str, Any]) -> bool:
        """简单AI购买决策：只在有足够资金时购买便宜房产"""
        if cell.cell_type not in [CellType.PROPERTY, CellType.AIRPORT, CellType.UTILITY]:
            return False
        
        # 保留至少3000金币作为安全资金
        safety_money = 3000
        available_money = player.money - safety_money
        
        # 只购买价格低于2000且有足够资金的房产
        if cell.price <= 2000 and available_money >= cell.price:
            return True
        
        return False
    
    def decide_upgrade(self, player: Player, properties: List[MapCell]) -> Optional[int]:
        """简单AI升级决策：很少升级"""
        # 只有在资金充足时才考虑升级最便宜的房产
        if player.money < 5000:
            return None
        
        upgradeable = [p for p in properties if p.can_upgrade() and p.owner_id == player.id]
        if not upgradeable:
            return None
        
        # 随机决定是否升级（30%概率）
        if random.random() < 0.3:
            # 选择升级成本最低的房产
            cheapest = min(upgradeable, key=lambda p: p.upgrade_cost)
            if player.money >= cheapest.upgrade_cost + 2000:  # 保留安全资金
                return cheapest.position
        
        return None
    
    def decide_jail_action(self, player: Player) -> str:
        """简单AI监狱决策：通常等待"""
        # 如果资金充足且剩余轮数较多，考虑付费出狱
        if player.money > 3000 and player.jail_turns > 1:
            return "pay" if random.random() < 0.3 else "wait"
        return "wait"
    
    def decide_trade(self, player: Player, other_players: List[Player], 
                    properties: List[MapCell]) -> Optional[Dict[str, Any]]:
        """简单AI交易决策：很少交易"""
        # 简单AI不主动交易
        return None

class MediumAIStrategy(AIStrategy):
    """中等AI策略 - 平衡型"""
    
    def decide_purchase(self, player: Player, cell: MapCell, game_state: Dict[str, Any]) -> bool:
        """中等AI购买决策：考虑投资回报率"""
        if cell.cell_type not in [CellType.PROPERTY, CellType.AIRPORT, CellType.UTILITY]:
            return False
        
        # 计算投资回报率
        if cell.price == 0:
            return False
        
        roi = cell.rent_base / cell.price if cell.price > 0 else 0
        
        # 保留安全资金
        safety_money = 2000
        available_money = player.money - safety_money
        
        # 根据ROI和资金情况决定
        if available_money >= cell.price:
            if roi > 0.08:  # ROI超过8%
                return True
            elif roi > 0.05 and cell.price < 3000:  # ROI超过5%且价格合理
                return True
            elif len(player.properties) < 3:  # 房产数量少时更积极
                return True
        
        return False
    
    def decide_upgrade(self, player: Player, properties: List[MapCell]) -> Optional[int]:
        """中等AI升级决策：优先升级高收益房产"""
        if player.money < 3000:
            return None
        
        upgradeable = [p for p in properties if p.can_upgrade() and p.owner_id == player.id]
        if not upgradeable:
            return None
        
        # 计算升级后的收益增长
        best_property = None
        best_roi = 0
        
        for prop in upgradeable:
            current_rent = prop.get_rent()
            # 模拟升级后的租金
            temp_level = PropertyLevel(prop.level.value + 1)
            future_rent = prop.rent_base * (2 ** temp_level.value) if temp_level.value > 0 else prop.rent_base
            
            rent_increase = future_rent - current_rent
            upgrade_roi = rent_increase / prop.upgrade_cost if prop.upgrade_cost > 0 else 0
            
            if upgrade_roi > best_roi and player.money >= prop.upgrade_cost + 1500:
                best_roi = upgrade_roi
                best_property = prop
        
        # 50%概率执行最佳升级
        if best_property and random.random() < 0.5:
            return best_property.position
        
        return None
    
    def decide_jail_action(self, player: Player) -> str:
        """中等AI监狱决策：权衡利弊"""
        # 如果有免狱卡，优先使用
        if "免狱卡" in player.items:
            return "use_item"
        
        # 根据资金和剩余轮数决定
        if player.money > 2000:
            if player.jail_turns >= 2:
                return "pay"
            else:
                return "wait" if random.random() < 0.6 else "pay"
        
        return "wait"
    
    def decide_trade(self, player: Player, other_players: List[Player], 
                    properties: List[MapCell]) -> Optional[Dict[str, Any]]:
        """中等AI交易决策：偶尔交易"""
        # 30%概率考虑交易
        if random.random() > 0.3:
            return None
        
        # 寻找可能的交易对象
        for other_player in other_players:
            if other_player.is_bankrupt or other_player.id == player.id:
                continue
            
            # 简单的交易逻辑：用金钱购买对方的低价值房产
            other_properties = [p for p in properties if p.owner_id == other_player.id]
            if other_properties:
                cheapest = min(other_properties, key=lambda p: p.price)
                offer_price = int(cheapest.price * 1.2)  # 溢价20%
                
                if player.money >= offer_price + 2000:  # 保留安全资金
                    return {
                        "type": "buy_property",
                        "target_player": other_player.id,
                        "property_id": cheapest.position,
                        "offer_money": offer_price
                    }
        
        return None

class HardAIStrategy(AIStrategy):
    """困难AI策略 - 激进型"""
    
    def decide_purchase(self, player: Player, cell: MapCell, game_state: Dict[str, Any]) -> bool:
        """困难AI购买决策：激进投资策略"""
        if cell.cell_type not in [CellType.PROPERTY, CellType.AIRPORT, CellType.UTILITY, CellType.LANDMARK]:
            return False
        
        # 更激进的资金管理
        safety_money = 1000
        available_money = player.money - safety_money
        
        if available_money >= cell.price:
            # 优先购买高价值房产
            if cell.cell_type == CellType.LANDMARK:
                return True
            elif cell.cell_type == CellType.AIRPORT:
                return True
            elif cell.price > 2000:  # 偏好高价房产
                return True
            elif len(player.properties) < 5:  # 积极扩张
                return True
        
        return False
    
    def decide_upgrade(self, player: Player, properties: List[MapCell]) -> Optional[int]:
        """困难AI升级决策：积极升级高价值房产"""
        if player.money < 2000:
            return None
        
        upgradeable = [p for p in properties if p.can_upgrade() and p.owner_id == player.id]
        if not upgradeable:
            return None
        
        # 优先升级高价值房产
        high_value = [p for p in upgradeable if p.price >= 2000]
        target_properties = high_value if high_value else upgradeable
        
        # 选择租金最高的房产升级
        best_property = max(target_properties, key=lambda p: p.get_rent())
        
        if player.money >= best_property.upgrade_cost + 1000:
            # 70%概率执行升级
            if random.random() < 0.7:
                return best_property.position
        
        return None
    
    def decide_jail_action(self, player: Player) -> str:
        """困难AI监狱决策：倾向于快速出狱"""
        # 优先使用道具
        if "免狱卡" in player.items:
            return "use_item"
        
        # 激进的出狱策略
        if player.money > 1500:
            return "pay"
        elif player.jail_turns >= 2:
            return "pay" if player.money >= 500 else "wait"
        
        return "wait"
    
    def decide_trade(self, player: Player, other_players: List[Player], 
                    properties: List[MapCell]) -> Optional[Dict[str, Any]]:
        """困难AI交易决策：积极寻求有利交易"""
        # 60%概率考虑交易
        if random.random() > 0.6:
            return None
        
        # 寻找战略性交易机会
        for other_player in other_players:
            if other_player.is_bankrupt or other_player.id == player.id:
                continue
            
            other_properties = [p for p in properties if p.owner_id == other_player.id]
            
            # 寻找高价值房产
            valuable_properties = [p for p in other_properties if p.price >= 2000]
            
            if valuable_properties:
                target = max(valuable_properties, key=lambda p: p.price)
                offer_price = int(target.price * 1.5)  # 溢价50%
                
                if player.money >= offer_price + 1000:
                    return {
                        "type": "buy_property",
                        "target_player": other_player.id,
                        "property_id": target.position,
                        "offer_money": offer_price
                    }
            
            # 考虑复合交易（房产+金钱）
            if len(player.properties) > 2 and other_player.money > 1000:
                my_properties = [p for p in properties if p.owner_id == player.id]
                if my_properties:
                    trade_property = min(my_properties, key=lambda p: p.price)
                    return {
                        "type": "complex_trade",
                        "target_player": other_player.id,
                        "give_property": trade_property.position,
                        "request_money": int(trade_property.price * 1.3)
                    }
        
        return None

class AIStrategyFactory:
    """AI策略工厂 - 工厂模式"""
    
    @staticmethod
    def create_strategy(difficulty: str) -> AIStrategy:
        """根据难度创建AI策略"""
        strategies = {
            "easy": EasyAIStrategy,
            "medium": MediumAIStrategy,
            "hard": HardAIStrategy
        }
        
        strategy_class = strategies.get(difficulty.lower(), MediumAIStrategy)
        return strategy_class()

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