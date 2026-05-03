using System.Collections.ObjectModel;
using System.Windows.Input;
using CatiaClient.Models;

namespace CatiaClient.ViewModels;

/// <summary>
/// 零件列表页面 ViewModel，展示所有零件并支持搜索。
/// 登录成功后显示此页面，可选择零件进入详情页。
/// </summary>
public class PartsViewModel : ViewModelBase
{
    private readonly Services.ApiClient _api;
    private readonly Services.CatiaService _catia;
    private readonly Action<Part> _onPartSelected;
    private readonly Action _onLogout;
    private string _searchText = "";
    private bool _isLoading;

    /// <summary>
    /// 初始化零件列表 ViewModel，自动加载零件列表。
    /// </summary>
    /// <param name="api">API 客户端实例</param>
    /// <param name="catia">CATIA 服务实例</param>
    /// <param name="onPartSelected">选中零件时的回调</param>
    /// <param name="onLogout">退出登录回调</param>
    public PartsViewModel(Services.ApiClient api, Services.CatiaService catia, Action<Part> onPartSelected, Action onLogout)
    {
        _api = api;
        _catia = catia;
        _onPartSelected = onPartSelected;
        _onLogout = onLogout;
        Parts = new ObservableCollection<Part>();
        SearchCommand = new RelayCommand(async () => await LoadParts());
        RefreshCommand = new RelayCommand(async () => await LoadParts());
        LogoutCommand = new RelayCommand(() => _onLogout());
        NewPartCommand = new RelayCommand(OpenNewPartDialog);
        _ = LoadParts();
    }

    /// <summary>零件列表，绑定到 UI 列表控件</summary>
    public ObservableCollection<Part> Parts { get; }

    /// <summary>搜索关键词，支持按名称或编号模糊搜索</summary>
    public string SearchText { get => _searchText; set => SetProperty(ref _searchText, value); }

    /// <summary>是否正在加载中</summary>
    public bool IsLoading { get => _isLoading; set => SetProperty(ref _isLoading, value); }

    /// <summary>搜索命令，根据 SearchText 过滤零件</summary>
    public ICommand SearchCommand { get; }

    /// <summary>刷新命令，重新加载零件列表</summary>
    public ICommand RefreshCommand { get; }

    /// <summary>退出登录命令</summary>
    public ICommand LogoutCommand { get; }

    /// <summary>新建零件命令，打开创建对话框</summary>
    public ICommand NewPartCommand { get; }

    /// <summary>
    /// 选中指定零件，触发回调导航到详情页。
    /// </summary>
    /// <param name="part">选中的零件</param>
    public void SelectPart(Part part) => _onPartSelected(part);

    /// <summary>
    /// 打开新建零件对话框。创建成功后提示用户选择文件导入，然后自动刷新零件列表。
    /// </summary>
    private void OpenNewPartDialog()
    {
        Views.UploadDialog? dialog = null;
        var vm = new UploadViewModel(_api,
            onCancel: () => { dialog?.Close(); },
            onCreated: part =>
            {
                dialog?.Close();
                // 创建成功后提示用户选择 CATIA 文件导入
                var result = System.Windows.MessageBox.Show(
                    $"零件 {part.PartNumber} 创建成功！\n\n是否立即选择文件导入到系统？",
                    "导入文件", System.Windows.MessageBoxButton.YesNo, System.Windows.MessageBoxImage.Question);
                if (result == System.Windows.MessageBoxResult.Yes)
                {
                    ImportFileForPart(part);
                }
                _ = LoadParts();
            });
        dialog = new Views.UploadDialog { DataContext = vm, Owner = System.Windows.Application.Current.MainWindow };
        dialog.ShowDialog();
    }

    /// <summary>
    /// 为指定零件导入文件：弹出文件选择对话框，用户选择本地 CATIA 文件后检入到系统。
    /// </summary>
    private async void ImportFileForPart(Part part)
    {
        var dlg = new Microsoft.Win32.OpenFileDialog
        {
            Title = "选择要导入的 CATIA 文件",
            Filter = "CATIA 文件 (*.CATPart;*.CATProduct)|*.CATPart;*.CATProduct|STEP 文件 (*.step;*.stp)|*.step;*.stp|所有文件 (*.*)|*.*"
        };
        if (dlg.ShowDialog() == true)
        {
            try
            {
                // 先检出再检入，完成文件导入
                await _api.CheckoutAsync(part.Id);
                var (updated, error) = await _api.CheckinAsync(part.Id, dlg.FileName, "初始导入");
                if (updated != null)
                    System.Windows.MessageBox.Show($"文件导入成功！零件 {updated.PartNumber} 已更新。", "成功");
                else
                    System.Windows.MessageBox.Show($"文件导入失败: {error}", "错误");
            }
            catch (Exception ex)
            {
                System.Windows.MessageBox.Show($"导入失败: {ex.Message}", "错误");
            }
        }
    }

    /// <summary>
    /// 从服务器加载零件列表。支持按 SearchText 进行模糊搜索。
    /// </summary>
    private async Task LoadParts()
    {
        IsLoading = true;
        try
        {
            var parts = await _api.GetPartsAsync(SearchText);
            Parts.Clear();
            foreach (var p in parts) Parts.Add(p);
        }
        catch (Exception ex)
        {
            System.Windows.MessageBox.Show($"加载零件列表失败: {ex.Message}", "错误");
        }
        finally { IsLoading = false; }
    }
}
