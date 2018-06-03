""" Entry point for the solver. """

import math
from string import punctuation

from words import WordStats


class QuipProb(object):
    """ Just a container for the Cryptoquip problem. """
    def __init__(self, sentence, hint_src, hint_dst, answer=None):
        """
        :type sentence: str
        :param sentence: encrypted sentence
        :type hint_src: str
        :param hint_src: hint's original char
        :type hint_dst: str
        :param hint_dst: hint's encrypted char
        :type answer: str
        """
        self.sentence = sentence.lower()
        self.hint_src = hint_src.lower()
        self.hint_dst = hint_dst.lower()
        self.answer = answer
        if self.answer:
            self.answer = self.answer.lower()
        return
    pass


class Solver(object):
    def __init__(self, prob, ignores=' ' + punctuation):
        """
        :type prob: QuipProb
        """
        self.prob = prob
        self.ignores = ignores
        self.ws = WordStats()
        return

    def get_default_dict(self):
        d = dict()
        d[self.prob.hint_src] = self.prob.hint_dst
        return d

    def split_words(self, s):
        """ Split using given char ignore list.
        :type s: str
        """
        words = []
        def _append_word(l, h):
            if l >= h:
                return
            if l < 0 or h > len(s):
                return
            words.append(s[l:h])
            return

        low = 0
        high = 0
        while low < len(s) and high < len(s):
            if s[high] in self.ignores:
                _append_word(low, high)
                high += 1
                low = high
            else:
                assert s[high].isalpha()
                high += 1
                pass
            pass
        _append_word(low, len(s))  # for possible last incomplete pass
        return words

    def same_char_locs(self, w):
        """ Collect which locations of a word are having the same character.
        :type w: str
        :return: a list of sets, where each set contains same char locations
        """
        d = dict()
        for i in range(len(w)):
            c = w[i]
            if c in d:
                d[c].add(i)
            else:
                d[c] = {i}
            pass
        d = d.items()
        res = [p for p in list(d) if len(p[1]) > 1]
        res = [list(p[1]) for p in res]
        return res

    def extend_dict_copy(self, d, src, dst):
        """ Return a copy of d with extra mapping src=>dst added.
        :type d: dict
        :type src: str
        :type dst: str
        """
        assert len(src) == len(dst)
        d = d.copy()
        for i in range(len(src)):
            c = src[i]
            goal = dst[i]
            if c in d:
                assert d[c] == goal
            d[c] = goal
        return d

    def find_candidates(self, encrypted, curr_dict):
        """ Rules:
        1. With same length;
        2. Match with existing mapping;
        3. Match with same internal constraint.
        """
        size = len(encrypted)
        assert size in self.ws.by_len, 'No words of length %d' % size
        pool = self.ws.by_len[size]

        fixed_chars = []  # holding (loc, target-char)
        for i in range(size):
            c = encrypted[i]
            if c in curr_dict:
                # already fixed
                fixed_chars.append((i, curr_dict[c]))
                pass
            pass

        same_locs = self.same_char_locs(encrypted)

        def _valid(w):
            # matching mapping
            for loc, ch in fixed_chars:
                if w[loc] != ch:
                    return False
                pass

            # matching internal constraint
            for group in same_locs:
                for i in range(len(group)):
                    idx1 = group[i]
                    for j in range(i+1, len(group)):
                        idx2 = group[j]
                        if w[idx1] != w[idx2]:
                            return False
                    pass
                pass
            return True

        return [w for w in pool if _valid(w)]

    def map_str(self, d, s, allow_holes=False):
        """
        :type d: dict
        :type s: str
        :param allow_holes: if True, the dict could be incomplete.
        """
        def _map(c):
            if c in self.ignores:
                return c
            if c in d:
                return d[c]

            if allow_holes:
                return '_'
            else:
                raise ValueError('Some char ' + c + ' is not mapped.')

        return ''.join([_map(c) for c in s])

    def solve(self):
        encrypted_ws = self.split_words(self.prob.sentence)
        curr_dict = self.get_default_dict()
        dicts = []

        self._solve(encrypted_ws, curr_dict, dicts)
        if not dicts:
            return ['FAILED. No match found.']

        def _heuristic(d):
            """ Idea: the more popular each word is, the more likely it's a correct sentence. """
            decrypted_ws = [self.map_str(d, w) for w in encrypted_ws]
            score = 0.0
            for w in decrypted_ws:
                idx = self.ws.by_len[len(w)].index(w)
                try:
                    score += math.log(idx + 1)  # to avoid it being 0
                except:
                    print(w, idx)
                    raise ValueError()
            return score

        res = []
        for i in range(min(3, len(dicts))):
            # Select the top 3, or all if there are <3 possibilities.
            d = min(dicts, key=_heuristic)
            dicts.remove(d)
            res.append(self.map_str(d, self.prob.sentence))
            pass
        return res

    def _solve(self, encrypted_ws, curr_dict, collection):
        """
        :return: the decrypted sentence, or None when failed
        """
        '''
        Some thoughts:
        * It is essentially a SAT problem (with string theory?). But I am doing it using heuristic search + NLP.
        * I may also try Reinforcement Learning on the automation policy?
        * One unsettled step is to determine the validity of final sentence -- how to know it's some human sentence?
            * Perhaps use the heuristic from final words' their popularity position, the small, the better.
            * A better way would be to see the occurrence probability of words using Embedding, for example.
        * In each step, filter words using:
            Length;
            Existing Mapping;
            Internal constraint (e.g. same char);
            External constraint (e.g. some char cannot be mapped to xxx);  (this becomes more like SAT solving)
        * Possible strategy (1):
            Goal is to map 26 chars to 26 chars.
            So the greedy step is to first try those SRC CHARs that would restrict the space most.
        * Possible strategy (2): (used)
            Iterate each word, find most heuristic words to start.
            Then try each word to propagate the determined chars.
            Maintain only words that are not fully parsed (not all chars in parsed dict).
            The search space should be smaller.
        * Possible strategy (3):
            Find internal constraints first.
            Filter cases that are impossible? It's just easier for computer to enumerate..


        Current status:
            317756 words loaded in descending order of frequency.
            amekbtdc jcgtyhb udblf qkmohbjdlakm dykgl heehqlaohcf nhhuamz bamzchlj am lvh vdab: qgbc ldcn.
            Top 3 Possibilities:
            informal slumber party conversation about effectively keeping ringlets in the hair: curl talk.
            informal slumber party conversation about effectively beeping ringlets in the hair: curl talb.
            informal slumber party conversation about effectively keeping ringlets in tpe pair: curl talk.
            
            317756 words loaded in descending order of frequency.
            nbxd lkq hqvxjl ezkhd zxhofcd qdcoxv eofoxe scjcofhl sxsuxhe, nbfo vk lkq vk? edqu sfhcdxe.
            Top 3 Possibilities:
            then you rudely scorn certain united states military members, that do you do? snub marines.
            when you rudely scorn certain united states military members, what do you do? snub marines.
            been you rudely scorn certain united states military members, beat do you do? snub marines.
            
            317756 words loaded in descending order of frequency.
            xmnqt erc anmdvnt xmhdhxhju daed dqrcj dp jkmqec vmpu kqmjpr dp kqmjpr: hrvqxdhoq hroqxdhoq.
            Top 3 Possibilities:
            cruel and hurtful criticism that tends to spread from person to person: infective invective.
            cruel and hurtful criticism that tends ta spread fram persan ta persan: infective invective.
            cruel and hurtful criticise that tends ta spread frae persan ta persan: infective invective.
            
            317756 words loaded in descending order of frequency.
            nd b n oqrppbog gbighnejtc xgr xtnco n wett-hteipg owbcphbwt incdtep? wbhpbt no qgncitj!
            Top 3 Possibilities:
            FAILED. No match found.
            
            317756 words loaded in descending order of frequency.
            uoeynv ns preeco'e yoicvoq vwov'e o yrvt gnkcxt gtoev ynktptz fcvw o snptev iqoxv: unee ynf.
            Top 3 Possibilities:
            mascot of russia's capital that's a cute bovine beast covered with a forest plant: moss cow.
            mascot of rossia's capital that's a cote bovine beast covered with a forest plant: moss cow.
            mascot of russia's capital that's a cute bovine beast covered pith a forest plant: moss cop.
            
            317756 words loaded in descending order of frequency.
            rpbqjgp apw gzpbxqnsv xg wpzqxwxoy smjya ixospw hmmsipqw, gap bqnng apwgpnh q rmms-xbxqo.
            Top 3 Possibilities:
            FAILED. No match found.
            
            317756 words loaded in descending order of frequency.
            ipkejokuen pbqqnor abpylerom qpije depwesk yniulskw dsk qip lepmnv ekv jikov: yloea qpsnnr.
            Top 3 Possibilities:
            FAILED. No match found.
            
            317756 words loaded in descending order of frequency.
            htam xun hgmp pu vgsa duppawx vgwsay hbpt rucuw dgprtao, b vbftp onffaop nobmf vuppcbmf rcgx.
            Top 3 Possibilities:
            when you want to make pottery market with color patches, i might suggest using mottling clay.
            when you want to make lottery market with color latches, i might suggest using mottling clay.
            when you want to make pottery marked with color patches, i might suggest using mottling clay.
            
            317756 words loaded in descending order of frequency.
            vyhseajt ptvqghmshnz nl srt vsgtsqrtgv yvtp af lhgvs gtvmnzptgv: tctgitzqf ctphqej vygleqtv.
            Top 3 Possibilities:
            suitable description of the stretchers used by first responders: emergency medical surfaces.
            suitable description of the stretchers used be first responders: emergence medical surfaces.
            
            -----
            
        Remaining problem:
            Still cannot decide which one is more human..
            I suppose it should be useful to apply the idea of training work embeddings..
        '''

        if not encrypted_ws:
            collection.append(curr_dict)
            return

        candidates = dict()
        for w in encrypted_ws:
            candidates[w] = self.find_candidates(w, curr_dict)
            pass

        selected = min(encrypted_ws, key=lambda w: len(candidates[w]))
        if len(candidates[selected]) <= 0:
            return

        remaining = encrypted_ws.copy()
        remaining.remove(selected)
        candidates = candidates[selected]
        for w in candidates:
            new_dict = self.extend_dict_copy(curr_dict, selected, w)
            self._solve(remaining, new_dict, collection)
        return
    pass


