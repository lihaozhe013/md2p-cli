import re

RULES = [
    # **`code`** → `code`  strip invalid bold wrapping inline code
    (re.compile(r'\*\*`([^`]+)`\*\*'), r'`\1`'),
]


def preprocess(content: str) -> str:
    for pattern, replacement in RULES:
        content = pattern.sub(replacement, content)
    return content
