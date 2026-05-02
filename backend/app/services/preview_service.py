"""
3D 预览服务 - 将 CATIA/STEP 文件转换为 glTF 格式供前端查看

转换优先级：
1. FreeCAD CLI（支持 CATIA 原始格式）
2. trimesh 库（支持 STEP 等通用格式）

转换在零件检入时异步触发，失败不影响检入流程。
"""
import os
import subprocess
from pathlib import Path


# 预览文件存储目录
PREVIEW_DIR = Path(__file__).parent.parent.parent / "storage" / "previews"


async def convert_to_gltf(source_path: str, part_id: str) -> str | None:
    """将 CATIA/STEP 文件转换为 glTF 格式（.glb），返回输出路径或 None"""
    output_dir = PREVIEW_DIR / str(part_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "model.glb"

    # 已有预览文件则直接返回（缓存）
    if output_path.exists():
        return str(output_path)

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
            return str(output_path)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass  # FreeCAD 未安装或超时，降级到 trimesh

    # 降级尝试 trimesh（Python 库，支持 STEP 等格式）
    try:
        import trimesh
        scene = trimesh.load(source_path)
        if hasattr(scene, 'export'):
            scene.export(str(output_path), file_type='glb')
            return str(output_path)
        elif hasattr(scene, 'dump'):
            scene.dump(str(output_path))
            return str(output_path)
    except Exception:
        pass

    return None


def get_preview_path(part_id: str) -> str | None:
    """获取零件的 3D 预览文件路径，不存在则返回 None"""
    path = PREVIEW_DIR / str(part_id) / "model.glb"
    if path.exists():
        return str(path)
    return None
