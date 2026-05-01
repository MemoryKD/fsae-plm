import re


class NumberEngine:
    def __init__(self, prefix: str, separator: str = "-", digit_count: int = 3):
        self.prefix = prefix
        self.separator = separator
        self.digit_count = digit_count

    def generate(self, subsystem_code: str, sequence: int) -> str:
        seq_str = str(sequence).zfill(self.digit_count)
        parts = [p for p in [self.prefix, subsystem_code, seq_str] if p]
        return self.separator.join(parts)

    def validate(self, part_number: str) -> bool:
        prefix_escaped = re.escape(self.prefix)
        sep_escaped = re.escape(self.separator)
        pattern = rf"^{prefix_escaped}{sep_escaped}[A-Z]{{2,5}}{sep_escaped}\d{{{self.digit_count}}}$"
        return bool(re.match(pattern, part_number))

    @classmethod
    def from_template(cls, template) -> "NumberEngine":
        return cls(
            prefix=template.prefix or "",
            separator=template.separator or "-",
            digit_count=template.digit_count or 3,
        )
