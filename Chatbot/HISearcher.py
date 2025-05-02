from Interfaces import *
from typing import List
import Parameters.declarations as dec
import spacy
import pandas as pd
import os

# Load Spacy model and perform preprocessing
nlp = spacy.load("en_core_web_md") # md is necessary for better recognition
nlpLabels = [nlp(label) for label in dec.BENEFIT_LABELS.keys()]

# Text
text = """
The patient scheduled a primary care treatment visit after injuring their hand.
They were also advised to attend a follow-up appointment in two weeks.
"""

# Process with Spacy
doc = nlp(text)

def extractEntities(text: str, labels: dict, threshold: int) -> list[str]:
    doc = nlp(text)
    label_keys = labels.keys()
    results = []

    for chunk in doc.noun_chunks:
        chunk_text = chunk.text.strip().lower()
        chunk_doc = nlp(chunk_text)
        
        # score text by similarity to labels
        score = [(label.text, chunk_doc.similarity(label)) for label in nlpLabels]
        # take the best match by taking the highest element in the list
        best_match = sorted(score, key=lambda x: x[1], reverse=True)[0]

        print(f"Noun chunk: '{chunk_text}'")
        print(f"  Best label match: {best_match[0]} (Similarity: {best_match[1]:.2f})")
        if best_match[1] > threshold: 
            #print(f"    --> Accepted as {match}")
            results.append(best_match[0])
            pass
    
    return(results)

