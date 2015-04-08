__author__ = 'rim'

from gensim import models
import pymorphy2
import re
import itertools
import sys

morph = pymorphy2.MorphAnalyzer()


class Sentences():
    def __init__(self, filename):
        self.filename = filename

    def __iter__(self):
        with open(self.filename, 'r') as f:
            for line in f:
                yield re.split('(\W+)', line.rstrip())


class Verbs():
    def __init__(self, filename, vocab=False):
        self.filename = filename
        self.vocab = vocab

    def __iter__(self):
        with open(self.filename, 'r') as f:
            for line in f:
                verb, freq = line.rstrip().split()
                if self.vocab:
                    yield [verb]*int(freq)
                else:
                    yield verb



def get_verbs_similarity(new_verbs_filename='new_verbs.txt',
                         verbs_filename='verbs.txt', topn=10,
                         sentences_filename='sentences_medium.txt', output_filename='similarities.txt'):

    # model = models.Word2Vec(Sentences(sentences_filename), size=100, min_count=1, window=5, workers=4)
    # model.build_vocab(Sentences(sentences_filename))

    model = models.Word2Vec(size=100, min_count=1, window=5, workers=4)
    model.build_vocab(itertools.chain(Verbs(verbs_filename, vocab=True), Verbs(new_verbs_filename, vocab=True)))

    model.train(Sentences(sentences_filename))

    verbs = list(Verbs(verbs_filename))
    new_verbs = list(Verbs(new_verbs_filename))
    print(len([v for v in verbs if v in model.vocab]), 'of', len(verbs))
    print(len([v for v in new_verbs if v in model.vocab]), 'of', len(new_verbs))
    print('Model training finished. Vocabulary length =', len(model.vocab))
    l = len(new_verbs)
    with open(output_filename, 'w') as sim_file:
        for i, new_verb in enumerate(new_verbs):
            print(100*i/l, '% finished.', )
            try:
                verb_similarity = sorted([(verb, model.similarity(new_verb, verb)) for verb in verbs], key=lambda p: -p[1])[:topn]
                print(new_verb, '|', *verb_similarity, sep=' ', file=sim_file)
            except KeyError as e:
                print(new_verb, 'not in vocabulary')


def main():
    get_verbs_similarity()


if __name__ == '__main__':
    main()