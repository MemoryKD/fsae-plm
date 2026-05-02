namespace CatiaClient.Models;

/// <summary>
/// 零件编号模板，定义编号生成规则。
/// 例如模板 "SUS" 可生成编号 "SUS-A-001"，其中 A 为子系统代码，001 为序号。
/// </summary>
public class Template
{
    /// <summary>模板唯一标识符</summary>
    public Guid Id { get; set; }

    /// <summary>模板名称（如悬架模板、转向模板）</summary>
    public string Name { get; set; } = "";

    /// <summary>编号前缀（如 SUS、STR）</summary>
    public string? Prefix { get; set; }

    /// <summary>编号各段之间的分隔符，默认为 "-"</summary>
    public string Separator { get; set; } = "-";

    /// <summary>序号位数，默认为 3（生成 001、002 等）</summary>
    public int DigitCount { get; set; } = 3;

    /// <summary>子系统名称到代码的映射（如 "悬架" -> "A"）</summary>
    public Dictionary<string, string> SubsystemCodes { get; set; } = new();

    /// <summary>零件类型到代码的映射（如 "零件" -> "P"、"总成" -> "A"）</summary>
    public Dictionary<string, string> TypeCodes { get; set; } = new();
}
