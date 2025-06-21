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

### 环境要求
- Python 3.8+
- tkinter (通常随Python安装)
- SQLite3 (Python内置)

### 安装步骤
1. 克隆项目到本地
2. 创建虚拟环境: `python -m venv .venv`
3. 激活虚拟环境:
   - Windows: `.venv\Scripts\activate`
   - Linux/Mac: `source .venv/bin/activate`
4. 安装依赖: `pip install -r requirements.txt`
5. 运行游戏: `python main.py`

### 游戏操作
1. 启动游戏后，在开始页面配置玩家信息
2. 设置玩家数量（2-6人）和初始金币
3. 选择人类玩家或AI玩家
4. 点击开始游戏进入主界面
5. 使用掷骰子按钮进行游戏

## 项目结构

### 根目录文件
```
monopoly_game/
├── main.py                 # 程序入口，应用程序主类
├── requirements.txt        # Python依赖包列表
├── README.md              # 项目说明文档
├── .gitignore             # Git忽略文件配置
└── .venv/                 # Python虚拟环境目录
```

### 表示层 (presentation/)
负责用户界面和交互逻辑
```
presentation/
├── __init__.py            # 包初始化文件
├── main_window.py         # 游戏主界面，包含游戏板、玩家信息、控制面板
└── start_page.py          # 游戏开始页面，玩家配置和游戏设置
```

### 业务逻辑层 (business/)
包含游戏核心逻辑和规则
```
business/
├── __init__.py            # 包初始化文件
├── game_manager.py        # 游戏管理器（单例模式），核心游戏逻辑控制
├── models.py              # 数据模型定义（玩家、地图格子、游戏状态等）
├── ai_strategy.py         # AI玩家策略算法实现
├── events.py              # 事件系统（观察者模式）
├── commands.py            # 游戏命令封装（命令模式）
├── config_manager.py      # 配置管理器
├── game_state_manager.py  # 游戏状态管理器
└── game_statistics.py     # 游戏统计数据管理
```

### 数据访问层 (data_access/)
负责数据持久化和文件操作
```
data_access/
├── __init__.py            # 包初始化文件
└── database_manager.py    # 数据库管理器（单例模式），SQLite数据库操作
```

### 数据文件 (data/)
存储游戏配置和地图数据
```
data/
└── default_map.json       # 默认游戏地图配置（36格青岛主题地图）
```

### 其他目录
```
assets/                    # 游戏资源文件（图片、音效等）
exports/                   # 游戏数据导出目录
logs/                      # 日志文件目录
saves/                     # 游戏存档目录
```

## 核心文件详细说明

### main.py
- **MonopolyGameApp类**: 应用程序主控制器
- 负责初始化各个管理器和组件
- 处理应用程序生命周期
- 实现自动保存功能

### business/game_manager.py
- **GameManager类**: 游戏核心控制器（单例模式）
- 管理游戏状态、玩家回合、游戏规则
- 处理玩家移动、房产交易、事件触发
- 实现观察者模式，通知界面更新

### business/models.py
- **Player类**: 玩家数据模型
- **MapCell类**: 地图格子数据模型
- **GameState/PlayerType/CellType**: 枚举类型定义
- **GameConfig类**: 游戏配置数据模型

### presentation/main_window.py
- **GameGUI类**: 游戏主界面控制器
- 实现游戏板绘制、玩家信息显示
- 处理用户交互事件
- 实现观察者模式，响应游戏状态变化

### data_access/database_manager.py
- **DatabaseManager类**: 数据库操作管理器（单例模式）
- 处理SQLite数据库连接和操作
- 实现游戏数据的持久化存储

## 开发指南

### 代码规范
- 遵循PEP 8 Python编码规范
- 使用类型注解提高代码可读性
- 每个类和方法都有详细的文档字符串
- 采用三层架构，保持层次分离

### 设计模式应用
1. **单例模式**: GameManager、DatabaseManager确保全局唯一实例
2. **观察者模式**: 游戏状态变化通知界面更新
3. **工厂模式**: AI策略创建
4. **命令模式**: 游戏操作封装，支持撤销/重做
5. **策略模式**: AI决策算法可插拔

### 扩展开发
- **添加新地图**: 修改`data/default_map.json`文件
- **新增AI策略**: 在`business/ai_strategy.py`中实现新策略类
- **自定义事件**: 在`business/events.py`中添加新事件类型
- **界面美化**: 修改`presentation/`目录下的界面文件

## 测试

项目包含完整的测试套件：
- **test_game.py**: 单元测试文件
- **run_tests.py**: 测试运行器
- **benchmark.py**: 性能基准测试
- **test_config.json**: 测试配置文件

运行测试：
```bash
# 运行所有测试
python run_tests.py

# 运行性能测试
python benchmark.py

# 运行快速性能测试
python benchmark.py quick
```

## 游戏特色

### 地图设计
- 36格青岛主题地图
- 包含著名景点：栈桥、八大关、崂山等
- 多种格子类型：房产、机场、税务、监狱等

### AI智能
- 多种AI策略：保守型、激进型、平衡型
- 智能决策算法，考虑投资回报率
- 动态策略调整

### 数据统计
- 详细的游戏统计数据
- 玩家表现分析
- 游戏历史记录

## 版本信息
- **当前版本**: v1.0.0
- **开发语言**: Python 3.8+
- **GUI框架**: Tkinter
- **数据库**: SQLite3
- **架构模式**: 三层架构 + 设计模式

## 贡献指南
1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证
本项目采用 MIT 许可证 - 查看 LICENSE 文件了解详情