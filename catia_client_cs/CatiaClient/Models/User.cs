namespace CatiaClient.Models;

/// <summary>
/// 用户数据模型，对应 PLM 系统中的用户实体。
/// </summary>
public class User
{
    /// <summary>用户唯一标识符</summary>
    public Guid Id { get; set; }

    /// <summary>登录用户名</summary>
    public string Username { get; set; } = "";

    /// <summary>用户真实姓名</summary>
    public string? FullName { get; set; }

    /// <summary>用户角色（如 admin、member）</summary>
    public string? Role { get; set; }
}
