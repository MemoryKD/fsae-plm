"""FSAE-PLM CATIA 客户端主窗口"""
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox

from api_client import PLMClient
from catia_bridge import CATIABridge
from config import load_config, save_config
from gui.login_frame import LoginFrame
from gui.parts_frame import PartsFrame
from gui.part_detail import PartDetailDialog
from gui.upload_dialog import UploadDialog


class App(ttk.Window):
    def __init__(self):
        super().__init__(title="FSAE-PLM CATIA 客户端", themename="cosmo",
                         size=(1200, 800))
        self.api = None
        self.catia = CATIABridge()
        self.config_data = load_config()

        self._try_connect_catia()
        self._show_login()

    def _try_connect_catia(self):
        """尝试连接 CATIA"""
        if self.catia.connect():
            self.title("FSAE-PLM CATIA 客户端 [CATIA 已连接]")
        else:
            self.title("FSAE-PLM CATIA 客户端 [CATIA 未连接]")

    def _show_login(self):
        """显示登录界面"""
        for w in self.winfo_children():
            w.destroy()

        self.login_frame = LoginFrame(self, on_login=self._do_login)
        self.login_frame.pack(fill=BOTH, expand=True)

        # 恢复记住的用户名
        if self.config_data.get("username"):
            self.login_frame.entry_username.insert(0, self.config_data["username"])
        if self.config_data.get("server_url"):
            self.login_frame.entry_server.delete(0, END)
            self.login_frame.entry_server.insert(0, self.config_data["server_url"])

    def _do_login(self, server: str, username: str, password: str, remember: bool):
        """执行登录"""
        try:
            self.api = PLMClient(server)
            self.api.login(username, password)

            if remember:
                self.config_data["server_url"] = server
                self.config_data["username"] = username
                save_config(self.config_data)

            self._show_main()
        except Exception as e:
            self.login_frame.set_status(f"登录失败: {e}")
            self.login_frame.set_button_state(NORMAL)

    def _show_main(self):
        """显示主界面"""
        for w in self.winfo_children():
            w.destroy()

        self.parts_frame = PartsFrame(
            self, api_client=self.api, on_part_click=self._show_part_detail
        )
        self.parts_frame._on_new_part = self._show_upload_dialog
        self.parts_frame._on_catia_action = self._show_catia_action
        # 更新按钮命令（覆盖 _build_ui 中绑定的空方法）
        self.parts_frame.btn_upload.config(command=self._show_upload_dialog)
        self.parts_frame.btn_catia.config(command=self._show_catia_action)
        self.parts_frame.pack(fill=BOTH, expand=True)
        self.parts_frame.refresh()

    def _show_part_detail(self, part_data: dict):
        """显示零件详情"""
        PartDetailDialog(self, self.api, part_data)
        # 关闭详情后刷新列表
        self.parts_frame.refresh()

    def _show_upload_dialog(self):
        """显示上传对话框"""
        UploadDialog(self, self.api, self.catia)
        self.parts_frame.refresh()

    def _show_catia_action(self):
        """CATIA 操作菜单"""
        if not self.catia.connected:
            messagebox.showwarning("CATIA", "CATIA 未连接，请先启动 CATIA V5")
            return

        doc = self.catia.get_active_document()
        if not doc:
            messagebox.showinfo("CATIA", "请在 CATIA 中打开一个零件文件")
            return

        # 弹出操作选择
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="从 CATIA 创建零件", command=self._catia_create_part)
        menu.add_command(label="检入当前文件", command=self._catia_checkin)
        menu.add_command(label="查看零件信息", command=lambda: messagebox.showinfo(
            "CATIA 零件信息",
            f"文件: {doc.get('name', '-')}\n"
            f"零件号: {doc.get('part_number', '-')}\n"
            f"版本: {doc.get('plm_version', '-')}\n"
            f"状态: {doc.get('plm_state', '-')}\n"
            f"名称: {doc.get('plm_name', '-')}"
        ))
        try:
            menu.tk_popup(self.winfo_pointerx(), self.winfo_pointery())
        finally:
            menu.grab_release()

    def _catia_create_part(self):
        """从 CATIA 创建零件"""
        UploadDialog(self, self.api, self.catia)
        self.parts_frame.refresh()

    def _catia_checkin(self):
        """从 CATIA 检入"""
        doc = self.catia.get_active_document()
        if not doc or not doc.get("part_number"):
            messagebox.showwarning("CATIA", "当前文件没有 PLM 零件号属性，请先创建零件")
            return

        try:
            result = self.api.check_part_number(doc["part_number"])
            if not result.get("exists"):
                messagebox.showwarning("PLM", f"零件号 {doc['part_number']} 不存在，请先创建")
                return

            part = result["part"]
            if part.get("check_state") != "检出":
                messagebox.showinfo("PLM", "该零件未检出，无法检入")
                return

            # 保存临时文件并检入
            temp_path = self.catia.get_temp_save_path(doc["part_number"])
            if self.catia.save_document_copy(temp_path):
                self.api.checkin(part["id"], temp_path, "从 CATIA 客户端检入")
                self.catia.sync_plm_properties(temp_path, self.api.get_part(part["id"]))
                messagebox.showinfo("成功", f"零件 {doc['part_number']} 检入成功")
                self.parts_frame.refresh()
        except Exception as e:
            messagebox.showerror("错误", f"检入失败: {e}")
