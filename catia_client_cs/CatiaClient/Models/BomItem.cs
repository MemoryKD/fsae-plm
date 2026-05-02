namespace CatiaClient.Models;

/// <summary>
/// BOM（物料清单）条目，描述总成与子零件之间的装配关系。
/// </summary>
public class BomItem
{
    /// <summary>BOM 条目唯一标识符</summary>
    public Guid Id { get; set; }

    /// <summary>所属总成零件 ID</summary>
    public Guid AssemblyId { get; set; }

    /// <summary>子零件 ID</summary>
    public Guid PartId { get; set; }

    /// <summary>装配数量，默认为 1</summary>
    public int Quantity { get; set; } = 1;

    /// <summary>BOM 层级深度，0 表示直接子项</summary>
    public int Level { get; set; } = 0;

    /// <summary>创建时间</summary>
    public DateTime CreatedAt { get; set; }
}
