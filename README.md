# FSAE-PLM

大学生方程式赛车队简易 PLM（产品生命周期管理）系统。

解决 CATIA 零件文件命名混乱、版本丢失、文件分散等问题，提供集中存储、自动编号、版本管理、BOM 管理和分支追踪功能。

## v1.4.0 更新（CATIA 内嵌版）

- **CATIA 内嵌客户端**：通过 C# COM DLL + VBS 宏将 PLM 功能嵌入 CATIA 工具栏，用户无需切换窗口
- **8 个工具栏按钮**：登录、搜索零件、检出、检入、发布、同步属性、新建零件、自动启动检查
- **CATIA 连接检测**：启动时自动检测 CATIA 进程、COM 连接、宏安装状态
- **独立测试程序**：可脱离 CATIA 独立运行测试 WinForms 界面和 API 通信

## v1.3.0 更新

- **CATIA 连接状态**：客户端底部实时显示 CATIA 连接状态（绿灯/红灯），支持一键重连，连接失败显示详细错误信息
- **新建零件流程优化**：创建零件后自动弹出文件选择器，用户可直接将 CATIA 文件导入系统
- **检入/检出文件校验**：后端增加 4 层校验（扩展名白名单、文件类型一致性、SHA-256 哈希、重复文件检测）
- **C# 客户端健壮性**：修复注册密码未传递、创建零件 Content-Type 不匹配、按钮 CanExecute 不刷新等多个 bug
- **3D 预览改进**：支持 trimesh 转换，新增手动触发预览生成端点，HEAD 请求兼容
- **角色管理修复**：修复修改用户角色 500 错误，改用 `.get()` 安全取值

## 功能概览

| 模块 | 功能 |
|------|------|
| 用户认证 | JWT 登录注册，注册需管理员审批，角色权限（管理员/组长/设计师/查看者） |
| 零件管理 | 创建、搜索、删除零件，缩略图预览，3D 模型在线预览 |
| 版本管理 | 检入/检出工作流，版本自动递增（A.1→A.2→B.1），文件校验（扩展名/类型/哈希） |
| 生命周期 | 工作中（检入/检出）↔ 已发布，取消发布需更改通告 |
| 分支追踪 | 零件分支/派生，谱系追溯，支持从已有零件创建分支 |
| 编号规则 | 可配置编号模板（如 `FS-SUS-001`），子系统/类型代码字典，拖拽排序，自动生成零件号 |
| 工作流引擎 | 可配置状态流转，审批历史 |
| BOM 管理 | 装配体-零件关系、级联检入/检出、Excel 导出、整包下载（ZIP） |
| 更改通告 | 已发布零件变更需创建更改通告（ECN），审批流程 |
| 知识库 | 分类管理技术文档，支持文件附件上传下载 |
| 角色权限 | 16 项细粒度权限，4 种默认角色，自定义角色 |
| CATIA 客户端 | C# WPF 客户端（推荐），CATIA 连接状态监控，检入/检出文件管理，属性同步 |

## 技术栈

- **后端**: FastAPI + SQLAlchemy (async) + PostgreSQL + Redis
- **前端**: Vue 3 + Element Plus + Pinia + Three.js
- **CATIA 客户端**: C# WPF (.NET 8) / Python + ttkbootstrap + pywin32 COM
- **部署**: Docker Compose (Nginx + Backend + Frontend + PostgreSQL + Redis)

## 项目结构

