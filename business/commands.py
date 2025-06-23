from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import random
from .models import Player, MapCell, PropertyLevel


class Command(ABC):
    """命令接口 - 命令模式"""
    
    @abstractmethod
    def execute(self) -> Dict[str, Any]:
        """执行命令"""
        pass
    
    @abstractmethod
    def undo(self) -> Dict[str, Any]:
        """撤销命令"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """获取命令描述"""
        pass


class PurchasePropertyCommand(Command):
    """购买房产命令"""
    
    def __init__(self, game_manager, player: Player, cell: MapCell):
        self.game_manager = game_manager
        self.player = player
        self.cell = cell
        self.original_owner = cell.owner_id
        self.purchase_price = 0
        self.executed = False
    
    def execute(self) -> Dict[str, Any]:
        """执行购买房产"""
        if self.executed:
            return {"success": False, "message": "命令已执行"}
        
        if self.cell.owner_id is not None:
            return {"success": False, "message": "房产已有主人"}
        
        # 检查折扣效果
        discount = 1.0
        if self.player.id in self.game_manager.special_effects:
            effects = self.game_manager.special_effects[self.player.id]
            if "property_discount" in effects:
                discount = effects["property_discount"]
        
        self.purchase_price = int(self.cell.price * discount)
        
        if self.player.money < self.purchase_price:
            return {"success": False, "message": "金钱不足"}
        
        # 执行购买
        self.player.spend_money(self.purchase_price)
        self.cell.owner_id = self.player.id
        self.player.properties.append(self.cell.position)
        
        # 移除折扣效果
        if self.player.id in self.game_manager.special_effects:
            effects = self.game_manager.special_effects[self.player.id]
            if "property_discount" in effects:
                del effects["property_discount"]
        
        self.executed = True
        
        message = f"{self.player.name} 购买了 {self.cell.name}，花费 {self.purchase_price} 金币"
        self.game_manager._log(message)
        self.game_manager.notify({"message": message, "type": "purchase"})
        
        return {
            "success": True,
            "message": message,
            "player": self.player,
            "cell": self.cell,
            "price": self.purchase_price
        }
    
    def undo(self) -> Dict[str, Any]:
        """撤销购买房产"""
        if not self.executed:
            return {"success": False, "message": "命令未执行"}
        
        # 撤销购买
        self.player.add_money(self.purchase_price)
        self.cell.owner_id = self.original_owner
        if self.cell.position in self.player.properties:
            self.player.properties.remove(self.cell.position)
        
        self.executed = False
        
        message = f"撤销 {self.player.name} 购买 {self.cell.name} 的操作"
        self.game_manager._log(message)
        self.game_manager.notify({"message": message, "type": "undo"})
        
        return {
            "success": True,
            "message": message,
            "player": self.player,
            "cell": self.cell
        }
    
    def get_description(self) -> str:
        return f"购买房产: {self.cell.name} (价格: {self.purchase_price})"


class UpgradePropertyCommand(Command):
    """升级房产命令"""
    
    def __init__(self, game_manager, player: Player, cell: MapCell):
        self.game_manager = game_manager
        self.player = player
        self.cell = cell
        self.original_level = cell.level
        self.upgrade_cost = 0
        self.executed = False
    
    def execute(self) -> Dict[str, Any]:
        """执行升级房产"""
        if self.executed:
            return {"success": False, "message": "命令已执行"}
        
        if self.cell.owner_id != self.player.id:
            return {"success": False, "message": "不是您的房产"}
        
        if not self.cell.can_upgrade():
            return {"success": False, "message": "房产无法升级"}
        
        self.upgrade_cost = self.cell.get_upgrade_cost()
        
        if self.player.money < self.upgrade_cost:
            return {"success": False, "message": "金钱不足"}
        
        # 执行升级
        self.player.spend_money(self.upgrade_cost)
        self.cell.level = PropertyLevel(self.cell.level.value + 1)
        
        self.executed = True
        
        message = f"{self.player.name} 升级了 {self.cell.name}，花费 {self.upgrade_cost} 金币"
        self.game_manager._log(message)
        self.game_manager.notify({"message": message, "type": "upgrade"})
        
        return {
            "success": True,
            "message": message,
            "player": self.player,
            "cell": self.cell,
            "cost": self.upgrade_cost
        }
    
    def undo(self) -> Dict[str, Any]:
        """撤销升级房产"""
        if not self.executed:
            return {"success": False, "message": "命令未执行"}
        
        # 撤销升级
        self.player.add_money(self.upgrade_cost)
        self.cell.level = self.original_level
        
        self.executed = False
        
        message = f"撤销 {self.player.name} 升级 {self.cell.name} 的操作"
        self.game_manager._log(message)
        self.game_manager.notify({"message": message, "type": "undo"})
        
        return {
            "success": True,
            "message": message,
            "player": self.player,
            "cell": self.cell
        }
    
    def get_description(self) -> str:
        return f"升级房产: {self.cell.name} (费用: {self.upgrade_cost})"


class PayTaxCommand(Command):
    """交税命令"""
    
    def __init__(self, game_manager, player: Player, cell: MapCell):
        self.game_manager = game_manager
        self.player = player
        self.cell = cell
        self.tax_amount = 0
        self.executed = False
    
    def execute(self) -> Dict[str, Any]:
        """执行交税"""
        if self.executed:
            return {"success": False, "message": "命令已执行"}
        
        # 计算税额
        if "所得税" in self.cell.name:
            self.tax_amount = 200
        elif "奢侈税" in self.cell.name:
            self.tax_amount = 100
        else:
            self.tax_amount = int(self.player.money * self.game_manager.config.tax_rate)
        
        if self.player.money < self.tax_amount:
            return {"success": False, "message": "金钱不足支付税款"}
        
        # 执行交税
        self.player.spend_money(self.tax_amount)
        
        self.executed = True
        
        message = f"{self.player.name} 支付了 {self.tax_amount} 金币的 {self.cell.name}"
        self.game_manager._log(message)
        self.game_manager.notify({"message": message, "type": "tax"})
        
        return {
            "success": True,
            "message": message,
            "player": self.player,
            "tax_amount": self.tax_amount,
            "tax_type": self.cell.name
        }
    
    def undo(self) -> Dict[str, Any]:
        """撤销交税"""
        if not self.executed:
            return {"success": False, "message": "命令未执行"}
        
        # 撤销交税
        self.player.add_money(self.tax_amount)
        
        self.executed = False
        
        message = f"撤销 {self.player.name} 支付 {self.cell.name} 的操作"
        self.game_manager._log(message)
        self.game_manager.notify({"message": message, "type": "undo"})
        
        return {
            "success": True,
            "message": message,
            "player": self.player,
            "tax_amount": self.tax_amount
        }
    
    def get_description(self) -> str:
        return f"支付税款: {self.cell.name} (金额: {self.tax_amount})"


class MovePlayerCommand(Command):
    """移动玩家命令"""
    
    def __init__(self, game_manager, player: Player, steps: int):
        self.game_manager = game_manager
        self.player = player
        self.steps = steps
        self.original_position = player.position
        self.start_bonus = 0
        self.executed = False
    
    def execute(self) -> Dict[str, Any]:
        """执行移动玩家"""
        if self.executed:
            return {"success": False, "message": "命令已执行"}
        
        old_position = self.player.position
        passed_start = self.player.move(self.steps, len(self.game_manager.map_cells))
        
        # 经过起点获得奖励
        if passed_start:
            self.start_bonus = self.game_manager.config.start_bonus
            self.player.add_money(self.start_bonus)
            self.game_manager._log(f"{self.player.name} 经过起点，获得 {self.start_bonus} 金币")
        
        self.executed = True
        
        message = f"{self.player.name} 从位置 {old_position} 移动到位置 {self.player.position}"
        self.game_manager._log(message)
        self.game_manager.notify({"message": message, "type": "move"})
        
        return {
            "success": True,
            "message": message,
            "player": self.player,
            "old_position": old_position,
            "new_position": self.player.position,
            "passed_start": passed_start,
            "start_bonus": self.start_bonus
        }
    
    def undo(self) -> Dict[str, Any]:
        """撤销移动玩家"""
        if not self.executed:
            return {"success": False, "message": "命令未执行"}
        
        # 撤销移动
        self.player.position = self.original_position
        
        # 撤销起点奖励
        if self.start_bonus > 0:
            self.player.spend_money(self.start_bonus)
        
        self.executed = False
        
        message = f"撤销 {self.player.name} 的移动操作"
        self.game_manager._log(message)
        self.game_manager.notify({"message": message, "type": "undo"})
        
        return {
            "success": True,
            "message": message,
            "player": self.player
        }
    
    def get_description(self) -> str:
        return f"移动玩家: {self.player.name} 移动 {self.steps} 步"


class CommandInvoker:
    """命令调用器 - 管理命令的执行和撤销"""
    
    def __init__(self, max_history: int = 10):
        self.command_history: List[Command] = []
        self.current_index = -1
        self.max_history = max_history
    
    def execute_command(self, command: Command) -> Dict[str, Any]:
        """执行命令"""
        result = command.execute()
        
        if result.get("success", False):
            # 清除当前位置之后的历史记录
            self.command_history = self.command_history[:self.current_index + 1]
            
            # 添加新命令到历史记录
            self.command_history.append(command)
            self.current_index += 1
            
            # 限制历史记录长度
            if len(self.command_history) > self.max_history:
                self.command_history.pop(0)
                self.current_index -= 1
        
        return result
    
    def undo(self) -> Dict[str, Any]:
        """撤销上一个命令"""
        if self.current_index < 0:
            return {"success": False, "message": "没有可撤销的操作"}
        
        command = self.command_history[self.current_index]
        result = command.undo()
        
        if result.get("success", False):
            self.current_index -= 1
        
        return result
    
    def redo(self) -> Dict[str, Any]:
        """重做下一个命令"""
        if self.current_index >= len(self.command_history) - 1:
            return {"success": False, "message": "没有可重做的操作"}
        
        self.current_index += 1
        command = self.command_history[self.current_index]
        result = command.execute()
        
        if not result.get("success", False):
            self.current_index -= 1
        
        return result
    
    def get_command_history(self) -> List[str]:
        """获取命令历史描述"""
        return [cmd.get_description() for cmd in self.command_history]
    
    def can_undo(self) -> bool:
        """是否可以撤销"""
        return self.current_index >= 0
    
    def can_redo(self) -> bool:
        """是否可以重做"""
        return self.current_index < len(self.command_history) - 1
    
    def clear_history(self):
        """清空命令历史"""
        self.command_history.clear()
        self.current_index = -1