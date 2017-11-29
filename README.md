# monolign
_probably better named multilign, but too late now_

Repository for the IJCNLP paper "Deriving Consensus for Multi-Parallel Corpora: an English Bible Study" [[pdf](http://cs.jhu.edu/~paxia/ijcnlp17-paper.pdf)][[slides](http://cs.jhu.edu/~paxia/ijcnlp17-slides.pdf)]

# Execution

To run, run
```
python monolign.py DATA_DIR ALIGNER
```
where DATA_DIR consists of n texts where the ith line of each document are parallel. ALIGNER in this case is the location of `fast_align`, and `aligner.py` would need to be modified for other aligners.

# Analysis

These scripts are mostly the same, and were one-off scripts used to generate figures for the paper. Use with caution.

# Output + Resources

The output of the program will be in `alignments.log` for each iteration, though the best will be in the folder for the last iteration. Each line from the input file will correspond to three sections, an alignment matrix (like the ones in the paper but not sorted by index), a list of dependency arcs, and possible paraphrases/word pairs. These can be found [here (92M)](http://cs.jhu.edu/~paxia/papers/monolign.tar.gz) or a [sample (45M)](http://cs.jhu.edu/~paxia/papers/monolign-small.tar.gz).
