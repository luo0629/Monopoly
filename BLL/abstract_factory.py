from abc import ABC, abstractmethod
from typing import List, Dict, Any
from Model.models import GameEvent
from .ai_strategy_base import AIStrategy

# 抽象工厂接口
class AbstractGameFactory(ABC):
    """游戏组件抽象工厂"""
    
    @abstractmethod
    def create_ai_strategy(self, difficulty: str) -> AIStrategy:
        """创建AI策略"""
        pass
    
    @abstractmethod
    def create_chance_events(self) -> List[GameEvent]:
        """创建幸运事件"""
        pass
    
    @abstractmethod
    def create_misfortune_events(self) -> List[GameEvent]:
        """创建不幸事件"""
        pass

# 工厂管理器
class GameFactoryManager:
    """游戏工厂管理器 - 根据游戏模式选择合适的工厂"""
    
    _factories = {}
    
    @classmethod
    def get_factory(cls, game_mode: str = "standard") -> AbstractGameFactory:
        """根据游戏模式获取对应的工厂"""
        from .concrete_factories import StandardGameFactory
        
        if not cls._factories:
            cls._initialize_factories()
        
        factory_class = cls._factories.get(game_mode.lower(), StandardGameFactory)
        return factory_class()
    
    @classmethod
    def _initialize_factories(cls):
        """初始化工厂映射"""
        from .concrete_factories import (
            StandardGameFactory,
            HardModeGameFactory,
            EasyModeGameFactory
        )
        
        cls._factories = {
            "standard": StandardGameFactory,
            "easy": EasyModeGameFactory,
            "hard": HardModeGameFactory
        }
    
    @classmethod
    def register_factory(cls, mode: str, factory_class: type):
        """注册新的工厂类型"""
        if not cls._factories:
            cls._initialize_factories()
        cls._factories[mode.lower()] = factory_class
    
    @classmethod
    def get_available_modes(cls) -> List[str]:
        """获取所有可用的游戏模式"""
        if not cls._factories:
            cls._initialize_factories()
        return list(cls._factories.keys())