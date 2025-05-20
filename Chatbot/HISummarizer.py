# HISummarizer.py
from typing import List, Optional
import google.generativeai as genai
import os
import traceback
import pandas as pd
import re
# Assuming Interfaces defines UserProfile, HIPlan
try:
    from Interfaces import UserProfile, HIPlan, HIPlanInfo
except ImportError:
    print("Warning: Could not import Interfaces in HISummarizer. Defining dummies.")
    class UserProfile: pass
    class HIPlan: pass
    class HIPlanInfo: pass

ASP_PREDICATE_EXPLANATIONS = {
    "advice consider low oop due to age and premium mismatch": "Given your age and that this plan's premium is higher than your preference, you might want to prioritize plans with lower out-of-pocket maximums to better manage potential healthcare costs if significant care is needed.",
    "advice consider medicare": "Based on your age, it would be beneficial to explore Medicare options, as they might offer coverage specifically designed for your needs.",
    "advice unrealistic financial goals": "It's often challenging to find a health plan with both very low monthly premiums and very low deductibles. You might want to consider which of these is a higher priority for your financial situation and healthcare needs.",
    "advice tradeoff higher premium for lower deductible": "For more comprehensive coverage, especially if you anticipate needing regular medical care, have dependents, or specific health conditions, a plan with a somewhat higher premium can often lead to a lower deductible and more predictable out-of-pocket costs when you access services.",
    "advice tradeoff higher deductible for lower premium": "If you're currently in good health and looking to minimize monthly expenses, a plan with a lower premium in exchange for a higher deductible could be considered. However, this means you'd pay more upfront if you do need significant medical care.",
    "advice tobacco impacts premium": "It's important to be aware that tobacco use generally results in higher health insurance premiums due to associated health risks.",
    "advice potential low income considerations": "If your income falls within certain federal guidelines, you might qualify for subsidies or specific programs (like those through the Affordable Care Act marketplace) that could significantly lower your healthcare costs. It's highly recommended to check your eligibility.",
    "plan meets desired premium": "This plan's premium aligns with your stated preference.", # More of a direct pro/con
    "plan exceeds desired premium": "This plan's premium is higher than your stated preference.", # More of a direct pro/con
    "plan meets desired deductible": "This plan's deductible aligns with your stated preference.", # More of a direct pro/con
    "plan exceeds desired deductible": "This plan's deductible is higher than your stated preference.", # More of a direct pro/con
    "plan meets desired oop max": "This plan's out-of-pocket maximum aligns with your stated preference.", # More of a direct pro/con
    "plan exceeds desired oop max": "This plan's out-of-pocket maximum is higher than your stated preference.", # More of a direct pro/con
    "asp validates plan": "Our detailed analysis suggests this plan generally aligns with several key aspects of your profile based on common insurance considerations.",
    
}
class HISummarizer():
    def __init__(self):
        """
        Initialize HISummarizer with Google Generative AI configuration and model.
        """
        try:
            
            api_key = "AIzaSyAJW3hAL4mmw_NePRqLWKfeqtGXr99RJ-M" # Replace with your actual key
            if not api_key:
                 raise ValueError("GEMINI_API_KEY not found or provided.")

            genai.configure(api_key=api_key)

            # --- Instantiate the Model ---
            # Using a recommended model like gemini-1.5-flash-latest
            self.model = genai.GenerativeModel('gemini-1.5-flash-latest')
            print("HISummarizer initialized with Gemini model.")

        except ValueError as ve:
             print(f"Error initializing HISummarizer (API Key issue?): {ve}")
             self.model = None # Ensure model is None if init fails
        except Exception as e:
            print(f"An unexpected error occurred during HISummarizer initialization: {e}")
            traceback.print_exc()
            self.model = None # Ensure model is None if init fails

    def _generate_with_fallback(self, prompt: str, fallback_text: str = "Summary generation failed.") -> str:
        """Internal helper to generate content with error handling."""
        if not self.model:
            print("Error: Gemini model not initialized in HISummarizer.")
            return fallback_text
        try:
            # Generate content using the model instance
            response = self.model.generate_content(prompt)
            # Basic check if response has text (structure might vary slightly)
            if hasattr(response, 'text') and response.text:
                 return response.text.strip()
            elif hasattr(response, 'parts') and response.parts:
                 # Handle potential multi-part responses if necessary
                 return "".join(part.text for part in response.parts).strip()
            else:
                 print(f"Warning: Unexpected response structure from Gemini: {response}")
                 return fallback_text + " (Unexpected response format)"
        except Exception as e:
            print(f"Error during Gemini content generation: {e}")
            traceback.print_exc()
            return fallback_text + f" (Error: {e})"


    def summarize_plan(self, plan: HIPlan,) -> str:
        """
        Summarize a health insurance plan using the configured Gemini model.
        """
        if not hasattr(plan, 'info') or not plan.info:
             return "Error: Plan information is missing."

        info = plan.info

        # Helper to format currency or return 'N/A'
        def format_currency(value):
            if value is None or pd.isna(value): return "N/A"
            try: return f"${float(value):,.2f}"
            except (ValueError, TypeError): return "N/A"

        # Helper to format list or return 'None specified'
        def format_list(items):
             if not items: return "None specified"
             return ", ".join(map(str, items))


        name = getattr(info, 'plan_marketing_name', 'Unknown Plan')
        in_network = getattr(info, 'in_network', False)
        coverage_level = getattr(info, 'coverage_level', 'Unknown')
        premium = format_currency(getattr(info, 'premium', None))
        deductible = format_currency(getattr(info, 'deductible', None))
        copay = str(getattr(info, 'copay', 'N/A')) # Keep copay as string based on previous request
        oop_max = format_currency(getattr(info, 'out_of_pocket_max', None))
        covered_medications = format_list(getattr(info, 'covered_medications', []))
        num_dependents = getattr(info, 'num_dependents', 0)
        couple_or_primary = getattr(info, 'couple_or_primary', 'Unknown')
        plan_id = getattr(plan, 'id', 'N/A')
        score = getattr(plan, 'score', 0.0)

        in_network_string = "in-network" if in_network else "out-of-network"

        # Construct details safely using getattr and formatting helpers
        plan_details = (
            f"This is a {coverage_level} health insurance plan called '{name}' (ID: {plan_id}, Match Score: {score:.2f}). "
            f"It is {in_network_string} and covers a {couple_or_primary} plus {num_dependents} dependents. "
            f"The deductible is {deductible}, "
            f"monthly premium is {premium}, "
            f"the typical copay/coinsurance string is '{copay}', "
            f"and the out-of-pocket maximum is {oop_max}. "
            f"Covered medications listed include: {covered_medications}."
        )
        prompt = (
            f"Summarize this health insurance plan in a friendly, conversational tone, based ONLY on these details: {plan_details} "
            f"Keep the tone engaging and clear, as if explaining to someone new to insurance. Output only a single paragraph summarizing the plan. "
            f"Do not refer to 'the user' or 'you'. Focus solely on describing the plan's key features mentioned above."
        )

        # Generate summary using the helper method
        summary = self._generate_with_fallback(prompt, f"Could not generate summary for plan {name}.")
        print(f"Generated summary for {name}: {summary[:100]}...") # Print start of summary
        return summary


    def compare_plan_and_preferences(self, user: UserProfile, plan: HIPlan, asp_inferred_predicates:Optional[List[str]]=None) -> str:
        """
        Compare a health insurance plan to user preferences using the Gemini model.
        """
        if not hasattr(plan, 'info') or not plan.info:
             return "Error: Plan information is missing for comparison."

        info = plan.info
        pros = []
        cons = []

        # Helper functions from summarize_plan
        def format_currency(value):
            if value is None or pd.isna(value): return None # Return None if N/A for comparison
            try: return float(value)
            except (ValueError, TypeError): return None
        def format_list(items):
             if not items: return []
             return [str(item).strip() for item in items] # Ensure list of strings
        def get_numeric_from_string(value_str):
            if value_str is None or not isinstance(value_str, str):
                return None
            # Remove $, commas, and any trailing text like ' per person'/' per group' (case-insensitive)
            cleaned_str = re.sub(r'[$,]', '', value_str)
            cleaned_str = re.sub(r'\s*(per person|per group).*$', '', cleaned_str, flags=re.IGNORECASE).strip()
            try:
                return float(cleaned_str)
            except (ValueError, TypeError):
                return None # Return None if conversion fails

        # --- Comparisons ---
        plan_premium = format_currency(getattr(info, 'premium', None))
        plan_meds = format_list(getattr(info, 'covered_medications', []))
        plan_in_network = getattr(info, 'in_network', False)
        plan_num_deps_covered = getattr(info, 'num_dependents', 0) # Assuming this reflects actual coverage
        plan_deductible_str = getattr(info, 'deductible', None) # Get the string (e.g., '$8000')
        plan_oop_max_str = getattr(info, 'out_of_pocket_max', None) # Get the string (e.g., '$16000')
        plan_deductible_num = get_numeric_from_string(plan_deductible_str)
        plan_oop_max_num = get_numeric_from_string(plan_oop_max_str)


        # Location/Network
        if user.location:
            if plan_in_network: pros.append(f"appears to be in-network for your location ({user.location}), which usually means lower costs for covered services")
            else: cons.append(f"may be out-of-network for your location ({user.location}), potentially leading to higher costs")

        # Dependents
        if user.dependents > 0:
            # Compare user's needed dependents vs plan's coverage capacity
            # (Using plan_num_deps_covered which might be an estimate - refine if plan data is better)
            if plan_num_deps_covered >= user.dependents:
                pros.append(f"seems to cover enough individuals ({plan_num_deps_covered}) for your family size ({user.dependents} dependents)")
            else:
                cons.append(f"might not cover enough individuals ({plan_num_deps_covered}) for your family size ({user.dependents} dependents)")

        # Premium (Check if user specified a desire)
        if hasattr(user, 'desiredPremium') and user.desiredPremium and user.desiredPremium[0] and plan_premium is not None:
            if plan_premium <= user.desiredPremium[1]:
                pros.append(f"monthly premium of ${plan_premium:.2f} fits within your desired maximum of ${user.desiredPremium[1]:.2f}")
            else:
                cons.append(f"monthly premium of ${plan_premium:.2f} is higher than your desired maximum of ${user.desiredPremium[1]:.2f}")
        elif plan_premium is not None:
            pros.append(f"has a monthly premium of ${plan_premium:.2f} (you didn't specify a budget for comparison)") # Neutral if no budget set

        # Deductible (Compare numeric, display string)
        # *** FIXED HERE ***
        if hasattr(user, 'desiredDeductible') and user.desiredDeductible[0] and plan_deductible_num is not None:
            user_desired_deductible_str = user.desiredDeductible[1] # Get user's desired string limit
            user_desired_deductible_num = get_numeric_from_string(user_desired_deductible_str) # Convert user's limit to numeric
            if user_desired_deductible_num is not None: # Check if user's limit could be converted
                if plan_deductible_num <= user_desired_deductible_num:
                    # Use plan_deductible_str and user_desired_deductible_str for display
                    pros.append(f"deductible of {plan_deductible_str} is within your desired limit of {user_desired_deductible_str}")
                else:
                    cons.append(f"deductible of {plan_deductible_str} is higher than your desired limit of {user_desired_deductible_str}")
            else: # User specified a desire, but it wasn't a recognizable number string
                 cons.append(f"could not numerically compare plan deductible ({plan_deductible_str}) with your desired limit ('{user_desired_deductible_str}')")
        elif plan_deductible_str is not None:
             pros.append(f"has a deductible of {plan_deductible_str}")

        # OOP Max (Compare numeric, display string)
        # *** FIXED HERE ***
        if hasattr(user, 'desiredOOP') and user.desiredOOP[0] and plan_oop_max_num is not None:
            user_desired_oop_str = user.desiredOOP[1] # Get user's desired string limit
            user_desired_oop_num = get_numeric_from_string(user_desired_oop_str) # Convert user's limit to numeric
            if user_desired_oop_num is not None: # Check if user's limit could be converted
                if plan_oop_max_num <= user_desired_oop_num:
                    # Use plan_oop_max_str and user_desired_oop_str for display
                    pros.append(f"out-of-pocket maximum of {plan_oop_max_str} is within your desired limit of {user_desired_oop_str}")
                else:
                    cons.append(f"out-of-pocket maximum of {plan_oop_max_str} is higher than your desired limit of {user_desired_oop_str}")
            else: # User specified a desire, but it wasn't a recognizable number string
                 cons.append(f"could not numerically compare plan out-of-pocket max ({plan_oop_max_str}) with your desired limit ('{user_desired_oop_str}')")
        elif plan_oop_max_str is not None:
             pros.append(f"has an out-of-pocket maximum of {plan_oop_max_str}")

        

        # Medications (Compare user.medications list with plan_meds list)
        if hasattr(user, 'medications') and user.medications:
            user_meds_list = format_list(user.medications)
            uncovered = [med for med in user_meds_list if med.lower() not in (pm.lower() for pm in plan_meds)] # Case-insensitive check
            if not uncovered:
                pros.append("appears to cover all the specific medications you mentioned")
            else:
                cons.append(f"might not cover the following medications you mentioned: {', '.join(uncovered)}")
        # --- End Comparisons ---


        pros_text = "; ".join(pros) if pros else "no specific positive matches found based on your preferences"
        cons_text = "; ".join(cons) if cons else "no specific negative points found based on your preferences"

        #----ASP Predicate Interpretation---
        asp_insights_list=[]
        if asp_inferred_predicates:
            for pred_str in asp_inferred_predicates:
                if pred_str.startswith("advice consider family benefit"):
                    benefit_name_match=re.search(r"advice consider family benefit (.*)",pred_str)
                    if benefit_name_match:
                        benefit_name =benefit_name_match.group(1).replace("_"," ")
                        asp_insights_list.append(f"For families, considering coverage for '{benefit_name}' is important , and this plan might be suitable if it includes it.")
                elif pred_str in ASP_PREDICATE_EXPLANATIONS:
                    asp_insights_list.append(ASP_PREDICATE_EXPLANATIONS[pred_str])
                
        asp_insights_text= "\n\nFurther Considerations based on your profile:\n" + "\n".join(f"- {insight}" for insight in asp_insights_list) if asp_insights_list else ""


        plan_name_display = getattr(info, 'plan_marketing_name', 'N/A')
        plan_id_display = getattr(plan, 'id', 'N/A')

        # Construct the prompt for the comparison
        prompt = (
            f"You are an expert health insurance advisor. Based on the user's preferences and the details of the health insurance plan named '{plan_name_display}' (ID: {plan_id_display}), provide a clear and friendly explanation of why this plan might be a good or bad fit. "
            f"Do not invent any information not provided.\n\n"
            f"User's key financial preferences and direct plan matches:\n"
            f"Positive points (Pros): {pros_text}\n"
            f"Negative points (Cons): {cons_text}\n"
            f"{asp_insights_text}\n\n"
            f"Task: Synthesize all the above information (Pros, Cons, and Further Considerations) into a balanced, conversational explanation. "
            f"Structure your response into a few clear paragraphs. Start with an overall assessment if possible. "
            f"If 'advice consider medicare' was noted, prominently suggest the user explore Medicare options. "
            f"If 'advice unrealistic financial goals' was noted, gently suggest that finding a plan with both very low premiums and very low deductibles is challenging and they might need to prioritize. "
            f"If 'advice tobacco impacts premium' was noted, mention that tobacco use generally leads to higher premiums. "
            f"If 'advice consider family benefit' points were made, weave them into the discussion about family needs. "
            f"The goal is to help someone new to insurance understand if this specific plan is a reasonable choice for them, given all the analyzed factors. "
            f"Be objective and informative. Do not use asterisks or markdown for emphasis in your final output."
        )

        # Generate comparison using the helper method
        comparison = self._generate_with_fallback(prompt, f"Could not generate comparison for plan {getattr(info, 'plan_marketing_name', 'N/A')}.")
        print(f"Generated comparison for {getattr(info, 'plan_marketing_name', 'N/A')}: {comparison[:100]}...") # Print start of comparison
        return comparison

