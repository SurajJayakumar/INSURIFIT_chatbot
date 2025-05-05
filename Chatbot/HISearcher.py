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

    def RetrievePlanInfo(self, plan_id: str, profile: UserProfile) -> HIPlanInfo|None:
        """
        Fetches detailed information for a single plan ID from various CSV files
        using the HIDatabase instance (defaultDB).
        Returns a populated HIPlanInfo object or None if essential data is missing.
        """
        print(f"    Retrieving details for Plan ID: {plan_id}")
        if not plan_id or not defaultDB:
            print("      Error: Invalid plan_id or database instance.")
            return None

        # Use a dictionary to gather info before creating the object
        plan_data = {'plan_id': plan_id}

        try:
            # --- 1. Get Overview Data ---
            overview_cols = ['HIOS Plan ID', 'Plan Marketing Name', 'Market Coverage',
                             'Service Area ID', 'Plan Type', 'Level of Coverage']
            # Filter by the specific plan ID
            overview_info = defaultDB.pullData(defaultDB.Files_Overview, overview_cols,
                                              [[plan_id], [], [], [], [], []], True)
            if not overview_info:
                print(f"      Error: No overview data found for Plan ID {plan_id}")
                # Decide if this is critical; maybe return None or continue with defaults
                return None
            # Assuming plan_id is unique in overview, take the first result
            plan_data.update(overview_info[0])
            print(f"      Fetched overview: Name='{plan_data.get('Plan Marketing Name')}', Level='{plan_data.get('Level of Coverage')}'")

            # --- 2. Get Base Rate (Premium) ---
            # Requires age, tobacco status, and rating area for accuracy
            ageVal = ""
            if profile.age <= 14: ageVal = "0-14"
            elif profile.age >= 64: ageVal = "64 and over"
            else: ageVal = str(profile.age)

            if profile.tobacco_use is True: tobaccoVal = ["Tobacco User/Non-Tobacco User"]
            elif profile.tobacco_use is False: tobaccoVal = ["No Preference"]
            

            groupVal = "Individual" if profile.dependents == 0 else "Small Group"
            rating_area_cols = ['Rating Area ID', 'Market', 'County']
            ratingAreaInfo = defaultDB.pullData(defaultDB.Files_RatingArea, rating_area_cols,
                                               [[], [groupVal], [profile.location.upper()]], True)
            ratingAreaNames = []
            if ratingAreaInfo:
                rating_df = pd.DataFrame(ratingAreaInfo)
                ratingAreaInts = pd.to_numeric(rating_df['Rating Area ID'], errors='coerce').dropna().unique()
                ratingAreaNames = [f"Rating Area {int(id)}" for id in ratingAreaInts]

            rate_cols = ['Plan ID', 'Age', 'Tobacco', 'Rating Area ID', 'Individual Rate', 'Individual Tobacco Rate']
            rate_info_list = []
            for rate_file in defaultDB.Files_BaseRate:
                # Fetch all rates for this plan ID first, then filter
                chunk_rate_info = defaultDB.pullData(rate_file, rate_cols, [[plan_id], [], [], [], [], []], True)
                rate_info_list.extend(chunk_rate_info)
                
            effective_rate = None
            if rate_info_list:
                
                rate_df = pd.DataFrame(rate_info_list)
                rate_df = rate_df[rate_df['Age'] == ageVal]
                if ratingAreaNames:
                    rate_df = rate_df[rate_df['Rating Area ID'].isin(ratingAreaNames)]
                    
                if not rate_df.empty:
                    
                    rate_df['Effective Rate'] = pd.to_numeric(rate_df['Individual Rate'], errors='coerce')
                    if profile.tobacco_use is True:
                        tobacco_rate = pd.to_numeric(rate_df['Individual Tobacco Rate'], errors='coerce')
                        rate_df['Effective Rate'] = rate_df['Effective Rate'].mask(tobacco_rate.notna(), tobacco_rate)
                    valid_rates = rate_df['Effective Rate'].dropna()
                    if not valid_rates.empty: effective_rate = valid_rates.min() # Get lowest applicable rate

            plan_data['premium'] = effective_rate
            print(f"      Fetched premium: {effective_rate}")

            #DEDUCTIBLE AND OUT OF POCKET(NOT WORKING AS OF NOW TODO)
            
            ddctbl_cols = [
                'Insurance Plan Identifier', 'Network Category Type Code', 'Insurance Plan Annual Out Of Pocket Limit Amount Per Person','Insurance Plan Annual Out Of Pocket Limit Amount Per Group'
            ]
            ddctbl_info = defaultDB.pullData(defaultDB.Files_DDCTBL_MOOP, ddctbl_cols, [[plan_id], ['In Network'], [],[]], True)
            deductible_str = None
            oop_max_str = None
            if ddctbl_info:
                first_match = ddctbl_info[0] # Assuming first match is relevant

                # Get the string value for the 'Per Person' limit
                raw_deductible = first_match.get('Insurance Plan Annual Out Of Pocket Limit Amount Per Person')
                if raw_deductible is not None:
                    deductible_str = str(raw_deductible).strip()
                    # Remove " per person" suffix (case-insensitive)
                    suffix_index_person = deductible_str.lower().find(' per person')
                    if suffix_index_person != -1:
                        deductible_str = deductible_str[:suffix_index_person].strip()
                else:
                    deductible_str = "Not Available"

                # Get the string value for the 'Per Group' limit
                raw_oop_max = first_match.get('Insurance Plan Annual Out Of Pocket Limit Amount Per Group')
                if raw_oop_max is not None:
                    oop_max_str = str(raw_oop_max).strip()
                    # Remove " per group" suffix (case-insensitive)
                    suffix_index_group = oop_max_str.lower().find(' per group')
                    if suffix_index_group != -1:
                        oop_max_str = oop_max_str[:suffix_index_group].strip()
                else:
                    oop_max_str = "Not Available"
            else:
                deductible_str = "Not Available"
                oop_max_str = "Not Available"
                print(f"      Warning: No 'In Network' Deductible/MOOP info found for {plan_id}")

            # Store the cleaned string values
            plan_data['deductible'] = deductible_str
            plan_data['out_of_pocket_max'] = oop_max_str
            print(f"      Fetched and cleaned deductible string: '{plan_data['deductible']}', OOP Max string: '{plan_data['out_of_pocket_max']}'")
            # if ddctbl_info:
            #     print(f"XXXXXXXXXXX{ddctbl_info}")
            #     # Simplistic: take the first row found. May need logic for CSR variations.
            #     plan_data['deductible'] = pd.to_numeric(ddctbl_info[0].get('Insurance Plan Annual Out Of Pocket Limit Amount Per Person'), errors='coerce')
            #     plan_data['out_of_pocket_max'] = pd.to_numeric(ddctbl_info[0].get('Insurance Plan Annual Out Of Pocket Limit Amount Per Group'), errors='coerce')
            # else:
            #     plan_data['deductible'] = None
            #     plan_data['out_of_pocket_max'] = None
            # print(f"      Fetched deductible: {plan_data['deductible']}, OOP Max: {plan_data['out_of_pocket_max']}")


            # --- 4. Get coinsurance (Example: Primary Care Visit) ---
            # Assumes columns like 'Benefit Name', 'Copay In Network Tier 1' exist
            cost_share_cols = ['HIOS Plan ID','Co payment','Co Insurance'] # ADJUST COLUMN NAMES!
            # Filter by plan ID and the specific benefit you want the copay for
            cost_share_info = defaultDB.pullData(defaultDB.Files_BenefitCost, cost_share_cols,
                                                [[plan_id], ['Not Applicable'], []], True)
            
            copay_string = None # Default to None
            if cost_share_info:
                # Get the raw string value from the specified column
                # Use .get() for safety in case the column is missing in some rows
                raw_value = cost_share_info[0].get('Co Insurance') # Or 'Copay In Network Tier 1'

                # Store the value as a string, handling potential None or non-string types
                if raw_value is not None:
                    copay_string = str(raw_value).strip() # Convert to string and strip whitespace
                else:
                    copay_string = "Not Available" # Or keep as None, or use empty string ""

            # Store the raw string value under the 'copay' key
            plan_data['copay'] = copay_string
            print(f"      Fetched primary care cost share string (stored as copay): '{plan_data['copay']}'")
            


            # --- 5. Get Covered Medications (Example - Needs Refinement) ---
            # This is complex. You'd likely need to query Files_Benefits for relevant
            # pharmacy/drug benefits and potentially cross-reference with a formulary file (not listed).
            # Placeholder:
            plan_data['covered_medications'] = ["Metformin", "Lisinopril"] # Replace with actual logic
            print(f"      Fetched covered meds (placeholder): {plan_data['covered_medications']}")


            # --- 6. Determine In-Network Status (Example - Needs Refinement) ---
            # Compare plan's Service Area ID (from overview_data) with user's county/location.
            # Requires more robust logic based on your service area definitions.
            # Placeholder:
            plan_data['in_network'] = True # Assume true for now
            print(f"      Determined in_network (placeholder): {plan_data['in_network']}")


            # --- 7. Determine Num Dependents Covered / Couple Status ---
            # This might come from plan variant data or overview. Using estimates.
            plan_data['num_dependents'] = profile.dependents # Estimate based on user profile
            plan_data['couple_or_primary'] = "Couple" if profile.dependents > 0 else "Primary Only" # Estimate
            print(f"      Determined dependents/couple (estimate): Deps={plan_data['num_dependents']}, Type='{plan_data['couple_or_primary']}'")


            # --- Create HIPlanInfo Object ---
            # Use .get() with defaults for all fields for safety
            info_obj = HIPlanInfo(
                plan_marketing_name=plan_data.get('Plan Marketing Name', 'N/A'),
                in_network=plan_data.get('in_network', False),
                coverage_level=plan_data.get('Level of Coverage', 'Unknown'),
                service_area_id=plan_data.get('Service Area ID', 'N/A'),
                premium=plan_data.get('premium'), # Already fetched/converted
                deductible=plan_data.get('deductible'), # Already fetched/converted
                copay=plan_data.get('copay'), # Already fetched/converted
                out_of_pocket_max=plan_data.get('out_of_pocket_max'), # Already fetched/converted
                covered_medications=plan_data.get('covered_medications', []),
                num_dependents=plan_data.get('num_dependents', 0),
                couple_or_primary=plan_data.get('couple_or_primary', 'Unknown')
                # Add any other fields required by HIPlanInfo constructor
            )
            print(f"    Successfully created HIPlanInfo object for {plan_id}")
            return info_obj

        except Exception as e:
            print(f"      Error during detail retrieval for Plan ID {plan_id}: {e}")
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
        useTobaccoRate = profile.tobacco_use
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

