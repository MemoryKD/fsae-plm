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

    /// <summary>
    /// 选中指定零件，触发回调导航到详情页。
    /// </summary>
    /// <param name="part">选中的零件</param>
    public void SelectPart(Part part) => _onPartSelected(part);

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
        finally { IsLoading = false; }
    }
}
