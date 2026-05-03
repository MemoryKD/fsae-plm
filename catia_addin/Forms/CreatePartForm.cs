using System;
using System.Collections.Generic;
using System.Drawing;
using System.Windows.Forms;
using FSAE_PLM.Models;
using FSAE_PLM.Services;

namespace FSAE_PLM.Forms
{
    /// <summary>
    /// 新建零件对话框，基于模板自动生成零件编号。
    /// 用户选择模板、子系统和类型后预览编号，确认创建。
    /// </summary>
    public class CreatePartForm : Form
    {
        private readonly PlmApiService _api;

        private TextBox _txtName = null!;
        private ComboBox _cmbType = null!;
        private ComboBox _cmbTemplate = null!;
        private ComboBox _cmbSubsystem = null!;
        private Label _lblPreview = null!;
        private Button _btnCreate = null!;
        private Button _btnCancel = null!;
        private Label _lblStatus = null!;

        private List<TemplateInfo> _templates = new();

        /// <summary>
        /// 创建成功后的零件 ID。
        /// </summary>
        public string? CreatedPartId { get; private set; }

        /// <summary>
        /// 创建成功后的零件编号。
        /// </summary>
        public string? CreatedPartNumber { get; private set; }

        /// <summary>
        /// 初始化创建零件表单。
        /// </summary>
        /// <param name="api">PLM API 服务实例</param>
        public CreatePartForm(PlmApiService api)
        {
            _api = api;
            BuildUI();
            LoadTemplates();
        }

        /// <summary>
        /// 以代码方式构建所有 UI 控件。
        /// </summary>
        private void BuildUI()
        {
            this.Text = "FSAE PLM - 新建零件";
            this.Size = new Size(450, 380);
            this.StartPosition = FormStartPosition.CenterParent;
            this.FormBorderStyle = FormBorderStyle.FixedDialog;
            this.MaximizeBox = false;
            this.MinimizeBox = false;
            this.ShowInTaskbar = true;
            this.TopMost = true;

            int y = 20;
            int labelX = 30;
            int controlX = 120;
            int controlWidth = 280;

            // 零件名称
            var lblName = new Label
            {
                Text = "零件名称:",
                Location = new Point(labelX, y + 3),
                Size = new Size(85, 23),
                TextAlign = ContentAlignment.MiddleRight
            };
            this.Controls.Add(lblName);

            _txtName = new TextBox
            {
                Location = new Point(controlX, y),
                Size = new Size(controlWidth, 23)
            };
            this.Controls.Add(_txtName);

            y += 40;

            // 零件类型
            var lblType = new Label
            {
                Text = "零件类型:",
                Location = new Point(labelX, y + 3),
                Size = new Size(85, 23),
                TextAlign = ContentAlignment.MiddleRight
            };
            this.Controls.Add(lblType);

            _cmbType = new ComboBox
            {
                Location = new Point(controlX, y),
                Size = new Size(controlWidth, 23),
                DropDownStyle = ComboBoxStyle.DropDownList
            };
            _cmbType.Items.AddRange(new object[] { "part", "assembly", "document" });
            _cmbType.SelectedIndex = 0;
            _cmbType.SelectedIndexChanged += CmbTypeOrSubsystem_Changed;
            this.Controls.Add(_cmbType);

            y += 40;

            // 编号模板
            var lblTemplate = new Label
            {
                Text = "编号模板:",
                Location = new Point(labelX, y + 3),
                Size = new Size(85, 23),
                TextAlign = ContentAlignment.MiddleRight
            };
            this.Controls.Add(lblTemplate);

            _cmbTemplate = new ComboBox
            {
                Location = new Point(controlX, y),
                Size = new Size(controlWidth, 23),
                DropDownStyle = ComboBoxStyle.DropDownList
            };
            _cmbTemplate.SelectedIndexChanged += CmbTemplate_SelectedIndexChanged;
            this.Controls.Add(_cmbTemplate);

            y += 40;

            // 子系统
            var lblSubsystem = new Label
            {
                Text = "子系统:",
                Location = new Point(labelX, y + 3),
                Size = new Size(85, 23),
                TextAlign = ContentAlignment.MiddleRight
            };
            this.Controls.Add(lblSubsystem);

            _cmbSubsystem = new ComboBox
            {
                Location = new Point(controlX, y),
                Size = new Size(controlWidth, 23),
                DropDownStyle = ComboBoxStyle.DropDownList
            };
            _cmbSubsystem.SelectedIndexChanged += CmbTypeOrSubsystem_Changed;
            this.Controls.Add(_cmbSubsystem);

            y += 45;

            // 编号预览
            var lblPreviewTitle = new Label
            {
                Text = "编号预览:",
                Location = new Point(labelX, y + 3),
                Size = new Size(85, 23),
                TextAlign = ContentAlignment.MiddleRight,
                ForeColor = Color.Gray
            };
            this.Controls.Add(lblPreviewTitle);

            _lblPreview = new Label
            {
                Text = "-",
                Location = new Point(controlX, y),
                Size = new Size(controlWidth, 23),
                Font = new Font("Microsoft YaHei", 11, FontStyle.Bold),
                ForeColor = Color.DarkBlue,
                TextAlign = ContentAlignment.MiddleLeft
            };
            this.Controls.Add(_lblPreview);

            y += 50;

            // 按钮
            _btnCreate = new Button
            {
                Text = "创 建",
                Location = new Point(controlX, y),
                Size = new Size(130, 35),
                Font = new Font("Microsoft YaHei", 10, FontStyle.Bold)
            };
            _btnCreate.Click += BtnCreate_Click;
            this.Controls.Add(_btnCreate);

            _btnCancel = new Button
            {
                Text = "取 消",
                Location = new Point(controlX + 150, y),
                Size = new Size(130, 35)
            };
            _btnCancel.Click += (s, e) => this.Close();
            this.Controls.Add(_btnCancel);

            // 状态标签
            _lblStatus = new Label
            {
                Text = "",
                ForeColor = Color.Red,
                Location = new Point(30, y + 42),
                Size = new Size(370, 23),
                TextAlign = ContentAlignment.MiddleCenter
            };
            this.Controls.Add(_lblStatus);
        }

