"""
3D 预览服务 - 将 CATIA/STEP 文件转换为 glTF 格式供前端查看

转换优先级：
1. FreeCAD CLI（支持 CATIA 原始格式 .CATPart/.CATProduct）
2. trimesh 库（支持 STL/STEP/OBJ 等通用格式）

转换在零件检入时异步触发，失败不影响检入流程。
"""
import logging
import os
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

# 预览文件存储目录
PREVIEW_DIR = Path(__file__).parent.parent.parent / "storage" / "previews"


async def convert_to_gltf(source_path: str, part_id: str) -> str | None:
    """将 CATIA/STEP 文件转换为 glTF 格式（.glb），返回输出路径或 None

    转换策略：
    1. 已有缓存直接返回
    2. 尝试 FreeCAD CLI（对 CATIA 格式支持最好）
    3. 降级到 trimesh（Python 库，支持 STL/STEP 等格式）
    """
    output_dir = PREVIEW_DIR / str(part_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "model.glb"

    # 已有预览文件则直接返回（缓存）
    if output_path.exists():
        return str(output_path)

    source = Path(source_path)
    if not source.exists():
        logger.warning(f"源文件不存在，无法生成预览: {source_path}")
        return None

    ext = source.suffix.lower()
    logger.info(f"开始生成 3D 预览: {source_path} (格式: {ext})")

    # 优先尝试 FreeCAD CLI 转换（对 CATIA 格式支持最好）
    try:
        result = subprocess.run(
            [
                "freecad-cli",
                "--console",
                "--run-script",
                f"""
import ImportGui
ImportGui.insert("{source_path}", "Unnamed")
import Mesh
objs = App.ActiveDocument.Objects
Mesh.export(objs, "{output_path}")
""",
            ],
            capture_output=True, timeout=60,
        )
        if output_path.exists():
            logger.info(f"FreeCAD 转换成功: {output_path}")
            return str(output_path)
        else:
            logger.debug(f"FreeCAD 转换未生成输出文件，stderr: {result.stderr.decode()[:200]}")
    except FileNotFoundError:
        logger.debug("FreeCAD CLI 未安装，跳过")
    except subprocess.TimeoutExpired:
        logger.warning("FreeCAD 转换超时（60秒）")

    # 降级尝试 trimesh（Python 库，支持 STL/OBJ/STEP 等格式）
    try:
        import trimesh
        scene = trimesh.load(source_path, force=None)
        # trimesh.load 可能返回 Scene 或 Trimesh
        if hasattr(scene, 'export'):
            scene.export(str(output_path), file_type='glb')
            if output_path.exists():
                logger.info(f"trimesh 转换成功: {output_path}")
                return str(output_path)
        elif hasattr(scene, 'dump'):
            scene.dump(str(output_path))
            if output_path.exists():
                logger.info(f"trimesh dump 成功: {output_path}")
                return str(output_path)
        else:
            logger.warning(f"trimesh 无法处理该格式: {ext}, 返回类型: {type(scene)}")
    except ImportError:
        logger.warning("trimesh 未安装，无法转换 3D 文件")
    except Exception as e:
        logger.warning(f"trimesh 转换失败: {e}")

    logger.info(f"所有转换方式均失败，该文件格式暂不支持预览: {ext}")
    return None


def get_preview_path(part_id: str) -> str | None:
    """获取零件的 3D 预览文件路径，不存在则返回 None"""
    path = PREVIEW_DIR / str(part_id) / "model.glb"
    if path.exists():
        return str(path)
    return None
