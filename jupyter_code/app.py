# # In app.py, improved version with better error handling:
# import joblib
# from flask import Flask, request, jsonify, send_file, Response
# import pandas as pd
# import os
# from datetime import datetime
# import io
# from fpdf import FPDF
# import traceback
# import re  # Add this at the top of your app.py file with other imports
# from smoking1 import SmokingCessationAdvisor  # Import the SmokingCessationAdvisor class

# # Initialize the advisor
# advisor = SmokingCessationAdvisor()
# advisor.load_model()  # Load the model

# app = Flask(__name__)

# @app.route('/')
# def home():
#     return "Welcome to the Smoking Cessation Predictor API!"

# @app.route('/predict', methods=['POST'])
# def predict():
#     try:
#         app.logger.info("Received prediction request")
#         data = request.get_json(force=True)
#         app.logger.info(f"Request data: {data}")
        
#         # Create user profile from input data
#         user_profile = {
#             'Gender': data['gender'],
#             'Age': data['age'],
#             'Smoking Duration': data['years_smoking'],
#             'Cigarettes per day': data['cigarettes_per_day'],
#             'Previous Quit Attempts': data['previous_attempts'],
#             'Craving Level': data['craving_level'],
#             'Stress Level': data['stress_level'],
#             'Physical Activity': data['physical_activity'],
#             'Support System': data['support_system'],
#             'Nicotine Dependence Score': data['nicotine_Dependence'],
#             'Reason for Start Smoking': data['reason_for_starting'],
#             'Location': 'National (States and DC)',  # Default value
#             'Smoking Behavior': 'Cigarette Use (Youth)',  # Default value
#             'Smoking Percentage': min(data['cigarettes_per_day'] * 1.0, 100)  # Calculated field
#         }

#         # Check if report generation is requested
#         generate_report = data.get('generate_report', False)
#         app.logger.info(f"Generate report? {generate_report}")
        
#         if not generate_report:
#             # Original behavior: just return prediction
#             prediction = advisor.predict_quit_success(user_profile)
#             prediction_value = int(prediction > 0.5)
#             app.logger.info(f"Returning prediction: {prediction_value} (probability: {prediction:.4f})")
#             return jsonify({'prediction': prediction_value, 'probability': float(prediction)})
        
#         # Otherwise, generate PDF report
#         app.logger.info("Generating PDF report")
#         # Get recommendations
#         recommendations = advisor.get_recommendations(user_profile)
        
#         # Generate comprehensive report
#         report_text = advisor.generate_report(user_profile, recommendations, 'comprehensive')
        
#         # Convert report to PDF
#         pdf_file = create_pdf_report(report_text, user_profile)
#         app.logger.info("PDF report created successfully")
        
#         filename = f"smoking_cessation_report_{datetime.now().strftime('%Y%m%d')}.pdf"
#         return send_file(
#             pdf_file,
#             mimetype='application/pdf',
#             as_attachment=True,
#             download_name=filename
#         )

#     except Exception as e:
#         app.logger.error(f"Error in prediction: {str(e)}")
#         app.logger.error(traceback.format_exc())
#         return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500



# def create_pdf_report(report_text, user_profile):
#     """Convert text report to PDF with improved formatting and text wrapping"""
#     # Replace Unicode bullet points with compatible characters
#     report_text = report_text.replace('•', '-')
    
#     pdf = FPDF()
#     # Set page size and margins
#     pdf.set_left_margin(15)
#     pdf.set_right_margin(15)
#     pdf.set_auto_page_break(True, margin=15)  # Enable auto page break
#     pdf.add_page()
    
#     # Set up fonts
#     pdf.set_font("Arial", 'B', 16)
#     pdf.cell(180, 10, "Smoking Cessation Report", 0, 1, 'C')
    
#     # Add date
#     pdf.set_font("Arial", '', 12)
#     pdf.cell(180, 10, f"Generated on: {datetime.now().strftime('%B %d, %Y')}", 0, 1, 'R')
    
#     # Add report content with improved formatting
#     # Split the report text into sections and process
#     sections = report_text.split('===')
    
#     for section in sections:
#         if not section.strip():
#             continue
            
#         # Process section title and content
#         lines = section.strip().split('\n')
#         if not lines:
#             continue
            
#         # Section heading
#         section_title = lines[0].strip()
#         pdf.set_font("Arial", 'B', 14)
#         pdf.ln(5)
#         # Draw a light gray background for section headers
#         pdf.set_fill_color(240, 240, 240)
#         pdf.cell(180, 8, section_title.upper(), 0, 1, 'L', True)
#         pdf.ln(2)
        
