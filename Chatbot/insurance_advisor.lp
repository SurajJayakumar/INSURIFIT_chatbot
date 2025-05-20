% --- Dynamically Generated Facts (from Python) ---
% These will be added by the Python script for each user/plan evaluation.
% Example format (UNCOMMENT FOR DIRECT TESTING):
%user(currentUser).
%age(currentUser, 47).
%dependents(currentUser, 2).
%tobacco_user(currentUser). % Present if true
%desires_premium_max(currentUser, 500). % Max desired premium (numeric)
%desires_deductible_max(currentUser, 3000). % Max desired deductible (numeric)
%desires_oop_max(currentUser, 6000). % Max desired OOP (numeric)
%user_wants_benefit(currentUser, preventative_care).
%user_wants_benefit(currentUser, diabetes_care).
%user_on_medication(currentUser). % Fact present if user is on any medication

%plan(plan123). % The current plan being evaluated
%plan_premium(plan123, 450).
%plan_deductible(plan123, 2500).
%plan_oop_max(plan123, 7000).
%plan_metal_level(plan123, gold).
%plan_type(plan123, hmo).
%plan_covers_benefit(plan123, diabetes_care).


% --- Threshold Definitions ---
low_premium_threshold(300).      % Example: premiums below this are considered "low" by user
moderate_premium_threshold(600).
low_deductible_threshold(1000).   % Example: deductibles below this are "low"
moderate_deductible_threshold(4000).
very_low_premium_threshold_for_low_income_inference(250).
age_threshold_older_for_oop_warning(40).
age_threshold_young_for_preventative(40).
age_threshold_medicare(65).
age_threshold_low_income_inference(30).


% --- Intermediate Inferred Predicates (User Characteristics) ---

% Helper: User desires a numerically low premium
user_desires_low_premium(User) :-
    user(User), % Ensure User is grounded
    desires_premium_max(User, DesiredMaxP),
    low_premium_threshold(Threshold),
    DesiredMaxP < Threshold.

% Helper: User desires a numerically low deductible
user_desires_low_deductible(User) :-
    user(User), % Ensure User is grounded
    desires_deductible_max(User, DesiredMaxD),
    low_deductible_threshold(Threshold),
    DesiredMaxD < Threshold.

% 0.5) Young and Healthy Status
is_young_for_health_status(User) :-
    user(User), age(User, Age),
    age_threshold_young_for_preventative(AgeThreshold),
    Age < AgeThreshold.

is_healthy_candidate(User) :- % Candidate, can be overridden
    user(User),
    user_wants_benefit(User, preventative_care),
    is_young_for_health_status(User).

is_young_and_healthy(User) :-
    user(User),
    is_healthy_candidate(User),
    not user_on_medication(User), % True if user_on_medication(User) is not derivable
    not tobacco_user(User).       % True if tobacco_user(User) is not derivable

% --- Rules for Generating Advice/Insights (These become the predicates fed to Gemini API for better explanations) ---

% 1) Warning: Older user wanting low premium but plan premium is higher
advice_consider_low_oop_due_to_age_and_premium_mismatch(User, Plan) :-
    user(User), plan(Plan),
    desires_premium_max(User, DesiredMaxP),
    plan_premium(Plan, ActualP),
    ActualP > DesiredMaxP, % Plan is more expensive than desired
    age(User, Age),
    age_threshold_older_for_oop_warning(AgeThreshold),
    Age > AgeThreshold.
#show advice_consider_low_oop_due_to_age_and_premium_mismatch/2.

% 2) Medicare Suggestion
advice_consider_medicare(User) :-
    user(User),
    age(User, Age),
    age_threshold_medicare(AgeThreshold),
    Age >= AgeThreshold.
#show advice_consider_medicare/1.



% 4) Unrealistic Financial Goals & Trade-off Advice
advice_unrealistic_financial_goals(User) :-
    user(User),
    user_desires_low_premium(User),
    user_desires_low_deductible(User).
#show advice_unrealistic_financial_goals/1.

% favor higher premiums to be safe or risk it for lower premiums?
advice_tradeoff_higher_premium_for_lower_deductible(User) :-
    user(User),
    dependents(User, Deps),
    Deps > 0,
    user_wants_benefit(User, chemotherapy),
    user_desires_low_deductible(User).

advice_tradeoff_higher_premium_for_lower_deductible(User) :-
    user(User),
    dependents(User, Deps),
    Deps > 0,
    user_wants_benefit(User, diabetes_care),
    user_desires_low_deductible(User).

advice_tradeoff_higher_premium_for_lower_deductible(User) :-
    user(User),
    dependents(User, Deps),
    Deps > 0,
    user_wants_benefit(User, dialysis),
    user_desires_low_deductible(User).
#show advice_tradeoff_higher_premium_for_lower_deductible/1.

