import re
from typing import List, Optional
from Interfaces import *

def normalize_for_asp(text: str)->str:
    if not isinstance(text,str): text=str(text)
    text=text.lower()
    text=re.sub(r'\s+','_', text)# replacing spaces with underscores
    text=re.sub(r'[^a-z0-9_-]','',text) #remove non alphabetic(caret symbol inside square bracket means exclude the characters inside brackets) 
    text=text.strip('_')
    return text if text else "unknown"

def get_numeric_from_string_for_asp(value_str:Optional[str])->Optional[float]:
    if value_str is None or not isinstance(value_str,str):return None
    cleaned_str=re.sub(r'[$,]', '', value_str)
    cleaned_str=re.sub(r'\s*(per person|per group).*$', '',cleaned_str,flags=re.IGNORECASE).strip()
    try: return float(cleaned_str)
    except (ValueError, TypeError): return None

def user_profile_to_asp_facts(user: UserProfile, user_asp_id:str = "currentUser")-> List[str]:
    facts=[f"user({user_asp_id})."]
    facts.append(f"age({user_asp_id}, {normalize_for_asp(user.age)}).")
    facts.append(f"dependents({user_asp_id},{user.dependents}).")
    if user.tobacco_use: facts.append(f"tobacco_user({user_asp_id}).")

    if user.desiredDeductible[0]:
        numeric_desired_deductible=get_numeric_from_string_for_asp(user.desiredDeductible[1])
        if numeric_desired_deductible is not None:
            facts.append(f"desires_deductible_max({user_asp_id},{int(numeric_desired_deductible)}).")
        else:
            facts.append(f"desires_deductible_max({user_asp_id},{normalize_for_asp(user.desired_deductible[1])}).")

    if user.desiredPremium[0]:
        facts.append(f"desires_premium_max({user_asp_id},{int(user.desiredPremium[1])}).")
    
    if user.preferences:
        beneval=user.preferences.split()
        for i in beneval:
            benefit = i.replace(" ", "_")
            benefit=benefit.lower()
            facts.append(f"user_wants_benefit({user_asp_id},{benefit}).")

    return facts

def plan_info_to_asp_facts(plan_info:HIPlanInfo,plan_id_original:str)->List[str]:
    plan_asp_id=normalize_for_asp(plan_id_original)
    plan_asp_id='p'+plan_asp_id
    facts=[f"plan({plan_asp_id})."]
    if plan_info.plan_marketing_name: facts.append(f"plan_marketing_name({plan_asp_id},{normalize_for_asp(plan_info.plan_marketing_name)}).")
    if plan_info.premium is not None: facts.append(f"plan_premium({plan_asp_id},{plan_info.premium:.0f}).")

    deductible_num=get_numeric_from_string_for_asp(plan_info.deductible)
    if deductible_num is not None:
        facts.append(f"plan_deductible({plan_asp_id},{int(deductible_num)}).")
    
    oop=get_numeric_from_string_for_asp(plan_info.out_of_pocket_max)
    if oop is not None:
        facts.append(f"plan_oop_max({plan_asp_id},{int(oop)}).")
    
    return facts




