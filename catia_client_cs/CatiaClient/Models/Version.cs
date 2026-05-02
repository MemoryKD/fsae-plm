namespace CatiaClient.Models;

/// <summary>
/// 零件版本数据模型，记录每次检入产生的文件版本。
/// </summary>
public class PartVersion
{
    /// <summary>版本唯一标识符</summary>
    public Guid Id { get; set; }

    /// <summary>所属零件 ID</summary>
    public Guid PartId { get; set; }

    /// <summary>版本号（如 v1、v2）</summary>
    public string VersionNumber { get; set; } = "";

    /// <summary>文件在服务器上的存储路径</summary>
    public string? FilePath { get; set; }

    /// <summary>文件大小（字节）</summary>
    public long? FileSize { get; set; }

    /// <summary>文件类型/扩展名（如 CATPart、step）</summary>
    public string? FileType { get; set; }

    /// <summary>检入时填写的备注说明</summary>
    public string? Comment { get; set; }

    /// <summary>创建者用户 ID</summary>
    public Guid? CreatedBy { get; set; }

    /// <summary>版本创建时间</summary>
    public DateTime CreatedAt { get; set; }
}
