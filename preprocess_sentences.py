__author__ = 'rim'
import sys
import re

for line in sys.stdin:
    line = re.sub('«', '', line.strip().lower())
    line = re.sub('»', '', line)
    line = re.sub('•', '', line)
    print(line)