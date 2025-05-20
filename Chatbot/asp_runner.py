import clingo
import os
import traceback
from typing import List, Dict, Any, Optional



# --- Load Static ASP Rules ---
STATIC_ASP_RULES = ""
try:
    # Determine path relative to this file (asp_runner.py)
    # Adjust if insurance_advisor.lp is elsewhere
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Assuming insurance_advisor.lp is in the same directory as asp_runner.py
    # If it's in the main project directory (where app.py is), adjust path:
    # rules_file_path = os.path.join(os.path.dirname(current_dir), "insurance_advisor.lp")
    rules_file_path = os.path.join(current_dir, "insurance_advisor.lp")

    if not os.path.exists(rules_file_path):
        # Try path relative to where app.py might be (one level up if asp_runner is in a subdir)
        app_py_level_path = os.path.join(os.path.dirname(current_dir), "insurance_advisor.lp")
        if os.path.exists(app_py_level_path):
            rules_file_path = app_py_level_path
        else:
            print(f"ERROR: Could not find ASP rules file at {rules_file_path} or {app_py_level_path}. ASP validation will be disabled.")
            raise FileNotFoundError # Or handle more gracefully

    with open(rules_file_path, "r") as f:
        STATIC_ASP_RULES = f.read()
    print("Successfully loaded ASP rules from insurance_advisor.lp")
except FileNotFoundError:
    print(f"ERROR: ASP rules file 'insurance_advisor.lp' not found. Ensure it's correctly placed.")
    STATIC_ASP_RULES = "" # Ensure it's defined even if loading fails
except Exception as e:
    print(f"Error loading ASP rules: {e}")
    STATIC_ASP_RULES = ""


def run_clingo_for_insights(user_asp_facts: List[str],
                            plan_asp_facts: List[str],
                            original_plan_id: str, # For context
                            user_asp_id: str = "currentUser",
                            plan_asp_id_in_facts: str = "currentPlan" # The ID used in plan_facts
                            ) -> Dict[str, Any]:
    """
    Runs Clingo with user and plan facts against static rules.
    Returns a dictionary containing the original plan ID and a list of inferred predicates (strings).
    """
    if not STATIC_ASP_RULES:
        print("ASP rules not loaded. Skipping Clingo execution.")
        return {"original_plan_id": original_plan_id, "inferred_predicates": ["asp_rules_not_loaded_error"]}

    asp_program_parts = []
    asp_program_parts.extend(user_asp_facts)
    asp_program_parts.extend(plan_asp_facts)
    asp_program_parts.append(STATIC_ASP_RULES) # Add the static rules

    asp_program_string = "\n".join(asp_program_parts)

    # For debugging the generated ASP program:
    # print(f"\n--- ASP Program for Plan: {original_plan_id} ---")
    # print(asp_program_string)
    # print("--- End ASP Program ---\n")

    ctl = clingo.Control(["--models=0"]) # Get all stable models
    inferred_predicates = []

    try:
        ctl.add("base", [], asp_program_string)
        ctl.ground([("base", [])])

        with ctl.solve(yield_=True) as handle:
            model_found = False
            for model in handle:
                model_found = True
                # print(f"Model found for {original_plan_id}: {model.symbols(shown=True)}")
                for symbol in model.symbols(shown=True): # Iterate through shown atoms
                    predicate_name = symbol.name
                    args = symbol.arguments

                    # Simplify arguments for Gemini: remove currentUser and currentPlan if they are the only args
                    # or if they are present with other more specific args.
                    simplified_args_list = []
                    for arg_symbol in args:
                        arg_str = str(arg_symbol)
                        # Don't include the generic user/plan IDs if other args exist or if it's a unary predicate on user/plan
                        if arg_str == user_asp_id and len(args) > 1 : continue
                        if arg_str == plan_asp_id_in_facts and len(args) > 1: continue
                        simplified_args_list.append(arg_str)

                    if simplified_args_list:
                        # For predicates like advice_consider_family_benefit(currentUser, "delivery_and_maternity_care")
                        # we want "advice consider family benefit delivery and maternity care"
                        predicate_str = predicate_name
                        for s_arg in simplified_args_list:
                            # Remove quotes from string arguments for better readability
                            predicate_str += f" {s_arg.strip('"')}"
                    else:
                        # For unary predicates like advice_consider_medicare(currentUser)
                        predicate_str = predicate_name

                    inferred_predicates.append(predicate_str.replace("_", " "))
                # Typically, for insight generation, one (or the first) model is sufficient.
                # If your ASP program is designed to produce multiple distinct sets of insights
                # in different models, you might need to aggregate them.
                break # Process only the first model for simplicity
            
            if not model_found:
                print(f"No stable model found by Clingo for plan {original_plan_id}. This might mean inconsistencies or no derivable #shown predicates.")
                # You might want to add a specific predicate if no model is found, if that's meaningful.
                # inferred_predicates.append("no_asp_model_found")


    except RuntimeError as e:
        print(f"Clingo Runtime Error for plan {original_plan_id}: {e}")
        inferred_predicates.append("clingo_runtime_error")
    except Exception as e:
        print(f"Unexpected error during ASP solving for plan {original_plan_id}: {e}")
        traceback.print_exc()
        inferred_predicates.append("asp_solving_exception")

    return {"original_plan_id": original_plan_id, "inferred_predicates": list(set(inferred_predicates))}