#         # Process content after the heading
#         pdf.set_font("Arial", '', 10)
#         content_lines = lines[1:] if len(lines) > 1 else []
        
#         # Handle different section types
#         section_name = section_title.upper()
        
#         # For profile section, handle one item per line
#         if "YOUR PROFILE" in section_name:
#             for line in content_lines:
#                 line = line.strip()
#                 if not line:
#                     pdf.ln(2)
#                     continue
                
#                 # Handle profile items (key: value)
#                 if ':' in line:
#                     parts = line.split(':', 1)
#                     if len(parts) == 2:
#                         key, value = parts[0].strip(), parts[1].strip()
#                         pdf.set_font("Arial", 'B', 10)
#                         # Key on its own line
#                         pdf.cell(180, 6, key + ':', 0, 1)
#                         # Value indented on next line
#                         pdf.set_font("Arial", '', 10)
#                         pdf.cell(10, 6, "", 0, 0)  # Indent
#                         pdf.multi_cell(170, 6, value)
#                         pdf.ln(1)  # Extra space between items
#                     else:
#                         pdf.multi_cell(180, 6, line)
#                 else:
#                     pdf.multi_cell(180, 6, line)
        
#         # For success probability section
#         elif "YOUR QUIT SUCCESS PROBABILITY" in section_name:
#             for line in content_lines:
#                 line = line.strip()
#                 if not line:
#                     pdf.ln(2)
#                     continue
                    
#                 # Handle probability line specifically
#                 if line.startswith("Estimated probability"):
#                     pdf.set_font("Arial", 'B', 12)
#                     pdf.multi_cell(180, 6, line)
#                     pdf.ln(2)
#                     pdf.set_font("Arial", '', 10)
#                 else:
#                     # Regular text with proper wrapping
#                     pdf.multi_cell(180, 6, line)
#                     pdf.ln(2)
                    
#         # For all other sections
#         else:
#             current_subsection = ""
            
#             for line in content_lines:
#                 line = line.strip()
#                 if not line:
#                     pdf.ln(2)
#                     continue
                    
#                 # Handle subsection titles (marked with ---)
#                 if line.startswith('---'):
#                     current_subsection = line.replace('-', '').strip()
#                     pdf.set_font("Arial", 'B', 12)
#                     pdf.ln(3)
#                     pdf.cell(180, 6, current_subsection, 0, 1, 'L')
#                     pdf.set_font("Arial", '', 10)
#                     pdf.ln(1)
#                     continue
                
#                 # Handle numbered points (like "1. Something")
#                 if re.match(r'^\d+\.', line):
#                     parts = line.split('.', 1)
#                     if len(parts) == 2:
#                         pdf.set_font("Arial", 'B', 10)
#                         num_part = parts[0] + '.'
#                         text_part = parts[1].strip()
                        
#                         # Add number with fixed width
#                         pdf.cell(8, 6, num_part, 0, 0)
#                         pdf.set_font("Arial", '', 10)
#                         # Use multi_cell to ensure proper wrapping
#                         pdf.multi_cell(172, 6, text_part)
#                         pdf.ln(1)
#                     else:
#                         # Fallback if splitting fails
#                         pdf.multi_cell(180, 6, line)
#                         pdf.ln(1)
#                     continue
                    
#                 # Handle bullet points
#                 if line.startswith('-') or line.startswith('•'):
#                     pdf.cell(8, 6, '-', 0, 0)
#                     pdf.multi_cell(172, 6, line[1:].strip())
#                     pdf.ln(1)
#                     continue
                    
#                 # Handle "Why:" lines with proper indentation
#                 if line.startswith('Why:'):
#                     pdf.cell(15, 6, 'Why:', 0, 0)
#                     pdf.set_font("Arial", 'I', 10)  # Italics for the explanation
#                     pdf.multi_cell(165, 6, line[4:].strip())
#                     pdf.set_font("Arial", '', 10)  # Back to normal font
#                     pdf.ln(1)
#                     continue
                
#                 # Handle section headers that might be in ALL CAPS
#                 if line.upper() == line and len(line) > 10:
#                     pdf.set_font("Arial", 'B', 11)
#                     pdf.multi_cell(180, 6, line)
#                     pdf.set_font("Arial", '', 10)
#                     pdf.ln(1)
#                     continue
                    
#                 # Default handling for regular text
#                 pdf.multi_cell(180, 6, line)
#                 pdf.ln(1)  # Add space after paragraphs
    
#     # Create in-memory file object
#     pdf_buffer = io.BytesIO()
    
