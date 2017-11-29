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

# aligner interface with disk
# This file targets creating pairwise alignments, which is needed between
# every iteration.

import codecs
import os
import time
import sys
import random 

from collections import defaultdict

CLEAN = False

def passesSimilarity(word1, word2):
    # We can handcraft a similarity function between words instead of
    # simply using the identity, but for simplicity only identity is present here.
    # Other heuristics could include edit distance or similarity.
    return word1 == word2

def collapseRules(rules):
    # Merges rules and adds them to end of bitext
    allRules = set()
    for row in rules:
        for relation in row:
            for i in xrange(len(relation)):
                for j in xrange(i+1):
                    if (passesSimilarity(relation[i], relation[j])):
                        allRules.add((relation[i], relation[j]))
                        allRules.add((relation[j], relation[i]))
    return allRules

def lowQuality(pairs):
    return (sum([int(p[0]) for p in pairs]) == 0 or
            sum([int(p[1]) for p in pairs]) == 0)

class Aligner:
    def __init__(self, srcDir, dataDir, alignerDir):
        self.aligner = alignerDir # this is a string
        self.iteration = 0
        self.newDir = "{}_aligns{}".format(
            dataDir[:-1],
            time.strftime('%S%M%H_%m%d')
        )
        try:
            os.mkdir(self.newDir)
        except:
            print ("New working directory could not be created")
            pass
        self.currDir = "{}/{}".format(self.newDir, self.iteration)
        self.fileList = [codecs.open(os.path.join(dataDir, f), 'r', encoding='utf-8') 
                         for f in os.listdir(dataDir) 
                         if f.endswith(".txt")]
        self.fileNames = [os.path.basename(f) 
                          for f in os.listdir(dataDir)
                          if f.endswith(".txt")]
        self.numFiles = len(self.fileList)
        self.size = 0
        # assumes all files are equal lengths -- they better be!
        self.perm = range(self.numFiles)
        random.shuffle(self.perm)

        if (len(self.fileList) > 0):
            self.size = len(self.read(0))
            self.fileList[0].seek(0)

    def clean(self):
        # delete pairwise alignments
        # comment out if needed for debug
        if (CLEAN):
            os.system("rm -R -- {}/*/".format(self.currDir))
        

    def update(self, iteration):
        self.iteration = iteration
        self.currDir = "{}/{}".format(
            self.newDir,
            self.iteration
        )

        try:
            os.mkdir(self.currDir)
        except:
            print ("New iteration directory could not be created")
            pass

        for f in self.fileList:
            f.seek(0)
        return

    def shuffle(self):
        # specify how many are test, assumes last one is.
        #copy = self.perm[:-1]
        random.shuffle(self.perm)
        #self.perm[:-1] = copy
        return self.perm
        
    def createDir(self, fileiIdx):
        # make a dir to put alignments in
        try:
            os.mkdir('{}/{}'.format(self.currDir, self.fileNames[self.perm[fileiIdx]]))
        except Exception, e:
            # directory already exists
            print (e)
            pass

    def formatRules(self, new_rules, base_rules):
        allRules = set(base_rules)
        allRules.union(collapseRules(new_rules))
        return u"\n".join([u"{} ||| {}".format(a, b) for (a,b) in list(allRules)])
                    

    def alignWith(self, file1Idx, file2Idx, new_rules, base_rules):
        # aligns file1Idxth and file2Idxth files into a separate directory
        #t0 = time.time()
        file1dir = "{}/{}".format(self.currDir,
                                  self.fileNames[self.perm[file1Idx]])
        tmpFile = "{}/{}tmp".format(
            file1dir, self.perm[file2Idx]
        )
        
        os.system("paste {} {} | sed 's/\t/ ||| /' > {} ".format(
            self.fileList[self.perm[file1Idx]].name,
            self.fileList[self.perm[file2Idx]].name,
            tmpFile
        ))
        # add rules >>
        with codecs.open(tmpFile, 'a', "utf-8") as tmpOpenFile:
            tmpOpenFile.write(self.formatRules(new_rules, base_rules))


        # experiment with alignment args.
        os.system("{} -i {} -d -o -v 1>{}/{}.align 2>{}/{}.log".format(
            self.aligner, tmpFile, file1dir, self.fileNames[self.perm[file2Idx]],
            file1dir, self.fileNames[self.perm[file2Idx]])
        )
        
        if (CLEAN):
            os.system("rm {}".format(tmpFile))
        #t1 = time.time()

    def predict(self, f):
        # make a dir to put alignments in
        fileName = f.name.split("/")[-1] # should use os instead of split
        self.currDir = "{}/{}".format(
            self.newDir,
            fileName
        )
        try:
            os.mkdir('{}'.format(self.currDir))
            print ("PredictDir is {}".format(self.currDir))
        except Exception, e:
            # directory already exists
            print (e)
            pass
        
        for fileiIdx in xrange(self.numFiles):
            tmpFile = "{}/{}tmp".format(self.currDir, fileiIdx)
            os.system("paste {} {} | sed 's/\t/ ||| /' > {} ".format(
                f.name,
                self.fileList[fileiIdx].name,
                tmpFile
            ))
            # no additional rules
            os.system("{} -i {} -d -o -v 1>{}/{}.align 2>{}/{}.log".format(
                self.aligner, tmpFile, self.currDir, self.fileNames[fileiIdx],
                self.currDir, self.fileNames[fileiIdx])
            )
        # load into an array
        A = [[defaultdict(list) for _ in xrange(self.numFiles)] 
             for _ in xrange(self.size)]
        for fileiIdx in xrange(self.numFiles):
            try:
                document = open('{}/{}.align'.format(
                    self.currDir,
                    self.fileNames[fileiIdx]), 'r').read().split("\n")
                for lineIdx in xrange(self.size):
                    line = document[lineIdx]
                    if (len(line) > 0):
                        pairs = map(lambda x : x.split("-"), line.split(" "))
                        for pair in pairs:
                            A[lineIdx][fileiIdx][int(pair[0])].append(int(pair[1]))
            except Exception, e:
                print ("Failed to open document: {}/{}.align... {}".format(
                    self.currDir, self.fileNames[fileiIdx], e))

        return A
            
    def read(self, fileiIdx):
        # expects a file index
        return self.fileList[self.perm[fileiIdx]].read().split("\n")
        
    def loadAlignments(self, fileiIdx):
        """
        returns a massive array with respect to fileiIdx with the following behavior:
        for filejIdx < fileiIdx
        A[filejIdx] is the alignments in tmp/i/j.align and
        A[filejIdx][line] is the alignments ,a, at tmp/i/j.align:line
        where a[wordiIdx] = wordIdx list from j.align:line that aligned to a[wordiIdx]
        """
        A = [[defaultdict(list) for i in xrange(self.size)] for j in xrange(fileiIdx)]
        for filejIdx in xrange(fileiIdx):
            try:
                document = open('{}/{}/{}.align'.format(
                    self.currDir, 
                    self.fileNames[self.perm[fileiIdx]], 
                    self.fileNames[self.perm[filejIdx]]), 'r').read().split("\n")
                for lineIdx in xrange(self.size): #= len(document)
                    line = document[lineIdx]
                    if (len(line) > 0):
                        pairs = map(lambda x: x.split("-"), line.strip().split(" "))
                        if (lowQuality(pairs)):
                            continue
                        else:
                            for pair in pairs:
                                A[filejIdx][lineIdx][int(pair[0])].append(int(pair[1]))
            except Exception, e:
                print ("Failed to open document: {}, {} -> {}, {}".format(filejIdx, fileiIdx, 
                                                                self.perm[filejIdx], self.perm[fileiIdx]))
                print ("Did not open {}/{}/{}.align".format(
                    self.currDir, 
                    self.fileNames[self.perm[fileiIdx]], 
                    self.fileNames[self.perm[filejIdx]]))
                print (e)
                # Alignments don't exist. Oh well, we saved memory and time.
                pass

        return A

    def writeProgress(self, inferers, rules, t0):
        name = "alignments.log"
        name2 = "predicates.log"
        path = "{}/{}".format(self.currDir, name)
        path2 = "{}/{}".format(self.currDir, name2)
        output = codecs.open(path, 'w', "utf-8")
        output2 = codecs.open(path2, 'w', "utf-8")
        for (inferer, rule) in zip(inferers, rules):
            infererString, relationsString = inferer.toString()
            output.write(u"{}\nAlignments:\n{}\n\nRules:\n{}\nScore:{}\n".format(    
                 "-" * 50,
                 infererString,
                 str(rule),
                 inferer.getScore()
             ))
            output2.write(u"{}\n{}\n".format(
                "-" * 50,
                relationsString)
            )
        output.write(u"Score reports\n")
        for inferer in inferers:
            output.write(u"{}\n".format(inferer.getScore()))
        output.write(u"Total: {}\n".format(sum([inferer.getScore() for inferer in inferers])))
        t1 = time.time()
        output.write(u"Approx. Time: {}\n".format(t1-t0))
        output.close()
        output2.close()
        return path

    def writePairAlignments(self, inferers):
        alignDir = "{}/pair_alignments".format(self.currDir)
        print ("Writing pair alignments")
        try:
            os.mkdir(alignDir)
        except Exception, e:
            #?
            print (e)
            pass
        for i in xrange(self.numFiles):
            for j in xrange(i):
                outAlignsFile = "{}/{}-{}.align".format(alignDir, i, j)
                outAligns = codecs.open(outAlignsFile, 'w', "utf-8")
                for inferer in inferers:
                    aligns = []
                    for r in inferer.relations:
                        if (inferer.invperm[i] in r.structures and
                            inferer.invperm[j] in r.structures):
                            aligns.append("{}-{}".format(
                                r.structures[inferer.invperm[i]].name.i,
                                r.structures[inferer.invperm[j]].name.i))
                    outAligns.write("{}\n".format(" ".join(aligns)))
                outAligns.close()

    def writeCommonAlignments(self, inferers):
        alignDir = "{}/alignments".format(self.currDir)
        print ("Writing alignments")
        try:
            os.mkdir(alignDir)
        except Exception, e:
            #?
            print (e)
            pass
        # write common alignment key
        common = []
        for inferer in inferers:
            current = []
            for relation in inferer.relations:
                current.append(relation.finalString())
            common.append(" ".join(current))
        outCommonFile = "{}/common.key".format(alignDir)
        outCommon = codecs.open(outCommonFile, 'w', "utf-8")
        outCommon.write("\n".join(common))
        outCommon.close()

        # write alignments w.r.t. common
        for i in xrange(self.numFiles):
            outAlignsFile = "{}/{}.align".format(alignDir, i)
            outAligns = codecs.open(outAlignsFile, 'w', "utf-8")
            for inferer in inferers:
                aligns = []
                for c, r in enumerate(inferer.relations):
                    if (inferer.invperm[i] in r.structures):
                        aligns.append("{}-{}".format(
                            r.structures[inferer.invperm[i]].name.i,
                            c))
                outAligns.write("{}\n".format(" ".join(aligns)))
            outAligns.close()

    # write POS
    def writePOSHeads(self, inferers):
        posDir = "{}/pos".format(self.currDir)
        headDir = "{}/heads".format(self.currDir)
        wordDir = "{}/words".format(self.currDir)
        print ("Writing POS and heads")
        try:
            os.mkdir(posDir)
            os.mkdir(headDir)
            os.mkdir(wordDir)
        except Exception, e:
            #?
            print (e)
            pass

        for i,f in enumerate(self.fileNames):
            outPosFile = "{}/{}.pos".format(posDir, f)
            outHeadFile = "{}/{}.head".format(headDir, f)
            outWordFile = "{}/{}.words".format(wordDir, f)
            outPos = codecs.open(outPosFile, 'w', "utf-8")
            outHead = codecs.open(outHeadFile, 'w', "utf-8")
            outWords = codecs.open(outWordFile, 'w', "utf-8")

            for inferer in inferers:
                tags = {}
                heads = {}
                words = {}
                for r in inferer.relations:
                    if (inferer.invperm[i] in r.structures):
                        structName = r.structures[inferer.invperm[i]].name
                        structIndex = structName.i
                        tags[structIndex] = str(structName.tag_)
                        heads[structIndex] = str(structName.head.i)
                        words[structIndex] = str(structName)
                # this feels unsafe
                outPos.write(u"{}\n".format(u" ".join(tags.values())))
                outHead.write(u"{}\n".format(u" ".join(heads.values())))
                try:
                    outWords.write(u"{}\n".format(u" ".join(words.values())))
                except:
                    outWords.write(u"{}\n".format("----DND----"))
            outPos.close()
            outHead.close()
            outWords.close()
