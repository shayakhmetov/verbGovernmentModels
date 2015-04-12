#coding=utf-8
__author__ = 'rim'
from pyparsing import Word, Optional, Group, Literal, ParseException, OneOrMore, Forward, delimitedList, oneOf
import pickle
import sys
import copy


rus_alphas = 'ЁЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ'
rus_lower_alphas = rus_alphas.lower()
digits = '1234567890'


def parse_dict(file_name, suppress_errors=True):
    verb_dict = {}
    errors_count = 0
    error_file = open('errors.txt', 'w')
    i = 0
    with open(file_name, 'r') as f:
        for line in f:
            try:
                line = line.strip()
                parsed_dict = parse_line(line)
                verb, gov_model = parsed_dict['verb'], parsed_dict['model']
                verb_dict[verb.lower()] = {"id": i, "model": gov_model, "source": line.split(" ", 1)[1]}
                i += 1
            except ParseException as pe:
                errors_count += 1
                if not suppress_errors:
                    print(pe.line, file=sys.stderr)
                    print(" "*(pe.column - 1) + "^", file=sys.stderr)
                    print(" ", pe, '\n', file=sys.stderr)
                print(line, file=error_file)
                # for key, val in verb_dict.items():
                #     print(key, val)
                # exit(1)
    return verb_dict, errors_count


def parse_line(line):
    l_bracket = Literal('[').suppress()
    r_bracket = Literal(']').suppress()
    l_paren = Literal('(').suppress()
    r_paren = Literal(')').suppress()
    l_brace = Literal('{').suppress()
    r_brace = Literal('}').suppress()

    sem_classes = Group(l_paren + delimitedList(Word(digits), delim=',') + r_paren)

    animate = oneOf('о но о/но')
    preposition = Word(rus_lower_alphas + '-')
    word_case = oneOf('Р Р2 Д В Т П П2')
    question = oneOf('где куда откуда')

    prepositional_group = Group(preposition + word_case + Optional(sem_classes))
    # prepositional_group = Optional(preposition) + Optional(word_case) + Optional(sem_classes)

    c_description = delimitedList(prepositional_group, delim=',')
    c_descriptions = question + Group(c_description)

    a_description = (preposition + word_case + animate + sem_classes) | (word_case + animate + sem_classes)
    a_descriptions = delimitedList(a_description, delim=',')

    do_description = (Literal('В') + animate + sem_classes) | (Literal('Р2') + animate + sem_classes)
    do_descriptions = delimitedList(do_description, delim=',')

    or_and = oneOf('|| &&')
    plus = Literal('+')

    # gov_model = Forward()
    elementary_expr = Forward()
    element = Group(Literal('DO:') + do_descriptions) | Group(Literal('A:') + a_descriptions) | \
              Group(Literal('C:') + c_descriptions) | Group(Literal('INF')) | l_paren + elementary_expr + r_paren

    elementary_expr << Group(element + Optional(OneOrMore(or_and + element)))

    elements = elementary_expr + Optional(OneOrMore(plus + elementary_expr))

    gov_model = Group(l_paren + elements('elements') + r_paren)
    gov_models = Group(OneOrMore(gov_model))

    transitive = oneOf('п нп п/нп возвр')
    syntax_role = Group(l_brace + transitive('transitive') + gov_models('gov_models') + r_brace)
    syntax_roles = Group(OneOrMore(syntax_role))

    verb_aspect = oneOf('св нсв св/нсв')

    omonim = Group(l_bracket + verb_aspect('verb_aspect') + syntax_roles('syntax_roles') + r_bracket)

    verb_name = Word(rus_alphas) # or rus_alphas ONLY! rus_lower_alphas + '.'

    dict_element = verb_name('verb') + Group(OneOrMore(omonim))('model')
    return dict_element.parseString(line)


def elements_print(intend, elementary_expr):
        if elementary_expr[0] not in ['DO:', 'A:', 'C:', 'INF']:
            for element in elementary_expr:
                if element == '&&' or element == '||':
                    print(' '*(intend+4), element)
                elif element[0] in ['DO:', 'A:', 'C:', 'INF']:
                    print(' '*(intend+6), element)
                else:
                    if len(element) > 1:
                        elements_print((intend+4), element)
                    else:
                        elements_print(intend, element)
        else:
            print(' '*(intend+2), elementary_expr)