# --- main function for testing HISummarizer ---
def main():
    print("\n--- Testing HISummarizer ---")
    summarizer = HISummarizer()

    # Check if summarizer initialized correctly
    if not summarizer.model:
         print("Summarizer model failed to initialize. Exiting test.")
         return

    # Create sample UserProfile (ensure attributes match those used in compare_plan_and_preferences)
    user = UserProfile(
        age=44, # Note: UserProfile in Interfaces might expect int
        location="Dallas",
        dependents=2,
        desiredPremium=(True, 500.00),
        desiredDeductible=(True, "500"),
        desiredCopay=(False, 0), # Not specified
        desiredOOP=(True, "8000.00"),
        medications=["Metformin", "Lisinopril", "Amlodipine"], # Added one not in plan
        preferences="Need family coverage, trying to keep premium under $500 and deductible under $3000.",
        tobacco_use=False
    )
    print("\nTest User Profile:")
    print(f"  Age: {user.age}, Location: {user.location}, Dependents: {user.dependents}")
    print(f"  Desired Premium Max: {user.desiredPremium[1] if user.desiredPremium[0] else 'N/A'}")
    print(f"  Desired Deductible Max: {user.desiredDeductible[1] if user.desiredDeductible[0] else 'N/A'}")
    print(f"  Desired OOP Max: {user.desiredOOP[1] if user.desiredOOP[0] else 'N/A'}")
    print(f"  Medications: {user.medications}")


    # Create sample HIPlanInfo (ensure attributes match those used)
    info = HIPlanInfo(
        plan_marketing_name="FamilyCare Gold TX",
        in_network=True,
        coverage_level="Gold",
        service_area_id="TX001", # Assuming Dallas is in TX001
        premium=480.75,
        deductible=2500.00,
        copay="20%", # String value as requested
        out_of_pocket_max=7800.00,
        covered_medications=["Metformin", "Lisinopril"], # Missing Amlodipine
        num_dependents=3, # Covers enough dependents
        couple_or_primary="Couple"
    )

    # Create sample HIPlan
    plan = HIPlan(id="98765TXGOLD01", rank=1, score=0.85, info=info)
    print("\nTest Plan Details:")
    print(f"  ID: {plan.id}, Name: {info.plan_marketing_name}")
    print(f"  Premium: {info.premium}, Deductible: {info.deductible}, OOP Max: {info.out_of_pocket_max}")
    print(f"  Copay/Coinsurance String: '{info.copay}'")
    print(f"  Covered Meds: {info.covered_medications}")


    # Test the comparison function
    print("\n--- Calling compare_plan_and_preferences ---")
    comparison_text = summarizer.compare_plan_and_preferences(user=user, plan=plan)

    print("\n--- Generated Comparison Text ---")
    print(comparison_text)
    print("--- End of HISummarizer Test ---")


if __name__ == "__main__":
    
    main()