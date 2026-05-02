using System.Runtime.InteropServices;
using CatiaClient.Models;

namespace CatiaClient.Services;

/// <summary>
/// CATIA COM 自动化服务，通过 P/Invoke 和动态 COM 互操作与正在运行的 CATIA 进程通信。
/// 提供文档操作、自定义属性读写、缩略图捕获等功能。
/// </summary>
public class CatiaService
{
    /// <summary>CATIA Application COM 对象，通过 dynamic 类型实现后期绑定调用</summary>
    private dynamic? _catia;

    /// <summary>
    /// P/Invoke 声明：获取已运行的 COM 对象实例。
    /// oleaut32.dll 中的 GetActiveObject 根据 CLSID 查找已注册的运行中 COM 对象。
    /// PreserveSig = false 表示失败时抛出异常而非返回 HRESULT。
    /// </summary>
    [DllImport("oleaut32.dll", PreserveSig = false)]
    private static extern void GetActiveObject(
        [MarshalAs(UnmanagedType.LPStruct)] Guid rclsid,
        IntPtr pvReserved,
        [MarshalAs(UnmanagedType.IUnknown)] out object ppunk);

    /// <summary>
    /// P/Invoke 声明：将 ProgID（如 "CATIA.Application"）转换为 CLSID。
    /// ole32.dll 中的 CLSIDFromProgID 是 COM 基础设施函数。
    /// </summary>
    [DllImport("ole32.dll")]
    private static extern int CLSIDFromProgID(
        [MarshalAs(UnmanagedType.LPWStr)] string progId,
        out Guid clsid);

    /// <summary>
    /// 获取已运行的 COM 对象实例。先将 ProgID 转为 CLSID，再查找运行中的对象。
    /// 如果 CATIA 未运行，GetActiveObject 会抛出异常，此时返回 null。
    /// </summary>
    /// <param name="progId">COM 应用程序的 ProgID（如 "CATIA.Application"）</param>
    /// <returns>COM 对象实例，未找到返回 null</returns>
    private static object? GetActiveComObject(string progId)
    {
        CLSIDFromProgID(progId, out var clsid);
        try
        {
            GetActiveObject(clsid, IntPtr.Zero, out var obj);
            return obj;
        }
        catch
        {
            return null;
        }
    }

    /// <summary>是否已连接到 CATIA 进程</summary>
    public bool IsConnected => _catia != null;

    /// <summary>
    /// 连接到已运行的 CATIA 进程。CATIA 必须已启动，否则连接失败。
    /// 通过 COM 的 GetActiveObject 获取 CATIA Application 对象。
    /// </summary>
    /// <returns>连接成功返回 true</returns>
    public bool Connect()
    {
        try
        {
            _catia = GetActiveComObject("CATIA.Application");
            return _catia != null;
        }
        catch
        {
            return false;
        }
    }

    /// <summary>
    /// 获取 CATIA 当前活动文档的名称（不含路径）。
    /// </summary>
    /// <returns>文档名称，无活动文档返回 null</returns>
    public string? GetActiveDocumentName()
    {
        try { return _catia?.ActiveDocument?.Name; }
        catch { return null; }
    }

    /// <summary>
    /// 获取 CATIA 当前活动文档的完整文件路径。
    /// </summary>
    /// <returns>文件完整路径，无活动文档返回 null</returns>
    public string? GetActiveDocumentPath()
    {
        try { return _catia?.ActiveDocument?.FullName; }
        catch { return null; }
    }

    /// <summary>
    /// 读取 CATIA 当前活动文档的所有自定义属性（UserRefProperties）。
    /// CATIA 的 UserRefProperties 集合索引从 1 开始（非 0）。
    /// </summary>
    /// <returns>属性名-值字典，无文档时返回空字典</returns>
    public Dictionary<string, string> GetCustomProperties()
    {
        var props = new Dictionary<string, string>();
        try
        {
            if (_catia?.ActiveDocument == null) return props;
            var userRefs = _catia.ActiveDocument.UserRefProperties;
            // CATIA COM 集合索引从 1 开始
            for (int i = 1; i <= userRefs.Count; i++)
            {
                var prop = userRefs.Item(i);
                props[prop.Name] = prop.Value?.ToString() ?? "";
            }
        }
        catch { }
        return props;
    }

    /// <summary>
    /// 设置 CATIA 当前活动文档的指定自定义属性值。
    /// 如果属性不存在，CATIA 会抛出异常（静默忽略）。
    /// </summary>
    /// <param name="name">属性名称</param>
    /// <param name="value">属性值</param>
    public void SetCustomProperty(string name, string value)
    {
        try
        {
            if (_catia?.ActiveDocument == null) return;
            _catia.ActiveDocument.UserRefProperties.Item(name).Value = value;
        }
        catch { }
    }

    /// <summary>
    /// 将 PLM 零件属性同步到 CATIA 文档的自定义属性中。
    /// 写入 PLM_PartNumber、PLM_Name、PLM_Version、PLM_State 四个属性。
    /// </summary>
    /// <param name="part">PLM 零件数据</param>
    public void SyncPlmProperties(Part part)
    {
        SetCustomProperty("PLM_PartNumber", part.PartNumber);
        SetCustomProperty("PLM_Name", part.Name);
        SetCustomProperty("PLM_Version", part.CurrentVersion ?? "");
        SetCustomProperty("PLM_State", part.LifecycleState);
    }

    /// <summary>
    /// 捕获 CATIA 当前活动文档的缩略图。通过 ExportData 导出为 BMP 格式。
    /// width 和 height 参数当前未使用，ExportData 按 CATIA 默认分辨率导出。
    /// </summary>
    /// <param name="savePath">缩略图保存路径</param>
    /// <param name="width">期望宽度（当前未生效）</param>
    /// <param name="height">期望高度（当前未生效）</param>
    /// <returns>保存路径，失败返回 null</returns>
    public string? CaptureThumbnail(string savePath, int width = 800, int height = 600)
    {
        try
        {
            if (_catia?.ActiveDocument == null) return null;
            _catia.ActiveDocument.ExportData(savePath, "bmp");
            return savePath;
        }
        catch { return null; }
    }

    /// <summary>
    /// 保存 CATIA 当前活动文档。
    /// </summary>
    public void SaveDocument()
    {
        try { _catia?.ActiveDocument?.Save(); }
        catch { }
    }

    /// <summary>
    /// 在 CATIA 中打开指定路径的文档。
    /// </summary>
    /// <param name="filePath">文档文件的完整路径</param>
    public void OpenDocument(string filePath)
    {
        try { _catia?.Documents?.Open(filePath); }
        catch { }
    }
}
