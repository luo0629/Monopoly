from typing import Dict, Any, Optional
import json
import os
from dataclasses import asdict
from .models import GameConfig
from data_access.database_manager import DatabaseManager

class ConfigManager:
    """配置管理器 - 单例模式"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.db_manager = DatabaseManager()
            self.config_file = "game_config.json"
            self.default_config = self._create_default_config()
            self._initialized = True
    
    def _create_default_config(self) -> GameConfig:
        """创建默认配置"""
        return GameConfig(
            initial_money=15000,
            start_bonus=2000,
            jail_position=10,
            hospital_position=20,
            tax_office_position=30,
            jail_turns=3,
            hospital_fee=1000,
            tax_rate=0.1,
            max_players=6,
            min_players=2,
            dice_count=2,
            dice_sides=6,
            board_size=40,
            bankruptcy_threshold=0,
            property_mortgage_rate=0.5,
            hotel_limit=4,
            house_limit=32,
            auction_enabled=True,
            trading_enabled=True,
            time_limit_per_turn=300,  # 5分钟
            auto_save_interval=600,   # 10分钟
            sound_enabled=True,
            animation_enabled=True,
            difficulty_level="medium",
            language="zh_CN"
        )
    
    def load_config(self) -> GameConfig:
        """加载配置"""
        # 首先尝试从数据库加载
        try:
            # 从数据库加载所有配置项
            config_data = {}
            for key in self.default_config.__dict__.keys():
                value = self.db_manager.get_config(key)
                if value is not None:
                    config_data[key] = value
            
            if config_data:
                return GameConfig(**config_data)
        except Exception as e:
            print(f"从数据库加载配置失败: {e}")
        
        # 然后尝试从文件加载
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    return GameConfig(**config_data)
        except Exception as e:
            print(f"从文件加载配置失败: {e}")
        
        # 返回默认配置
        return self.default_config
    
    def save_config(self, config: GameConfig) -> bool:
        """保存配置"""
        try:
            # 保存到数据库
            config_dict = asdict(config)
            self.db_manager.save_config(config_dict)
            
            # 保存到文件作为备份
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        config = self.load_config()
        return getattr(config, key, default)
    
    def set_config_value(self, key: str, value: Any) -> bool:
        """设置配置值"""
        try:
            config = self.load_config()
            if hasattr(config, key):
                setattr(config, key, value)
                return self.save_config(config)
            else:
                print(f"配置项 {key} 不存在")
                return False
        except Exception as e:
            print(f"设置配置值失败: {e}")
            return False
    
    def reset_to_default(self) -> bool:
        """重置为默认配置"""
        return self.save_config(self.default_config)
    
    def validate_config(self, config: GameConfig) -> tuple[bool, list[str]]:
        """验证配置"""
        errors = []
        
        # 验证基本数值
        if config.initial_money <= 0:
            errors.append("初始金钱必须大于0")
        
        if config.start_bonus < 0:
            errors.append("起点奖励不能为负数")
        
        if config.max_players < config.min_players:
            errors.append("最大玩家数不能小于最小玩家数")
        
        if config.min_players < 2:
            errors.append("最小玩家数不能少于2")
        
        if config.max_players > 8:
            errors.append("最大玩家数不能超过8")
        
        if config.dice_count <= 0 or config.dice_count > 3:
            errors.append("骰子数量必须在1-3之间")
        
        if config.dice_sides < 4 or config.dice_sides > 20:
            errors.append("骰子面数必须在4-20之间")
        
        if config.board_size < 20 or config.board_size > 60:
            errors.append("棋盘大小必须在20-60之间")
        
        if config.jail_turns < 1 or config.jail_turns > 10:
            errors.append("监狱轮数必须在1-10之间")
        
        if config.hospital_fee < 0:
            errors.append("医院费用不能为负数")
        
        if config.tax_rate < 0 or config.tax_rate > 1:
            errors.append("税率必须在0-1之间")
        
        if config.property_mortgage_rate < 0 or config.property_mortgage_rate > 1:
            errors.append("房产抵押率必须在0-1之间")
        
        if config.time_limit_per_turn < 30 or config.time_limit_per_turn > 1800:
            errors.append("每回合时间限制必须在30秒-30分钟之间")
        
        if config.auto_save_interval < 60 or config.auto_save_interval > 3600:
            errors.append("自动保存间隔必须在1分钟-1小时之间")
        
        # 验证位置
        positions = [config.jail_position, config.hospital_position, config.tax_office_position]
        for pos in positions:
            if pos < 0 or pos >= config.board_size:
                errors.append(f"位置 {pos} 超出棋盘范围")
        
        if len(set(positions)) != len(positions):
            errors.append("特殊位置不能重复")
        
        # 验证难度等级
        valid_difficulties = ["easy", "medium", "hard"]
        if config.difficulty_level not in valid_difficulties:
            errors.append(f"难度等级必须是: {', '.join(valid_difficulties)}")
        
        # 验证语言
        valid_languages = ["zh_CN", "en_US"]
        if config.language not in valid_languages:
            errors.append(f"语言必须是: {', '.join(valid_languages)}")
        
        return len(errors) == 0, errors
    
    def get_display_config(self) -> Dict[str, Any]:
        """获取用于显示的配置信息"""
        config = self.load_config()
        return {
            "游戏设置": {
                "初始金钱": config.initial_money,
                "起点奖励": config.start_bonus,
                "最小玩家数": config.min_players,
                "最大玩家数": config.max_players,
                "棋盘大小": config.board_size,
                "破产阈值": config.bankruptcy_threshold
            },
            "特殊位置": {
                "监狱位置": config.jail_position,
                "医院位置": config.hospital_position,
                "税务局位置": config.tax_office_position
            },
            "游戏规则": {
                "监狱轮数": config.jail_turns,
                "医院费用": config.hospital_fee,
                "税率": f"{config.tax_rate * 100}%",
                "房产抵押率": f"{config.property_mortgage_rate * 100}%",
                "启用拍卖": "是" if config.auction_enabled else "否",
                "启用交易": "是" if config.trading_enabled else "否"
            },
            "骰子设置": {
                "骰子数量": config.dice_count,
                "骰子面数": config.dice_sides
            },
            "时间设置": {
                "每回合时间限制": f"{config.time_limit_per_turn}秒",
                "自动保存间隔": f"{config.auto_save_interval}秒"
            },
            "界面设置": {
                "启用声音": "是" if config.sound_enabled else "否",
                "启用动画": "是" if config.animation_enabled else "否",
                "难度等级": config.difficulty_level,
                "语言": config.language
            },
            "建筑限制": {
                "酒店限制": config.hotel_limit,
                "房屋限制": config.house_limit
            }
        }
    
    def export_config(self, file_path: str) -> bool:
        """导出配置到文件"""
        try:
            config = self.load_config()
            config_dict = asdict(config)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"导出配置失败: {e}")
            return False
    
    def import_config(self, file_path: str) -> bool:
        """从文件导入配置"""
        try:
            if not os.path.exists(file_path):
                print(f"配置文件不存在: {file_path}")
                return False
            
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            config = GameConfig(**config_data)
            
            # 验证配置
            is_valid, errors = self.validate_config(config)
            if not is_valid:
                print(f"配置验证失败: {', '.join(errors)}")
                return False
            
            return self.save_config(config)
        except Exception as e:
            print(f"导入配置失败: {e}")
            return False
    
    def get_config_templates(self) -> Dict[str, GameConfig]:
        """获取配置模板"""
        templates = {
            "简单模式": GameConfig(
                initial_money=20000,
                start_bonus=3000,
                jail_position=10,
                hospital_position=20,
                tax_office_position=30,
                jail_turns=2,
                hospital_fee=500,
                tax_rate=0.05,
                max_players=4,
                min_players=2,
                dice_count=2,
                dice_sides=6,
                board_size=32,
                bankruptcy_threshold=0,
                property_mortgage_rate=0.6,
                hotel_limit=4,
                house_limit=32,
                auction_enabled=False,
                trading_enabled=True,
                time_limit_per_turn=600,
                auto_save_interval=300,
                sound_enabled=True,
                animation_enabled=True,
                difficulty_level="easy",
                language="zh_CN"
            ),
            "标准模式": self.default_config,
            "困难模式": GameConfig(
                initial_money=10000,
                start_bonus=1000,
                jail_position=10,
                hospital_position=20,
                tax_office_position=30,
                jail_turns=5,
                hospital_fee=2000,
                tax_rate=0.15,
                max_players=6,
                min_players=3,
                dice_count=2,
                dice_sides=6,
                board_size=48,
                bankruptcy_threshold=0,
                property_mortgage_rate=0.4,
                hotel_limit=3,
                house_limit=24,
                auction_enabled=True,
                trading_enabled=True,
                time_limit_per_turn=180,
                auto_save_interval=900,
                sound_enabled=True,
                animation_enabled=True,
                difficulty_level="hard",
                language="zh_CN"
            ),
            "快速游戏": GameConfig(
                initial_money=8000,
                start_bonus=1500,
                jail_position=8,
                hospital_position=16,
                tax_office_position=24,
                jail_turns=1,
                hospital_fee=800,
                tax_rate=0.08,
                max_players=4,
                min_players=2,
                dice_count=2,
                dice_sides=6,
                board_size=24,
                bankruptcy_threshold=0,
                property_mortgage_rate=0.5,
                hotel_limit=2,
                house_limit=16,
                auction_enabled=True,
                trading_enabled=False,
                time_limit_per_turn=120,
                auto_save_interval=180,
                sound_enabled=True,
                animation_enabled=False,
                difficulty_level="medium",
                language="zh_CN"
            )
        }
        
        return templates
    
    def apply_template(self, template_name: str) -> bool:
        """应用配置模板"""
        templates = self.get_config_templates()
        if template_name in templates:
            return self.save_config(templates[template_name])
        else:
            print(f"配置模板不存在: {template_name}")
            return False