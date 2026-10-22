"""Small MapReduce simulation using only the Python standard library."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from itertools import groupby
from pathlib import Path
import re
import zlib


def mapper(path):
    """One input file is one split; emit (word, 1)."""
    text = path.read_text(encoding="utf-8")
    return [(word, 1) for word in re.findall(r"[a-z0-9]+", text.lower())]


def combine(pairs):
    totals = {}
    for word, count in pairs:
        totals[word] = totals.get(word, 0) + count
    return list(totals.items())


def partition(word):
    # Stable across runs, unlike Python's randomized built-in hash().
    return zlib.crc32(word.encode("utf-8")) % 2


def shuffle_sort(pairs):
    pairs = sorted(pairs, key=lambda pair: pair[0])
    return [(word, [count for _, count in group])
            for word, group in groupby(pairs, key=lambda pair: pair[0])]


def reducer(groups):
    return [(word, sum(values)) for word, values in groups]


def run(input_dir, output_dir):
    # README and the reference answer are metadata, not input splits.
    splits = sorted(p for p in input_dir.glob("*.txt")
                    if p.name != "expected_word_count.txt" and p.is_file())
    if not splits:
        raise ValueError(f"No input text files in {input_dir}")
    if input_dir.resolve() == output_dir.resolve():
        raise ValueError("Use a separate output directory")

    with ThreadPoolExecutor(max_workers=len(splits)) as pool:
        mapped = list(pool.map(mapper, splits))
    buckets = [[], []]
    for split, pairs in zip(splits, mapped):
        combined = combine(pairs)
        print(f"Map {split.name}: {len(pairs)} pairs -> {len(combined)} local totals")
        for word, count in combined:
            buckets[partition(word)].append((word, count))

    grouped = [shuffle_sort(bucket) for bucket in buckets]
    with ThreadPoolExecutor(max_workers=2) as pool:
        reduced = list(pool.map(reducer, grouped))
    output_dir.mkdir(parents=True, exist_ok=True)
    result = {}
    for index, rows in enumerate(reduced):
        path = output_dir / f"part-{index:05d}.txt"
        path.write_text("".join(f"{word} {count}\n" for word, count in rows),
                        encoding="utf-8")
        result.update(rows)
        print(f"Reducer {index}: {len(rows)} words -> {path}")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, default=Path("output"))
    parser.add_argument("--expected", type=Path)
    args = parser.parse_args()
    actual = run(args.input, args.output)
    if args.expected:
        expected = {}
        for line in args.expected.read_text(encoding="utf-8").splitlines():
            if line.strip():
                word, count = line.split()
                expected[word] = expected.get(word, 0) + int(count)
        if actual != expected:
            for word in sorted(actual.keys() | expected.keys()):
                if actual.get(word, 0) != expected.get(word, 0):
                    print(f"{word}: actual={actual.get(word, 0)}, expected={expected.get(word, 0)}")
            raise SystemExit("FAIL: output differs from expected word counts")
        print(f"PASS: all {len(actual)} word counts match the reference")


if __name__ == "__main__":
    main()
