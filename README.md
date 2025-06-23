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

## 面向对象设计原则

本项目严格遵循面向对象设计的SOLID原则，确保代码的可维护性、可扩展性和可重用性：

### 1. 单一职责原则 (Single Responsibility Principle)

每个类都有明确且单一的职责：

- **Player类** (`business/models.py`): 专门负责玩家数据和行为管理

  - 管理玩家属性（金钱、位置、房产等）
  - 处理玩家行为（移动、购买、升级等）
  - 不涉及界面显示或数据库操作
- **MapCell类** (`business/models.py`): 专门负责地图格子的属性和行为

  - 管理格子属性（价格、租金、等级等）
  - 处理房产相关操作（升级、租金计算等）
  - 不处理玩家逻辑或界面更新
- **DatabaseManager类** (`data_access/database_manager.py`): 专门负责数据库操作

  - 管理数据库连接和事务
  - 提供数据的增删改查接口
  - 不涉及业务逻辑处理
- **GameManager类** (`business/game_manager.py`): 专门负责游戏流程控制

  - 管理游戏状态和回合流转
  - 协调各个组件的交互
  - 不直接处理界面显示或数据存储

### 2. 开闭原则 (Open-Closed Principle)

系统对扩展开放，对修改封闭：

- **AI策略扩展**: 通过继承 `AIStrategy`抽象基类，可以轻松添加新的AI策略，无需修改现有代码

  ```python
  class NewAIStrategy(AIStrategy):
      def decide_purchase(self, player, cell):
          # 新的决策逻辑
          pass
  ```
- **事件系统扩展**: 通过抽象工厂模式，可以添加新的游戏模式和事件类型

  ```python
  class CustomGameFactory(AbstractGameFactory):
      def create_chance_events(self):
          # 创建自定义幸运事件
          pass
  ```
- **观察者模式**: 可以添加新的观察者（如日志记录器、统计模块）而不修改主题类

### 3. 里氏替换原则 (Liskov Substitution Principle)

子类可以完全替换父类使用：

- **AI策略替换**: 所有AI策略类都可以互相替换使用

  ```python
  # 任何AI策略都可以替换使用
  ai_strategy: AIStrategy = EasyAIStrategy()  # 或 MediumAIStrategy() 或 HardAIStrategy()
  decision = ai_strategy.decide_purchase(player, cell)
  ```
- **工厂类替换**: 不同的游戏工厂可以互相替换

  ```python
  # 任何工厂都可以替换使用
  factory: AbstractGameFactory = StandardGameFactory()  # 或其他工厂
  ai_strategy = factory.create_ai_strategy("medium")
  ```

### 4. 接口隔离原则 (Interface Segregation Principle)

接口设计精简，避免强迫类实现不需要的方法：

- **EventObserver接口**: 只定义必要的事件回调方法

  ```python
  class EventObserver(ABC):
      @abstractmethod
      def on_event_triggered(self, event_result: dict):
          pass
  ```
- **AIStrategy接口**: 分离不同类型的决策方法，每个方法职责明确

  ```python
  class AIStrategy(ABC):
      @abstractmethod
      def decide_purchase(self, player, cell): pass

      @abstractmethod
      def decide_upgrade(self, player, cell): pass

      @abstractmethod
      def decide_jail_action(self, player): pass
  ```

### 5. 依赖倒置原则 (Dependency Inversion Principle)

高层模块不依赖低层模块，都依赖抽象：

- **GameManager依赖抽象**: 依赖 `AIStrategy`抽象而不是具体实现

  ```python
  class GameManager:
      def __init__(self):
          self.ai_strategy: AIStrategy = None  # 依赖抽象
  ```
- **工厂模式应用**: 通过抽象工厂创建对象，避免直接依赖具体类

  ```python
  # 依赖抽象工厂而不是具体工厂
  factory = GameFactoryManager.get_factory(game_mode)
  ai_strategy = factory.create_ai_strategy(difficulty)
  ```

### 封装性体现

- **数据封装**: 使用 `@dataclass`和私有属性保护数据
- **方法封装**: 将复杂逻辑封装在私有方法中
- **模块封装**: 通过包结构实现功能模块的封装

### 多态性体现

- **AI策略多态**: 不同AI策略类实现相同接口，表现出不同行为
- **工厂类多态**: 不同工厂类创建不同的产品族
- **事件观察者多态**: 不同观察者对同一事件有不同响应

## 设计模式

- 单例模式 (Singleton): 游戏管理器
- 抽象工厂模式 (Abstract Factory): AI策略和事件系统的产品族创建
- 工厂模式 (Factory): 玩家和事件创建
- 观察者模式 (Observer): 游戏状态通知
- 策略模式 (Strategy): AI决策算法

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

