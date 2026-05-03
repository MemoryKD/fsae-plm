using System.Runtime.InteropServices;

namespace FSAE_PLM.Models;

/// <summary>
/// COM-visible data transfer objects for the PLM add-in.
/// All classes use AutoDual so VBS can access properties via late binding.
/// </summary>

[ComVisible(true)]
[ClassInterface(ClassInterfaceType.AutoDual)]
[Guid("C1A2B3D4-E5F6-4A7B-8C9D-0E1F2A3B4C5D")]
public class PartInfo
{
    public Guid Id { get; set; }
    public string PartNumber { get; set; } = "";
    public string Name { get; set; } = "";
    public string Type { get; set; } = "part";
    public string? Subsystem { get; set; }
    public string? CurrentVersion { get; set; }
    public string LifecycleState { get; set; } = "";
    public string CheckState { get; set; } = "";
    public string? BranchName { get; set; }
    public Guid? DerivedFromId { get; set; }
    public DateTime? BranchCreatedAt { get; set; }
    public Guid? CreatedBy { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }

    public PartInfo() { }
}

[ComVisible(true)]
[ClassInterface(ClassInterfaceType.AutoDual)]
[Guid("D2B3C4E5-F6A7-4B8C-9D0E-1F2A3B4C5D6E")]
public class VersionInfo
{
    public Guid Id { get; set; }
    public string VersionNumber { get; set; } = "";
    public string? FileType { get; set; }
    public long? FileSize { get; set; }
    public string? Comment { get; set; }
    public DateTime CreatedAt { get; set; }

    public VersionInfo() { }
}

[ComVisible(true)]
[ClassInterface(ClassInterfaceType.AutoDual)]
[Guid("E3C4D5F6-A7B8-4C9D-0E1F-2A3B4C5D6E7F")]
public class TemplateInfo
{
    public Guid Id { get; set; }
    public string Name { get; set; } = "";
    public string? Prefix { get; set; }
    public string Separator { get; set; } = "-";
    public Dictionary<string, string> SubsystemCodes { get; set; } = new();
    public Dictionary<string, string> TypeCodes { get; set; } = new();

    public TemplateInfo() { }
}

[ComVisible(true)]
[ClassInterface(ClassInterfaceType.AutoDual)]
[Guid("F4D5E6A7-B8C9-4D0E-1F2A-3B4C5D6E7F80")]
public class BomItemInfo
{
    public Guid PartId { get; set; }
    public string PartNumber { get; set; } = "";
    public string Name { get; set; } = "";
    public int Quantity { get; set; } = 1;
    public int Level { get; set; } = 0;

    public BomItemInfo() { }
}
