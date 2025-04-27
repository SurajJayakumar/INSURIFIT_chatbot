import sys
import csv, json
import os

"""
Run this on the directory containing HIOS dat files. (provide that directory as a commandline argument)
It will go through and parse out data relevant to texas. 
Issuer IDs will be added to a recognized list if found in the same dataset as a texas plan ID, but may need some help if the files are done out of order.

Some files may take a while to process due to the length of the data and needing to match field items.
"""

# exit script if the file directory isn't provided
print(len(sys.argv))
if len(sys.argv) < 2:
    print('exiting')
    quit()

# set known delimiter
delimiter = '|'

# set known identifier methods:
texasFieldNames = ['HIOS Plan ID', 'Plan ID', 'Insurance Plan Identifier', 'Service Area ID', 'HIOS Issuer ID', 'Service Area ID', 'State']
texasIssuerIDs = []

def isTexas(IDType: str, input: str) -> bool:
    texasFound = False
    # my computer wanted to use python 3.8; this can be swapped out with a switch block
    if IDType == 'Plan ID' or IDType == 'HIOS Plan ID' or IDType == 'Insurance Plan Identifier':
        texasFound = bool(input[5:7] == 'TX')
    elif IDType == 'Service Area ID':
        texasFound = bool(input[0:2] == 'TX')
    elif IDType == 'HIOS Issuer ID':
        texasFound = bool(texasIssuerIDs.__contains__(input))
    elif IDType == 'State':
        texasFound = bool(input.lower() == 'texas' or input.lower() == 'tx')
    else:
        texasFound = False
    return texasFound

"""
Processing takes a while so we add a loading bar
https://stackoverflow.com/questions/3173320/text-progress-bar-in-terminal-with-block-characters
"""

# Print iterations progress
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    # Print New Line on Complete
    if iteration == total: 
        print()

def getFileRows(file_path: str) -> int:
    try:
        with open(file_path, 'r') as file:
            row_count = sum(1 for row in file)
        return row_count
    except FileNotFoundError:
        return f"Error: File not found: {file_path}"

directory = sys.argv[1]
files = os.listdir(sys.argv[1])
for file in files:
    if file.endswith(".dat"):
        print(file)
        numRowsTotal = getFileRows(directory + '/' + file)
        with open(directory + '/' + file) as datfile:
            header = datfile.readline().strip().split(delimiter)
            print(header)

            addIssuers = False
            if ('Plan ID' in header or 'HIOS Plan ID' in header or 'Insurance Plan Identifier' in header) and 'HIOS Issuer ID' in header:
                addIssuers = True
            
            IDType = ""
            for fieldName in texasFieldNames:
                if fieldName in header:
                    IDType = fieldName
                    break
            if IDType == "":
                break
            print("Extracting using IDType: ", IDType)

            with open(file.replace(".dat", ".csv"), 'w', newline='', encoding='utf-8') as csvfile:
                csvfile.truncate() # clear csv file if it is there
                spamreader = csv.DictReader(datfile, header, delimiter='|')
                writer = csv.DictWriter(csvfile, header)
                writer.writeheader()
                
                numRows = 0
                totalRows = 0
                for row in spamreader:
                    totalRows += 1
                    if isTexas(IDType, row[IDType]) == True:
                        numRows += 1
                        writer.writerow(row)
                        if addIssuers and row['HIOS Issuer ID'] not in texasIssuerIDs:
                            texasIssuerIDs.append(row['HIOS Issuer ID'])
                    if totalRows % 50 == 0: # update only so often to save performance
                        printProgressBar(totalRows, numRowsTotal, prefix = 'Progress:', suffix = 'Complete', length = 50)
                printProgressBar(numRowsTotal+1, numRowsTotal, prefix = 'Progress:', suffix = 'Complete', length = 50)
                print("\nrows written: ", numRows, " / ", totalRows)

            csvfile.close()
        datfile.close()

print(texasIssuerIDs)