__author__ = 'rim'
import sys

denied_vs = [".", "?", "!", "…", "iq", '<unknown>', 'её']
denied_cases = ['nominative', '*n', 'vocative', '-', '']
denied_verb_forms = ['participle', 'gerund', 'imperative']


def valid_verb(verb, ru_table_dict):
    return verb[3] == 'V' and verb[2] not in denied_vs and verb[5] in ru_table_dict \
        and ru_table_dict[verb[5]][17] not in denied_verb_forms


def valid_word(word, ru_table_dict):
    return word[3] not in 'VS' and word[5] in ru_table_dict and ru_table_dict[word[5]][3] not in denied_cases


def valid_prep(prep, ru_table_dict):
    return prep[3] == 'S' and prep[2] not in denied_vs and prep[1] not in denied_vs and prep[5] in ru_table_dict


def valid_inf(inf, ru_table_dict):
    return inf[3] == 'V' and inf[2] not in denied_vs \
        and inf[5] in ru_table_dict and ru_table_dict[inf[5]][17] == 'infinitive'


def valid_main_verb_dep(word, verb):
    main_deps = ["1-компл", "2-компл", "3-компл", "4-компл", "5-компл",
                 "1-несобст-компл", "2-несобст-компл", "3-несобст-компл", "неакт-компл"]
    return int(word[6]) == int(verb[0]) and word[7] in main_deps


def valid_word_for_prep(word, prep, ru_table_dict):
    deps = ["предл"]
    return valid_word(word, ru_table_dict) and int(word[6]) == int(prep(0)) and int(prep[0]) < int(word[0])


def get_verb_dependencies(one_clause, dictionary, ru_table_dict):
    verbs_dependencies = []
    for word in one_clause:
        dependencies = []
        if word[2] in dictionary:
            known = True
        else:
            known = False

        # if word[5] not in ru_table_dict:
        #     print('Not in a ru-table', word[5], file=sys.stderr)

        if valid_verb(word, ru_table_dict):
            depended_words = [w for w in one_clause if w != word]
            for i, depended_word in enumerate(depended_words):
                if valid_main_verb_dep(depended_word, word):
                    if valid_word(depended_word, ru_table_dict):
                        dependencies.append(depended_word)

                    elif valid_prep(depended_word, ru_table_dict):
                        deeps = [w for w in depended_words if w != depended_word]
                        for deep_depended_word in deeps:
                            if valid_word_for_prep(depended_word, deep_depended_word, ru_table_dict):
                                dependencies.append(depended_word)
                                if deep_depended_word not in dependencies:
                                    dependencies.append(deep_depended_word)
                                break

                    elif valid_inf(depended_word, ru_table_dict):
                        dependencies.append(depended_word)

        if dependencies and not (len(dependencies) == 1 and dependencies[0][3] == 'S'):
            dependencies = sorted(dependencies, key=lambda w: int(w[0]))
            verbs_dependencies.append({'verb': word, 'deps': dependencies, 'source': ' '.join([w[0] + '[' + w[1] + ']' for w in one_clause]), 'known': known})

    return verbs_dependencies


def get_conll_verbs(conll_filename, dictionary, ru_table_dict):
    n = 0
    i = 0
    with open(conll_filename, 'r') as conll_file:
        one_clause = []
        for line in conll_file:
            if line.strip() == '' and one_clause:
                verbs_dependencies = get_verb_dependencies(one_clause, dictionary, ru_table_dict)
                if verbs_dependencies:
                    i += 1
                    for verb_dependencies in verbs_dependencies:
                        yield verb_dependencies
                one_clause = []
                n += 1
            else:
                line = [w.strip() for w in line.rstrip().split()]
                assert len(line) == 10
                one_clause.append(line)

        if one_clause:
            verbs_dependencies = get_verb_dependencies(one_clause, dictionary, ru_table_dict)
            if verbs_dependencies:
                i += 1
                for verb_dependencies in verbs_dependencies:
                    yield verb_dependencies
    print("%.2f" % (100*i/n), "% of output_parser is used.", file=sys.stderr)


def get_dependencies(dictionary, ru_table_dict):
    conll_filename = 'malt-1.5/output_parser_backup90000'
    print("Getting verb dependencies...", file=sys.stderr)
    return get_conll_verbs(conll_filename, dictionary, ru_table_dict)

