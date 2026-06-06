# SelectClass — 基于设计模式的智能选课系统

> 一款遵循经典设计模式规范重构的学生选课管理平台，采用 Vue 3 + Flask 前后端分离架构，支持自然语言对话选课与个性化课程推荐。

---

## 一、项目简介

### 1.1 项目名称

**SelectClass — 智能选课系统（设计模式重构版）**

### 1.2 项目定位

本系统是一款基于经典设计模式规范重构的学生选课管理平台。针对原有系统**耦合度高、代码冗余、可维护性差**等问题，通过引入 9 种设计模式（覆盖创建型、结构型、行为型三大类），实现了模块职责清晰、代码可复用、易于扩展的现代化架构。

### 1.3 核心功能

| 功能模块 | 功能说明 |
|---------|---------|
| **登录认证** | 学生注册、登录，JWT Token 认证，密码 bcrypt 加密 |
| **课程浏览** | 按院系、类型、难度筛选，关键词搜索，课程详情查看 |
| **选课/退课** | 批量选课、单课程退选，自动检测时间冲突 |
| **智能助理** | 自然语言对话选课（"帮我选CS101"、"退掉数学课"等） |
| **个性化推荐** | 基于专业、年级、兴趣的智能课程推荐 |
| **个人中心** | 查看/编辑个人资料（专业、年级、兴趣） |
| **暗色模式** | 支持亮色/暗色主题切换 |

### 1.4 重构亮点

- **9 种设计模式落地**：单例、工厂、MVC、蓝图、观察者、模板方法、代理、策略、装饰器
- **前后端分层解耦**：后端 MVC 三层架构，前端 Store/View/Component 分层
- **策略模式驱动选课**：不同课程类型（专业课/公共课/选修课）采用独立选课策略，开闭原则
- **统一响应模板**：所有接口返回格式统一 `{code, message, data}`，降低前后端联调成本
- **装饰器组合**：`@login_required`（代理）+ `@log_request`（装饰器）组合使用，职责清晰


## 三、设计模式应用详情

### 创建型模式

#### 1. 单例模式 (Singleton Pattern)

- **模式类型**：创建型
- **应用场景**：
  - 后端数据库连接（SQLAlchemy 实例）
  - 后端全局配置加载
  - 后端 AI 助手实例
  - 前端全局 Axios 实例
  - 前端 Pinia Store（天然单例）
- **核心作用**：保证全局唯一实例，避免资源重复创建，节约系统开销
- **优化说明**：解决重构前数据库连接重复创建、配置多处加载、HTTP 客户端分散管理的问题

**代码示例 — 后端数据库单例**：

文件路径：`backend/app/extensions.py`

```python
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

# 数据库单例 — 全局唯一 SQLAlchemy 实例
db = SQLAlchemy()

# CORS 单例
cors = CORS()
```

在 `create_app()` 中通过 `db.init_app(app)` 初始化，确保全局共享同一连接池。

**代码示例 — 前端 Axios 单例**：

文件路径：`src/api/request.js`

```javascript
import axios from 'axios'

// Singleton — 全局唯一 Axios 实例
const request = axios.create({
  baseURL: '',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' }
})

export default request
```

**代码示例 — 后端配置单例**：

文件路径：`backend/app/config.py`

```python
class Config:
    """基础配置（单例基类）"""
    SECRET_KEY = os.getenv("JWT_SECRET", "dev-secret-key")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = 8
    # ...

# 配置映射 — 全局唯一入口
config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
```

---

#### 2. 工厂模式 (Factory Pattern)

- **模式类型**：创建型
- **应用场景**：
  - 后端 Flask 应用创建（`create_app()` 函数）
  - 前端 Vue 应用创建（`createApp()` 函数）
- **核心作用**：封装对象创建的完整流程（配置加载 → 扩展初始化 → 蓝图/路由注册），解耦创建与使用
- **优化说明**：解决重构前应用初始化逻辑散落、多环境切换困难的问题

**代码示例 — 后端应用工厂**：

文件路径：`backend/app/__init__.py`

```python
def create_app(config_name: str = "default") -> Flask:
    """Flask 应用工厂 — Factory Pattern"""
    app = Flask(__name__)

    # 1. 加载配置（Singleton Pattern）
    app.config.from_object(config[config_name])
    app.config["SQLALCHEMY_DATABASE_URI"] = config[config_name]().SQLALCHEMY_DATABASE_URI

    # 2. 初始化扩展（Singleton Pattern）
    db.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", ["*"])}})

    # 3. 注册蓝图（Blueprint Pattern）
    _register_blueprints(app)

    # 4. 注册错误处理器
    _register_error_handlers(app)

    # 5. 创建数据库表
    with app.app_context():
        from . import models
        db.create_all()

    return app
```

