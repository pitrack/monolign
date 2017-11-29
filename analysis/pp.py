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

def gen(f, head, fnum):
    return ("{}/words/{}.words".format(head, f),
            "{}/alignments/{}.align".format(head, fnum))

PP = defaultdict(lambda: defaultdict(int))
aligndir = sys.argv[1]
directory = sys.argv[2]

commonfile = "{}/alignments/common.key".format(aligndir)
common = open(commonfile, 'r').read().split("\n")

for fnum, fname in enumerate(os.listdir(directory)):
    (wordfile, alignfile) = gen(fname, aligndir, fnum)
    sents = open(wordfile, 'r').read().split("\n")
    aligns = open(alignfile, 'r').read().split("\n")
    for sent, alignseq, commonsent in zip(sents, aligns, common):
        if "DND" in sent or sent == "":
            continue
        sentence = sent.strip().split(" ")
        common_sentence = commonsent.strip().split(" ")
        wordset = defaultdict(list)
        for pair in alignseq.split(" "):
            if pair == "":
                continue
            first, second = pair.split("-")
            commonword = common_sentence[int(second)]
            sentword = sentence[int(first)]
            # side effect of inserting commonword to wordset
            if commonword in wordset:
                if wordset[commonword][-1] == sentword:
                    continue
            wordset[commonword].append(sentword)
            
        PP[commonword][" ".join(wordset[commonword])] += 1

PPoutput = []
for key, hists in PP.items():
    valueSum = sum(hists.values())
    valueList = [(k, float(v)/float(valueSum)) for k, v in hists.items()]
    valueList.sort(key=lambda(x,y):-1*y)
    PPoutput.append("{}: {}".format(key, " ".join(["{}: {}".format(k, v) for k, v in valueList])))
    

PPoutput.sort()
print "\n".join(PPoutput)
