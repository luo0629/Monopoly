import random
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from Model.models import GameEvent, Player
from .abstract_factory import GameFactoryManager
class EventFactory:
    """事件工厂类"""
    
    @staticmethod
    def create_chance_events(game_mode: str = "standard") -> List[GameEvent]:
        """创建幸运事件列表"""       
        # 使用抽象工厂模式
        factory = GameFactoryManager.get_factory(game_mode)
        return factory.create_chance_events()
    

    
    @staticmethod
    def create_misfortune_events(game_mode: str = "standard") -> List[GameEvent]:
        """创建不幸事件列表"""       
        # 使用抽象工厂模式
        factory = GameFactoryManager.get_factory(game_mode)
        return factory.create_misfortune_events()
    


class EventProcessor:
    """事件处理器"""
    
    def __init__(self, game_mode: str = "standard"):
        self.game_mode = game_mode
        self.chance_events = EventFactory.create_chance_events(game_mode)
        self.misfortune_events = EventFactory.create_misfortune_events(game_mode)
    
    def get_random_chance_event(self) -> GameEvent:
        """获取随机幸运事件"""
        return random.choice(self.chance_events)
    
    def get_random_misfortune_event(self) -> GameEvent:
        """获取随机不幸事件"""
        return random.choice(self.misfortune_events)
    
    def process_event(self, event: GameEvent, player: Player, all_players: List[Player]) -> Dict[str, Any]:
        """处理事件效果"""
        result = {
            "event": event,
            "message": f"{player.name}: {event.title} - {event.description}",
            "effects": []
        }
        
        effect = event.effect
        
        # 处理金钱变化
        if "money" in effect:
            amount = effect["money"]
            if amount > 0:
                player.add_money(amount)
                result["effects"].append(f"获得 {amount} 金币")
            else:
                player.spend_money(abs(amount))
                result["effects"].append(f"失去 {abs(amount)} 金币")
        
        # 处理生日事件
        if "birthday" in effect:
            amount_per_player = effect["birthday"]
            total_received = 0
            for other_player in all_players:
                if other_player.id != player.id and not other_player.is_bankrupt:
                    if other_player.spend_money(amount_per_player):
                        total_received += amount_per_player
            player.add_money(total_received)
            result["effects"].append(f"从其他玩家处获得 {total_received} 金币")
        
        # 处理房屋维修
        if "house_repair" in effect:
            repair_cost = effect["house_repair"]
            total_cost = len(player.properties) * repair_cost
            player.spend_money(total_cost)
            result["effects"].append(f"房屋维修费用 {total_cost} 金币")
        
        # 处理额外税收
        if "tax_extra" in effect:
            tax_rate = effect["tax_extra"]
            tax_amount = int(player.money * tax_rate)
            player.spend_money(tax_amount)
            result["effects"].append(f"额外缴税 {tax_amount} 金币")
        
        # 处理进监狱
        if "go_to_jail" in effect and effect["go_to_jail"]:
            player.go_to_jail()
            result["effects"].append("直接进监狱")
        
        # 处理后退
        if "move_back" in effect:
            steps = effect["move_back"]
            player.position = max(0, player.position - steps)
            result["effects"].append(f"后退 {steps} 步")
        
        # 处理道具
        if "item" in effect:
            item = effect["item"]
            player.items.append(item)
            result["effects"].append(f"获得道具: {item}")
        
        # 处理特殊效果（需要在游戏逻辑中处理）
        if "free_move" in effect:
            result["special_effect"] = "free_move"
        
        if "extra_turn" in effect:
            result["special_effect"] = "extra_turn"
        
        if "discount" in effect:
            result["special_effect"] = "property_discount"
            result["discount_rate"] = effect["discount"]
        
        return result

class EventObserver(ABC):
    """事件观察者接口 - 观察者模式"""
    
    @abstractmethod
    def on_event_triggered(self, event_result: Dict[str, Any]):
        """事件触发时的回调"""
        pass

class EventSubject:
    """事件主题类 - 观察者模式"""
    
    def __init__(self):
        self._observers: List[EventObserver] = []
    
    def attach(self, observer: EventObserver):
        """添加观察者"""
        self._observers.append(observer)
    
    def detach(self, observer: EventObserver):
        """移除观察者"""
        if observer in self._observers:
            self._observers.remove(observer)
    
    def notify(self, event_result: Dict[str, Any]):
        """通知所有观察者"""
        for observer in self._observers:
            observer.on_event_triggered(event_result)