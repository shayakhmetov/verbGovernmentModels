__author__ = 'rim'

import sys

from parse_dict import print_model

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
            return 0
        else:
            for element in elementary_expr:
                if element == '&&' or element == '||':
                    return 1
                else:
                    return compute_complexity_expr(element)
    complexity = 0
    for elementary_expr in raw_gov_model['gov_model']:
        if elementary_expr != '+':
            complexity += compute_complexity_expr(elementary_expr)
        else:
            complexity += 1
    return complexity

def local_print(d):
    if d['type'] not in 'VS':
        return "%d %s %s %s" % (d['id'], d['type'], d['case'], d['animate'])
    elif d['type'] == 'S':
        return "%d %s %s" % (d['id'], d['type'], d['name'])
    else:
        return "%d %s" % (d['id'], d['type'])


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


def construct_new_models(deps_dict, dictionary, filename_new_models, filename_cannot_construct, check_model):
    known = None
    used_complexities = {}
    with open(filename_new_models, 'w') as new_models_file, open(filename_cannot_construct, 'w') as cannot_construct_file:
        all_raw_gov_models = []
        for verb_name, value in dictionary.items():
            for raw_gov_model in get_raw_gov_models(value['model']):
                if raw_gov_model not in all_raw_gov_models:
                    all_raw_gov_models.append(raw_gov_model)
        all_raw_gov_models = sorted(all_raw_gov_models, key=lambda gm: compute_complexity_gm(gm))
        complexities = {}

        all_gov_models = [construct_gov_model([gm]) for gm in all_raw_gov_models]
        for gm in all_raw_gov_models:
            c = compute_complexity_gm(gm)
            if c not in complexities:
                complexities[c] = 1
            else:
                complexities[c] += 1
        print('all gov models: len =', len(all_gov_models), '\nDistribution by complexity: ', [str(k) + ':' + str(complexities[k]) for k in sorted(complexities.keys())], file=sys.stderr)
        number_of_constructed = 0
        for verb_name, value in deps_dict.items():
            can_construct = True
            indices = []
            for verb, deps, source in zip(value['verb'], value['all_deps'], value['sources']):
                matched = False
                if value['known']:
                    known = True
                else:
                    known = False
                verb_deps = {'verb': value['verb'], 'all_deps': [deps], 'sources': [source]}

                for i, gov_model in enumerate(all_gov_models):
                    result, percent = check_model(gov_model, verb_deps)
                    if result:
                        if i not in indices:
                            indices.append(i)
                        matched = True
                        c = compute_complexity_gm(all_raw_gov_models[i])
                        if c not in used_complexities:
                            used_complexities[c] = 1
                        else:
                            used_complexities[c] += 1
                        break
                if not matched:
                    can_construct = False
                    print('cannot construct: ', verb['id'], verb_name, end='\t', file=cannot_construct_file)
                    print([local_print(d) for d in deps], file=cannot_construct_file)
                    print(source, file=cannot_construct_file, end='\n\n')
                    break
            if can_construct:
                number_of_constructed += 1
                constructed_model = construct_gov_model([all_raw_gov_models[i] for i in sorted(indices)])

                assert check_model(constructed_model, value)[0]

                print(verb_name, file=new_models_file)
                print_model(constructed_model, file=new_models_file)
                print(file=new_models_file)


        print("CONSTRUCTED MODELS: %.2f" % (100*number_of_constructed/len(deps_dict)), end='', file=sys.stderr)
        if known:
            print("% of known verbs", number_of_constructed, 'of', len(deps_dict), file=sys.stderr)
        else:
            print("% of unknown verbs", number_of_constructed, 'of', len(deps_dict), file=sys.stderr)
        print('constructed compexities distribution: ', [str(k) + ':' + str(used_complexities[k]) for k in sorted(used_complexities.keys())], file=sys.stderr)

