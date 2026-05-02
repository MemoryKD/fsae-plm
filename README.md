# FSAE-PLM

大学生方程式赛车队简易 PLM（产品生命周期管理）系统。

解决 CATIA 零件文件命名混乱、版本丢失、文件分散等问题，提供集中存储、自动编号、版本管理和 BOM 管理功能。

## 功能概览

| 模块 | 功能 |
|------|------|
| 用户认证 | JWT 登录注册，角色权限（管理员/组长/设计师/查看者） |
| 零件管理 | 创建、搜索、分页查看零件，缩略图预览 |
| 版本管理 | 检入/检出工作流，版本自动递增（A.1→A.2→B.1），文件服务器存储 |
| 生命周期 | 工作中（检入/检出）↔ 已发布，取消发布需更改通告 |
| 编号规则 | 可配置编号模板（如 `FS-SUS-001`），子系统代码字典，自动生成零件号 |
| 工作流引擎 | 可配置状态流转，审批历史 |
| BOM 管理 | 装配体-零件关系、Excel 导出 |
| CATIA 客户端 | Python 独立程序，自动识别/创建零件，属性同步，缩略图截取 |
| 更改通告 | 已发布零件变更需创建更改通告，审批流程 |

## 技术栈

- **后端**: FastAPI + SQLAlchemy + PostgreSQL（开发时可用 SQLite）
- **前端**: Vue 3 + Element Plus + Pinia
- **CATIA 客户端**: Python + ttkbootstrap + pywin32 COM
- **部署**: Docker Compose (Nginx + Backend + Frontend + PostgreSQL + Redis + MinIO)

## 项目结构

```
fsae-plm/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── models/            # SQLAlchemy 数据模型
│   │   │   ├── part.py        # 零件模型（含生命周期、检入检出状态）
│   │   │   ├── version.py     # 版本模型
│   │   │   ├── change_notice.py # 更改通告模型
│   │   │   ├── template.py    # 编号模板
│   │   │   ├── user.py        # 用户模型
│   │   │   └── bom.py         # BOM 模型
│   │   ├── routers/           # API 路由
│   │   ├── schemas/           # Pydantic 请求/响应模型
│   │   ├── services/          # 业务逻辑
│   │   │   ├── part_service.py      # 零件服务（检入/检出/发布/取消发布）
│   │   │   ├── version_service.py   # 版本引擎（A.1→A.2→B.1）
│   │   │   └── auth_service.py      # 认证服务
│   │   └── utils/             # 工具（JWT、文件存储、类型适配）
│   ├── tests/                 # 测试
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                  # Vue 3 前端
│   ├── src/
│   │   ├── views/             # 页面
│   │   ├── components/        # 布局组件
│   │   ├── stores/            # Pinia 状态管理
│   │   ├── api/               # Axios HTTP 客户端
│   │   └── router/            # Vue Router
│   ├── package.json
│   └── Dockerfile
├── catia_client/              # CATIA Python 客户端（替代 VBA 宏）
│   ├── main.py                # 入口点
│   ├── api_client.py          # PLM REST API 客户端
│   ├── catia_bridge.py        # CATIA COM 自动化桥接
│   ├── config.py              # 配置
│   ├── requirements.txt       # ttkbootstrap, requests, Pillow, pywin32
│   ├── install.bat            # 一键安装脚本
│   └── gui/
│       ├── app.py             # 主窗口
│       ├── login_frame.py     # 登录界面
│       ├── parts_frame.py     # 零件列表（搜索+缩略图卡片）
│       ├── part_detail.py     # 零件详情（检入/检出/发布/更改通告）
│       └── upload_dialog.py   # 智能上传对话框
├── catia_plugin/              # CATIA V5 VBA 宏（旧版，保留参考）
├── nginx/nginx.conf           # Nginx 反向代理配置
├── docker-compose.yml         # Docker 部署
└── docs/                      # 设计文档与使用教程
    └── TUTORIAL.md
```

