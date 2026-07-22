"""Small, dependency-free and safe Markdown renderer for task descriptions."""

import html
import re
from urllib.parse import urlparse

from markupsafe import Markup


_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
_CODE_PATTERN = re.compile(r"`([^`\n]+)`")
_UNORDERED_ITEM = re.compile(r"^\s*[-+*]\s+(.+)$")
_ORDERED_ITEM = re.compile(r"^\s*\d+[.)]\s+(.+)$")
_HEADING = re.compile(r"^(#{1,3})\s+(.+)$")
_TASK_ITEM = re.compile(r"^\[([ xX])\]\s+(.+)$")


def _safe_url(value):
    parsed = urlparse(value)
    if parsed.scheme in {"http", "https", "mailto"}:
        return value
    if not parsed.scheme and value.startswith(("/", "#")):
        return value
    return None


def _render_emphasis(value):
    value = html.escape(value, quote=False)
    value = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", value)
    value = re.sub(r"__(.+?)__", r"<strong>\1</strong>", value)
    value = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", value)
    value = re.sub(r"(?<!\w)_([^_\n]+)_(?!\w)", r"<em>\1</em>", value)
    value = re.sub(r"~~(.+?)~~", r"<del>\1</del>", value)
    return value


def _render_links(value):
    output = []
    position = 0
    for match in _LINK_PATTERN.finditer(value):
        output.append(_render_emphasis(value[position : match.start()]))
        label, target = match.groups()
        safe_target = _safe_url(target)
        if safe_target:
            output.append(
                '<a href="{}" rel="noopener noreferrer">{}</a>'.format(
                    html.escape(safe_target, quote=True),
                    _render_emphasis(label),
                )
            )
        else:
            output.append(_render_emphasis(match.group(0)))
        position = match.end()
    output.append(_render_emphasis(value[position:]))
    return "".join(output)


def _render_inline(value):
    output = []
    position = 0
    for match in _CODE_PATTERN.finditer(value):
        output.append(_render_links(value[position : match.start()]))
        output.append(f"<code>{html.escape(match.group(1), quote=False)}</code>")
        position = match.end()
    output.append(_render_links(value[position:]))
    return "".join(output)


def _starts_block(line):
    stripped = line.strip()
    return bool(
        stripped.startswith("```")
        or _HEADING.match(stripped)
        or stripped.startswith(">")
        or _UNORDERED_ITEM.match(line)
        or _ORDERED_ITEM.match(line)
    )


def _render_list_item(value):
    task_match = _TASK_ITEM.match(value)
    if not task_match:
        return f"<li>{_render_inline(value)}</li>"

    checked = task_match.group(1).lower() == "x"
    checked_attribute = " checked" if checked else ""
    return (
        '<li class="markdown-task-item">'
        f'<input type="checkbox" disabled{checked_attribute} aria-hidden="true">'
        f"<span>{_render_inline(task_match.group(2))}</span></li>"
    )


def render_markdown(value):
    """Render a useful Markdown subset while escaping all raw HTML."""
    if not value:
        return Markup("")

    lines = str(value).replace("\r\n", "\n").replace("\r", "\n").split("\n")
    blocks = []
    index = 0

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if not stripped:
            index += 1
            continue

        if stripped.startswith("```"):
            language = stripped[3:].strip()
            code_lines = []
            index += 1
            while index < len(lines) and not lines[index].strip().startswith("```"):
                code_lines.append(lines[index])
                index += 1
            if index < len(lines):
                index += 1
            language_class = ""
            if language and re.fullmatch(r"[A-Za-z0-9_-]+", language):
                language_class = f' class="language-{language}"'
            code = html.escape("\n".join(code_lines), quote=False)
            blocks.append(f"<pre><code{language_class}>{code}</code></pre>")
            continue

        heading = _HEADING.match(stripped)
        if heading:
            level = len(heading.group(1)) + 2
            blocks.append(f"<h{level}>{_render_inline(heading.group(2))}</h{level}>")
            index += 1
            continue

        if stripped.startswith(">"):
            quote_lines = []
            while index < len(lines) and lines[index].strip().startswith(">"):
                quote_lines.append(lines[index].strip()[1:].lstrip())
                index += 1
            blocks.append(f"<blockquote>{_render_inline(' '.join(quote_lines))}</blockquote>")
            continue

        unordered = _UNORDERED_ITEM.match(line)
        if unordered:
            items = []
            while index < len(lines):
                item = _UNORDERED_ITEM.match(lines[index])
                if not item:
                    break
                items.append(_render_list_item(item.group(1)))
                index += 1
            blocks.append(f"<ul>{''.join(items)}</ul>")
            continue

        ordered = _ORDERED_ITEM.match(line)
        if ordered:
            items = []
            while index < len(lines):
                item = _ORDERED_ITEM.match(lines[index])
                if not item:
                    break
                items.append(f"<li>{_render_inline(item.group(1))}</li>")
                index += 1
            blocks.append(f"<ol>{''.join(items)}</ol>")
            continue

        paragraph_lines = [stripped]
        index += 1
        while index < len(lines) and lines[index].strip() and not _starts_block(lines[index]):
            paragraph_lines.append(lines[index].strip())
            index += 1
        blocks.append(f"<p>{_render_inline(' '.join(paragraph_lines))}</p>")

    return Markup("\n".join(blocks))
    