if __name__ == '__main__':
    prob_0521_1 = QuipProb('AMEKBTDC JCGTYHB UDBLF QKMOHBJDLAKM DYKGL HEEHQLAOHCF NHHUAMZ BAMZCHLJ AM LVH VDAB: QGBC LDCN.', 'J', 'S',
                           answer='informal slumber party conversation about effectively keeping ringlets in the hair: curl talk.')
    prob_0521_2 = QuipProb('NBXD LKQ HQVXJL EZKHD ZXHOFCD QDCOXV EOFOXE SCJCOFHL SXSUXHE, NBFO VK LKQ VK? EDQU SFHCDXE.', 'H', 'R',
                           answer='when you rudely scorn certain united states military members, what do you do? snub marines.')
    prob_0521_3 = QuipProb('XMNQT ERC ANMDVNT XMHDHXHJU DAED DQRCJ DP JKMQEC VMPU KQMJPR DP KQMJPR: HRVQXDHOQ HROQXDHOQ.', 'X', 'C',
                           answer='cruel and hurtful criticism that tends to spread from person to person: infective invective.')

    prob_0524_1 = QuipProb('ND B N OQRPPBOG GBIGHNEJTC XGR XTNCO N WETT-HTEIPG OWBCPHBWT INCDTEP? WBHPBT NO QGNCITJ!', 'D', 'M')
    prob_0524_2 = QuipProb("UOEYNV NS PREECO'E YOICVOQ VWOV'E O YRVT GNKCXT GTOEV YNKTPTZ FCVW O SNPTEV IQOXV: UNEE YNF.", 'G', 'B')
    prob_0524_3 = QuipProb('RPBQJGP APW GZPBXQNSV XG WPZQXWXOY SMJYA IXOSPW HMMSIPQW, GAP BQNNG APWGPNH Q RMMS-XBXQO.', 'A', 'H')

    prob_0531_1 = QuipProb('IPKEJOKUEN PBQQNOR ABPYLEROM QPIJE DEPWESK YNIULSKW DSK QIP LEPMNV EKV JIKOV: YLOEA QPSNNR.', 'P', 'R')
    prob_0531_2 = QuipProb('HTAM XUN HGMP PU VGSA DUPPAWX VGWSAY HBPT RUCUW DGPRTAO, B VBFTP ONFFAOP NOBMF VUPPCBMF RCGX.', 'V', 'M')
    prob_0531_3 = QuipProb('VYHSEAJT PTVQGHMSHNZ NL SRT VSGTSQRTGV YVTP AF LHGVS GTVMNZPTGV: TCTGITZQF CTPHQEJ VYGLEQTV.', 'P', 'D')

    all_probs = [prob_0521_1, prob_0521_2, prob_0521_3,
                 prob_0524_1, prob_0524_2, prob_0524_3,
                 prob_0531_1, prob_0531_2, prob_0531_3]

    for prob in all_probs:
        solver = Solver(prob)
        print(prob.sentence)
        res = solver.solve()
        print('Top 3 Possibilities:')
        for s in res:
            print(s)
        print()
    pass