**代码示例 — 前端应用工厂**：

文件路径：`src/main.js`

```javascript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'

// Factory Pattern — 创建应用实例
const app = createApp(App)

// 注册 Pinia — Observer Pattern 的基础设施
const pinia = createPinia()
app.use(pinia)

// 注册路由 — Blueprint Pattern 的前端实现
app.use(router)

app.mount('#app')
```

---

### 结构型模式

#### 3. MVC 模式 (Model-View-Controller)

- **模式类型**：结构型
- **应用场景**：贯穿全系统的核心分层架构
- **核心作用**：将数据模型、用户界面、业务逻辑三者分离，每个层职责单一
- **优化说明**：解决重构前业务逻辑与路由处理混杂、数据操作分散的问题

**后端 MVC 分层**：

| 层 | 目录 | 职责 | 代表文件 |
|----|------|------|---------|
| **Model** | `backend/app/models/` | 数据模型定义、ORM 映射、关系声明 | `user.py`, `course.py`, `selection.py` |
| **View** | `backend/app/utils/response.py` | 接口 JSON 响应封装 | `ApiResponse` 类 |
| **Controller** | `backend/app/blueprints/` | 路由处理、参数校验、委托 Service 层 | `auth.py`, `courses.py`, `selection.py` |

**前端 MVC 分层**：

| 层 | 目录 | 职责 | 代表文件 |
|----|------|------|---------|
| **Model** | `src/stores/` | 响应式数据状态管理 | `auth.js`, `courses.js`, `selection.js` |
| **View** | `src/views/`, `src/components/` | UI 模板渲染 | `CatalogView.vue`, `CourseCard.vue` |
| **Controller** | Store actions + 事件处理 | 业务逻辑、API 调用 | Store 中的 `login()`, `addCourse()` 等 |

**代码示例 — Model 层**：

文件路径：`backend/app/models/user.py`

```python
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, index=True)
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    major = db.Column(db.String(100), default="")
    grade = db.Column(db.String(50), default="")
    interests = db.Column(db.Text, default="")

    selections = db.relationship("Selection", back_populates="user", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id, "username": self.username,
            "major": self.major, "grade": self.grade, "interests": self.interests,
        }
```

**代码示例 — Controller 层（蓝图）**：

文件路径：`backend/app/blueprints/selection.py`

```python
selection_bp = Blueprint("selection", __name__, url_prefix="/api/selection")

@selection_bp.route("/", methods=["POST"])
@login_required
@log_request
def enroll():
    """批量选课 — Controller 层：参数校验 + 委托 Service"""
    data = request.get_json(silent=True) or {}
    course_ids = data.get("courseIds") or data.get("course_ids") or []
    if not course_ids:
        return ApiResponse.error("请提交选课课程 ID 列表。")

    result = selection_service.enroll_courses(g.current_user, course_ids)
    if not result["success"]:
        return ApiResponse.error(result["error"])

    return ApiResponse.success([c.to_dict() for c in result["courses"]])
```

---

#### 4. 蓝图模式 (Blueprint Pattern)

- **模式类型**：结构型
- **应用场景**：后端路由模块化拆分、前端路由模块化
- **核心作用**：将不同业务模块的路由独立封装，降低模块间耦合，统一注册管理
- **优化说明**：解决重构前所有路由堆砌在同一文件、模块边界模糊的问题

**后端蓝图注册表**：

| 蓝图 | 文件路径 | URL 前缀 | 职责 |
|------|---------|----------|------|
| `auth_bp` | `backend/app/blueprints/auth.py` | `/api/auth` | 注册、登录、获取用户 |
| `courses_bp` | `backend/app/blueprints/courses.py` | `/api/courses` | 课程列表、详情 |
| `selection_bp` | `backend/app/blueprints/selection.py` | `/api/selection` | 选课、退课、已选列表 |
| `profile_bp` | `backend/app/blueprints/profile.py` | `/api/profile` | 个人资料更新 |
| `recommendations_bp` | `backend/app/blueprints/recommendations.py` | `/api/recommendations` | 课程推荐 |
| `chat_bp` | `backend/app/blueprints/chat.py` | `/api/chat` | 智能助手对话 |

**代码示例 — 蓝图定义与注册**：

文件路径：`backend/app/blueprints/auth.py`

```python
from flask import Blueprint

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

@auth_bp.route("/register", methods=["POST"])
def register():
    # ...
```

文件路径：`backend/app/__init__.py`