```
fsae-plm/
├── backend/                        # FastAPI 后端
│   ├── app/
│   │   ├── models/                 # SQLAlchemy 数据模型
│   │   │   ├── part.py             # 零件模型（含生命周期、检入检出、分支）
│   │   │   ├── version.py          # 版本模型
│   │   │   ├── change_notice.py    # 更改通告模型
│   │   │   ├── template.py         # 编号模板
│   │   │   ├── user.py             # 用户模型（含审批状态）
│   │   │   ├── bom.py              # BOM 模型
│   │   │   ├── role.py             # 角色权限模型
│   │   │   ├── workflow.py         # 工作流模型
│   │   │   └── knowledge.py        # 知识库模型
│   │   ├── routers/                # API 路由（10 个模块）
│   │   ├── schemas/                # Pydantic 请求/响应模型
│   │   ├── services/               # 业务逻辑
│   │   └── utils/                  # 工具（JWT、文件存储、类型适配）
│   ├── tests/                      # 测试
│   └── Dockerfile
├── frontend/                       # Vue 3 前端
│   ├── src/
│   │   ├── views/                  # 页面（10 个）
│   │   ├── components/             # 组件（Layout、ModelViewer）
│   │   ├── stores/                 # Pinia 状态管理
│   │   ├── api/                    # Axios HTTP 客户端
│   │   └── router/                 # Vue Router
│   └── Dockerfile
├── catia_addin/                    # CATIA 内嵌版客户端（C# COM + VBS 宏）
│   ├── FSAE_PLM.csproj             # .NET 8 COM DLL 项目
│   ├── PlmBridge.cs                # COM 入口（VBS 通过 CreateObject 调用）
│   ├── Services/PlmApiService.cs   # 17 个同步 API 方法
│   ├── Models/PartInfo.cs          # COM 可见数据模型
│   ├── Forms/                      # WinForms 对话框（登录/列表/详情/新建）
│   ├── macros/                     # 8 个 VBS 宏脚本（安装到 CATIA）
│   ├── deploy.bat                  # 一键构建+注册+安装
│   └── register_com.ps1            # COM 注册脚本
├── catia_client_cs/                # C# WPF CATIA 客户端（独立窗口版）
│   └── CatiaClient/
│       ├── Models/                 # 数据模型
│       ├── Services/               # ApiClient + CatiaService
│       ├── ViewModels/             # MVVM ViewModel 层
│       └── Views/                  # XAML 视图
├── catia_client/                   # Python CATIA 客户端（旧版）
├── nginx/nginx.conf                # Nginx 反向代理配置
├── docker-compose.yml              # Docker 部署
└── docs/
    └── TUTORIAL.md                 # 详细使用教程
```

## 快速开始

### Docker 部署（推荐）

```bash
git clone https://github.com/MemoryKD/fsae-plm.git
cd fsae-plm
docker-compose up -d
```

启动后访问：
- 前端页面：http://localhost
- API 文档：http://localhost/api/docs

默认管理员账号：`admin` / `admin123`

### 本地开发

**后端：**

```bash
cd backend
pip install -r requirements.txt
echo "DATABASE_URL=sqlite+aiosqlite:///./fsae_plm.db" > .env
echo "SECRET_KEY=your-secret-key" >> .env
uvicorn app.main:app --reload --port 8000
```

**前端：**

```bash
cd frontend
npm install
npm run dev
```

**C# CATIA 客户端（独立窗口版）：**

```bash
cd catia_client_cs/CatiaClient
dotnet build
# 或在 Visual Studio 中打开 CatiaClient.sln
```

**CATIA 内嵌版客户端（推荐）：**

```bash
cd catia_addin
dotnet build FSAE_PLM.csproj -c Release
# 以管理员身份运行 register_com.ps1 注册 COM
# 将 macros/*.catvbs 复制到 CATIA 宏目录
```

或直接运行 `deploy.bat`（需管理员权限）。

需要 .NET 8.0 SDK 和 Windows 系统。

### 运行测试

```bash
cd backend
pip install -r requirements.txt aiosqlite
pytest tests/ -v
```

## 用户注册与审批

新用户注册后状态为"待审批"，需要管理员在网页端「待审批用户」页面批准后才能登录。

注册信息包含：用户名、密码、姓名、部门、加入年份、联系电话。

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

## 分支与谱系

零件支持分支/派生功能：

- 从已有零件创建分支，自动生成新零件号
- 分支继承源零件的初始版本
- 支持查看零件谱系（从当前零件追溯到根零件）
- 支持查看零件的所有分支

## API 端点

