"""登录界面"""
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *


class LoginFrame(ttk.Frame):
    def __init__(self, master, on_login=None):
        super().__init__(master, padding=40)
        self.on_login = on_login
        self._build_ui()

    def _build_ui(self):
        # 标题
        title = ttk.Label(self, text="FSAE-PLM", font=("Microsoft YaHei", 24, "bold"))
        title.pack(pady=(20, 5))
        subtitle = ttk.Label(self, text="CATIA 集成客户端", font=("Microsoft YaHei", 12))
        subtitle.pack(pady=(0, 30))

        # 服务器地址
        frm_server = ttk.Frame(self)
        frm_server.pack(fill=X, pady=5)
        ttk.Label(frm_server, text="服务器地址:", width=10).pack(side=LEFT)
        self.entry_server = ttk.Entry(frm_server)
        self.entry_server.pack(side=LEFT, fill=X, expand=True, padx=(10, 0))
        self.entry_server.insert(0, "http://localhost")

        # 用户名
        frm_user = ttk.Frame(self)
        frm_user.pack(fill=X, pady=5)
        ttk.Label(frm_user, text="用户名:", width=10).pack(side=LEFT)
        self.entry_username = ttk.Entry(frm_user)
        self.entry_username.pack(side=LEFT, fill=X, expand=True, padx=(10, 0))

        # 密码
        frm_pass = ttk.Frame(self)
        frm_pass.pack(fill=X, pady=5)
        ttk.Label(frm_pass, text="密码:", width=10).pack(side=LEFT)
        self.entry_password = ttk.Entry(frm_pass, show="*")
        self.entry_password.pack(side=LEFT, fill=X, expand=True, padx=(10, 0))

        # 记住我
        self.remember_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self, text="记住我", variable=self.remember_var).pack(pady=10)

        # 登录按钮
        self.btn_login = ttk.Button(
            self, text="登录", bootstyle=PRIMARY, command=self._do_login
        )
        self.btn_login.pack(fill=X, pady=10, ipady=8)

        # 状态标签
        self.lbl_status = ttk.Label(self, text="", bootstyle=DANGER)
        self.lbl_status.pack(pady=5)

        # 绑定回车
        self.entry_password.bind("<Return>", lambda e: self._do_login())

    def _do_login(self):
        server = self.entry_server.get().strip()
        username = self.entry_username.get().strip()
        password = self.entry_password.get().strip()

        if not server or not username or not password:
            self.lbl_status.config(text="请填写所有字段")
            return

        self.btn_login.config(state=DISABLED)
        self.lbl_status.config(text="登录中...")
        self.update()

        if self.on_login:
            try:
                self.on_login(server, username, password, self.remember_var.get())
            except Exception as e:
                self.lbl_status.config(text=f"登录失败: {e}")
                self.btn_login.config(state=NORMAL)

    def set_status(self, text: str, style: str = "danger"):
        self.lbl_status.config(text=text, bootstyle=style)

    def set_button_state(self, state):
        self.btn_login.config(state=state)
