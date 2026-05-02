using System.Windows.Input;

namespace CatiaClient.ViewModels;

/// <summary>
/// 通用命令实现，将 ICommand 接口委托给 Action/Func 委托。
/// 用于将 XAML 控件的命令绑定（如 Button.Command）连接到 ViewModel 中的方法。
/// 支持两种构造方式：无参 Action 和带参数 Action&lt;object?&gt;。
/// </summary>
public class RelayCommand : ICommand
{
    private readonly Action<object?>? _execute;
    private readonly Func<bool>? _canExecute;
    private readonly Action? _simpleExecute;

    /// <summary>
    /// 使用无参委托构造命令。
    /// </summary>
    /// <param name="execute">命令执行时调用的方法</param>
    /// <param name="canExecute">判断命令是否可执行的回调，为 null 时始终可执行</param>
    public RelayCommand(Action execute, Func<bool>? canExecute = null)
    {
        _simpleExecute = execute;
        _canExecute = canExecute;
    }

    /// <summary>
    /// 使用带参数委托构造命令。
    /// </summary>
    /// <param name="execute">命令执行时调用的方法，接收命令参数</param>
    /// <param name="canExecute">判断命令是否可执行的回调，为 null 时始终可执行</param>
    public RelayCommand(Action<object?> execute, Func<bool>? canExecute = null)
    {
        _execute = execute;
        _canExecute = canExecute;
    }

    /// <summary>
    /// 当命令可执行状态变化时触发的事件。
    /// 绑定到 CommandManager.RequerySuggested 以自动响应 UI 状态变化。
    /// </summary>
    public event EventHandler? CanExecuteChanged
    {
        add => CommandManager.RequerySuggested += value;
        remove => CommandManager.RequerySuggested -= value;
    }

    /// <summary>
    /// 判断命令当前是否可执行。
    /// </summary>
    /// <param name="parameter">命令参数（未使用）</param>
    /// <returns>可执行返回 true，否则返回 false</returns>
    public bool CanExecute(object? parameter) => _canExecute?.Invoke() ?? true;

    /// <summary>
    /// 执行命令。
    /// </summary>
    /// <param name="parameter">命令参数，传递给带参数的委托</param>
    public void Execute(object? parameter)
    {
        _simpleExecute?.Invoke();
        _execute?.Invoke(parameter);
    }
}
