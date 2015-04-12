__author__ = 'rim'
import sys

number_of_new_examples, number_of_good_examples = 1000000, 1000000
n_of_new_verbs, n_of_good_verbs = 0, 0

def clean_clause(clause):
    return [w for w in clause if w[7] not in ['количест', 'опред', 'PUNC']]


def get_verb_dependencies(one_clause, dictionary, ru_table_dict):
    verbs_dependencies = []
    one_clause = clean_clause(one_clause)
    for word in one_clause:
        dependencies = []
        if word[2] in dictionary:
            known = True
        else:
            known = False
        global n_of_good_verbs, n_of_new_verbs
        if word[3] == 'V' and word[2] != '<unknown>' and word[5] in ru_table_dict:
            for depended_word in one_clause:
                if word != depended_word and depended_word[5] in ru_table_dict and int(depended_word[6]) == int(word[0]) \
                        and abs(int(word[0]) - int(depended_word[0]) < 5)\
                        and depended_word[2] not in [".", "?", "!", "…", "iq"] and depended_word[4] in 'NSVP':
                    if not (depended_word[4] in 'NP' and ru_table_dict[depended_word[5]][3] in ['nominative', '*n', 'vocative', '-'])\
                            and not (depended_word[4] == 'V' and depended_word[1] != depended_word[2]):
                        if depended_word[2] == '<unknown>':
                            depended_word[2] = depended_word[1]
                        dependencies.append(depended_word)
                        if depended_word[4] == 'S':
                            for deep_depended_word in one_clause:
                                if word != deep_depended_word and depended_word != deep_depended_word \
                                        and abs(int(deep_depended_word[0]) - int(depended_word[0]) < 3) and deep_depended_word[5] in ru_table_dict \
                                        and int(deep_depended_word[6]) == int(depended_word[0]) and deep_depended_word[4] in 'NMP' \
                                        and deep_depended_word[2] not in [".", "?", "!", "…", "iq"]:
                                    if not (deep_depended_word[4] in 'NMP' and ru_table_dict[deep_depended_word[5]][3] in ['nominative', '*n', 'vocative', '-']):
                                        if deep_depended_word[2] == '<unknown>':
                                            deep_depended_word[2] = deep_depended_word[1]
                                        dependencies.append(deep_depended_word)
        if dependencies:
            if not known:
                n_of_new_verbs += 1
            else:
                n_of_good_verbs += 1
            dependencies = sorted(dependencies, key=lambda w: int(w[0]))
            verbs_dependencies.append({'verb': word, 'deps': dependencies, 'source': ' '.join([w[0] + '[' + w[1] + ']' for w in one_clause]), 'known': known})

    return verbs_dependencies


def get_conll_verbs(conll_filename, dictionary, ru_table_dict):
    with open(conll_filename, 'r') as conll_file:
        one_clause = []
        for line in conll_file:
            if line.strip() == '' and one_clause:
                verbs_dependencies = get_verb_dependencies(one_clause, dictionary, ru_table_dict)
                if verbs_dependencies:
                    for verb_dependencies in verbs_dependencies:
                        yield verb_dependencies
                one_clause = []
            else:
                line = [w.strip() for w in line.rstrip().split()]
                assert len(line) == 10
                one_clause.append(line)

        if one_clause:
            verbs_dependencies = get_verb_dependencies(one_clause, dictionary, ru_table_dict)
            if verbs_dependencies:
                for verb_dependencies in verbs_dependencies:
                    yield verb_dependencies


def get_dependencies(dictionary, ru_table_dict):
    conll_filename = 'malt-1.5/output_parser'
    print("Getting verb dependencies...", file=sys.stderr)
    return get_conll_verbs(conll_filename, dictionary, ru_table_dict)

