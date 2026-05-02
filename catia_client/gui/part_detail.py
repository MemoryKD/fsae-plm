"""零件详情对话框"""
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from PIL import Image, ImageTk
import io


class PartDetailDialog:
    def __init__(self, parent, api_client, part_data: dict):
        self.parent = parent
        self.api = api_client
        self.part_data = part_data
        self.part_id = part_data["id"]
        self._thumbnail_ref = None

        self.win = ttk.Toplevel(parent)
        self.win.title(f"零件详情 - {part_data.get('part_number', '')}")
        self.win.geometry("600x700")
        self.win.transient(parent)
        self.win.grab_set()

        self._build_ui()
        self._load_thumbnail()
        self._load_versions()

    def _build_ui(self):
        main = ttk.Frame(self.win, padding=15)
        main.pack(fill=BOTH, expand=True)

        # 缩略图
        img_frame = ttk.Frame(main, height=150)
        img_frame.pack(fill=X, pady=(0, 10))
        img_frame.pack_propagate(False)
        self.img_label = ttk.Label(img_frame, text="加载缩略图...", anchor=CENTER)
        self.img_label.pack(fill=BOTH, expand=True)

        # 属性信息
        info = ttk.LabelFrame(main, text="基本信息")
        info.pack(fill=X, pady=5, padx=10)

        fields = [
            ("零件号", "part_number"),
            ("名称", "name"),
            ("类型", "type"),
            ("子系统", "subsystem"),
            ("当前版本", "current_version"),
            ("生命周期", "lifecycle_state"),
            ("检入/检出", "check_state"),
        ]
        self.field_labels = {}
        for label, key in fields:
            row = ttk.Frame(info)
            row.pack(fill=X, pady=2)
            ttk.Label(row, text=f"{label}:", width=12, font=("Microsoft YaHei", 10, "bold")).pack(side=LEFT)
            lbl = ttk.Label(row, text=str(self.part_data.get(key, "-")), font=("Microsoft YaHei", 10))
            lbl.pack(side=LEFT, fill=X, expand=True)
            self.field_labels[key] = lbl

        # 操作按钮
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=X, pady=10)

        lifecycle = self.part_data.get("lifecycle_state", "工作中")
        check = self.part_data.get("check_state", "检入")

        if lifecycle == "已发布":
            ttk.Button(btn_frame, text="取消发布", bootstyle=WARNING,
                       command=self._unpublish).pack(side=LEFT, padx=5)
        elif check == "检入":
            ttk.Button(btn_frame, text="检出", bootstyle=PRIMARY,
                       command=self._checkout).pack(side=LEFT, padx=5)
            ttk.Button(btn_frame, text="发布", bootstyle=SUCCESS,
                       command=self._publish).pack(side=LEFT, padx=5)
        elif check == "检出":
            ttk.Button(btn_frame, text="检入", bootstyle=INFO,
                       command=self._checkin).pack(side=LEFT, padx=5)

        ttk.Button(btn_frame, text="关闭", bootstyle=SECONDARY,
                   command=self.win.destroy).pack(side=RIGHT, padx=5)

        # 版本历史
        ver_frame = ttk.LabelFrame(main, text="版本历史")
        ver_frame.pack(fill=BOTH, expand=True, pady=5, padx=10)

        cols = ("版本号", "文件类型", "说明", "时间")
        self.ver_tree = ttk.Treeview(ver_frame, columns=cols, show="headings", height=8)
        for c in cols:
            self.ver_tree.heading(c, text=c)
            self.ver_tree.column(c, width=100)
        self.ver_tree.column("版本号", width=60)
        self.ver_tree.column("说明", width=200)
        self.ver_tree.pack(fill=BOTH, expand=True)

        # 状态消息
        self.msg_var = tk.StringVar()
        ttk.Label(main, textvariable=self.msg_var, bootstyle=INFO).pack(fill=X, pady=5)

    def _load_thumbnail(self):
        try:
            data = self.api.get_thumbnail(self.part_id)
            if data:
                img = Image.open(io.BytesIO(data))
                img = img.resize((300, 200), Image.Resampling.LANCZOS)
                self._thumbnail_ref = ImageTk.PhotoImage(img)
                self.img_label.config(image=self._thumbnail_ref, text="")
            else:
                self.img_label.config(text="无缩略图")
        except Exception:
            self.img_label.config(text="无缩略图")

    def _load_versions(self):
        try:
            versions = self.api.get_versions(self.part_id)
            for v in versions:
                self.ver_tree.insert("", END, values=(
                    v.get("version_number", ""),
                    v.get("file_type", ""),
                    v.get("comment", ""),
                    v.get("created_at", "")[:19],
                ))
        except Exception:
            pass

    def _checkout(self):
        try:
            result = self.api.checkout(self.part_id)
            self.msg_var.set("检出成功，正在下载文件...")
            self._refresh_part(result)
            # 下载文件到本地
            from tkinter import filedialog, messagebox
            save_path = filedialog.asksaveasfilename(
                title="保存文件到",
                initialfile=f"{self.part_data.get('part_number', 'file')}.{self.part_data.get('type', 'CATPart')}",
                filetypes=[("CATIA 文件", "*.CATPart *.CATProduct *.CATDrawing"), ("所有文件", "*.*")],
            )
            if save_path:
                try:
                    self.api.download_file(self.part_id, save_path)
                    self.msg_var.set(f"检出成功，文件已保存到: {save_path}")
                    if messagebox.askyesno("打开文件", "是否在 CATIA 中打开该文件？"):
                        import os
                        os.startfile(save_path)
                except Exception as e:
                    self.msg_var.set(f"检出成功，但文件下载失败: {e}")
            else:
                self.msg_var.set("检出成功（未下载文件）")
        except Exception as e:
            self.msg_var.set(f"检出失败: {e}")

    def _checkin(self):
        from tkinter import filedialog, messagebox
        # 弹出文件选择对话框
        file_path = filedialog.askopenfilename(
            title="选择检入文件",
            filetypes=[("CATIA 文件", "*.CATPart *.CATProduct *.CATDrawing"), ("所有文件", "*.*")]
        )
        if not file_path:
            return

        comment = self._ask_comment()
        try:
            result = self.api.checkin(self.part_id, file_path, comment)
            self.msg_var.set(f"检入成功，版本: {result.get('current_version', '')}")
            self._refresh_part(result)
            self._load_versions()
            # 提示是否删除本地文件
            if messagebox.askyesno("删除本地文件", "文件已成功上传到服务器。\n是否删除本地文件？"):
                import os
                try:
                    os.remove(file_path)
                    self.msg_var.set(f"检入成功，本地文件已删除")
                except Exception:
                    self.msg_var.set(f"检入成功，但本地文件删除失败")
        except Exception as e:
            self.msg_var.set(f"检入失败: {e}")

    def _publish(self):
        try:
            result = self.api.publish(self.part_id)
            self.msg_var.set("发布成功")
            self._refresh_part(result)
        except Exception as e:
            self.msg_var.set(f"发布失败: {e}")

    def _unpublish(self):
        """取消发布 - 需要先创建更改通告"""
        from tkinter import messagebox
        # 弹出更改通告创建对话框
        cn_data = self._ask_change_notice()
        if not cn_data:
            return
        try:
            # 创建更改通告
            cn = self.api.create_change_notice(
                self.part_id, cn_data["title"], cn_data["reason"], cn_data.get("description", "")
            )
            # 自动批准（简化流程，实际应有审批环节）
            self.api.approve_change_notice(cn["id"], True)
            # 执行取消发布
            result = self.api.unpublish(self.part_id, cn["id"])
            self.msg_var.set(f"取消发布成功，新版本: {result.get('current_version', '')}")
            self._refresh_part(result)
        except Exception as e:
            self.msg_var.set(f"取消发布失败: {e}")

    def _ask_change_notice(self) -> dict | None:
        """弹出对话框创建更改通告"""
        dialog = ttk.Toplevel(self.win)
        dialog.title("创建更改通告")
        dialog.geometry("450x300")
        dialog.transient(self.win)
        dialog.grab_set()

        result = {}

        ttk.Label(dialog, text="取消发布需要创建更改通告", font=("Microsoft YaHei", 10, "bold")).pack(padx=15, pady=(10, 5))

        ttk.Label(dialog, text="通告标题:").pack(padx=15, anchor=W)
        title_entry = ttk.Entry(dialog, width=50)
        title_entry.pack(padx=15, pady=2)

        ttk.Label(dialog, text="变更原因:").pack(padx=15, anchor=W)
        reason_entry = ttk.Entry(dialog, width=50)
        reason_entry.pack(padx=15, pady=2)

        ttk.Label(dialog, text="详细说明（可选）:").pack(padx=15, anchor=W)
        desc_entry = ttk.Entry(dialog, width=50)
        desc_entry.pack(padx=15, pady=2)

        def ok():
            if not title_entry.get().strip() or not reason_entry.get().strip():
                from tkinter import messagebox
                messagebox.showwarning("提示", "请填写标题和变更原因")
                return
            result["title"] = title_entry.get().strip()
            result["reason"] = reason_entry.get().strip()
            result["description"] = desc_entry.get().strip()
            dialog.destroy()

        def cancel():
            dialog.destroy()

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=15)
        ttk.Button(btn_frame, text="确定", command=ok).pack(side=LEFT, padx=10)
        ttk.Button(btn_frame, text="取消", command=cancel).pack(side=LEFT, padx=10)

        dialog.wait_window()
        return result if result else None

    def _refresh_part(self, new_data: dict):
        self.part_data = new_data
        for key, lbl in self.field_labels.items():
            lbl.config(text=str(new_data.get(key, "-")))

    def _ask_comment(self) -> str:
        """弹出对话框输入备注"""
        dialog = ttk.Toplevel(self.win)
        dialog.title("检入备注")
        dialog.geometry("400x150")
        dialog.transient(self.win)
        dialog.grab_set()

        ttk.Label(dialog, text="请输入检入备注（可选）:").pack(padx=15, pady=10)
        entry = ttk.Entry(dialog, width=50)
        entry.pack(padx=15, pady=5)
        result = {"comment": ""}

        def ok():
            result["comment"] = entry.get()
            dialog.destroy()

        ttk.Button(dialog, text="确定", command=ok).pack(pady=10)
        dialog.wait_window()
        return result["comment"]
