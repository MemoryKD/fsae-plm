"""
FSAE-PLM 应用入口 - FastAPI 应用工厂

职责：
- 创建 FastAPI 应用实例并配置生命周期（启动时初始化数据库）
- 注册 CORS 中间件
- 挂载所有业务路由模块
- 提供健康检查端点
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import auth, users, parts, versions, templates, workflows, bom, change_notices, knowledge, roles


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动时初始化数据库和种子数据"""
    await init_db()
    yield


app = FastAPI(title="FSAE-PLM", version="1.0.0", lifespan=lifespan)

# CORS 中间件：允许所有来源（开发阶段配置，生产环境应限制）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册业务路由，prefix 统一以 /api 开头
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(users.router, prefix="/api/users", tags=["用户管理"])
app.include_router(parts.router, prefix="/api/parts", tags=["零件管理"])
app.include_router(versions.router, prefix="/api/parts", tags=["版本管理"])
app.include_router(templates.router, prefix="/api/templates", tags=["编号规则"])
app.include_router(workflows.router, prefix="/api/workflows", tags=["工作流"])
app.include_router(bom.router, prefix="/api/parts", tags=["BOM管理"])
app.include_router(change_notices.router, prefix="/api/change-notices", tags=["更改通告"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["知识库"])
app.include_router(roles.router, prefix="/api/roles", tags=["角色管理"])


@app.get("/api/health")
async def health():
    """健康检查端点，用于容器探针和负载均衡器"""
    return {"status": "ok"}
