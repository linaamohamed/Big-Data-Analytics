# MapReduce Word Count Simulation

Requires Python 3.9+; no external packages, Hadoop, or Spark.

From the repository root:

```sh
python mapreduce/word_count.py datasets/text-files --output mapreduce/output
python -m unittest discover -s mapreduce -v
```

## Phases

1. **Input / split:** each `.txt` file in the input folder is one split. The supplied `expected_word_count.txt` is excluded because it is a reference answer.
2. **Map:** one thread per split emits `(word, 1)` pairs. Words are lowercase ASCII letter/digit sequences; punctuation separates words.
3. **Combine:** sum repeated words within each mapper's output.
4. **Partition:** a stable CRC32 hash modulo 2 sends every occurrence of a word to the same reducer.
5. **Shuffle and sort:** collect each reducer's pairs, sort by word, and group values for equal keys.
6. **Reduce:** two reducers sum each group's values and write `part-00000.txt` and `part-00001.txt`. Each file is sorted by word.

Example: mapper A emits `(cat, 1), (cat, 1)` and mapper B emits `(cat, 1)`. Combining gives `(cat, 2)` and `(cat, 1)`. Partitioning routes both to one reducer; shuffle groups `cat: [2, 1]`; reduce produces `cat 3`.

The optional `--expected` comparison checks the merged reducer results against the supplied reference and exits with an error if any count differs. The expected file is never used to compute the output.

**Reference discrepancy:** the upstream `expected_word_count.txt` does not match the supplied books. For example, `data` occurs twice but the reference says 1; `before` occurs twice but the reference says 1. It also contains two entries for `reduce`; the checker adds duplicate entries. Passing `--expected datasets/text-files/expected_word_count.txt` deliberately reports these mismatches and returns failure. The upstream reference is preserved. Tests instead verify a hand-counted example and compare the supplied books against a separate sequential count. The books yield 235 tokens and 182 distinct words.

## Scope

This is an in-memory educational simulation. Threads schedule mapper tasks concurrently; Python's GIL means this does not promise multicore speedup for CPU work. It has no cluster, distributed storage, retry system, or fault tolerance. Output part files are overwritten on each run.

## Submission

Fork the original repository in your GitHub account, copy this `mapreduce` folder into your fork, add your real name and student ID to the root README, then commit and push. Include the output and the successful validation message if requested by your instructor. Review the code so you can explain every phase.