#     # Different FPDF versions handle output differently
#     try:
#         pdf_bytes = pdf.output(dest='S')
#         if not isinstance(pdf_bytes, bytes):
#             pdf_bytes = bytes(pdf_bytes)
#         pdf_buffer.write(pdf_bytes)
#     except TypeError:
#         # For newer FPDF versions
#         pdf_buffer = io.BytesIO(pdf.output(dest='S').encode('latin-1'))
    
#     pdf_buffer.seek(0)
#     return pdf_buffer

# @app.route('/report', methods=['POST'])
# def generate_report_only():
#     """Generate report without saving to disk"""
#     try:
#         app.logger.info("Received report generation request")
#         data = request.get_json(force=True)
#         app.logger.info(f"Report request data: {data}")
        
#         # Same user profile creation as in predict
#         user_profile = {
#             'Gender': data['gender'],
#             'Age': data['age'],
#             'Smoking Duration': data['years_smoking'],
#             'Cigarettes per day': data['cigarettes_per_day'],
#             'Previous Quit Attempts': data['previous_attempts'],
#             'Craving Level': data['craving_level'],
#             'Stress Level': data['stress_level'],
#             'Physical Activity': data['physical_activity'],
#             'Support System': data['support_system'],
#             'Nicotine Dependence Score': data['nicotine_Dependence'],
#             'Reason for Start Smoking': data['reason_for_starting'],
#             'Location': 'National (States and DC)',  # Default value
#             'Smoking Behavior': 'Cigarette Use (Youth)',  # Default value
#             'Smoking Percentage': min(data['cigarettes_per_day'] * 1.0, 100)  # Calculated field
#         }
        
#         # Get recommendations
#         recommendations = advisor.get_recommendations(user_profile)
        
#         # Generate report based on type
#         report_type = data.get('report_type', 'comprehensive')
#         app.logger.info(f"Generating {report_type} report")
#         report_text = advisor.generate_report(user_profile, recommendations, report_type)
        
#         # Return as JSON if client prefers
#         if data.get('format', 'pdf') == 'json':
#             prediction = advisor.predict_quit_success(user_profile)
#             app.logger.info("Returning JSON report")
#             return jsonify({
#                 'report': report_text, 
#                 'success_probability': float(prediction)
#             })
        
#         # Otherwise return as PDF
#         app.logger.info("Creating PDF for report")
#         pdf_file = create_pdf_report(report_text, user_profile)
#         app.logger.info("PDF created successfully")
        
#         filename = f"smoking_cessation_report_{datetime.now().strftime('%Y%m%d')}.pdf"
#         return send_file(
#             pdf_file,
#             mimetype='application/pdf',
#             as_attachment=True,
#             download_name=filename
#         )

#     except Exception as e:
#         app.logger.error(f"Error in report generation: {str(e)}")
#         app.logger.error(traceback.format_exc())
#         return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

# # Add a dedicated endpoint just for testing PDF generation
# @app.route('/test-pdf', methods=['GET'])
# def test_pdf():
#     """Test endpoint that always returns a simple PDF"""
#     try:
#         app.logger.info("Testing PDF generation")
        
#         # Create a simple PDF
#         pdf = FPDF()
#         pdf.add_page()
#         pdf.set_font("Arial", size=12)
#         pdf.cell(200, 10, txt="This is a test PDF from the Smoking Cessation API", ln=True)
#         pdf.cell(200, 10, txt=f"Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
        
#         # Output to memory
#         pdf_buffer = io.BytesIO()
#         pdf.output(pdf_buffer)
#         pdf_buffer.seek(0)
        
#         app.logger.info("Test PDF created successfully")
        
#         # Return the PDF
#         return send_file(
#             pdf_buffer,
#             mimetype='application/pdf',
#             as_attachment=True,
#             download_name=f"test_pdf_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
#         )
#     except Exception as e:
#         app.logger.error(f"Error in PDF test: {str(e)}")
#         app.logger.error(traceback.format_exc())
#         return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

# if __name__ == '__main__':
#     app.run(debug=True)


# Updated app.py with PDF report generation and download functionality
import joblib
from flask import Flask, request, jsonify, send_file, make_response
import pandas as pd
from io import BytesIO
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime

# Import our SmokingCessationAdvisor class
from smoking1 import SmokingCessationAdvisor

# Load the model
model = joblib.load('smoking_cessation_model.pkl')

