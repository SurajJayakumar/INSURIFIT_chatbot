import sys
import csv, json

# exit script if the file directory isn't provided
print(len(sys.argv))
if len(sys.argv) < 1:
    print('exiting')
    exit

# set known delimiter
delimiter = '|'
headers = []
for i in range(len(sys.argv)):
    if i == 0:
        continue

    # open provided file
    print(sys.argv[i])
    with open(sys.argv[i], "r", encoding="utf-8") as datfile:
        # strip fields for header
        header = datfile.readline().strip().split(delimiter)
        print(header)
    datfile.close()
