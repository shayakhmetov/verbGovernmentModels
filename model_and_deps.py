__author__ = 'rim'
import sys

from add_ru_table import construct_ru_table
from parse_dict import get_dictionary, print_model, elements_print
from get_dependencies_conll import get_dependencies
import itertools
from collections import Counter
from classifier import train_and_predict


def evaluate_element(element, deps, mask):
    def check_animate(from_model, from_deps):
        if from_model == 'о/но' or from_deps == 'о/но':
            return True
        else:
            return from_deps == from_model

    if element[0] == 'INF':
        for i, w in enumerate(deps):
            if i not in mask and w['type'] == 'V':
                return [i]

    elif element[0] == 'DO:':
        for i, w in enumerate(deps):
            if i not in mask and w['type'] not in 'VS' and (w['case'] == 'В')\
                    and check_animate(element[2], w['animate']):#TODO here is check for 'Р' case
                return [i]

    elif element[0] == 'C:':
        prepositions = [i for i, w in enumerate(deps)
                        if i not in mask and w['type'] == 'S' and w['name'] in [e[0] for e in element[2]]]

        nouns = [i for i, w in enumerate(deps)
                 if i not in mask and w['type'] not in 'VS' and w['case'] in [e[1] for e in element[2]]]
        for prep, case in [(e[0], e[1]) for e in element[2]]:
            for noun_i in nouns:
                for prep_i in prepositions:
                    if prep_i < noun_i and deps[noun_i]['case'] == case and deps[prep_i]['name'] == prep:
                        return [prep_i, noun_i]

    elif element[0] == 'A:':
        if len(element) == 5:
            nouns = [i for i, w in enumerate(deps)
                     if w['type'] not in 'VS' and w['case'] == element[2] and check_animate(element[3], w['animate'])]
            prepositions = [i for i, w in enumerate(deps)
                            if w['type'] == 'S' and w['name'] == element[1]]
            for prep in prepositions:
                for noun in nouns:
                    if prep < noun:
                        return [prep, noun]
        elif len(element) == 4:
            for i, w in enumerate(deps):
                if i not in mask and w['type'] not in 'VS' and w['case'] == element[1] and check_animate(element[2], w['animate']):
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
                        current_res = list(set(next_res + current_res))
                        mask = list(set(mask + next_res))
                    else:
                        return current_res
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
        if len(exprs[0][1]) == len(deps):
            return True
    else:
        for i, expr in enumerate(exprs):
            for p in itertools.product([0, 1], repeat=len(exprs) - 1):
                bit_mask = [item for item in p]
                bit_mask.insert(i, 0)

                mask = [e[1] for j, e in enumerate(exprs) if bit_mask[j] == 1]
                evaluated_mask = []
                for m in mask:
                    for el in m:
                        if el not in evaluated_mask:
                            evaluated_mask.append(el)
                computed_result = evaluate_expr(expr[0], deps, evaluated_mask)
                if len(set((computed_result + evaluated_mask))) == len(deps):
                    return True

    return False


def check_gov_model(verb_model, verb, deps):
    def check_aspect(from_model, from_deps):
        if from_model == 'св/нсв' or from_deps == 'св/нсв':
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
                            exprs.append((elementary_expr, evaluate_expr(elementary_expr, deps, [])))
                    if evaluate_plus(exprs, deps):
                        return i, j, k
    return None


def local_print(d):
                if d['type'] not in 'VS':
                    return "%d %s %s %s" % (d['id'], d['type'], d['case'], d['animate'])
                elif d['type'] == 'S':
                    return "%d %s %s" % (d['id'], d['type'], d['name'])
                else:
                    return "%d %s" % (d['id'], d['type'])


