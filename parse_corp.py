__author__ = 'rim'

from lxml import etree
import sys


def get_sentences(xml_file):
    number_of_sentences = 0
    new_verbs = {}
    tree = etree.parse(xml_file)
    root = tree.getroot()
    texts_list = root.findall("text")
    root.clear()
    for text in texts_list:
        paragraphs = text.findall("paragraphs")
        for paragraph in paragraphs:
            paragraph_list = paragraph.findall("paragraph")
            paragraph.clear()
            for par in paragraph_list:
                sentences = par.findall("sentence")
                par.clear()
                for sentence in sentences:
                    number_of_sentences += 1
                    sentence_text = sentence.find('source').text.lower()
                    passes = False
                    tokens = sentence.find('tokens')
                    token_list = tokens.findall('token')
                    for token in token_list:
                        tfr = token.find('tfr')
                        v = tfr.find('v')
                        tfr.clear()
                        l = v.find('l')
                        v.clear()
                        g = l.find('g')
                        if g.get('v') == 'VERB' or g.get('v') == 'INFN':
                            yield sentence_text
                            sentence.clear()
                            token.clear()
                            g.clear()
                            break
                    token_list.clear()


def main():

    # dictionary = get_dictionary("cleaned_dict.txt")
    print('Parsing corpora...')

    # sentences = get_sentences("opencorpora_very_small.xml")
    sentences = get_sentences("opencorpora_small.xml")
    # sentences = get_sentences("opencorpora_medium.xml")
    # sentences = get_sentences("opencorpora.xml")
    length = 0
    with open("sentences_small.txt", "w") as file_sentences:
        for sentence in set(sentences):
            file_sentences.write(sentence + '\n')
            length += 1
    print('\nResult:', length, ' sentences selected', file=sys.stderr)

if __name__ == '__main__':
    main()