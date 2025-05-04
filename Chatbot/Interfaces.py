from abc import ABC, abstractmethod
from dataclasses import dataclass
import pandas as pd

# --- type definitions --- #

# database entry identifier
databaseId = int

# --- data classes --- #

# This class stores user input fields for use in health insurance database searcher
# a bool value is added via tuple to some elements as a way of showing if they are set or not.
# TODO: modify this class with necessary fields 
@dataclass
class UserProfile:
    age: str # age of user (may not be necessary)
    location: str # location of user (to consider in-network)
    dependents: int # number of dependents to consider on a plan. Returned plans should only have >= number of dependents
    desiredPremium: tuple[bool, float] # desired premium, may be omitted
    desiredDeductible: tuple[bool, float] # desired deductible, may be omitted
    desiredCopay: tuple[bool, float] # desired copay amount, may be omitted
    desiredOOP: tuple[bool, float] # desired out-of-pocket amount, may be omitted
    medications: list[str] # any medicines that need to be given preference in the search
    preferences: str # other preferences (may not be necessary)
    tobacco_use: bool 
    

# This class is used to store complete information about a plan in the database
# TODO: determine what information needs to be returned for RAG usage
@dataclass
class HIPlanInfo:
    plan_marketing_name: str # User-friendly name of the plan; RBIS.INSURANCE_PLAN: Plan Marketing Name
    in_network: bool # if the plan uses in-network providers; RBIS.INSURANCE_PLAN: Network ID
    coverage_level: str # metal tier; shows cost-sharing level; RBIS.INSURANCE_PLAN: Level of Coverage
    service_area_id: str # geographic area, location fit (may not be needed if all returned plans are a location fit); RBIS.INSURANCE_PLAN: Service_Area_ID
    premium: float # monthly premium; RBIS.INSURANCE_PLAN_BASE_RATE_FILE: Individual Rate
    deductible: float # annual deductible, shows initial out-of-pocket costs; RBIS.INSURANCE_PLAN_VARIANT_DDCTL_MOOP: Insurance Plan Individual Deductible Amount
    copay: float # fixed amount paid for each service; RBIS.INSURANCE_PLAN_BENEFIT_COST_SHARE: Co Payment
    out_of_pocket_max: float # max annual out-of-pocket expenses; RBIS.INSURANCE_PLAN_VARIANT_DDCTBL_MOOP: Insurance Plan Annual Out of Pocket Limit Amount
    covered_medications: list[str] # list of covered medications; RBIS.INSURANCE_PLAN_BENEFITS: Benefit
    num_dependents: int
    couple_or_primary: str

# This class is used to store minimal output information about searched health insurance plans
@dataclass
class HIPlan:
    id: databaseId # database identifier for the plan
    rank: int # how well the plan matches user preferences compared to the N closest plans returned
    score: float # how well the plan matches user preferences
    info: HIPlanInfo # info needed for summarization


# --- class interfaces --- #

# An interface for the health insurance database searcher
class HIPlanSearchInterface(ABC):
    # This function takes a user profile and returns the top matching results
    @abstractmethod
    def MatchPlansFromProfile(profile: UserProfile, takeTopN: int) -> list[HIPlan]:
        pass
    # This function returns the full information corresponding to database IDs
    @abstractmethod
    def RetrievePlanInfo(ids: list[databaseId]) -> list[HIPlanInfo]:
        pass



