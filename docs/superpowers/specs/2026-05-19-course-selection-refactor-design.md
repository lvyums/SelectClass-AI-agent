# Course Selection System — Design Pattern Refactoring Spec

## Overview

Refactor the existing course selection system from FastAPI to Flask, applying design patterns across both backend (Flask + SQLAlchemy + SQLite) and frontend (Vue3 + Pinia + Vue Router). Preserve all existing functionality including AI chat, recommendations, and enrollment.

## Architecture

### Backend: Flask MVC

```
backend/
├── run.py                        # Entry point
├── requirements.txt
├── data/courses.json
├── scripts/import_courses.py
├── course_selection.db
└── app/
    ├── __init__.py               # create_app() — Factory Pattern
    ├── config.py                 # Singleton — Config class
    ├── extensions.py             # Singleton — db, migrate, cors instances
    ├── models/                   # Model Layer (MVC)
    │   ├── __init__.py
    │   ├── user.py
    │   ├── course.py
    │   ├── selection.py
    │   └── history.py
    ├── schemas/                  # Marshmallow serialization
    │   ├── __init__.py
    │   ├── user.py
    │   ├── course.py
    │   └── selection.py
    ├── services/                 # Business Logic Layer
    │   ├── __init__.py
    │   ├── auth_service.py
    │   ├── course_service.py
    │   ├── selection_service.py  # Strategy Pattern
    │   ├── recommendation_service.py
    │   ├── agent_service.py
    │   └── conflict.py
    ├── blueprints/               # Blueprint Pattern (Controller Layer)
    │   ├── __init__.py
    │   ├── auth.py
    │   ├── courses.py
    │   ├── selection.py
    │   ├── profile.py
    │   ├── recommendations.py
    │   └── chat.py
    ├── decorators/               # Decorator + Proxy Pattern
    │   ├── __init__.py
    │   ├── auth.py               # @login_required
    │   └── logging.py            # @log_request
    └── utils/                    # Template Method Pattern
        ├── __init__.py
        ├── response.py           #统一响应封装
        └── validators.py
```

### Frontend: Vue3 + Pinia + Vue Router

```
src/
├── main.js                       # createApp — Factory Pattern
├── App.vue
├── router/index.js               # Blueprint equivalent
├── stores/                       # Observer Pattern (Pinia)
│   ├── auth.js
│   ├── courses.js
│   └── selection.js
├── api/                          # Singleton + Template Method
│   ├── request.js                # Axios singleton + interceptors
│   ├── auth.js
│   ├── courses.js
│   ├── selection.js
│   ├── chat.js
│   └── recommendations.js
├── views/
│   ├── LoginView.vue
│   ├── CatalogView.vue
│   ├── ProfileView.vue
│   └── NotFoundView.vue
├── components/
│   ├── AppHeader.vue
│   ├── CourseCard.vue
│   ├── CourseModal.vue
│   ├── CartSummary.vue
│   └── Sidebar.vue
├── composables/
│   ├── useConflict.js
│   └── useDarkMode.js
└── assets/styles.css
```

## Design Patterns

### 1. Singleton Pattern

**Backend — Config Singleton (`app/config.py`)**
- Single `Config` class instance loaded from `.env` via `python-dotenv`
- Accessed globally as `current_app.config` or via `config` module-level instance

**Backend — DB Singleton (`app/extensions.py`)**
- `db = SQLAlchemy()` created once, initialized in `create_app()` via `db.init_app(app)`
- Global single connection pool

**Frontend — Axios Instance (`api/request.js`)**
- Single `axios.create()` instance with base URL, interceptors
- Exported and reused by all API modules

**Frontend — Pinia Stores**
- Each store (`useAuthStore`, `useCourseStore`, `useSelectionStore`) is a singleton by Pinia's design

### 2. Factory Pattern

**Backend — `create_app()` (`app/__init__.py`)**
```python
def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    register_extensions(app)
    register_blueprints(app)
    register_error_handlers(app)
    return app
```

**Frontend — `createApp()` (`main.js`)**
- Factory for Vue app with router, Pinia, component registration

### 3. MVC Pattern

**Backend MVC:**
- **Model**: SQLAlchemy models (`models/`) — data structure + relationships
- **View**: JSON responses via `utils/response.py` — presentation layer
- **Controller**: Blueprints (`blueprints/`) — route handling, delegates to services

**Frontend MVC:**
- **Model**: Pinia stores (`stores/`) — reactive data state
- **View**: Vue templates (`views/`, `components/`) — UI rendering
- **Controller**: Store actions + event handlers — business logic + API calls

### 4. Blueprint Pattern (Backend)

Each module gets its own Blueprint:
- `auth_bp` — `/api/auth/*` (register, login, me)
- `courses_bp` — `/api/courses/*` (list, detail)
- `selection_bp` — `/api/selection/*` (enroll, drop, list)
- `profile_bp` — `/api/profile/*` (update profile)
- `recommendations_bp` — `/api/recommendations/*`
- `chat_bp` — `/api/chat/*`

