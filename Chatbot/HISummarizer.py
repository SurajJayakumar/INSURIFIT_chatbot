from Interfaces import *
from HISearcher import *
from google import genai
import pandas as pd


class HISummarizer():
    def __init__(self, user: UserProfile):
        """
        Initialize HIFormatter with NLP text generation.
        """
        self.client = genai.Client(api_key="AIzaSyD9AbZEe1YMquELbS7v9pZs3LBsk4imvDQ")
        self.user = user

    def create_plan_from_dataframe(self, df: pd.Series) -> HIPlan:
        plan_marketing_name = df.get('Plan Marketing Name')
        if pd.isna(plan_marketing_name):
            raise ValueError("Missing required field: 'Plan Marketing Name'")
        
        in_network = True
        coverage_level = df.get('Level of Coverage')
        if pd.isna(coverage_level):
            raise ValueError("Missing required field: 'Level of Coverage'")
        
        service_area_id = df.get('Service Area ID')
        if pd.isna(service_area_id):
            raise ValueError("Missing required field: 'Service Area ID'")
        
        premium_col = "Individual Tobacco Rate" if self.user.tobacco_use == True else "Individual Rate"
        premium = df.get(premium_col)
        if pd.isna(premium):
            raise ValueError("Missing required field: 'Individual Rate/Individual Tobacco Rate'")
        
        ddctbl_moop_frame = df.get('MoopSubframe')
        deductible_row = ddctbl_moop_frame.iloc[1]
        moop_row = ddctbl_moop_frame.iloc[4]

        ddctbl_moop_col = "Insurance Plan Individual Deductible Amount \ Insurance Plan Annual Out Of Pocket Limit Amount"
        deductible = deductible_row.get(ddctbl_moop_col)
        moop = moop_row.get(ddctbl_moop_col)
        if self.user.dependents != None and self.user.dependents > 0:
            deductible *= 2
            moop *= 2

        if pd.isna(deductible):
            raise ValueError("Missing required field: 'Deductible'")
        
        if pd.isna(moop):
            raise ValueError("Missing required field: 'Deductible'")
        
        benefits = df.get('Benefits')
        if not benefits or 'Benefit Array' not in benefits:
            raise ValueError("Missing or malformed 'Benefits' data")
        
        covered_medications = benefits['Benefit Array']

        score = df.get('Score')

        info = HIPlanInfo(plan_marketing_name = plan_marketing_name,
            in_network = in_network,
            coverage_level = coverage_level,
            service_area_id = service_area_id,
            premium = premium,
            deductible = deductible,
            # copay = 30.00,
            out_of_pocket_max = moop,
            covered_medications = covered_medications,
        )

        return info

    def summarize_plan(self, plan: HIPlan) -> str:
        """
        Summarize a health insurance plan in a conversational, NLP-driven way.
        
        Args:
            plan: HIPlan with plan details
            
        Returns:
            str: Conversational summary of the plan
        """
        
        info = plan.info

        name = info.plan_marketing_name
        in_network = info.in_network
        coverage_level = info.coverage_level
        area_id = info.service_area_id
        premium = info.premium
        deductible = info.deductible
        #copay = info.copay
        oop_max = info.out_of_pocket_max
        covered_medications = info.covered_medications

        in_network_string = "in network"
        if in_network == False:
            in_network_string = "out of network"


        plan_details = (
            f"This is a {coverage_level} health insurance plan called {name} (ID: {plan.id}, Match Score: {plan.score:.2f}). "
            f"It is {in_network_string} and covers one person and up to 3 dependents. "
            f"The deductible is ${deductible:.2f}, "
            f"monthly premium is ${premium:.2f}"
            #f"copay is ${copay:.2f} "
            f"and out-of-pocket maximum is ${oop_max:.2f}."
            f"It covers these medications: {covered_medications}"
        )
        prompt = (
            f"Summarize this health insurance plan in a friendly, conversational tone: {plan_details} "
            f"Keep the tone engaging and clear, as if explaining to someone new to insurance. Keep it in paragraph form."
            f"Try to avoid referring to the person you're conversing with, only summarize the plan. Delete all asterisks around variables."
        )

        # Generate summary
        generated = self.client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        print(generated.text)
        return generated.text

    
    def compare_plan_and_preferences(self, plan: HIPlan) -> str:
        """
        Compare a health insurance plan to user preferences and explain why it’s good or bad.
        
        Args:
            user: UserProfile with preferences (location, dependents, desiredPremium, desiredDeductible, 
                  desiredCopay, desiredOOP, medications, preferences)
            plan: HIPlan with details (coverage_level, in_network, num_covered, deductible, premium, 
                  copay, out_of_pocket_max, covered_medications)
        
        Returns:
            str: Conversational explanation of why the plan fits or doesn’t fit user preferences
        """
        pros = []
        cons = []

        info = plan.info

        # Location
        if self.user.location:
            if info.in_network:
                pros.append(f"in-network for {self.user.location}, keeping costs low")
            else:
                cons.append(f"out-of-network in {self.user.location}, which may increase costs")

        # Dependents
        if self.user.dependents > 0:
            if 3 >= self.user.dependents:
                pros.append(f"covers up to 3 dependents, enough for your {self.user.dependents} dependents")
            else:
                cons.append(f"only covers 3 dependents, not enough for your {self.user.dependents} dependents")

        # Premium
        if self.user.desiredPremium[0]:
            if info.premium <= self.user.desiredPremium[1]:
                pros.append(f"premium of ${info.premium:.2f} fits your budget of ${self.user.desiredPremium[1]:.2f}")
            else:
                cons.append(f"premium of ${info.premium:.2f} exceeds your budget of ${self.user.desiredPremium[1]:.2f}")

        # Deductible
        if self.user.desiredDeductible[0]:
            if info.deductible <= self.user.desiredDeductible[1]:
                pros.append(f"deductible of ${info.deductible:.2f} within your limit of ${self.user.desiredDeductible[1]:.2f}")
            else:
                cons.append(f"deductible of ${info.deductible:.2f} exceeds your limit of ${self.user.desiredDeductible[1]:.2f}")

        # # Copay
        # if self.user.desiredCopay[0]:
        #     if info.copay <= self.user.desiredCopay[1]:
        #         pros.append(f"copay of ${info.copay:.2f} meets your target of ${self.user.desiredCopay[1]:.2f}")
        #     else:
        #         cons.append(f"copay of ${info.copay:.2f} higher than your target of ${self.user.desiredCopay[1]:.2f}")

        # Out-of-pocket max
        if self.user.desiredOOP[0]:
            if info.out_of_pocket_max <= self.user.desiredOOP[1]:
                pros.append(f"out-of-pocket max of ${info.out_of_pocket_max:.2f} within your limit of ${self.user.desiredOOP[1]:.2f}")
            else:
                cons.append(f"out-of-pocket max of ${info.out_of_pocket_max:.2f} exceeds your limit of ${self.user.desiredOOP[1]:.2f}")

        # Medications
        if self.user.medications:
            uncovered = [med for med in self.user.medications if med not in info.covered_medications]
            if not uncovered:
                pros.append("covers all your medications")
            else:
                cons.append(f"does not cover: {', '.join(uncovered)}")


        pros_text = "; ".join(pros) if pros else "no specific matches"
        cons_text = "; ".join(cons) if cons else "no specific issues"

        # Prompt 
        # TODO: Dial in the prompting so it does exactly what we want it to do 
        prompt = (
            f"In a friendly, conversational tone, explain why this health insurance plan is a good or bad fit for the user. "
            f"Why it’s good: {pros_text}. "
            f"Why it’s not ideal: {cons_text}. "
            f"Keep it clear and engaging, like explaining to someone new to insurance."
            f"Make two paragraphs, one for what is good and one for what is a bad fit. Delete asterisks around variables."
        )

        # Generate summary
        generated = self.client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        print(generated.text)
        return generated.text
        
def main():
    searcher = HISearcher()

    user = UserProfile(
        age=44,
        location="Collin",
        dependents=2,
        desiredPremium=(True, 300.00),       
        desiredDeductible=(True, 1500.00),    
        # desiredCopay=(True, 40.00),           
        desiredOOP=(True, 8000.00),           
        medications=["Metformin", "Atorvastatin"],
        preferences="",
        tobacco_use=False
    )

    summarizer = HISummarizer(user=user)

    plans = searcher.MatchPlansFromProfile(user, 3)
    first_plan = plans.iloc[0]

    plan = summarizer.create_plan_from_dataframe(first_plan)

if __name__ == "__main__":
    main()