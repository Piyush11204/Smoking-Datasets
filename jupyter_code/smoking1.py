import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os
from flask import Flask
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, roc_curve, auc, f1_score
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline

import warnings
warnings.filterwarnings('ignore')

class SmokingCessationAdvisor:
    """
    A comprehensive class for smoking cessation prediction and personalized recommendations
    """
    def __init__(self, data_path='combined_smoking_cessation_data.csv', model_path='models/smoking_cessation_model.pkl'):
        self.data_path = data_path
        self.model_path = model_path
        self.model = None
        self.feature_names = None
        self.feature_importances = None
        self.df = None
        self.numerical_features = ['Age', 'Smoking Duration', 'Cigarettes per day', 
                                'Previous Quit Attempts', 'Nicotine Dependence Score', 
                                'Smoking Percentage']
        self.categorical_features = ['Location', 'Gender', 'Smoking Behavior', 'Craving Level', 
                                'Stress Level', 'Physical Activity', 'Support System', 
                                'Reason for Start Smoking']
    
    def load_data(self):
        """Load the smoking cessation dataset"""
        try:
            self.df = pd.read_csv(self.data_path)
            print(f"Data loaded successfully! Shape: {self.df.shape}")
            return self.df
        except Exception as e:
            print(f"Error loading data: {e}")
            return None
    
    def load_model(self):
        """Load a previously saved model"""
        try:
            self.model = joblib.load(self.model_path)
            print("Model loaded successfully!")
            
            # Try to load feature names if available
            model_dir = os.path.dirname(self.model_path)
            feature_names_path = os.path.join(model_dir, 'feature_names.txt')
            if os.path.exists(feature_names_path):
                with open(feature_names_path, 'r') as f:
                    self.feature_names = [line.strip() for line in f.readlines()]
                print("Feature names loaded!")
                
            return self.model
        except Exception as e:
            print(f"Error loading model: {e}")
            return None
    
    def train_model(self, advanced=True, save=True):
        """
        Train a smoking cessation prediction model
        
        Parameters:
        advanced (bool): Whether to use advanced model training techniques
        save (bool): Whether to save the trained model
        """
        if self.df is None:
            self.df = self.load_data()
            if self.df is None:
                print("Unable to load data. Model training aborted.")
                return None
        
        # Prepare features and target
        X = self.df.drop('Quit Success', axis=1)
        y = self.df['Quit Success'].map({'Yes': 1, 'No': 0})
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Create preprocessor
        numerical_transformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler())
        ])
        
        categorical_transformer = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='most_frequent')),
            ('onehot', OneHotEncoder(handle_unknown='ignore'))
        ])
        
        preprocessor = ColumnTransformer(
            transformers=[
                ('num', numerical_transformer, self.numerical_features),
                ('cat', categorical_transformer, self.categorical_features)
            ])
        
        if advanced:
            print("Training advanced ensemble model...")
            
            # Handle class imbalance with SMOTE
            # print("Applying SMOTE to balance classes...")
            # X_train_transformed = preprocessor.fit_transform(X_train)
            # smote = SMOTE(random_state=42)
            # X_train_resampled, y_train_resampled = smote.fit_resample(X_train_transformed, y_train)
            
            # Create ensemble of models
            estimators = [
                ('rf', RandomForestClassifier(n_estimators=200, max_depth=10, min_samples_split=5,
                                         min_samples_leaf=2, random_state=42)),
                ('gb', GradientBoostingClassifier(n_estimators=100, learning_rate=0.1,
                                             max_depth=5, random_state=42))
            ]
            
            ensemble = VotingClassifier(estimators=estimators, voting='soft')
            
            # Create full pipeline
            self.model = Pipeline(steps=[
                ('preprocessor', preprocessor),
                ('classifier', ensemble)
            ])
            
            # Fit model
            print("Fitting ensemble model...")
            #self.model.fit(X_train, y_train_resampled)
            self.model.fit(X_train, y_train)  # ✅ Correct when using pipeline with SMOTE inside

            
            # Get feature names and importances (using RandomForest component)
            X_processed = preprocessor.fit_transform(X)
            ohe = preprocessor.named_transformers_['cat'].named_steps['onehot']
            self.feature_names = (
                self.numerical_features + 
                ohe.get_feature_names_out(self.categorical_features).tolist()
            )
            
            # For ensemble, we'll get feature importance from the RandomForest component
            rf_model = RandomForestClassifier(n_estimators=200, max_depth=10, min_samples_split=5,
                                         min_samples_leaf=2, random_state=42)
            rf_model.fit(X_processed, y)
            self.feature_importances = rf_model.feature_importances_
        else:
            print("Training basic Random Forest model...")
            # Basic model
            self.model = Pipeline(steps=[
                ('preprocessor', preprocessor),
                ('smote', SMOTE(random_state=42)), 
                ('classifier', RandomForestClassifier(n_estimators=100, random_state=42))
            ])
            
            # Fit model
            self.model.fit(X_train, y_train)
            
            # Get feature names and importances
            self.feature_names = (
                self.numerical_features + 
                preprocessor.named_transformers_['cat'].named_steps['onehot'].get_feature_names_out(self.categorical_features).tolist()
            )
            self.feature_importances = self.model.named_steps['classifier'].feature_importances_
        
        # Evaluate model
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        
        print(f"Model Evaluation:")
        print(f"Accuracy: {accuracy:.4f}")
        print(f"F1 Score: {f1:.4f}")
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred))
        
        # Save model if requested
        if save:
            self._save_model()
        
        return self.model
    
    def _save_model(self, output_dir='models'):
        """Save the model and feature information"""
        if self.model is None:
            print("No model to save!")
            return
        
        # Create output directory if needed
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Save model
        model_path = f'{output_dir}/smoking_cessation_model.pkl'
        joblib.dump(self.model, model_path)
        
        # Save feature names
        if self.feature_names is not None:
            with open(f'{output_dir}/feature_names.txt', 'w') as f:
                for feature in self.feature_names:
                    f.write(f"{feature}\n")
        
        # Save feature importances
        if self.feature_importances is not None:
            with open(f'{output_dir}/feature_importances.txt', 'w') as f:
                for i, importance in enumerate(self.feature_importances):
                    f.write(f"{self.feature_names[i]}: {importance}\n")
        
        print(f"Model and feature information saved to {output_dir}")
    
    def predict_quit_success(self, user_data):
        """
        Predict the probability of quit success for a user
        
        Parameters:
        user_data (dict): Dictionary containing user data
        
        Returns:
        float: Probability of successful quitting
        """
        if self.model is None:
            if not self.load_model():
                print("No model available. Training basic model...")
                self.train_model(advanced=False)
        
        # Convert user data to DataFrame
        df = pd.DataFrame([user_data])
        
        # Predict probability
        try:
            prob_success = self.model.predict_proba(df)[:, 1][0]
            return prob_success
        except Exception as e:
            print(f"Error during prediction: {e}")
            return 0.5  # Default to 50% if prediction fails
    
    def get_recommendations(self, user_profile):
        """
        Generate personalized recommendations based on a user's profile and success probability
        
        Parameters:
        user_profile (dict): Dictionary containing user characteristics
        
        Returns:
        list: Personalized recommendations
        """
        personalized_recs = []
        
        # Calculate success probability to tailor recommendations
        success_probability = self.predict_quit_success(user_profile)
        
        # Critical factors based on research
        
        # Support system - highly correlated with success
        if user_profile.get('Support System') == 'None':
            personalized_recs.append({
                'priority': 'CRITICAL',
                'category': 'Support',
                'recommendation': "Build a support network. This is one of the strongest predictors of success. "
                                "Consider joining a support group or seeking professional counseling.",
                'rationale': "Research shows that quitters with social support are 2-3 times more likely to succeed."
            })
        
        # Nicotine dependence - strong predictor
        if user_profile.get('Nicotine Dependence Score', 0) > 5:
            if success_probability < 0.4:
                personalized_recs.append({
                    'priority': 'CRITICAL',  # Upgraded from HIGH for low success probability
                    'category': 'Medication',
                    'recommendation': "Your high nicotine dependence combined with other factors makes medication essential. "
                                    "Schedule an appointment with your doctor to discuss prescription options like Chantix or Wellbutrin.",
                    'rationale': "For highly dependent smokers with challenging profiles, combination therapy can triple success rates."
                })
            else:
                personalized_recs.append({
                    'priority': 'HIGH',
                    'category': 'Medication',
                    'recommendation': "Your nicotine dependence score suggests you would benefit from "
                                    "nicotine replacement therapy or medication. Consult a healthcare provider.",
                    'rationale': "Nicotine replacement therapy can double your chances of quitting successfully."
                })
        
        # Cigarettes per day - indicator of dependency
        if user_profile.get('Cigarettes per day', 0) > 20:
            if success_probability < 0.3:
                personalized_recs.append({
                    'priority': 'HIGH',  # Upgraded from MEDIUM for very low success probability
                    'category': 'Reduction Strategy',
                    'recommendation': "As a heavy smoker with challenging quitting factors, start with a structured reduction plan "
                                    "before attempting to quit. Cut by 2-3 cigarettes every 3 days and use nicotine replacement "
                                    "during reduction.",
                    'rationale': "Heavy smokers with multiple risk factors often experience overwhelming withdrawal when quitting cold turkey."
                })
            else:
                personalized_recs.append({
                    'priority': 'MEDIUM',
                    'category': 'Reduction Strategy',
                    'recommendation': "Consider gradually reducing your cigarette consumption before attempting to quit completely. "
                                    "Try reducing by 25% each week.",
                    'rationale': "Heavy smokers often benefit from a gradual reduction approach rather than quitting cold turkey."
                })
        
        # Stress level - significant barrier
        if user_profile.get('Stress Level') == 'High':
            if success_probability < 0.4:
                personalized_recs.append({
                    'priority': 'HIGH',  # Upgraded from MEDIUM for low success probability
                    'category': 'Stress Management',
                    'recommendation': "Your high stress levels combined with other factors make stress management critical. "
                                    "Consider professional counseling and daily stress-reduction practices like guided "
                                    "meditation or cognitive behavioral techniques.",
                    'rationale': "For profiles with multiple challenges, untreated stress is one of the strongest predictors of early relapse."
                })
            else:
                personalized_recs.append({
                    'priority': 'MEDIUM',
                    'category': 'Stress Management',
                    'recommendation': "Your high stress levels may make quitting more difficult. Consider stress-management "
                                    "techniques such as meditation, exercise, or counseling.",
                    'rationale': "Stress is a common trigger for smoking and a major cause of relapse."
                })
        
        # Craving management - key to successful quitting
        if user_profile.get('Craving Level') == 'High':
            if success_probability < 0.3:
                personalized_recs.append({
                    'priority': 'HIGH',  # Upgraded for very low success probability
                    'category': 'Craving Management',
                    'recommendation': "With your profile, intense cravings may be your biggest challenge. Consider "
                                    "combining behavioral strategies with medication. Use the DEADS technique: Delay, "
                                    "Escape, Avoid, Distract, Substitute. Keep a detailed craving journal.",
                    'rationale': "Profiles with multiple risk factors need comprehensive craving management strategies that combine multiple approaches."
                })
            else:
                personalized_recs.append({
                    'priority': 'MEDIUM',
                    'category': 'Craving Management',
                    'recommendation': "Develop a personalized craving management plan. Identify your triggers and "
                                    "have specific strategies ready for when cravings hit.",
                    'rationale': "The ability to manage cravings effectively is strongly associated with quit success."
                })
        
        # Physical activity - helpful adjunct
        if user_profile.get('Physical Activity') == 'Sedentary':
            personalized_recs.append({
                'priority': 'MEDIUM',
                'category': 'Lifestyle',
                'recommendation': "Increasing your physical activity can help manage cravings and improve mood. "
                                "Consider starting with short daily walks.",
                'rationale': "Exercise reduces cravings and withdrawal symptoms while boosting mood naturally."
            })
        
        # Age-specific recommendations
        age = user_profile.get('Age', 35)
        if age < 25:
            personalized_recs.append({
                'priority': 'MEDIUM',
                'category': 'Age-Specific',
                'recommendation': "As a younger smoker, focus on the immediate benefits like improved fitness, "
                                "better skin, and saving money to stay motivated.",
                'rationale': "Younger smokers are often more motivated by immediate benefits than long-term health concerns."
            })
        elif age > 50:
            personalized_recs.append({
                'priority': 'MEDIUM',
                'category': 'Age-Specific',
                'recommendation': "Quitting smoking at your age can still significantly reduce your risk of "
                                "serious health problems and improve quality of life.",
                'rationale': "Research shows health benefits begin immediately after quitting, regardless of age or smoking history."
            })
        
        # Previous quit attempts - learning opportunity
        quit_attempts = user_profile.get('Previous Quit Attempts', 0)
        if quit_attempts > 2:
            if success_probability < 0.3:
                personalized_recs.append({
                    'priority': 'HIGH',  # Upgraded from MEDIUM for very low success probability
                    'category': 'Previous Attempts',
                    'recommendation': "With multiple unsuccessful attempts and challenging factors, you need a completely "
                                    "different approach. Work with a smoking cessation specialist to analyze your "
                                    "specific relapse patterns and design an intensive plan that addresses your unique barriers.",
                    'rationale': "Continuing with similar quit strategies after multiple failures may be ineffective; a specialized approach is needed."
                })
            else:
                personalized_recs.append({
                    'priority': 'MEDIUM',
                    'category': 'Previous Attempts',
                    'recommendation': "Analyze what triggered relapse in your previous quit attempts and develop "
                                    "specific strategies to address those situations.",
                    'rationale': "Each quit attempt provides valuable information for future success. Most successful quitters tried multiple times before succeeding."
                })
        
        # Low success probability specific recommendations
        if success_probability < 0.3:
            personalized_recs.append({
                'priority': 'CRITICAL',
                'category': 'Professional Help',
                'recommendation': "Based on your profile, we strongly recommend working with a smoking cessation specialist "
                                "or addiction counselor who can provide personalized ongoing support.",
                'rationale': "Users with multiple challenging factors benefit significantly from professional guidance."
            })
            
            personalized_recs.append({
                'priority': 'HIGH',
                'category': 'Intensive Strategy',
                'recommendation': "Consider a more structured, intensive approach such as a comprehensive smoking cessation "
                                "program that combines counseling, medication, and ongoing support.",
                'rationale': "Research shows that combined approaches work best for challenging cases."
            })
        
        # Medium-low success probability recommendations
        elif success_probability < 0.5:
            personalized_recs.append({
                'priority': 'HIGH',
                'category': 'Combination Approach',
                'recommendation': "Your profile suggests you would benefit from combining multiple quitting strategies: "
                                "medication + behavioral support + regular check-ins with a health provider.",
                'rationale': "Combining approaches can significantly improve success rates for more challenging cases."
            })
        
        # General recommendations - tailored by success probability
        general_recs = []
        
        # Preparation recommendation varies by success probability
        if success_probability < 0.3:
            general_recs.append({
                'priority': 'HIGH',
                'category': 'Preparation',
                'recommendation': "Take more time to prepare. Set a quit date 3-4 weeks from now and use this time to "
                                "build skills, reduce consumption gradually, and establish your support system.",
                'rationale': "More challenging cases benefit from extended preparation rather than rushing into a quit attempt."
            })
        else:
            general_recs.append({
                'priority': 'STANDARD',
                'category': 'Preparation',
                'recommendation': "Set a quit date within the next two weeks and remove all smoking products from your environment.",
                'rationale': "Having a concrete plan with a specific date increases commitment to quitting."
            })
        
        # Coping strategy recommendation
        general_recs.append({
            'priority': 'STANDARD',
            'category': 'Coping Strategy',
            'recommendation': "Practice the 4Ds when cravings hit: Delay, Deep breathe, Drink water, Do something else.",
            'rationale': "Most cravings pass within 3-5 minutes if you can distract yourself."
        })
        
        # Motivation recommendation
        general_recs.append({
            'priority': 'STANDARD',
            'category': 'Motivation',
            'recommendation': "Write down your top reasons for quitting and review them daily, especially when cravings hit.",
            'rationale': "Maintaining motivation is crucial for long-term success."
        })
        
        # Milestone celebration recommendation
        general_recs.append({
            'priority': 'STANDARD',
            'category': 'Milestone Celebration',
            'recommendation': "Plan rewards for reaching milestones (1 day, 1 week, 1 month smoke-free).",
            'rationale': "Positive reinforcement helps maintain motivation during the quit process."
        })
        
        # Add general recommendations that don't overlap with personalized ones
        existing_categories = [rec['category'] for rec in personalized_recs]
        for rec in general_recs:
            if rec['category'] not in existing_categories:
                personalized_recs.append(rec)
        
        # Sort recommendations by priority
        priority_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'STANDARD': 3}
        personalized_recs.sort(key=lambda x: priority_order[x['priority']])
        
        return personalized_recs
    
    def generate_report(self, user_profile, recommendations, report_type='brief'):
        """
        Generate a personalized smoking cessation report
        
        Parameters:
        user_profile (dict): User profile data
        recommendations (list): List of recommendation dictionaries
        report_type (str): 'brief' or 'comprehensive'
        
        Returns:
        str: Formatted report
        """
        # Calculate success probability
        success_probability = self.predict_quit_success(user_profile)
        success_percentage = success_probability * 100
        
        # Start building the report
        current_date = datetime.now().strftime("%B %d, %Y")
        
        if report_type == 'brief':
            report = f"===== SMOKING CESSATION BRIEF REPORT =====\n"
            report += f"Generated on: {current_date}\n\n"
            
            # Success probability
            report += f"=== QUIT SUCCESS PROBABILITY ===\n"
            report += f"Your estimated probability of successfully quitting: {success_percentage:.1f}%\n\n"
            
            # Brief interpretation - more detailed based on probability range
            if success_probability >= 0.7:
                report += "You have a very good chance of successfully quitting smoking! Your profile suggests you may face fewer challenges than many others.\n"
            elif success_probability >= 0.5:
                report += "You have a good chance of quitting smoking with the right approach and consistent effort.\n"
            elif success_probability >= 0.3:
                report += "Quitting may present moderate challenges, but with structured support and the right strategies, you can succeed.\n"
            else:
                report += "Based on your profile, quitting will likely be challenging. However, many people with similar profiles have succeeded with intensive support and the right approach.\n"
            
            # Top recommendations - show more for low probability cases
            num_recommendations = 5 if success_probability < 0.4 else 3
            report += f"\n=== KEY RECOMMENDATIONS ===\n"
            for i, rec in enumerate(recommendations[:num_recommendations], 1):
                report += f"{i}. {rec['recommendation']}\n"
            
            # Resources - more resources for lower probabilities
            report += "\n=== RESOURCES ===\n"
            report += "• National Quitline: 1-800-QUIT-NOW (1-800-784-8669)\n"
            report += "• SmokeFree.gov: https://smokefree.gov\n"
            
            if success_probability < 0.4:
                report += "• American Lung Association: https://www.lung.org/quit-smoking\n"
                report += "• Find a smoking cessation specialist: https://www.aafp.org/family-physician.html\n"
            
        else:  # comprehensive report
            report = f"====================================================\n"
            report += f"     COMPREHENSIVE SMOKING CESSATION PLAN\n"
            report += f"====================================================\n"
            report += f"Generated on: {current_date}\n\n"
            
            # Profile summary
            report += "=== YOUR PROFILE ===\n"
            
            # Format the profile information nicely
            profile_items = [
                ("Age", user_profile.get("Age", "N/A")),
                ("Gender", user_profile.get("Gender", "N/A")),
                ("Smoking Duration", f"{user_profile.get('Smoking Duration', 'N/A')} years"),
                ("Cigarettes per day", user_profile.get("Cigarettes per day", "N/A")),
                ("Nicotine Dependence", f"{user_profile.get('Nicotine Dependence Score', 'N/A')}/10"),
                ("Previous Quit Attempts", user_profile.get("Previous Quit Attempts", "N/A")),
                ("Stress Level", user_profile.get("Stress Level", "N/A")),
                ("Physical Activity", user_profile.get("Physical Activity", "N/A")),
                ("Support System", user_profile.get("Support System", "N/A"))
            ]
            
            for label, value in profile_items:
                report += f"{label}: {value}\n"
            
            # Quit success probability
            report += "\n=== YOUR QUIT SUCCESS PROBABILITY ===\n"
            report += f"Estimated probability of successfully quitting: {success_percentage:.1f}%\n\n"
            
            # Detailed interpretation - much more specific based on probability
            if success_probability >= 0.7:
                report += "You have a very good chance of successfully quitting smoking! Your profile shows many positive\n"
                report += "factors that are associated with successful quitting. While no quit attempt is guaranteed, \n"
                report += "with your current profile, many people find they can quit successfully with standard \n"
                report += "approaches. Focus on maintaining your motivation and following through with your plan.\n"
            elif success_probability >= 0.5:
                report += "You have a good chance of quitting smoking. Your profile includes several positive factors\n"
                report += "that can help you succeed. Be sure to prepare thoroughly and utilize the recommended strategies\n"
                report += "to maximize your chances of success. Consistency will be important in your quit journey.\n"
            elif success_probability >= 0.3:
                report += "You have a moderate chance of quitting smoking. Your profile suggests you may face some \n"
                report += "significant challenges in your quit attempt. We recommend focusing particularly on the \n"
                report += "high-priority recommendations below. With the right support and strategies, and possibly \n"
                report += "multiple attempts, you can overcome these challenges.\n"
            else:
                report += "Your profile suggests quitting will be challenging, with a lower estimated success probability.\n"
                report += "However, this does NOT mean you cannot quit successfully. Many people with similar profiles \n"
                report += "have quit by using more intensive approaches. We strongly recommend following the CRITICAL \n"
                report += "and HIGH priority recommendations, seeking professional support, and possibly using a \n"
                report += "combination of medications and behavioral strategies. Be prepared that you may need multiple \n"
                report += "serious attempts, but each attempt teaches valuable lessons for eventual success.\n"
            
            # Personalized recommendations section
            report += "\n=== YOUR PERSONALIZED RECOMMENDATIONS ===\n"
            
            # Group recommendations by priority
            for priority in ["CRITICAL", "HIGH", "MEDIUM", "STANDARD"]:
                priority_recs = [r for r in recommendations if r['priority'] == priority]
                if priority_recs:
                    if priority == "CRITICAL":
                        report += "\n--- CRITICAL PRIORITIES ---\n"
                    elif priority == "HIGH":
                        report += "\n--- HIGH PRIORITIES ---\n"
                    elif priority == "MEDIUM":
                        report += "\n--- RECOMMENDED STRATEGIES ---\n"
                    else:
                        report += "\n--- GENERAL RECOMMENDATIONS ---\n"
                    
                    for i, rec in enumerate(priority_recs, 1):
                        report += f"{i}. {rec['recommendation']}\n"
                        if report_type == 'comprehensive':
                            report += f"   Why: {rec['rationale']}\n\n"
            
            # Daily plan section - tailored by success probability
            report += "\n=== YOUR PERSONALIZED QUIT PLAN ===\n"
            
            if success_probability < 0.3:
                # More gradual approach for challenging cases
                report += "Phase 1 (Weeks 1-2): Preparation and Skill Building\n"
                report += "• Begin using a smoking journal to identify patterns and triggers\n"
                report += "• Practice delayed gratification by waiting 10 minutes before smoking\n"
                report += "• Speak with your doctor about medication options\n"
                report += "• Begin learning stress management techniques\n\n"
                
                report += "Phase 2 (Weeks 3-4): Reduction\n"
                report += "• Gradually reduce smoking by 25% each week\n"
                report += "• Start nicotine replacement if prescribed\n"
                report += "• Avoid your top 3 smoking triggers\n"
                report += "• Practice your coping strategies daily\n\n"
                
                report += "Phase 3 (Week 5): Quit Week\n"
                report += "• Set your quit date and remove all smoking materials\n"
                report += "• Follow your medication plan exactly\n"
                report += "• Check in with support people daily\n"
                report += "• Use distraction techniques for cravings\n\n"
                
                report += "Phase 4 (Weeks 6-8): Intensive Support\n"
                report += "• Continue all medications as prescribed\n"
                report += "• Attend support groups or counseling sessions\n"
                report += "• Avoid high-risk situations\n"
                report += "• Celebrate even small successes\n"
            elif success_probability < 0.5:
                # Moderate approach for medium-difficulty cases
                report += "Week 1-2: Preparation\n"
                report += "• Set your quit date 2 weeks from now\n"
                report += "• Remove all cigarettes, lighters, and ashtrays from your environment\n"
                report += "• Begin cutting down gradually\n"
                report += "• Tell friends and family about your plan to quit\n\n"
                
                report += "Week 3: Quit Week\n"
                report += "• Use nicotine replacement or medication as recommended\n"
                report += "• Practice the 4Ds when cravings hit\n"
                report += "• Check in with a support person daily\n"
                report += "• Stay busy with activities you enjoy\n\n"
                
                report += "Weeks 4-6: Building Momentum\n"
                report += "• Track your success and savings\n"
                report += "• Avoid triggers and high-risk situations\n"
                report += "• Manage stress with your chosen techniques\n"
                report += "• Reward yourself for milestones\n"
            else:
                # Standard approach for higher probability cases
                report += "Day 1-2: Preparation\n"
                report += "• Set your quit date\n"
                report += "• Remove all cigarettes, lighters, and ashtrays from your environment\n"
                report += "• Tell friends and family about your plan to quit\n\n"
                
                report += "Day 3-4: Quit Day and Early Coping\n"
                report += "• Use nicotine replacement if chosen\n"
                report += "• Practice the 4Ds when cravings hit\n"
                report += "• Stay busy with activities you enjoy\n\n"
                
                report += "Day 5-7: Building Momentum\n"
                report += "• Track your success and savings\n"
                report += "• Avoid triggers and high-risk situations\n"
                report += "• Reward yourself for making it through the first week\n\n"
            
            # Additional resources - more for lower probabilities
            report += "=== COMPREHENSIVE RESOURCES ===\n"
            report += "• National Quitline: 1-800-QUIT-NOW (1-800-784-8669)\n"
            report += "• SmokeFree.gov: https://smokefree.gov\n"
            report += "• American Lung Association: https://www.lung.org/quit-smoking\n"
            
            if success_probability < 0.5:
                report += "• CDC Tips From Former Smokers: https://www.cdc.gov/tobacco/campaign/tips/\n"
                report += "• Find a smoking cessation specialist: https://www.aafp.org/family-physician.html\n"
                report += "• Nicotine Anonymous meetings: https://nicotine-anonymous.org/\n"
            
            # Coping with challenges section - tailored to success probability
            report += "\n=== HANDLING COMMON CHALLENGES ===\n"
            
            if success_probability < 0.3:
                report += "• Overwhelming Withdrawal: Consider using combination therapy (patch + gum/lozenge)\n"
                report += "• Multiple Failed Attempts: Work with a specialist on a completely new approach\n"
                report += "• Severe Cravings: Use the HALT method (check if you're Hungry, Angry, Lonely, or Tired)\n"
                report += "• High Stress Environment: Create designated smoke-free zones and times\n"
                report += "• Limited Support: Join online communities like r/quitsmoking or QuitNet\n"
            else:
                report += "• Intense Cravings: Practice deep breathing, use the 4Ds, call a support person\n"
                report += "• Social Situations: Have a plan before attending events where others may smoke\n"
                report += "• Stress: Develop healthy alternatives like exercise, meditation, or hobbies\n"
                report += "• Weight Gain Concerns: Focus on healthy eating and moderate physical activity\n"
                report += "• Slips and Relapses: Don't give up - learn from the experience and try again\n"
            
            # Closing motivation - tailored to probability
            report += "\n=== REMEMBER ===\n"
            if success_probability < 0.3:
                report += "Even though your quit journey may be challenging, remember that thousands of people with \n"
                report += "similar profiles have successfully quit. The key is finding the right combination of \n"
                report += "strategies that work for your specific situation and not giving up. Each attempt \n"
                report += "increases your skills and knowledge about what does and doesn't work for you.\n"
            else:
                report += "Quitting smoking is one of the most important things you can do for your health.\n"
                report += "The benefits begin within 20 minutes of your last cigarette and continue to grow.\n"
                report += "Millions of people have successfully quit smoking, and you can too.\n"
        
        return report
    def run_interactive_advisor(self):
        """
        Run an interactive smoking cessation advisor
        """
        # Ensure model is loaded
        if self.model is None:
            if not self.load_model():
                print("Training a new model...")
                self.train_model(advanced=False)
        
        print("\n===== Smoking Cessation Advisor =====")
        print("This tool will help predict your chances of successfully quitting smoking")
        print("and provide personalized recommendations to help you quit.")
        
        try:
            # Collect user information
            user_profile = {}
            
            # Location (simplified)
            print("\nWhat state do you live in? (Enter state name or 'skip')")
            location = input("> ")
            user_profile['Location'] = location if location.lower() != 'skip' else 'National (States and DC)'
            
            # Gender
            print("\nWhat is your gender? (Male/Female/Overall)")
            gender = input("> ")
            user_profile['Gender'] = gender if gender in ['Male', 'Female'] else 'Overall'
            
            # Smoking behavior
            user_profile['Smoking Behavior'] = 'Cigarette Use (Youth)'
            
            # Age
            print("\nWhat is your age?")
            age = int(input("> "))
            user_profile['Age'] = age
            
            # Smoking duration
            print("\nHow many years have you been smoking?")
            smoking_duration = int(input("> "))
            user_profile['Smoking Duration'] = smoking_duration
            
            # Cigarettes per day
            print("\nHow many cigarettes do you smoke per day?")
            cigarettes_per_day = int(input("> "))
            user_profile['Cigarettes per day'] = cigarettes_per_day
            
            # Previous quit attempts
            print("\nHow many times have you attempted to quit smoking?")
            quit_attempts = int(input("> "))
            user_profile['Previous Quit Attempts'] = quit_attempts
            
            # Craving level
            print("\nHow would you rate your cigarette cravings? (Low/Medium/High)")
            craving_level = input("> ")
            user_profile['Craving Level'] = craving_level
            
            # Stress level
            print("\nHow would you rate your stress level? (Low/Medium/High)")
            stress_level = input("> ")
            user_profile['Stress Level'] = stress_level
            
            # Physical activity
            print("\nHow physically active are you? (Sedentary/Moderate/Active)")
            physical_activity = input("> ")
            user_profile['Physical Activity'] = physical_activity
            
            # Support system
            print("\nWhat kind of support system do you have? (None/Family & Friends/Professional Help)")
            support_system = input("> ")
            user_profile['Support System'] = support_system
            
            # Nicotine dependence score
            print("\nOn a scale of 0-10, how dependent are you on nicotine?")
            dependence_score = int(input("> "))
            user_profile['Nicotine Dependence Score'] = dependence_score
            
            # Reason for starting smoking
            print("\nWhat was your main reason for starting smoking?")
            print("(Curiosity/Peer Pressure/Family Influence/Media Influence/Stress Relief/Other)")
            reason = input("> ")
            user_profile['Reason for Start Smoking'] = reason
            
            # Set a default value for Smoking Percentage (estimated from cigarettes per day)
            user_profile['Smoking Percentage'] = min(cigarettes_per_day * 1.0, 100)
            
            # Generate recommendations
            recommendations = self.get_recommendations(user_profile)
            
            # Generate brief report
            brief_report = self.generate_report(user_profile, recommendations, 'brief')
            
            # Display brief report
            print("\n" + brief_report)
            
            # Ask if user wants a comprehensive report
            print("\nWould you like to generate a comprehensive cessation plan? (yes/no)")
            comprehensive_choice = input("> ")
            
            if comprehensive_choice.lower() == "yes":
                # Generate comprehensive report
                comprehensive_report = self.generate_report(user_profile, recommendations, 'comprehensive')
                
                # Save comprehensive report
                current_date = datetime.now().strftime("%Y%m%d")
                filename = f"cessation_plan_{current_date}_{user_profile.get('Location', 'user').replace(' ', '_')}.txt"
                
                with open(filename, 'w') as f:
                    f.write(comprehensive_report)
                
                print(f"\nYour comprehensive cessation plan has been saved to {filename}")
            
            print("\nThank you for using the Smoking Cessation Advisor!")
            print("Remember, quitting smoking is a journey, and each attempt increases your chances of success.")
        
        except Exception as e:
            print(f"\nAn error occurred: {e}")
            print("Please try again.")

    

# Example usage
if __name__ == "__main__":
    advisor = SmokingCessationAdvisor()
    
    # Uncomment to train an advanced model
    # advisor.train_model(advanced=True)
    
    # Run the interactive advisor
    advisor.run_interactive_advisor()

# Create the Flask app
app = Flask(__name__)

@app.route('/')
def home():
    return "Welcome to the Smoking Cessation Predictor API!"

# Initialize model for Flask app
try:
    model = joblib.load('smoking_cessation_model.pkl')
except Exception as e:
    print(f"Error loading model for Flask app: {e}")
    print("Training a new model...")
    # Train a model when the app starts if needed
    advisor = SmokingCessationAdvisor()
    advisor.load_data()
    model = advisor.train_model(advanced=True, save=True)
    joblib.dump(model, "smoking_cessation_model.pkl")