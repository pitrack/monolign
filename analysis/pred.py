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

def POSify(triple_set):
    return {k[0]: (k[1], k[2]) for k in triple_set}

def wordify(triple_set):
    return {k[1]: (k[0], k[2]) for k in triple_set}

def expand(word, d_list):
    if word == None:
        return []
    current = [word]
    if word[1] == 'VERB':
        return current
    for d in d_list:
        if word[0] in d:
            link = d[word[0]]
            new_words = POSify(link[1]).values()
            for new_word in new_words:
                current.append(expand(new_word, d_list))
    return current

class Predicate():
    def __init__(self, d):
        self.predicate = d.keys()[0]
        args = POSify(d.values()[0][1])
        self.nsubj = None
        self.dobj = None
        self.prep = None
        self.comp = None
        if 'nsubj' in args:
            self.nsubj = args['nsubj']
        if 'dobj' in args:
            self.dobj = args['dobj']
        if 'prep' in args:
            self.prep = args['prep']
        if 'xcomp' in args:
            self.comp = args['xcomp']

    def __str__(self):
        return "{} | NSUBJ: {} | DOBJ: {} | NSUBJ_exp: {} | DOBJ_exp: {} | PREP_exp: {} | COMP_exp: {}".format(
            self.predicate, self.nsubj, self.dobj, self.nsubj_list, self.dobj_list, self.prep_list, self.comp)
    def __repr__(self):
        return self.__str__()
            
def collapse(d_list):
    # collect verbs
    verbs = []
    for d in d_list:
        if d.values()[0][0] == 'VERB':
            verbs.append(d)
    preds = []
    for verb in verbs:
        verb_p = Predicate(verb)
        try:
            verb_p.nsubj_list = expand(verb_p.nsubj, d_list)
            verb_p.dobj_list = expand(verb_p.dobj, d_list)
            verb_p.prep_list = expand(verb_p.prep, d_list)
            verb_p.comp_list = expand(verb_p.comp, d_list)
            preds.append(verb_p)
        except:
            # TODO id the words so there's no recursion
            continue

    return preds

def read_d_list(f):
    text = open(f, 'r').read().split("-" * 50)
    result = []
    for block in text:
        block_list = []
        if len(block) == 0:
            result.append("")
            continue
        for b in block.split("\n"):
            if b == "":
                continue
            try:
                block_list.append(eval(b))
            except:
                b = b.replace("':", '":').replace(" '", ' "')
                try:
                    block_list.append(eval(b))
                except:
                    print "Error: {}".format(b, block, len(block))
        result.append(block_list)
    return result
    

if __name__ == "__main__":
    d_list_lists = read_d_list(sys.argv[1])
    for line_no, d_list in enumerate(d_list_lists):
        collapsed = collapse(d_list)
        if len(collapsed) != 0:
            print "{}\n{}".format(line_no, "\n".join(map(lambda x: str(x), collapsed)))
    
