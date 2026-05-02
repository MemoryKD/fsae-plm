"""智能上传对话框 - 自动识别/生成零件号"""
import os
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox


class UploadDialog:
    def __init__(self, parent, api_client, catia_bridge=None):
        self.parent = parent
        self.api = api_client
        self.catia = catia_bridge
        self.templates = []
        self.selected_file = None

        self.win = ttk.Toplevel(parent)
        self.win.title("新建零件")
        self.win.geometry("500x600")
        self.win.transient(parent)
        self.win.grab_set()

        self._load_templates()
        try:
            self._build_ui()
        except Exception as e:
            ttk.Label(self.win, text=f"加载失败: {e}", bootstyle="danger").pack(padx=20, pady=20)
            import traceback
            traceback.print_exc()

    def _load_templates(self):
        try:
            self.templates = self.api.get_templates()
        except Exception:
            self.templates = []

    def _build_ui(self):
        main = ttk.Frame(self.win, padding=20)
        main.pack(fill=BOTH, expand=True)

        ttk.Label(main, text="新建零件到 PLM", font=("Microsoft YaHei", 14, "bold")).pack(pady=(0, 15))

        file_frame = ttk.LabelFrame(main, text="CATIA 文件")
        file_frame.pack(fill=X, pady=5, padx=10)

        self.file_var = tk.StringVar(value="未选择文件")
        ttk.Label(file_frame, textvariable=self.file_var).pack(side=LEFT, fill=X, expand=True)
        ttk.Button(file_frame, text="选择文件", bootstyle=SECONDARY,
                   command=self._select_file).pack(side=RIGHT, padx=5)
        ttk.Button(file_frame, text="从 CATIA", bootstyle=INFO,
                   command=self._from_catia).pack(side=RIGHT, padx=5)

        info_frame = ttk.LabelFrame(main, text="零件信息")
        info_frame.pack(fill=X, pady=5, padx=10)

        row = ttk.Frame(info_frame)
        row.pack(fill=X, pady=3)
        ttk.Label(row, text="零件名称:", width=10).pack(side=LEFT)
        self.name_entry = ttk.Entry(row)
        self.name_entry.pack(side=LEFT, fill=X, expand=True, padx=(10, 0))

        row = ttk.Frame(info_frame)
        row.pack(fill=X, pady=3)
        ttk.Label(row, text="类型:", width=10).pack(side=LEFT)
        self.type_var = tk.StringVar(value="part")
        type_combo = ttk.Combobox(row, textvariable=self.type_var, values=["part", "assembly", "document"],
                     state="readonly")
        type_combo.pack(side=LEFT, fill=X, expand=True, padx=(10, 0))
        type_combo.bind("<<ComboboxSelected>>", lambda e: self._update_preview())

        row = ttk.Frame(info_frame)
        row.pack(fill=X, pady=3)
        ttk.Label(row, text="子系统:", width=10).pack(side=LEFT)
        self.subsystem_var = tk.StringVar()
        self.subsys_combo = ttk.Combobox(row, textvariable=self.subsystem_var, state="readonly")
        self.subsys_combo.pack(side=LEFT, fill=X, expand=True, padx=(10, 0))
        self.subsys_combo.bind("<<ComboboxSelected>>", lambda e: self._update_preview())

        row = ttk.Frame(info_frame)
        row.pack(fill=X, pady=3)
        ttk.Label(row, text="编号模板:", width=10).pack(side=LEFT)
        self.template_var = tk.StringVar()
        template_names = [t["name"] for t in self.templates] if self.templates else ["无模板"]
        self.template_combo = ttk.Combobox(row, textvariable=self.template_var,
                                           values=template_names, state="readonly")
        self.template_combo.pack(side=LEFT, fill=X, expand=True, padx=(10, 0))
        if template_names:
            self.template_combo.current(0)
        self.template_combo.bind("<<ComboboxSelected>>", lambda e: self._on_template_change())

        preview_frame = ttk.LabelFrame(main, text="零件号预览")
        preview_frame.pack(fill=X, pady=5, padx=10)
        self.preview_var = tk.StringVar(value="请先选择模板和子系统")
        ttk.Label(preview_frame, textvariable=self.preview_var,
                  font=("Consolas", 12, "bold")).pack()

        self.check_var = tk.StringVar()
        ttk.Label(main, textvariable=self.check_var, bootstyle=INFO).pack(fill=X, pady=5)

        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=X, pady=15)
        ttk.Button(btn_frame, text="创建并上传", bootstyle=SUCCESS,
                   command=self._do_upload).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", bootstyle=SECONDARY,
                   command=self.win.destroy).pack(side=RIGHT, padx=5)

        self.msg_var = tk.StringVar()
        ttk.Label(main, textvariable=self.msg_var, bootstyle=DANGER).pack(fill=X, pady=5)

        # 初始化子系统和预览（所有控件已创建完毕）
        if template_names:
            self._on_template_change()

    def _select_file(self):
        path = filedialog.askopenfilename(
            title="选择 CATIA 文件",
            filetypes=[("CATIA 文件", "*.CATPart *.CATProduct *.CATDrawing"), ("所有文件", "*.*")]
        )
        if path:
            self.selected_file = path
            self.file_var.set(os.path.basename(path))

    def _from_catia(self):
        if not self.catia or not self.catia.connected:
            messagebox.showwarning("CATIA", "请先确保 CATIA 已启动")
            return
        doc = self.catia.get_active_document()
        if not doc:
            messagebox.showwarning("CATIA", "请在 CATIA 中打开一个零件")
            return
        temp_path = self.catia.get_temp_save_path("temp_upload")
        if self.catia.save_document_copy(temp_path):
            self.selected_file = temp_path
            self.file_var.set(doc.get("name", "CATIA 文件"))
            if doc.get("plm_name"):
                self.name_entry.delete(0, tk.END)
                self.name_entry.insert(0, doc["plm_name"])
            if doc.get("part_number"):
                try:
                    result = self.api.check_part_number(doc["part_number"])
                    if result.get("exists"):
                        self.check_var.set(f"零件号 {doc['part_number']} 已存在，可直接检入")
                except Exception:
                    pass

    def _on_template_change(self):
        """模板切换时更新子系统下拉列表"""
        template_name = self.template_var.get()
        template = next((t for t in self.templates if t["name"] == template_name), None)
        if template and template.get("subsystem_codes"):
            subsys_list = [f"{code} - {desc}" for code, desc in template["subsystem_codes"].items()]
            self.subsys_combo.config(values=subsys_list)
            if subsys_list:
                self.subsys_combo.current(0)
        else:
            self.subsys_combo.config(values=[])
            self.subsystem_var.set("")
        self._update_preview()

    def _update_preview(self):
        template_name = self.template_var.get()
        template = next((t for t in self.templates if t["name"] == template_name), None)
        if not template:
            return
        subsys = self.subsystem_var.get().split(" - ")[0] if self.subsystem_var.get() else ""
        part_type = self.type_var.get()
        try:
            result = self.api.get_next_part_number(template["id"], subsys, part_type)
            self.preview_var.set(result.get("part_number", "预览失败"))
            check = self.api.check_part_number(result["part_number"])
            if check.get("exists"):
                self.check_var.set(f"注意: {result['part_number']} 已存在")
            else:
                self.check_var.set(f"将创建: {result['part_number']}")
        except Exception as e:
            self.preview_var.set(f"预览失败: {e}")

    def _do_upload(self):
        if not self.selected_file:
            self.msg_var.set("请选择文件")
            return
        name = self.name_entry.get().strip()
        if not name:
            self.msg_var.set("请输入零件名称")
            return
        template_name = self.template_var.get()
        template = next((t for t in self.templates if t["name"] == template_name), None)
        if not template:
            self.msg_var.set("请选择编号模板")
            return
        subsys = self.subsystem_var.get().split(" - ")[0] if self.subsystem_var.get() else ""
        part_type = self.type_var.get()
        try:
            result = self.api.auto_create_part(
                name=name, part_type=part_type, subsystem=subsys,
                template_id=template["id"], file_path=self.selected_file,
            )
            self.msg_var.set(f"创建成功: {result.get('part_number', '')}")
            if self.catia and self.catia.connected:
                self.catia.sync_plm_properties(self.selected_file, result)
            if self.catia and self.catia.connected:
                import tempfile
                thumb_path = os.path.join(tempfile.gettempdir(), "plm_thumb.png")
                if self.catia.capture_thumbnail(thumb_path):
                    try:
                        self.api.upload_thumbnail(result["id"], thumb_path)
                    except Exception:
                        pass
            self.win.after(1500, self.win.destroy)
        except Exception as e:
            self.msg_var.set(f"创建失败: {e}")
