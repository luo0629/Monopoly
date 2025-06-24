from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict
import json
import os
from Model.models import Player, GameState
from DAL.database_manager import DatabaseManager

@dataclass
class PlayerStatistics:
    """玩家统计数据"""
    player_name: str
    games_played: int = 0
    games_won: int = 0
    games_lost: int = 0
    total_money_earned: int = 0
    total_money_spent: int = 0
    properties_bought: int = 0
    properties_sold: int = 0
    rent_collected: int = 0
    rent_paid: int = 0
    jail_visits: int = 0
    hospital_visits: int = 0
    tax_paid: int = 0
    lucky_events: int = 0
    unlucky_events: int = 0
    bankruptcies: int = 0
    average_game_duration: float = 0.0
    longest_game: float = 0.0
    shortest_game: float = 0.0
    favorite_properties: List[str] = None
    win_rate: float = 0.0
    average_money_per_game: float = 0.0
    
    def __post_init__(self):
        if self.favorite_properties is None:
            self.favorite_properties = []
    
    def calculate_derived_stats(self):
        """计算派生统计数据"""
        if self.games_played > 0:
            self.win_rate = self.games_won / self.games_played
            self.average_money_per_game = self.total_money_earned / self.games_played

@dataclass
class GameStatistics:
    """游戏统计数据"""
    game_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: float = 0.0
    players: List[str] = None
    winner: Optional[str] = None
    total_turns: int = 0
    total_transactions: int = 0
    total_money_circulated: int = 0
    properties_traded: int = 0
    bankruptcies: int = 0
    jail_visits: int = 0
    hospital_visits: int = 0
    lucky_events_triggered: int = 0
    unlucky_events_triggered: int = 0
    ai_players: int = 0
    human_players: int = 0
    game_mode: str = "standard"
    difficulty: str = "medium"
    
    def __post_init__(self):
        if self.players is None:
            self.players = []
    
    def calculate_duration(self):
        """计算游戏时长"""
        if self.end_time and self.start_time:
            self.duration = (self.end_time - self.start_time).total_seconds() / 60  # 分钟