def check_model(verb_model, verb_deps, print_not_matched=False, check_all=False):
    result = []
    everything_matched = True
    number_of_matched = 0
    for verb, deps, source in zip(verb_deps['verb'], verb_deps['all_deps'], verb_deps['sources']):
        matched = check_gov_model(verb_model, verb, deps)
        if not matched:
            if print_not_matched:
                print()
                print('ДЕРЕВО ДЛЯ: ', verb['id'], verb['name'], verb['aspect'])
                print([local_print(d) for d in deps])
                print(source, end='\n\n')
                print_model(verb_model)
                print()
            everything_matched = False
            if not check_all:
                return None, 0
        else:
            if check_all:
                number_of_matched += 1
            result.append(matched)
    if everything_matched:
        return result, 1
    elif check_all:
        return None, number_of_matched/len(verb_deps['verb'])
    else:
        return None, 0


def print_one_gov_model(model, coordinates, file=sys.stdout):
    omonim = model[coordinates[0]]
    syntax_role = omonim['syntax_roles'][coordinates[1]]
    gov_model = syntax_role['gov_models'][coordinates[2]]
    for elementary_expr in gov_model['elements']:
        if elementary_expr != '+':
            elements_print(1, elementary_expr, file=file)
        else:
            print(' ', elementary_expr, file=file)


def get_raw_gov_models(model):
    results = []
    for omonim in model:
        for syntax_role in omonim['syntax_roles']:
            for gov_model in syntax_role['gov_models']:
                result = {'verb_aspect': omonim['verb_aspect'],
                          'transitive': syntax_role['transitive'],
                          'gov_model': gov_model['elements']}
                results.append(result)
    return results


def construct_gov_model(raw_gov_models):
    omonim1 = ([gm for gm in raw_gov_models if gm['verb_aspect'] == 'св'], 'св')
    omonim2 = ([gm for gm in raw_gov_models if gm['verb_aspect'] == 'нсв'], 'нсв')
    omonim3 = ([gm for gm in raw_gov_models if gm['verb_aspect'] == 'св/нсв'], 'св/нсв')
    new_model = []
    for omonim, aspect in [omonim1, omonim2, omonim3]:
        if omonim:
            new_omonim = {'verb_aspect': aspect, 'syntax_roles': []}
            syntax_role1 = ([gm for gm in omonim if gm['transitive'] == 'п'], 'п')
            syntax_role2 = ([gm for gm in omonim if gm['transitive'] == 'нп'], 'нп')
            syntax_role3 = ([gm for gm in omonim if gm['transitive'] == 'п/нп'], 'п/нп')
            syntax_role4 = ([gm for gm in omonim if gm['transitive'] == 'возвр'], 'возвр')
            for syntax_role, transitive in [syntax_role1, syntax_role2, syntax_role3, syntax_role4]:
                if syntax_role:
                    new_syntax_role = {'gov_models': [], 'transitive': transitive}
                    for gm in syntax_role:
                        new_syntax_role['gov_models'].append({'elements': gm['gov_model']})
                    new_omonim['syntax_roles'].append(new_syntax_role)
            new_model.append(new_omonim)
    return new_model


def compute_complexity_gm(raw_gov_model):
    def compute_complexity_expr(elementary_expr):
        if elementary_expr[0] in ['DO:', 'A:', 'C:', 'INF']:
            return 1
        else:
            for element in elementary_expr:
                if element == '&&' or element == '||':
                    return len(elementary_expr)
                else:
                    return compute_complexity_expr(element)
    complexity = 0
    for elementary_expr in raw_gov_model['gov_model']:
        if elementary_expr != '+':
            complexity += compute_complexity_expr(elementary_expr)
        else:
            complexity += len(raw_gov_model['gov_model'])
    return complexity


def transform_words(words, ru_table_dict):
    transform_case = {'accusative': 'В', 'dative': 'Д', 'genitive': 'Р', 'instrumental': 'Т', 'locative': 'П'}
    transform_animate = {'yes': 'о', 'no': 'но', '-': 'о/но', '': 'о/но'}
    result = []
    for word in words:
        temp = {'name': word[2], 'type': word[4], 'id': int(word[0])}
        if temp['type'] not in 'VS':
            temp['case'] = transform_case[ru_table_dict[word[5]][3]]
            temp['animate'] = transform_animate[ru_table_dict[word[5]][0]]
        result.append(temp)
    return result


