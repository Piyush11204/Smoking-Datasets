# In app.py, change from using pickle to joblib:
import joblib
from flask import Flask, request, jsonify
import pandas as pd

# Load the model
model = joblib.load('smoking_cessation_model.pkl')

app = Flask(__name__)

@app.route('/')
def home():
    return "Welcome to the Smoking Cessation Predictor API!"

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json(force=True)

        # Convert input JSON into a DataFrame
        input_df = pd.DataFrame([{
            'Gender': data['gender'],
            'Age': data['age'],
            'Smoking Duration': data['years_smoking'],
            'Cigarettes per day': data['cigarettes_per_day'],
            'Previous Quit Attempts': data['previous_attempts'],
            'Craving Level': data['craving_level'],
            'Stress Level': data['stress_level'],
            'Physical Activity': data['physical_activity'],
            'Support System': data['support_system'],
            'Nicotine Dependence Score': data['nicotine_Dependence'],
            'Reason for Start Smoking': data['reason_for_starting'],
            'Location': 'National (States and DC)',  # Default value
            'Smoking Behavior': 'Cigarette Use (Youth)',  # Default value
            'Smoking Percentage': min(data['cigarettes_per_day'] * 1.0, 100)  # Calculated field
        }])

        # Predict using the model
        prediction = model.predict(input_df)[0]

        return jsonify({'prediction': int(prediction)})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)