advice_tradeoff_higher_deductible_for_lower_premium(User) :-
    user(User),
    is_young_and_healthy(User),
    user_desires_low_premium(User).
#show advice_tradeoff_higher_deductible_for_lower_premium/1.

% 5) Tobacco Use Implications
advice_tobacco_impacts_premium(User) :-
    user(User),
    tobacco_user(User).
#show advice_tobacco_impacts_premium/1.

% 6) Dependents Benefit Suggestions (Split into separate rules)
advice_consider_family_benefit(User, delivery_and_maternity_care) :-
    not user_wants_benefit(User, delivery_and_maternity_care),
    user(User),
    dependents(User, Deps), Deps > 0.

advice_consider_family_benefit(User, pediatric_services_other) :-
    not user_wants_benefit(User,pediatric_services_other),
    user(User),
    dependents(User, Deps), Deps > 0.
#show advice_consider_family_benefit/2.

% 7) Infer Potential Low Income (as a candidate for advice)
advice_potential_low_income_considerations(User) :-
    user(User),
    desires_premium_max(User, DesiredMaxP),
    very_low_premium_threshold_for_low_income_inference(Threshold),
    DesiredMaxP < Threshold,
    age(User, Age),
    age_threshold_low_income_inference(AgeThreshold),
    Age > AgeThreshold,
    dependents(User, Deps), Deps > 0.
#show advice_potential_low_income_considerations/1.


% --- General Plan Evaluation Predicates  ---

% Plan meets user's desired premium
plan_meets_desired_premium(Plan, User) :-
    plan(Plan), user(User),
    plan_premium(Plan, ActualP),
    desires_premium_max(User, DesiredMaxP), 
    ActualP <= DesiredMaxP.
#show plan_meets_desired_premium/2.

% Plan exceeds user's desired premium
plan_exceeds_desired_premium(Plan, User) :-
    plan(Plan), user(User),
    plan_premium(Plan, ActualP),
    desires_premium_max(User, DesiredMaxP),
    ActualP > DesiredMaxP.
#show plan_exceeds_desired_premium/2.

% Plan meets user's desired deductible
plan_meets_desired_deductible(Plan, User) :-
    plan(Plan), user(User),
    plan_deductible(Plan, ActualD),
    desires_deductible_max(User, DesiredMaxD), 
    ActualD <= DesiredMaxD.
#show plan_meets_desired_deductible/2.

% Plan exceeds user's desired deductible
plan_exceeds_desired_deductible(Plan, User) :-
    plan(Plan), user(User),
    plan_deductible(Plan, ActualD),
    desires_deductible_max(User, DesiredMaxD),
    ActualD > DesiredMaxD.
#show plan_exceeds_desired_deductible/2.

% Plan meets user's desired OOP max
plan_meets_desired_oop_max(Plan, User) :-
    plan(Plan), user(User),
    plan_oop_max(Plan, ActualO),
    desires_oop_max(User, DesiredMaxO), 
    ActualO <= DesiredMaxO.
#show plan_meets_desired_oop_max/2.

% Plan exceeds user's desired OOP max
plan_exceeds_desired_oop_max(Plan, User) :-
    plan(Plan), user(User),
    plan_oop_max(Plan, ActualO),
    desires_oop_max(User, DesiredMaxO),
    ActualO > DesiredMaxO.
#show plan_exceeds_desired_oop_max/2.

% --- Auxiliary predicates for checking existence of desired limits ---
has_desires_premium_max(User) :- user(User), desires_premium_max(User, _ValueP).
has_desires_deductible_max(User) :- user(User), desires_deductible_max(User, _ValueD).
% No #show needed for these helpers usually

% --- asp_validates_plan rule  ---

% Case 1: Meets premium preference, Meets deductible preference
asp_validates_plan(Plan, User) :-
    plan(Plan), user(User),
    plan_meets_desired_premium(Plan, User),
    plan_meets_desired_deductible(Plan, User),
    not advice_consider_medicare(User).

% Case 2: Meets premium preference, No deductible preference set by user
asp_validates_plan(Plan, User) :-
    plan(Plan), user(User),
    plan_meets_desired_premium(Plan, User),
    not has_desires_deductible_max(User),
    not advice_consider_medicare(User).

% Case 3: No premium preference set by user, Meets deductible preference
asp_validates_plan(Plan, User) :-
    plan(Plan), user(User),
    not has_desires_premium_max(User),
    plan_meets_desired_deductible(Plan, User),
    not advice_consider_medicare(User).

% Case 4: No premium preference set by user, No deductible preference set by user
asp_validates_plan(Plan, User) :-
    plan(Plan), user(User),
    not has_desires_premium_max(User),
    not has_desires_deductible_max(User),
    not advice_consider_medicare(User).

#show asp_validates_plan/2.
