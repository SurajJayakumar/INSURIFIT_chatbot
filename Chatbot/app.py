from flask_cors import CORS

import HISearcher, HISummarizer
from HISearcher import testFunc
from Interfaces import *
from flask import Flask, request, jsonify


# --- Flask App ---
app = Flask(__name__)
CORS(app)

summarizer_instance = None
searcher_instance = None
try:
    # Instantiate Searcher first
    
    searcher_instance = HISearcher.HISearcher()
    print("HISearcher initialized successfully.")
    

    # Instantiate Summarizer
    summarizer_instance = HISummarizer.HISummarizer()
    # Check if summarizer loaded its model (if applicable in your actual class)
    # if hasattr(summarizer_instance, 'model') and summarizer_instance.model:
    print("HISummarizer initialized successfully.")
    # else:
    #    print("Warning: HISummarizer initialized, but model might not be loaded.")

except Exception as e:
    print(f"Failed to initialize HISummarizer or HISearcher: {e}")
    if not summarizer_instance: print("Summarization will be disabled.")
    if not searcher_instance: print("Plan searching may fail.")

@app.route('/recommend', methods=['POST'])
def recommend_plan():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    data=request.json
    print(f"Received data: {data}")
    required_keys=['age','desired_benefits','dependents','county','is_tobacco_user']
    if not all(key in data for key in required_keys):
        missing_keys = [key for key in required_keys if key not in data]
        return jsonify({"error": f"Missing required keys: {', '.join(missing_keys)}"}), 400
    age = int(data['age'])
    desired_benefits = str(data['desired_benefits'])
    dependents = int(data['dependents'])
    county = str(data['county'])
    is_tobacco_user = bool(data['is_tobacco_user'])

    desired_premium = data.get('desired_premium') # Key from JS
    desired_deductible = data.get('desiredDeductible') # Key from JS
    desired_oop= data.get('desiredOOP') # Key from JS
    desired_copay= data.get('desired_Copay') # Key from JS (maps to temp_coinsurance)
    # --- Call testFunc to get top 5 plan IDs/Scores ---
    # Format numeric preferences (Premium, Copay) -> (bool, float)
    def format_preference_float(value):
        if value is not None and value != '':
            try: return (True, float(value))
            except (ValueError, TypeError): print(f"Warning: Could not convert '{value}' to float."); return (False, 0.0)
        else: return (False, 0.0)

    # Format string preferences (Deductible, OOP) -> (bool, str)
    def format_preference_string(value):
        if value is not None and value != '':
            return (True, str(value).strip()) # Preference is set, store the string
        else:
            return (False, "") # Preference not set or empty

    desired_premium_tuple = format_preference_float(desired_premium)
    desired_deductible_tuple = format_preference_string(desired_deductible) # Use string formatter
    desired_copay_tuple = format_preference_float(desired_copay)
    desired_oop_tuple = format_preference_string(desired_oop) # Use string formatt
    user_profile = UserProfile(
            age=age,
            location=county,
            dependents=dependents,
            preferences=desired_benefits, # Use the text description here
            tobacco_use=is_tobacco_user,
            # Pass the formatted tuples to the correct UserProfile attributes
            desiredPremium=desired_premium_tuple,
            desiredDeductible=desired_deductible_tuple,
            desiredCopay=desired_copay_tuple,
            desiredOOP=desired_oop_tuple,
            medications=[] 
        )
    # Log the created profile attributes for verification
    print(f"Created UserProfile:")
    print(f"  Age: {user_profile.age}, Location: {user_profile.location}, Dependents: {user_profile.dependents}, Tobacco: {user_profile.tobacco_use}")
    print(f"  Preferences Text: '{user_profile.preferences}'")
    print(f"  Desired Premium: {user_profile.desiredPremium}")
    print(f"  Desired Deductible: {user_profile.desiredDeductible}")
    print(f"  Desired Copay: {user_profile.desiredCopay}")
    print(f"  Desired OOP: {user_profile.desiredOOP}")
    try:
        print(f"Calling testFunc with: age={age}, benefits='{desired_benefits}', deps={dependents}, county='{county}', tobacco={is_tobacco_user}")
        # Assuming testFunc returns a DataFrame with 'HIOS Plan ID' and 'Score' columns
        top_plans_df = testFunc(age, desired_benefits, dependents, county, is_tobacco_user)

        if not isinstance(top_plans_df, pd.DataFrame) or top_plans_df.empty:
            print("testFunc did not return any suitable plans.")
            return jsonify({
                "message": "No suitable plans found matching your criteria.",
                "summaries": [] # Return empty list
                }), 200 # Return 200 OK status

        print(f"testFunc returned {len(top_plans_df)} plans. Processing top 1.")
        # Ensure we only process up to 1 plans if more are returned
        top_plans_df = top_plans_df.head(1)

        # --- Retrieve Details and Generate Summaries ---
        plan_summaries = []
        # Check if instances were created successfully
        if searcher_instance and summarizer_instance:
            print("Retrieving details and generating comparison summaries...")
            for index, plan_row in top_plans_df.iterrows():
                # Use .get() for safety in case columns are missing
                plan_id = plan_row.get('HIOS Plan ID')
                plan_score = plan_row.get('Score', 0.0) # Get score from initial ranking
                rank = index + 1

                if not plan_id:
                    print(f"Warning: Missing 'HIOS Plan ID' in row {index}. Skipping.")
                    plan_summaries.append(f"Error: Could not process plan at rank {rank} due to missing ID.")
                    continue

                try:
                    print(f"  Retrieving details for Plan ID: {plan_id} (Rank: {rank}, Score: {plan_score:.4f})")
                    # *** Call function to get FULL details for this specific plan ***
                    # Pass user_profile for context (e.g., age/tobacco for rates)
                    plan_details_info = searcher_instance.RetrievePlanInfo(plan_id, user_profile)

                    if plan_details_info is None:
                        print(f"  Could not retrieve full details for Plan ID: {plan_id}. Skipping summary.")
                        plan_summaries.append(f"Could not retrieve full details for Plan ID: {plan_id}.")
                        continue

                    # Create the HIPlan object using the retrieved detailed info
                    plan_obj = HIPlan(
                        id=plan_id,
                        rank=rank,
                        score=float(plan_score) if pd.notna(plan_score) else 0.0, # Convert score
                        info=plan_details_info # Use the fully populated info object
                    )

                    # Generate the comparison summary string using the detailed plan object
                    print(f"  Generating summary for Plan ID: {plan_id}...")
                    summary = summarizer_instance.compare_plan_and_preferences(
                        user=user_profile,
                        plan=plan_obj
                    )
                    plan_summaries.append(summary) # Add the generated string
                    print(f"    Summary generated successfully.")

                except Exception as e:
                    print(f"Error processing or summarizing plan ID {plan_id}: {e}")
                    plan_summaries.append(f"Error generating summary for plan ID: {plan_id}.")

        elif not searcher_instance:
             print("Error: HISearcher instance not available. Cannot retrieve plan details.")
             # Return an error or empty summaries
             return jsonify({"error": "Internal configuration error (Searcher).", "summaries": []}), 500
        else: # Summarizer not available
            print("Summarizer not available. Returning basic plan info.")
            # Fallback: return basic info if summarizer failed
            for index, plan_row in top_plans_df.iterrows():
                 plan_summaries.append(f"Plan Rank {index+1}: ID {plan_row.get('HIOS Plan ID', 'N/A')}, Score: {plan_row.get('Score', 0.0):.2f} (Summary generation unavailable)")


        print(f"Returning {len(plan_summaries)} summaries.")
        return jsonify({"summaries": plan_summaries}), 200 # Return 200 OK

    except Exception as e:
        print(f"An unexpected error occurred in /recommend endpoint: {e}")
        return jsonify({"error": "An internal server error occurred processing the request."}), 500


if __name__ == "__main__":

    app.run(host='0.0.0.0', port=5000, debug=True)
