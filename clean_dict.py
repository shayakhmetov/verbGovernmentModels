__author__ = 'rim'
#coding=utf-8
import sys
import re


def main():
    for line in sys.stdin:
        if not re.search(r"\{п \}|\{п  \}|\{нп \}|\{нп  \}|\{нп   \}|\{п   \}|\{п\}|"
                         r"\{нп\}|\{п/нп\}|\{п/нп \}|\{п/нп  \}|\{п/нп   \}|"
                         r"\{возвр   \}|\{возвр  \}|\{возвр \}|\{возвр\}", line):
            if not re.search(r"\[ \{", line):
                    if not re.search(r"\|\|  \)\)|&&  \)\)|\|\| \)|&& \)", line):
                        if not re.search(r"\(0\), \(0\)", line):
                            sys.stdout.write(line)

        # if re.search(r"\{п \}|\{п  \}|\{нп \}|\{нп  \}|\{нп   \}|\{п   \}|\{п\}|"
        #                  r"\{нп\}|\{п/нп\}|\{п/нп \}|\{п/нп  \}|\{п/нп   \}|"
        #                  r"\{возвр   \}|\{возвр  \}|\{возвр \}|\{возвр\}", line):
        #     sys.stdout.write(line)

if __name__ == '__main__':
    main()