```
# 认证
POST   /api/auth/register               # 注册（需审批）
POST   /api/auth/login                   # 登录
GET    /api/auth/me                      # 当前用户信息
GET    /api/auth/pending-users           # 待审批用户列表（管理员）
POST   /api/auth/approve/{id}            # 批准用户（管理员）
POST   /api/auth/reject/{id}             # 拒绝用户（管理员）

# 零件
GET    /api/parts/                       # 零件列表（支持 ?search=）
POST   /api/parts/                       # 创建零件
GET    /api/parts/{id}                   # 零件详情
DELETE /api/parts/{id}                   # 删除零件
POST   /api/parts/create-with-template   # 使用模板创建零件

# 检入/检出/发布
POST   /api/parts/{id}/checkout          # 检出
POST   /api/parts/{id}/checkin           # 检入（multipart: file + comment）
POST   /api/parts/{id}/publish           # 发布
POST   /api/parts/{id}/unpublish         # 取消发布（需 change_notice_id）

# 文件
GET    /api/parts/{id}/download          # 下载最新版本文件
GET    /api/parts/{id}/thumbnail         # 获取缩略图
POST   /api/parts/{id}/thumbnail         # 上传缩略图
GET    /api/parts/{id}/preview           # 3D 预览（glTF）
GET    /api/parts/{id}/download-all      # 下载装配体所有文件（ZIP）

# 分支
POST   /api/parts/{id}/branch            # 创建分支
GET    /api/parts/{id}/branches          # 获取分支列表
GET    /api/parts/{id}/lineage           # 获取谱系

# 版本
GET    /api/parts/{id}/versions          # 版本列表
GET    /api/parts/{id}/versions/{vid}/download  # 下载指定版本

# BOM
GET    /api/parts/{id}/bom               # 获取 BOM
POST   /api/parts/{id}/bom               # 添加 BOM 项
DELETE /api/parts/{id}/bom/{bid}         # 删除 BOM 项
GET    /api/parts/{id}/bom/export        # 导出 Excel

# 编号
GET    /api/parts/next-number            # 获取下一个可用零件号

# 更改通告
GET    /api/change-notices/              # 通告列表
POST   /api/change-notices/              # 创建通告
POST   /api/change-notices/{id}/approve  # 审批通告

# 编号模板
GET    /api/templates/                   # 模板列表
POST   /api/templates/                   # 创建模板
PUT    /api/templates/{id}               # 更新模板
DELETE /api/templates/{id}               # 删除模板

# 知识库
GET    /api/knowledge/categories         # 分类列表
POST   /api/knowledge/categories         # 创建分类
GET    /api/knowledge/articles           # 文章列表
POST   /api/knowledge/articles           # 创建文章
GET    /api/knowledge/articles/{id}      # 文章详情
PUT    /api/knowledge/articles/{id}      # 更新文章
DELETE /api/knowledge/articles/{id}      # 删除文章
POST   /api/knowledge/articles/{id}/attachments  # 上传附件
GET    /api/knowledge/attachments/{id}/download   # 下载附件

# 角色管理
GET    /api/roles/                       # 角色列表
POST   /api/roles/                       # 创建角色
PUT    /api/roles/{id}                   # 更新角色
DELETE /api/roles/{id}                   # 删除角色

# 用户管理
GET    /api/users/                       # 用户列表
PUT    /api/users/{id}/role              # 修改用户角色

# 工作流
GET    /api/workflows/                   # 工作流模板列表
POST   /api/workflows/                   # 创建工作流模板
POST   /api/workflows/{id}/transition    # 执行状态流转
```

## 配置

通过环境变量或 `.env` 文件配置：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/fsae_plm` | 数据库连接 |
| `SECRET_KEY` | `change-this-to-a-random-string` | JWT 密钥 |
| `STORAGE_TYPE` | `local` | 文件存储类型 (local/minio) |
| `LOCAL_STORAGE_PATH` | `./storage` | 本地文件存储路径 |

## 权限系统

系统内置 16 项细粒度权限和 4 种默认角色：

| 角色 | 说明 | 主要权限 |
|------|------|---------|
| `admin` | 管理员 | 全部权限 |
| `manager` | 组长 | 零件管理、审批更改通告、用户管理 |
| `designer` | 设计师 | 创建/编辑零件、检入/检出、上传版本 |
| `viewer` | 查看者 | 只读查看零件和 BOM |

可在网页端「角色管理」页面自定义角色和权限。

## 许可证

MIT
