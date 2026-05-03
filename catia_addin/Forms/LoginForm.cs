using System;
using System.Diagnostics;
using System.Drawing;
using System.Windows.Forms;
using FSAE_PLM.Services;

namespace FSAE_PLM.Forms
{
    /// <summary>
    /// 登录对话框，用于用户认证。从 CATIA VBS 宏启动时显示。
    /// 登录成功后关闭对话框，调用方可通过 DialogResult 判断结果。
    /// </summary>
    public class LoginForm : Form
    {
        private readonly PlmApiService _api;

        private TextBox _txtServerUrl = null!;
        private TextBox _txtUsername = null!;
        private TextBox _txtPassword = null!;
        private Button _btnLogin = null!;
        private Button _btnRegister = null!;
        private Label _lblStatus = null!;
        private Label _lblTitle = null!;
        private Label _lblCatiaStatus = null!;

        /// <summary>
        /// 初始化登录表单。
        /// </summary>
        /// <param name="api">PLM API 服务实例</param>
        public LoginForm(PlmApiService api)
        {
            _api = api;
            BuildUI();
        }

        private bool IsCatiaRunning()
        {
            return Process.GetProcessesByName("CNEXT").Length > 0
                || Process.GetProcessesByName("CATIA").Length > 0
                || Process.GetProcessesByName("cnext").Length > 0;
        }

        /// <summary>
        /// 以代码方式构建所有 UI 控件，不依赖设计器文件。
        /// </summary>
        private void BuildUI()
        {
            // 表单基本设置
            this.Text = "FSAE PLM - 用户登录";
            this.Size = new Size(420, 380);
            this.StartPosition = FormStartPosition.CenterScreen;
            this.FormBorderStyle = FormBorderStyle.FixedDialog;
            this.MaximizeBox = false;
            this.MinimizeBox = false;
            this.ShowInTaskbar = true;
            this.TopMost = true;

            // CATIA 连接状态栏
            bool catiaRunning = IsCatiaRunning();
            _lblCatiaStatus = new Label
            {
                Text = catiaRunning ? "CATIA V5 已连接" : "CATIA V5 未运行",
                ForeColor = catiaRunning ? Color.Green : Color.Red,
                Font = new Font("Microsoft YaHei", 9, FontStyle.Bold),
                Dock = DockStyle.Top,
                Height = 30,
                TextAlign = ContentAlignment.MiddleCenter,
                BackColor = catiaRunning ? Color.FromArgb(232, 245, 233) : Color.FromArgb(255, 235, 238)
            };
            this.Controls.Add(_lblCatiaStatus);

            // 标题
            _lblTitle = new Label
            {
                Text = "FSAE 赛车 PLM 系统",
                Font = new Font("Microsoft YaHei", 14, FontStyle.Bold),
                TextAlign = ContentAlignment.MiddleCenter,
                Location = new Point(20, 15),
                Size = new Size(360, 35)
            };
            this.Controls.Add(_lblTitle);

            // 服务器地址
            var lblServer = new Label
            {
                Text = "服务器地址:",
                Location = new Point(30, 65),
                Size = new Size(80, 23),
                TextAlign = ContentAlignment.MiddleRight
            };
            this.Controls.Add(lblServer);

            _txtServerUrl = new TextBox
            {
                Location = new Point(115, 65),
                Size = new Size(255, 23),
                Text = "http://localhost/api"
            };
            this.Controls.Add(_txtServerUrl);

            // 用户名
            var lblUsername = new Label
            {
                Text = "用户名:",
                Location = new Point(30, 100),
                Size = new Size(80, 23),
                TextAlign = ContentAlignment.MiddleRight
            };
            this.Controls.Add(lblUsername);

            _txtUsername = new TextBox
            {
                Location = new Point(115, 100),
                Size = new Size(255, 23)
            };
            this.Controls.Add(_txtUsername);

            // 密码
            var lblPassword = new Label
            {
                Text = "密码:",
                Location = new Point(30, 135),
                Size = new Size(80, 23),
                TextAlign = ContentAlignment.MiddleRight
            };
            this.Controls.Add(lblPassword);

            _txtPassword = new TextBox
            {
                Location = new Point(115, 135),
                Size = new Size(255, 23),
                UseSystemPasswordChar = true
            };
            this.Controls.Add(_txtPassword);

            // 登录按钮
            _btnLogin = new Button
            {
                Text = "登 录",
                Location = new Point(115, 180),
                Size = new Size(120, 35),
                Font = new Font("Microsoft YaHei", 10, FontStyle.Bold)
            };
            _btnLogin.Click += BtnLogin_Click;
            this.Controls.Add(_btnLogin);

            // 注册按钮
            _btnRegister = new Button
            {
                Text = "注册新用户",
                Location = new Point(250, 180),
                Size = new Size(120, 35),
                Font = new Font("Microsoft YaHei", 9)
            };
            _btnRegister.Click += BtnRegister_Click;
            this.Controls.Add(_btnRegister);

            // 状态标签（错误/提示信息）
            _lblStatus = new Label
            {
                Text = "",
                ForeColor = Color.Red,
                Location = new Point(30, 230),
                Size = new Size(340, 40),
                TextAlign = ContentAlignment.MiddleCenter
            };
            this.Controls.Add(_lblStatus);

            // 回车键触发登录
            this.AcceptButton = _btnLogin;
        }

        /// <summary>
        /// 登录按钮点击事件。验证输入后调用 PlmApiService.Login()。
        /// </summary>
        private void BtnLogin_Click(object? sender, EventArgs e)
        {
            _lblStatus.Text = "";
            _lblStatus.ForeColor = Color.Red;

            var serverUrl = _txtServerUrl.Text.Trim();
            var username = _txtUsername.Text.Trim();
            var password = _txtPassword.Text;

            if (string.IsNullOrEmpty(username))
            {
                _lblStatus.Text = "请输入用户名";
                return;
            }

            if (string.IsNullOrEmpty(password))
            {
                _lblStatus.Text = "请输入密码";
                return;
            }

            SetControlsEnabled(false);
            _lblStatus.Text = "正在登录...";
            _lblStatus.ForeColor = Color.Gray;

            try
            {
                var success = _api.Login(serverUrl, username, password);
                if (success)
                {
                    this.DialogResult = DialogResult.OK;
                    this.Close();
                }
                else
                {
                    _lblStatus.Text = _api.LastError;
                    _lblStatus.ForeColor = Color.Red;
                }
            }
            catch (Exception ex)
            {
                _lblStatus.Text = $"连接服务器失败: {ex.Message}";
                _lblStatus.ForeColor = Color.Red;
            }
            finally
            {
                SetControlsEnabled(true);
            }
        }

        /// <summary>
        /// 注册按钮点击事件。打开注册表单。
        /// </summary>
        private void BtnRegister_Click(object? sender, EventArgs e)
        {
            try
            {
                var registerForm = new RegisterForm(_api);
                registerForm.ShowDialog(this);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"打开注册窗口失败: {ex.Message}", "错误",
                    MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        /// <summary>
        /// 启用/禁用输入控件，防止重复提交。
        /// </summary>
        private void SetControlsEnabled(bool enabled)
        {
            _txtServerUrl.Enabled = enabled;
            _txtUsername.Enabled = enabled;
            _txtPassword.Enabled = enabled;
            _btnLogin.Enabled = enabled;
            _btnRegister.Enabled = enabled;
        }
    }
}
