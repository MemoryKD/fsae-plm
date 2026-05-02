using System.ComponentModel;
using System.Runtime.CompilerServices;

namespace CatiaClient.ViewModels;

/// <summary>
/// ViewModel 基类，实现 INotifyPropertyChanged 接口。
/// 所有 ViewModel 继承此类以获得属性变更通知能力，支持 WPF 数据绑定。
/// </summary>
public abstract class ViewModelBase : INotifyPropertyChanged
{
    /// <summary>属性变更事件，WPF 绑定引擎通过此事件监听属性变化并刷新 UI</summary>
    public event PropertyChangedEventHandler? PropertyChanged;

    /// <summary>
    /// 设置属性值并在值发生变化时触发 PropertyChanged 通知。
    /// 使用 CallerMemberName 自动获取调用方属性名，避免手写字符串。
    /// </summary>
    /// <typeparam name="T">属性类型</typeparam>
    /// <param name="field">属性的后备字段引用</param>
    /// <param name="value">要设置的新值</param>
    /// <param name="propertyName">属性名（由编译器自动填充）</param>
    /// <returns>值发生变化返回 true，未变化返回 false</returns>
    protected bool SetProperty<T>(ref T field, T value, [CallerMemberName] string? propertyName = null)
    {
        if (EqualityComparer<T>.Default.Equals(field, value)) return false;
        field = value;
        OnPropertyChanged(propertyName);
        return true;
    }

    /// <summary>
    /// 触发指定属性的 PropertyChanged 通知。
    /// </summary>
    /// <param name="propertyName">要通知的属性名</param>
    protected void OnPropertyChanged([CallerMemberName] string? propertyName = null)
    {
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
    }
}
