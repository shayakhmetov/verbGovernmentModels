__author__ = 'rim'
from sklearn.naive_bayes import MultinomialNB
import sys


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

    #in main
    # train_and_predict(all_verbs_dependencies, ru_table, dictionary)
