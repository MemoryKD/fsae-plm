using System;
using System.Collections.Generic;
using System.Drawing;
using System.Windows.Forms;
using FSAE_PLM.Models;
using FSAE_PLM.Services;

namespace FSAE_PLM.Forms
{
    /// <summary>
    /// 零件列表对话框，展示所有零件并支持搜索、查看详情、新建零件。
    /// 登录成功后从 VBS 宏调用显示。
    /// </summary>
    public class PartsListForm : Form
    {
        private readonly PlmApiService _api;

        private TextBox _txtSearch = null!;
        private Button _btnSearch = null!;
        private Button _btnRefresh = null!;
        private DataGridView _dgvParts = null!;
        private Button _btnViewDetail = null!;
        private Button _btnNewPart = null!;
        private Button _btnClose = null!;
        private Label _lblStatus = null!;

        // 缓存零件列表，用于根据行索引查找零件 ID
        private List<PartInfo> _cachedParts = new();

        /// <summary>
        /// 最后一次选中并查看详情的零件 ID。
        /// VBS 宏可通过此属性获取选中的零件。
        /// </summary>
        public string? SelectedPartId { get; private set; }

        /// <summary>
        /// 最后一次选中并查看详情的零件完整信息。
        /// </summary>
        public PartInfo? SelectedPart { get; private set; }

        /// <summary>
        /// 初始化零件列表表单。
        /// </summary>
        /// <param name="api">PLM API 服务实例</param>
        public PartsListForm(PlmApiService api)
        {
            _api = api;
            BuildUI();
            LoadParts();
        }

        /// <summary>
        /// 以代码方式构建所有 UI 控件。
        /// </summary>
        private void BuildUI()
        {
            this.Text = "FSAE PLM - 零件列表";
            this.Size = new Size(900, 560);
            this.StartPosition = FormStartPosition.CenterScreen;
            this.MinimumSize = new Size(700, 400);
            this.ShowInTaskbar = true;
            this.TopMost = true;

            // 顶部搜索栏面板
            var panelTop = new Panel
            {
                Dock = DockStyle.Top,
                Height = 50,
                Padding = new Padding(10, 8, 10, 8)
            };

            var lblSearch = new Label
            {
                Text = "搜索:",
                Location = new Point(10, 14),
                Size = new Size(45, 23),
                TextAlign = ContentAlignment.MiddleRight
            };
            panelTop.Controls.Add(lblSearch);

            _txtSearch = new TextBox
            {
                Location = new Point(58, 11),
                Size = new Size(250, 23)
            };
            _txtSearch.KeyDown += (s, e) => { if (e.KeyCode == Keys.Enter) LoadParts(); };
            panelTop.Controls.Add(_txtSearch);

            _btnSearch = new Button
            {
                Text = "搜索",
                Location = new Point(315, 10),
                Size = new Size(70, 25)
            };
            _btnSearch.Click += (s, e) => LoadParts();
            panelTop.Controls.Add(_btnSearch);

            _btnRefresh = new Button
            {
                Text = "刷新",
                Location = new Point(392, 10),
                Size = new Size(70, 25)
            };
            _btnRefresh.Click += (s, e) =>
            {
                _txtSearch.Text = "";
                LoadParts();
            };
            panelTop.Controls.Add(_btnRefresh);

            this.Controls.Add(panelTop);

            // 底部按钮面板
            var panelBottom = new Panel
            {
                Dock = DockStyle.Bottom,
                Height = 50,
                Padding = new Padding(10, 8, 10, 8)
            };

            _lblStatus = new Label
            {
                Text = "",
                ForeColor = Color.Gray,
                Location = new Point(10, 14),
                Size = new Size(300, 23)
            };
            panelBottom.Controls.Add(_lblStatus);

            _btnClose = new Button
            {
                Text = "关闭",
                Anchor = AnchorStyles.Right | AnchorStyles.Top,
                Location = new Point(panelBottom.Width - 90, 10),
                Size = new Size(80, 30)
            };
            _btnClose.Click += (s, e) => this.Close();
            panelBottom.Controls.Add(_btnClose);

            _btnNewPart = new Button
            {
                Text = "新建零件",
                Anchor = AnchorStyles.Right | AnchorStyles.Top,
                Location = new Point(panelBottom.Width - 180, 10),
                Size = new Size(85, 30)
            };
            _btnNewPart.Click += BtnNewPart_Click;
            panelBottom.Controls.Add(_btnNewPart);

            _btnViewDetail = new Button
            {
                Text = "查看详情",
                Anchor = AnchorStyles.Right | AnchorStyles.Top,
                Location = new Point(panelBottom.Width - 275, 10),
                Size = new Size(85, 30)
            };
            _btnViewDetail.Click += BtnViewDetail_Click;
            panelBottom.Controls.Add(_btnViewDetail);

            this.Controls.Add(panelBottom);

            // 零件列表 DataGridView
            _dgvParts = new DataGridView
            {
                Dock = DockStyle.Fill,
                ReadOnly = true,
                AllowUserToAddRows = false,
                AllowUserToDeleteRows = false,
                AllowUserToResizeRows = false,
                SelectionMode = DataGridViewSelectionMode.FullRowSelect,
                MultiSelect = false,
                AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill,
                BackgroundColor = Color.White,
                RowHeadersVisible = false
            };

            _dgvParts.Columns.Add("PartNumber", "零件编号");
            _dgvParts.Columns.Add("Name", "名称");
            _dgvParts.Columns.Add("Type", "类型");
            _dgvParts.Columns.Add("Version", "版本");
            _dgvParts.Columns.Add("LifecycleState", "生命周期状态");
            _dgvParts.Columns.Add("CheckState", "检入/检出");
            _dgvParts.Columns.Add("BranchName", "分支");

            // 双击行查看详情
            _dgvParts.CellDoubleClick += (s, e) =>
            {
                if (e.RowIndex >= 0) BtnViewDetail_Click(s, e);
            };

            this.Controls.Add(_dgvParts);
            // 确保 DataGridView 在填充区域内显示
            _dgvParts.BringToFront();
        }

