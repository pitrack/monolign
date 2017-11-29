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

ALIGN_SCORE = 1
CHILD_ALIGN_SCORE = 1
DEBUG = False
SHOULD_IGNORE = []

class Structure:
    """
    HEAD [tags] (edge1 -> token, edge2 -> token, edge3 -> token...)
    special rules are used for certain edge types
    -> does not necessarily follow tree edges
    """
    # empty is a leftover function, probably not needed.
    # def empty(edition = -1):
    #     self.name = ""
    #     self.tags = {}
    #     self.args = defaultdict(list)
    #     self.ed = edition
    #     self.score = 0 ??
    #     self.bestScore = 0???


    def __init__(self, token, edition):        
        self.name = token
        self.counter = token.i + 1
        self.tags = {} # possible morphosyntactic features
        self.pos = token.pos_
        self.args = defaultdict(list)
        for left in token.lefts:
            self.args[left.dep_].append(left)
        for right in token.rights:
            self.args[right.dep_].append(right)
        self.ed = edition # purely for indexing reasons

    def shouldIgnore(self):
        return (self.pos in SHOULD_IGNORE)

    def sim(self, s2, s2Alignments):
        # This comment is about similarity in general:
        # may want to look at children properties
        # at the very least, they can't both be empty!
        # this only looks at chilcren
        # features 
        # 1. word similarity with spacy
        # 2. point for POS tag 
        # 3. value for child similarity
        # 4. value for edge weights

        # most of these features not implemented/included in final scoring function
        
        ownKeys = set(self.args.keys())
        s2Keys = set(s2.args.keys())
        edgeOverlaps = ownKeys.intersection(s2Keys)
        score = 0
        for edge in edgeOverlaps:
            ownSet = self.args[edge]
            s2Set = s2.args[edge]
            edgeScore = min(len(ownSet), len(s2Set)) # approximation - could be weighted
            for token1 in ownSet:
                for token2 in s2Set:
                    if (token2.i in s2Alignments[token1.i]):
                        edgeScore += CHILD_ALIGN_SCORE             # yet another weight
            score += edgeScore
        return score

    def scoreWith(self, s2, alignments):
        '''
        assumptions, not fully commutative
        s2 - "other"
        self - "this
        s2.ed < self.ed
        '''
        # do some evaluation calculating similarity of trees, 
        #use their scores, increase scores based on alignment
        if (DEBUG):
            print (self.name, s2.name)
            print (s2.name.i, self.name.i, alignments[s2.ed])

        align_score = 0
        if (s2.name.i in alignments[s2.ed][self.name.i]):
            align_score += ALIGN_SCORE # this could be finer grained?
        
        identity_score = 0
        if (s2.name.orth_ == self.name.orth_):
            identity_score = 3
        lemma_score = 0
        if (s2.name.lemma_ == self.name.lemma_):
            lemma_score = 1
        parentID_score = 0
        if (s2.name.head.orth_ == self.name.head.orth_):
            parentID_score = 1
        pos_score = 0
        if (self.pos == s2.pos):
            pos_score = 1

        child_score = self.sim(s2, alignments[s2.ed]) # looks at children

        return {"align": align_score, 
                "id": identity_score, 
                "lemma": lemma_score,
                "parent": parentID_score,
                "pos" : pos_score,
                "children": child_score}
        
    def toString(self):
        return u"{}.{} [{}] ({})".format(
            self.name, self.name.tag_, 
            u",".join(list(self.tags)), 
            u",".join([u"{} -> [{}]".format(
                edge, 
                u",".join([u"{}.{}".format(token, token.tag_) for token in tokens]))
            for (edge, tokens) in self.args.items()])
        )

