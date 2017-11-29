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
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import codecs
import sys
import time
from spacy.en import English

from aligner import *
from inferer import Inferer
from structures import *
from parser import Parser

ITERATIONS = 10

def processFile(parser, aligner, inferers, new_rules, base_rules, fileiIdx, iteration):
    """
    Process a single file by:
    1. Alignment to all existing files
    2. Parsing each line
    3. Updating the inferer for each line
    
    """
    t0 = time.time()
    #create a working directory
    aligner.createDir(fileiIdx)
    # align to previous files
    filei = aligner.read(fileiIdx)
    t1 = time.time()
    # maybe in the future we only need to align once to save dev time
    for filejIdx in xrange(fileiIdx):
        aligner.alignWith(fileiIdx, filejIdx, new_rules, base_rules)
    t2 = time.time()
    alignments = aligner.loadAlignments(fileiIdx)

    for row in xrange(aligner.size): 
        parsedTree = parser.parse(filei[row])
        score = inferers[row].infer(parsedTree, [ed[row] for ed in alignments])
        theseRules = inferers[row].extractRules()
        new_rules[row].extend(theseRules)
    t3 = time.time()
    print ("Process file times: creating dir: {} aligning: {} inferring: {}".format(t1-t0, t2-t1, t3-t2))
    
def saturate(parser, aligner):
    """
    parser - English parser
    aligner - our Aligner object

    returns:
    inferer list
    rule list

    We no longer want to print all alignments because of space
    What happened to score??
    """

    base_rules = []
    final_alignments = ""
    # Do for multiple iterations
    best_inferers = [None for _ in xrange(aligner.size)]
    for iteration in xrange(ITERATIONS):
        t0 = time.time()
        aligner.update(iteration)
        perm = aligner.shuffle()
        new_rules = [[] for i in xrange(aligner.size)]
        inferers = [Inferer(perm) for i in xrange(aligner.size)]
        print ("Iteration {}".format(iteration), end="\n")
        t1 = time.time()
        for fileiIdx in xrange(aligner.numFiles):
            # clear the outdated rules:
            processFile(parser, aligner, inferers, new_rules, base_rules, fileiIdx, iteration)
        t2 = time.time()
        [inferer.score() for inferer in inferers]

        for i in xrange(aligner.size):
            if (best_inferers[i] == None or 
                best_inferers[i].getScore() < inferers[i].getScore()):
                best_inferers[i] = inferers[i]
            
        final_alignments = aligner.writeProgress(best_inferers, new_rules, t0)
        base_rules = list(collapseRules(new_rules))
        aligner.clean()
        print ("Orig. Score {}, Total Score {}".format(
            sum([inferer.getScore() for inferer in inferers]),
            sum([inferer.getScore() for inferer in best_inferers])
        ))
        aligner.writePairAlignments(best_inferers)
        aligner.writeCommonAlignments(best_inferers)
        aligner.writePOSHeads(best_inferers)
        t3 = time.time()
        print ("Prep: {} Processing files: {} Inferring: {}".format(t1-t0, t2-t1, t3-t2))
    return (final_alignments, best_inferers)
    
if __name__ == "__main__":
    #init
    t0 = time.time()
    parser = Parser()
    aligner = Aligner(sys.argv[0], sys.argv[1], sys.argv[2])


    t1 = time.time()
    (final_alignments, best_inferers) = saturate(parser, aligner)
    t2 = time.time()

    if (len(sys.argv) > 3):
        testFile = codecs.open(sys.argv[3], 'r', encoding='utf-8')
        text = testFile.read().split("\n")
        assert(len(best_inferers) == len(text))
        suggested = aligner.predict(testFile)
        for i in xrange(len(text)):
            best_inferers[i].predict(text[i].split(" "), suggested[i])            
        aligner.writeProgress(best_inferers, [[] for _ in xrange(len(text))], t2)
        
        
    t3 = time.time()

    print ("Initialization: {0:.4f}, Execution: {1:.4f}, Prediction: {2:.4f}\n{3:}\n{4:}".format(
        t1-t0, t2-t1, t3-t2, aligner.newDir, final_alignments))

