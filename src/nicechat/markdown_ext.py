import re

from markdown2 import FencedCodeBlocks, Latex


class Latex2(Latex):
    """
    Convert \\( \\) and \\[ \\] to <math> and </math> tags for inline and block math.
    """

    name = "latex2"
    _single_dollar_re = re.compile(r"\\\((.*?)\\\)")
    _double_dollar_re = re.compile(r"\\\[(.*?)\\\]", re.DOTALL)


Latex2.register()


def _code_block_with_lexer_sub(self, codeblock: str, leading_indent: str, lexer) -> str:
    """
    Args:
        codeblock: the codeblock to format
        leading_indent: the indentation to prefix the block with
        lexer (pygments.Lexer): the lexer to use
    """
    formatter_opts = self.md.extras[self.name] or {}

    def unhash_code(codeblock):
        for key, sanitized in list(self.md.html_spans.items()):
            codeblock = codeblock.replace(key, sanitized)
        replacements = [("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">")]
        for old, new in replacements:
            codeblock = codeblock.replace(old, new)
        return codeblock

    # remove leading indent from code block
    _, codeblock = self.md._uniform_outdent(codeblock, max_outdent=leading_indent)

    codeblock = unhash_code(codeblock)
    colored = self.md._color_with_pygments(codeblock, lexer, **formatter_opts)

    # Wrap in container with copy and save buttons
    return f"""
<div class="code-block-container">
{self.md._uniform_indent(colored, leading_indent, True)}
<div class="code-buttons">
    <button class="copy-button" onclick="navigator.clipboard.writeText(this.parentNode.parentNode.querySelector('pre').textContent).then(() => {{
        const toast = document.createElement('div');
        toast.textContent = 'Copied';
        toast.className = 'text-xs text-gray-500';
        toast.style.position = 'absolute';
        toast.style.top = '0em';
        toast.style.right = '3.5em';
        toast.style.padding = '4px 8px';
        toast.style.borderRadius = '4px';
        toast.style.zIndex = '1';
        this.parentNode.appendChild(toast);
        setTimeout(() => toast.remove(), 1000);
    }})">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
        </svg>
    </button>
    <button class="save-button" onclick="(() => {{
        const code = this.parentNode.parentNode.querySelector('pre').textContent;
        const blob = new Blob([code], {{type: 'text/plain'}});
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `code.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }})()">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="7 10 12 15 17 10"></polyline>
            <line x1="12" y1="15" x2="12" y2="3"></line>
        </svg>
    </button>
</div>
</div>
"""  # noqa


FencedCodeBlocks.fenced_code_block_re = re.compile(
    r"""
        (?:\n+|\A\n?|(?<=\n))
        (^[ \t]*`{3,})\s{0,99}?([\w+-]+)?\s{0,99}?\n  # $1 = opening fence (captured for back-referencing), $2 = optional lang
        (.*?)                             # $3 = code block content
        (\1[ \t]*\n|\Z)                      # closing fence or EOF
        """,  # noqa
    re.M | re.X | re.S,
)
FencedCodeBlocks._code_block_with_lexer_sub = _code_block_with_lexer_sub

if __name__ in {"__main__", "__mp_main__"}:
    from nicegui import ui

    text = r"""
\[
x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}
\]
\(x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}\)

```python
def test():
  pass
"""
    ui.markdown(text, extras=["latex2", "fenced-code-blocks", "mermaid"])

    ui.run()