        /// <summary>
        /// 从 API 加载零件列表并填充 DataGridView。同步调用。
        /// </summary>
        private void LoadParts()
        {
            _lblStatus.Text = "正在加载...";
            _lblStatus.ForeColor = Color.Gray;
            _dgvParts.Rows.Clear();
            _cachedParts.Clear();

            try
            {
                var search = string.IsNullOrWhiteSpace(_txtSearch.Text) ? "" : _txtSearch.Text.Trim();
                var parts = _api.GetParts(search);

                foreach (var part in parts)
                {
                    _cachedParts.Add(part);
                    _dgvParts.Rows.Add(
                        part.PartNumber,
                        part.Name,
                        part.Type,
                        part.CurrentVersion ?? "-",
                        part.LifecycleState,
                        part.CheckState,
                        part.BranchName ?? "-"
                    );
                }

                _lblStatus.Text = $"共 {parts.Length} 个零件";
                _lblStatus.ForeColor = Color.Black;
            }
            catch (Exception ex)
            {
                _lblStatus.Text = "加载失败";
                _lblStatus.ForeColor = Color.Red;
                MessageBox.Show($"加载零件列表失败: {ex.Message}", "错误",
                    MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        /// <summary>
        /// 查看选中零件的详情。打开 PartDetailForm。
        /// </summary>
        private void BtnViewDetail_Click(object? sender, EventArgs e)
        {
            if (_dgvParts.SelectedRows.Count == 0)
            {
                MessageBox.Show("请先选择一个零件", "提示",
                    MessageBoxButtons.OK, MessageBoxIcon.Information);
                return;
            }

            var selectedIndex = _dgvParts.SelectedRows[0].Index;

            if (selectedIndex < 0 || selectedIndex >= _cachedParts.Count)
            {
                MessageBox.Show("无法获取零件信息", "错误",
                    MessageBoxButtons.OK, MessageBoxIcon.Error);
                return;
            }

            var part = _cachedParts[selectedIndex];
            SelectedPartId = part.Id.ToString();
            SelectedPart = part;

            try
            {
                var detailForm = new PartDetailForm(_api, part.Id.ToString());
                detailForm.ShowDialog(this);

                // 刷新列表以反映可能的状态变更
                LoadParts();
            }
            catch (Exception ex)
            {
                MessageBox.Show($"打开详情失败: {ex.Message}", "错误",
                    MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        /// <summary>
        /// 打开新建零件对话框。
        /// </summary>
        private void BtnNewPart_Click(object? sender, EventArgs e)
        {
            try
            {
                var createForm = new CreatePartForm(_api);
                createForm.ShowDialog(this);

                if (!string.IsNullOrEmpty(createForm.CreatedPartId))
                {
                    _lblStatus.Text = $"零件 {createForm.CreatedPartNumber} 创建成功";
                    _lblStatus.ForeColor = Color.Green;
                    LoadParts();
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"打开创建窗口失败: {ex.Message}", "错误",
                    MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }
    }
}