```python
def _register_blueprints(app: Flask):
    """注册所有蓝图 — Blueprint Pattern"""
    from .blueprints import (
        auth_bp, courses_bp, selection_bp,
        profile_bp, recommendations_bp, chat_bp,
    )
    app.register_blueprint(auth_bp)
    app.register_blueprint(courses_bp)
    app.register_blueprint(selection_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(recommendations_bp)
    app.register_blueprint(chat_bp)
```

**前端路由（Vue Router — 等价蓝图模式）**：

文件路径：`src/router/index.js`

```javascript
const routes = [
  { path: '/login',  name: 'Login',   component: () => import('../views/LoginView.vue'),   meta: { requiresAuth: false } },
  { path: '/',       name: 'Catalog', component: () => import('../views/CatalogView.vue'),  meta: { requiresAuth: true } },
  { path: '/profile',name: 'Profile', component: () => import('../views/ProfileView.vue'),  meta: { requiresAuth: true } },
  { path: '/:pathMatch(.*)*', name: 'NotFound', component: () => import('../views/NotFoundView.vue') },
]
```

---

#### 5. 代理模式 (Proxy Pattern)

- **模式类型**：结构型
- **应用场景**：
  - 后端 `@login_required` 装饰器 — 代理视图函数执行，拦截未授权请求
  - 前端 Axios 请求拦截器 — 代理所有 HTTP 请求，自动注入 Token
  - 前端路由守卫 — 代理页面导航，拦截未登录访问
- **核心作用**：在不修改原对象/函数的情况下，拦截和控制访问行为
- **优化说明**：解决重构前权限校验代码重复、Token 管理分散的问题

**代码示例 — 后端权限代理**：

文件路径：`backend/app/decorators/auth.py`

```python
def login_required(f):
    """登录校验装饰器 — Proxy Pattern：代理视图函数的执行"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        token = auth_header.replace("Bearer ", "").strip()

        if not token:
            return ApiResponse.unauthorized("缺少认证令牌")

        try:
            cfg = config["default"]
            payload = jwt.decode(token, cfg.JWT_SECRET, algorithms=[cfg.JWT_ALGORITHM])
            username = payload.get("sub")
            if username is None:
                return ApiResponse.unauthorized("无效的认证令牌")
        except JWTError:
            return ApiResponse.unauthorized("认证令牌已过期或无效")

        user = db.session.query(User).filter(User.username == username).first()
        if user is None:
            return ApiResponse.unauthorized("用户不存在")

        g.current_user = user  # 验证通过，注入用户对象
        return f(*args, **kwargs)
    return decorated
```

**代码示例 — 前端请求代理**：

文件路径：`src/api/request.js`

```javascript
// Proxy Pattern — 请求拦截器：代理所有请求，自动注入 Token
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器：代理所有响应，统一处理 401
request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.hash = '#/login'
    }
    return Promise.reject(error)
  }
)
```

**代码示例 — 前端路由守卫**：

文件路径：`src/router/index.js`

```javascript
// Proxy Pattern — 路由守卫：代理导航行为
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/')
  } else {
    next()
  }
})
```

---

#### 6. 装饰器模式 (Decorator Pattern)

- **模式类型**：结构型
- **应用场景**：后端 `@log_request` 日志装饰器
- **核心作用**：动态地为视图函数附加日志记录功能，不修改原函数逻辑
- **优化说明**：解决重构前日志记录代码散落在各路由函数中的问题

**代码示例**：

文件路径：`backend/app/decorators/logging.py`

```python
def log_request(f):
    """请求日志装饰器 — Decorator Pattern：为视图函数附加日志记录"""
    @wraps(f)
    def decorated(*args, **kwargs):
        start = time.time()
        logger.info("→ %s %s", request.method, request.path)
        result = f(*args, **kwargs)
        elapsed = time.time() - start
        logger.info("← %s %s (%.3fs)", request.method, request.path, elapsed)
        return result
    return decorated
```

**装饰器组合使用**（代理 + 装饰器）：

文件路径：`backend/app/blueprints/selection.py`

```python
@selection_bp.route("/", methods=["GET"])
@login_required   # 代理模式 — 控制访问权限
@log_request      # 装饰器模式 — 附加日志功能
def list_selections():
    """两个装饰器组合：先验证身份，再记录日志"""
    courses = selection_service.get_user_selections(g.current_user.id)
    return ApiResponse.success([c.to_dict() for c in courses])
```

---

### 行为型模式

#### 7. 观察者模式 (Observer Pattern)

- **模式类型**：行为型
- **应用场景**：前端 Pinia 状态管理（课程列表、已选课程、登录状态等响应式数据）
- **核心作用**：当数据状态变化时，所有订阅该数据的组件自动更新视图，无需手动操作 DOM
- **优化说明**：解决重构前组件间数据传递层层 props 下发、事件层层冒泡的问题

