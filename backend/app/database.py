"""
数据库配置与初始化模块

负责：
- 异步数据库引擎和会话工厂的创建（单例模式）
- SQLAlchemy ORM Base 声明
- 数据库迁移（通过 ALTER TABLE 增量添加新列）
- 预置角色数据的种子初始化
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# 全局单例：数据库引擎和会话工厂（延迟初始化）
engine = None
async_session = None


def get_engine():
    """获取或创建异步数据库引擎（单例）"""
    global engine
    if engine is None:
        engine = create_async_engine(settings.DATABASE_URL, echo=False)
    return engine


def get_session_factory():
    """获取或创建异步会话工厂（单例），expire_on_commit=False 允许提交后继续访问对象属性"""
    global async_session
    if async_session is None:
        async_session = async_sessionmaker(get_engine(), class_=AsyncSession, expire_on_commit=False)
    return async_session


class Base(DeclarativeBase):
    """所有 ORM 模型的基类"""
    pass


async def get_db():
    """FastAPI 依赖注入函数，提供数据库会话（自动提交/回滚）"""
    session_factory = get_session_factory()
    async with session_factory() as session:
        yield session


async def init_db():
    """数据库初始化：运行增量迁移 + 建表 + 种子数据

    迁移策略：每条 ALTER TABLE 在独立事务中执行，
    已存在的列会导致异常被捕获忽略（幂等）。
    """
    # 增量迁移：为已有表添加新列（失败说明列已存在，安全忽略）
    for sql in [
        "ALTER TABLE users ADD COLUMN role_id VARCHAR(36)",
        "ALTER TABLE part_number_templates ADD COLUMN type_codes JSONB DEFAULT '{}'",
        "ALTER TABLE parts ADD COLUMN derived_from_id VARCHAR(36)",
        "ALTER TABLE parts ADD COLUMN branch_name VARCHAR(100)",
        "ALTER TABLE parts ADD COLUMN branch_created_at TIMESTAMP",
        "ALTER TABLE users ADD COLUMN full_name VARCHAR(100)",
        "ALTER TABLE users ADD COLUMN department VARCHAR(100)",
        "ALTER TABLE users ADD COLUMN join_year VARCHAR(4)",
        "ALTER TABLE users ADD COLUMN phone VARCHAR(20)",
        "ALTER TABLE users ADD COLUMN status VARCHAR(20) DEFAULT 'approved'",
        "ALTER TABLE versions ADD COLUMN file_hash VARCHAR(64)",
    ]:
        try:
            async with get_engine().begin() as conn:
                await conn.execute(__import__("sqlalchemy").text(sql))
        except Exception:
            pass  # 列已存在，跳过

    # 创建所有新表（已存在的表会跳过）
    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # 初始化预置角色数据
    await _seed_roles()


async def _seed_roles():
    """种子数据初始化：创建预置角色，并将已有用户迁移到对应角色"""
    from sqlalchemy import select
    from app.models.role import Role, DEFAULT_ROLES

    session_factory = get_session_factory()
    async with session_factory() as db:
        # 如果角色表已有数据，说明已初始化过，跳过
        result = await db.execute(select(Role).limit(1))
        if result.scalar_one_or_none() is not None:
            return

        # 创建预置角色
        roles = []
        for rd in DEFAULT_ROLES:
            role = Role(**rd)
            db.add(role)
            roles.append(role)
        await db.commit()

        # 将已有用户（role_id 为空）映射到对应角色
        from app.models.user import User
        roles_map = {r.name: r.id for r in roles}
        users_result = await db.execute(select(User).where(User.role_id.is_(None)))
        for user in users_result.scalars().all():
            # 按旧 role 字段匹配，未匹配到的默认分配 designer 角色
            user.role_id = roles_map.get(user.role, roles_map["designer"])
        await db.commit()