def testFunc(age:int,desired_benefits:str,dependent_no:int,county:str,is_tobacco_user:bool)->list[HIPlan]:
    searcher = HISearcher()
    profile = UserProfile()
    profile.location = county
    profile.tobacco_use=is_tobacco_user
    profile.dependents=dependent_no
    profile.age = age
    profile.preferences = desired_benefits
    topPlans=searcher.MatchPlansFromProfile(profile, 1)
    return topPlans
    
# --- Main function for testing RetrievePlanInfo ---
def main_test_retrieval():
    """Tests the RetrievePlanInfo function."""
    print("\n--- Testing RetrievePlanInfo ---")

    # 1. Create a Searcher instance (using the global defaultDB)
    if defaultDB is None:
        print("Error: defaultDB is not initialized. Cannot run test.")
        return
    searcher = HISearcher()

    # 2. Create a sample UserProfile
    #    Use realistic values, especially for location (county)
    test_profile = UserProfile(
        age=44,
        location="brown",
        dependents=0,
        desiredPremium=(True, 300.00),       
        desiredDeductible=(True, 1500.00),    
        desiredCopay=(True, 40.00),           
        desiredOOP=(True, 8000.00),           
        medications=["Metformin", "Atorvastatin"],
        preferences="Looking for in-network plans with solid coverage for a couple and kids",
        tobacco_use=False
    )
    print(f"Test Profile: Age={test_profile.age}, County='{test_profile.location}', Deps={test_profile.dependents}, Tobacco={test_profile.tobacco_use}")

    # 3. Define a Plan ID to test
    #    *** IMPORTANT: Replace this with a valid HIOS Plan ID from your dataset ***
    #    Find one by looking at the output of testFunc or directly in your CSVs.
    plan_id_to_test = "37755TX0250001" # e.g., "12345TX0123456-01"

    if plan_id_to_test == "YOUR_REAL_HIOS_PLAN_ID_HERE":
        print("\n*** Please replace 'YOUR_REAL_HIOS_PLAN_ID_HERE' in the code with a valid Plan ID from your data! ***")
        return

    print(f"\nAttempting to retrieve details for Plan ID: {plan_id_to_test}")

    # 4. Call RetrievePlanInfo
    start_time = timeit.default_timer()
    detailed_info = searcher.RetrievePlanInfo(plan_id_to_test, test_profile)
    end_time = timeit.default_timer()
    print(f"RetrievePlanInfo execution time: {end_time - start_time:.4f} seconds")


    # 5. Print the results
    if detailed_info:
        print("\nSuccessfully retrieved details:")
        # Print attributes of the HIPlanInfo object
        # Use vars() to get a dictionary of attributes, or access them directly
        try:
            # Use vars() for a quick view, might be long
            # print(vars(detailed_info))

            # Or print specific attributes:
            print(f"  Marketing Name: {getattr(detailed_info, 'plan_marketing_name', 'N/A')}")
            print(f"  Coverage Level: {getattr(detailed_info, 'coverage_level', 'N/A')}")
            print(f"  Premium:        {getattr(detailed_info, 'premium', 'N/A')}")
            print(f"  Deductible:     {getattr(detailed_info, 'deductible', 'N/A')}")
            print(f"  OOP Max:        {getattr(detailed_info, 'out_of_pocket_max', 'N/A')}")
            print(f"  Copay String:   '{getattr(detailed_info, 'copay', 'N/A')}'") # Display the string
            print(f"  In Network:     {getattr(detailed_info, 'in_network', 'N/A')}")
            print(f"  Covered Meds:   {getattr(detailed_info, 'covered_medications', 'N/A')}") # Placeholder
            # Add other relevant fields...

        except AttributeError as ae:
             print(f"Error accessing attributes of retrieved info object: {ae}")
        except Exception as pe:
             print(f"Error printing retrieved info: {pe}")

    else:
        print(f"\nFailed to retrieve details for Plan ID: {plan_id_to_test}")

    print("--- End of RetrievePlanInfo Test ---")


# --- Main block ---
if __name__ == "__main__":
    # Call the specific test function you want to run
    main_test_retrieval()
    