business/
├── __init__.py            # 包初始化文件
├── game_manager.py        # 游戏管理器（单例模式），核心游戏逻辑控制
├── models.py              # 数据模型定义（玩家、地图格子、游戏状态等）
├── ai_strategy.py         # AI玩家策略算法实现
├── events.py              # 事件系统（观察者模式）
├── config_manager.py      # 配置管理器
├── game_state_manager.py  # 游戏状态管理器
└── game_statistics.py     # 游戏统计数据管理

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
2. **抽象工厂模式**: AI策略和事件系统的产品族创建
3. **观察者模式**: 游戏状态变化通知界面更新
4. **工厂模式**: AI策略创建
5. **命令模式**: 游戏操作封装，支持撤销/重做
6. **策略模式**: AI决策算法可插拔

#### 单例模式详细实现

**项目中的单例模式使用位置**:

**1. 游戏管理器 (GameManager)**

- 文件位置: `business/game_manager.py` 第16行
- 实现方式: 线程安全的双重检查锁定单例模式
- 职责: 游戏核心逻辑控制，管理游戏状态、玩家回合、游戏规则
- 关键代码:

```python
class GameManager(Observer):
    _instance = None
    _lock = threading.Lock()
  
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(GameManager, cls).__new__(cls)
        return cls._instance
```

**2. 数据库管理器 (DatabaseManager)**

- 文件位置: `data_access/database_manager.py` 第8行
- 实现方式: 线程安全的双重检查锁定单例模式
- 职责: SQLite数据库连接管理，游戏数据的持久化存储
- 关键代码:

```python
class DatabaseManager:
    _instance = None
    _lock = threading.Lock()
  
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance
```

**3. 配置管理器 (ConfigManager)**

- 文件位置: `business/config_manager.py` 第9行
- 实现方式: 简单单例模式
- 职责: 游戏配置参数管理，配置文件读取和写入
- 关键代码:

