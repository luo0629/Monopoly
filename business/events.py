import random
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from .models import GameEvent, Player

class EventFactory:
    """事件工厂类 - 工厂模式"""
    
    @staticmethod
    def create_chance_events() -> List[GameEvent]:
        """创建幸运事件列表"""
        return [
            GameEvent(
                event_type="money",
                title="银行分红",
                description="你的投资获得回报，银行给你分红！",
                effect={"money": 500}
            ),
            GameEvent(
                event_type="money",
                title="彩票中奖",
                description="恭喜你中了彩票大奖！",
                effect={"money": 1000}
            ),
            GameEvent(
                event_type="money",
                title="股票上涨",
                description="你持有的股票大涨，获得丰厚收益！",
                effect={"money": 800}
            ),
            GameEvent(
                event_type="move",
                title="免费旅行",
                description="获得免费旅行机会，可以移动到任意位置！",
                effect={"free_move": True}
            ),
            GameEvent(
                event_type="roll_again",
                title="再投一次",
                description="幸运女神眷顾，你可以再投一次骰子！",
                effect={"extra_turn": True}
            ),
            GameEvent(
                event_type="money",
                title="房租减免",
                description="政府房租减免政策，你获得补贴！",
                effect={"money": 300}
            ),
            GameEvent(
                event_type="item",
                title="获得道具",
                description="你找到了一张免租卡！",
                effect={"item": "免租卡"}
            ),
            GameEvent(
                event_type="money",
                title="生日快乐",
                description="今天是你的生日，每个玩家给你50金币！",
                effect={"birthday": 50}
            ),
            GameEvent(
                event_type="money",
                title="工作奖金",
                description="你的出色工作获得了老板的奖金！",
                effect={"money": 400}
            ),
            GameEvent(
                event_type="property_discount",
                title="房产折扣",
                description="下次购买房产可享受8折优惠！",
                effect={"discount": 0.8}
            )
        ]
    
    @staticmethod
    def create_misfortune_events() -> List[GameEvent]:
        """创建不幸事件列表"""
        return [
            GameEvent(
                event_type="money",
                title="医疗费用",
                description="你生病了，需要支付医疗费用。",
                effect={"money": -300}
            ),
            GameEvent(
                event_type="money",
                title="车辆维修",
                description="你的车坏了，需要支付维修费。",
                effect={"money": -200}
            ),
            GameEvent(
                event_type="jail",
                title="违章停车",
                description="你违章停车被抓，直接进监狱！",
                effect={"go_to_jail": True}
            ),
            GameEvent(
                event_type="money",
                title="投资失败",
                description="你的投资项目失败了，损失惨重！",
                effect={"money": -500}
            ),
            GameEvent(
                event_type="money",
                title="房屋维修",
                description="你的房产需要维修，每处房产支付100金币。",
                effect={"house_repair": 100}
            ),
            GameEvent(
                event_type="money",
                title="罚款通知",
                description="你收到了一张罚款单。",
                effect={"money": -150}
            ),
            GameEvent(
                event_type="move_back",
                title="迷路了",
                description="你迷路了，需要后退3步。",
                effect={"move_back": 3}
            ),
            GameEvent(
                event_type="money",
                title="税务检查",
                description="税务局检查，需要额外缴税。",
                effect={"tax_extra": 0.05}
            ),
            GameEvent(
                event_type="money",
                title="手机丢失",
                description="你的手机丢了，需要买新的。",
                effect={"money": -250}
            ),
            GameEvent(
                event_type="money",
                title="信用卡被盗刷",
                description="你的信用卡被盗刷了！",
                effect={"money": -400}
            )
        ]

class EventProcessor:
    """事件处理器"""
    
    def __init__(self):
        self.chance_events = EventFactory.create_chance_events()
        self.misfortune_events = EventFactory.create_misfortune_events()
    
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