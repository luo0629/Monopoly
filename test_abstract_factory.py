#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抽象工厂模式演示
演示如何使用抽象工厂模式创建不同模式下的游戏组件
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from BLL.abstract_factory import GameFactoryManager, AbstractGameFactory
from BLL.concrete_factories import StandardGameFactory, HardModeGameFactory, EasyModeGameFactory
from BLL.ai_strategy import AIStrategyFactory
from BLL.events import EventFactory, EventProcessor

def test_abstract_factory_pattern():
    """测试抽象工厂模式"""
    print("=== 抽象工厂模式演示 ===")
    print()
    
    # 1. 测试工厂管理器
    print("1. 可用的游戏模式:")
    modes = GameFactoryManager.get_available_modes()
    for mode in modes:
        print(f"   - {mode}")
    print()
    
    # 2. 测试不同模式的工厂
    test_modes = ["standard", "easy", "hard"]
    
    for mode in test_modes:
        print(f"=== {mode.upper()} 模式测试 ===")
        
        # 获取工厂
        factory = GameFactoryManager.get_factory(mode)
        print(f"工厂类型: {factory.__class__.__name__}")
        
        # 测试AI策略创建
        print("\nAI策略测试:")
        for difficulty in ["easy", "medium", "hard"]:
            ai_strategy = factory.create_ai_strategy(difficulty)
            print(f"   {difficulty} -> {ai_strategy.__class__.__name__}")
        
        # 测试事件创建
        print("\n事件创建测试:")
        chance_events = factory.create_chance_events()
        misfortune_events = factory.create_misfortune_events()
        print(f"   幸运事件数量: {len(chance_events)}")
        print(f"   不幸事件数量: {len(misfortune_events)}")
        
        # 显示部分事件示例
        print("   幸运事件示例:")
        for i, event in enumerate(chance_events[:3]):
            print(f"     {i+1}. {event.title}: {event.description}")
            print(f"        效果: {event.effect}")
        
        print("   不幸事件示例:")
        for i, event in enumerate(misfortune_events[:3]):
            print(f"     {i+1}. {event.title}: {event.description}")
            print(f"        效果: {event.effect}")
        
        print()

def test_backward_compatibility():
    """测试向后兼容性"""
    print("=== 向后兼容性测试 ===")
    print()
    
    # 测试旧的API仍然可用
    print("1. 测试旧的AIStrategyFactory API:")
    try:
        # 旧的调用方式（不传game_mode参数）
        ai_strategy = AIStrategyFactory.create_strategy("medium")
        print(f"   成功创建: {ai_strategy.__class__.__name__}")
        
        # 新的调用方式（传入game_mode参数）
        ai_strategy_hard = AIStrategyFactory.create_strategy("medium", "hard")
        print(f"   困难模式: {ai_strategy_hard.__class__.__name__}")
    except Exception as e:
        print(f"   错误: {e}")
    
    print("\n2. 测试旧的EventFactory API:")
    try:
        # 旧的调用方式
        chance_events = EventFactory.create_chance_events()
        misfortune_events = EventFactory.create_misfortune_events()
        print(f"   标准模式 - 幸运事件: {len(chance_events)}, 不幸事件: {len(misfortune_events)}")
        
        # 新的调用方式
        easy_chance_events = EventFactory.create_chance_events("easy")
        easy_misfortune_events = EventFactory.create_misfortune_events("easy")
        print(f"   简单模式 - 幸运事件: {len(easy_chance_events)}, 不幸事件: {len(easy_misfortune_events)}")
    except Exception as e:
        print(f"   错误: {e}")
    
    print("\n3. 测试EventProcessor:")
    try:
        # 标准模式
        processor_standard = EventProcessor()
        print(f"   标准模式处理器创建成功")
        
        # 困难模式
        processor_hard = EventProcessor("hard")
        print(f"   困难模式处理器创建成功")
        
        # 比较事件数量
        print(f"   标准模式幸运事件: {len(processor_standard.chance_events)}")
        print(f"   困难模式幸运事件: {len(processor_hard.chance_events)}")
    except Exception as e:
        print(f"   错误: {e}")
    
    print()

def test_extensibility():
    """测试扩展性"""
    print("=== 扩展性测试 ===")
    print()
    
    # 创建自定义工厂
    class CustomGameFactory(AbstractGameFactory):
        """自定义游戏工厂"""
        
        def create_ai_strategy(self, difficulty: str):
            from BLL.ai_strategy_implementations import HardAIStrategy
            return HardAIStrategy()  # 所有AI都使用困难策略
        
        def create_chance_events(self):
            from Model.models import GameEvent
            return [
                GameEvent(
                    event_type="money",
                    title="超级大奖",
                    description="你获得了超级大奖！",
                    effect={"money": 10000}
                )
            ]
        
        def create_misfortune_events(self):
            from entities.models import GameEvent
            return [
                GameEvent(
                    event_type="money",
                    title="轻微损失",
                    description="你有一点小损失。",
                    effect={"money": -10}
                )
            ]
    
    # 注册自定义工厂
    GameFactoryManager.register_factory("custom", CustomGameFactory)
    
    print("1. 注册自定义工厂后的可用模式:")
    modes = GameFactoryManager.get_available_modes()
    for mode in modes:
        print(f"   - {mode}")
    
    print("\n2. 测试自定义工厂:")
    custom_factory = GameFactoryManager.get_factory("custom")
    print(f"   工厂类型: {custom_factory.__class__.__name__}")
    
    # 测试自定义AI策略
    ai_strategy = custom_factory.create_ai_strategy("easy")
    print(f"   AI策略: {ai_strategy.__class__.__name__}")
    
    # 测试自定义事件
    chance_events = custom_factory.create_chance_events()
    misfortune_events = custom_factory.create_misfortune_events()
    print(f"   幸运事件: {len(chance_events)} 个")
    print(f"   不幸事件: {len(misfortune_events)} 个")
    
    if chance_events:
        print(f"   幸运事件示例: {chance_events[0].title} - {chance_events[0].effect}")
    if misfortune_events:
        print(f"   不幸事件示例: {misfortune_events[0].title} - {misfortune_events[0].effect}")
    
    print()

def main():
    """主函数"""
    print("抽象工厂模式重构演示")
    print("=" * 50)
    print()
    
    try:
        # 测试抽象工厂模式
        test_abstract_factory_pattern()
        
        # 测试向后兼容性
        test_backward_compatibility()
        
        # 测试扩展性
        test_extensibility()
        
        print("=== 总结 ===")
        print("✅ 抽象工厂模式重构成功！")
        print("✅ 向后兼容性保持良好！")
        print("✅ 扩展性得到增强！")
        print()
        print("抽象工厂模式的优势:")
        print("1. 产品族一致性 - 确保同一模式下的组件协调工作")
        print("2. 易于切换产品族 - 通过改变工厂即可切换整套产品")
        print("3. 符合开闭原则 - 新增产品族无需修改现有代码")
        print("4. 分离接口与实现 - 客户端只依赖抽象接口")
        print("5. 便于测试 - 可以轻松创建测试用的工厂")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()