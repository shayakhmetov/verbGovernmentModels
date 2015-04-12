__author__ = 'rim'
import sys

from add_ru_table import construct_ru_table
from parse_dict import get_dictionary, print_model
from get_dependencies_conll import get_dependencies


def evaluate_element(element, deps, mask):
    def check_animate(from_model, from_deps):
        if from_model == 'о/но':
            return True
        else:
            return from_deps == from_model

    if element[0] == 'INF':
        for i, w in enumerate(deps):
            if i not in mask and w['type'] == 'V': #TODO infinitive
                return [i]

    elif element[0] == 'DO:':
        for i, w in enumerate(deps):
            if i not in mask and w['type'] == 'N' and w['case'] == 'В' and check_animate(element[2], w['animate']):
                return [i]

    elif element[0] == 'C:':
        prepositions = [i for i, w in enumerate(deps)
                        if i not in mask and w['type'] == 'S' and w['name'] in [e[0] for e in element[2]]]

        nouns = [i for i, w in enumerate(deps)
                 if i not in mask and w['type'] == 'N' and w['case'] in [e[1] for e in element[2]]]
        for prep, case in [(e[0], e[1]) for e in element[2]]:
            for noun_i in nouns:
                for prep_i in prepositions:
                    if prep_i < noun_i and deps[noun_i]['case'] == case and deps[prep_i]['name'] == case:
                        return [prep_i, noun_i]

    elif element[0] == 'A:':
        if len(element) == 5:
            nouns = [i for i, w in enumerate(deps)
                     if w['type'] == 'N' and w['case'] == element[2] and check_animate(element[3], w['animate'])]
            prepositions = [i for i, w in enumerate(deps)
                            if w['type'] == 'S' and w['name'] == element[1]]
            for prep in prepositions:
                for noun in nouns:
                    if prep < noun:
                        return [prep, noun]
        elif len(element) == 4:
            for i, w in enumerate(deps):
                if i not in mask and w['type'] == 'N' and w['case'] == element[1] and check_animate(element[2], w['animate']):
                    return [i]
        else:
            assert False
    return []


def evaluate_expr(elementary_expr, deps, mask):
    if elementary_expr[0] in ['DO:', 'A:', 'C:', 'INF']:
        return evaluate_element(elementary_expr, deps, mask)
    else:
        current_res = evaluate_expr(elementary_expr[0], deps, mask)
        mask = list(set(mask + current_res))
        i = 1
        while i < len(elementary_expr) - 1:
            if elementary_expr[i] == '&&':
                if current_res:
                    next_res = evaluate_expr(elementary_expr[i+1], deps, mask)
                    if next_res:
                        current_res += next_res
                        mask = list(set(mask + current_res))
                else:
                    return []
            elif elementary_expr[i] == '||':
                next_res = evaluate_expr(elementary_expr[i+1], deps, [m for m in mask if m not in current_res])
                if next_res and len(next_res) > len(current_res):
                    mask = [m for m in mask if m not in current_res]
                    current_res = next_res
                    mask = list(set(mask + next_res))
            i += 2
        return current_res


def evaluate_plus(exprs, deps):
    if len(exprs) == 1:
        if len(exprs[0]) == len(deps):
            return True
    else:
        result = set()
        for expr in exprs:
            for index in expr:
                result.add(index)
        if len(result) == len(deps):
            return True
    return False


def check_gov_model(verb_model, verb, deps):
    def check_aspect(from_model, from_deps):
        if from_model == 'п/нп' or from_model == 'возвр': #TODO возвр и п/нп
            return True
        else:
            return from_model == from_deps

    for i, omonim in enumerate(verb_model):
            # if not check_aspect(omonim['verb_aspect'], verb['aspect']):
            #     continue
            for j, syntax_role in enumerate(omonim['syntax_roles']):
                #TODO transitive check
                for k, gov_model in enumerate(syntax_role['gov_models']):
                    exprs = []
                    for elementary_expr in gov_model['elements']:
                        if elementary_expr != '+':
                            exprs.append(evaluate_expr(elementary_expr, deps, []))
                    if evaluate_plus(exprs, deps):
                        return i, j, k
    return None