        /// <summary>
        /// 从 API 加载可用的编号模板列表。同步调用。
        /// </summary>
        private void LoadTemplates()
        {
            try
            {
                var templates = _api.GetTemplates();
                _templates = new List<TemplateInfo>(templates);

                _cmbTemplate.Items.Clear();
                foreach (var t in _templates)
                {
                    _cmbTemplate.Items.Add(t.Name);
                }

                if (_cmbTemplate.Items.Count > 0)
                    _cmbTemplate.SelectedIndex = 0;
            }
            catch (Exception ex)
            {
                _lblStatus.Text = $"加载模板失败: {ex.Message}";
                _lblStatus.ForeColor = Color.Red;
            }
        }

        /// <summary>
        /// 模板选择变更：更新子系统下拉列表。
        /// </summary>
        private void CmbTemplate_SelectedIndexChanged(object? sender, EventArgs e)
        {
            _cmbSubsystem.Items.Clear();

            var templateIndex = _cmbTemplate.SelectedIndex;
            if (templateIndex < 0 || templateIndex >= _templates.Count)
                return;

            var template = _templates[templateIndex];
            foreach (var subsystemName in template.SubsystemCodes.Keys)
            {
                _cmbSubsystem.Items.Add(subsystemName);
            }

            if (_cmbSubsystem.Items.Count > 0)
                _cmbSubsystem.SelectedIndex = 0;
        }

        /// <summary>
        /// 类型或子系统变更时更新编号预览。同步调用。
        /// </summary>
        private void CmbTypeOrSubsystem_Changed(object? sender, EventArgs e)
        {
            UpdatePreview();
        }

