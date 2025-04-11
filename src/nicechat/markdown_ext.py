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

if __name__ in {"__main__", "__mp_main__"}:
    from nicegui import ui

    ui.markdown(
        r"""
\[
x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}
\]
\(x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}\)
""",
        extras=["latex2"],
    )

    ui.run()
