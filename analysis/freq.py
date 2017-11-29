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

def gen(f, head):
    return ("{}/words/{}.words".format(head, f),
            "{}/pos/{}.pos".format(head, f),
            "{}/heads/{}.head".format(head, f))

POS = defaultdict(lambda: defaultdict(int))
H = defaultdict(lambda: defaultdict(int))
aligndir = sys.argv[1]
directory = sys.argv[2]

for fname in os.listdir(directory):
    (wordfile, posfile, headfile) = gen(fname, aligndir)
    sents = open(wordfile, 'r').read().strip().split("\n")
    tags = open(posfile, 'r').read().strip().split("\n")
    heads = open(headfile, 'r').read().strip().split("\n")
    for sent, tagseq, headseq in zip(sents, tags, heads):
        if "DND" in sent or sent == "":
            continue
        sentence = sent.strip().split(" ")
        for word, tag, head in zip(sentence, tagseq.strip().split(" "), headseq.strip().split(" ")):
            POS[word][tag] += 1
            try:
                H[word][sentence[int(head)]] += 1
            except:
                print "{}|{}|{}|{}|".format(word, sent, tag, head)
                exit(0)

POSoutput = []
for key, hists in POS.items():
    valueSum = sum(hists.values())
    valueList = [(k, float(v)/float(valueSum)) for k, v in hists.items()]
    valueList.sort(key=lambda(x,y):-1*y)
    POSoutput.append("{}: {}".format(key, " ".join(["{}: {}".format(k, v) for k, v in valueList])))
    

POSoutput.sort()
print "\n".join(POSoutput)

Houtput = []
for key, hists in H.items():
    valueSum = sum(hists.values())
    valueList = [(k, float(v)/float(valueSum)) for k, v in hists.items()]
    valueList.sort(key=lambda (x,y) : -1*y)
    Houtput.append("{}: {}".format(key, " ".join(["{}: {}".format(k, v) for k, v in valueList])))

Houtput.sort()
print "\n".join(Houtput)
