namespace CatiaClient.Models;

/// <summary>
/// 零件数据模型，对应 PLM 系统中的零件实体。
/// 包含零件编号、版本、检入/检出状态、生命周期状态等核心信息。
/// </summary>
public class Part
{
    /// <summary>零件唯一标识符</summary>
    public Guid Id { get; set; }

    /// <summary>零件编号，由模板规则自动生成（如 SUS-A-001）</summary>
    public string PartNumber { get; set; } = "";

    /// <summary>零件名称</summary>
    public string Name { get; set; } = "";

    /// <summary>零件类型：part（零件）或 assembly（总成）</summary>
    public string Type { get; set; } = "part";

    /// <summary>所属子系统名称（如悬架、转向等）</summary>
    public string? Subsystem { get; set; }

    /// <summary>当前版本号</summary>
    public string? CurrentVersion { get; set; }

    /// <summary>工作流状态（如审批中、已驳回等）</summary>
    public string WorkflowState { get; set; } = "";

    /// <summary>生命周期状态：设计中、已检入、已发布等</summary>
    public string LifecycleState { get; set; } = "";

    /// <summary>检入/检出状态：检入（可检出）、检出（正在编辑）</summary>
    public string CheckState { get; set; } = "";

    /// <summary>当前检出用户的 ID，为空表示未被检出</summary>
    public Guid? CheckedOutBy { get; set; }

    /// <summary>缩略图文件路径</summary>
    public string? ThumbnailPath { get; set; }

    /// <summary>派生来源零件 ID（分支或复制时记录原始零件）</summary>
    public Guid? DerivedFromId { get; set; }

    /// <summary>分支名称</summary>
    public string? BranchName { get; set; }

    /// <summary>分支创建时间</summary>
    public DateTime? BranchCreatedAt { get; set; }

    /// <summary>创建者用户 ID</summary>
    public Guid? CreatedBy { get; set; }

    /// <summary>创建时间</summary>
    public DateTime CreatedAt { get; set; }

    /// <summary>最后更新时间</summary>
    public DateTime UpdatedAt { get; set; }
}
