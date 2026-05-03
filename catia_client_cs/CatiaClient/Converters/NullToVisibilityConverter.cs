using System.Globalization;
using System.Windows;
using System.Windows.Data;

namespace CatiaClient.Converters;

/// <summary>
/// 将 null 值转换为 Visibility 枚举。
/// null → Collapsed，非 null → Visible。
/// 用于在 XAML 中根据属性是否为 null 来显示/隐藏 UI 元素。
/// </summary>
public class NullToVisibilityConverter : IValueConverter
{
    /// <summary>
    /// 将值转换为 Visibility。null 或空字符串返回 Collapsed，否则返回 Visible。
    /// </summary>
    public object Convert(object? value, Type targetType, object? parameter, CultureInfo culture)
    {
        if (value == null) return Visibility.Collapsed;
        if (value is string s && string.IsNullOrEmpty(s)) return Visibility.Collapsed;
        return Visibility.Visible;
    }

    /// <summary>
    /// 反向转换（未实现，抛出 NotSupportedException）。
    /// </summary>
    public object ConvertBack(object? value, Type targetType, object? parameter, CultureInfo culture)
    {
        throw new NotSupportedException();
    }
}
