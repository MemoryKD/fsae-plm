using System.Windows.Input;

namespace CatiaClient.ViewModels;

/// <summary>
/// 主窗口 ViewModel，负责页面导航和全局服务实例管理。
/// 通过切换 CurrentView 实现登录、零件列表、零件详情等页面之间的导航。
/// </summary>
public class MainViewModel : ViewModelBase
{
    private ViewModelBase _currentView;
    private readonly Services.ApiClient _api;
    private readonly Services.CatiaService _catia;

    /// <summary>
    /// 初始化主窗口，创建 API 客户端和 CATIA 服务，连接 CATIA 并显示登录页面。
    /// </summary>
    public MainViewModel()
    {
        _api = new Services.ApiClient();
        _catia = new Services.CatiaService();
        _catia.Connect();
        _currentView = new LoginViewModel(_api, OnLoginSuccess, OnRegister);
    }

    /// <summary>
    /// 当前显示的 ViewModel，绑定到主窗口的 ContentControl。
    /// 切换此属性即可实现页面导航。
    /// </summary>
    public ViewModelBase CurrentView
    {
        get => _currentView;
        set => SetProperty(ref _currentView, value);
    }

    /// <summary>登录成功后导航到零件列表页面</summary>
    private void OnLoginSuccess()
    {
        CurrentView = new PartsViewModel(_api, _catia, OnPartSelected, OnLogout);
    }

    /// <summary>从登录页导航到注册页面</summary>
    private void OnRegister()
    {
        CurrentView = new RegisterViewModel(_api, OnBackToLogin);
    }

    /// <summary>从注册页返回登录页面</summary>
    private void OnBackToLogin()
    {
        CurrentView = new LoginViewModel(_api, OnLoginSuccess, OnRegister);
    }

    /// <summary>选中零件后导航到零件详情页面</summary>
    /// <param name="part">选中的零件</param>
    private void OnPartSelected(Models.Part part)
    {
        CurrentView = new PartDetailViewModel(_api, _catia, part, OnBack);
    }

    /// <summary>从详情页返回零件列表页面</summary>
    private void OnBack()
    {
        CurrentView = new PartsViewModel(_api, _catia, OnPartSelected, OnLogout);
    }

    /// <summary>退出登录，返回登录页面</summary>
    private void OnLogout()
    {
        CurrentView = new LoginViewModel(_api, OnLoginSuccess, OnRegister);
    }
}
