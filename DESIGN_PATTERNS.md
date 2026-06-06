# 设计模式应用说明

本文档详细说明选课系统重构中每个设计模式的应用位置、核心作用和选择理由。

---

## 一、创建型模式

### 1. 单例模式 (Singleton Pattern)

**应用场景：** 确保全局唯一实例，节约资源

| 应用位置 | 说明 |
|---------|------|
| `backend/app/extensions.py` | `db = SQLAlchemy()` — 全局唯一的数据库连接池实例 |
| `backend/app/config.py` | `config` 字典 — 全局唯一的配置映射，通过 `python-dotenv` 加载 |
| `backend/app/services/agent_service.py:771` | `agent = CourseAgent()` — 全局唯一的 AI 助手实例 |
| `src/api/request.js` | `axios.create()` — 全局唯一的 HTTP 请求实例 |
| `src/stores/auth.js` | `useAuthStore` — Pinia store 天然单例 |
| `src/stores/courses.js` | `useCourseStore` — Pinia store 天然单例 |
| `src/stores/selection.js` | `useSelectionStore` — Pinia store 天然单例 |

**选择理由：** 数据库连接池、配置、HTTP 客户端等资源应全局共享，避免重复创建浪费资源。Pinia 的 store 本身设计就是单例的。

---

### 2. 工厂模式 (Factory Pattern)

**应用场景：** 封装对象创建逻辑，解耦创建与使用

| 应用位置 | 说明 |
|---------|------|
| `backend/app/__init__.py` | `create_app(config_name)` — Flask 应用工厂，封装配置加载、扩展初始化、蓝图注册全流程 |
| `src/main.js` | `createApp(App)` — Vue 应用工厂，注册 Pinia 和 Router |

**选择理由：** 应用创建涉及多个步骤（配置、初始化、注册），工厂模式将这些步骤封装，调用方只需一行代码即可获得配置完成的应用实例。支持多环境切换（dev/test/prod）。

---

## 二、结构型模式

### 3. MVC 模式 (Model-View-Controller)

**应用场景：** 贯穿全系统架构的核心分层模式

#### 后端 MVC

| 层 | 目录 | 职责 |
|----|------|------|
| **Model** | `backend/app/models/` | 数据模型定义（User, Course, Selection, UserHistory），ORM 映射 |
| **View** | `backend/app/utils/response.py` | 接口 JSON 响应封装（ApiResponse） |
| **Controller** | `backend/app/blueprints/` | 路由处理 + 业务逻辑委托给 Service 层 |

#### 前端 MVC

| 层 | 目录 | 职责 |
|----|------|------|
| **Model** | `src/stores/` | 响应式数据状态（Pinia stores） |
| **View** | `src/views/`, `src/components/` | UI 渲染（Vue 模板） |
| **Controller** | Store actions + 事件处理 | 业务逻辑 + API 调用 |

**选择理由：** MVC 是最经典的分层模式，将数据、展示、逻辑三者分离，每个模块职责清晰，便于独立开发和测试。

---

### 4. 蓝图模式 (Blueprint Pattern)

**应用场景：** 后端路由模块化拆分，前端路由模块化

| 应用位置 | 说明 |
|---------|------|
| `backend/app/blueprints/auth.py` | 认证蓝图 — `/api/auth/*` |
| `backend/app/blueprints/courses.py` | 课程蓝图 — `/api/courses/*` |
| `backend/app/blueprints/selection.py` | 选课蓝图 — `/api/selection/*` |
| `backend/app/blueprints/profile.py` | 个人资料蓝图 — `/api/profile/*` |
| `backend/app/blueprints/recommendations.py` | 推荐蓝图 — `/api/recommendations/*` |
| `backend/app/blueprints/chat.py` | 聊天蓝图 — `/api/chat/*` |
| `src/router/index.js` | Vue Router 路由配置 — 按页面拆分路由 |

**选择理由：** 将不同业务模块的路由独立封装，每个蓝图只关注自己的业务域，降低模块间耦合。统一在 `create_app()` 中注册，便于管理。

---

### 5. 代理模式 (Proxy Pattern)

**应用场景：** 在不修改原对象的情况下，拦截和增强请求

| 应用位置 | 说明 |
|---------|------|
| `backend/app/decorators/auth.py` | `@login_required` — 代理视图函数执行，在调用前验证 JWT Token |
| `src/api/request.js` | Axios 请求拦截器 — 代理所有 HTTP 请求，自动注入 Token |
| `src/api/request.js` | Axios 响应拦截器 — 代理所有 HTTP 响应，统一处理 401 跳转 |
| `src/router/index.js` | 路由守卫 `beforeEach` — 代理页面导航，拦截未登录访问 |