**代码示例 — 认证状态观察者**：

文件路径：`src/stores/auth.js`

```javascript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  // State — 被观察的数据
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(null)

  // Getters — 自动响应数据变化
  const isLoggedIn = computed(() => !!token.value && !!user.value)
  const needsProfile = computed(() => isLoggedIn.value && !user.value?.major)

  // Actions — 修改状态，自动触发视图更新
  function setToken(value) {
    token.value = value
    if (value) localStorage.setItem('token', value)
    else localStorage.removeItem('token')
  }

  function logout() {
    setToken('')
    user.value = null  // 触发所有依赖 user 的组件重新渲染
  }

  return { token, user, isLoggedIn, needsProfile, setToken, logout }
})
```

**观察者模式的工作流**：

```
用户操作 → Store Action 修改 State → Vue 响应式系统检测变化 → 自动更新所有订阅组件
```

例如：`selectionStore.addCourse(course)` 执行后，CartSummary（学分统计）、CatalogView（已选标记）、Sidebar（推荐列表）三个组件自动更新。

---

#### 9. 策略模式 (Strategy Pattern)

- **模式类型**：行为型
- **应用场景**：后端选课服务 — 不同课程类型（专业课、公共课、选修课）采用不同的选课规则
- **核心作用**：将选课规则封装为独立策略类，根据课程类型动态选择策略执行
- **优化说明**：解决重构前选课逻辑中大量 if-else 分支、新增规则需修改核心代码的问题（开闭原则）

**代码示例 — 策略抽象基类与具体策略**：

文件路径：`backend/app/services/selection_service.py`

```python
from abc import ABC, abstractmethod

# 策略抽象基类
class EnrollmentStrategy(ABC):
    @abstractmethod
    def validate(self, user, course, existing_courses) -> str | None:
        """校验选课条件"""
        pass

    @abstractmethod
    def execute(self, user_id: int, course) -> None:
        """执行选课操作"""
        pass

# 专业课策略 — 无额外限制
class MajorCourseStrategy(EnrollmentStrategy):
    def validate(self, user, course, existing_courses):
        if course.id in {c.id for c in existing_courses}:
            return f"你已经选了 {course.code}，不需要重复添加"
        if find_conflict(existing_courses, [course]):
            return f"课程 {course.code} 与已选课程存在时间冲突"
        return None

    def execute(self, user_id, course):
        db.session.add(Selection(user_id=user_id, course_id=course.id))

# 公共课策略 — 限制选课数量
class GeneralCourseStrategy(EnrollmentStrategy):
    MAX_GENERAL_COURSES = 5

    def validate(self, user, course, existing_courses):
        # ... 同上校验 + 额外数量限制
        general_count = sum(1 for c in existing_courses if c.course_type == "公共课")
        if general_count >= self.MAX_GENERAL_COURSES:
            return f"公共课最多选 {self.MAX_GENERAL_COURSES} 门"
        return None

# 选修课策略 — 默认策略
class ElectiveCourseStrategy(EnrollmentStrategy):
    # ...

# 策略注册表
_strategies = {
    "专业课": MajorCourseStrategy(),
    "公共课": GeneralCourseStrategy(),
}
_default_strategy = ElectiveCourseStrategy()

def _get_strategy(course_type: str) -> EnrollmentStrategy:
    return _strategies.get(course_type, _default_strategy)
```

**策略模式调用**：

```python
def enroll_courses(user, course_ids: list[int]) -> dict:
    for course in requested_courses:
        strategy = _get_strategy(course.course_type)  # 根据类型选择策略
        error = strategy.validate(user, course, existing_courses)
        if error:
            return {"success": False, "error": error}
        strategy.execute(user.id, course)  # 执行策略
```

**扩展方式**：新增课程类型只需添加新的策略类并注册到 `_strategies` 字典，无需修改 `enroll_courses()` 函数。

---

## 四、项目结构

### 4.1 后端目录结构

