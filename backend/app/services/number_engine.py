"""
零件号生成引擎 - 根据模板规则自动生成唯一零件号

零件号格式：PREFIX-TYPE_CODE-SUBSYSTEM-SEQUENCE
示例：FSAE-PRT-ENG-001, FSAE-ASM-CHS-012

各段含义：
- PREFIX：项目前缀（如 FSAE）
- TYPE_CODE：类型代码（PRT=零件, ASM=装配体, DOC=文档）
- SUBSYSTEM：子系统代码（如 ENG=动力, CHS=底盘）
- SEQUENCE：序号，零填充（如 001, 012）
"""
import re


class NumberEngine:
    """零件号生成器，根据模板配置生成符合规则的零件编号"""

    def __init__(self, prefix: str, separator: str = "-", digit_count: int = 3):
        self.prefix = prefix
        self.separator = separator
        # 序号零填充位数，如 3 表示 001、012
        self.digit_count = digit_count

    def generate(self, subsystem_code: str, sequence: int, type_code: str = "") -> str:
        """生成零件号：将各段拼接，序号零填充到指定位数"""
        seq_str = str(sequence).zfill(self.digit_count)
        # 过滤空值段后用分隔符拼接
        parts = [p for p in [self.prefix, type_code, subsystem_code, seq_str] if p]
        return self.separator.join(parts)

    def validate(self, part_number: str) -> bool:
        """验证零件号是否符合当前模板的格式规则"""
        prefix_escaped = re.escape(self.prefix)
        sep_escaped = re.escape(self.separator)
        pattern = rf"^{prefix_escaped}{sep_escaped}[A-Z]{{2,5}}{sep_escaped}\d{{{self.digit_count}}}$"
        return bool(re.match(pattern, part_number))

    @classmethod
    def from_template(cls, template) -> "NumberEngine":
        """从 PartNumberTemplate 模型实例创建引擎"""
        return cls(
            prefix=template.prefix or "",
            separator=template.separator or "-",
            digit_count=template.digit_count or 3,
        )
