using System.Windows.Input;

namespace CatiaClient.ViewModels;

/// <summary>
/// 登录页面 ViewModel，处理用户登录逻辑。
/// 支持自定义服务器地址、用户名密码登录，登录成功后回调导航。
/// </summary>
public class LoginViewModel : ViewModelBase
{
    private readonly Services.ApiClient _api;
    private readonly Action _onSuccess;
    private readonly Action _onRegister;
    private string _username = "";
    private string _password = "";
    private string _serverUrl = "http://localhost/api";
    private string _errorMessage = "";
    private bool _isLoading;

    /// <summary>
    /// 初始化登录 ViewModel。
    /// </summary>
    /// <param name="api">API 客户端实例</param>
    /// <param name="onSuccess">登录成功回调</param>
    /// <param name="onRegister">点击注册按钮回调</param>
    public LoginViewModel(Services.ApiClient api, Action onSuccess, Action onRegister)
    {
        _api = api;
        _onSuccess = onSuccess;
        _onRegister = onRegister;
        LoginCommand = new RelayCommand(LoginAsync, () => !IsLoading);
        RegisterCommand = new RelayCommand(() => _onRegister());
    }

    /// <summary>用户名</summary>
    public string Username { get => _username; set => SetProperty(ref _username, value); }

    /// <summary>密码</summary>
    public string Password { get => _password; set => SetProperty(ref _password, value); }

    /// <summary>服务器地址，可自定义后端 API 地址</summary>
    public string ServerUrl { get => _serverUrl; set => SetProperty(ref _serverUrl, value); }

    /// <summary>错误提示信息，登录失败时显示</summary>
    public string ErrorMessage { get => _errorMessage; set => SetProperty(ref _errorMessage, value); }

    /// <summary>是否正在加载中，用于禁用按钮和显示加载状态</summary>
    public bool IsLoading { get => _isLoading; set => SetProperty(ref _isLoading, value); }

    /// <summary>登录命令</summary>
    public ICommand LoginCommand { get; }

    /// <summary>注册命令，导航到注册页面</summary>
    public ICommand RegisterCommand { get; }

    /// <summary>
    /// 执行登录操作。先更新 API 服务器地址，再调用登录接口。
    /// 登录成功触发 onSuccess 回调，失败显示错误信息。
    /// </summary>
    private async void LoginAsync()
    {
        IsLoading = true;
        ErrorMessage = "";
        try
        {
            _api.SetBaseUrl(ServerUrl);
            var success = await _api.LoginAsync(Username, Password);
            if (success) _onSuccess();
            else ErrorMessage = "登录失败，请检查用户名和密码";
        }
        catch (Exception ex)
        {
            ErrorMessage = $"连接失败: {ex.Message}";
        }
        finally
        {
            IsLoading = false;
        }
    }
}
