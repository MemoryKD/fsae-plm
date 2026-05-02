using System.Windows.Input;

namespace CatiaClient.ViewModels;

/// <summary>
/// 用户注册页面 ViewModel，处理新用户注册逻辑。
/// 注册后需等待管理员审批才能登录。
/// </summary>
public class RegisterViewModel : ViewModelBase
{
    private readonly Services.ApiClient _api;
    private readonly Action _onBack;
    private string _username = "";
    private string _password = "";
    private string _fullName = "";
    private string _department = "";
    private string _joinYear = "";
    private string _phone = "";
    private string _errorMessage = "";
    private string _successMessage = "";
    private bool _isLoading;

    /// <summary>
    /// 初始化注册 ViewModel。
    /// </summary>
    /// <param name="api">API 客户端实例</param>
    /// <param name="onBack">返回登录页回调</param>
    public RegisterViewModel(Services.ApiClient api, Action onBack)
    {
        _api = api;
        _onBack = onBack;
        RegisterCommand = new RelayCommand(RegisterAsync, () => !IsLoading);
        BackCommand = new RelayCommand(() => _onBack());
    }

    /// <summary>用户名</summary>
    public string Username { get => _username; set => SetProperty(ref _username, value); }

    /// <summary>密码</summary>
    public string Password { get => _password; set => SetProperty(ref _password, value); }

    /// <summary>真实姓名</summary>
    public string FullName { get => _fullName; set => SetProperty(ref _fullName, value); }

    /// <summary>所属部门（如悬架组、转向组）</summary>
    public string Department { get => _department; set => SetProperty(ref _department, value); }

    /// <summary>入队年份</summary>
    public string JoinYear { get => _joinYear; set => SetProperty(ref _joinYear, value); }

    /// <summary>联系电话</summary>
    public string Phone { get => _phone; set => SetProperty(ref _phone, value); }

    /// <summary>错误提示信息</summary>
    public string ErrorMessage { get => _errorMessage; set => SetProperty(ref _errorMessage, value); }

    /// <summary>成功提示信息</summary>
    public string SuccessMessage { get => _successMessage; set => SetProperty(ref _successMessage, value); }

    /// <summary>是否正在加载中</summary>
    public bool IsLoading { get => _isLoading; set => SetProperty(ref _isLoading, value); }

    /// <summary>注册命令</summary>
    public ICommand RegisterCommand { get; }

    /// <summary>返回登录页命令</summary>
    public ICommand BackCommand { get; }

    /// <summary>
    /// 执行注册操作。空白字段传 null 以使用服务端默认值。
    /// 注册成功后显示等待审批提示，失败显示错误信息。
    /// </summary>
    private async void RegisterAsync()
    {
        IsLoading = true;
        ErrorMessage = "";
        SuccessMessage = "";
        try
        {
            var (success, error) = await _api.RegisterAsync(Username, Password, FullName,
                string.IsNullOrWhiteSpace(Department) ? null : Department,
                string.IsNullOrWhiteSpace(JoinYear) ? null : JoinYear,
                string.IsNullOrWhiteSpace(Phone) ? null : Phone);
            if (success)
                SuccessMessage = "注册成功！请等待管理员审批后即可登录。";
            else
                ErrorMessage = error;
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