        /// <summary>
        /// 从 API 获取下一个可用编号并更新预览标签。同步调用。
        /// </summary>
        private void UpdatePreview()
        {
            var templateIndex = _cmbTemplate.SelectedIndex;
            var subsystemName = _cmbSubsystem.SelectedItem?.ToString();
            var partType = _cmbType.SelectedItem?.ToString();

            if (templateIndex < 0 || templateIndex >= _templates.Count
                || string.IsNullOrEmpty(subsystemName)
                || string.IsNullOrEmpty(partType))
            {
                _lblPreview.Text = "-";
                return;
            }

            var template = _templates[templateIndex];
            if (!template.SubsystemCodes.TryGetValue(subsystemName, out var subsystemCode))
            {
                _lblPreview.Text = "-";
                return;
            }

            try
            {
                var nextNumber = _api.GetNextPartNumber(template.Id, subsystemCode, partType);
                _lblPreview.Text = string.IsNullOrEmpty(nextNumber) ? "预览失败" : nextNumber;
            }
            catch
            {
                _lblPreview.Text = "预览失败";
            }
        }

        /// <summary>
        /// 创建按钮点击事件。校验输入后调用 API 创建零件。
        /// </summary>
        private void BtnCreate_Click(object? sender, EventArgs e)
        {
            _lblStatus.Text = "";

            var name = _txtName.Text.Trim();
            var partType = _cmbType.SelectedItem?.ToString() ?? "part";
            var subsystemName = _cmbSubsystem.SelectedItem?.ToString();
            var templateIndex = _cmbTemplate.SelectedIndex;

            // 输入校验
            if (string.IsNullOrEmpty(name))
            {
                _lblStatus.Text = "请输入零件名称";
                _lblStatus.ForeColor = Color.Red;
                return;
            }

            if (templateIndex < 0 || templateIndex >= _templates.Count)
            {
                _lblStatus.Text = "请选择编号模板";
                _lblStatus.ForeColor = Color.Red;
                return;
            }

            if (string.IsNullOrEmpty(subsystemName))
            {
                _lblStatus.Text = "请选择子系统";
                _lblStatus.ForeColor = Color.Red;
                return;
            }

            var template = _templates[templateIndex];
            if (!template.SubsystemCodes.TryGetValue(subsystemName, out _))
            {
                _lblStatus.Text = "子系统配置错误";
                _lblStatus.ForeColor = Color.Red;
                return;
            }

            SetControlsEnabled(false);
            _lblStatus.Text = "正在创建...";
            _lblStatus.ForeColor = Color.Gray;

            try
            {
                var part = _api.CreateWithTemplate(name, partType, subsystemName, template.Id);
                if (part != null)
                {
                    CreatedPartId = part.Id.ToString();
                    CreatedPartNumber = part.PartNumber;
                    _lblStatus.Text = $"创建成功: {part.PartNumber}";
                    _lblStatus.ForeColor = Color.Green;

                    MessageBox.Show(
                        $"零件创建成功!\n\n零件编号: {part.PartNumber}\n名称: {part.Name}",
                        "成功", MessageBoxButtons.OK, MessageBoxIcon.Information);

                    this.Close();
                }
                else
                {
                    _lblStatus.Text = $"创建失败: {_api.LastError}";
                    _lblStatus.ForeColor = Color.Red;
                    MessageBox.Show($"零件创建失败: {_api.LastError}", "错误",
                        MessageBoxButtons.OK, MessageBoxIcon.Error);
                }
            }
            catch (Exception ex)
            {
                _lblStatus.Text = $"创建失败: {ex.Message}";
                _lblStatus.ForeColor = Color.Red;
                MessageBox.Show($"创建失败: {ex.Message}", "错误",
                    MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
            finally
            {
                SetControlsEnabled(true);
            }
        }

        /// <summary>
        /// 启用/禁用输入控件，防止重复提交。
        /// </summary>
        private void SetControlsEnabled(bool enabled)
        {
            _txtName.Enabled = enabled;
            _cmbType.Enabled = enabled;
            _cmbTemplate.Enabled = enabled;
            _cmbSubsystem.Enabled = enabled;
            _btnCreate.Enabled = enabled;
        }
    }
}