# Create an instance of the advisor
advisor = SmokingCessationAdvisor(model_path='smoking_cessation_model.pkl')

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

        # Create user profile dictionary from data
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
            'Location': 'National (States and DC)',
            'Smoking Behavior': 'Cigarette Use (Youth)',
            'Smoking Percentage': min(data['cigarettes_per_day'] * 1.0, 100)
        }

        return jsonify({
            'prediction': int(prediction),
            'report_url': f"/get_report?user_id={request.remote_addr}"  # Include a URL to download the report
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def create_pdf_report(text, title):
    """
    Create a properly formatted PDF report from cessation plan text
    
    Parameters:
    text (str): The report text to convert
    title (str): The title of the PDF report
    
    Returns:
    BytesIO: A buffer containing the PDF data
    """
    buffer = BytesIO()
    
    # Create PDF document with appropriate margins
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter,
        rightMargin=72,  # 1 inch margins
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = styles['Title']
    heading1_style = styles['Heading1']
    heading2_style = styles['Heading2']
    heading3_style = styles['Heading3']
    normal_style = styles['Normal']
    
    # Add spacing after paragraphs
    normal_style.spaceAfter = 6
    heading1_style.spaceAfter = 12
    heading2_style.spaceAfter = 10
    heading3_style.spaceAfter = 8
    
    # Create content elements
    content = []
    
    # Add title
    content.append(Paragraph(title, title_style))
    content.append(Spacer(1, 24))  # Add more space after title
    
    # Add generation date
    current_date = datetime.now().strftime("%B %d, %Y")
    content.append(Paragraph(f"Generated on: {current_date}", normal_style))
    content.append(Spacer(1, 24))
    
    in_profile_section = False
    in_list_item = False
    bullet_text = ""
    
    # Split text by lines and add each line with proper formatting
    lines = text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines unless needed for spacing
        if line == '':
            if not in_profile_section:  # Don't add extra space in profile section
                content.append(Spacer(1, 6))
            i += 1
            continue
            
        # Handle section headers
        if line.startswith('===') and line.endswith('==='):
            # Main section header
            header_text = line.strip('= ')
            content.append(Spacer(1, 12))
            content.append(Paragraph(header_text, heading1_style))
            content.append(Spacer(1, 6))
            
            # Check if this is the profile section
            if "PROFILE" in header_text:
                in_profile_section = True
            else:
                in_profile_section = False
                
        # Handle subsection headers
        elif line.startswith('---') and line.endswith('---'):
            # Subsection header
            header_text = line.strip('- ')
            content.append(Paragraph(header_text, heading2_style))
            
        # Handle bullet points and list items
        elif line.startswith('•') or line.startswith('-'):
            bullet_text = line[1:].strip()
            
            # Check if there's more content on next lines that belongs to this bullet
            next_index = i + 1
            while (next_index < len(lines) and 
                   not lines[next_index].strip().startswith('•') and 
                   not lines[next_index].strip().startswith('-') and
                   not lines[next_index].strip().startswith('===') and
                   not lines[next_index].strip().startswith('---') and
                   not lines[next_index].strip() == ''):
                bullet_text += " " + lines[next_index].strip()
                i = next_index
                next_index += 1
                
            content.append(Paragraph("• " + bullet_text, normal_style))
        
        # Handle profile key-value pairs
        elif in_profile_section and (':' in line):
            key, value = line.split(':', 1)
            content.append(Paragraph(f"<b>{key.strip()}:</b> {value.strip()}", normal_style))
            
        # Handle numbered list items
        elif line[0].isdigit() and line[1:].startswith('.'):
            item_text = line.strip()
            
            # Check if there's more content on next lines that belongs to this item
            next_index = i + 1
            while (next_index < len(lines) and 
                   not lines[next_index].strip().startswith('•') and 
                   not lines[next_index].strip().startswith('-') and
                   not lines[next_index].strip()[0].isdigit() and
                   not lines[next_index].strip().startswith('===') and
                   not lines[next_index].strip().startswith('---') and
                   not lines[next_index].strip().startswith('Why:') and
                   not lines[next_index].strip() == ''):
                item_text += " " + lines[next_index].strip()
                i = next_index
                next_index += 1
                
            content.append(Paragraph(item_text, normal_style))
            
            # Check for "Why:" explanations that follow list items
            if next_index < len(lines) and lines[next_index].strip().startswith('Why:'):
                why_text = lines[next_index].strip()
                content.append(Paragraph(f"<i>{why_text}</i>", normal_style))
                i = next_index
        
        # Regular text
        else:
            para_text = line.strip()
            
            # Check if there's more content on next lines that should be in the same paragraph
            next_index = i + 1
            while (next_index < len(lines) and 
                   not lines[next_index].strip().startswith('•') and 
                   not lines[next_index].strip().startswith('-') and
                   not lines[next_index].strip().startswith('===') and
                   not lines[next_index].strip().startswith('---') and
                   not lines[next_index].strip() == '' and
                   not lines[next_index].strip()[0].isdigit() and
                   ':' not in lines[next_index].strip()):
                para_text += " " + lines[next_index].strip()
                i = next_index
                next_index += 1
                
            content.append(Paragraph(para_text, normal_style))
        
        i += 1
    
    # Build PDF
    doc.build(content)
    buffer.seek(0)
    
    return buffer

@app.route('/generate_report', methods=['POST'])
def generate_report():
    try:
        data = request.get_json(force=True)
        report_type = data.get('report_type', 'comprehensive')  # Default to comprehensive

        # Create user profile dictionary from data
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
            'Location': 'National (States and DC)',
            'Smoking Behavior': 'Cigarette Use (Youth)',
            'Smoking Percentage': min(data['cigarettes_per_day'] * 1.0, 100)
        }

        # Get recommendations
        recommendations = advisor.get_recommendations(user_profile)
        
        # Generate report as text
        text_report = advisor.generate_report(user_profile, recommendations, report_type)
        
        # Format report title based on type
        report_title = f"Comprehensive Smoking Cessation Plan" if report_type == 'comprehensive' else f"Smoking Cessation {report_type.title()} Report"
        
        # Convert report to PDF using the new function
        pdf_buffer = create_pdf_report(text_report, report_title)
        
        # Create response with PDF file
        response = make_response(pdf_buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=smoking_cessation_plan_{datetime.now().strftime("%Y%m%d")}.pdf'
        
        return response

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_report', methods=['GET'])
def get_report():
    try:
        user_id = request.args.get('user_id', 'anonymous')
        report_type = request.args.get('report_type', 'comprehensive')
        
        # This is a placeholder - in a real application, you'd look up the user's data
        # stored in a database or session to generate their report
        
        # For demonstration, we'll use sample data
        user_profile = {
            'Gender': 'Overall',
            'Age': 35,
            'Smoking Duration': 15,
            'Cigarettes per day': 20,
            'Previous Quit Attempts': 2,
            'Craving Level': 'Medium',
            'Stress Level': 'Medium',
            'Physical Activity': 'Moderate',
            'Support System': 'Family & Friends',
            'Nicotine Dependence Score': 6,
            'Reason for Start Smoking': 'Peer Pressure',
            'Location': 'National (States and DC)',
            'Smoking Behavior': 'Cigarette Use (Youth)',
            'Smoking Percentage': 20.0
        }
        
        # Get recommendations
        recommendations = advisor.get_recommendations(user_profile)
        
        # Generate comprehensive report
        report = advisor.generate_report(user_profile, recommendations, report_type)
        
        # Format report title based on type
        report_title = f"Comprehensive Smoking Cessation Plan" if report_type == 'comprehensive' else f"Smoking Cessation {report_type.title()} Report"
        
        # Convert to PDF using the new function
        pdf_buffer = create_pdf_report(report, report_title)
        
        # Create response with PDF file
        response = make_response(pdf_buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=smoking_cessation_plan_{datetime.now().strftime("%Y%m%d")}.pdf'
        
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Keeping the old function for backward compatibility if needed
def convert_text_to_pdf(text, title):
    """
    Convert text to PDF format
    
    Parameters:
    text (str): The text to convert
    title (str): The title of the PDF
    
    Returns:
    BytesIO: A buffer containing the PDF data
    """
    buffer = BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Create content elements
    content = []
    
    # Add title
    content.append(Paragraph(title, styles['Title']))
    content.append(Spacer(1, 12))
    
    # Split text by lines and add each line
    for line in text.split('\n'):
        if line.startswith('===') and line.endswith('==='):
            # Section header
            header_text = line.strip('= ')
            content.append(Spacer(1, 6))
            content.append(Paragraph(header_text, styles['Heading2']))
            content.append(Spacer(1, 6))
        elif line.startswith('---') and line.endswith('---'):
            # Subsection header
            header_text = line.strip('- ')
            content.append(Paragraph(header_text, styles['Heading3']))
        elif line.strip() == '':
            # Empty line
            content.append(Spacer(1, 6))
        else:
            # Regular text
            content.append(Paragraph(line, styles['Normal']))
    
    # Build PDF
    doc.build(content)
    buffer.seek(0)
    
    return buffer

if __name__ == '__main__':
    app.run(debug=True)