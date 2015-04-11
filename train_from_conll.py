__author__ = 'rim'
import sys
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import MultinomialNB
from sklearn.feature_extraction import FeatureHasher
from add_ru_table import construct_ru_table
from parse_dict import get_dictionary


number_of_new_examples, number_of_good_examples = 1000000, 1000000
n_of_new_verbs, n_of_good_verbs = 0, 0


def get_verbs_dependencies(one_clause, dictionary, ru_table_dict):
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
                if depended_word[6] == word[0] and depended_word[4] in 'NSAV' and depended_word[5] not in ru_table_dict:
                    dependencies = []
                    break
                if word != depended_word and depended_word[5] in ru_table_dict and depended_word[6] == word[0]\
                        and depended_word[2] not in [".", "?", "!", "iq", "<unknown>"] and depended_word[4] in 'NASV':
                    if not (depended_word[4] in 'NA' and ru_table_dict[depended_word[5]][3] == 'nominative'):
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
                verbs_dependencies = get_verbs_dependencies(one_clause, dictionary, ru_table_dict)
                if verbs_dependencies:
                    for verb_dependencies in verbs_dependencies:
                        yield verb_dependencies
                one_clause = []
            else:
                line = [w.strip() for w in line.rstrip().split()]
                assert len(line) == 10
                one_clause.append(line)

        if one_clause:
            verbs_dependencies = get_verbs_dependencies(one_clause, dictionary, ru_table_dict)
            if verbs_dependencies:
                for verb_dependencies in verbs_dependencies:
                    yield verb_dependencies


def add_word_features(word, all_deprel, ru_table):
    features = []
    values3 = {c: i for i, c in enumerate('NSV')}
    # values4 = {c: i for i, c in enumerate(' -,ACIMNPQRSV')}
    values7 = all_deprel

    features.append(values3[word[3]] + 1)
    features.append(values7[word[7]] + 1)
    def select_important(vector_from_table):
        return [v + 1 for i, v in enumerate(vector_from_table) if i in {0, 1, 3, 6, 7, 10, 11, 12, 15, 16, 17, 18}]
    features += select_important(ru_table['vectors'][ru_table['dict'][word[5]]])

    return features


def construct_features(verb_deps, all_deprel, ru_table):
    features = []
    verb = verb_deps['verb']
    deps = verb_deps['deps']

    features += add_word_features(verb, all_deprel, ru_table)
    word_features_len = len(features)

    left_deps = [d for d in deps if int(d[0]) < int(verb[0])]
    right_deps = [d for d in deps if int(d[0]) > int(verb[0])]

    for i in range(2):
        if i < len(right_deps):
            features += add_word_features(right_deps[i], all_deprel, ru_table)
            features.append(int(right_deps[i][0]) - int(verb[0]))
        else:
            features += [0]*(word_features_len + 1)

    for i in range(2):
        if len(left_deps) - i - 1 >= 0:
            features += add_word_features(left_deps[-(i + 1)], all_deprel, ru_table)
            features.append(int(verb[0]) - int(left_deps[-(i + 1)][0]))
        else:
            features += [0]*(word_features_len + 1)

    return features


def ru_table_to_vec(ru_table):
    new_dict = [(key, ru_table['dict'][key]) for key in ru_table['dict'].keys()]
    for i, (key, values) in enumerate(new_dict):
        ru_table['dict'][key] = i
    new_dict = [values for key, values in new_dict]
    vectors = []
    range_of_values = [[]]*len(new_dict[0])
    for values in new_dict:
        for i in range(len(values)):
            if values[i] not in range_of_values[i]:
                range_of_values[i].append(values[i])
    for values in new_dict:
        vectors.append([range_of_values[i].index(v) for i, v in enumerate(values)])
    return vectors


def construct_verb_model(list_verb_deps, ru_table):
    verb_models = []
    for verb_deps in list_verb_deps:
        verb = verb_deps['verb']
        deps = verb_deps['deps']
        left_valents = [d for d in deps if int(d[0]) < int(verb[0])]
        right_valents = [d for d in deps if int(d[0]) > int(verb[0])]


def train_and_predict(verbs_dependencies, ru_table, dictionary):
    ru_table['vectors'] = ru_table_to_vec(ru_table)

    all_deprel_filename = 'all_deprel.txt'
    all_deprel = {}
    with open(all_deprel_filename, 'r') as file:
        for i, tag in enumerate(file):
            tag = tag.strip()
            all_deprel[tag] = i

    verbs = {}
    data_set, targets = [], []

    control_set, new_verbs = [], []

    for verb_dependencies in verbs_dependencies:
        if verb_dependencies['known']:
            data_set.append(construct_features(verb_dependencies, all_deprel, ru_table))
            targets.append(dictionary[verb_dependencies['verb'][2]]['id'])
            verbs[dictionary[verb_dependencies['verb'][2]]['id']] = verb_dependencies['verb'][2]
        else:
            control_set.append(construct_features(verb_dependencies, all_deprel, ru_table))
            new_verbs.append(verb_dependencies['verb'][2])


    print('Good examples', len(data_set), '\tControl examples', len(control_set), '\tNumber of features ', len(data_set[0]), file=sys.stderr)
    # clf = RandomForestClassifier(n_estimators=10, max_features=1)
    clf = MultinomialNB()
    print('Training the model...', file=sys.stderr)
    clf.fit(data_set, targets)
    print('Predicting control verbs...', file=sys.stderr)
    predicted = clf.predict(control_set)
    print(*[(new_verbs[i], verbs[d]) for i, d in enumerate(predicted)], sep='\n')


def main():
    conll_filename = 'malt-1.5/output_parser'
    ru_table_filename = 'ru-table-extended.tab'

    dictionary = get_dictionary()
    ru_table = construct_ru_table(ru_table_filename)
    ru_table_dict = ru_table['dict']
    all_verbs_dependencies = get_conll_verbs(conll_filename, dictionary, ru_table_dict)

    deps_dict = {}

    def transform_words(words):
        return [{'name': word[2], 'case': ru_table_dict[word[5]][3], 'type': word[4], 'animate': ru_table_dict[word[5]][0], 'id': int(word[0])} for word in words]

    def transform_verb(verb_word):
        return {'aspect': ru_table_dict[verb_word[5]][1], 'id': int(verb_word[0])}

    for verb_deps in all_verbs_dependencies:
        verb_name = verb_deps['verb'][2]
        if verb_name in deps_dict:
            deps_dict[verb_name]['all_deps'].append(transform_words(verb_deps['deps']))
            deps_dict[verb_name]['verb'].append(transform_verb(verb_deps['verb']))
            deps_dict[verb_name]['sources'].append(verb_deps['source'])
        else:
            deps_dict[verb_name] = {'verb': [transform_verb(verb_deps['verb'])], 'all_deps': [transform_words(verb_deps['deps'])], 'sources': [verb_deps['source']]}

    for verb, value in deps_dict.items():
        # print(' '*10, verb, value['verb'])
        print(verb)
        for verb, deps, source in zip(value['verb'], value['all_deps'], value['sources']):
            print(verb, [(w['id'], w['type']) for w in deps], sep='\t')
            print(source)
            # train_and_predict(all_verbs_dependencies, ru_table, dictionary)
        print()
if __name__ == '__main__':
    main()
