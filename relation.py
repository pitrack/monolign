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

import spacy
from collections import defaultdict
from structures import Structure

class Relation:
    """
    single structure, contains list of structures
    """
    def __init__(self, structure):
        self.ed = structure.ed # only for indexing reasons
        self.name = structure.name # only for hashing purposes
        self.structures = {}
        self.structureBuffer = [(structure, 0)]
        self.stringify = ""
        self.predicts = []
        self.score = 0
        self.canon = None
        self.args = None
        self.pos = None
        self.rules = None

    def addStructure(self, structure):
        self.structures[structure[0].ed] = structure[0]
        self.score += structure[1]
        
        
    def flushBuffer(self):
        if (len(self.structureBuffer) > 1):
            print ("Buffer exceeded size 1")
            raise AssertionError
        for structure in self.structureBuffer:
            self.addStructure(structure)
            
        self.structureBuffer = []

    def pickConsensus(self):
        # need to deal with children, for now just returns name
        names = defaultdict(int)
        for s in self.structures.values():
            names[s.name.orth_] += 1
        # pick most common name
        # pick most common tags
        # what to do about args?
        return max(names, key=names.get)

    def sim(self, structure):
        # commutative
        return sum([structure.sim(s) for s in self.structures.values()])

    def scoreWith(self, structure, suggested, parentsMatrixAtHere):
        """
        self: relation
        structure: new thing (structure)
        """
        # pairwise scores:
        pairwiseScores = sum([sum(structure.scoreWith(s, suggested).values()) 
                              for s in self.structures.values()])/(len(self.structures))
        
        # global scores: 
        childrenScores = sum([parentsMatrixAtHere[child.i] for child in structure.name.children])
        # "How likely am I the parent of my children?"
        

        # print ("{}:R, {}:S, word={}, child={}".format(self.finalString(), structure.name,
        #                                               wordFeatures, childrenFeatures))
        return pairwiseScores + childrenScores
 
    def toString(self, backMap, relations):
        #return "\t".join([u"({}, {})".format(s.toString(), s.ed) for s in self.structures.values()])
        if self.stringify == "":
            edges = self.getEdges(backMap, relations)
            self.stringify = u"{{ '{}':('{}', {}) }}".format(
                self.getString(), edges[0], edges[1])
        return self.stringify

    def toList(self, size):
        output = ["" for _ in xrange(size)]
        for s in self.structures.values():
            output[s.ed] = (u"({}, {})".format(s.name, s.name.i))
        if len(self.predicts) > 0:
            output.extend(self.predicts)
        return output
    
    def extractRules(self):
        self.rules = set([s.name.orth_ for s in self.structures.values()])
        return self.rules

    def getRules(self):
        if self.rules == None:
            return extractRules()
        else:
            return self.rules
 
    def extractEdges(self, backMap, relations):
        allPOS = defaultdict(int)
        allEdges = defaultdict(lambda: defaultdict(int))

        # keys are of type (edgeType, R(child): Robj)
        for ed, s in self.structures.items():
            allPOS[s.pos] += 1
            for (e, tokens) in s.args.items():
                for tok in tokens:
                    if (ed, tok.i) in backMap:
                        allEdges[e][backMap[(ed, tok.i)]] += 1

        # most common POS tag:
        self.pos = max(allPOS, key=allPOS.get)

        # most common edges
        self.args = set()
        for edge in allEdges.keys():
            k = int(0.5 + (sum(allEdges[edge].values())/float(len(self.structures))))
            for i in xrange(k):
                newRi = max(allEdges[edge], key=allEdges[edge].get)
                self.args.add((edge, relations[newRi].finalString(), 
                               "{:.2f}".format(allEdges[edge][newRi]/float(len(self.structures)))))
                allEdges[edge].pop(newRi)

        
        return (self.pos, self.args)


    def getEdges(self, backmap, relations):
        if self.args == None or self.pos == None:
            return self.extractEdges(backmap, relations)
            
        else:
            return (self.pos, self.args)
            
    def getString(self):
        if self.canon is None:
            self.canon = self.pickConsensus()
        return self.canon


    def finalString(self):
        self.canon = self.pickConsensus()
        return self.canon
