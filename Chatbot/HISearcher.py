from Interfaces import *
from typing import List
import Parameters.declarations as dec
import spacy

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
    
    # Cached list of currently selected plan rows
    selectedPlans = list(int)

    # File references for retrieving data
    Files_BaseRate = str
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

        # -- Measure distance from each element
        # Use N element list to capture [takeTopN] best results  

        # -- Return results

mytext = "I have diabetes and need tier 3 drugs."

print(extractEntities(mytext, dec.BENEFIT_LABELS, 70))

