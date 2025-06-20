from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
import pickle
import base64
from dataclasses import asdict
from .models import Player, MapCell, GameState, GameConfig
from .game_manager import GameManager
from data_access.database_manager import DatabaseManager

class GameStateManager:
    """游戏状态管理器 - 备忘录模式"""
    
    def __init__(self, game_manager: GameManager):
        self.game_manager = game_manager
        self.db_manager = DatabaseManager()
        self.auto_save_enabled = True
        self.auto_save_interval = 300  # 5分钟
        self.last_auto_save = datetime.now()
        self.max_auto_saves = 5
        self.max_manual_saves = 20
    
    def create_game_state(self, save_name: str = None, is_auto_save: bool = False) -> Dict[str, Any]:
        """创建游戏状态快照"""
        if not save_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_name = f"{'auto_' if is_auto_save else 'manual_'}{timestamp}"
        
        # 收集游戏状态数据
        game_state = {
            "save_info": {
                "save_name": save_name,
                "save_time": datetime.now().isoformat(),
                "is_auto_save": is_auto_save,
                "game_version": "1.0.0",
                "save_format_version": "1.0"
            },
            "game_config": asdict(self.game_manager.config),
            "game_state": {
                "current_state": self.game_manager.game_state.value,
                "current_player_index": self.game_manager.current_player_index,
                "turn_number": self.game_manager.turn_number,
                "round_number": getattr(self.game_manager, 'round_number', 1),
                "game_start_time": getattr(self.game_manager, 'game_start_time', datetime.now()).isoformat(),
                "last_dice_roll": getattr(self.game_manager, 'last_dice_roll', []),
                "game_events_log": getattr(self.game_manager, 'game_events', [])
            },
            "players": [self._serialize_player(player) for player in self.game_manager.players],
            "map_data": [self._serialize_map_cell(cell) for cell in self.game_manager.map_data],
            "game_statistics": self._get_current_game_statistics(),
            "special_states": {
                "properties_in_auction": getattr(self.game_manager, 'properties_in_auction', []),
                "pending_trades": getattr(self.game_manager, 'pending_trades', []),
                "active_events": getattr(self.game_manager, 'active_events', []),
                "jail_queue": getattr(self.game_manager, 'jail_queue', []),
                "hospital_queue": getattr(self.game_manager, 'hospital_queue', [])
            }
        }
        
        return game_state
    
    def save_game_state(self, save_name: str = None, is_auto_save: bool = False) -> bool:
        """保存游戏状态"""
        try:
            game_state = self.create_game_state(save_name, is_auto_save)
            
            # 保存到数据库
            success = self.db_manager.save_game(
                save_name=game_state["save_info"]["save_name"],
                game_data=game_state,
                is_auto_save=is_auto_save
            )
            
            if success:
                if is_auto_save:
                    self.last_auto_save = datetime.now()
                    self._cleanup_old_auto_saves()
                else:
                    self._cleanup_old_manual_saves()
                
                self.game_manager.log_event(f"游戏已保存: {game_state['save_info']['save_name']}")
                return True
            
            return False
        except Exception as e:
            print(f"保存游戏状态失败: {e}")
            return False
    
    def load_game_state(self, save_name: str) -> bool:
        """加载游戏状态"""
        try:
            game_data = self.db_manager.load_game(save_name)
            if not game_data:
                print(f"找不到存档: {save_name}")
                return False
            
            # 验证存档格式
            if not self._validate_save_format(game_data):
                print("存档格式不兼容")
                return False
            
            # 恢复游戏配置
            if "game_config" in game_data:
                self.game_manager.config = GameConfig(**game_data["game_config"])
            
            # 恢复游戏状态
            if "game_state" in game_data:
                state_data = game_data["game_state"]
                self.game_manager.game_state = GameState(state_data["current_state"])
                self.game_manager.current_player_index = state_data["current_player_index"]
                self.game_manager.turn_number = state_data["turn_number"]
                
                # 恢复可选字段
                if "round_number" in state_data:
                    self.game_manager.round_number = state_data["round_number"]
                if "game_start_time" in state_data:
                    self.game_manager.game_start_time = datetime.fromisoformat(state_data["game_start_time"])
                if "last_dice_roll" in state_data:
                    self.game_manager.last_dice_roll = state_data["last_dice_roll"]
                if "game_events_log" in state_data:
                    self.game_manager.game_events = state_data["game_events_log"]
            
            # 恢复玩家数据
            if "players" in game_data:
                self.game_manager.players = [self._deserialize_player(player_data) 
                                           for player_data in game_data["players"]]
            
            # 恢复地图数据
            if "map_data" in game_data:
                self.game_manager.map_data = [self._deserialize_map_cell(cell_data) 
                                            for cell_data in game_data["map_data"]]
            
            # 恢复特殊状态
            if "special_states" in game_data:
                special_states = game_data["special_states"]
                for key, value in special_states.items():
                    setattr(self.game_manager, key, value)
            
            self.game_manager.log_event(f"游戏已加载: {save_name}")
            return True
            
        except Exception as e:
            print(f"加载游戏状态失败: {e}")
            return False
    
    def get_save_list(self, include_auto_saves: bool = True) -> List[Dict[str, Any]]:
        """获取存档列表"""
        try:
            saves = self.db_manager.get_save_list()
            
            if not include_auto_saves:
                saves = [save for save in saves if not save.get("is_auto_save", False)]
            
            # 按保存时间排序
            saves.sort(key=lambda x: x.get("save_time", ""), reverse=True)
            
            return saves
        except Exception as e:
            print(f"获取存档列表失败: {e}")
            return []
    
    def delete_save(self, save_name: str) -> bool:
        """删除存档"""
        try:
            return self.db_manager.delete_save(save_name)
        except Exception as e:
            print(f"删除存档失败: {e}")
            return False
    
    def export_save(self, save_name: str, file_path: str) -> bool:
        """导出存档到文件"""
        try:
            game_data = self.db_manager.load_game(save_name)
            if not game_data:
                return False
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(game_data, f, ensure_ascii=False, indent=2, default=str)
            
            return True
        except Exception as e:
            print(f"导出存档失败: {e}")
            return False
    
    def import_save(self, file_path: str, save_name: str = None) -> bool:
        """从文件导入存档"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                game_data = json.load(f)
            
            if not self._validate_save_format(game_data):
                print("存档文件格式不正确")
                return False
            
            if not save_name:
                save_name = game_data.get("save_info", {}).get("save_name", "imported_save")
            
            # 更新保存信息
            game_data["save_info"]["save_name"] = save_name
            game_data["save_info"]["save_time"] = datetime.now().isoformat()
            game_data["save_info"]["is_auto_save"] = False
            
            return self.db_manager.save_game(save_name, game_data, False)
            
        except Exception as e:
            print(f"导入存档失败: {e}")
            return False
    
    def auto_save_if_needed(self) -> bool:
        """如果需要则自动保存"""
        if not self.auto_save_enabled:
            return False
        
        if self.game_manager.game_state not in [GameState.PLAYING, GameState.PAUSED]:
            return False
        
        time_since_last_save = (datetime.now() - self.last_auto_save).total_seconds()
        if time_since_last_save >= self.auto_save_interval:
            return self.save_game_state(is_auto_save=True)
        
        return False
    
    def create_checkpoint(self, checkpoint_name: str = None) -> str:
        """创建检查点"""
        if not checkpoint_name:
            checkpoint_name = f"checkpoint_{datetime.now().strftime('%H%M%S')}"
        
        if self.save_game_state(checkpoint_name, is_auto_save=False):
            return checkpoint_name
        return None
    
    def get_save_info(self, save_name: str) -> Optional[Dict[str, Any]]:
        """获取存档信息"""
        try:
            saves = self.get_save_list()
            for save in saves:
                if save.get("save_name") == save_name:
                    return save
            return None
        except Exception as e:
            print(f"获取存档信息失败: {e}")
            return None
    
    def _serialize_player(self, player: Player) -> Dict[str, Any]:
        """序列化玩家数据"""
        player_data = asdict(player)
        # 处理特殊字段
        if hasattr(player, 'ai_strategy') and player.ai_strategy:
            player_data['ai_strategy_type'] = type(player.ai_strategy).__name__
        return player_data
    
    def _deserialize_player(self, player_data: Dict[str, Any]) -> Player:
        """反序列化玩家数据"""
        # 移除AI策略类型字段，因为Player类不直接包含它
        ai_strategy_type = player_data.pop('ai_strategy_type', None)
        player = Player(**player_data)
        
        # 如果是AI玩家，重新创建AI策略
        if player.is_ai and ai_strategy_type:
            from .ai_strategy import AIStrategyFactory
            difficulty = getattr(self.game_manager.config, 'difficulty_level', 'medium')
            player.ai_strategy = AIStrategyFactory.create_strategy(difficulty)
        
        return player
    
    def _serialize_map_cell(self, cell: MapCell) -> Dict[str, Any]:
        """序列化地图单元格数据"""
        return asdict(cell)
    
    def _deserialize_map_cell(self, cell_data: Dict[str, Any]) -> MapCell:
        """反序列化地图单元格数据"""
        return MapCell(**cell_data)
    
    def _get_current_game_statistics(self) -> Dict[str, Any]:
        """获取当前游戏统计"""
        # 这里可以集成统计管理器的数据
        return {
            "turns_played": self.game_manager.turn_number,
            "players_count": len(self.game_manager.players),
            "active_players": len([p for p in self.game_manager.players if not p.is_bankrupt]),
            "total_properties_owned": sum(len(p.properties) for p in self.game_manager.players),
            "total_money_in_game": sum(p.money for p in self.game_manager.players)
        }
    
    def _validate_save_format(self, game_data: Dict[str, Any]) -> bool:
        """验证存档格式"""
        required_fields = ["save_info", "game_state", "players", "map_data"]
        
        for field in required_fields:
            if field not in game_data:
                print(f"存档缺少必要字段: {field}")
                return False
        
        # 检查版本兼容性
        save_info = game_data.get("save_info", {})
        save_format_version = save_info.get("save_format_version", "1.0")
        
        # 这里可以添加版本兼容性检查逻辑
        supported_versions = ["1.0"]
        if save_format_version not in supported_versions:
            print(f"不支持的存档格式版本: {save_format_version}")
            return False
        
        return True
    
    def _cleanup_old_auto_saves(self):
        """清理旧的自动存档"""
        try:
            saves = self.get_save_list(include_auto_saves=True)
            auto_saves = [save for save in saves if save.get("is_auto_save", False)]
            
            if len(auto_saves) > self.max_auto_saves:
                # 按时间排序，删除最旧的
                auto_saves.sort(key=lambda x: x.get("save_time", ""))
                saves_to_delete = auto_saves[:-self.max_auto_saves]
                
                for save in saves_to_delete:
                    self.delete_save(save["save_name"])
        except Exception as e:
            print(f"清理自动存档失败: {e}")
    
    def _cleanup_old_manual_saves(self):
        """清理旧的手动存档"""
        try:
            saves = self.get_save_list(include_auto_saves=False)
            
            if len(saves) > self.max_manual_saves:
                # 按时间排序，删除最旧的
                saves.sort(key=lambda x: x.get("save_time", ""))
                saves_to_delete = saves[:-self.max_manual_saves]
                
                for save in saves_to_delete:
                    self.delete_save(save["save_name"])
        except Exception as e:
            print(f"清理手动存档失败: {e}")
    
    def get_quick_save_name(self) -> str:
        """获取快速保存名称"""
        return f"quicksave_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def quick_save(self) -> bool:
        """快速保存"""
        return self.save_game_state(self.get_quick_save_name(), is_auto_save=False)
    
    def get_latest_save(self, include_auto_saves: bool = True) -> Optional[str]:
        """获取最新的存档名称"""
        saves = self.get_save_list(include_auto_saves)
        if saves:
            return saves[0]["save_name"]
        return None
    
    def set_auto_save_settings(self, enabled: bool, interval: int = 300):
        """设置自动保存设置"""
        self.auto_save_enabled = enabled
        self.auto_save_interval = max(60, interval)  # 最少1分钟
    
    def get_save_statistics(self) -> Dict[str, Any]:
        """获取存档统计信息"""
        saves = self.get_save_list()
        auto_saves = [s for s in saves if s.get("is_auto_save", False)]
        manual_saves = [s for s in saves if not s.get("is_auto_save", False)]
        
        return {
            "总存档数": len(saves),
            "自动存档数": len(auto_saves),
            "手动存档数": len(manual_saves),
            "最新存档时间": saves[0].get("save_time") if saves else None,
            "自动保存状态": "启用" if self.auto_save_enabled else "禁用",
            "自动保存间隔": f"{self.auto_save_interval}秒"
        }