def transform_verb(verb_word, ru_table_dict):
    transform_aspect = {'progressive': 'нсв', 'perfective': 'св', 'biaspectual': 'св/нсв'}
    return {'aspect': transform_aspect[ru_table_dict[verb_word[5]][1]], 'id': int(verb_word[0]), 'name': verb_word[2]}


def main():
    big_checking = False
    unknown_checking = False
    train_and_classify = False
    construct_unknown_models = True

    print(file=sys.stderr)
    ru_table_filename = 'ru-table.tab'

    dictionary = get_dictionary(pickled=True)
    ru_table = construct_ru_table(ru_table_filename)
    ru_table_dict = ru_table['dict']

    all_verbs_dependencies = get_dependencies(dictionary, ru_table_dict)

    deps_dict = {}

    i = 0
    for verb_deps in all_verbs_dependencies:
        verb_name = verb_deps['verb'][2]
        if verb_name in deps_dict:
            deps_dict[verb_name]['all_deps'].append(transform_words(verb_deps['deps'], ru_table_dict))
            deps_dict[verb_name]['verb'].append(transform_verb(verb_deps['verb'], ru_table_dict))
            deps_dict[verb_name]['sources'].append(verb_deps['source'])
        else:
            if verb_deps['known']:
                i += 1
            deps_dict[verb_name] = {'verb': [transform_verb(verb_deps['verb'], ru_table_dict)],
                                    'all_deps': [transform_words(verb_deps['deps'], ru_table_dict)],
                                    'sources': [verb_deps['source']],
                                    'known': verb_deps['known']}

    print("All occurences =", sum([len(v['sources']) for k, v in deps_dict.items()]), file=sys.stderr)
    print("Known verbs =", i, "\tAll verbs =", len(deps_dict), file=sys.stderr)
    i = 0
    deep_i = 0.
    known = {verb_name: value for verb_name, value in deps_dict.items() if value['known']}
    unknown = {verb_name: value for verb_name, value in deps_dict.items() if not value['known']}

    # --MAIN STATISTICS--

    for verb_name, value in known.items():
        result, percent = check_model(dictionary[verb_name]['model'], value, print_not_matched=True, check_all=True)
        if result:
            i += 1
        deep_i += percent
    print("KNOWN CHECKING: %.2f" % (100*i/len(known)), "% of known verbs matched.", i, 'of', len(known), file=sys.stderr)
    print("KNOWN CHECKING: %.2f" % (100*deep_i/len(known)), "% of known verbs' occurences matched.", file=sys.stderr)

    # --EXTRA STATISTICS--
    if big_checking:
        print('\nRunning big checking...', file=sys.stderr)
        with open('compared_models.txt', 'w') as compared_models, open('not_matched_known.txt', 'w') as not_matched_known_file:
            i = 0
            accumulated_deep_i = 0.
            for verb_name, value in known.items():
                deep_i = 0.
                result, percent = check_model(dictionary[verb_name]['model'], value, check_all=False)
                if result:
                    i += 1
                    deep_i = 1
                else:
                    if percent > deep_i:
                        deep_i = percent
                    for some_verb in dictionary:
                        if some_verb != verb_name:
                            result, percent = check_model(dictionary[some_verb]['model'], value, check_all=False)
                            if result:
                                i += 1
                                deep_i = 1
                                print('-'*40, file=compared_models)
                                print('TWO MODELS:', file=compared_models)
                                print('MODEL THAT DID NOT MATCH:', verb_name, file=compared_models)
                                print_model(dictionary[verb_name]['model'], file=compared_models)
                                print('MODEL THAT MATCHED:', some_verb, file=compared_models)
                                print_model(dictionary[some_verb]['model'], file=compared_models)
                                print('GOV_MODELS THAT WAS USED:', file=compared_models)
                                for coordinates, freq in sorted(Counter(result).items(), key=lambda item: item[1], reverse=True):
                                    print('FREQ = 5:', file=compared_models)
                                    print_one_gov_model(dictionary[some_verb]['model'], coordinates, file=compared_models)
                                print(file=compared_models)
                                break
                            elif percent > deep_i:
                                deep_i = percent
                assert 0 <= deep_i <= 1
                accumulated_deep_i += deep_i
                if deep_i == 0:
                    print(verb_name, file=not_matched_known_file)

            print("BIG_CKECKING: %.2f" % (100*i/len(known)), "% of known verbs matched with one of GM in dictionary.", i, 'of', len(known), file=sys.stderr)
            # print("BIG_CKECKING: %.2f" % (100*accumulated_deep_i/len(known)), "% of known verbs' occurences matched with one of GM in dictionary", file=sys.stderr)
            #TODO print not_matched for the most likely GM

    if unknown_checking:
        print('\nRunning unknown checking...', file=sys.stderr)
        with open('not_matched_unknown.txt', 'w') as not_matched_known_file:
            i = 0
            accumulated_deep_i = 0.
            for verb_name, value in unknown.items():
                deep_i = 0.
                for some_verb in dictionary:
                    result, percent = check_model(dictionary[some_verb]['model'], value, check_all=False)
                    if result:
                        i += 1
                        deep_i = 1
                        break
                    elif percent > deep_i:
                         deep_i = percent
                assert 0 <= deep_i <= 1
                accumulated_deep_i += deep_i
                if deep_i != 1:
                    print(verb_name, file=not_matched_known_file)

            print("UNKNOWN CHECKING: %.2f" % (100*i/len(unknown)), "% of unknown verbs matched with one of GM in dictionary.", i, 'of', len(unknown), file=sys.stderr)
            # print("UNKNOWN CHECKING: %.2f" % (100*accumulated_deep_i/len(unknown)), "% of unknown verbs' occurences matched with one of GM in dictionary", file=sys.stderr)

    if construct_unknown_models:
        with open('new_models.txt', 'w') as new_models_file:
            print('\nConstructing new government models...', file=sys.stderr)
            all_raw_gov_models = []
            for verb_name, value in dictionary.items():
                for raw_gov_model in get_raw_gov_models(value['model']):
                    if raw_gov_model not in all_raw_gov_models:
                        all_raw_gov_models.append(raw_gov_model)
            all_raw_gov_models = sorted(all_raw_gov_models, key=lambda gm: compute_complexity_gm(gm))
            all_gov_models = [construct_gov_model([gm]) for gm in all_raw_gov_models]

            number_of_constructed = 0
            for verb_name, value in unknown.items():
                can_construct = True
                indices = []
                for deps, source in zip(value['all_deps'], value['sources']):
                    matched = False
                    verb_deps = {'verb': value['verb'], 'all_deps': [deps], 'sources': [source]}

                    for i, gov_model in enumerate(all_gov_models):
                        result, percent = check_model(gov_model, verb_deps)
                        if result:
                            if i not in indices:
                                indices.append(i)
                            matched = True
                            break
                    if not matched:
                        can_construct = False
                        print('cannot construct: ', verb_name, end='\t', file=sys.stderr)
                        print([local_print(d) for d in deps], file=sys.stderr)
                        break
                if can_construct:
                    number_of_constructed += 1
                    constructed_model = construct_gov_model([all_raw_gov_models[i] for i in sorted(indices)])

                    assert check_model(constructed_model, value)[0]

                    print(verb_name, file=new_models_file)
                    print_model(constructed_model, file=new_models_file)
                    print(file=new_models_file)


            print("CONSTRUCTED MODELS: %.2f" % (100*number_of_constructed/len(unknown)), "% of unknown verbs", number_of_constructed, 'of', len(unknown), file=sys.stderr)

if __name__ == '__main__':
    main()
