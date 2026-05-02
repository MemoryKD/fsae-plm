"""CATIA COM 自动化桥接模块

通过 pywin32 控制运行中的 CATIA V5 实例，
读写零件属性、截取缩略图、文件操作。
"""

import os
import tempfile
from typing import Optional


class CATIABridge:
    PLM_PREFIX = "PLM_"
    PLM_PROPERTIES = [
        "PLM_PartNumber", "PLM_Version", "PLM_State", "PLM_Name",
    ]

    def __init__(self):
        self.catia = None

    def connect(self) -> bool:
        """连接到运行中的 CATIA 实例"""
        try:
            import win32com.client
            self.catia = win32com.client.Dispatch("CATIA.Application")
            self.catia.Visible = True
            return True
        except Exception as e:
            print(f"无法连接 CATIA: {e}")
            self.catia = None
            return False

    @property
    def connected(self) -> bool:
        return self.catia is not None

    def get_active_document(self) -> Optional[dict]:
        """获取当前活动文档信息"""
        if not self.connected:
            return None
        try:
            doc = self.catia.ActiveDocument
            doc_type = type(doc).__name__
            result = {
                "type": doc_type,
                "name": doc.Name,
                "path": doc.FullName if hasattr(doc, "FullName") else "",
            }
            # 读取用户自定义属性
            props = self._read_user_properties(doc)
            result["part_number"] = props.get("PLM_PartNumber", "")
            result["plm_version"] = props.get("PLM_Version", "")
            result["plm_state"] = props.get("PLM_State", "")
            result["plm_name"] = props.get("PLM_Name", "")
            # Also read from Product built-in properties
            try:
                product = doc.Product
                if not result["part_number"]:
                    result["part_number"] = getattr(product, "PartNumber", "")
                if not result["plm_version"]:
                    result["plm_version"] = getattr(product, "Revision", "")
                if not result["plm_name"]:
                    result["plm_name"] = getattr(product, "Nomenclature", "")
                result["definition"] = getattr(product, "Definition", "")
            except Exception:
                pass
            return result
        except Exception as e:
            print(f"获取活动文档失败: {e}")
            return None

    def _read_user_properties(self, doc) -> dict:
        """读取文档的用户自定义属性"""
        props = {}
        try:
            user_props = doc.UserProperties
            for i in range(1, user_props.Count + 1):
                prop = user_props.Item(i)
                name = prop.Name
                if name.startswith(self.PLM_PREFIX):
                    try:
                        props[name] = prop.Value
                    except Exception:
                        props[name] = str(prop)
        except Exception:
            pass
        return props

    def set_custom_properties(self, doc_path: str, properties: dict):
        """写入 CATIA 文件自定义属性"""
        if not self.connected:
            return False
        try:
            doc = self.catia.Documents.Open(doc_path)
            user_props = doc.UserProperties
            for name, value in properties.items():
                try:
                    # 尝试更新已有属性
                    prop = user_props.Item(name)
                    prop.Value = value
                except Exception:
                    # 创建新属性
                    try:
                        user_props.CreateReal(name, float(value))
                    except (ValueError, TypeError):
                        try:
                            user_props.CreateString(name, str(value))
                        except Exception:
                            pass
            doc.Save()
            return True
        except Exception as e:
            print(f"写入属性失败: {e}")
            return False

    def _set_product_properties(self, doc_path: str, part_data: dict):
        """写入 CATIA Product 对象的内置属性（基本信息）"""
        if not self.connected:
            return False
        try:
            doc = self.catia.Documents.Open(doc_path)
            product = doc.Product
            product.PartNumber = part_data.get("part_number", "")
            product.Revision = part_data.get("current_version", "")
            product.Definition = part_data.get("name", "")
            product.Nomenclature = part_data.get("name", "")
            doc.Save()
            return True
        except Exception as e:
            print(f"写入 Product 属性失败: {e}")
            return False

    def sync_plm_properties(self, doc_path: str, part_data: dict):
        """同步 PLM 属性到 CATIA 文件"""
        props = {
            "PLM_PartNumber": part_data.get("part_number", ""),
            "PLM_Version": part_data.get("current_version", ""),
            "PLM_State": f"{part_data.get('lifecycle_state', '')}-{part_data.get('check_state', '')}",
            "PLM_Name": part_data.get("name", ""),
        }
        self.set_custom_properties(doc_path, props)
        self._set_product_properties(doc_path, part_data)
        return True

    def capture_thumbnail(self, output_path: str, width: int = 800, height: int = 600) -> Optional[str]:
        """截取当前 3D 视图作为缩略图"""
        if not self.connected:
            return None
        try:
            doc = self.catia.ActiveDocument
            # 获取 3D 视图窗口
            windows = self.catia.Windows
            if windows.Count == 0:
                return None
            window = windows.Item(1)
            viewer = window.ActiveViewer
            # 使用 CATIA 内置截图功能
            viewer.CaptureToFile(3, output_path)  # 3 = PNG format
            if os.path.exists(output_path):
                return output_path
            return None
        except Exception as e:
            print(f"截取缩略图失败: {e}")
            # 备选方案：使用 PrintScreen API
            try:
                return self._capture_fallback(output_path)
            except Exception:
                return None

    def _capture_fallback(self, output_path: str) -> Optional[str]:
        """备选截图方案"""
        try:
            from PIL import ImageGrab
            img = ImageGrab.grab()
            img = img.resize((400, 300))
            img.save(output_path, "PNG")
            return output_path
        except Exception:
            return None

    def save_document(self) -> bool:
        """保存当前文档"""
        if not self.connected:
            return False
        try:
            self.catia.ActiveDocument.Save()
            return True
        except Exception as e:
            print(f"保存文档失败: {e}")
            return False

    def save_document_copy(self, output_path: str) -> bool:
        """保存当前文档副本到指定路径"""
        if not self.connected:
            return False
        try:
            doc = self.catia.ActiveDocument
            # 保存为副本
            doc.SaveAs(output_path)
            return True
        except Exception as e:
            print(f"保存文档副本失败: {e}")
            return False

    def open_document(self, file_path: str) -> bool:
        """打开文件"""
        if not self.connected:
            return False
        try:
            self.catia.Documents.Open(file_path)
            return True
        except Exception as e:
            print(f"打开文件失败: {e}")
            return False

    def get_temp_save_path(self, part_number: str) -> str:
        """获取临时保存路径"""
        ext = ".CATPart"
        if self.connected:
            try:
                doc = self.catia.ActiveDocument
                doc_type = type(doc).__name__
                if "Product" in doc_type:
                    ext = ".CATProduct"
                elif "Drawing" in doc_type:
                    ext = ".CATDrawing"
            except Exception:
                pass
        temp_dir = tempfile.gettempdir()
        return os.path.join(temp_dir, f"{part_number}{ext}")