def print_model(model):
    print(' '*2, 'omonims[]:')
    for i, omonim in enumerate(model):
        print()
        print(' '*4, i+1, 'omonim')
        print(' '*6, 'verb_aspect =', omonim['verb_aspect'])
        print(' '*6, 'syntax_roles[]:')
        for j, syntax_role in enumerate(omonim['syntax_roles']):
            print(' '*8, j+1, 'syntax_role')
            print(' '*10, 'transitive =', syntax_role['transitive'])
            print(' '*10, 'gov_models[]:')
            for k, gov_model in enumerate(syntax_role['gov_models']):
                print(' '*12, k+1, 'gov_model')
                print(' '*12, 'elementary_exprs[]:')
                for elementary_expr in gov_model['elements']:
                    if elementary_expr != '+':
                        elements_print(14, elementary_expr)
                    else:
                        print(' '*14, elementary_expr)


def create_pickling_element(elementary_expr):
    if elementary_expr[0] not in ['DO:', 'A:', 'C:', 'INF']:
        new_elements = []
        for element in elementary_expr:
            if element == '&&' or element == '||':
                new_elements.append(copy.copy(element))
            else:
                new_elements.append(create_pickling_element(element))
        return new_elements
    else:
        new_element = []
        new_element.append(copy.copy(elementary_expr[0]))

        def create_sem_classes(sem_classes):
            new_sem_classes = []
            for sem in sem_classes:
                if sem:
                    new_sem_classes.append(copy.copy(sem))
            return new_sem_classes

        if new_element[0] == 'INF':
            return new_element
        elif new_element[0] == 'DO:':
            new_element.append(copy.copy(elementary_expr[1]))
            new_element.append(copy.copy(elementary_expr[2]))
            new_element.append(create_sem_classes(elementary_expr[3]))
        elif new_element[0] == 'C:':
            new_element.append(copy.copy(elementary_expr[1]))
            new_c_descriptions = []
            for item in elementary_expr[2]:
                new_item = []
                for i, el in enumerate(item):
                    if i == len(item) - 1:
                        new_item.append(create_sem_classes(el))
                    else:
                        new_item.append(copy.copy(el))
                new_c_descriptions.append(new_item)
            new_element.append(new_c_descriptions)
        elif new_element[0] == 'A:':
            if len(elementary_expr) == 5:
                new_element.append(copy.copy(elementary_expr[1]))
                new_element.append(copy.copy(elementary_expr[2]))
                new_element.append(copy.copy(elementary_expr[3]))
                new_element.append(create_sem_classes(elementary_expr[4]))
            elif len(elementary_expr) == 4:
                new_element.append(copy.copy(elementary_expr[1]))
                new_element.append(copy.copy(elementary_expr[2]))
                new_element.append(create_sem_classes(elementary_expr[3]))
        return new_element


def create_pickling_model(model):
    new_model = []
    for omonim in model:
        new_omonim = {'syntax_roles': [], 'verb_aspect': copy.copy(omonim['verb_aspect'])}
        for syntax_role in omonim['syntax_roles']:
            new_syntax_role = {'transitive': copy.copy(syntax_role['transitive']), 'gov_models': []}
            for gov_model in syntax_role['gov_models']:
                new_gov_model = {'elements': []}
                for elementary_expr in gov_model['elements']:
                    if elementary_expr != '+':
                        new_gov_model['elements'].append(create_pickling_element(elementary_expr))
                    else:
                        new_gov_model['elements'].append(copy.copy(elementary_expr))

                new_syntax_role['gov_models'].append(new_gov_model)
            new_omonim['syntax_roles'].append(new_syntax_role)
        new_model.append(new_omonim)
    return new_model


def create_pickling_dict(dict_res):
    new_dict = {}
    for key, value in dict_res.items():
        new_dict[key] = {'id': copy.copy(value['id']), 'source': copy.copy(value['source'])}
        new_dict[key]['model'] = create_pickling_model(value['model'])
    return new_dict


def get_dictionary(pickled=False):
    pickled_filename = 'pickled_dict'
    if pickled:
        print('Loading dictionary from', pickled_filename, '...', file=sys.stderr)
        dict_res = pickle.load(open(pickled_filename, 'rb'))
    else:
        print('Parsing dictionary...', file=sys.stderr)
        # filename = 'temp.txt'
        # filename = 'dict_cleaned.txt'
        filename = 'dict.txt'
        dict_res, err_number = parse_dict(filename, suppress_errors=True)
        print('\nParsing completed!\n', file=sys.stderr)
        dict_res = create_pickling_dict(dict_res)

        print('Dumping dictionary...', file=sys.stderr)
        pickle.dump(dict_res, open(pickled_filename, 'wb'))
        dict_res = pickle.load(open(pickled_filename, 'rb'))

        # for key, val in dict_res.items():
        #     print(key, val['source'])
        #     print_model(val['model'])

        print('\nParsing results:\nTotal ', len(dict_res) + err_number, '\nParsed ', len(dict_res), '\nNotParsed ', err_number, file=sys.stderr)

    return dict_res


if __name__ == '__main__':
    get_dictionary()