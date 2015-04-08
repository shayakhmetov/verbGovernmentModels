__author__ = 'rim'

from lxml import etree
from parse_dict import get_dictionary
import pymorphy2

morph = pymorphy2.MorphAnalyzer()

def get_sentences(xml_file, verbs):
    with open('new_verbs.txt', 'w') as new_verbs_file, open('verbs.txt', 'w') as verbs_with_model_file:
        number_of_sentences = 0
        new_verbs = {}
        verbs_with_model = {verb: 0 for verb in verbs.keys()}
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
                                p = [p_res for p_res in morph.parse(token.get('text').lower()) if 'VERB' in p_res.tag or 'INFN' in p_res.tag][0]
                                verb = p.normal_form
                                if verb in verbs:
                                    passes = True
                                    sentence.clear()
                                    token.clear()
                                    token_list.clear()
                                    g.clear()
                                    verbs_with_model[verb] += 1
                                else:
                                    if new_verbs.get(verb):
                                        new_verbs[verb] += 1
                                    else:
                                        new_verbs[verb] = 1
                        if passes:
                            yield sentence_text

        for verb, freq in new_verbs.items():
            if freq > 0:
                new_verbs_file.write(verb + ' ' + str(freq) + '\n')
        print('new_verbs.txt generated.')
        for verb, freq in verbs_with_model.items():
            if freq > 0:
                verbs_with_model_file.write(verb + ' ' + str(freq) + '\n')
        print('verbs.txt generated.')
        print('All sentences in corpora =', number_of_sentences)


def main():

    dictionary = get_dictionary("cleaned_dict.txt")
    # dictionary = get_dictionary("cleaned_dict.txt", write_file='dict_serialized')
    # dictionary = get_dictionary(read_file='dict_serialized')
    print('Parsing corpora...')

    # sentences = get_sentences("opencorpora_very_small.xml", dictionary)
    sentences = get_sentences("opencorpora_small.xml", dictionary)
    # sentences = get_sentences("opencorpora_medium.xml", dictionary)
    # sentences = get_sentences("opencorpora.xml", dictionary)
    length = 0
    with open("sentences_medium.txt", "w") as file_sentences:
        for sentence in set(sentences):
            file_sentences.write(sentence + '\n')
            length += 1
    print('\nResult:', length, ' sentences selected')

if __name__ == '__main__':
    main()