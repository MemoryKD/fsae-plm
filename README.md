# FSAE-PLM

大学生方程式赛车队简易 PLM（产品生命周期管理）系统。

解决 CATIA 零件文件命名混乱、版本丢失、文件分散等问题，提供集中存储、自动编号、版本管理和 BOM 管理功能。

## 功能概览

| 模块 | 功能 |
|------|------|
| 用户认证 | JWT 登录注册，角色权限（管理员/组长/设计师/查看者） |
| 零件管理 | 创建、搜索、分页查看零件 |
| 版本管理 | 文件上传、版本历史、版本下载 |
| 编号规则 | 可配置编号模板（如 `FS-SUS-001`），子系统代码字典 |
| 工作流引擎 | 可配置状态流转（设计中→审核中→已发布），审批历史 |
| BOM 管理 | 装配体-零件关系、Excel 导出 |
| CATIA 插件 | VBA 宏，在 CATIA 内直接保存到 PLM |

## 技术栈

- **后端**: FastAPI + SQLAlchemy + PostgreSQL
- **前端**: Vue 3 + Element Plus + Pinia
- **部署**: Docker Compose (Nginx + Backend + Frontend + PostgreSQL + Redis + MinIO)

## 项目结构

```
fsae-plm/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── models/            # SQLAlchemy 数据模型
│   │   ├── routers/           # API 路由 (auth, parts, versions, bom, workflows, templates, users)
│   │   ├── schemas/           # Pydantic 请求/响应模型
│   │   ├── services/          # 业务逻辑 (认证、编号引擎、工作流引擎等)
│   │   ├── utils/             # 工具 (JWT、文件存储、类型适配)
│   │   ├── config.py          # 配置 (环境变量)
│   │   ├── database.py        # 数据库连接
│   │   └── main.py            # FastAPI 应用入口
│   ├── tests/                 # 测试 (17 个用例)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                  # Vue 3 前端
│   ├── src/
│   │   ├── views/             # 页面 (登录、零件列表、零件详情、BOM、用户管理、模板管理)
│   │   ├── components/        # 布局组件
│   │   ├── stores/            # Pinia 状态管理
│   │   ├── api/               # Axios HTTP 客户端
│   │   └── router/            # Vue Router
│   ├── package.json
│   └── Dockerfile
├── catia_plugin/              # CATIA V5 VBA 宏插件
│   ├── FSAE_PLM_Macro.catvba
│   └── README.md
├── nginx/nginx.conf           # Nginx 反向代理配置
├── docker-compose.yml         # Docker 部署
└── docs/                      # 设计文档
```

## 快速开始

### 本地开发

**后端:**

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API 文档: http://localhost:8000/docs

**前端:**

```bash
cd frontend
npm install
npm run dev
```

访问: http://localhost:5173

### Docker 部署

```bash
docker-compose up -d
```

访问: http://localhost

### 运行测试

```bash
cd backend
pip install -r requirements.txt aiosqlite
pytest tests/ -v
```

测试使用 SQLite，无需运行 PostgreSQL。

## API 端点

```
# 认证
POST   /api/auth/register       # 注册
POST   /api/auth/login           # 登录

# 零件
GET    /api/parts/               # 零件列表 (支持 ?search=)
POST   /api/parts/               # 创建零件
GET    /api/parts/{id}           # 零件详情

# 版本
GET    /api/parts/{id}/versions/ # 版本列表
POST   /api/parts/{id}/versions/ # 上传新版本

# BOM
GET    /api/parts/{id}/bom/      # 获取 BOM
POST   /api/parts/{id}/bom/      # 添加 BOM 项
GET    /api/parts/{id}/bom/export # 导出 Excel

# 工作流
POST   /api/parts/{id}/workflow/transition  # 状态流转
GET    /api/parts/{id}/workflow/history     # 审批历史

# 编号模板 (管理员)
GET    /api/templates/           # 模板列表
POST   /api/templates/           # 创建模板
PUT    /api/templates/{id}       # 更新模板

# 用户管理 (管理员)
GET    /api/users/               # 用户列表
PUT    /api/users/{id}/role      # 修改角色
```

## 配置

通过环境变量或 `.env` 文件配置:

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/fsae_plm` | 数据库连接 |
| `SECRET_KEY` | `change-this-to-a-random-string` | JWT 密钥 |
| `STORAGE_TYPE` | `local` | 文件存储类型 (local/minio) |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis 连接 |

## CATIA 插件安装

详见 [catia_plugin/README.md](catia_plugin/README.md)。

1. 打开 CATIA V5 → 工具 → 宏 → 宏
2. 导入 `FSAE_PLM_Macro.catvba`
3. 将宏按钮添加到工具栏

## 许可证

MIT
