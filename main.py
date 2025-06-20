#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大富翁游戏主程序
作者: AI Assistant
版本: 1.0.0
描述: 基于三层架构和设计模式的大富翁游戏
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox, ttk
import threading
import time
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入业务逻辑层
from business.game_manager import GameManager
from business.config_manager import ConfigManager
from business.game_statistics import StatisticsManager
from business.game_state_manager import GameStateManager
from business.models import GameConfig

# 导入数据访问层
from data_access.database_manager import DatabaseManager

# 导入表示层
from presentation.main_window import GameGUI

class MonopolyGameApp:
    """大富翁游戏应用程序主类"""
    
    def __init__(self):
        self.root = None
        self.main_window = None
        self.game_manager = None
        self.config_manager = None
        self.statistics_manager = None
        self.state_manager = None
        self.db_manager = None
        self.auto_save_thread = None
        self.running = False
        
    def initialize(self):
        """初始化应用程序"""
        try:
            print("正在初始化大富翁游戏...")
            
            # 初始化数据库
            print("初始化数据库...")
            self.db_manager = DatabaseManager()
            if not self.db_manager.connect():
                raise Exception("数据库连接失败")
            
            # 初始化配置管理器
            print("加载游戏配置...")
            self.config_manager = ConfigManager()
            config = self.config_manager.load_config()
            
            # 初始化游戏管理器
            print("初始化游戏管理器...")
            self.game_manager = GameManager()
            self.game_manager.config = config
            
            # 初始化统计管理器
            print("初始化统计管理器...")
            self.statistics_manager = StatisticsManager()
            
            # 初始化状态管理器
            print("初始化状态管理器...")
            self.state_manager = GameStateManager(self.game_manager)
            
            # 初始化GUI
            print("初始化用户界面...")
            
            # 创建主窗口
            self.main_window = GameGUI()
            self.root = self.main_window.root
            
            # 设置游戏管理器等组件
            self.main_window.game_manager = self.game_manager
            self.main_window.config_manager = self.config_manager
            self.main_window.statistics_manager = self.statistics_manager
            self.main_window.state_manager = self.state_manager
            
            # 设置关闭事件处理
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            
            # 启动自动保存线程
            self.start_auto_save_thread()
            
            self.running = True
            print("游戏初始化完成！")
            
            return True
            
        except Exception as e:
            error_msg = f"初始化失败: {str(e)}"
            print(error_msg)
            if self.root:
                messagebox.showerror("初始化错误", error_msg)
            return False
    
    def run(self):
        """运行应用程序"""
        if not self.initialize():
            return False
        
        try:
            print("启动游戏界面...")
            
            # 显示欢迎信息
            self.show_welcome_message()
            
            # 启动主循环
            self.root.mainloop()
            
        except Exception as e:
            error_msg = f"运行时错误: {str(e)}"
            print(error_msg)
            messagebox.showerror("运行错误", error_msg)
            return False
        
        finally:
            self.cleanup()
        
        return True
    
    def show_welcome_message(self):
        """显示欢迎信息"""
        welcome_text = """
欢迎来到大富翁游戏！

游戏特色：
• 支持2-6名玩家（包括AI玩家）
• 完整的房产买卖和升级系统
• 丰富的随机事件和特殊格子
• 智能AI对手，多种难度选择
• 完善的游戏统计和排行榜
• 自动保存和手动存档功能

开始游戏前，请先添加玩家并配置游戏设置。
祝您游戏愉快！
        """
        
        # 在状态栏显示欢迎信息
        if self.main_window:
            self.main_window.add_log_message("系统", welcome_text.strip())
    
    def start_auto_save_thread(self):
        """启动自动保存线程"""
        if self.state_manager and self.state_manager.auto_save_enabled:
            self.auto_save_thread = threading.Thread(
                target=self._auto_save_worker, 
                daemon=True
            )
            self.auto_save_thread.start()
    
    def _auto_save_worker(self):
        """自动保存工作线程"""
        while self.running:
            try:
                time.sleep(60)  # 每分钟检查一次
                if self.running and self.state_manager:
                    self.state_manager.auto_save_if_needed()
            except Exception as e:
                print(f"自动保存线程错误: {e}")
    
    def on_closing(self):
        """处理窗口关闭事件"""
        try:
            # 检查是否有未保存的游戏
            if (self.game_manager and 
                self.game_manager.game_state.value in ["playing", "paused"]):
                
                result = messagebox.askyesnocancel(
                    "退出游戏",
                    "当前游戏尚未保存，是否保存后退出？\n\n"
                    "是 - 保存并退出\n"
                    "否 - 不保存直接退出\n"
                    "取消 - 返回游戏"
                )
                
                if result is None:  # 取消
                    return
                elif result:  # 是，保存
                    if self.state_manager:
                        save_name = f"exit_save_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        if not self.state_manager.save_game_state(save_name):
                            if not messagebox.askyesno("保存失败", "保存失败，是否仍要退出？"):
                                return
            
            # 保存配置和统计数据
            if self.config_manager:
                self.config_manager.save_config(self.game_manager.config)
            
            if self.statistics_manager:
                self.statistics_manager.save_statistics()
            
            # 关闭应用程序
            self.running = False
            if self.root:
                self.root.quit()
                self.root.destroy()
                
        except Exception as e:
            print(f"关闭应用程序时出错: {e}")
            if self.root:
                self.root.quit()
                self.root.destroy()
    
    def cleanup(self):
        """清理资源"""
        try:
            print("正在清理资源...")
            
            self.running = False
            
            # 等待自动保存线程结束
            if self.auto_save_thread and self.auto_save_thread.is_alive():
                self.auto_save_thread.join(timeout=2)
            
            # 关闭数据库连接
            if self.db_manager:
                self.db_manager.close()
            
            print("资源清理完成")
            
        except Exception as e:
            print(f"清理资源时出错: {e}")
    
    @staticmethod
    def check_dependencies():
        """检查依赖项"""
        try:
            import tkinter
            import sqlite3
            print("依赖项检查通过")
            return True
        except ImportError as e:
            print(f"缺少必要的依赖项: {e}")
            return False
    
    @staticmethod
    def create_directories():
        """创建必要的目录"""
        directories = [
            "saves",
            "logs",
            "exports",
            "assets"
        ]
        
        for directory in directories:
            try:
                os.makedirs(directory, exist_ok=True)
            except Exception as e:
                print(f"创建目录 {directory} 失败: {e}")

