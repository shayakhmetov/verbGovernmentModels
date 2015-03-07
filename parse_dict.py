#coding=utf-8
__author__ = 'rim'
import codecs
import sys
from pyparsing import Word, Optional, Group, Literal, ParseException, OneOrMore, Forward, delimitedList, oneOf

rus_alphas = 'ЁЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ'
rus_lower_alphas = rus_alphas.lower()
digits = '1234567890'

def parse_dict(filename):
    dict = {}
    err_number = 0
    error_file = open('errors.txt', 'w')

    with codecs.open(filename, 'r', 'utf-8') as f:
        for line in f:
            try:
                [word, gov_model] = parse_line(line)
                dict[word] = gov_model
            except ParseException as pe:
                err_number += 1
                if len(line) < 70 or True:
                    print(pe.line)
                    print(" "*(pe.column - 1) + "^")
                    print(" ", pe, '\n')
                error_file.write(line)

    return dict, err_number


def parse_line(line):
    l_bracket = Literal('[').suppress()
    r_bracket = Literal(']').suppress()
    l_paren = Literal('(').suppress()
    r_paren = Literal(')').suppress()
    l_brace = Literal('{').suppress()
    r_brace = Literal('}').suppress()

    sem_classes = Group(l_paren + delimitedList(Word(digits), delim=',') + r_paren)

    animate = oneOf('о но о/но')
    preposition = Word(rus_lower_alphas)
    word_case = oneOf('Р Р2 Д В Т П П2')
    question = oneOf('где куда откуда')

    # prepositional_group = preposition + word_case + Optional(sem_classes)
    prepositional_group = Optional(preposition) + Optional(word_case) + Optional(sem_classes)

    c_description = delimitedList(prepositional_group, delim=',')
    c_descriptions = question + c_description

    a_description = (preposition + word_case + animate + sem_classes) | (word_case + animate + sem_classes)
    a_descriptions = delimitedList(a_description, delim=',')

    do_description = (Literal('В') + animate + sem_classes) | (Literal('Р2') + animate + sem_classes)
    do_descriptions = delimitedList(do_description, delim=',')

    or_and = oneOf('|| &&')
    elements = Forward()
    element = (Literal('DO:') + do_descriptions) | (Literal('A:') + a_descriptions) | (Literal('C:') + c_descriptions)
    elements_tail = Optional(or_and + elements)
    # elements << (element + or_and + elements | element | l_paren + elements + r_paren |
    #              l_paren + element + or_and + elements + r_paren)
    elements << (element + elements_tail | l_paren + elements + r_paren + elements_tail)


    gov_model = Group(l_paren + elements + r_paren)
    gov_models = OneOrMore(gov_model)

    transitive = oneOf('п нп п/нп возвр')
    # syntax_role = Group(l_brace + transitive + Optional(gov_models) + r_brace)
    syntax_role = Group(l_brace + transitive + gov_models + r_brace)
    syntax_roles = OneOrMore(syntax_role)

    verb_aspect = oneOf('св нсв св/нсв')

    # omonim = Group(l_bracket + Optional(sem_classes) + Optional(verb_aspect) + Optional(syntax_roles) + r_bracket)
    omonim = Group(l_bracket + verb_aspect + syntax_roles + r_bracket) # Optional(sem_classes)

    verb_name = Word(rus_alphas)

    dict_element = verb_name + Group(OneOrMore(omonim))

    if line[-1] == '\n':
        line = line[:-1]

    return dict_element.parseString(line)

if __name__ == '__main__':
    filename = 'temp.txt'
    # filename = 'cleaned_dict.txt'
    # filename = 'dict.txt'
    print('Parsing ...\n')
    dict_res, err_number = parse_dict(filename)
    print('\nParsing completed!\n')
    # for key, val in dict_res.items():
    #     print(key, val)
    print('\nParsing results:\nTotal ', len(dict_res) + err_number, '\nParsed ', len(dict_res), '\nNotParsed ', err_number)