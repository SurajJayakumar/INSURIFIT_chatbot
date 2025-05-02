from abc import ABC, abstractmethod
from dataclasses import dataclass

# --- type definitions --- #

# database entry identifier
databaseId = int

# --- data classes --- #

# This class stores user input fields for use in health insurance database searcher
# a bool value is added via tuple to some elements as a way of showing if they are set or not.
# TODO: modify this class with necessary fields 
@dataclass
class UserProfile:
    def __init__(self):
        self.age = ""
        self.location = ""
        self.dependents = 0
        self.desiredPremium = []

    age: str # age of user (may not be necessary)
    location: str # location of user (to consider in-network)
    dependents: int # number of dependents to consider on a plan. Returned plans should only have >= number of dependents
    desiredPremium: tuple[bool, float] # desired premium, may be omitted
    desiredDeductible: tuple[bool, float] # desired deductible, may be omitted
    desiredCopay: tuple[bool, float] # desired copay amount, may be omitted
    desiredOOP: tuple[bool, float] # desired out-of-pocket amount, may be omitted
    medications: list[str] # any medicines that need to be given preference in the search
    preferences: str # other preferences (may not be necessary)

# This class is used to store minimal output information about searched health insurance plans
@dataclass
class HIPlan:
    id: databaseId # database identifier for the plan
    rank: int # how well the plan matches user preferences compared to the N closest plans returned
    score: float # how well the plan matches user preferences

# This class is used to store complete information about a plan in the database
# TODO: determine what information needs to be returned for RAG usage
@dataclass
class HIPlanInfo:
    pass

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



