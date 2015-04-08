__author__ = 'rim'
#coding=utf-8
import sys
import re


def main():
    """
        standart input <- dictionary
        standart output <- cleaned dictionary
        writes error verbs by category into "dictionary_bugs/" directory
    """
    empty_models = r"\{п \}|\{п  \}|\{нп \}|\{нп  \}|\{нп   \}|\{п   \}|\{п\}|\{нп\}|" \
                   r"\{п/нп\}|\{п/нп \}|\{п/нп  \}|\{п/нп   \}|\{возвр   \}|" \
                   r"\{возвр  \}|\{возвр \}|\{возвр\}"
    empty_verb_aspect = r"\[ \{"
    logic_operators_parenth = r"\|\|  \)\)|&&  \)\)|\|\| \)|&& \)"
    logic_two_or = r"\|\|  \|\||&&  &&"
    abscent_prep_and_case = r"\(0\), \(0\)"
    strange_dot = r"•"
    two_dots_empty = r",\. \."
    models_together = r"\)[ACD]:|откуда[ACD]:"
    two_braces = r"\{(возвр|нп|п|п/нп) \{(возвр|нп|п|п/нп)"

    file_empty_models = open("dictionary_bugs/bugs_empty_models.txt", "w")
    file_empty_verb_aspect = open("dictionary_bugs/bugs_empty_verb_aspect.txt", "w")
    file_logic_operators_parenth = open("dictionary_bugs/bugs_logic_operators_parenth.txt", "w")
    file_logic_two_or = open("dictionary_bugs/bugs_logic_two_or.txt", "w")
    file_abscent_prep_and_case = open("dictionary_bugs/bugs_abscent_prepNcase.txt", "w")
    file_strange_dot = open("dictionary_bugs/bugs_strange_dot.txt", "w")
    file_two_dots_empty = open("dictionary_bugs/bugs_two_dots_empty.txt", "w")
    file_models_together = open("dictionary_bugs/bugs_models_together.txt", "w")
    file_two_braces = open("dictionary_bugs/bugs_two_braces.txt", "w")

    file_empty_models.write("# ошибки вида `{п  }`, пустые модели управления\n")
    file_empty_verb_aspect.write("# ошибки вида `[  {`, отсутствует вид глагола\n")
    file_logic_operators_parenth.write("# ошибки вида `||  ))`\n")
    file_logic_two_or.write("# ошибки вида `||  ||`\n")
    file_abscent_prep_and_case.write("# ошибки вида `(0), (0)`, отсутствие предлога и падежа\n")
    file_strange_dot.write("# ошибки вида `•`, неопознанный символ\n")
    file_two_dots_empty.write("# ошибки вида `,. .`, многоточие\n")
    file_models_together.write("# ошибки вида `)C:`, слитные модели управления без разделителей (&&, ||)\n")
    file_two_braces.write("# ошибки вида '{возвр {возвр'\n")


    for line in sys.stdin:
        if not re.search(empty_models, line):
            if not re.search(empty_verb_aspect, line):
                    if not re.search(logic_operators_parenth, line):
                        if not re.search(logic_two_or, line):
                            if not re.search(abscent_prep_and_case, line):
                                if not re.search(strange_dot, line):
                                    if not re.search(two_dots_empty, line):
                                        if not re.search(models_together, line):
                                            if not re.search(two_braces, line):
                                                sys.stdout.write(line)

        if re.search(empty_models, line):
            file_empty_models.write(line)
        if re.search(empty_verb_aspect, line):
            file_empty_verb_aspect.write(line)
        if re.search(logic_operators_parenth, line):
            file_logic_operators_parenth.write(line)
        if re.search(logic_two_or, line):
            file_logic_two_or.write(line)
        if re.search(abscent_prep_and_case, line):
            file_abscent_prep_and_case.write(line)
        if re.search(strange_dot, line):
            file_strange_dot.write(line)
        if re.search(two_dots_empty, line):
            file_two_dots_empty.write(line)
        if re.search(models_together, line):
            file_models_together.write(line)
        if re.search(two_braces, line):
            file_two_braces.write(line)

if __name__ == '__main__':
    main()