__author__ = 'rim'
import sys


def clean_clause(clause, ru_table_dict):
    clause = [w for w in clause if w[7] not in ['количест', 'опред', 'PUNC']]
    for word in clause:
        if word[4] == 'V':
            yield word
        else:
            s = word[5]
            while s and s not in ru_table_dict:
                s = s[:-1]
            if s:
                word[5] = s
            yield word


def get_verb_dependencies(one_clause, dictionary, ru_table_dict):
    verbs_dependencies = []
    one_clause = list(clean_clause(one_clause, ru_table_dict))
    for word in one_clause:
        dependencies = []
        if word[2] in dictionary:
            known = True
        else:
            known = False
        denied_words = [".", "?", "!", "…", "iq", "что", "благодаря"]
        denied_cases = ['nominative', '*n', 'vocative', '-']

        if word[3] == 'V' and word[2] != '<unknown>' and word[5] in ru_table_dict:
            for depended_word in one_clause:
                if word != depended_word and depended_word[5] in ru_table_dict and int(depended_word[6]) == int(word[0]) \
                        and abs(int(word[0]) - int(depended_word[0]) < 4)\
                        and depended_word[2] not in denied_words and depended_word[4] in 'NSVP':
                    if not (depended_word[4] in 'NP' and ru_table_dict[depended_word[5]][3] in denied_cases)\
                            and not (depended_word[4] == 'V' and depended_word[1] != depended_word[2]):
                        if depended_word[2] == '<unknown>':
                            depended_word[2] = depended_word[1]
                        dependencies.append(depended_word)
                        if depended_word[4] == 'S':
                            for deep_depended_word in one_clause:
                                if word != deep_depended_word and depended_word != deep_depended_word \
                                        and abs(int(deep_depended_word[0]) - int(depended_word[0]) < 3) and deep_depended_word[5] in ru_table_dict \
                                        and int(deep_depended_word[6]) == int(depended_word[0]) and deep_depended_word[4] in 'NMPA' \
                                        and deep_depended_word[2] not in denied_words:
                                    if not (deep_depended_word[4] in 'NMPA' and ru_table_dict[deep_depended_word[5]][3] in denied_cases):
                                        if deep_depended_word[2] == '<unknown>':
                                            deep_depended_word[2] = deep_depended_word[1]
                                        dependencies.append(deep_depended_word)
        if dependencies:
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

