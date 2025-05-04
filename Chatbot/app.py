from flask_cors import CORS
from Interfaces import *
from flask import Flask, request, jsonify



# --- Flask App ---
app = Flask(__name__)
CORS(app)


@app.route('/recommend', methods=['POST'])
def recommend_plan():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    data=request.json
    print(f"Received data: {data}")
    required_keys=['age','desired_benefits','dependents','county','is_tobacco_user']
    if not all(key in data for key in required_keys):
        missing_keys = [key for key in required_keys if key not in data]
        return jsonify({"error": f"Missing required keys: {', '.join(missing_keys)}"}), 400
    
if __name__ == "__main__":

    # mytext = "I have diabetes and need tier 3 drugs."

    # print(extractEntities(mytext, dec.BENEFIT_LABELS, 70))
    
    # executionTime = timeit.timeit(testFunc, number=1)
    # print(f"Execution time: {executionTime:.4f} seconds")
    
    # print(db.GetServicerInfoForCountyp("EL PASO"))
    # Set host='0.0.0.0' to make it accessible on your network
    # Use debug=True only for development (auto-reloads, provides debugger)
    app.run(host='0.0.0.0', port=5000, debug=True)
