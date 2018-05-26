""" Prepare the words data, originated from pre-trained word embeddings. """

from os import path


class WordStats(object):
    """ Provide insights on all the words. """

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