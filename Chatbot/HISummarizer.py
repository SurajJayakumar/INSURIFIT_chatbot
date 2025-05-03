from Interfaces import *
from google import genai


class HISummarizer():
    def __init__(self):
        """
        Initialize HIFormatter with NLP text generation.
        """
        self.client = genai.Client(api_key="AIzaSyD9AbZEe1YMquELbS7v9pZs3LBsk4imvDQ")

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
        copay = info.copay
        oop_max = info.out_of_pocket_max
        covered_medications = info.covered_medications
        num_dependents = info.num_dependents
        couple_or_primary = info.couple_or_primary

        in_network_string = "in network"
        if in_network == False:
            in_network_string = "out of network"


        plan_details = (
            f"This is a {coverage_level} health insurance plan called {name} (ID: {plan.id}, Match Score: {plan.score:.2f}). "
            f"It is {in_network} and covers a {couple_or_primary} and {num_dependents} dependents. "
            f"The deductible is ${deductible:.2f}, "
            f"monthly premium is ${premium:.2f}"
            f"copay is ${copay:.2f} "
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

    
    def compare_plan_and_preferences(self, user: UserProfile, plan: HIPlan) -> str:
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
        if user.location:
            if info.in_network:
                pros.append(f"in-network for {user.location}, keeping costs low")
            else:
                cons.append(f"out-of-network in {user.location}, which may increase costs")

        # Dependents
        if user.dependents > 0:
            if info.num_dependents >= user.dependents:
                pros.append(f"covers {info.num_dependents} people, enough for your {user.dependents} dependents")
            else:
                cons.append(f"only covers {plan.num_covered} people, not enough for your {user.dependents} dependents")

        # Premium
        if user.desiredPremium[0]:
            if info.premium <= user.desiredPremium[1]:
                pros.append(f"premium of ${info.premium:.2f} fits your budget of ${user.desiredPremium[1]:.2f}")
            else:
                cons.append(f"premium of ${info.premium:.2f} exceeds your budget of ${user.desiredPremium[1]:.2f}")

        # Deductible
        if user.desiredDeductible[0]:
            if info.deductible <= user.desiredDeductible[1]:
                pros.append(f"deductible of ${info.deductible:.2f} within your limit of ${user.desiredDeductible[1]:.2f}")
            else:
                cons.append(f"deductible of ${info.deductible:.2f} exceeds your limit of ${user.desiredDeductible[1]:.2f}")

        # Copay
        if user.desiredCopay[0]:
            if info.copay <= user.desiredCopay[1]:
                pros.append(f"copay of ${info.copay:.2f} meets your target of ${user.desiredCopay[1]:.2f}")
            else:
                cons.append(f"copay of ${info.copay:.2f} higher than your target of ${user.desiredCopay[1]:.2f}")

        # Out-of-pocket max
        if user.desiredOOP[0]:
            if info.out_of_pocket_max <= user.desiredOOP[1]:
                pros.append(f"out-of-pocket max of ${info.out_of_pocket_max:.2f} within your limit of ${user.desiredOOP[1]:.2f}")
            else:
                cons.append(f"out-of-pocket max of ${info.out_of_pocket_max:.2f} exceeds your limit of ${user.desiredOOP[1]:.2f}")

        # Medications
        if user.medications:
            uncovered = [med for med in user.medications if med not in info.covered_medications]
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
    summarizer = HISummarizer()

    id = 1
    rank = 1
    score = 1

    user = UserProfile(
        age="44",
        location="TX001",
        dependents=2,
        desiredPremium=(True, 300.00),       
        desiredDeductible=(True, 1500.00),    
        desiredCopay=(True, 40.00),           
        desiredOOP=(True, 8000.00),           
        medications=["Metformin", "Atorvastatin"],
        preferences="Looking for in-network plans with solid coverage for a couple and kids",
        tobacco_use=False
    )

    info = HIPlanInfo(plan_marketing_name = "HealthyChoice Silver",
        in_network = True,
        coverage_level = "Silver",
        service_area_id = "TX001",
        premium = 350.50,
        deductible = 2000.00,
        copay = 30.00,
        out_of_pocket_max = 7500.00,
        covered_medications = ["Metformin", "Atorvastatin"],
        num_dependents = 3,
        couple_or_primary = "Couple"
    )

    plan = HIPlan(id=id, rank=rank, score=score, info=info)
    
    summarizer.compare_plan_and_preferences(plan=plan, user=user)

if __name__ == "__main__":
    main()