"""零件列表界面 - 卡片网格布局"""
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from PIL import Image, ImageTk
import io


class PartCard(ttk.Frame):
    """单个零件卡片"""
    def __init__(self, master, part_data: dict, thumbnail_data: bytes = None, on_click=None):
        super().__init__(master, bootstyle=SECONDARY, padding=8)
        self.part_data = part_data
        self.on_click = on_click
        self._thumbnail_ref = None  # 防止GC回收
        self._build_ui(thumbnail_data)
        self.bind("<Button-1>", self._on_click)

    def _build_ui(self, thumbnail_data):
        # 缩略图
        self.img_label = ttk.Label(self, text="无缩略图", anchor=CENTER)
        self.img_label.pack(fill=X, pady=(0, 5))

        if thumbnail_data:
            try:
                img = Image.open(io.BytesIO(thumbnail_data))
                img = img.resize((160, 120), Image.Resampling.LANCZOS)
                self._thumbnail_ref = ImageTk.PhotoImage(img)
                self.img_label.config(image=self._thumbnail_ref, text="")
            except Exception:
                pass

        # 零件号
        pn = self.part_data.get("part_number", "")
        ttk.Label(self, text=pn, font=("Consolas", 11, "bold"), anchor=CENTER).pack(fill=X)

        # 名称
        name = self.part_data.get("name", "")
        ttk.Label(self, text=name, font=("Microsoft YaHei", 10), anchor=CENTER).pack(fill=X)

        # 状态标签
        lifecycle = self.part_data.get("lifecycle_state", "工作中")
        check = self.part_data.get("check_state", "检入")
        version = self.part_data.get("current_version", "A.1")

        state_text = f"{lifecycle} · {check}"
        state_style = "success" if lifecycle == "已发布" else ("warning" if check == "检出" else "info")

        frm = ttk.Frame(self)
        frm.pack(fill=X, pady=(5, 0))
        ttk.Label(frm, text=f"v{version}", font=("Consolas", 9)).pack(side=LEFT)
        ttk.Label(frm, text=state_text, bootstyle=state_style, font=("Microsoft YaHei", 9)).pack(side=RIGHT)

        # 绑定点击事件到所有子组件
        for child in self.winfo_children():
            child.bind("<Button-1>", self._on_click)
            for sub in child.winfo_children():
                sub.bind("<Button-1>", self._on_click)

    def _on_click(self, event=None):
        if self.on_click:
            self.on_click(self.part_data)


class PartsFrame(ttk.Frame):
    """零件列表主界面"""
    def __init__(self, master, api_client, on_part_click=None):
        super().__init__(master)
        self.api = api_client
        self.on_part_click = on_part_click
        self.cards = []
        self._build_ui()

    def _build_ui(self):
        # 顶部工具栏
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=X, padx=10, pady=(10, 5))

        ttk.Label(toolbar, text="FSAE-PLM", font=("Microsoft YaHei", 14, "bold")).pack(side=LEFT)

        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=30)
        search_entry.pack(side=LEFT, padx=(20, 5))
        search_entry.bind("<Return>", lambda e: self.refresh())

        ttk.Button(toolbar, text="搜索", bootstyle=PRIMARY, command=self.refresh).pack(side=LEFT, padx=5)

        self.btn_refresh = ttk.Button(toolbar, text="刷新", bootstyle=INFO, command=self.refresh)
        self.btn_refresh.pack(side=RIGHT, padx=5)

        self.btn_upload = ttk.Button(toolbar, text="新建零件", bootstyle=SUCCESS, command=self._on_new_part)
        self.btn_upload.pack(side=RIGHT, padx=5)

        self.btn_catia = ttk.Button(toolbar, text="CATIA 操作", bootstyle=WARNING, command=self._on_catia_action)
        self.btn_catia.pack(side=RIGHT, padx=5)

        # 可滚动的卡片区域
        self.canvas = tk.Canvas(self, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient=VERTICAL, command=self.canvas.yview)
        self.card_frame = ttk.Frame(self.canvas)

        self.card_frame.bind("<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.card_frame, anchor=NW)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side=LEFT, fill=BOTH, expand=True, padx=10, pady=5)
        scrollbar.pack(side=RIGHT, fill=Y, pady=5)

        # 绑定鼠标滚轮
        self.canvas.bind_all("<MouseWheel>",
            lambda e: self.canvas.yview_scroll(-1 * (e.delta // 120), "units"))

        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(self, textvariable=self.status_var, bootstyle=SECONDARY)
        status_bar.pack(fill=X, padx=10, pady=(0, 5))

    def refresh(self):
        """刷新零件列表"""
        self.status_var.set("加载中...")
        self.update()

        # 清空现有卡片
        for widget in self.card_frame.winfo_children():
            widget.destroy()
        self.cards = []

        try:
            query = self.search_var.get().strip()
            parts = self.api.search_parts(query)
            self.status_var.set(f"共 {len(parts)} 个零件")

            # 加载缩略图（批量）
            thumbnails = {}
            for part in parts:
                pid = part.get("id")
                if part.get("thumbnail_path"):
                    try:
                        thumb = self.api.get_thumbnail(pid)
                        if thumb:
                            thumbnails[pid] = thumb
                    except Exception:
                        pass

            # 创建卡片网格
            cols = 4
            for i, part in enumerate(parts):
                row, col = divmod(i, cols)
                card = PartCard(
                    self.card_frame,
                    part_data=part,
                    thumbnail_data=thumbnails.get(part.get("id")),
                    on_click=self._on_card_click,
                )
                card.grid(row=row, column=col, padx=8, pady=8, sticky=NSEW)
                self.cards.append(card)

            # 配置列权重
            for c in range(cols):
                self.card_frame.columnconfigure(c, weight=1)

        except Exception as e:
            self.status_var.set(f"加载失败: {e}")

    def _on_card_click(self, part_data):
        if self.on_part_click:
            self.on_part_click(part_data)

    def _on_new_part(self):
        """新建零件回调 - 由 App 注入"""
        pass

    def _on_catia_action(self):
        """CATIA 操作回调 - 由 App 注入"""
        pass
