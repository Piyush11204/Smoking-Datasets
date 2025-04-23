# In app.py, improved version with better error handling:
import joblib
from flask import Flask, request, jsonify, send_file, Response
import pandas as pd
import os
from datetime import datetime
import io
from fpdf import FPDF
import traceback
import re  # Add this import
from smoking1 import SmokingCessationAdvisor  # Import the SmokingCessationAdvisor class

# Initialize the advisor
advisor = SmokingCessationAdvisor()
advisor.load_model()  # Load the model

app = Flask(__name__)

@app.route('/')
def home():
    return "Welcome to the Smoking Cessation Predictor API!"

@app.route('/predict', methods=['POST'])
def predict():
    try:
        app.logger.info("Received prediction request")
        data = request.get_json(force=True)
        app.logger.info(f"Request data: {data}")
        
        # Create user profile from input data
        user_profile = {
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
        }

        # Check if report generation is requested
        generate_report = data.get('generate_report', False)
        app.logger.info(f"Generate report? {generate_report}")
        
        if not generate_report:
            # Original behavior: just return prediction
            prediction = advisor.predict_quit_success(user_profile)
            prediction_value = int(prediction > 0.5)
            app.logger.info(f"Returning prediction: {prediction_value} (probability: {prediction:.4f})")
            return jsonify({'prediction': prediction_value, 'probability': float(prediction)})
        
        # Otherwise, generate PDF report
        app.logger.info("Generating PDF report")
        # Get recommendations
        recommendations = advisor.get_recommendations(user_profile)
        
        # Generate comprehensive report
        report_text = advisor.generate_report(user_profile, recommendations, 'comprehensive')
        
        # Convert report to PDF
        pdf_file = create_pdf_report(report_text, user_profile)
        app.logger.info("PDF report created successfully")
        
        filename = f"smoking_cessation_report_{datetime.now().strftime('%Y%m%d')}.pdf"
        return send_file(
            pdf_file,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        app.logger.error(f"Error in prediction: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

def create_pdf_report(report_text, user_profile):
    """Convert text report to PDF with improved formatting"""
    pdf = FPDF()
    pdf.add_page()
    
    # Set default font
    pdf.set_font("Arial", size=10)
    
    # Add title
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(190, 15, "Smoking Cessation Report", 0, 1, 'C')
    
    # Add date
    pdf.set_font("Arial", 'I', 12)
    pdf.cell(190, 10, f"Generated on: {datetime.now().strftime('%B %d, %Y')}", 0, 1, 'R')
    pdf.ln(5)
    
    # Process the report content
    sections = report_text.split('===')
    
    for section in sections:
        if not section.strip():
            continue
            
        lines = section.strip().split('\n')
        if not lines:
            continue
            
        # Section heading
        heading = lines[0].strip()
        if heading:
            pdf.set_font("Arial", 'B', 14)
            pdf.set_fill_color(240, 240, 240)  # Light gray background
            pdf.cell(190, 10, heading, 0, 1, 'L', True)
            pdf.ln(2)
        
        # Process content
        pdf.set_font("Arial", '', 10)
        for line in lines[1:]:
            line = line.strip()
            if not line:
                pdf.ln(2)
                continue
            
            # Subsection titles (marked with ---)
            if line.startswith('---'):
                subsection = line.replace('-', '').strip()
                pdf.set_font("Arial", 'B', 12)
                pdf.set_fill_color(245, 245, 245)
                pdf.cell(190, 8, subsection, 0, 1, 'L', True)
                pdf.set_font("Arial", '', 10)
                continue
            
            # Numbered points
            if re.match(r'^\d+\.', line):
                parts = line.split('.', 1)
                if len(parts) == 2:
                    pdf.set_font("Arial", 'B', 10)
                    pdf.cell(10, 6, parts[0] + '.', 0, 0)
                    pdf.set_font("Arial", '', 10)
                    pdf.multi_cell(180, 6, parts[1].strip())
                continue
            
            # Bullet points
            if line.startswith('•') or line.startswith('-'):
                pdf.cell(10, 6, '•', 0, 0)
                pdf.multi_cell(180, 6, line[1:].strip())
                continue
            
            # Profile information
            if ':' in line and len(line) < 50:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    pdf.set_font("Arial", 'B', 10)
                    pdf.cell(50, 6, parts[0] + ':', 0, 0)
                    pdf.set_font("Arial", '', 10)
                    pdf.multi_cell(140, 6, parts[1].strip())
                    continue
            
            # Regular text
            pdf.multi_cell(190, 6, line)
    
    # Create in-memory buffer
    pdf_buffer = io.BytesIO()
    pdf_bytes = pdf.output(dest='S').encode('latin1')  # Encode to handle special characters
    pdf_buffer.write(pdf_bytes)
    pdf_buffer.seek(0)
    
    return pdf_buffer

@app.route('/report', methods=['POST'])
def generate_report_only():
    try:
        app.logger.info("Received report generation request")
        data = request.get_json(force=True)
        app.logger.info(f"Report request data: {data}")
        
        # Create user profile from input data
        user_profile = {
            'Gender': data.get('gender', 'Overall'),
            'Age': data.get('age', 30),
            'Smoking Duration': data.get('years_smoking', 0),
            'Cigarettes per day': data.get('cigarettes_per_day', 0),
            'Previous Quit Attempts': data.get('previous_attempts', 0),
            'Craving Level': data.get('craving_level', 'Medium'),
            'Stress Level': data.get('stress_level', 'Medium'),
            'Physical Activity': data.get('physical_activity', 'Moderate'),
            'Support System': data.get('support_system', 'None'),
            'Nicotine Dependence Score': data.get('nicotine_Dependence', 0),
            'Reason for Start Smoking': data.get('reason_for_starting', 'Other'),
            'Location': 'National (States and DC)',
            'Smoking Behavior': 'Cigarette Use (Youth)',
            'Smoking Percentage': min(data.get('cigarettes_per_day', 0) * 1.0, 100)
        }
        
        recommendations = advisor.get_recommendations(user_profile)
        report_type = data.get('report_type', 'comprehensive')
        report_text = advisor.generate_report(user_profile, recommendations, report_type)
        
        if data.get('format', 'pdf') == 'json':
            prediction = advisor.predict_quit_success(user_profile)
            return jsonify({
                'report': report_text,
                'success_probability': float(prediction)
            })
        
        pdf_file = create_pdf_report(report_text, user_profile)
        filename = f"smoking_cessation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return send_file(
            pdf_file,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        app.logger.error(f"Error in report generation: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

# Add a dedicated endpoint just for testing PDF generation
@app.route('/test-pdf', methods=['GET'])
def test_pdf():
    """Test endpoint that always returns a simple PDF"""
    try:
        app.logger.info("Testing PDF generation")
        
        # Create a simple PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="This is a test PDF from the Smoking Cessation API", ln=True)
        pdf.cell(200, 10, txt=f"Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
        
        # Output to memory
        pdf_buffer = io.BytesIO()
        pdf.output(pdf_buffer)
        pdf_buffer.seek(0)
        
        app.logger.info("Test PDF created successfully")
        
        # Return the PDF
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"test_pdf_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )
    except Exception as e:
        app.logger.error(f"Error in PDF test: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

if __name__ == '__main__':
    app.run(debug=True)