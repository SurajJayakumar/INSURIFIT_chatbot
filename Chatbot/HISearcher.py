from Interfaces import *
import Parameters.declarations as dec

import spacy
from rapidfuzz import process

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


# Helper class for health insurance plan database searching
# See corresponding interface in chatbot/interfaces.py for usage
# TODO: implement
class HISearcher(HIPlanSearchInterface):
    def MatchPlansFromProfile(profile: UserProfile, takeTopN: int) -> list[HIPlan]:
        pass
        # -- Check for invalid input

        # -- Codify profile

        # -- Access database

        # -- Measure distance from each element
        # Use N element list to capture [takeTopN] best results  

        # -- Return results

mytext = "I have diabetes and need tier 3 drugs."

print(extractEntities(mytext, dec.BENEFIT_LABELS, 70))

