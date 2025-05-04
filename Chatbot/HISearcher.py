from Interfaces import *
from typing import List
import Parameters.declarations as dec
import spacy
import pandas as pd
import os
import timeit

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

def extractEntities(text: str, labels: dict, threshold: float) -> list[str]:
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
            filePath, 
            sep=',', 
            usecols=columns, 
            header=0, 
            encoding='utf-8', 
            iterator=True, 
            chunksize=1000)
        
        for chunk in iter_csv:
            
            masks = []
            for col, filters in zip(columns, filterValues):
                if len(filters) == 0:  # No filter for this column
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
    def __init__(self):
        return

    def RetrievePlanInfo(PlanID: str) -> HIPlanInfo:
        return None

    # can score 1 point per category base, multiplied by field weights
    def ScorePlan(self, profile: UserProfile, benefitList: list, plan: pd.DataFrame) -> float:
        planFrame = plan
        validColumns = planFrame.columns

        # score AV
        # 1 point for 100% coverage
        score_AV = 0.0
        if 'AV Calculator Output Number' in validColumns and planFrame['AV Calculator Output Number'].iloc[0] != "NaN" and planFrame['AV Calculator Output Number'].iloc[0] != "":
            score_AV = planFrame['AV Calculator Output Number'].iloc[0].astype(float) / 100.0
        elif 'Issuer Actuarial Value' in validColumns and planFrame['Issuer Actuarial Value'] != "NaN" and planFrame['Issuer Actuarial Value'] != "":
            score_AV = planFrame['Issuer Actuarial Value'].iloc[0].astype(float) / 100.0
        
        # score base rate
        # 1 point for low rate; account for tobacco usage
        score_BaseRate = 0.0
        useTobaccoRate = True #profile.tobacco #TODO: edit me to use profile tobacco
        tobacco_rate = 0.0
        if 'Tobacco' in validColumns and planFrame['Tobacco'].iloc[0] == "No Preference":
            useTobaccoRate = False
        if useTobaccoRate:
            tobacco_rate = planFrame['Individual Rate'].iloc[0].astype(float)
        else:
            tobacco_rate = planFrame['Individual Tobacco Rate'].iloc[0].astype(float)
        score_BaseRate = max(min(1.0 - (tobacco_rate / 2000.0), 1.0), 0.0)

        # score benefits
        # 1 point for all possible benefits
        score_Benefits = 0.0
        if 'Benefit' in validColumns and planFrame['Benefits'].iloc[0] != "NaN":
            score_Benefits = len(planFrame['Benefits'].iloc[0].get('Benefit Array', [])) / len(benefitList)

        # score wellness program
        # 1 point for having it
        score_WellnessProg = 0.0
        if 'Wellness Program Offered' in validColumns and planFrame['Wellness Program Offered'].iloc[0] == 'Yes':
            score_WellnessProg = 1.0


        return score_AV + score_BaseRate + score_Benefits + score_WellnessProg

    def ExtractUserBenefits():
        pass

    def MatchPlansFromProfile(self, profile: UserProfile, takeTopN: int) -> list[HIPlan]:
        pass

        
        # -- Check for invalid input

        # -- Codify profile
        ageVal = ""
        if profile.age <= 14:
            ageVal = "0-14"
        elif profile.age >= 64:
            ageVal = "64 and over"
        else:
            ageVal = str(profile.age)
        
        tobaccoVal = ["Tobacco User/Non-Tobacco User", "No Preference"]
        """
        if profile.tobacco == True:
            tobaccoVal.append("Tobacco User")
        else:
            tobaccoVal.append("Non-Tobacco User")
        """

        groupVal = "Individual"
        if profile.dependents > 0:
            groupVal = "Small Group"
        else:
            groupVal = "Individual"

        variantVal = "Exchange variant (no CSR)" # or "Non-Exchange variant"

        # -- Extract desired benefits
        labels = extractEntities(profile.preferences, dec.BENEFIT_LABELS, 0.7)
        beneVal = []
        for label in labels:
            beneVal.extend(dec.BENEFIT_LABELS[label])

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

        # Service Area ID is what we'll use to check if a plan is offered in the overview file
        # service area info
        serviceAreaInfo = defaultDB.pullData(
            defaultDB.Files_ServiceArea, 
            ['HIOS Issuer ID', 'Service Area ID', 'State', 'County Name', 'Market'], 
            [[], [], ['Yes'], [profile.location], []],
            False)
        temp_frame = pd.DataFrame(serviceAreaInfo)
        temp_frame = temp_frame[temp_frame['Market'].astype(str).str.upper() == groupVal.upper()]
        if 'Service Area ID' not in temp_frame.columns:
            print("no service areas found")
            return []
        IssuerServiceInfo = temp_frame[['HIOS Issuer ID', 'Service Area ID']] # pull out issuer service info
        serviceAreaIDs = temp_frame['Service Area ID'].unique()
        # print(IssuerServiceInfo)
        
        # rating area info
        ratingAreaInfo = defaultDB.pullData(
            defaultDB.Files_RatingArea, 
            ['Rating Area ID', 'Market', 'County'], 
            [[], [groupVal], [profile.location.upper()]],
            True)
        temp_frame = pd.DataFrame(ratingAreaInfo)
        if 'Rating Area ID' not in temp_frame.columns:
            print("no rating areas found")
            return []
        ratingAreaInts = temp_frame['Rating Area ID'].unique()
        ratingAreaNames = ['Rating Area '.join([' ', str(ID)]).strip() for ID in ratingAreaInts]
        # print(ratingAreaNames)
        
        # plan overview info
        possiblePlanInfo = defaultDB.pullData(
            defaultDB.Files_Overview, 
            ['HIOS Plan ID', 'Plan Marketing Name', 'Market Coverage', 'Network ID', 'Service Area ID', 'Plan Type', 'Level of Coverage', 'Wellness Program Offered', 'Disease Management Programs Offered', 'National Network', 'Enrollment Payment URL', 'Does this plan offer Composite Rating'], 
            [[], [], [groupVal], [], serviceAreaIDs, [], [], [], [], [], [], []],
            True)
        temp_frame = pd.DataFrame(possiblePlanInfo)
        if 'HIOS Plan ID' not in temp_frame.columns:
            print("no possible plans found")
            return []
        possiblePlanIDs = temp_frame['HIOS Plan ID'].unique()
        possiblePlanFrame = temp_frame
        # print("num possible IDs:", len(possiblePlanIDs))

        # base rate information
        baseRateInfo = []
        for file in defaultDB.Files_BaseRate:
            planBaseRateInfo = defaultDB.pullData(
                file, 
                ['Plan ID', 'Age', 'Tobacco', 'Rating Area ID', 'Individual Rate', 'Individual Tobacco Rate', 'HIOS Issuer ID', 'Market Coverage'], 
                [possiblePlanIDs, [ageVal], tobaccoVal, ratingAreaNames, [], [], [], [groupVal]],
                True)
            
            baseRateInfo.extend(planBaseRateInfo)
        # reevaluate possible plan IDs
        temp_frame = pd.DataFrame(baseRateInfo)
        if len(temp_frame) == 0:
            return []
        temp_frame.rename(columns={'Plan ID': 'HIOS Plan ID'}, inplace=True) # rename column to match for merging later
        temp_frame = temp_frame[temp_frame['HIOS Issuer ID'].astype(str).str.upper().isin(IssuerServiceInfo['HIOS Issuer ID'].astype(str))]
        possiblePlanIDs = temp_frame['HIOS Plan ID'].unique()
        baseRateFrame = temp_frame

        # benefits information
        BenefitInfo = defaultDB.pullData(
            defaultDB.Files_Benefits, 
            ['HIOS Plan ID', 'Benefit', 'EHB', 'Is This Benefit Covered', 'Quantitative Limit On Service', 'Limit Quantity', 'Limit Unit', 'Exclusions', 'Explanation', 'EHB Variance Reason', 'Excluded from In Network MOOP', 'Excluded from Out Of Network MOOP'], 
            [possiblePlanIDs, beneVal, [], ['Covered'], [], [], [], [], [], [], [], []],
            True)
        temp_frame = pd.DataFrame(BenefitInfo)
        benefitFrame = pd.DataFrame(columns=['HIOS Plan ID', 'Benefits'])
        for planID in temp_frame['HIOS Plan ID'].unique():
            temp_frame2 = temp_frame[(temp_frame['HIOS Plan ID'] == planID)]
            temp_frame2 = temp_frame2['Benefit'].to_list()
            benefitFrame.loc[len(benefitFrame)] = [planID, {'Benefit Array': temp_frame2}]
        print(benefitFrame)
        # print("benefit entries found:", len(temp_frame))

        # Plan MOOP information
        MoopInfo = defaultDB.pullData(
            defaultDB.Files_DDCTBL_MOOP, 
            ['Insurance Plan Identifier', 'Insurance Plan Variant Component Type Name', 'Medical And Drug Deductibles Integrated', 'Maximum Out of Pocket \\ Deductible Type', 'Network Category Type Code', 'Insurance Plan Individual Deductible Amount \\ Insurance Plan Annual Out Of Pocket Limit Amount', 'Insurance Plan Family Deductible Amount \\ Insurance Plan Annual Out Of Pocket Limit Amount Per Person', 'Insurance Plan Family Deductible Amount \\ Insurance Plan Annual Out Of Pocket Limit Amount Per Group', 'Insurance Plan Default Co-Insurance Amount', 'Level of Coverage Type Code'],
            # we could probably check if the user qualifies for csr, but it's not a big deal here
            [possiblePlanIDs, [], [], [], [], [], [], [], [], []],
            True)
        temp_frame = pd.DataFrame(MoopInfo)
        moopFrame = pd.DataFrame(columns=['HIOS Plan ID', 'MoopSubframe'])
        for planID in temp_frame['Insurance Plan Identifier'].unique():
            temp_frame2 = temp_frame[(temp_frame['Insurance Plan Identifier'] == planID)].to_dict()
            moopFrame.loc[len(moopFrame)] = [planID, {'Moop Subframe': temp_frame2}]
        print(moopFrame)
        # example how to access dataframe for results
        print(pd.DataFrame(moopFrame[(moopFrame['HIOS Plan ID'] == '29418TX0170023')].iloc[0, 1].get('Moop Subframe')))

        # Plan variant information
        VariantInfo = defaultDB.pullData(
            defaultDB.Files_PlanVariant, 
            ['HIOS Plan ID', 'Level of Coverage', 'CSR Variation Type', 'Issuer Actuarial Value', 'AV Calculator Output Number', ' Plan Brochure', 'URL for Summary of Benefits and Coverage', 'HSA Eligible', 'Plan Variant Marketing Name'], 
            # we could probably check if the user qualifies for csr, but it's not a big deal here
            [possiblePlanIDs, [], [variantVal], [], [], [], [], [], [], [], [], []],
            True)
        variantFrame = pd.DataFrame(VariantInfo)

        # -- Retrieve data for each unique plan in the list
        fullPlanFrame = pd.merge(possiblePlanFrame, baseRateFrame, on='HIOS Plan ID', how='left')
        fullPlanFrame = pd.merge(fullPlanFrame, variantFrame, on='HIOS Plan ID', how='left')
        fullPlanFrame = pd.merge(fullPlanFrame, moopFrame, on='HIOS Plan ID', how='left')
        fullPlanFrame = pd.merge(fullPlanFrame, benefitFrame, on='HIOS Plan ID', how='left')

        print("scoring...")
        scores = pd.DataFrame(columns=['HIOS Plan ID', 'Score'])
        for planID in fullPlanFrame['HIOS Plan ID'].to_list():
            # - score plans and rank
            scores.loc[len(scores)] = [planID, self.ScorePlan(profile, beneVal, fullPlanFrame[fullPlanFrame['HIOS Plan ID'] == planID])]
        print("done scoring")

        # take top N plan IDs
        fullPlanFrame = pd.merge(fullPlanFrame, scores, on='HIOS Plan ID', how='left')
        topPlans = fullPlanFrame.sort_values(by='Score', ascending=False).head(takeTopN)

        print("top plans:")
        print(topPlans)
        print(pd.DataFrame(topPlans.iloc[0]['MoopSubframe'].get('Moop Subframe')))
        print(pd.DataFrame(topPlans.loc[0]['MoopSubframe'].get('Moop Subframe'))) # example of how to access moop frame in this version

        # -- Return results
        return topPlans

def testFunc():
    searcher = HISearcher()
    profile = UserProfile()
    profile.location = "Dallas"
    profile.age = 47
    profile.preferences = "Diabetes"
    searcher.MatchPlansFromProfile(profile, 10)
    pass

if __name__ == "__main__":

    # mytext = "I have diabetes and need tier 3 drugs."

    # print(extractEntities(mytext, dec.BENEFIT_LABELS, 70))
    
    executionTime = timeit.timeit(testFunc, number=1)
    print(f"Execution time: {executionTime:.4f} seconds")
    
    # print(db.GetServicerInfoForCountyp("EL PASO"))