class StatisticsManager:
    """统计管理器"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.stats_file = "game_statistics.json"
        self.current_game_stats: Optional[GameStatistics] = None
        self.player_stats: Dict[str, PlayerStatistics] = {}
        self.session_stats = defaultdict(int)
        self.load_statistics()
    
    def load_statistics(self):
        """加载统计数据"""
        try:
            # 从数据库加载
            stats_data = self.db_manager.get_statistics()
            if stats_data:
                self._parse_statistics_data(stats_data)
            
            # 从文件加载作为备份
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    file_data = json.load(f)
                    self._merge_statistics_data(file_data)
        except Exception as e:
            print(f"加载统计数据失败: {e}")
    
    def save_statistics(self):
        """保存统计数据"""
        try:
            stats_data = self._serialize_statistics()
            
            # 保存到数据库
            self.db_manager.save_statistics(stats_data)
            
            # 保存到文件作为备份
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats_data, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            print(f"保存统计数据失败: {e}")
    
    def start_game_tracking(self, game_id: str, players: List[Player], 
                          game_mode: str = "standard", difficulty: str = "medium"):
        """开始游戏跟踪"""
        player_names = [player.name for player in players]
        ai_count = sum(1 for player in players if player.is_ai)
        human_count = len(players) - ai_count
        
        self.current_game_stats = GameStatistics(
            game_id=game_id,
            start_time=datetime.now(),
            players=player_names,
            ai_players=ai_count,
            human_players=human_count,
            game_mode=game_mode,
            difficulty=difficulty
        )
        
        # 初始化玩家统计
        for player_name in player_names:
            if player_name not in self.player_stats:
                self.player_stats[player_name] = PlayerStatistics(player_name=player_name)
            self.player_stats[player_name].games_played += 1
    
    def end_game_tracking(self, winner: Optional[str], final_players: List[Player]):
        """结束游戏跟踪"""
        if not self.current_game_stats:
            return
        
        self.current_game_stats.end_time = datetime.now()
        self.current_game_stats.calculate_duration()
        self.current_game_stats.winner = winner
        
        # 更新玩家统计
        for player in final_players:
            player_stat = self.player_stats.get(player.name)
            if player_stat:
                if player.name == winner:
                    player_stat.games_won += 1
                else:
                    player_stat.games_lost += 1
                
                if player.is_bankrupt:
                    player_stat.bankruptcies += 1
                
                # 更新游戏时长统计
                duration = self.current_game_stats.duration
                if player_stat.longest_game == 0 or duration > player_stat.longest_game:
                    player_stat.longest_game = duration
                if player_stat.shortest_game == 0 or duration < player_stat.shortest_game:
                    player_stat.shortest_game = duration
                
                # 计算平均游戏时长
                total_duration = player_stat.average_game_duration * (player_stat.games_played - 1) + duration
                player_stat.average_game_duration = total_duration / player_stat.games_played
                
                player_stat.calculate_derived_stats()
        
        self.save_statistics()
        self.current_game_stats = None
    
    def record_transaction(self, transaction_type: str, player_name: str, 
                         amount: int, details: Dict[str, Any] = None):
        """记录交易"""
        if not self.current_game_stats:
            return
        
        self.current_game_stats.total_transactions += 1
        self.current_game_stats.total_money_circulated += abs(amount)
        
        player_stat = self.player_stats.get(player_name)
        if not player_stat:
            return
        
        if transaction_type == "property_purchase":
            player_stat.properties_bought += 1
            player_stat.total_money_spent += amount
        elif transaction_type == "property_sale":
            player_stat.properties_sold += 1
            player_stat.total_money_earned += amount
            self.current_game_stats.properties_traded += 1
        elif transaction_type == "rent_payment":
            player_stat.rent_paid += amount
            player_stat.total_money_spent += amount
        elif transaction_type == "rent_collection":
            player_stat.rent_collected += amount
            player_stat.total_money_earned += amount
        elif transaction_type == "tax_payment":
            player_stat.tax_paid += amount
            player_stat.total_money_spent += amount
        elif transaction_type == "lucky_bonus":
            player_stat.total_money_earned += amount
        elif transaction_type == "unlucky_penalty":
            player_stat.total_money_spent += amount
        
        # 记录最喜欢的房产
        if details and "property_name" in details:
            property_name = details["property_name"]
            if property_name not in player_stat.favorite_properties:
                player_stat.favorite_properties.append(property_name)
    
    def record_event(self, event_type: str, player_name: str, details: Dict[str, Any] = None):
        """记录事件"""
        if not self.current_game_stats:
            return
        
        player_stat = self.player_stats.get(player_name)
        if not player_stat:
            return
        
        if event_type == "jail_visit":
            player_stat.jail_visits += 1
            self.current_game_stats.jail_visits += 1
        elif event_type == "hospital_visit":
            player_stat.hospital_visits += 1
            self.current_game_stats.hospital_visits += 1
        elif event_type == "lucky_event":
            player_stat.lucky_events += 1
            self.current_game_stats.lucky_events_triggered += 1
        elif event_type == "unlucky_event":
            player_stat.unlucky_events += 1
            self.current_game_stats.unlucky_events_triggered += 1
        elif event_type == "turn_completed":
            self.current_game_stats.total_turns += 1
    
    def get_player_statistics(self, player_name: str) -> Optional[PlayerStatistics]:
        """获取玩家统计"""
        return self.player_stats.get(player_name)
    
    def get_all_player_statistics(self) -> Dict[str, PlayerStatistics]:
        """获取所有玩家统计"""
        return self.player_stats.copy()
    
    def get_leaderboard(self, sort_by: str = "win_rate", limit: int = 10) -> List[PlayerStatistics]:
        """获取排行榜"""
        players = list(self.player_stats.values())
        
        # 只包含至少玩过一局的玩家
        players = [p for p in players if p.games_played > 0]
        
        # 计算派生统计
        for player in players:
            player.calculate_derived_stats()
        
        # 排序
        if sort_by == "win_rate":
            players.sort(key=lambda p: p.win_rate, reverse=True)
        elif sort_by == "games_won":
            players.sort(key=lambda p: p.games_won, reverse=True)
        elif sort_by == "games_played":
            players.sort(key=lambda p: p.games_played, reverse=True)
        elif sort_by == "total_money_earned":
            players.sort(key=lambda p: p.total_money_earned, reverse=True)
        elif sort_by == "average_money_per_game":
            players.sort(key=lambda p: p.average_money_per_game, reverse=True)
        
        return players[:limit]
    
    def get_game_summary(self) -> Dict[str, Any]:
        """获取游戏总结"""
        total_games = len([p for p in self.player_stats.values() if p.games_played > 0])
        total_players = len(self.player_stats)
        
        if total_players == 0:
            return {"message": "暂无游戏数据"}
        
        # 计算总体统计
        total_money_circulated = sum(p.total_money_earned + p.total_money_spent 
                                   for p in self.player_stats.values())
        total_properties_traded = sum(p.properties_bought + p.properties_sold 
                                    for p in self.player_stats.values())
        total_jail_visits = sum(p.jail_visits for p in self.player_stats.values())
        total_hospital_visits = sum(p.hospital_visits for p in self.player_stats.values())
        
        # 找出最活跃的玩家
        most_active = max(self.player_stats.values(), key=lambda p: p.games_played)
        
        # 找出胜率最高的玩家（至少玩过3局）
        eligible_players = [p for p in self.player_stats.values() if p.games_played >= 3]
        if eligible_players:
            for p in eligible_players:
                p.calculate_derived_stats()
            highest_win_rate = max(eligible_players, key=lambda p: p.win_rate)
        else:
            highest_win_rate = None
        
        return {
            "总体统计": {
                "总游戏数": total_games,
                "总玩家数": total_players,
                "总金钱流通": total_money_circulated,
                "总房产交易": total_properties_traded,
                "总监狱访问": total_jail_visits,
                "总医院访问": total_hospital_visits
            },
            "最活跃玩家": {
                "姓名": most_active.player_name,
                "游戏数": most_active.games_played,
                "胜率": f"{most_active.win_rate:.2%}"
            } if most_active else None,
            "最高胜率玩家": {
                "姓名": highest_win_rate.player_name,
                "胜率": f"{highest_win_rate.win_rate:.2%}",
                "游戏数": highest_win_rate.games_played
            } if highest_win_rate else None
        }
    
    def get_trends_analysis(self, days: int = 30) -> Dict[str, Any]:
        """获取趋势分析"""
        # 这里可以添加更复杂的趋势分析逻辑
        # 目前返回基本的统计信息
        return {
            "时间范围": f"最近{days}天",
            "分析": "趋势分析功能待完善"
        }
    
    def export_statistics(self, file_path: str, format_type: str = "json") -> bool:
        """导出统计数据"""
        try:
            stats_data = self._serialize_statistics()
            
            if format_type.lower() == "json":
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(stats_data, f, ensure_ascii=False, indent=2, default=str)
            elif format_type.lower() == "csv":
                import csv
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    # 写入玩家统计数据
                    writer.writerow(["玩家名", "游戏数", "胜利数", "胜率", "总收入", "总支出"])
                    for player_stat in self.player_stats.values():
                        player_stat.calculate_derived_stats()
                        writer.writerow([
                            player_stat.player_name,
                            player_stat.games_played,
                            player_stat.games_won,
                            f"{player_stat.win_rate:.2%}",
                            player_stat.total_money_earned,
                            player_stat.total_money_spent
                        ])
            
            return True
        except Exception as e:
            print(f"导出统计数据失败: {e}")
            return False
    
    def reset_statistics(self, player_name: Optional[str] = None) -> bool:
        """重置统计数据"""
        try:
            if player_name:
                # 重置特定玩家的统计
                if player_name in self.player_stats:
                    self.player_stats[player_name] = PlayerStatistics(player_name=player_name)
            else:
                # 重置所有统计
                self.player_stats.clear()
                self.current_game_stats = None
            
            self.save_statistics()
            return True
        except Exception as e:
            print(f"重置统计数据失败: {e}")
            return False
    
    def _serialize_statistics(self) -> Dict[str, Any]:
        """序列化统计数据"""
        return {
            "player_statistics": {name: asdict(stats) for name, stats in self.player_stats.items()},
            "current_game": asdict(self.current_game_stats) if self.current_game_stats else None,
            "last_updated": datetime.now().isoformat()
        }
    
    def _parse_statistics_data(self, data: Dict[str, Any]):
        """解析统计数据"""
        if "player_statistics" in data:
            for name, stats_dict in data["player_statistics"].items():
                self.player_stats[name] = PlayerStatistics(**stats_dict)
    
    def _merge_statistics_data(self, data: Dict[str, Any]):
        """合并统计数据"""
        # 这里可以实现更复杂的合并逻辑
        # 目前简单地更新不存在的数据
        if "player_statistics" in data:
            for name, stats_dict in data["player_statistics"].items():
                if name not in self.player_stats:
                    self.player_stats[name] = PlayerStatistics(**stats_dict)