# A wrapper for the HIOS database files
# Accesses, Retrieves, and filters plans from the database
class HIDatabase():

    def __init__(self, 
                 FilePath: str,
                 Files_Overview: str,
                 Files_BaseRate: list[str] = [], 
                 Files_BenefitCost: str = "", 
                 Files_Benefits: str = "", 
                 Files_PlanVariant: str = "", 
                 Files_DDCTBL_MOOP: str = "",
                 Files_SBC_Scenario: str = "", 
                 Files_BusinessRule: str = "", 
                 Files_ServiceArea: str = "", 
                 Files_RatingArea: str = ""):
        self.FilePath = os.path.join(os.path.dirname(os.path.realpath(__file__)), FilePath)
        self.Files_Overview = os.path.join(self.FilePath, Files_Overview)
        self.Files_BaseRate = [os.path.join(self.FilePath, baseRateFile) for baseRateFile in Files_BaseRate]
        self.Files_BenefitCost = os.path.join(self.FilePath, Files_BenefitCost)
        self.Files_Benefits = os.path.join(self.FilePath, Files_Benefits)
        self.Files_PlanVariant = os.path.join(self.FilePath, Files_PlanVariant)
        self.Files_DDCTBL_MOOP = os.path.join(self.FilePath, Files_DDCTBL_MOOP)
        self.Files_SBC_Scenario = os.path.join(self.FilePath, Files_SBC_Scenario)
        self.Files_BusinessRule = os.path.join(self.FilePath, Files_BusinessRule)
        self.Files_ServiceArea = os.path.join(self.FilePath, Files_ServiceArea)
        self.Files_RatingArea = os.path.join(self.FilePath, Files_RatingArea)
    
    # Cached list of currently selected plan rows
    selectedPlans = list[int]

    # File references for retrieving data
    FilePath = str
    Files_Overview = str
    Files_BaseRate = list[str]
    Files_BenefitCost = str
    Files_Benefits = str
    Files_PlanVariant = str
    Files_DDCTBL_MOOP = str
    Files_SBC_Scenario = str
    Files_BusinessRule = str
    Files_ServiceArea = str
    Files_RatingArea = str

    def ClearSelection(self):
        self.selectedPlans = []

    def pullData(self, filePath: str, columns: list[str], filterValues: list[list[str]], onlyAll: bool) -> dict:
        results = []
        
        iter_csv = pd.read_csv(
            self.Files_ServiceArea, 
            sep=',', 
            usecols=columns, 
            header=0, 
            encoding='utf-8', 
            iterator=True, 
            chunksize=1000)
        
        for chunk in iter_csv:
            
            masks = []
            for col, filters in zip(columns, filterValues):
                if not filters:  # No filter for this column
                    continue
                # Case-insensitive comparison
                mask = chunk[col].astype(str).str.upper().isin([f.upper() for f in filters])
                masks.append(mask)
            
            if not masks:
                filtered_chunk = chunk  # No filters at all
            elif onlyAll:
                combined_mask = masks[0]
                for mask in masks[1:]:
                    combined_mask &= mask
                filtered_chunk = chunk[combined_mask]
            else:
                combined_mask = masks[0]
                for mask in masks[1:]:
                    combined_mask |= mask
                filtered_chunk = chunk[combined_mask]

            # Append filtered rows as dicts
            results.extend(filtered_chunk.to_dict('records'))
    
        return results

    def GetServicerInfoForCounty(self, countyName: str) -> dict:
        resultDict = {
            'Service Area ID': "[insert name]",
            }
        resultDict['Servicer ID'] = []
        resultDict['Market Type'] = []
            
        if not os.path.exists(self.Files_ServiceArea):
            print("bad file:", self.Files_ServiceArea)
            return []
        
        iter_csv = pd.read_csv(
            self.Files_ServiceArea, 
            sep=',', 
            usecols=['HIOS Issuer ID', 'Service Area ID', 'State', 'County Name', 'Market'], 
            header=0, 
            encoding='utf-8', 
            iterator=True, 
            chunksize=1000)
        
        filtered_rows = []
        for chunk in iter_csv:
            # Filter rows where 'State' == 'Yes' OR 'County Name' matches (case-insensitive)
            filtered_chunk = chunk[
                    (chunk['State'] == 'Yes') |
                    (chunk['County Name'].str.upper() == countyName.upper())
                ]

            # Append filtered rows to the result list
            filtered_rows.extend(filtered_chunk.to_dict('records'))

        addedAreaID = False
        for row in filtered_rows:
            if addedAreaID == False:
                resultDict['Service Area ID'] = row['Service Area ID'] 
                addedAreaID = True
            resultDict['Servicer ID'].append(row['HIOS Issuer ID'])
            resultDict['Market Type'].append(row['Market'])

        return resultDict



    def FilterSelection(self, columnName: str, value: str):
        pass

    def FindPlansWithCriteria(self, criteria: list[tuple[str, str]]) -> list[str]:
        Results = []

        self.selectedPlans = Results
        return Results
    
    def FetchPlan(self, PlanID: str) -> HIPlanInfo:
        foundPlan = HIPlanInfo()
        for fileDir in self.Files_BaseRate:
            planFound = False
            with open(fileDir, "r", newline='', encoding='utf-8') as file:
                if True:
                    planFound = True
                    break
            if planFound:
                # fetch rest of plan data
                foundPlan = self.FetchPlan_Data()
                break
        pass

    def FetchPlan_Data(self, PlanID: str, Provider: str) -> HIPlanInfo:
        pass

defaultDB = HIDatabase(FilePath="../TexasFilteredData",
                    Files_Overview="RBIS.INSURANCE_PLAN_20240509202140.csv",
                    Files_BaseRate=["RBIS.INSURANCE_PLAN_BASE_RATE_FILE_20_21_22_24_25_26_20240509202140.csv",
                                    "RBIS.INSURANCE_PLAN_BASE_RATE_FILE1_20240509202140.csv",
                                    "RBIS.INSURANCE_PLAN_BASE_RATE_FILE3_20240509202140.csv",
                                    "RBIS.INSURANCE_PLAN_BASE_RATE_FILE4_20240509202140.csv",
                                    "RBIS.INSURANCE_PLAN_BASE_RATE_FILE5_20240509202140.csv",
                                    "RBIS.INSURANCE_PLAN_BASE_RATE_FILE6_20240509202140.csv",
                                    "RBIS.INSURANCE_PLAN_BASE_RATE_FILE7_20240509202140.csv",
                                    "RBIS.INSURANCE_PLAN_BASE_RATE_FILE8_20240509202140.csv",
                                    "RBIS.INSURANCE_PLAN_BASE_RATE_FILE9_20240509202140.csv",
                                    "RBIS.INSURANCE_PLAN_BASE_RATE_FILE29_20240509202140.csv"],
                    Files_BenefitCost="RBIS.INSURANCE_PLAN_BENEFIT_COST_SHARE_20240509202140.csv",
                    Files_Benefits="RBIS.INSURANCE_PLAN_BENEFITS_20240509202140.csv",
                    Files_PlanVariant="RBIS.INSURANCE_PLAN_VARIANT_20240509202140.csv",
                    Files_DDCTBL_MOOP="RBIS.INSURANCE_PLAN_VARIANT_DDCTBL_MOOP_20240509202140.csv",
                    Files_SBC_Scenario="RBIS.INSURANCE_PLAN_VARIANT_SBC_SCENARIO_20240509202140.csv",
                    Files_BusinessRule="RBIS.ISSUER_BUSINESS_RULE_20240509202140.csv",
                    Files_ServiceArea="RBIS.ISSUER_SERVICE_AREA_20240509202140.csv",
                    Files_RatingArea="RBIS.STATE_RATING_AREA_20240509202140.csv"
                    )