**选择理由：** 权限校验、Token 注入等横切关注点不应侵入业务代码。代理模式在不修改原函数/组件的情况下，附加额外行为。

---

### 6. 装饰器模式 (Decorator Pattern)

**应用场景：** 动态地为对象附加额外功能

| 应用位置 | 说明 |
|---------|------|
| `backend/app/decorators/logging.py` | `@log_request` — 为视图函数附加请求日志记录功能 |
| `backend/app/blueprints/*.py` | 装饰器组合使用：`@login_required` + `@log_request` |

**选择理由：** 日志记录是典型的横切关注点，装饰器模式允许在不修改原函数代码的情况下，为多个函数统一添加日志功能。与代理模式的区别：装饰器侧重"增强功能"，代理侧重"控制访问"。

---

## 三、行为型模式

### 7. 观察者模式 (Observer Pattern)

**应用场景：** 数据变化自动触发视图更新

| 应用位置 | 说明 |
|---------|------|
| `src/stores/auth.js` | 认证状态变化 → 登录/退出按钮、路由守卫自动响应 |
| `src/stores/courses.js` | 课程数据/筛选条件变化 → `filteredCourses` 自动重算，课程列表自动刷新 |
| `src/stores/selection.js` | 已选课程变化 → CartSummary 学分自动更新、冲突警告自动重算 |

**核心机制：** Vue 3 的响应式系统（`ref`、`computed`）+ Pinia 的 store 订阅机制，实现了观察者模式。当 store 中的 `ref` 值变化时，所有通过 `storeToRefs()` 或直接访问 store 的组件会自动重新渲染。

**选择理由：** 手动操作 DOM 来同步数据状态既繁琐又易出错。观察者模式让数据驱动视图，开发者只需关心数据变化，视图更新由框架自动完成。

---

### 8. 模板方法模式 (Template Method Pattern)

**应用场景：** 定义操作的骨架，将某些步骤延迟到子类/具体实现

| 应用位置 | 说明 |
|---------|------|
| `backend/app/utils/response.py` | `ApiResponse` — 统一响应模板，所有接口返回 `{code, message, data}` |
| `src/api/request.js` | Axios 拦截器 — 统一的请求/响应处理模板 |
| `src/api/*.js` | 各 API 模块遵循相同的调用模板：导入 request → 调用方法 → 返回数据 |

**选择理由：** 接口响应格式不统一会增加前端解析成本。模板方法模式确保所有接口遵循同一响应格式，减少重复代码，提高可维护性。

---

### 9. 策略模式 (Strategy Pattern)

**应用场景：** 封装可互换的算法族，根据上下文选择不同策略

| 应用位置 | 说明 |
|---------|------|
| `backend/app/services/selection_service.py` | `EnrollmentStrategy` — 选课策略抽象基类 |
| 同上 | `MajorCourseStrategy` — 专业课策略（无额外限制） |
| 同上 | `GeneralCourseStrategy` — 公共课策略（限制选课数量 ≤ 5） |
| 同上 | `ElectiveCourseStrategy` — 选修课策略（默认策略） |
| 同上 | `SelectionService._get_strategy()` — 策略工厂，根据课程类型选择策略 |

**选择理由：** 不同课程类型的选课规则可能不同（如公共课有数量限制）。策略模式将每种规则封装为独立策略，新增规则只需添加新策略类，无需修改现有代码（开闭原则）。

---

## 四、模式组合应用

### 代理 + 装饰器组合

```python
@auth_bp.route("/me", methods=["GET"])
@login_required   # 代理模式 — 控制访问
@log_request      # 装饰器模式 — 增强功能
def me():
    return ApiResponse.success({"user": g.current_user.to_dict()})
```

`@login_required` 先验证身份（代理），`@log_request` 再记录日志（装饰器），两者组合使用，职责清晰。

### 工厂 + 单例 + 蓝图组合

```python
def create_app(config_name):    # 工厂模式
    app = Flask(__name__)
    app.config.from_object(config[config_name])  # 单例配置
    db.init_app(app)            # 单例 db
    _register_blueprints(app)   # 蓝图模式
    return app
```

工厂函数统一协调单例实例和蓝图注册，三者协同工作。

---

## 五、扩展建议

| 扩展方向 | 推荐模式 | 说明 |
|---------|---------|------|
| 角色权限控制 | 策略模式 + 代理模式 | 新增 `RoleStrategy`，`@role_required` 装饰器 |
| 成绩管理 | 工厂模式 + MVC | 新增 `Grade` 模型和蓝图 |
| 课程统计 | 观察者模式 | 统计数据变化时自动更新图表 |
| 缓存优化 | 代理模式 | 缓存代理拦截重复查询 |
| 消息通知 | 观察者模式 | 选课事件发布 → 通知订阅者 |
