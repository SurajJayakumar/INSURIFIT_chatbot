from Interfaces import *

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

