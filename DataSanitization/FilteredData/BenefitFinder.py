import sys
import csv, json
import os
import re

# exit script if the file directory isn't provided
print(len(sys.argv))
if len(sys.argv) < 2:
    print('exiting')
    exit

# set known delimiter
delimiter = ','
headers = []
uniqueValues = []
wordDistribution = {}
field = sys.argv[2]
with open(sys.argv[1], "r", newline='', encoding="utf-8") as csvfile:
    # strip fields for header
    header = csvfile.readline().strip().split(delimiter)
    # print(header)

    spamreader = csv.DictReader(csvfile, header, delimiter=delimiter)

    for row in spamreader:
        newterm = row[field].upper().strip().replace('\n', '')
        if newterm not in uniqueValues:
            uniqueValues.append(newterm)
            newterm_words = re.split(r'[\\\s,-/]+', newterm)
            for word in newterm_words:
                wordDistribution[word] = wordDistribution.get(word, 0) + 1

print(uniqueValues)
print(wordDistribution)
command = 'echo ' + str(uniqueValues).strip() + '| clip'
os.system(command)