def test_clingo_setup(user_info:List[str], plan_info:List[str],user_asp_id: str = "currentUser",
                            plan_asp_id_in_facts: str = "currentPlan")->Optional[List[str]]:
    """
    # Tests the Clingo setup with static rules and mock dynamic facts.
    # """
    print("\n--- Testing Clingo Setup ---")

    if not STATIC_ASP_RULES:
        print("Static ASP rules not loaded. Cannot perform test.")
        return

    # Test 1: Run Clingo with only static rules
    print("\nTest 1: Running Clingo with STATIC_ASP_RULES only...")
    ctl_static = clingo.Control(["--models=0"])
    static_test_passed = False
    try:
        ctl_static.add("base_static", [], STATIC_ASP_RULES)
        ctl_static.ground([("base_static", [])])
        with ctl_static.solve(yield_=True) as handle:
            for model_count, model in enumerate(handle): # Iterate to check if it solves
                print(f"  Static rules model {model_count+1} found (may be empty if no facts): {model.symbols(shown=True)}")
                static_test_passed = True
                break # Just need to know it can solve
            if not static_test_passed: # No model found but solved
                 print("  Static rules parsed and grounded, but no model found (expected if no facts lead to #shown atoms).")
                 static_test_passed = True # Parsing and grounding is a success for this test
        print("  Test 1 Result: Static rules parsed and grounded successfully.")
    except RuntimeError as e:
        print(f"  Test 1 FAILED: Clingo Runtime Error with static rules: {e}")
    except Exception as e:
        print(f"  Test 1 FAILED: Unexpected error with static rules: {e}")
        traceback.print_exc()

    # Test 2: Run Clingo with static rules AND mock dynamic facts
    print("\nTest 1: Running Clingo with static rules and dynamic facts...")
    mock_user_facts = user_info
    mock_plan_facts = plan_info

    combined_program_parts = []
    combined_program_parts.extend(mock_user_facts)
    combined_program_parts.extend(mock_plan_facts)
    combined_program_parts.append(STATIC_ASP_RULES)
    combined_program_string = "\n".join(combined_program_parts)

    print("\n--- Mock ASP Program for Test 2 ---")
    print(combined_program_string)
    print("--- End Mock ASP Program ---\n")

    ctl_dynamic = clingo.Control(["--models=0"])
    inferred_predicates=[]
    try:
        ctl_dynamic.add("base_dynamic", [], combined_program_string)
        ctl_dynamic.ground([("base_dynamic", [])])
        print("  Mock dynamic program grounded successfully.")
        with ctl_dynamic.solve(yield_=True) as handle:
            for model_count, model in enumerate(handle):
                print(f"  Dynamic test model {model_count+1} found. Shown atoms:")
                for symbol in model.symbols(shown=True):
                    print(f"    {symbol}")
                    predicate_name = symbol.name
                    args = symbol.arguments

                    # Simplify arguments for Gemini: remove currentUser and currentPlan if they are the only args
                    # or if they are present with other more specific args.
                    simplified_args_list = []
                    for arg_symbol in args:
                        arg_str = str(arg_symbol)
                        # Don't include the generic user/plan IDs if other args exist or if it's a unary predicate on user/plan
                        if arg_str == user_asp_id and len(args) > 1 : continue
                        if arg_str == plan_asp_id_in_facts and len(args) > 1: continue
                        simplified_args_list.append(arg_str)

                    if simplified_args_list:
                        # For predicates like advice_consider_family_benefit(currentUser, "delivery_and_maternity_care")
                        # we want "advice consider family benefit delivery and maternity care"
                        predicate_str = predicate_name
                        for s_arg in simplified_args_list:
                            # Remove quotes from string arguments for better readability
                            predicate_str += f" {s_arg.strip('"')}"
                    else:
                        # For unary predicates like advice_consider_medicare(currentUser)
                        predicate_str = predicate_name

                    inferred_predicates.append(predicate_str.replace("_", " "))
                
        print("  Test 1 Result: Static rules with mock dynamic facts processed successfully by Clingo.")
    except RuntimeError as e:
        print(f"  Test 2 FAILED: Clingo Runtime Error with mock dynamic facts: {e}")
        print("    This likely indicates a syntax error in your STATIC_ASP_RULES or how facts interact with them.")
    except Exception as e:
        print(f"  Test 2 FAILED: Unexpected error with mock dynamic facts: {e}")
        traceback.print_exc()

    print("\n--- End of Clingo Setup Test ---")
    return inferred_predicates

if __name__ == '__main__':
    # This will run when asp_runner.py is executed directly
    test_clingo_setup()
