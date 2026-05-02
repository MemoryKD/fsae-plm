using System.Collections.ObjectModel;
using System.IO;
using System.Windows.Input;
using CatiaClient.Models;

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
        finally { IsLoading = false; }
    }

    /// <summary>
    /// 执行检出操作。调用 API 锁定零件，下载最新版本文件到临时目录，
    /// 然后在 CATIA 中自动打开该文件。
    /// </summary>
    private async void DoCheckoutAsync()
    {
        var result = await _api.CheckoutAsync(CurrentPart.Id);
        if (result != null)
        {
            CurrentPart = result;
            OnPropertyChanged(nameof(CurrentPart));
            // 下载最新版本文件到临时目录，然后在 CATIA 中打开
            if (Versions.Count > 0)
            {
                var tempDir = Path.Combine(Path.GetTempPath(), "catia_plm");
                Directory.CreateDirectory(tempDir);
                var latest = Versions[0];
                var ext = !string.IsNullOrEmpty(latest.FileType) ? $".{latest.FileType}" : "";
                var savePath = Path.Combine(tempDir, $"{CurrentPart.PartNumber}_{latest.VersionNumber}{ext}");
                await _api.DownloadVersionAsync(CurrentPart.Id, latest.Id, savePath);
                _catia.OpenDocument(savePath);
            }
        }
    }

    /// <summary>
    /// 执行检入操作。从 CATIA 获取当前打开的文档路径，保存文档后上传到服务器。
    /// 如果 CATIA 中没有打开的文档，弹出错误提示。
    /// </summary>
    private async void DoCheckinAsync()
    {
        var docPath = _catia.GetActiveDocumentPath();
        if (string.IsNullOrEmpty(docPath))
        {
            System.Windows.MessageBox.Show("CATIA 中没有打开的文档", "错误");
            return;
        }
        _catia.SaveDocument();
        var result = await _api.CheckinAsync(CurrentPart.Id, docPath);
        if (result != null)
        {
            CurrentPart = result;
            OnPropertyChanged(nameof(CurrentPart));
            await LoadData();
        }
    }

    /// <summary>
    /// 执行发布操作，将零件状态从"已检入"变更为"已发布"。
    /// </summary>
    private async void DoPublishAsync()
    {
        var result = await _api.PublishAsync(CurrentPart.Id);
        if (result != null)
        {
            CurrentPart = result;
            OnPropertyChanged(nameof(CurrentPart));
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
