import re
import subprocess
from pathlib import Path
import unittest


TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "template.html"


class HighlightTemplateTests(unittest.TestCase):
    def test_markable_text_segment_rejects_whitespace_only_fragments(self):
        template = TEMPLATE_PATH.read_text(encoding="utf-8")
        match = re.search(
            r"function isMarkableTextSegment\(text\) \{.*?\n\}",
            template,
            flags=re.S,
        )
        self.assertIsNotNone(match, "template should define isMarkableTextSegment")
        self.assertIn(
            "if (!isMarkableTextSegment(middle)) return;",
            template,
            "wrapRangeWithMark should skip whitespace-only text fragments",
        )

        script = (
            match.group(0)
            + """
const cases = [
  ["", false],
  ["\\n", false],
  ["   \\n\\t", false],
  ["\\u00a0", false],
  ["这句要标注", true],
  ["  grade-ai-draft  ", true],
];
for (const [input, expected] of cases) {
  const actual = isMarkableTextSegment(input);
  if (actual !== expected) {
    throw new Error(`${JSON.stringify(input)} expected ${expected} got ${actual}`);
  }
}
"""
        )
        subprocess.run(["node", "-e", script], check=True)


if __name__ == "__main__":
    unittest.main()
