using System.Collections.ObjectModel;
using System.IO;
using System.Windows.Input;
using CatiaClient.Models;
using System.Windows;

namespace CatiaClient.ViewModels;

/// <summary>
/// 零件详情页面 ViewModel，展示零件信息并提供检出、检入、发布、属性同步等操作。
/// 检出时自动下载文件并在 CATIA 中打开，检入时从 CATIA 获取当前文档上传。
/// </summary>
public class PartDetailViewModel : ViewModelBase
{
    private readonly Services.ApiClient _api;
    private readonly Services.CatiaService _catia;
    private readonly Action _onBack;
    private bool _isLoading;

    /// <summary>
    /// 初始化零件详情 ViewModel，加载版本历史和 BOM 数据。
    /// </summary>
    /// <param name="api">API 客户端实例</param>
    /// <param name="catia">CATIA 服务实例</param>
    /// <param name="part">当前查看的零件</param>
    /// <param name="onBack">返回零件列表回调</param>
    public PartDetailViewModel(Services.ApiClient api, Services.CatiaService catia, Part part, Action onBack)
    {
        _api = api;
        _catia = catia;
        _onBack = onBack;
        CurrentPart = part;
        Versions = new ObservableCollection<PartVersion>();
        BomItems = new ObservableCollection<BomItem>();

        BackCommand = new RelayCommand(() => _onBack());
        CheckoutCommand = new RelayCommand(DoCheckoutAsync, () => CurrentPart.CheckState == "检入");
        CheckinCommand = new RelayCommand(DoCheckinAsync, () => CurrentPart.CheckState == "检出");
        PublishCommand = new RelayCommand(DoPublishAsync, () => CurrentPart.CheckState == "检入" && CurrentPart.LifecycleState != "已发布");
        SyncCommand = new RelayCommand(SyncToCatia);
        RefreshCommand = new RelayCommand(async () => await LoadData());

        _ = LoadData();
    }

    /// <summary>当前零件信息</summary>
    public Part CurrentPart { get; private set; }

    /// <summary>版本历史列表</summary>
    public ObservableCollection<PartVersion> Versions { get; }

    /// <summary>BOM 条目列表（仅总成类型零件有数据）</summary>
    public ObservableCollection<BomItem> BomItems { get; }

    /// <summary>是否正在加载中</summary>
    public bool IsLoading { get => _isLoading; set => SetProperty(ref _isLoading, value); }

    /// <summary>返回零件列表命令</summary>
    public ICommand BackCommand { get; }

    /// <summary>检出命令，仅在零件已检入状态时可用</summary>
    public ICommand CheckoutCommand { get; }

    /// <summary>检入命令，仅在零件已检出状态时可用</summary>
    public ICommand CheckinCommand { get; }

    /// <summary>发布命令，仅在零件已检入且未发布时可用</summary>
    public ICommand PublishCommand { get; }

    /// <summary>同步属性到 CATIA 命令，将 PLM 属性写入 CATIA 文档自定义属性</summary>
    public ICommand SyncCommand { get; }

    /// <summary>刷新命令，重新加载零件数据</summary>
    public ICommand RefreshCommand { get; }

    /// <summary>
    /// 从服务器加载零件详情、版本历史和 BOM 数据。
    /// </summary>
    private async Task LoadData()
    {
        IsLoading = true;
        try
        {
            var part = await _api.GetPartAsync(CurrentPart.Id);
            if (part != null) CurrentPart = part;
            OnPropertyChanged(nameof(CurrentPart));

            var versions = await _api.GetVersionsAsync(CurrentPart.Id);
            Versions.Clear();
            foreach (var v in versions) Versions.Add(v);

            if (CurrentPart.Type == "assembly")
            {
                var bom = await _api.GetBomAsync(CurrentPart.Id);
                BomItems.Clear();
                foreach (var b in bom) BomItems.Add(b);
            }
        }
        catch (Exception ex)
        {
            MessageBox.Show($"加载零件数据失败: {ex.Message}", "错误");
        }
        finally
        {
            IsLoading = false;
            // 刷新所有按钮的 CanExecute 状态
            CommandManager.InvalidateRequerySuggested();
        }
    }

