using System;
using System.Drawing;
using System.IO;
using System.Windows.Forms;
using FSAE_PLM.Models;
using FSAE_PLM.Services;

namespace FSAE_PLM.Forms
{
    /// <summary>
    /// 零件详情对话框，展示零件信息、版本历史和 BOM，提供检出、检入、发布等操作。
    /// 从 PartsListForm 双击或"查看详情"按钮打开。
    /// </summary>
    public class PartDetailForm : Form
    {
        private readonly PlmApiService _api;
        private readonly Guid _partId;
        private PartInfo? _currentPart;

        // 信息面板标签
        private Label _lblPartNumber = null!;
        private Label _lblName = null!;
        private Label _lblType = null!;
        private Label _lblSubsystem = null!;
        private Label _lblVersion = null!;
        private Label _lblLifecycleState = null!;
        private Label _lblCheckState = null!;

        // 版本历史和 BOM
        private DataGridView _dgvVersions = null!;
        private DataGridView _dgvBom = null!;
        private TabControl _tabControl = null!;

        // 操作按钮
        private Button _btnCheckout = null!;
        private Button _btnCheckin = null!;
        private Button _btnPublish = null!;
        private Button _btnSyncProperties = null!;
        private Button _btnBranch = null!;
        private Button _btnClose = null!;
        private Label _lblStatus = null!;

        // 公开属性，供调用方检查操作结果
        public string? CheckoutFilePath { get; private set; }
        public bool WasCheckedIn { get; private set; }
        public bool WasPublished { get; private set; }

        /// <summary>
        /// 初始化零件详情表单。
        /// </summary>
        /// <param name="api">PLM API 服务实例</param>
        /// <param name="partId">要查看的零件 ID（GUID 字符串）</param>
        public PartDetailForm(PlmApiService api, string partId)
        {
            _api = api;
            _partId = Guid.Parse(partId);
            BuildUI();
            LoadData();
        }