def check_model(verb_model, verb_deps):
    result = []
    for verb, deps, source in zip(verb_deps['verb'], verb_deps['all_deps'], verb_deps['sources']):
        matched = check_gov_model(verb_model, verb, deps)
        if not matched:
            def local_print(d):
                if d['type'] == 'N':
                    return "%d %s %s %s" % (d['id'], d['type'], d['case'], d['animate'])
                elif d['type'] == 'S':
                    return "%d %s %s" % (d['id'], d['type'], d['name'])
                else:
                    return "%d %s" % (d['id'], d['type'])
            print()
            print('ДЕРЕВО ДЛЯ: ', verb['id'], verb['name'], verb['aspect'])
            print([local_print(d) for d in deps])
            print(source, end='\n\n')
            print_model(verb_model)
            print()
            return None
        else:
            result.append(matched)
    return result


def main():
    ru_table_filename = 'ru-table.tab'

    dictionary = get_dictionary()
    ru_table = construct_ru_table(ru_table_filename)
    ru_table_dict = ru_table['dict']

    all_verbs_dependencies = get_dependencies(dictionary, ru_table_dict)

    deps_dict = {}

    def transform_words(words):
        transform_case = {'accusative': 'В', 'dative': 'Д', 'genitive': 'Р', 'instrumental': 'Т', 'locative': 'П'}
        transform_animate = {'yes': 'о', 'no': 'но'}#  '': 'о/но'}
        result = []
        for word in words:
            temp = {'name': word[2], 'type': word[4], 'id': int(word[0])}
            if temp['type'] == 'N':
                temp['case'] = transform_case[ru_table_dict[word[5]][3]]
                temp['animate'] = transform_animate[ru_table_dict[word[5]][0]]
            result.append(temp)
        return result

    def transform_verb(verb_word):
        transform_aspect = {'progressive': 'нсв', 'perfective': 'св'}#'': 'св/нсв'}
        return {'aspect': transform_aspect[ru_table_dict[verb_word[5]][1]], 'id': int(verb_word[0]), 'name': verb_word[2]}

    i = 0
    for verb_deps in all_verbs_dependencies:
        verb_name = verb_deps['verb'][2]
        if verb_name in deps_dict:
            deps_dict[verb_name]['all_deps'].append(transform_words(verb_deps['deps']))
            deps_dict[verb_name]['verb'].append(transform_verb(verb_deps['verb']))
            deps_dict[verb_name]['sources'].append(verb_deps['source'])
        else:
            if verb_deps['known']:
                i += 1
            deps_dict[verb_name] = {'verb': [transform_verb(verb_deps['verb'])],
                                    'all_deps': [transform_words(verb_deps['deps'])],
                                    'sources': [verb_deps['source']],
                                    'known': verb_deps['known']}

    print("Known verbs =", i, "\tAll verbs =", len(deps_dict), file=sys.stderr)

    # with open('verb_deps.txt', 'w') as file_deps:
    #     for verb, value in deps_dict.items():
    #         print(verb, file=file_deps)
    #         for verb, deps, source in zip(value['verb'], value['all_deps'], value['sources']):
    #             print(verb, [(w['id'], w['type']) for w in deps], sep='\t', file=file_deps)
    #             print(source, file=file_deps)
    #         print(file=file_deps)
    #     print("verb_deps.txt created.", file=sys.stderr)

    i = 0
    known = {verb_name: value for verb_name, value in deps_dict.items() if value['known']}
    for verb_name, value in known.items():
        if check_model(dictionary[verb_name]['model'], value):
            i += 1
    print("only %f percent is right" % (100*i/len(known)), file=sys.stderr)

if __name__ == '__main__':
    main()