All registered with `/api` prefix in `create_app()`.

### 5. Observer Pattern (Frontend)

- Pinia stores hold reactive state
- Components subscribe via `storeToRefs()` or direct store access
- When store actions mutate state, all subscribed components re-render automatically
- Example: `useSelectionStore().addCourse()` → CartSummary, CatalogView, Sidebar all update

### 6. Template Method Pattern

**Backend — Unified Response (`utils/response.py`)**
```python
class ApiResponse:
    @staticmethod
    def success(data=None, message='success'):
        return jsonify({'code': 200, 'message': message, 'data': data})

    @staticmethod
    def error(message='error', code=400):
        return jsonify({'code': code, 'message': message, 'data': None}), code
```

**Backend — Base CRUD Service**
- Common query patterns extracted to base service methods

**Frontend — Axios Interceptors (`api/request.js`)**
- Request interceptor: auto-attach token
- Response interceptor: unwrap `data`, handle 401 redirect, extract error messages
- All API modules follow same call pattern

### 7. Proxy Pattern

**Backend — Auth Decorator (`decorators/auth.py`)**
```python
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        user = verify_token(token)
        if not user:
            return ApiResponse.error('Unauthorized', 401)
        g.current_user = user
        return f(*args, **kwargs)
    return decorated
```

**Frontend — Axios Request Interceptor**
- Proxies every request to inject auth token
- Proxies every response to handle errors uniformly

### 8. Strategy Pattern (Backend)

**Enrollment Strategies (`services/selection_service.py`)**
```python
class EnrollmentStrategy(ABC):
    @abstractmethod
    def validate(self, user, course, existing): ...
    @abstractmethod
    def execute(self, user, course, db): ...

class MajorCourseStrategy(EnrollmentStrategy): ...
class ElectiveCourseStrategy(EnrollmentStrategy): ...
class GeneralCourseStrategy(EnrollmentStrategy): ...

class SelectionService:
    _strategies = {
        '专业课': MajorCourseStrategy(),
        '公共课': GeneralCourseStrategy(),
    }
    def enroll(self, user, course_ids, db):
        strategy = self._strategies.get(course.course_type, ElectiveCourseStrategy())
        strategy.validate(user, course, existing)
        strategy.execute(user, course, db)
```

### 9. Decorator Pattern (Backend)

**Request Logging (`decorators/logging.py`)**
```python
def log_request(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        logger.info(f"{request.method} {request.path}")
        start = time.time()
        result = f(*args, **kwargs)
        logger.info(f"Completed in {time.time()-start:.3f}s")
        return result
    return decorated
```

## API Endpoints (Preserved)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /api/auth/register | No | Register |
| POST | /api/auth/login | No | Login |
| GET | /api/auth/me | Yes | Current user |
| POST | /api/profile/ | Yes | Update profile |
| GET | /api/courses/ | No | List courses |
| GET | /api/courses/<id> | No | Course detail |
| POST | /api/selection/ | Yes | Enroll |
| DELETE | /api/selection/<id> | Yes | Drop course |
| GET | /api/selection/ | Yes | List selections |
| POST | /api/recommendations/ | Yes | Get recommendations |
| POST | /api/chat/ | Yes | AI chat |
| GET | /health | No | Health check |

## Frontend Routes

| Path | View | Auth |
|------|------|------|
| /login | LoginView | No |
| / | CatalogView | Yes |
| /profile | ProfileView | Yes |
| /:pathMatch(.*)* | NotFoundView | No |

## Database Models (Preserved)

- `User`: id, username, password_hash, major, grade, interests, created_at
- `Course`: id, code, title, faculty, course_type, instructor, level, credits, summary, objectives, difficulty, schedule_display, schedule_json, keywords, created_at
- `Selection`: id, user_id (FK), course_id (FK), created_at — unique(user_id, course_id)
- `UserHistory`: id, user_id (FK), event_type, payload (JSON), created_at

## Dependencies

**Backend (Flask):**
- flask, flask-sqlalchemy, flask-cors
- python-dotenv, passlib[bcrypt], python-jose[cryptography]
- requests (MiMo API), pymysql (optional MySQL)

**Frontend:**
- vue 3, vue-router 4, pinia, axios
- @vitejs/plugin-vue, vite

## Migration from FastAPI

Key changes:
1. FastAPI `Depends()` → Flask decorators + `g` object
2. Pydantic schemas → Marshmallow or manual dict serialization
3. FastAPI `APIRouter` → Flask `Blueprint`
4. FastAPI `HTTPException` → Flask `abort()` or `ApiResponse.error()`
5. Uvicorn → Flask dev server (or gunicorn for production)
6. Async endpoints → Sync (Flask default)
