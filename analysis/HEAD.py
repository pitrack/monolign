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
import sys
import os

from collections import defaultdict

aligndir = sys.argv[1]
posdir = sys.argv[2]
worddir = sys.argv[3]
common = open(sys.argv[4]).read().split("\n")

aligns = filter(lambda x: 'align' in x, os.listdir(aligndir))
pos = sorted(os.listdir(posdir))
allwords = sorted(os.listdir(worddir))
aligns = [(int(x.split('.')[0]), x) for x in aligns]
aligns.sort(key=lambda (x,y):x)

gTags = defaultdict(lambda : defaultdict(int))

def collect(line, tags, wordline, common):
    alignments = [pair.split("-") for pair in line.split() if pair != ""]
    splitTags = tags.split()
    sentWords = wordline.split()
    commonWords = common.split(" ")
    forwardIdx = {pair[0]: pair[1] for pair in alignments}
    for pair in alignments:
        try:
            sourceIdx = pair[0]
            commonIdx = pair[1]
            headWordIdx = forwardIdx[splitTags[int(sourceIdx)]]
        except:
            print "Index failure", int(sourceIdx), " could not get into",  sentWords
        gTags[commonWords[int(commonIdx)]][commonWords[int(headWordIdx)]] += 1

for i, f in aligns:
    posf = pos[i]
    allwordf = allwords[i]
    openedAlignFile = open(os.path.join(aligndir, f), 'r').read().split("\n")
    openedTagFile = open(os.path.join(posdir, posf), 'r').read().split("\n")
    openedWordFile = open(os.path.join(worddir, allwordf), 'r').read().split("\n")
    for errorIdx, (line, tags, wordline, commonline) in enumerate(zip(openedAlignFile, openedTagFile, openedWordFile, common)):
        try:
            collect(line, tags, wordline, commonline)
        except:
            print "error in collect"
            print errorIdx, i
            print line, tags, wordline, commonline
            print len(line.split()), len(tags.split()), len(wordline.split()), len(commonline.split())
            exit(0)

tagOutput = []
for key, hists in gTags.items():
    valueSum = sum(hists.values())
    valueList = [(k, float(v)/float(valueSum)) for k, v in hists.items()]
    valueList.sort(key=lambda(x,y):-1*y)
    tagOutput.append("{}: {}".format(key, " ".join(["{}: {}".format(k, v) for k, v in valueList])))

tagOutput.sort()
print "\n".join(tagOutput)

