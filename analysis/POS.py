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
common = open(sys.argv[3]).read().split("\n")

aligns = filter(lambda x: 'align' in x, os.listdir(aligndir))
pos = sorted(os.listdir(posdir))
aligns = [(int(x.split('.')[0]), x) for x in aligns]
aligns.sort(key=lambda (x,y):x)

gTags = defaultdict(lambda : defaultdict(int))

def collect(line, tags, common):
    alignments = [pair.split("-") for pair in line.split() if pair != ""]
    splitTags = tags.split()
    commonWords = common.split(" ")
    for pair in alignments:
        sourceIdx = pair[0]
        commonIdx = pair[1]
        gTags[commonWords[int(commonIdx)]][splitTags[int(sourceIdx)]] += 1

for i, f in aligns:
    posf = pos[i]
    openedAlignFile = open(os.path.join(aligndir, f), 'r').read().split("\n")
    openedTagFile = open(os.path.join(posdir, posf), 'r').read().split("\n")
    for errorIdx, (line, tags, commonline) in enumerate(zip(openedAlignFile, openedTagFile, common)):
        try:
            collect(line, tags, commonline)
        except:
            print "error in collect"
            print errorIdx, i
            print line, tags, commonline
            print len(line.split()), len(tags.split()), len(commonline.split())
            exit(0)

tagOutput = []
for key, hists in gTags.items():
    valueSum = sum(hists.values())
    valueList = [(k, float(v)/float(valueSum)) for k, v in hists.items()]
    valueList.sort(key=lambda(x,y):-1*y)
    tagOutput.append("{}: {}".format(key, " ".join(["{}: {}".format(k, v) for k, v in valueList])))

tagOutput.sort()
print "\n".join(tagOutput)

