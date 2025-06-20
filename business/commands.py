from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from .models import Player, MapCell
from .game_manager import GameManager

class Command(ABC):
    """命令接口 - 命令模式"""
    
    @abstractmethod
    def execute(self) -> bool:
        """执行命令"""
        pass
    
    @abstractmethod
    def undo(self) -> bool:
        """撤销命令"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """获取命令描述"""
        pass

class PurchasePropertyCommand(Command):
    """购买房产命令"""
    
    def __init__(self, game_manager: GameManager, player_id: int, cell_position: int):
        self.game_manager = game_manager
        self.player_id = player_id
        self.cell_position = cell_position
        self.executed = False
        self.purchase_price = 0
    
    def execute(self) -> bool:
        """执行购买"""
        player = self.game_manager.get_player_by_id(self.player_id)
        cell = self.game_manager.get_cell_at_position(self.cell_position)
        
        if not player or not cell or cell.owner_id is not None:
            return False
        
        if player.money >= cell.price:
            self.purchase_price = cell.price
            if self.game_manager.purchase_property(player, cell):
                self.executed = True
                return True
        
        return False
    
    def undo(self) -> bool:
        """撤销购买"""
        if not self.executed:
            return False
        
        player = self.game_manager.get_player_by_id(self.player_id)
        cell = self.game_manager.get_cell_at_position(self.cell_position)
        
        if player and cell and cell.owner_id == self.player_id:
            # 退还金钱
            player.add_money(self.purchase_price)
            # 移除房产所有权
            cell.reset_ownership()
            # 从玩家房产列表中移除
            if self.cell_position in player.properties:
                player.properties.remove(self.cell_position)
            
            self.executed = False
            return True
        
        return False
    
    def get_description(self) -> str:
        cell = self.game_manager.get_cell_at_position(self.cell_position)
        player = self.game_manager.get_player_by_id(self.player_id)
        return f"{player.name if player else '未知'} 购买 {cell.name if cell else '未知'}"

class UpgradePropertyCommand(Command):
    """升级房产命令"""
    
    def __init__(self, game_manager: GameManager, player_id: int, cell_position: int):
        self.game_manager = game_manager
        self.player_id = player_id
        self.cell_position = cell_position
        self.executed = False
        self.upgrade_cost = 0
        self.previous_level = None
    
    def execute(self) -> bool:
        """执行升级"""
        player = self.game_manager.get_player_by_id(self.player_id)
        cell = self.game_manager.get_cell_at_position(self.cell_position)
        
        if not player or not cell or cell.owner_id != self.player_id:
            return False
        
        if cell.can_upgrade() and player.money >= cell.upgrade_cost:
            self.previous_level = cell.level
            self.upgrade_cost = cell.upgrade_cost
            
            if self.game_manager.upgrade_property(player, cell):
                self.executed = True
                return True
        
        return False
    
    def undo(self) -> bool:
        """撤销升级"""
        if not self.executed or self.previous_level is None:
            return False
        
        player = self.game_manager.get_player_by_id(self.player_id)
        cell = self.game_manager.get_cell_at_position(self.cell_position)
        
        if player and cell:
            # 退还升级费用
            player.add_money(self.upgrade_cost)
            # 恢复房产等级
            cell.level = self.previous_level
            
            self.executed = False
            return True
        
        return False
    
    def get_description(self) -> str:
        cell = self.game_manager.get_cell_at_position(self.cell_position)
        player = self.game_manager.get_player_by_id(self.player_id)
        return f"{player.name if player else '未知'} 升级 {cell.name if cell else '未知'}"

class PayRentCommand(Command):
    """支付租金命令"""
    
    def __init__(self, game_manager: GameManager, payer_id: int, 
                 receiver_id: int, amount: int, cell_position: int):
        self.game_manager = game_manager
        self.payer_id = payer_id
        self.receiver_id = receiver_id
        self.amount = amount
        self.cell_position = cell_position
        self.executed = False
    
    def execute(self) -> bool:
        """执行支付租金"""
        payer = self.game_manager.get_player_by_id(self.payer_id)
        receiver = self.game_manager.get_player_by_id(self.receiver_id)
        
        if not payer or not receiver:
            return False
        
        if payer.spend_money(self.amount):
            receiver.add_money(self.amount)
            self.executed = True
            return True
        
        return False
    
    def undo(self) -> bool:
        """撤销支付租金"""
        if not self.executed:
            return False
        
        payer = self.game_manager.get_player_by_id(self.payer_id)
        receiver = self.game_manager.get_player_by_id(self.receiver_id)
        
        if payer and receiver:
            # 退还租金
            receiver.spend_money(self.amount)
            payer.add_money(self.amount)
            
            self.executed = False
            return True
        
        return False
    
    def get_description(self) -> str:
        payer = self.game_manager.get_player_by_id(self.payer_id)
        receiver = self.game_manager.get_player_by_id(self.receiver_id)
        cell = self.game_manager.get_cell_at_position(self.cell_position)
        return f"{payer.name if payer else '未知'} 向 {receiver.name if receiver else '未知'} 支付租金 {self.amount} (位置: {cell.name if cell else '未知'})"

class MovePlayerCommand(Command):
    """移动玩家命令"""
    
    def __init__(self, game_manager: GameManager, player_id: int, steps: int):
        self.game_manager = game_manager
        self.player_id = player_id
        self.steps = steps
        self.executed = False
        self.previous_position = None
        self.start_bonus_received = False
    
    def execute(self) -> bool:
        """执行移动"""
        player = self.game_manager.get_player_by_id(self.player_id)
        if not player:
            return False
        
        self.previous_position = player.position
        move_result = self.game_manager.move_player(player, self.steps)
        self.start_bonus_received = move_result.get("passed_start", False)
        
        self.executed = True
        return True
    
    def undo(self) -> bool:
        """撤销移动"""
        if not self.executed or self.previous_position is None:
            return False
        
        player = self.game_manager.get_player_by_id(self.player_id)
        if not player:
            return False
        
        # 恢复位置
        player.position = self.previous_position
        
        # 如果获得了起点奖励，需要扣除
        if self.start_bonus_received:
            player.spend_money(self.game_manager.config.start_bonus)
        
        self.executed = False
        return True
    
    def get_description(self) -> str:
        player = self.game_manager.get_player_by_id(self.player_id)
        return f"{player.name if player else '未知'} 移动 {self.steps} 步"

class PayTaxCommand(Command):
    """缴税命令"""
    
    def __init__(self, game_manager: GameManager, player_id: int, 
                 tax_amount: int, tax_type: str):
        self.game_manager = game_manager
        self.player_id = player_id
        self.tax_amount = tax_amount
        self.tax_type = tax_type
        self.executed = False
    
    def execute(self) -> bool:
        """执行缴税"""
        player = self.game_manager.get_player_by_id(self.player_id)
        if not player:
            return False
        
        if player.spend_money(self.tax_amount):
            self.executed = True
            return True
        
        return False
    
    def undo(self) -> bool:
        """撤销缴税"""
        if not self.executed:
            return False
        
        player = self.game_manager.get_player_by_id(self.player_id)
        if player:
            player.add_money(self.tax_amount)
            self.executed = False
            return True
        
        return False
    
    def get_description(self) -> str:
        player = self.game_manager.get_player_by_id(self.player_id)
        return f"{player.name if player else '未知'} 缴纳 {self.tax_type} {self.tax_amount} 金币"

class GoToJailCommand(Command):
    """进监狱命令"""
    
    def __init__(self, game_manager: GameManager, player_id: int):
        self.game_manager = game_manager
        self.player_id = player_id
        self.executed = False
        self.previous_position = None
        self.was_in_jail = False
        self.previous_jail_turns = 0
    
    def execute(self) -> bool:
        """执行进监狱"""
        player = self.game_manager.get_player_by_id(self.player_id)
        if not player:
            return False
        
        self.previous_position = player.position
        self.was_in_jail = player.is_in_jail
        self.previous_jail_turns = player.jail_turns
        
        player.go_to_jail()
        self.executed = True
        return True
    
    def undo(self) -> bool:
        """撤销进监狱"""
        if not self.executed or self.previous_position is None:
            return False
        
        player = self.game_manager.get_player_by_id(self.player_id)
        if player:
            player.position = self.previous_position
            player.is_in_jail = self.was_in_jail
            player.jail_turns = self.previous_jail_turns
            
            self.executed = False
            return True
        
        return False
    
    def get_description(self) -> str:
        player = self.game_manager.get_player_by_id(self.player_id)
        return f"{player.name if player else '未知'} 进监狱"

class CommandInvoker:
    """命令调用者 - 命令模式"""
    
    def __init__(self):
        self.command_history: List[Command] = []
        self.current_index = -1
        self.max_history = 50  # 最大历史记录数
    
    def execute_command(self, command: Command) -> bool:
        """执行命令"""
        if command.execute():
            # 清除当前位置之后的历史记录
            self.command_history = self.command_history[:self.current_index + 1]
            
            # 添加新命令
            self.command_history.append(command)
            self.current_index += 1
            
            # 限制历史记录数量
            if len(self.command_history) > self.max_history:
                self.command_history.pop(0)
                self.current_index -= 1
            
            return True
        
        return False
    
    def undo(self) -> bool:
        """撤销上一个命令"""
        if self.can_undo():
            command = self.command_history[self.current_index]
            if command.undo():
                self.current_index -= 1
                return True
        
        return False
    
    def redo(self) -> bool:
        """重做下一个命令"""
        if self.can_redo():
            self.current_index += 1
            command = self.command_history[self.current_index]
            if command.execute():
                return True
            else:
                self.current_index -= 1
        
        return False
    
    def can_undo(self) -> bool:
        """是否可以撤销"""
        return self.current_index >= 0
    
    def can_redo(self) -> bool:
        """是否可以重做"""
        return self.current_index < len(self.command_history) - 1
    
    def get_command_history(self) -> List[str]:
        """获取命令历史描述"""
        return [cmd.get_description() for cmd in self.command_history]
    
    def clear_history(self):
        """清空命令历史"""
        self.command_history.clear()
        self.current_index = -1
    
    def get_current_command_description(self) -> Optional[str]:
        """获取当前命令描述"""
        if 0 <= self.current_index < len(self.command_history):
            return self.command_history[self.current_index].get_description()
        return None

class MacroCommand(Command):
    """宏命令 - 组合多个命令"""
    
    def __init__(self, commands: List[Command], description: str):
        self.commands = commands
        self.description = description
        self.executed_commands: List[Command] = []
    
    def execute(self) -> bool:
        """执行所有命令"""
        self.executed_commands.clear()
        
        for command in self.commands:
            if command.execute():
                self.executed_commands.append(command)
            else:
                # 如果某个命令失败，撤销已执行的命令
                self.undo()
                return False
        
        return True
    
    def undo(self) -> bool:
        """撤销所有已执行的命令"""
        success = True
        
        # 逆序撤销
        for command in reversed(self.executed_commands):
            if not command.undo():
                success = False
        
        self.executed_commands.clear()
        return success
    
    def get_description(self) -> str:
        return self.description