    /// <summary>
    /// 执行检出操作。调用 API 锁定零件，下载最新版本文件。
    /// 如果 CATIA 已连接则自动打开文件，否则提示用户文件保存位置。
    /// </summary>
    private async void DoCheckoutAsync()
    {
        try
        {
            var result = await _api.CheckoutAsync(CurrentPart.Id);
            if (result != null)
            {
                CurrentPart = result;
                OnPropertyChanged(nameof(CurrentPart));
                CommandManager.InvalidateRequerySuggested();

                if (Versions.Count > 0)
                {
                    var tempDir = Path.Combine(Path.GetTempPath(), "catia_plm");
                    Directory.CreateDirectory(tempDir);
                    var latest = Versions[0];
                    var ext = !string.IsNullOrEmpty(latest.FileType) ? $".{latest.FileType}" : "";
                    var savePath = Path.Combine(tempDir, $"{CurrentPart.PartNumber}_{latest.VersionNumber}{ext}");
                    var downloaded = await _api.DownloadVersionAsync(CurrentPart.Id, latest.Id, savePath);

                    if (downloaded)
                    {
                        if (_catia.IsConnected)
                        {
                            var opened = _catia.OpenDocument(savePath);
                            if (opened)
                                MessageBox.Show($"文件已下载并在 CATIA 中打开:\n{savePath}", "检出成功");
                            else
                                MessageBox.Show($"文件已下载但 CATIA 打开失败:\n{_catia.LastError}\n\n文件路径: {savePath}", "提示");
                        }
                        else
                        {
                            // CATIA 未连接，让用户选择保存位置
                            var dlg = new Microsoft.Win32.SaveFileDialog
                            {
                                Title = "保存检出文件",
                                FileName = $"{CurrentPart.PartNumber}_{latest.VersionNumber}{ext}",
                                Filter = "所有文件 (*.*)|*.*"
                            };
                            if (dlg.ShowDialog() == true)
                            {
                                File.Copy(savePath, dlg.FileName, true);
                                MessageBox.Show($"文件已保存到:\n{dlg.FileName}", "检出成功");
                            }
                            else
                            {
                                MessageBox.Show($"文件已下载到临时目录:\n{savePath}", "检出成功");
                            }
                        }
                    }
                    else
                    {
                        MessageBox.Show("文件下载失败", "错误");
                    }
                }
                else
                {
                    MessageBox.Show("检出成功（该零件暂无版本文件）", "提示");
                }
            }
            else
            {
                MessageBox.Show("检出失败，请检查零件状态", "错误");
            }
        }
        catch (Exception ex)
        {
            MessageBox.Show($"检出失败: {ex.Message}", "错误");
        }
    }

    /// <summary>
    /// 执行检入操作。如果 CATIA 已连接则从 CATIA 获取文档，否则弹出文件选择器让用户手动选择文件。
    /// </summary>
    private async void DoCheckinAsync()
    {
        try
        {
            string? filePath = null;

            if (_catia.IsConnected)
            {
                filePath = _catia.GetActiveDocumentPath();
                if (!string.IsNullOrEmpty(filePath))
                {
                    _catia.SaveDocument();
                }
                else
                {
                    // CATIA 已连接但没有打开文档，让用户选择文件
                    var dlg = new Microsoft.Win32.OpenFileDialog
                    {
                        Title = "选择要检入的文件",
                        Filter = "CATIA 文件 (*.CATPart;*.CATProduct)|*.CATPart;*.CATProduct|所有文件 (*.*)|*.*"
                    };
                    if (dlg.ShowDialog() == true)
                        filePath = dlg.FileName;
                }
            }
            else
            {
                // CATIA 未连接，让用户选择文件
                var dlg = new Microsoft.Win32.OpenFileDialog
                {
                    Title = "选择要检入的文件",
                    Filter = "CATIA 文件 (*.CATPart;*.CATProduct)|*.CATPart;*.CATProduct|所有文件 (*.*)|*.*"
                };
                if (dlg.ShowDialog() == true)
                    filePath = dlg.FileName;
            }

            if (string.IsNullOrEmpty(filePath))
            {
                MessageBox.Show("未选择文件，检入已取消", "提示");
                return;
            }

            var (result, error) = await _api.CheckinAsync(CurrentPart.Id, filePath);
            if (result != null)
            {
                CurrentPart = result;
                OnPropertyChanged(nameof(CurrentPart));
                CommandManager.InvalidateRequerySuggested();
                await LoadData();
                MessageBox.Show("检入成功", "成功");
            }
            else
            {
                MessageBox.Show($"检入失败: {error}", "错误");
            }
        }
        catch (Exception ex)
        {
            MessageBox.Show($"检入失败: {ex.Message}", "错误");
        }
    }

    /// <summary>
    /// 执行发布操作，将零件状态从"已检入"变更为"已发布"。
    /// </summary>
    private async void DoPublishAsync()
    {
        try
        {
            var result = await _api.PublishAsync(CurrentPart.Id);
            if (result != null)
            {
                CurrentPart = result;
                OnPropertyChanged(nameof(CurrentPart));
            }
            else
            {
                System.Windows.MessageBox.Show("发布失败，请检查零件状态", "错误");
            }
        }
        catch (Exception ex)
        {
            System.Windows.MessageBox.Show($"发布失败: {ex.Message}", "错误");
        }
    }

    /// <summary>
    /// 将 PLM 零件属性（编号、名称、版本、状态）同步到 CATIA 文档的自定义属性中。
    /// </summary>
    private void SyncToCatia()
    {
        _catia.SyncPlmProperties(CurrentPart);
        System.Windows.MessageBox.Show("属性已同步到 CATIA", "同步成功");
    }
}