# Helper class for health insurance plan database searching
# See corresponding interface in chatbot/interfaces.py for usage
# TODO: implement
class HISearcher(HIPlanSearchInterface):
    def FetchPlanInfo(PlanID: str) -> HIPlanInfo:
        pass

    def ScorePlan(Plan: HIPlanInfo, fieldWeights: list[float]) -> float:
        
        pass

    def RankPlans(self, takeTopN: int) -> list[HIPlanInfo]:
        
        # filter plans by hard requirements


        # determine field weights for scoring
        fieldWeights = []
        minScore = 0.0
        currScore = 0.0

        for planID in filteredPlans:
            CurrPlanInfo = self.FetchPlanInfo(planID)
            
            # score plans
            currScore = self.ScorePlan(CurrPlanInfo, fieldWeights)
            if currScore > minScore:
                # add new plan to top results

                # set new minimum score
                minScore = currScore

        # sort plans according to score

        pass

    def ExtractUserBenefits():
        pass

    def MatchPlansFromProfile(profile: UserProfile, takeTopN: int) -> list[HIPlan]:
        pass

        
        # -- Check for invalid input

        # -- Codify profile

        # -- Extract desired benefits

        # -- Access database
        # --- order for pulling data for plans: ---
        # 1 - Pull Service area ID and HIOS Issuer ID from service area file using county name
        #   - Pull Rating area ID from rating file using county name
        # 2 - Pull plan info and ID from overview file according to availability
        # 2a- Get and Filter benefits on plan with benefit file
        # 3 - Pull base rate from base rate files
        #   - Pull benefit cost share from cost share file
        #   - Pull AV and plan URLs from plan variant file
        #   - Pull MOOP info from MOOP file
        #   - Pull SBC info from SBC file

        serviceAreaInfo = defaultDB.pullData(
            defaultDB.Files_ServiceArea, 
            ['HIOS Issuer ID', 'Service Area ID', 'State', 'County Name', 'Market'], 
            [[], [], ['Yes'], [UserProfile.location.upper()], []],
            False)
        
        ratingAreaInfo = defaultDB.pullData(
            defaultDB.Files_RatingArea, 
            ['Rating Area ID', 'Market', 'County', 'FIPS'], 
            [[], [], [UserProfile.location.upper()], []],
            False)
        
        possiblePlanIDs = defaultDB.pullData(
            defaultDB.Files_BaseRate, 
            ['Rating Area ID', 'Market', 'County', 'FIPS'], 
            [[], [], [], []],
            False)

        # -- Measure distance from each element
        # Use N element list to capture [takeTopN] best results  

        # -- Return results

if __name__ == "__main__":

    # mytext = "I have diabetes and need tier 3 drugs."

    # print(extractEntities(mytext, dec.BENEFIT_LABELS, 70))
    
    
    print(defaultDB.pullData(defaultDB.Files_ServiceArea, 
                      ['HIOS Issuer ID', 'Service Area ID', 'State', 'County Name', 'Market'], 
                      [[], [], ['Yes'], ["EL PASO"], []],
                      False))
    
    
    
    # print(db.GetServicerInfoForCountyp("EL PASO"))

