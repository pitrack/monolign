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

import networkx as nx
import spacy
import sys
import time

from collections import defaultdict
from relation import Relation
from structures import *

THRESHOLD = 4 # higher numebrs speed up solver
POINTS = 1.0
BONUS_POINTS = 1.0
            
class Inferer:
    """
    Inferrer is technically the correct spelling. There is one inferrer for each
    passage of multilingual parallel text. 
    size : int                Number of relations (= num rows = len(relations))
    numEditions : int         Number of editions (<= num cols = len(sentences))
    relations : relation list List of relations 
    sentences : Doc list      List of sentences
    backMap : (int, int) dict If i = relations[r][ed] then backMap(ed, i) = 
    score : int               Final score of the inferer (-1 if unscored)
    """
    def __init__(self, perm):
        self.size = 0
        self.numEditions = 0
        self.relations = [] 
        self.sentences = []
        self.testSentences = []
        self.backMap = {}
        self.finalScore = -1
        self.perm = list(perm)
        self.invperm = [x[0] for x in 
                        sorted([f for f in enumerate(self.perm, 0)], 
                               key=lambda x:x[1])]

        

        

    def infer(self, parseTree, suggested):
        """
        Given a parsed tree and alignments, augments the object with either
        new relations or maps words from parsedTree to old relations.
        parseTree : Doc
        suggested : 2d alignment array with all other parses
        """
        t0 = time.time()
        newRelations = self.updateAlignmentsAtOnce(parseTree, suggested)
        t1 = time.time()
        for relation in newRelations:
            self.addRelation(relation)
        for relation in self.relations: 
            relation.flushBuffer() # buffer might not be needed anymore
        self.numEditions += 1
        self.sentences.append(parseTree)
        t2 = time.time()
        if t2 - t0 > 1:
            print ("UAAO: {}, other: {}".format(t1-t0, t2-t1))
        # SCORE is not passed on, this return value doesn't matter
        # TODO: remove
        return 1 # score, which can be derived from a similarity score?

    def updateAlignmentsAtOnce(self, parseTree, suggested):
        """
        Use maximum weight bipartite matching - (|parseTree| + |relations|)^3
        parseTree: Doc
        suggested: 2d alignment array
        """
        t0 = time.time()
        G = nx.Graph()
        structures = [Structure(word, self.numEditions) for word in parseTree]
        for s in structures:
            G.add_node(s)
        for relation in self.relations:
            G.add_node(relation)
        t1 = time.time()
        # create a parent matrix
        parentMatrix = self.createParentMatrix(parseTree, suggested)
        t2 = time.time()
        # note structures is already sorted into a DAG
        # might not be relevant
        prof_scores = []
        for s in structures:
            for relationIdx in xrange(len(self.relations)):
                relation = self.relations[relationIdx]
                score = relation.scoreWith(s, suggested, parentMatrix[relationIdx])
                if (score >= THRESHOLD):
                    G.add_edge(s, relation, {'weight': score})
                    prof_scores.append(score)
        t3 = time.time()
        bestMatching = nx.max_weight_matching(G)
        t4 = time.time()
        for relationIdx in xrange(len(self.relations)):
            relation = self.relations[relationIdx]
            if relation in bestMatching:
                newStructure = bestMatching[relation]
                relation.structureBuffer.append((newStructure, G[relation][newStructure]['weight']))
                self.backMap[(self.numEditions, newStructure.name.i)] = relationIdx

        unmatched = [Relation(s) for s in structures 
                     if (s not in bestMatching and not s.shouldIgnore())]
        t5 = time.time()
        if t5 - t0 > 1:
            print ("UAAO: create: {}, matrix: {}, score: {}, match: {}, combine: {}, weights: []".format(t1-t0, t2-t1, t3-t2, t4-t3, t5-t4, prof_scores))
        return unmatched

    def createParentMatrix(self, parseTree, suggested):
        """
        For each word, create a matrix that scores how close it is to all possible parents. This 
        is done by looking at its parent in other sentences. This is later used to determine
        whether two parents share similar children.
        parseTree: Doc
        suggested: 2d alignment array
        Returns:
        matrix = size by |parseTree| array
        matrix[r][i] = score that r is the parent relation of i.
        """
        matrix = [[0 for _ in parseTree] for _ in xrange(self.size)]
        for sIdx in xrange(len(parseTree)):
            for ed in xrange(self.numEditions):
                tIdxs = suggested[ed][sIdx]
                for tIdx in tIdxs:
                    try:
                        t = self.sentences[ed][tIdx]
                        pIdx = t.head.i
                        try:
                            r = self.backMap[(ed, pIdx)]
                            matrix[r][sIdx] += POINTS / len(tIdxs) 
                            if (t.dep_ == parseTree[sIdx].dep_):
                                matrix[r][sIdx] += BONUS_POINTS / len(tIdxs)
                            if (t.head.pos_ == parseTree[sIdx].pos_):
                                matrix[r][sIdx] += BONUS_POINTS / len(tIdxs)
                        except KeyError:
                            # Oh well, not found.
                            pass
                    except IndexError:
                        print (u"Could not index {} in {}: {}".format(tIdx, self.sentences[ed], self.sentences))
        return matrix
                

    def addRelation(self, relation):
        """
        Insert a relation into list, update backmap and size
        """
        self.relations.append(relation)
        self.backMap[(self.numEditions, relation.name.i)] = self.size
        self.size += 1
        return

    def extractRules(self):
        """
        returns a list of equivalent sets
        call pick consensus in here
        """
        return [list(r.extractRules()) for r in self.relations]

    def predict(self, testLine, suggested):
        # testline is an unparsed line from testfile
        # suggested is an alignment list, suggested[i] corresponds to alignments with filei
        # max weight between words and structures
        self.testSentences.append(" ".join(testLine))
        G = nx.Graph()
        for relation in xrange(self.size):
            G.add_node(relation)
        for word in testLine:
            G.add_node(word)

        for ed in xrange(self.numEditions):
            for i in xrange(len(testLine)):
                for j in suggested[ed][i]:
                    # (test[i], train[j]) are aligned
                    try:
                        relation = self.backMap[(self.perm[ed], j)]
                        if (testLine[i] in G[relation]):
                            G[relation][testLine[i]]['weight'] += 1
                        else:
                            G.add_edge(relation, testLine[i], weight=1)
                    except Exception, e:
                        pass

        bestMatching = nx.max_weight_matching(G)

        for relationIdx in xrange(self.size):
            relation = self.relations[relationIdx]
            if relationIdx in bestMatching:
                relation.predicts.append(bestMatching[relationIdx])
            else:
                relation.predicts.append("")
            # self.backMap update?
        # Ignore unmatched things, don't make new relations
        return None
        

    def score(self):
        if (self.size == 0):
            return 0
        self.finalScore = sum([r.score for r in self.relations])/(float(self.size))

    def getScore(self):
        return self.finalScore


    def toString(self):
        # stackoverflow print function
        headerRow = [str(self.perm[i]) for i in range(self.numEditions)]
        headerRow.insert(0, "ED:")
        headerRow.append("Predict?")
        data = [row.toList(self.numEditions) for row in self.relations]
        for i in xrange(self.size):
            data[i].insert(0, "{}".format(self.relations[i].finalString()))
        data.insert(0, headerRow)
        lens = [max(map(len, col)) for col in zip(*data)]
        fmt = u'\t'.join('{{:{}}}'.format(x) for x in lens)
        table = u"\n".join([fmt.format(*row) for row in data])
        sentences = u"\n".join([sent.string for sent in self.sentences])
        testSentences = u"\n".join(self.testSentences)
        relations = u"\n".join(["{}".format(r.toString(self.backMap, self.relations)) 
                                for r in self.relations
                                if len(r.getEdges(self.backMap, self.relations)[1]) > 0])
        return (u"{}\n\n{}\n\n{}\n\n{}".format(table, sentences, testSentences, relations),
                relations)