## 快速开始

### 本地开发

**后端:**

```bash
cd backend
pip install -r requirements.txt
# 创建 .env 文件（可选，默认使用 SQLite）
echo "DATABASE_URL=sqlite+aiosqlite:///./fsae_plm.db" > .env
echo "SECRET_KEY=your-secret-key" >> .env
uvicorn app.main:app --reload --port 8000
```

API 文档: http://localhost:8000/docs

**前端:**

```bash
cd frontend
npm install
npm run dev
```

访问: http://localhost:3000

**CATIA 客户端:**

```bash
cd catia_client
pip install -r requirements.txt
python main.py
```

或运行 `install.bat` 一键安装依赖。

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

## 版本管理规则

```
新零件创建 → A.1
检入 → 检出 → 递增小版本: A.1 → A.2
已发布 → 取消发布（需更改通告）→ 递增大版本: A.2 → B.1
```

| 操作 | 版本变化 | 说明 |
|------|----------|------|
| 创建零件 | → A.1 | 初始版本 |
| 检入 | A.1 → A.2 | 每次检入递增小版本 |
| 发布 | 不变 | 状态变为"已发布" |
| 取消发布 | A.2 → B.1 | 需要已批准的更改通告 |

## API 端点

```
# 认证
POST   /api/auth/register               # 注册
POST   /api/auth/login                   # 登录

# 零件
GET    /api/parts/                       # 零件列表（支持 ?search=）
POST   /api/parts/                       # 创建零件
GET    /api/parts/{id}                   # 零件详情
POST   /api/parts/auto-create            # 自动创建（自动编号+上传）

# 检入/检出/发布
POST   /api/parts/{id}/checkout          # 检出
POST   /api/parts/{id}/checkin           # 检入（multipart: file + comment）
POST   /api/parts/{id}/publish           # 发布
POST   /api/parts/{id}/unpublish         # 取消发布（需 change_notice_id）

# 文件
GET    /api/parts/{id}/download          # 下载最新版本文件
GET    /api/parts/{id}/thumbnail         # 获取缩略图
POST   /api/parts/{id}/thumbnail         # 上传缩略图

# 编号
GET    /api/parts/next-number            # 获取下一个可用零件号
GET    /api/parts/check-number           # 检查零件号是否存在

# 更改通告
GET    /api/change-notices/              # 通告列表（支持 ?part_id=）
POST   /api/change-notices/              # 创建通告
POST   /api/change-notices/{id}/approve  # 审批通告

# 版本
GET    /api/parts/{id}/versions          # 版本列表

# BOM
GET    /api/parts/{id}/bom/              # 获取 BOM
POST   /api/parts/{id}/bom/              # 添加 BOM 项
GET    /api/parts/{id}/bom/export        # 导出 Excel

# 编号模板（管理员）
GET    /api/templates/                   # 模板列表
POST   /api/templates/                   # 创建模板

# 用户管理（管理员）
GET    /api/users/                       # 用户列表
PUT    /api/users/{id}/role              # 修改角色
```

## 配置

通过环境变量或 `.env` 文件配置:

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/fsae_plm` | 数据库连接 |
| `SECRET_KEY` | `change-this-to-a-random-string` | JWT 密钥 |
| `STORAGE_TYPE` | `local` | 文件存储类型 (local/minio) |
| `LOCAL_STORAGE_PATH` | `./storage` | 本地文件存储路径 |

## CATIA 客户端使用

详见 [docs/TUTORIAL.md](docs/TUTORIAL.md) 第 9 节。

1. 安装依赖：运行 `catia_client/install.bat` 或手动 `pip install -r requirements.txt`
2. 启动 CATIA V5
3. 运行 `python catia_client/main.py`
4. 登录后可浏览零件、搜索、创建新零件、检入/检出/发布

## 许可证

MIT
