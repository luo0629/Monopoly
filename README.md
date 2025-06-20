# 大富翁游戏 (Monopoly Game)

## 项目简介
这是一个基于Python开发的大富翁桌面游戏，采用三层架构设计，支持单机和网络多人游戏。

## 功能特性
- 支持4个以上玩家同时游戏
- 包含AI玩家智能决策
- 游戏地图可通过文件配置
- 完整的房产买卖和升级系统
- 幸运/不幸事件系统
- 游戏进度保存和读取
- SQLite数据库存储

## 技术架构
- **表示层 (Presentation Layer)**: GUI界面和用户交互
- **业务逻辑层 (Business Logic Layer)**: 游戏规则和逻辑处理
- **数据访问层 (Data Access Layer)**: 数据库操作和文件管理

## 设计模式
- 单例模式 (Singleton): 游戏管理器
- 工厂模式 (Factory): 玩家和事件创建
- 观察者模式 (Observer): 游戏状态通知
- 策略模式 (Strategy): AI决策算法
- 命令模式 (Command): 游戏操作封装

## 安装和运行
1. 安装依赖: `pip install -r requirements.txt`
2. 运行游戏: `python main.py`

## 项目结构
```
monopoly_game/
├── main.py                 # 程序入口
├── requirements.txt        # 依赖包
├── README.md              # 项目说明
├── config/                # 配置文件
├── data/                  # 数据文件
├── presentation/          # 表示层
├── business/              # 业务逻辑层
├── data_access/           # 数据访问层
└── assets/                # 游戏资源
```