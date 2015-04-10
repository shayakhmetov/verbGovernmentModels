__author__ = 'rim'
import sys
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import MultinomialNB
from sklearn.feature_extraction import FeatureHasher
from add_ru_table import construct_ru_table


number_of_new_examples, number_of_good_examples = 1000000, 1000000
n_of_new_verbs, n_of_good_verbs = 0, 0

def construct_dictionary(verbs_filename):
    dictionary = {}
    with open(verbs_filename, 'r') as verbs_file:
        for i, line in enumerate(verbs_file):
            word = line.rstrip()
            dictionary[word] = {'id': i}
    return dictionary


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
                if word != depended_word and depended_word[5] in ru_table_dict and depended_word[6] == word[0]\
                        and depended_word[4] in 'NSV' and depended_word[2] not in [".", "?", "!", "iq", "<unknown>"]:
                    dependencies.append(depended_word)
        if dependencies:
            if not known:
                n_of_new_verbs += 1
            else:
                n_of_good_verbs += 1
            dependencies = sorted(dependencies, key=lambda w: int(w[0]))
            verbs_dependencies.append({'verb': word, 'deps': dependencies, 'clause': one_clause, 'known': known})
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


def construct_name_converter(filename, dictionary):
    with open(filename, 'r') as file:
        for i, tag in enumerate(file):
            tag = tag.strip()
            dictionary[tag] = i


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


def main():
    verbs_filename = 'all_only_verbs.txt'
    conll_filename = 'malt-1.5/output_parser'
    ru_table_filename = 'ru-table-extended.tab'

    all_deprel_filename = 'all_deprel.txt'
    all_deprel = {}

    construct_name_converter(all_deprel_filename, all_deprel)

    dictionary = construct_dictionary(verbs_filename)
    ru_table = construct_ru_table(ru_table_filename)
    ru_table_dict = ru_table['dict']
    verbs_dependencies = get_conll_verbs(conll_filename, dictionary, ru_table_dict)
    ru_table['vectors'] = ru_table_to_vec(ru_table)

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

        # if verb_dependencies['verb'][5] in ru_table_dict:
        #     inru += 1
        # else:
        #     notinru += 1
        #     print(verb_dependencies['verb'])
        # for dep in verb_dependencies['deps']:
        #     if dep[5] in ru_table_dict:
        #         inru += 1
        #     else:
        #         notinru += 1
        #         print(dep)


    print('Good examples', len(data_set), '\tControl examples', len(control_set), '\tNumber of features ', len(data_set[0]), file=sys.stderr)
    # clf = RandomForestClassifier(n_estimators=10, max_features=1)
    clf = MultinomialNB()
    print('Training the model...', file=sys.stderr)
    clf.fit(data_set, targets)
    print('Predicting control verbs...', file=sys.stderr)
    predicted = clf.predict(control_set)
    print(*[(new_verbs[i], verbs[d]) for i, d in enumerate(predicted)], sep='\n')


if __name__ == '__main__':
    main()
