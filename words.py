""" Prepare the words data, originated from pre-trained word embeddings. """
from itertools import groupby
from os import path


class WordStats(object):
    """ Provide insights on all the words. """
    def __init__(self, words_file='words.txt', load_limit=-1):
        if not path.isfile(words_file):
            raise ValueError('Words file not found: ' + words_file)

        f = open(words_file, 'r')
        self.all = f.readlines()
        f.close()

        if load_limit > 0:
            self.all = self.all[:load_limit]
        print('%d words loaded in descending order of frequency.' % len(self.all))

        self.all = [w.strip() for w in self.all]
        self.by_len = self._divide_by_len(self.all)
        return

    def _divide_by_len(self, all):
        groups = []
        uniquekeys = []
        data = sorted(all, key=len)  # the descending order of popularity should be preserved
        for k, g in groupby(data, key=len):
            groups.append(list(g))  # Store group iterator as a list
            uniquekeys.append(k)
            pass

        d = dict()
        for i in range(len(uniquekeys)):
            d[uniquekeys[i]] = groups[i]
        return d

    @classmethod
    def valid_word(cls, word):
        """ Word is valid if it's composed all by ASCII characters. """
        if not word:
            return None
        return all(ord(c) < 128 for c in word) and word.isalpha()

    @classmethod
    def prepare_from_embeddings(cls, embedding_file='glove.6B.50d.txt', words_file='words.txt', reload=False):
        """ Word Embeddings provide words in the descending order of their frequency online. """
        def _words_file_size_mb():
            return path.getsize(words_file) / 1024 / 1024

        if path.isfile(words_file) and not reload:
            print('Words already extracted before. Not changed.',
                  'Final file size: %.2fMB' % _words_file_size_mb())
            return

        if not path.isfile(embedding_file):
            raise ValueError('Pre-trained word embedding not found. ' +
                             'You could download from e.g. GloVe <https://nlp.stanford.edu/projects/glove/>. ' +
                             'They all follow the same format.')

        fi = open(embedding_file, 'rb')
        fo = open(words_file, 'w')
        for line in fi:
            vals = line.split()
            w = vals[0].decode()

            if cls.valid_word(w):
                fo.write(w + '\n')
            pass
        fo.close()
        fi.close()

        print('Words extracted from Word Embeddings.',
              'Final file size: %.2fMB' % _words_file_size_mb())
        return
    pass


if __name__ == '__main__':
    WordStats.prepare_from_embeddings(reload=True)
    pass
