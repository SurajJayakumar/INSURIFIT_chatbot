import sys
import csv, json

# exit script if the file directory isn't provided
print(len(sys.argv))
print(sys.argv[1])
if len(sys.argv) < 1:
    print('exiting')
    exit

# set known delimiter
delimiter = '|'

# open provided file
with open(sys.argv[1], "r", encoding="utf-8") as datfile:
    # strip fields for header
    header = datfile.readline().strip().split(delimiter)
    print(header)

    # open the output file
    with open('output.csv', 'w', newline='',  encoding='utf-8') as csvfile:
        csvfile.truncate() # clear file
        spamreader = csv.DictReader(datfile, header, delimiter='|')
        writer = csv.DictWriter(csvfile, header)
        writer.writeheader()
        
        # read data
        countyNames = []
        i = 0 # counter for total number of plans
        numTX = 0 # counter for number of texas plans
        for row in spamreader:
            if row['Service Area ID'][0:2] == 'TX': # service IDs are formatted by 'abbreviated state', 'S', '###'
                writer.writerow(row)
                if row['County Name'] not in countyNames and row['County Name'] != '':
                    countyNames.append(row['County Name'])
        
        print('number of counties: ', len(countyNames))
        print('counties: ', countyNames)

    csvfile.close()
