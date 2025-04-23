# In app.py, improved version with better error handling:
import joblib
from flask import Flask, request, jsonify, send_file, Response
import pandas as pd
import os
from datetime import datetime
import io
from fpdf import FPDF
import traceback
import re  # Add this at the top of your app.py file with other imports
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
    """Convert text report to PDF with improved formatting and text wrapping"""
    # Replace Unicode bullet points with compatible characters
    report_text = report_text.replace('•', '-')
    
    pdf = FPDF()
    # Set left and right margins to ensure text doesn't get cut off
    pdf.set_left_margin(15)
    pdf.set_right_margin(15)
    pdf.add_page()
    
    # Set up fonts
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(180, 10, "Smoking Cessation Report", 0, 1, 'C')
    
    # Add date
    pdf.set_font("Arial", '', 12)
    pdf.cell(180, 10, f"Generated on: {datetime.now().strftime('%B %d, %Y')}", 0, 1, 'R')
    
    # Add report content with improved formatting
    # Split the report text into sections and process
    sections = report_text.split('===')
    
    for section in sections:
        if not section.strip():
            continue
            
        # Process section title and content
        lines = section.strip().split('\n')
        if lines:
            # Section heading
            section_title = lines[0].strip()
            pdf.set_font("Arial", 'B', 14)
            pdf.ln(5)
            # Draw a light gray background for section headers
            pdf.set_fill_color(240, 240, 240)
            pdf.cell(180, 8, section_title.upper(), 0, 1, 'L', True)
            pdf.ln(2)
            
            # Process content after the heading
            pdf.set_font("Arial", '', 10)
            content_lines = lines[1:] if len(lines) > 1 else []
            
            for line in content_lines:
                line = line.strip()
                if not line:
                    pdf.ln(2)
                    continue
                    
                # Handle subsection titles (marked with ---)
                if line.startswith('---'):
                    subsection = line.replace('-', '').strip()
                    pdf.set_font("Arial", 'B', 12)
                    pdf.ln(3)
                    pdf.cell(180, 6, subsection, 0, 1, 'L')
                    pdf.set_font("Arial", '', 10)
                    continue
                
                # Handle numbered points (like "1. Something")
                if re.match(r'^\d+\.', line):
                    parts = line.split('.', 1)
                    if len(parts) == 2:
                        pdf.set_font("Arial", 'B', 10)
                        num_part = parts[0] + '.'
                        text_part = parts[1].strip()
                        
                        # Add number with fixed width
                        pdf.cell(8, 6, num_part, 0, 0)
                        pdf.set_font("Arial", '', 10)
                        # Use correct width calculation for the remaining text
                        pdf.multi_cell(172, 6, text_part)
                    else:
                        # Fallback if splitting fails
                        pdf.multi_cell(180, 6, line)
                    continue
                    
                # Handle bullet points
                if line.startswith('-') or line.startswith('•'):
                    pdf.cell(8, 6, '-', 0, 0)
                    pdf.multi_cell(172, 6, line[1:].strip())
                    continue
                    
                # Handle "Why:" lines
                if line.startswith('Why:'):
                    pdf.cell(15, 6, 'Why:', 0, 0)
                    pdf.set_font("Arial", 'I', 10)  # Italics for the explanation
                    pdf.multi_cell(165, 6, line[4:].strip())
                    pdf.set_font("Arial", '', 10)  # Back to normal font
                    continue
                    
                # Regular text - handle user profile info
                if ':' in line and len(line) < 50:  # Likely a profile field
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        key, value = parts[0], parts[1]
                        pdf.set_font("Arial", 'B', 10)
                        pdf.cell(60, 6, key + ':', 0, 0)
                        pdf.set_font("Arial", '', 10)
                        pdf.multi_cell(120, 6, value.strip())
                        continue
                
                # Default handling for regular text with proper width to prevent truncation
                pdf.multi_cell(180, 6, line)
    
    # Create in-memory file object
    pdf_buffer = io.BytesIO()
    
    # Fix: Use pdf.output() with destination parameter 'S' to get PDF as bytes
    pdf_bytes = pdf.output(dest='S').encode('latin1')  # Explicit encoding to avoid issues
    
    # Write the bytes to the BytesIO object
    pdf_buffer.write(pdf_bytes)
    pdf_buffer.seek(0)
    
    return pdf_buffer

@app.route('/report', methods=['POST'])
def generate_report_only():
    """Generate report without saving to disk"""
    try:
        app.logger.info("Received report generation request")
        data = request.get_json(force=True)
        app.logger.info(f"Report request data: {data}")
        
        # Same user profile creation as in predict
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
        
        # Get recommendations
        recommendations = advisor.get_recommendations(user_profile)
        
        # Generate report based on type
        report_type = data.get('report_type', 'comprehensive')
        app.logger.info(f"Generating {report_type} report")
        report_text = advisor.generate_report(user_profile, recommendations, report_type)
        
        # Return as JSON if client prefers
        if data.get('format', 'pdf') == 'json':
            prediction = advisor.predict_quit_success(user_profile)
            app.logger.info("Returning JSON report")
            return jsonify({
                'report': report_text, 
                'success_probability': float(prediction)
            })
        
        # Otherwise return as PDF
        app.logger.info("Creating PDF for report")
        pdf_file = create_pdf_report(report_text, user_profile)
        app.logger.info("PDF created successfully")
        
        filename = f"smoking_cessation_report_{datetime.now().strftime('%Y%m%d')}.pdf"
        return send_file(
            pdf_file,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        app.logger.error(f"Error in report generation: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

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