using System.Windows.Input;
using CatiaClient.Models;

namespace CatiaClient.ViewModels;

/// <summary>
/// 智能创建零件页面 ViewModel，基于模板自动生成零件编号。
/// 用户选择模板、子系统和零件类型后，系统预览编号并一键创建零件。
/// </summary>
public class UploadViewModel : ViewModelBase
{
    private readonly Services.ApiClient _api;
    private readonly Action _onCancel;
    private readonly Action<Part> _onCreated;
    private string _name = "";
    private string _type = "part";
    private string _subsystem = "";
    private string _previewNumber = "";
    private Template? _selectedTemplate;
    private bool _isLoading;

    /// <summary>
    /// 初始化创建零件 ViewModel，自动加载可用模板列表。
    /// </summary>
    /// <param name="api">API 客户端实例</param>
    /// <param name="onCancel">取消创建回调</param>
    /// <param name="onCreated">创建成功回调，传递新创建的零件</param>
    public UploadViewModel(Services.ApiClient api, Action onCancel, Action<Part> onCreated)
    {
        _api = api;
        _onCancel = onCancel;
        _onCreated = onCreated;
        CancelCommand = new RelayCommand(() => _onCancel());
        CreateCommand = new RelayCommand(DoCreateAsync);
        _ = LoadTemplates();
    }

    /// <summary>可用模板列表</summary>
    public List<Template> Templates { get; private set; } = new();

    /// <summary>当前选中模板的子系统列表</summary>
    public List<string> Subsystems { get; private set; } = new();

    /// <summary>零件名称</summary>
    public string Name { get => _name; set => SetProperty(ref _name, value); }

    /// <summary>零件类型（part 或 assembly），变更时自动更新编号预览</summary>
    public string Type { get => _type; set { SetProperty(ref _type, value); _ = UpdatePreview(); } }

    /// <summary>所属子系统，变更时自动更新编号预览</summary>
    public string Subsystem { get => _subsystem; set { SetProperty(ref _subsystem, value); _ = UpdatePreview(); } }

    /// <summary>编号预览，展示将要生成的零件编号</summary>
    public string PreviewNumber { get => _previewNumber; set => SetProperty(ref _previewNumber, value); }

    /// <summary>是否正在加载中</summary>
    public bool IsLoading { get => _isLoading; set => SetProperty(ref _isLoading, value); }

    /// <summary>
    /// 选中的模板。选择后自动更新子系统列表和编号预览。
    /// </summary>
    public Template? SelectedTemplate
    {
        get => _selectedTemplate;
        set
        {
            SetProperty(ref _selectedTemplate, value);
            if (value != null)
            {
                Subsystems = value.SubsystemCodes.Keys.ToList();
                OnPropertyChanged(nameof(Subsystems));
            }
            _ = UpdatePreview();
        }
    }

    /// <summary>取消命令，返回上一页</summary>
    public ICommand CancelCommand { get; }

    /// <summary>创建命令，提交新零件到服务器</summary>
    public ICommand CreateCommand { get; }

    /// <summary>
    /// 从服务器加载可用的编号模板列表。
    /// </summary>
    private async Task LoadTemplates()
    {
        Templates = await _api.GetTemplatesAsync();
        OnPropertyChanged(nameof(Templates));
    }

    /// <summary>
    /// 根据当前选中的模板、子系统和类型，从服务器获取下一个可用编号并更新预览。
    /// </summary>
    private async Task UpdatePreview()
    {
        if (SelectedTemplate == null || string.IsNullOrEmpty(Subsystem))
        {
            PreviewNumber = "";
            return;
        }
        PreviewNumber = await _api.GetNextPartNumberAsync(SelectedTemplate.Id, Subsystem, Type) ?? "预览失败";
    }

    /// <summary>
    /// 执行创建零件操作。校验必填项后调用 API 创建零件。
    /// 创建成功触发 onCreated 回调，失败弹出错误提示。
    /// </summary>
    private async void DoCreateAsync()
    {
        if (SelectedTemplate == null || string.IsNullOrEmpty(Name))
        {
            System.Windows.MessageBox.Show("请填写名称并选择模板", "提示");
            return;
        }
        IsLoading = true;
        try
        {
            var part = await _api.CreateWithTemplateAsync(Name, Type, Subsystem, SelectedTemplate.Id);
            if (part != null) _onCreated(part);
            else System.Windows.MessageBox.Show("创建失败", "错误");
        }
        finally { IsLoading = false; }
    }
}
