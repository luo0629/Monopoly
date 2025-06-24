from abc import ABC, abstractmethod
from typing import Dict, Any


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