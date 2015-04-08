__author__ = 'rim'


def construct_ru_table(ru_table_filename):
    ru_table = {'dict': {}}
    with open(ru_table_filename, 'r') as ru_table_file:
        for i, line in enumerate(ru_table_file):
            line = line.rstrip().split('\t')
            if len(line) < 20:
                for j in range(20 - len(line)):
                    line.append('')
            assert len(line) == 20
            if i == 0:
                ru_table['description'] = line
            else:
                ru_table['dict'][line[0]] = line[1:]
    return ru_table


def change_field(values, index, new_value):
    values[index] = new_value
    return values


def main():
    ru_table_filename = 'ru-table.tab'
    ru_table_extended_filename = 'ru-table-extended.tab'
    ru_table = construct_ru_table(ru_table_filename)
    ru_table_dict = ru_table['dict']

    new_ru_dict = {}

    cases_len11 = {'a': 'accusative', 'l': 'locative', 'g': 'genitive', 'i': 'instrumental', 'n': 'nominative', 'd': 'dative'}
    cases_len10 = {'e': 'progressive', 'p': 'perfective'}

    for key in ru_table_dict.keys():
        new_ru_dict[key] = ru_table_dict[key]
        if len(key) == 10 and key[-1] in cases_len10:
            for c in cases_len10.keys():
                if key[:-1] + c not in ru_table_dict:
                    new_ru_dict[key[:-1] + c] = change_field(ru_table_dict[key], 1, cases_len10[c])

        if len(key) == 11:
            for c11 in cases_len11.keys():
                for c10 in cases_len10.keys():
                    if key[:-2] + c11 + c10 not in ru_table_dict:
                        temp = change_field(ru_table_dict[key], 3, cases_len11[c11])
                        new_ru_dict[key[:-2] + c11 + c10] = change_field(temp, 1, cases_len10[c10])
                    if key[:-2] + c10 + c11 not in ru_table_dict:
                        temp = change_field(ru_table_dict[key], 3, cases_len11[c11])
                        new_ru_dict[key[:-2] + c10 + c11] = change_field(temp, 1, cases_len10[c10])

    ru_table_dict = new_ru_dict

    with open(ru_table_extended_filename, 'w') as ru_table_extended_file:
        print(*ru_table['description'], sep='\t', file=ru_table_extended_file)
        for key in sorted(ru_table_dict.keys()):
            print(key, *ru_table_dict[key], sep='\t', file=ru_table_extended_file)


if __name__ == '__main__':
    main()