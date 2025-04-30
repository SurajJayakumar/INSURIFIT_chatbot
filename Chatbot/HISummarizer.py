from Interfaces import *
from transformers import pipeline

# Helper class for health insurance plan database searching
# See corresponding interface in chatbot/interfaces.py for usage
# TODO: update with 
class HISummarizer():
    def __init__(self):
        """
        Initialize HIFormatter with NLP text generation capabilities.
        """
        self.generator = pipeline('text-generation', model='distilgpt2', max_new_tokens=200)


    def summarize_plan(self, plan: HIPlan) -> str:
        """
        Summarize a health insurance plan in a conversational, NLP-driven way.
        
        Args:
            plan: HIPlan with plan details
            
        Returns:
            str: Conversational summary of the plan
        """
        # Extract plan details
        coverage_level = plan.info.coverage_level
        in_network = "in-network" if plan.info.in_network else "out-of-network"
        deductible = plan.info.deductible_limit
        premium = plan.info.cost_benefits.get('premium', 'unknown')
        copay = plan.info.cost_benefits.get('copay', 'unknown')
        oop_max = plan.info.cost_benefits.get('out_of_pocket_max', 'unknown')
        num_covered = plan.info.num_covered

        # Construct prompt for NLP generation
        plan_details = (
            f"This is a {coverage_level} health insurance plan (ID: {plan.id}, Match Score: {plan.score:.2f}). "
            f"It is {in_network} and covers {num_covered} individuals. "
            f"The deductible is ${deductible:.2f}, "
            f"monthly premium is ${premium:.2f} if isinstance(premium, (int, float)) else premium, "
            f"copay is ${copay:.2f} if isinstance(copay, (int, float)) else copay, "
            f"and out-of-pocket maximum is ${oop_max:.2f} if isinstance(oop_max, (int, float)) else oop_max."
        )
        prompt = (
            f"Summarize this health insurance plan in a friendly, conversational tone: {plan_details} "
            f"Keep the tone engaging and clear, as if explaining to someone new to insurance. "
        )

        # Generate summary
        generated = self.generator(prompt, num_return_sequences=1)[0]['generated_text']
        
        # Clean up and format output
        summary = f"Health Insurance Plan Summary\n{'=' * 40}\n\n{generated.strip()}\n"
        return summary

    
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

        # Location
        if user.location:
            if plan.in_network:
                pros.append(f"in-network for {user.location}, keeping costs low")
            else:
                cons.append(f"out-of-network in {user.location}, which may increase costs")

        # Dependents
        if user.dependents > 0:
            if plan.num_covered >= user.dependents:
                pros.append(f"covers {plan.num_covered} people, enough for your {user.dependents} dependents")
            else:
                cons.append(f"only covers {plan.num_covered} people, not enough for your {user.dependents} dependents")

        # Premium
        if user.desiredPremium[0] and isinstance(plan.premium, (int, float)):
            if plan.premium <= user.desiredPremium[1]:
                pros.append(f"premium of ${plan.premium:.2f} fits your budget of ${user.desiredPremium[1]:.2f}")
            else:
                cons.append(f"premium of ${plan.premium:.2f} exceeds your budget of ${user.desiredPremium[1]:.2f}")

        # Deductible
        if user.desiredDeductible[0]:
            if plan.deductible <= user.desiredDeductible[1]:
                pros.append(f"deductible of ${plan.deductible:.2f} within your limit of ${user.desiredDeductible[1]:.2f}")
            else:
                cons.append(f"deductible of ${plan.deductible:.2f} exceeds your limit of ${user.desiredDeductible[1]:.2f}")

        # Copay
        if user.desiredCopay[0] and isinstance(plan.copay, (int, float)):
            if plan.copay <= user.desiredCopay[1]:
                pros.append(f"copay of ${plan.copay:.2f} meets your target of ${user.desiredCopay[1]:.2f}")
            else:
                cons.append(f"copay of ${plan.copay:.2f} higher than your target of ${user.desiredCopay[1]:.2f}")

        # Out-of-pocket max
        if user.desiredOOP[0] and isinstance(plan.out_of_pocket_max, (int, float)):
            if plan.out_of_pocket_max <= user.desiredOOP[1]:
                pros.append(f"out-of-pocket max of ${plan.out_of_pocket_max:.2f} within your limit of ${user.desiredOOP[1]:.2f}")
            else:
                cons.append(f"out-of-pocket max of ${plan.out_of_pocket_max:.2f} exceeds your limit of ${user.desiredOOP[1]:.2f}")

        # Medications
        if user.medications:
            uncovered = [med for med in user.medications if med not in plan.covered_medications]
            if not uncovered:
                pros.append("covers all your medications")
            else:
                cons.append(f"does not cover: {', '.join(uncovered)}")

        # Coverage level
        if user.preferences and user.preferences.lower().find(plan.coverage_level.lower()) != -1:
            pros.append(f"{plan.coverage_level} coverage matches your preferences")
        elif user.preferences:
            cons.append(f"{plan.coverage_level} coverage may not suit your preferences")

        # Comparison text for prompt
        pros_text = "; ".join(pros) if pros else "no specific matches"
        cons_text = "; ".join(cons) if cons else "no specific issues"

        # Prompt for NLP generation
        prompt = (
            f"In a friendly, conversational tone, explain why this health insurance plan is a good or bad fit for the user. "
            f"Why it’s good: {pros_text}. "
            f"Why it’s not ideal: {cons_text}. "
            f"Keep it clear and engaging, like explaining to someone new to insurance."
        )

        # Generate explanation
        generated = self.generator(prompt, num_return_sequences=1)[0]['generated_text']
        
        # Format output
        summary = f"Why This Plan Fits (or Doesn’t)\n{'=' * 30}\n{generated.strip()}\n"
        return summary
        