        /// <summary>
        /// 以代码方式构建所有 UI 控件。
        /// </summary>
        private void BuildUI()
        {
            this.Text = "FSAE PLM - 零件详情";
            this.Size = new Size(800, 620);
            this.StartPosition = FormStartPosition.CenterParent;
            this.MinimumSize = new Size(650, 480);
            this.ShowInTaskbar = true;
            this.TopMost = true;

            // 上半部分：零件信息面板
            var panelInfo = new GroupBox
            {
                Text = "零件信息",
                Dock = DockStyle.Top,
                Height = 140,
                Padding = new Padding(10, 5, 10, 5)
            };

            var infoLabels = new[]
            {
                "零件编号:", "名称:", "类型:", "子系统:", "版本:", "生命周期状态:", "检入/检出:"
            };
            var infoValues = new Label[7];

            for (int i = 0; i < 7; i++)
            {
                var row = i / 3;
                var col = i % 3;
                var x = 15 + col * 250;
                var y = 25 + row * 32;

                var lbl = new Label
                {
                    Text = infoLabels[i],
                    Location = new Point(x, y),
                    Size = new Size(80, 20),
                    TextAlign = ContentAlignment.MiddleRight,
                    ForeColor = Color.Gray
                };
                panelInfo.Controls.Add(lbl);

                infoValues[i] = new Label
                {
                    Text = "-",
                    Location = new Point(x + 85, y),
                    Size = new Size(150, 20),
                    TextAlign = ContentAlignment.MiddleLeft,
                    Font = new Font("Microsoft YaHei", 9, FontStyle.Bold)
                };
                panelInfo.Controls.Add(infoValues[i]);
            }

            _lblPartNumber = infoValues[0];
            _lblName = infoValues[1];
            _lblType = infoValues[2];
            _lblSubsystem = infoValues[3];
            _lblVersion = infoValues[4];
            _lblLifecycleState = infoValues[5];
            _lblCheckState = infoValues[6];

            this.Controls.Add(panelInfo);

            // 中间部分：Tab 控件（版本历史 / BOM）
            _tabControl = new TabControl
            {
                Dock = DockStyle.Fill,
                Padding = new Point(15, 5)
            };

            // 版本历史 Tab
            var tabVersions = new TabPage("版本历史");
            _dgvVersions = new DataGridView
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
            _dgvVersions.Columns.Add("VersionNumber", "版本号");
            _dgvVersions.Columns.Add("FileType", "文件类型");
            _dgvVersions.Columns.Add("FileSize", "文件大小");
            _dgvVersions.Columns.Add("Comment", "备注");
            _dgvVersions.Columns.Add("CreatedAt", "创建时间");
            tabVersions.Controls.Add(_dgvVersions);

            // BOM Tab
            var tabBom = new TabPage("BOM 物料清单");
            _dgvBom = new DataGridView
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
            _dgvBom.Columns.Add("PartNumber", "零件编号");
            _dgvBom.Columns.Add("Name", "名称");
            _dgvBom.Columns.Add("Quantity", "数量");
            _dgvBom.Columns.Add("Level", "层级");
            tabBom.Controls.Add(_dgvBom);

            _tabControl.TabPages.Add(tabVersions);
            _tabControl.TabPages.Add(tabBom);

            this.Controls.Add(_tabControl);

            // 底部操作按钮面板
            var panelBottom = new Panel
            {
                Dock = DockStyle.Bottom,
                Height = 55,
                Padding = new Padding(10, 8, 10, 8)
            };

            _lblStatus = new Label
            {
                Text = "",
                ForeColor = Color.Gray,
                Location = new Point(10, 30),
                Size = new Size(500, 20)
            };
            panelBottom.Controls.Add(_lblStatus);

            _btnClose = new Button
            {
                Text = "关闭",
                Anchor = AnchorStyles.Right | AnchorStyles.Top,
                Location = new Point(panelBottom.Width - 90, 5),
                Size = new Size(80, 25)
            };
            _btnClose.Click += (s, e) => this.Close();
            panelBottom.Controls.Add(_btnClose);

            _btnBranch = new Button
            {
                Text = "分支",
                Anchor = AnchorStyles.Right | AnchorStyles.Top,
                Location = new Point(panelBottom.Width - 178, 5),
                Size = new Size(80, 25)
            };
            _btnBranch.Click += BtnBranch_Click;
            panelBottom.Controls.Add(_btnBranch);

            _btnSyncProperties = new Button
            {
                Text = "同步属性",
                Anchor = AnchorStyles.Right | AnchorStyles.Top,
                Location = new Point(panelBottom.Width - 266, 5),
                Size = new Size(80, 25)
            };
            _btnSyncProperties.Click += BtnSyncProperties_Click;
            panelBottom.Controls.Add(_btnSyncProperties);

            _btnPublish = new Button
            {
                Text = "发布",
                Anchor = AnchorStyles.Right | AnchorStyles.Top,
                Location = new Point(panelBottom.Width - 354, 5),
                Size = new Size(80, 25)
            };
            _btnPublish.Click += BtnPublish_Click;
            panelBottom.Controls.Add(_btnPublish);

            _btnCheckin = new Button
            {
                Text = "检入",
                Anchor = AnchorStyles.Right | AnchorStyles.Top,
                Location = new Point(panelBottom.Width - 442, 5),
                Size = new Size(80, 25)
            };
            _btnCheckin.Click += BtnCheckin_Click;
            panelBottom.Controls.Add(_btnCheckin);

            _btnCheckout = new Button
            {
                Text = "检出",
                Anchor = AnchorStyles.Right | AnchorStyles.Top,
                Location = new Point(panelBottom.Width - 530, 5),
                Size = new Size(80, 25)
            };
            _btnCheckout.Click += BtnCheckout_Click;
            panelBottom.Controls.Add(_btnCheckout);

            this.Controls.Add(panelBottom);

            // 确保 TabControl 在 Fill 区域显示
            _tabControl.BringToFront();
        }