```python
class ConfigManager:
    _instance = None
    _initialized = False
  
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

**单例模式的使用场景**:

- GameManager: 作为游戏的中央控制器，确保全局唯一
- DatabaseManager: 管理数据库连接，避免连接池混乱
- ConfigManager: 统一管理游戏配置，确保配置一致性

#### 策略模式详细实现

**策略模式角色分析**:

**环境角色 (Context)**: `AIPlayer`类

- 持有策略对象的引用
- 提供统一的接口供客户端调用
- 将具体的决策委托给策略对象
- 位置: `business/ai_strategy.py` 第304行

**抽象策略角色 (Strategy)**: `AIStrategy`抽象基类

- 定义所有具体策略的公共接口
- 声明策略算法的抽象方法
- 确保所有具体策略都实现相同的接口
- 位置: `business/ai_strategy.py` 第6行
- 核心方法:
  - `decide_purchase()`: 购买决策
  - `decide_upgrade()`: 升级决策
  - `decide_jail_action()`: 监狱行动决策
  - `decide_trade()`: 交易决策

**具体策略角色 (ConcreteStrategy)**:

- `EasyAIStrategy` (第30行): 简单AI策略 - 保守型
  - 保守的购买策略（只买便宜房产）
  - 谨慎的升级决策
  - 倾向于在监狱中等待
- `MediumAIStrategy` (第80行): 中等AI策略 - 平衡型
  - 平衡的投资策略
  - 考虑收益的升级决策
  - 适度的风险承受能力
- `HardAIStrategy` (第184行): 困难AI策略 - 激进型
  - 激进的投资策略（偏好高价房产）
  - 积极的升级决策
  - 倾向于快速出狱

**工厂角色**: `AIStrategyFactory`类

- 根据难度参数创建相应的具体策略对象
- 封装策略对象的创建逻辑
- 位置: `business/ai_strategy.py` 第289行

**策略模式的使用场景**:

- 游戏管理器中: AI玩家创建时选择策略 (`game_manager.py` 第113行、第499行)
- 监狱决策: 调用 `ai_player.make_jail_decision()` (`game_manager.py` 第420行)
- 交易决策: 调用 `ai_player.make_trade_decision()` (`game_manager.py` 第447行)
- 购买决策: 调用 `ai_player.make_purchase_decision()` (`main_window.py` 第859行)
- 升级决策: 调用 `ai_player.make_upgrade_decision()` (`main_window.py` 第866行)

**策略模式的优势**:

- **可扩展性**: 可以轻松添加新的AI难度策略
- **可维护性**: 每种策略独立实现，互不影响
- **灵活性**: 运行时可以动态切换AI策略
- **代码复用**: 统一的策略接口，便于管理和调用

#### 抽象工厂模式详细实现

**抽象工厂模式角色分析**:

**抽象工厂 (AbstractFactory)**: `AbstractGameFactory`抽象类

- 定义创建产品族的抽象接口
- 位置: `business/abstract_factory.py` 第6行
- 核心方法:
  - `create_ai_strategy(difficulty)`: 创建AI策略
  - `create_chance_events()`: 创建幸运事件列表
  - `create_misfortune_events()`: 创建不幸事件列表

**具体工厂 (ConcreteFactory)**:

- `StandardGameFactory` (第6行): 标准游戏工厂
  - 创建标准难度的AI策略
  - 生成标准的幸运/不幸事件
  - 适用于普通游戏模式
- `HardModeGameFactory` (第35行): 困难模式工厂
  - 创建更具挑战性的AI策略
  - 生成更严苛的事件组合
  - 适用于高难度游戏
- `EasyModeGameFactory` (第64行): 简单模式工厂
  - 创建较为温和的AI策略
  - 生成更友好的事件组合
  - 适用于新手玩家

**抽象产品 (AbstractProduct)**:

- `AIStrategy`: AI策略抽象基类
- `ChanceEvent`: 幸运事件基类
- `MisfortuneEvent`: 不幸事件基类

**具体产品 (ConcreteProduct)**:

- AI策略产品族:
  - `EasyAIStrategy`: 简单AI策略
  - `MediumAIStrategy`: 中等AI策略
  - `HardAIStrategy`: 困难AI策略
- 事件产品族:
  - 各种具体的幸运事件实现
  - 各种具体的不幸事件实现

**工厂管理器 (Factory Manager)**: `GameFactoryManager`类

- 根据游戏模式选择合适的具体工厂
- 位置: `business/abstract_factory.py` 第93行
- 核心方法: `get_factory(game_mode)` - 返回对应的工厂实例
- 支持的游戏模式:
  - `"standard"`: 返回 `StandardGameFactory`
  - `"hard"`: 返回 `HardModeGameFactory`
  - `"easy"`: 返回 `EasyModeGameFactory`

**抽象工厂模式的使用场景**:

**AI策略系统**:

- 位置: `business/ai_strategy.py` 第12-15行
- 使用方式:
  ```python
  factory = GameFactoryManager.get_factory(game_mode)
  ai_strategy = factory.create_ai_strategy(difficulty)
  ```

**事件系统**:

- 位置: `business/events.py` 第15-25行
- 使用方式:
  ```python
  factory = GameFactoryManager.get_factory(game_mode)
  chance_events = factory.create_chance_events()
  misfortune_events = factory.create_misfortune_events()
  ```

**抽象工厂模式的优势**:

- **产品族一致性**: 确保同一游戏模式下的AI策略和事件风格一致
- **易于切换产品族**: 通过改变工厂类型，轻松切换整个产品族
- **符合开闭原则**: 添加新的游戏模式只需新增具体工厂，无需修改现有代码
- **分离接口与实现**: 客户端只依赖抽象工厂接口，不依赖具体实现
- **便于测试**: 可以轻松创建测试用的工厂和产品
- **扩展性强**: 支持添加新的产品类型和新的游戏模式

**扩展示例**:

要添加新的游戏模式（如"nightmare"超级困难模式），只需：

1. 创建 `NightmareGameFactory` 继承 `AbstractGameFactory`
2. 实现对应的产品创建方法
3. 在 `GameFactoryManager` 中注册新工厂
4. 无需修改任何现有代码

这种设计使得游戏的难度系统具有极高的可扩展性和可维护性。

#### 观察者模式详细实现

**观察者模式角色分析**:

**抽象观察者 (Observer)**: `EventObserver`接口

- 定义观察者的更新接口
- 位置: `business/events.py` 第231行
- 核心方法: `on_event_triggered(event_result)` - 事件触发时的回调

**主题类 (Subject)**: `EventSubject`类

- 维护观察者列表
- 提供添加、删除、通知观察者的方法
- 位置: `business/events.py` 第239行
- 核心方法:
  - `attach(observer)`: 添加观察者
  - `detach(observer)`: 移除观察者
  - `notify(event_result)`: 通知所有观察者

**具体主题 (ConcreteSubject)**: `GameManager`类

- 继承 `EventSubject`，作为事件发布者
- 在游戏状态变化时通知观察者
- 位置: `business/game_manager.py` 第15行

**具体观察者 (ConcreteObserver)**: `GameGUI`类

- 实现 `EventObserver` 接口
- 接收游戏事件通知并更新界面
- 位置: `presentation/main_window.py` 第13行
- 注册方式: `self.game_manager.attach(self)` (第29行)

**观察者模式的使用场景**:

- 幸运事件通知: 玩家触发幸运格子时 (`game_manager.py` 第286行)
- 不幸事件通知: 玩家触发不幸格子时 (`game_manager.py` 第299行)
- 购买通知: 玩家购买地产时 (`game_manager.py` 第355行)
- 升级通知: 玩家升级地产时 (`game_manager.py` 第370行)
- 监狱相关通知: 玩家进入/离开监狱时 (`game_manager.py` 第425-443行)
- 税务处理通知: 玩家缴纳税费时 (`game_manager.py` 第328行)

**观察者模式的优势**:

- 解耦合: 游戏逻辑层与界面层完全分离
- 实时更新: 游戏状态变化时自动通知界面更新
- 可扩展性: 可以轻松添加新的观察者(如日志记录器、统计模块等)
- 线程安全: 使用 `root.after()` 确保UI更新在主线程中执行

### 扩展开发

- **添加新地图**: 修改 `data/default_map.json`文件
- **新增AI策略**: 在 `business/ai_strategy.py`中实现新策略类
- **自定义事件**: 在 `business/events.py`中添加新事件类型
- **界面美化**: 修改 `presentation/`目录下的界面文件

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
