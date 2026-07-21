import html
import re

RULES = [
    (re.compile(r'\*\*`([^`]+)`\*\*'), r'`\1`'),
]

_MERMAID_BLOCK_RE = re.compile(r'```mermaid\s*\n(.*?)\n?```', re.DOTALL)


def _preprocess_mermaid(content: str) -> str:
    if not _MERMAID_BLOCK_RE.search(content):
        return content

    content = _MERMAID_BLOCK_RE.sub(
        lambda m: '<div class="mermaid">\n'
        + html.escape(m.group(1), quote=False)
        + '\n</div>',
        content,
    )

    prefix = '<script src="/js/mermaid.min.js"></script>\n'
    suffix = '\n<script>mermaid.initialize({ startOnLoad: true });</script>\n'

    first_div = content.find('<div class="mermaid">')
    if first_div >= 0:
        content = content[:first_div] + prefix + content[first_div:]

    content += suffix
    return content


def preprocess(content: str) -> str:
    for pattern, replacement in RULES:
        content = pattern.sub(replacement, content)
    content = _preprocess_mermaid(content)
    return content
