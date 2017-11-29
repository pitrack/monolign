# Copyright 2017 Johns Hopkins University. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
import sys, os
from collections import defaultdict

def gen(f, head, fnum, g, gnum):
    return ("{}/words/{}.words".format(head, f),
            "{}/pair_alignments/{}-{}.align".format(head, fnum, gnum),
            "{}/words/{}.words".format(head, g)
        )

PP = defaultdict(lambda: defaultdict(int))
aligndir = sys.argv[1]
directory = sys.argv[2]

currdir = os.listdir(directory)
for gnum, gname in enumerate(currdir):
    for fnum, fname in enumerate(currdir):
        if fnum <= gnum:
            continue
        (wordfile, alignfile, word2file) = gen(fname, aligndir, fnum, gname, gnum)
        sents1 = open(wordfile, 'r').read().split("\n")
        sents2 = open(word2file, 'r').read().split("\n")
        aligns = open(alignfile, 'r').read().split("\n")
        for sent, alignseq, sent2 in zip(sents1, aligns, sents2):
            if ("DND" in sent or sent == "" or
                "DND" in sent2 or sent2 == ""):
                continue
            sentence = sent.strip().split(" ")
            sentence2 = sent2.strip().split(" ")
            word1set = defaultdict(list)
            word2set = defaultdict(list)
            for pair in alignseq.split(" "):
                if pair == "":
                    continue
                first, second = pair.split("-")
                sent2word = sentence2[int(second)]
                sent1word = sentence[int(first)]
                if sent2word in word2set:
                    if word2set[sent2word][-1] == sent1word:
                        continue
                word2set[sent2word].append(sent1word)
                if sent1word in word1set:
                    if word1set[sent1word][-1] == sent2word:
                        continue
                word1set[sent1word].append(sent2word)

            for word1 in sentence:
                if len(word1set[word1]) > 0:
                    PP[word1][" ".join(word1set[word1])] += 1
            for word2 in sentence2:
                if len(word2set[word2]) > 0:
                    PP[word2][" ".join(word2set[word2])] += 1

PPoutput = []
for key, hists in PP.items():
    valueSum = sum(hists.values())
    valueList = [(k, float(v)/float(valueSum)) for k, v in hists.items()]
    valueList.sort(key=lambda(x,y):-1*y)
    PPoutput.append("{}: {}".format(key, " ".join(["{}: {}".format(k, v) for k, v in valueList])))
    

PPoutput.sort()
print "\n".join(PPoutput)
