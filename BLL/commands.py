from typing import List, Dict, Any
from .command_base import Command


class CommandInvoker:
    """命令调用者 - 命令模式"""
    
    def __init__(self, max_history: int = 10):
        self.command_history: List[Command] = []
        self.current_index = -1
        self.max_history = max_history
    
    def execute_command(self, command: Command) -> Dict[str, Any]:
        """执行命令并记录到历史"""
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
            return {"success": False, "message": "没有可撤销的命令"}
        
        command = self.command_history[self.current_index]
        result = command.undo()
        
        if result.get("success", False):
            self.current_index -= 1
        
        return result
    
    def redo(self) -> Dict[str, Any]:
        """重做下一个命令"""
        if self.current_index >= len(self.command_history) - 1:
            return {"success": False, "message": "没有可重做的命令"}
        
        self.current_index += 1
        command = self.command_history[self.current_index]
        result = command.execute()
        
        if not result.get("success", False):
            self.current_index -= 1
        
        return result
    
    def get_history(self) -> List[str]:
        """获取命令历史描述"""
        return [cmd.get_description() for cmd in self.command_history[:self.current_index + 1]]
    
    def clear_history(self):
        """清空命令历史"""
        self.command_history.clear()
        self.current_index = -1
    
    def can_undo(self) -> bool:
        """检查是否可以撤销"""
        return self.current_index >= 0
    
    def can_redo(self) -> bool:
        """检查是否可以重做"""
        return self.current_index < len(self.command_history) - 1