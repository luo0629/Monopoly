from typing import List, Dict, Any
from .models import GameEvent
from .ai_strategy import AIStrategy, EasyAIStrategy, MediumAIStrategy, HardAIStrategy
from .abstract_factory import AbstractGameFactory

# 具体工厂1：标准游戏工厂
class StandardGameFactory(AbstractGameFactory):
    """标准游戏工厂 - 创建标准难度的游戏组件"""
    
    def create_ai_strategy(self, difficulty: str) -> AIStrategy:
        """创建标准AI策略"""
        strategies = {
            "easy": EasyAIStrategy,
            "medium": MediumAIStrategy,
            "hard": HardAIStrategy
        }
        strategy_class = strategies.get(difficulty.lower(), MediumAIStrategy)
        return strategy_class()
    
    def create_chance_events(self) -> List[GameEvent]:
        """创建标准幸运事件"""
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
            )
        ]
    
    def create_misfortune_events(self) -> List[GameEvent]:
        """创建标准不幸事件"""
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
            )
        ]

# 具体工厂2：困难模式游戏工厂
class HardModeGameFactory(AbstractGameFactory):
    """困难模式游戏工厂 - 创建更具挑战性的游戏组件"""
    
    def create_ai_strategy(self, difficulty: str) -> AIStrategy:
        """创建困难模式AI策略（所有AI都更聪明）"""
        # 在困难模式下，即使是简单AI也使用中等策略
        strategies = {
            "easy": MediumAIStrategy,
            "medium": HardAIStrategy,
            "hard": HardAIStrategy
        }
        strategy_class = strategies.get(difficulty.lower(), HardAIStrategy)
        return strategy_class()
    
    def create_chance_events(self) -> List[GameEvent]:
        """创建困难模式幸运事件（奖励较少）"""
        return [
            GameEvent(
                event_type="money",
                title="小额分红",
                description="你的投资获得少量回报。",
                effect={"money": 200}
            ),
            GameEvent(
                event_type="money",
                title="彩票小奖",
                description="你中了彩票小奖。",
                effect={"money": 400}
            ),
            GameEvent(
                event_type="money",
                title="股票微涨",
                description="你持有的股票小幅上涨。",
                effect={"money": 300}
            ),
            GameEvent(
                event_type="roll_again",
                title="再投一次",
                description="幸运女神眷顾，你可以再投一次骰子！",
                effect={"extra_turn": True}
            )
        ]
    
    def create_misfortune_events(self) -> List[GameEvent]:
        """创建困难模式不幸事件（惩罚更重）"""
        return [
            GameEvent(
                event_type="money",
                title="重大医疗费用",
                description="你患了重病，需要支付高额医疗费用。",
                effect={"money": -800}
            ),
            GameEvent(
                event_type="money",
                title="车辆报废",
                description="你的车彻底报废了，需要买新车。",
                effect={"money": -1000}
            ),
            GameEvent(
                event_type="jail",
                title="严重违法",
                description="你严重违法被抓，直接进监狱！",
                effect={"go_to_jail": True}
            ),
            GameEvent(
                event_type="money",
                title="投资血本无归",
                description="你的投资项目彻底失败，血本无归！",
                effect={"money": -1200}
            ),
            GameEvent(
                event_type="money",
                title="房产大修",
                description="你的房产需要大修，每处房产支付200金币。",
                effect={"house_repair": 200}
            ),
            GameEvent(
                event_type="money",
                title="巨额罚款",
                description="你收到了一张巨额罚款单。",
                effect={"money": -600}
            ),
            GameEvent(
                event_type="move_back",
                title="严重迷路",
                description="你严重迷路了，需要后退5步。",
                effect={"move_back": 5}
            ),
            GameEvent(
                event_type="money",
                title="税务稽查",
                description="税务局严格稽查，需要缴纳重税。",
                effect={"tax_extra": 0.1}
            )
        ]

# 具体工厂3：简单模式游戏工厂
class EasyModeGameFactory(AbstractGameFactory):
    """简单模式游戏工厂 - 创建更友好的游戏组件"""
    
    def create_ai_strategy(self, difficulty: str) -> AIStrategy:
        """创建简单模式AI策略（所有AI都较弱）"""
        # 在简单模式下，即使是困难AI也使用简单策略
        strategies = {
            "easy": EasyAIStrategy,
            "medium": EasyAIStrategy,
            "hard": MediumAIStrategy
        }
        strategy_class = strategies.get(difficulty.lower(), EasyAIStrategy)
        return strategy_class()
    
    def create_chance_events(self) -> List[GameEvent]:
        """创建简单模式幸运事件（奖励更多）"""
        return [
            GameEvent(
                event_type="money",
                title="丰厚分红",
                description="你的投资获得丰厚回报！",
                effect={"money": 1000}
            ),
            GameEvent(
                event_type="money",
                title="彩票大奖",
                description="恭喜你中了彩票特等奖！",
                effect={"money": 2000}
            ),
            GameEvent(
                event_type="money",
                title="股票暴涨",
                description="你持有的股票暴涨，获得巨额收益！",
                effect={"money": 1500}
            ),
            GameEvent(
                event_type="move",
                title="免费旅行",
                description="获得免费旅行机会，可以移动到任意位置！",
                effect={"free_move": True}
            ),
            GameEvent(
                event_type="roll_again",
                title="连续好运",
                description="好运连连，你可以再投一次骰子！",
                effect={"extra_turn": True}
            ),
            GameEvent(
                event_type="money",
                title="政府补贴",
                description="政府给予你大额补贴！",
                effect={"money": 800}
            )
        ]
    
    def create_misfortune_events(self) -> List[GameEvent]:
        """创建简单模式不幸事件（惩罚较轻）"""
        return [
            GameEvent(
                event_type="money",
                title="小额医疗费",
                description="你有点小病，需要支付少量医疗费。",
                effect={"money": -100}
            ),
            GameEvent(
                event_type="money",
                title="车辆小修",
                description="你的车有点小问题，需要简单维修。",
                effect={"money": -80}
            ),
            GameEvent(
                event_type="money",
                title="小额投资失败",
                description="你的小额投资失败了。",
                effect={"money": -200}
            ),
            GameEvent(
                event_type="money",
                title="房屋小修",
                description="你的房产需要小修，每处房产支付50金币。",
                effect={"house_repair": 50}
            ),
            GameEvent(
                event_type="money",
                title="小额罚款",
                description="你收到了一张小额罚款单。",
                effect={"money": -50}
            ),
            GameEvent(
                event_type="move_back",
                title="走错路",
                description="你走错了路，需要后退1步。",
                effect={"move_back": 1}
            )
        ]