def main():
    """主函数"""
    print("="*50)
    print("大富翁游戏 v1.0.0")
    print("基于Python + Tkinter + SQLite")
    print("三层架构 + 设计模式")
    print("="*50)
    
    # 检查Python版本
    if sys.version_info < (3, 7):
        print("错误: 需要Python 3.7或更高版本")
        return False
    
    # 检查依赖项
    if not MonopolyGameApp.check_dependencies():
        print("错误: 依赖项检查失败")
        return False
    
    # 创建必要目录
    MonopolyGameApp.create_directories()
    
    # 创建并运行应用程序
    app = MonopolyGameApp()
    
    try:
        success = app.run()
        if success:
            print("游戏正常退出")
        else:
            print("游戏异常退出")
        return success
    except KeyboardInterrupt:
        print("\n用户中断程序")
        app.cleanup()
        return True
    except Exception as e:
        print(f"程序异常: {e}")
        app.cleanup()
        return False

def debug_mode():
    """调试模式"""
    print("启动调试模式...")
    
    # 可以在这里添加调试代码
    # 例如：测试各个模块的功能
    
    try:
        # 测试数据库连接
        db = DatabaseManager()
        if db.connect():
            print("✓ 数据库连接正常")
            db.close()
        else:
            print("✗ 数据库连接失败")
        
        # 测试配置管理器
        config_mgr = ConfigManager()
        config = config_mgr.load_config()
        print(f"✓ 配置加载正常: 初始金钱={config.initial_money}")
        
        # 测试游戏管理器
        game_mgr = GameManager()
        print("✓ 游戏管理器创建正常")
        
        print("调试检查完成")
        
    except Exception as e:
        print(f"调试模式错误: {e}")
        return False
    
    return True

if __name__ == "__main__":
    # 检查命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == "--debug":
        debug_mode()
    else:
        main()