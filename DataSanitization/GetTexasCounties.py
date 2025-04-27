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
counties = []
with open(sys.argv[1]) as datfile:
    # strip fields for header
    header = datfile.readline().strip().split(delimiter)
    print(header)

    # open the output file
    with open('texasCountyInfo.csv', 'w', newline='',  encoding='utf-8') as csvfile:
        csvfile.truncate() # clear csv file
        spamreader = csv.DictReader(datfile, header, delimiter='|')
        writer = csv.DictWriter(csvfile, header)
        writer.writeheader()
        
        # read dat
        # only get texas plans
        i = 0 # counter for total number of plans
        numTX = 0 # counter for number of texas plans
        ratingAreaDist = {}
        for row in spamreader:
            if row['State'] == 'Texas': # service IDs are formatted by 'abbreviated state', 'S', '###'
                ratingAreaDist[row['Rating Area ID']] = ratingAreaDist.get(row['Rating Area ID'], 0) + 1
                if row['County'] not in counties:
                    counties.append(row['County'])
                else:
                    i += 1
                writer.writerow(row)
                numTX += 1

    csvfile.close()
    print(numTX)
    print(len(counties))
    print(i)
    print(ratingAreaDist)
    print(counties)