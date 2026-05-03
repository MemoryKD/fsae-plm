using System;
using System.Drawing;
using System.Windows.Forms;
using FSAE_PLM.Services;

namespace FSAE_PLM.Forms
{
    /// <summary>
    /// 用户注册对话框。注册后需等待管理员审批才能登录。
    /// 从 LoginForm 的"注册"按钮打开。
    /// </summary>
    public class RegisterForm : Form
    {
        private readonly PlmApiService _api;

        private TextBox _txtUsername = null!;
        private TextBox _txtPassword = null!;
        private TextBox _txtFullName = null!;
        private TextBox _txtDepartment = null!;
        private TextBox _txtJoinYear = null!;
        private TextBox _txtPhone = null!;
        private Button _btnRegister = null!;
        private Button _btnBack = null!;
        private Label _lblStatus = null!;

        public RegisterForm(PlmApiService api)
        {
            _api = api;
            BuildUI();
        }

        private void BuildUI()
        {
            this.Text = "FSAE PLM - 用户注册";
            this.Size = new Size(420, 420);
            this.StartPosition = FormStartPosition.CenterParent;
            this.FormBorderStyle = FormBorderStyle.FixedDialog;
            this.MaximizeBox = false;
            this.MinimizeBox = false;
            this.ShowInTaskbar = true;
            this.TopMost = true;

            int y = 20;
            int labelX = 30;
            int controlX = 110;
            int controlWidth = 270;

            var fields = new[]
            {
                ("用户名:", false), ("密码:", true), ("真实姓名:", false),
                ("所属部门:", false), ("入队年份:", false), ("联系电话:", false)
            };

            var controls = new TextBox[6];
            for (int i = 0; i < fields.Length; i++)
            {
                var lbl = new Label
                {
                    Text = fields[i].Item1,
                    Location = new Point(labelX, y + 3),
                    Size = new Size(75, 23),
                    TextAlign = ContentAlignment.MiddleRight
                };
                this.Controls.Add(lbl);

                controls[i] = new TextBox
                {
                    Location = new Point(controlX, y),
                    Size = new Size(controlWidth, 23),
                    UseSystemPasswordChar = fields[i].Item2
                };
                this.Controls.Add(controls[i]);
                y += 35;
            }

            _txtUsername = controls[0];
            _txtPassword = controls[1];
            _txtFullName = controls[2];
            _txtDepartment = controls[3];
            _txtJoinYear = controls[4];
            _txtPhone = controls[5];

            y += 10;

            _btnRegister = new Button
            {
                Text = "注 册",
                Location = new Point(controlX, y),
                Size = new Size(125, 35),
                Font = new Font("Microsoft YaHei", 10, FontStyle.Bold)
            };
            _btnRegister.Click += BtnRegister_Click;
            this.Controls.Add(_btnRegister);

            _btnBack = new Button
            {
                Text = "返 回",
                Location = new Point(controlX + 145, y),
                Size = new Size(125, 35)
            };
            _btnBack.Click += (s, e) => this.Close();
            this.Controls.Add(_btnBack);

            _lblStatus = new Label
            {
                Text = "",
                ForeColor = Color.Red,
                Location = new Point(30, y + 42),
                Size = new Size(350, 23),
                TextAlign = ContentAlignment.MiddleCenter
            };
            this.Controls.Add(_lblStatus);
        }

        private void BtnRegister_Click(object? sender, EventArgs e)
        {
            _lblStatus.Text = "";

            var username = _txtUsername.Text.Trim();
            var password = _txtPassword.Text;
            var fullName = _txtFullName.Text.Trim();

            if (string.IsNullOrEmpty(username) || string.IsNullOrEmpty(password))
            {
                _lblStatus.Text = "用户名和密码不能为空";
                return;
            }

            if (string.IsNullOrEmpty(fullName))
            {
                _lblStatus.Text = "请输入真实姓名";
                return;
            }

            // TODO: PlmApiService 目前没有 Register 方法，需要后续添加
            // 暂时显示提示
            _lblStatus.Text = "注册功能待 API 服务实现后启用";
            _lblStatus.ForeColor = Color.Gray;
        }
    }
}
