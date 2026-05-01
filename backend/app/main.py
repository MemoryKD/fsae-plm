from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import auth, users, parts, versions, templates, workflows, bom


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="FSAE-PLM", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(users.router, prefix="/api/users", tags=["用户管理"])
app.include_router(parts.router, prefix="/api/parts", tags=["零件管理"])
app.include_router(versions.router, prefix="/api/parts", tags=["版本管理"])
app.include_router(templates.router, prefix="/api/templates", tags=["编号规则"])
app.include_router(workflows.router, prefix="/api/workflows", tags=["工作流"])
app.include_router(bom.router, prefix="/api/parts", tags=["BOM管理"])


@app.get("/api/health")
async def health():
    return {"status": "ok"}
