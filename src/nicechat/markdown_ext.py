import re

from markdown2 import Extra, FencedCodeBlocks, Stage


class Latex2(Extra):
    """
    Convert $ and $$ to <math> and </math> tags for inline and block math.
    """

    name = "latex2"
    order = (Stage.CODE_BLOCKS, FencedCodeBlocks), ()

    _inline_re = re.compile(r"\\\((.*?)\\\)")
    _block_re = re.compile(r"\\\[(.*?)\\\]", re.DOTALL)

    # Ways to escape
    _pre_code_block_re = re.compile(r"<pre>(.*?)</pre>", re.DOTALL)  # Wraped in <pre>
    _triple_re = re.compile(r"```(.*?)```", re.DOTALL)  # Wrapped in a code block ```
    _single_re = re.compile(r"(?<!`)(`)(.*?)(?<!`)\1(?!`)")  # Wrapped in a single `

    converter = None
    code_blocks = {}

    def _convert_single_match(self, match):
        return self.converter.convert(match.group(1))

    def _convert_double_match(self, match):
        return self.converter.convert(
            match.group(1).replace(r"\n", ""), display="block"
        )

    def code_placeholder(self, match):
        placeholder = f"<!--CODE_BLOCK_{len(self.code_blocks)}-->"
        self.code_blocks[placeholder] = match.group(0)
        return placeholder

    def run(self, text):
        try:
            import latex2mathml.converter

            self.converter = latex2mathml.converter
        except ImportError:
            raise ImportError(
                'The "latex" extra requires the "latex2mathml" package to be installed.'
            )

        # Escape by replacing with a code block
        text = self._pre_code_block_re.sub(self.code_placeholder, text)
        text = self._single_re.sub(self.code_placeholder, text)
        text = self._triple_re.sub(self.code_placeholder, text)

        text = self._inline_re.sub(self._convert_single_match, text)
        text = self._block_re.sub(self._convert_double_match, text)

        # Convert placeholder tag back to original code
        for placeholder, code_block in self.code_blocks.items():
            text = text.replace(placeholder, code_block)

        return text


Latex2.register()
