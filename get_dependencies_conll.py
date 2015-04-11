__author__ = 'rim'
import sys

number_of_new_examples, number_of_good_examples = 1000000, 1000000
n_of_new_verbs, n_of_good_verbs = 0, 0


def get_verb_dependencies(one_clause, dictionary, ru_table_dict):
    verbs_dependencies = []
    for word in one_clause:
        dependencies = []
        if word[2] in dictionary:
            known = True
        else:
            known = False
        global n_of_good_verbs, n_of_new_verbs
        if word[3] == 'V' and word[2] != '<unknown>' and word[5] in ru_table_dict and int(word[6]) == 0 \
                and ((known and n_of_good_verbs < number_of_good_examples) or (not known and n_of_new_verbs < number_of_new_examples)):
            for depended_word in one_clause:
                if depended_word[6] == word[0] and depended_word[4] in 'NSV' and depended_word[5] not in ru_table_dict:
                    dependencies = []
                    break
                if word != depended_word and depended_word[5] in ru_table_dict and depended_word[6] == word[0]\
                        and depended_word[2] not in [".", "?", "!", "iq", "<unknown>"] and depended_word[4] in 'NSV':
                    if not (depended_word[4] == 'N' and ru_table_dict[depended_word[5]][3] in ['nominative', '*n', 'vocative']):
                        dependencies.append(depended_word)
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

