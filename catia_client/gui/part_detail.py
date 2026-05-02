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
        self.btn_container = ttk.Frame(main)
        self.btn_container.pack(fill=X, pady=10)
        self._rebuild_buttons()
        ttk.Button(self.btn_container, text="关闭", bootstyle=SECONDARY,
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

        ver_btn_frame = ttk.Frame(ver_frame)
        ver_btn_frame.pack(fill=X, pady=(5, 0))
        ttk.Button(ver_btn_frame, text="下载选中版本", bootstyle=PRIMARY,
                   command=self._download_selected_version).pack(side=LEFT)

        # BOM section (for assemblies)
        if self.part_data.get("type") == "assembly":
            bom_frame = ttk.LabelFrame(main, text="BOM 物料清单")
            bom_frame.pack(fill=BOTH, expand=True, pady=5, padx=10)

            self.bom_tree = ttk.Treeview(bom_frame, columns=("零件号", "名称", "数量", "状态"), show="headings", height=5)
            for c in ("零件号", "名称", "数量", "状态"):
                self.bom_tree.heading(c, text=c)
                self.bom_tree.column(c, width=100)
            self.bom_tree.pack(fill=BOTH, expand=True)
            self._load_bom()

        # 状态消息
        self.msg_var = tk.StringVar()
        ttk.Label(main, textvariable=self.msg_var, bootstyle=INFO).pack(fill=X, pady=5)

    def _rebuild_buttons(self):
        """根据当前零件状态重建操作按钮"""
        for widget in self.btn_container.winfo_children():
            widget.destroy()

        lifecycle = self.part_data.get("lifecycle_state", "工作中")
        check = self.part_data.get("check_state", "检入")

        if lifecycle == "已发布":
            ttk.Button(self.btn_container, text="取消发布", bootstyle=WARNING,
                       command=self._unpublish).pack(side=LEFT, padx=5)
        elif check == "检入":
            ttk.Button(self.btn_container, text="检出", bootstyle=PRIMARY,
                       command=self._checkout).pack(side=LEFT, padx=5)
            ttk.Button(self.btn_container, text="发布", bootstyle=SUCCESS,
                       command=self._publish).pack(side=LEFT, padx=5)
        elif check == "检出":
            ttk.Button(self.btn_container, text="检入", bootstyle=INFO,
                       command=self._checkin).pack(side=LEFT, padx=5)

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

    def _load_bom(self):
        try:
            items = self.api.get_bom(self.part_id)
            for item in items:
                self.bom_tree.insert("", END, values=(
                    item.get("part_number", ""),
                    item.get("name", ""),
                    item.get("quantity", 1),
                    item.get("check_state", ""),
                ))
        except Exception:
            pass

    def _load_versions(self):
        try:
            self._versions_data = {}
            versions = self.api.get_versions(self.part_id)
            for v in versions:
                item_id = self.ver_tree.insert("", END, values=(
                    v.get("version_number", ""),
                    v.get("file_type", ""),
                    v.get("comment", ""),
                    v.get("created_at", "")[:19],
                ))
                self._versions_data[item_id] = v
        except Exception:
            self._versions_data = {}

    def _download_selected_version(self):
        from tkinter import filedialog, messagebox
        sel = self.ver_tree.selection()
        if not sel:
            messagebox.showinfo("提示", "请先选择一个版本")
            return
        item_id = sel[0]
        version = self._versions_data.get(item_id)
        if not version:
            return
        ext = f".{version.get('file_type', '')}" if version.get("file_type") else ""
        initial_name = f"{self.part_data.get('part_number', 'file')}_{version.get('version_number', '')}{ext}"
        save_path = filedialog.asksaveasfilename(
            title="保存版本文件",
            initialfile=initial_name,
            filetypes=[("CATIA 文件", "*.CATPart *.CATProduct *.CATDrawing"), ("所有文件", "*.*")],
        )
        if save_path:
            try:
                self.api.download_version(self.part_id, version["id"], save_path)
                self.msg_var.set(f"版本 {version.get('version_number', '')} 已保存到: {save_path}")
            except Exception as e:
                self.msg_var.set(f"下载失败: {e}")

    def _checkout(self):
        try:
            result = self.api.checkout(self.part_id)
            self.msg_var.set("检出成功，正在下载文件...")
            self._refresh_part(result)
            # 文件后缀映射
            ext_map = {"part": "CATPart", "assembly": "CATProduct", "document": "CATDrawing"}
            part_type = self.part_data.get("type", "part")
            ext = ext_map.get(part_type, "CATPart")
            # 下载文件到本地
            from tkinter import filedialog, messagebox
            save_path = filedialog.asksaveasfilename(
                title="保存文件到",
                initialfile=f"{self.part_data.get('part_number', 'file')}.{ext}",
                filetypes=[("CATIA 文件", "*.CATPart *.CATProduct *.CATDrawing"), ("所有文件", "*.*")],
            )
            if save_path:
                try:
                    if self.part_data.get("type") == "assembly":
                        import os
                        save_dir = os.path.dirname(save_path)
                        self.api.download_assembly(self.part_id, save_dir)
                    else:
                        self.api.download_file(self.part_id, save_path)
                    # 同步 PLM 属性到下载的文件
                    try:
                        catia = getattr(self.parent, 'catia', None)
                        if catia and catia.connected:
                            catia.sync_plm_properties(save_path, self.part_data)
                    except Exception:
                        pass
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
            # 执行取消发布
            result = self.api.unpublish(self.part_id, cn["id"])
            self.msg_var.set(f"更改通告 {cn.get('notice_number', '')} 已创建，等待审批")
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
        self._rebuild_buttons()

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
