import re

from markdown2 import Extra, FencedCodeBlocks, Latex, Stage


class Latex2(Latex):
    """
    Convert \\( \\) and \\[ \\] to <math> and </math> tags for inline and block math.
    """

    name = "latex2"
    _single_dollar_re = re.compile(r"\\\((.*?)\\\)")
    _double_dollar_re = re.compile(r"\\\[(.*?)\\\]", re.DOTALL)


Latex2.register()


class FencedCodeBlocks2(FencedCodeBlocks):
    """
    patch fenced-code-blocks to treat EOF as closing fence to better format streaming document
    """

    name = "fenced-code-blocks2"

    fenced_code_block_re = re.compile(
        r"""
        (?:\n+|\A\n?|(?<=\n))
        (^[ \t]*`{3,})\s{0,99}?([\w+-]+)?\s{0,99}?\n  # $1 = opening fence (captured for back-referencing), $2 = optional lang
        (.*?)                             # $3 = code block content
        (\1[ \t]*\n|\Z)                      # closing fence or EOF
        """,
        re.M | re.X | re.S,
    )

    def _code_block_with_lexer_sub(
        self, codeblock: str, leading_indent: str, lexer
    ) -> str:
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

        # add back the indent to all lines
        return "\n%s\n" % self.md._uniform_indent(colored, leading_indent, True)


FencedCodeBlocks2.register()

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
    ui.markdown(text, extras=["latex2", "fenced-code-blocks2"])

    ui.run()