```
backend/
├── run.py                              # Flask 应用入口
├── requirements.txt                    # Python 依赖清单
├── .env                                # 环境变量（不提交 Git）
├── course_selection.db                 # SQLite 数据库文件
├── data/
│   └── courses.json                    # 课程种子数据（36 门课，17 个学院）
├── scripts/
│   └── import_courses.py               # 课程数据导入脚本
└── app/                                # 核心业务代码
    ├── __init__.py                     # 应用工厂（Factory Pattern）
    ├── config.py                       # 配置管理（Singleton Pattern）
    ├── extensions.py                   # 扩展实例（Singleton Pattern）
    │
    ├── models/                         # === MVC Model 层 ===
    │   ├── __init__.py                 # 模型统一导出
    │   ├── user.py                     # 用户模型
    │   ├── course.py                   # 课程模型
    │   ├── selection.py                # 选课记录模型
    │   └── history.py                  # 用户行为历史模型
    │
    ├── blueprints/                     # === MVC Controller 层（Blueprint Pattern）===
    │   ├── __init__.py                 # 蓝图统一导出
    │   ├── auth.py                     # 认证蓝图（/api/auth/*）
    │   ├── courses.py                  # 课程蓝图（/api/courses/*）
    │   ├── selection.py                # 选课蓝图（/api/selection/*）
    │   ├── profile.py                  # 个人资料蓝图（/api/profile/*）
    │   ├── recommendations.py          # 推荐蓝图（/api/recommendations/*）
    │   └── chat.py                     # 聊天蓝图（/api/chat/*）
    │
    ├── services/                       # === 业务逻辑层 ===
    │   ├── __init__.py
    │   ├── auth_service.py             # 认证服务（密码哈希、JWT）
    │   ├── course_service.py           # 课程查询服务
    │   ├── selection_service.py        # 选课服务（Strategy Pattern）
    │   ├── recommendation_service.py   # 推荐服务（评分算法）
    │   ├── agent_service.py            # 智能助手（LLM 工具调用）
    │   ├── mimo_client.py              # MiMo LLM 客户端
    │   └── conflict.py                 # 时间冲突检测
    │
    ├── decorators/                     # === 装饰器（Proxy + Decorator Pattern）===
    │   ├── __init__.py
    │   ├── auth.py                     # @login_required（Proxy Pattern）
    │   └── logging.py                  # @log_request（Decorator Pattern）
    │
    └── utils/                          # === 工具模块（Template Method Pattern）===
        ├── __init__.py
        ├── response.py                 # ApiResponse 统一响应模板
        └── validators.py               # 参数校验工具
```

### 4.2 前端目录结构

```
src/
├── main.js                             # 应用入口（Factory Pattern）
├── App.vue                             # 根组件
│
├── router/                             # === 路由配置（Blueprint Pattern）===
│   └── index.js                        # 路由定义 + 路由守卫（Proxy Pattern）
│
├── stores/                             # === 状态管理（Observer Pattern）===
│   ├── auth.js                         # 认证状态（token、user、login/logout）
│   ├── courses.js                      # 课程状态（列表、筛选、搜索）
│   └── selection.js                    # 选课状态（已选课程、冲突检测、推荐）
│
├── api/                                # === API 请求层（Singleton + Template + Proxy）===
│   ├── request.js                      # Axios 单例 + 拦截器
│   ├── auth.js                         # 认证 API
│   ├── courses.js                      # 课程 API
│   ├── selection.js                    # 选课 API
│   ├── chat.js                         # 聊天 API
│   ├── recommendations.js              # 推荐 API
│   └── profile.js                      # 个人资料 API
│
├── views/                              # === 页面组件（MVC View 层）===
│   ├── LoginView.vue                   # 登录/注册页
│   ├── CatalogView.vue                 # 课程目录页（主页面）
│   ├── ProfileView.vue                 # 个人中心页
│   └── NotFoundView.vue                # 404 页面
│
├── components/                         # === 通用组件 ===
│   ├── AppHeader.vue                   # 全局导航栏
│   ├── CourseCard.vue                  # 课程卡片（支持拖拽）
│   ├── CourseModal.vue                 # 课程详情弹窗
│   ├── CartSummary.vue                 # 选课摘要侧边栏
│   └── Sidebar.vue                     # 智能助理聊天面板
│
└── assets/
    └── styles.css                      # 全局样式（含暗色主题）
```

### 4.3 目录拆分合理性说明

| 拆分决策 | 设计模式 | 理由 |
|---------|---------|------|
| `models/` 独立为包 | MVC Model | 模型职责单一，每个模型独立文件便于维护 |
| `blueprints/` 按业务拆分 | Blueprint | 每个蓝图只关注自己的业务域，互不依赖 |
| `services/` 业务逻辑层 | MVC Controller | 蓝图只做路由转发，业务逻辑下沉到 Service |
| `decorators/` 独立目录 | Proxy + Decorator | 装饰器是横切关注点，独立管理便于复用 |
| `stores/` 按功能拆分 | Observer | 每个 Store 管理一个独立的状态域 |
| `api/` 按模块拆分 | Singleton + Template | API 层与后端蓝图一一对应，职责清晰 |

---