        /// <summary>
        /// 从 API 加载零件详情、版本历史和 BOM 数据。同步调用。
        /// </summary>
        private void LoadData()
        {
            _lblStatus.Text = "正在加载...";
            _lblStatus.ForeColor = Color.Gray;

            try
            {
                // 加载零件详情
                _currentPart = _api.GetPart(_partId);
                if (_currentPart == null)
                {
                    _lblStatus.Text = $"零件不存在: {_api.LastError}";
                    _lblStatus.ForeColor = Color.Red;
                    return;
                }

                // 更新信息面板
                _lblPartNumber.Text = _currentPart.PartNumber;
                _lblName.Text = _currentPart.Name;
                _lblType.Text = _currentPart.Type;
                _lblSubsystem.Text = _currentPart.Subsystem ?? "-";
                _lblVersion.Text = _currentPart.CurrentVersion ?? "-";
                _lblLifecycleState.Text = _currentPart.LifecycleState;
                _lblCheckState.Text = _currentPart.CheckState;

                // 加载版本历史
                var versions = _api.GetVersions(_partId);
                _dgvVersions.Rows.Clear();
                foreach (var v in versions)
                {
                    var fileSize = v.FileSize.HasValue ? FormatFileSize(v.FileSize.Value) : "-";
                    _dgvVersions.Rows.Add(
                        v.VersionNumber,
                        v.FileType ?? "-",
                        fileSize,
                        v.Comment ?? "-",
                        v.CreatedAt.ToString("yyyy-MM-dd HH:mm")
                    );
                }

                // 加载 BOM（仅 assembly 类型）
                if (_currentPart.Type == "assembly")
                {
                    var bom = _api.GetBom(_partId);
                    _dgvBom.Rows.Clear();
                    foreach (var b in bom)
                    {
                        _dgvBom.Rows.Add(
                            b.PartNumber,
                            b.Name,
                            b.Quantity.ToString(),
                            b.Level.ToString()
                        );
                    }
                }

                // 更新按钮可用状态
                UpdateButtonStates();
                _lblStatus.Text = "加载完成";
                _lblStatus.ForeColor = Color.Green;
            }
            catch (Exception ex)
            {
                _lblStatus.Text = "加载失败";
                _lblStatus.ForeColor = Color.Red;
                MessageBox.Show($"加载零件数据失败: {ex.Message}", "错误",
                    MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        /// <summary>
        /// 根据当前零件状态更新各操作按钮的可用性。
        /// </summary>
        private void UpdateButtonStates()
        {
            if (_currentPart == null)
            {
                _btnCheckout.Enabled = false;
                _btnCheckin.Enabled = false;
                _btnPublish.Enabled = false;
                return;
            }

            // 已检入状态才能检出
            _btnCheckout.Enabled = _currentPart.CheckState == "检入";

            // 已检出状态才能检入
            _btnCheckin.Enabled = _currentPart.CheckState == "检出";

            // 已检入且未发布才能发布
            _btnPublish.Enabled = _currentPart.CheckState == "检入"
                                  && _currentPart.LifecycleState != "已发布";
        }

        /// <summary>
        /// 检出按钮：调用 API 检出零件，下载最新版本文件到临时目录，关闭表单。
        /// </summary>
        private void BtnCheckout_Click(object? sender, EventArgs e)
        {
            if (_currentPart == null) return;

            SetButtonsEnabled(false);
            try
            {
                var result = _api.Checkout(_partId);
                if (result == null)
                {
                    MessageBox.Show($"检出失败: {_api.LastError}", "错误",
                        MessageBoxButtons.OK, MessageBoxIcon.Error);
                    return;
                }

                _currentPart = result;

                // 下载最新版本文件
                var versions = _api.GetVersions(_partId);
                if (versions.Length > 0)
                {
                    var latest = versions[0];
                    var tempDir = Path.Combine(Path.GetTempPath(), "catia_plm");
                    Directory.CreateDirectory(tempDir);
                    var ext = !string.IsNullOrEmpty(latest.FileType) ? $".{latest.FileType}" : "";
                    var savePath = Path.Combine(tempDir,
                        $"{_currentPart.PartNumber}_{latest.VersionNumber}{ext}");

                    var downloaded = _api.DownloadVersion(_partId, latest.Id, savePath);
                    if (downloaded)
                    {
                        CheckoutFilePath = savePath;
                        MessageBox.Show($"检出成功，文件已下载到:\n{savePath}", "成功",
                            MessageBoxButtons.OK, MessageBoxIcon.Information);
                        this.Close();
                    }
                    else
                    {
                        MessageBox.Show($"检出成功但文件下载失败: {_api.LastError}", "错误",
                            MessageBoxButtons.OK, MessageBoxIcon.Error);
                    }
                }
                else
                {
                    MessageBox.Show("检出成功（该零件暂无版本文件）", "提示",
                        MessageBoxButtons.OK, MessageBoxIcon.Information);
                    this.Close();
                }

                LoadData();
            }
            catch (Exception ex)
            {
                MessageBox.Show($"检出失败: {ex.Message}", "错误",
                    MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
            finally
            {
                SetButtonsEnabled(true);
            }
        }

        /// <summary>
        /// 检入按钮：显示文件选择对话框让用户选择 .CATPart/.CATProduct 文件，
        /// 然后调用 API 检入。
        /// </summary>
        private void BtnCheckin_Click(object? sender, EventArgs e)
        {
            if (_currentPart == null) return;

            using var dlg = new OpenFileDialog
            {
                Title = "选择要检入的 CATIA 文件",
                Filter = "CATIA 文件 (*.CATPart;*.CATProduct)|*.CATPart;*.CATProduct|所有文件 (*.*)|*.*"
            };

            if (dlg.ShowDialog(this) != DialogResult.OK)
                return;

            SetButtonsEnabled(false);
            try
            {
                var result = _api.Checkin(_partId, dlg.FileName, "");
                if (result != null)
                {
                    _currentPart = result;
                    WasCheckedIn = true;
                    MessageBox.Show("检入成功", "成功",
                        MessageBoxButtons.OK, MessageBoxIcon.Information);
                    LoadData();
                }
                else
                {
                    MessageBox.Show($"检入失败: {_api.LastError}", "错误",
                        MessageBoxButtons.OK, MessageBoxIcon.Error);
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"检入失败: {ex.Message}", "错误",
                    MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
            finally
            {
                SetButtonsEnabled(true);
            }
        }

        /// <summary>
        /// 发布按钮：调用 API 将零件状态变更为"已发布"。
        /// </summary>
        private void BtnPublish_Click(object? sender, EventArgs e)
        {
            if (_currentPart == null) return;

            var confirm = MessageBox.Show(
                "确定要发布此零件吗？发布后状态将变更为\"已发布\"。",
                "确认发布", MessageBoxButtons.YesNo, MessageBoxIcon.Question);
            if (confirm != DialogResult.Yes) return;

            SetButtonsEnabled(false);
            try
            {
                var result = _api.Publish(_partId);
                if (result != null)
                {
                    _currentPart = result;
                    WasPublished = true;
                    MessageBox.Show("发布成功", "成功",
                        MessageBoxButtons.OK, MessageBoxIcon.Information);
                    LoadData();
                }
                else
                {
                    MessageBox.Show($"发布失败: {_api.LastError}", "错误",
                        MessageBoxButtons.OK, MessageBoxIcon.Error);
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"发布失败: {ex.Message}", "错误",
                    MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
            finally
            {
                SetButtonsEnabled(true);
            }
        }

        /// <summary>
        /// 同步属性按钮：将 PLM 属性信息展示给用户。
        /// 实际写入 CATIA 文档自定义属性需在 CATIA 环境中通过 VBS 宏执行。
        /// </summary>
        private void BtnSyncProperties_Click(object? sender, EventArgs e)
        {
            if (_currentPart == null) return;

            MessageBox.Show(
                $"属性信息:\n" +
                $"零件编号: {_currentPart.PartNumber}\n" +
                $"名称: {_currentPart.Name}\n" +
                $"版本: {_currentPart.CurrentVersion ?? "-"}\n" +
                $"生命周期: {_currentPart.LifecycleState}\n\n" +
                $"请在 CATIA 中打开文档后通过 VBS 宏执行属性同步。",
                "同步属性", MessageBoxButtons.OK, MessageBoxIcon.Information);
        }

        /// <summary>
        /// 分支按钮：提示输入分支名称，调用 API 创建分支。
        /// </summary>
        private void BtnBranch_Click(object? sender, EventArgs e)
        {
            if (_currentPart == null) return;

            // 简单输入对话框
            var inputForm = new Form
            {
                Text = "创建分支",
                Size = new Size(350, 160),
                StartPosition = FormStartPosition.CenterParent,
                FormBorderStyle = FormBorderStyle.FixedDialog,
                MaximizeBox = false,
                MinimizeBox = false,
                ShowInTaskbar = false,
                TopMost = true
            };

            var lbl = new Label
            {
                Text = "分支名称:",
                Location = new Point(20, 25),
                Size = new Size(70, 23)
            };
            inputForm.Controls.Add(lbl);

            var txtBranch = new TextBox
            {
                Location = new Point(95, 22),
                Size = new Size(220, 23)
            };
            inputForm.Controls.Add(txtBranch);

            var btnOk = new Button
            {
                Text = "确定",
                DialogResult = DialogResult.OK,
                Location = new Point(140, 70),
                Size = new Size(80, 30)
            };
            inputForm.Controls.Add(btnOk);

            var btnCancel = new Button
            {
                Text = "取消",
                DialogResult = DialogResult.Cancel,
                Location = new Point(230, 70),
                Size = new Size(80, 30)
            };
            inputForm.Controls.Add(btnCancel);

            inputForm.AcceptButton = btnOk;
            inputForm.CancelButton = btnCancel;

            if (inputForm.ShowDialog(this) != DialogResult.OK)
                return;

            var branchName = txtBranch.Text.Trim();
            if (string.IsNullOrEmpty(branchName))
            {
                MessageBox.Show("请输入分支名称", "提示",
                    MessageBoxButtons.OK, MessageBoxIcon.Information);
                return;
            }

            SetButtonsEnabled(false);
            try
            {
                var result = _api.CreateBranch(_partId, branchName);
                if (result != null)
                {
                    MessageBox.Show($"分支创建成功: {result.PartNumber}", "成功",
                        MessageBoxButtons.OK, MessageBoxIcon.Information);
                }
                else
                {
                    MessageBox.Show($"分支创建失败: {_api.LastError}", "错误",
                        MessageBoxButtons.OK, MessageBoxIcon.Error);
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"分支创建失败: {ex.Message}", "错误",
                    MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
            finally
            {
                SetButtonsEnabled(true);
            }
        }

        /// <summary>
        /// 启用/禁用所有操作按钮，防止重复操作。
        /// </summary>
        private void SetButtonsEnabled(bool enabled)
        {
            _btnCheckout.Enabled = enabled;
            _btnCheckin.Enabled = enabled;
            _btnPublish.Enabled = enabled;
            _btnSyncProperties.Enabled = enabled;
            _btnBranch.Enabled = enabled;
        }

        /// <summary>
        /// 将字节大小格式化为人类可读的字符串。
        /// </summary>
        private static string FormatFileSize(long bytes)
        {
            string[] suffixes = { "B", "KB", "MB", "GB" };
            int order = 0;
            double size = bytes;
            while (size >= 1024 && order < suffixes.Length - 1)
            {
                order++;
                size /= 1024;
            }
            return $"{size:0.##} {suffixes[order]}";
        }
    }
}
