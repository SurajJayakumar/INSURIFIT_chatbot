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

# declare NER we'd like to ignore in the data
badVals = {"", "N/A", "NA", "Not Applicable"}



# open provided file
with open(sys.argv[1], "r", encoding="utf-8") as datfile:
    # strip fields for header
    header = datfile.readline().strip().split(delimiter)
    print(header)

    # open the output file
    with open('output.csv', 'w', newline='',  encoding='utf-8') as csvfile:
        csvfile.truncate() # clear csv file
        spamreader = csv.DictReader(datfile, header, delimiter='|')
        writer = csv.DictWriter(csvfile, header)
        writer.writeheader()
        
        # read dat
        # only get texas plans
        i = 0 # counter for total number of plans
        numTX = 0 # counter for number of texas plans
        for row in spamreader:
            if row['Service Area ID'][0:2] == 'TX': # service IDs are formatted by 'abbreviated state', 'S', '###'
                writer.writerow(row)
    csvfile.close()
    
    with open('output.csv', 'r', newline='',  encoding='utf-8') as csvfile:
        csvfile.seek(0) # return to start of file
        # iterate over plans, parse out all named entities for each field
        with open('uniquePlanValues.json', 'w+', newline='', encoding='utf-8') as namedEntitiesFile:
            namedEntitiesFile.truncate() # reset file
            outputReader = csv.DictReader(csvfile, header, delimiter=',')
            NERWriter = csv.DictWriter(namedEntitiesFile, header)

            # create multidimensional array for NER items
            NERKeys = header
            NERData = []
            
            i = 0
            for item in header:
                csvfile.seek(0) # seek to begining of file
                next(outputReader) # dump header line
                #outputReader.line_num = 0
                NERData.append([])
                for row in outputReader: 
                    if row[item] != "" and row[item] not in NERData[i]:
                        NERData[i].append(row[item])
                    
                i += 1

            # check if there are any empty fields
            i = 0
            while i < len(NERKeys):
                if len(NERData[i]) <= 1:
                    del NERData[i]
                    del NERKeys[i]
                    continue # do not increment since we're removing a row
                i += 1

            NER_Json = dict(zip(NERKeys, NERData))
            json.dump(NER_Json, namedEntitiesFile, indent=4)


        

    csvfile.close()

exit
