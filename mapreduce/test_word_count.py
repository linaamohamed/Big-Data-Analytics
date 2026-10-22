import tempfile
import unittest
from collections import Counter
from pathlib import Path
from word_count import run


class WordCountTest(unittest.TestCase):
    def test_cross_split_counts_and_output(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            root = Path(directory)
            source = root / "input"
            source.mkdir()
            (source / "one.txt").write_text("Cat cat, DOG!", encoding="utf-8")
            (source / "two.txt").write_text("dog cat 42", encoding="utf-8")
            (source / "empty.txt").write_text("", encoding="utf-8")
            (source / "expected_word_count.txt").write_text("ignored 99", encoding="utf-8")
            output = root / "output"
            self.assertEqual(run(source, output), {"cat": 3, "dog": 2, "42": 1})
            rows = []
            for file in sorted(output.glob("part-*.txt")):
                lines = file.read_text().splitlines()
                self.assertEqual(lines, sorted(lines))
                rows.extend(lines)
            self.assertEqual(len(list(output.glob("part-*.txt"))), 2)
            self.assertEqual(sorted(rows), ["42 1", "cat 3", "dog 2"])

    def test_repository_dataset_against_independent_count(self):
        source = Path(__file__).resolve().parents[1] / "datasets" / "text-files"
        expected = Counter()
        for file in source.glob("book_*.txt"):
            for token in file.read_text(encoding="utf-8").lower().split():
                expected[token.strip(".,!?;:")] += 1
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            self.assertEqual(run(source, Path(directory)), dict(expected))


if __name__ == "__main__":
    unittest.main()
