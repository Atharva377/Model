import requests
import streamlit as st
import datetime
import pandas as pd
import random
from dotenv import load_dotenv  
import os
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if 'implemented_measures' not in st.session_state:
    st.session_state.implemented_measures = []
if 'improvement_history' not in st.session_state:
    st.session_state.improvement_history = []

def get_groq_response(prompt, model_type):
    groq_api_url = "https://api.groq.com/openai/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    
    system_message = {
        "model1": """You are a student advisor chatbot specialized in dropout prevention. 
        When providing preventive measures:
        1. Always provide exactly 5 measures
        2. Each measure must start with a category in square brackets
        3. Categories must be one of: [Counseling], [Mentoring], [Academic Support], [Financial Aid], [Engagement], [Monitoring]
        4. Each measure must be specific and actionable
        5. Format as a numbered list""",
        
        "model2": """You are an analytics bot that evaluates student dropout rate changes.
        When generating reports:
        1. Start with a clear summary of the rate change
        2. Analyze whether the change indicates improvement or decline
        3. Provide specific observations based on the measure type
        4. Give actionable recommendations
        5. Include quantitative analysis where possible"""
    }
    
    data = {
        "messages": [
            {"role": "system", "content": system_message[model_type]},
            {"role": "user", "content": prompt}
        ],
        "model": "llama-3.3-70b-versatile"
    }
    
    try:
        response = requests.post(groq_api_url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error: {str(e)}"

def calculate_improvement(measure_type, initial_rate):
    measure_lower = measure_type.lower()
    
    improvements = {
        "counseling": (5, 30, "Individual counseling sessions impact varied"),
        "mentoring": (10, 35, "Mentoring program showed varying results"),
        "academic support": (15, 40, "Academic support services impact observed"),
        "financial aid": (20, 45, "Financial assistance impact noted"),
        "engagement": (10, 35, "Engagement changes affected attendance"),
        "monitoring": (5, 30, "Monitoring showed mixed results")
    }
    
    for key, (min_imp, max_imp, feedback) in improvements.items():
        if key in measure_lower:
            improvement = random.uniform(min_imp, max_imp)
        
            if random.random() < 0.4: 
                improvement = -improvement  
            return improvement, feedback
    
    return random.uniform(-25, 25), "General impact observed"

def calculate_rate_change(initial_rate, adjusted_improvement):
    """
    Calculate the new dropout rate and rate change considering both improvement and decline
    
    Args:
        initial_rate (float): Initial dropout rate percentage
        adjusted_improvement (float): The calculated improvement percentage
                                    (positive means dropout reduction/improvement)
                                    (negative means dropout increase/decline)
    
    Returns:
        tuple: (new_rate, rate_change, change_direction)
    """
    # For dropout rates:
    # - A positive improvement should REDUCE the dropout rate
    # - A negative improvement should INCREASE the dropout rate
    rate_change = (adjusted_improvement / 100) * initial_rate
    
    new_rate = initial_rate - rate_change

    new_rate = max(0, min(100, new_rate))

    change_direction = "-" if new_rate < initial_rate else "+"
    
    return new_rate, abs(rate_change), change_direction

def display_improvement_metrics(col1, col2, col3, last_measures, new_rate, rate_change, change_direction):
    with col1:
        st.metric("Initial Rate", f"{last_measures['rate']:.1f}%")
    with col2:
        delta_color = "inverse" if new_rate > last_measures['rate'] else "normal"
        st.metric(
            "Current Rate", 
            f"{new_rate:.1f}%",
            f"{change_direction}{rate_change:.1f}%",
            delta_color=delta_color
        )
    with col3:
        status = "Decline" if new_rate > last_measures['rate'] else "Improvement"
        status_color = "#FF4B4B" if status == "Decline" else "#0FBA81"
        st.markdown(
            f"""
            <div style="padding: 10px; border-radius: 4px;">
                <p style="font-size: 14px; color: #808495; margin-bottom: 4px;">Status</p>
                <p style="font-size: 20px; color: {status_color}; margin: 0;">{status}</p>
            </div>
            """, 
            unsafe_allow_html=True
        )

def generate_improvement_report(measure, initial_rate, improvement_percentage, feedback):
    prompt = f"""
    Analyze the following dropout rate changes:
    
    MEASURE DETAILS:
    - Implementation: {measure}
    - Initial Rate: {initial_rate}%
    - Rate Change: {improvement_percentage:.1f}%
    - Key Observation: {feedback}
    
    Please provide a structured analysis following these points:
    1. Rate Change Summary
       - Quantify the change
       - Indicate if this is an improvement or decline
    
    2. Measure Effectiveness
       - Analyze why the measure succeeded or failed
       - Compare to expected outcomes
    
    3. Specific Observations
       - Key factors contributing to the change
       - Impact on different aspects of student engagement
    
    4. Recommendations
       - Specific actions to improve or maintain results
       - Risk mitigation strategies if needed
    
    5. Future Outlook
       - Expected trends
       - Key areas to monitor
    """
    return get_groq_response(prompt, "model2")

st.title("Student Dropout Prevention and Improvement Tracking System")

tab1, tab2 = st.tabs(["Get Preventive Measures", "Track Improvement"])

# Tab 1: Get Preventive Measures
with tab1:
    st.header("Dropout Prevention Analysis")
    
    initial_rate = st.number_input(
        "Current Dropout Rate (%):",
        0.0, 100.0, 0.0,
        key="initial_rate_input"
    )
    factors = st.text_area(
        "Describe the contributing factors:",
        key="factors_input"
    )
    
    if st.button("Get Preventive Measures", key="get_measures_button"):
        with st.spinner("Analyzing factors..."):
            prompt = f"""
            The dropout rate is {initial_rate}%. 
            The contributing factors are: {factors}. 
            Provide 5 specific, actionable preventive measures.
            Format each measure as a numbered list with the measure type in brackets.
            Example:
            1. [Counseling] Implement weekly individual counseling sessions
            2. [Academic Support] Provide after-school tutoring
            """
            
            measures = get_groq_response(prompt, "model1")
            st.write("### Recommended Preventive Measures:")
            st.write(measures)

            st.session_state.implemented_measures.append({
                "date": datetime.datetime.now(),
                "rate": initial_rate,
                "measures": measures.split('\n')
            })

# Tab 2: Track Improvement
with tab2:
    st.header("Progress Tracking")

    if not st.session_state.implemented_measures:
        st.warning("Please get preventive measures first in Tab 1")
    else:
        last_measures = st.session_state.implemented_measures[-1]
        st.write("### Select a highly effective measure:")

        valid_measures = [measure for measure in last_measures["measures"] if measure.strip()]

        selected_measure = st.radio(
            "Available Measures:",
            valid_measures,
            key="measure_radio"
        )

        if selected_measure:
            st.write(f"### Initial Dropout Rate: {last_measures['rate']}%")
            st.write("### Provide Feedback on the Student:")

            # 1. Attendance
            st.subheader("1. Attendance")
            attendance_improved = st.radio("Has the student’s attendance improved in the past month?", ["True", "False"], key="attendance_improved")
            attendance_consistency = st.slider("How consistent is the student’s attendance overall? (1 = highly inconsistent, 10 = always present)", 1, 10, key="attendance_consistency")

            # 2. Academic Performance
            st.subheader("2. Academic Performance")
            academic_performance_improved = st.radio("Has the student’s academic performance improved (e.g., better test scores, assignments)?", ["True", "False"], key="academic_performance_improved")
            grasp_academic_concepts = st.slider("How would you rate the student’s ability to grasp academic concepts? (1 = very poor, 10 = excellent)", 1, 10, key="grasp_academic_concepts")
            completing_assignments = st.radio("Is the student completing assignments and homework regularly?", ["True", "False"], key="completing_assignments")

            # 3. Classroom Engagement
            st.subheader("3. Classroom Engagement")
            classroom_engagement = st.radio("Is the student more engaged during classroom discussions and activities?", ["True", "False"], key="classroom_engagement")
            attentiveness_in_class = st.slider("How would you rate the student’s attentiveness in class? (1 = very inattentive, 10 = highly attentive)", 1, 10, key="attentiveness_in_class")
            asking_questions = st.radio("Is the student asking questions or seeking clarification when needed?", ["True", "False"], key="asking_questions")

            # 4. Social and Emotional Behavior
            st.subheader("4. Social and Emotional Behavior")
            behavior_improved = st.radio("Has the student’s behavior improved in terms of discipline and respect?", ["True", "False"], key="behavior_improved")
            interaction_with_peers = st.slider("How would you rate the student’s ability to interact positively with peers? (1 = very poor, 10 = excellent)", 1, 10, key="interaction_with_peers")
            emotional_stability = st.radio("Is the student showing signs of emotional stability (e.g., less stress, more confidence)?", ["True", "False"], key="emotional_stability")

            # 5. Parental Involvement
            st.subheader("5. Parental Involvement")
            parental_support = st.radio("Are the student’s parents actively supporting the student’s education?", ["True", "False"], key="parental_support")
            parental_involvement = st.slider("How involved are the parents in assisting the student’s academic growth? (1 = not involved at all, 10 = highly involved)", 1, 10, key="parental_involvement")

            # 6. Participation in Preventive Measures
            st.subheader("6. Participation in Preventive Measures")
            active_participation = st.radio("Has the student participated actively in the preventive measures (e.g., extra classes, mentoring sessions)?", ["True", "False"], key="active_participation")
            enthusiasm_in_activities = st.slider("How would you rate the student’s enthusiasm for the assigned preventive activities? (1 = not enthusiastic, 10 = very enthusiastic)", 1, 10, key="enthusiasm_in_activities")

            # 7. Extracurricular Engagement
            st.subheader("7. Extracurricular Engagement")
            extracurricular_participation = st.radio("Is the student participating in extracurricular activities (e.g., sports, art, clubs)?", ["True", "False"], key="extracurricular_participation")
            extracurricular_performance = st.slider("How would you rate the student’s performance in extracurricular activities? (1 = very poor, 10 = excellent)", 1, 10, key="extracurricular_performance")

            # 8. Time Management and Effort
            st.subheader("8. Time Management and Effort")
            effective_time_management = st.radio("Is the student managing their time effectively for studies and other commitments?", ["True", "False"], key="effective_time_management")
            overall_effort = st.slider("How would you rate the student’s overall effort and commitment to improving? (1 = very little effort, 10 = exceptional effort)", 1, 10, key="overall_effort")

            # 9. Gender-Specific and Cultural Barriers (if applicable)
            st.subheader("9. Gender-Specific and Cultural Barriers (if applicable)")
            cultural_barriers = st.radio("Are there any cultural or societal barriers affecting the student’s ability to attend or focus on school?", ["True", "False"], key="cultural_barriers")
            family_support_cultural_barriers = st.slider("How supportive is the student’s family toward overcoming such barriers? (1 = not supportive, 10 = highly supportive)", 1, 10, key="family_support_cultural_barriers")

            # 10. Overall Assessment
            st.subheader("10. Overall Assessment")
            dropout_risk_reduction = st.radio("Do you think the student’s overall risk of dropout has reduced?", ["True", "False"], key="dropout_risk_reduction")
            overall_progress = st.slider("How would you rate the student’s overall progress since the last intervention? (1 = no progress, 10 = significant progress)", 1, 10, key="overall_progress")
            # Process the feedback responses
            if st.button("Analyze Improvement", key="analyze_improvement_button"):
                st.write("### Analyzing Improvement...")

                feedback_scores = {
                        # 1. Attendance
                        "attendance_consistency": (attendance_consistency - 5) * 4,
                        "attendance": 20 if attendance_improved == "True" else -40,
    
                        # 2. Academic Performance
                        "academic_performance": 20 if academic_performance_improved == "True" else -40,
                        "grasp_academic_concepts": (grasp_academic_concepts - 5) * 4,
                        "completing_assignments": 20 if completing_assignments == "True" else -40,
    
                        # 3. Classroom Engagement
                        "classroom_engagement": 20 if classroom_engagement == "True" else -40,
                        "attentiveness_in_class": (attentiveness_in_class - 5) * 4,
                        "asking_questions": 20 if asking_questions == "True" else -40,
    
                        # 4. Social and Emotional Behavior
                        "behavior_improved": 20 if behavior_improved == "True" else -40,
                        "interaction_with_peers": (interaction_with_peers - 5) * 4,
                        "emotional_stability": 20 if emotional_stability == "True" else -40,
    
                        # 5. Parental Involvement
                        "parental_support": 20 if parental_support == "True" else -40,
                        "parental_involvement": (parental_involvement - 5) * 4,
    
                        # 6. Participation in Preventive Measures
                        "active_participation": 20 if active_participation == "True" else -40,
                        "enthusiasm_in_activities": (enthusiasm_in_activities - 5) * 4,
    
                        # 7. Extracurricular Engagement
                        "extracurricular_participation": 20 if extracurricular_participation == "True" else -40,
                        "extracurricular_performance": (extracurricular_performance - 5) * 4,
    
                        # 8. Time Management and Effort
                        "effective_time_management": 20 if effective_time_management == "True" else -40,
                        "overall_effort": (overall_effort - 5) * 4,
    
                        # 9. Cultural Barriers
                        "cultural_barriers": -40 if cultural_barriers == "True" else 20,  # Inverted and doubled
                        "family_support_cultural_barriers": (family_support_cultural_barriers - 5) * 4,
    
                        # 10. Overall Assessment
                        "dropout_risk_reduction": 20 if dropout_risk_reduction == "True" else -40,
                        "overall_progress": (overall_progress - 5) * 4
                    }


                weights = {
                    "attendance": 0.15,  
                    "attendance_consistency": 0.15,  
                    "academic_performance": 0.20, 
                    "grasp_academic_concepts": 0.15, 
                    "completing_assignments": 0.15,  
                    "classroom_engagement": 0.15,
                    "attentiveness_in_class": 0.15,
                    "asking_questions": 0.15,
                    "behavior_improved": 0.10,
                    "interaction_with_peers": 0.10,
                    "emotional_stability": 0.10,
                    "parental_support": 0.15,
                    "parental_involvement": 0.15
                }

                total_feedback_score = sum(
                    weights.get(key, 0.10) * value
                    for key, value in feedback_scores.items()
                )

                improvement_percentage, feedback_summary = calculate_improvement(selected_measure, last_measures["rate"])

                adjusted_improvement = improvement_percentage + (total_feedback_score / 1.5)  # Changed from /10 to /5

                new_rate, rate_change, change_direction = calculate_rate_change(
                    last_measures["rate"], 
                    adjusted_improvement
                )

                report = generate_improvement_report(
                    selected_measure,
                    last_measures["rate"],
                    rate_change,
                    feedback_summary
                )

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Initial Rate", f"{last_measures['rate']:.1f}%")
                with col2:
                    delta_color = "inverse" if new_rate > last_measures['rate'] else "normal"
                    st.metric(
                        "Current Rate", 
                        f"{new_rate:.1f}%",
                        f"{change_direction}{rate_change:.1f}%",
                        delta_color=delta_color
                    )
                with col3:
                    status = "Decline" if new_rate > last_measures['rate'] else "Improvement"
                    status_color = "#FF4B4B" if status == "Decline" else "#0FBA81"
                    st.markdown(
                        f"""
                        <div style="padding: 10px; border-radius: 4px;">
                            <p style="font-size: 14px; color: #808495; margin-bottom: 4px;">Status</p>
                            <p style="font-size: 20px; color: {status_color}; margin: 0;">{status}</p>
                            </div>
                            """, 
                            unsafe_allow_html=True
                        )
                    
                st.write("### Improvement Report")
                st.write(report)

                st.session_state.improvement_history.append({
                    "date": datetime.datetime.now(),
                    "measure": selected_measure,
                    "initial_rate": last_measures["rate"],
                    "final_rate": new_rate,
                    "rate_change": rate_change,
                    "feedback": feedback_summary,
                    "feedback_scores": feedback_scores
                })

# Sidebar for history
with st.sidebar:
    st.header("Improvement History")
    if st.session_state.improvement_history:
        for entry in reversed(st.session_state.improvement_history):
            with st.expander(f"Measure: {entry['measure'][:50]}..."):
                st.write(f"Date: {entry['date'].strftime('%Y-%m-%d %H:%M')}")
                st.write(f"Initial Rate: {entry['initial_rate']:.1f}%")
                st.write(f"Final Rate: {entry['final_rate']:.1f}%")
                st.write(f"Rate Change: {entry['rate_change']:.1f}%")
                st.write(f"Feedback: {entry['feedback']}")

# Download reports
if st.session_state.improvement_history:
    df = pd.DataFrame(st.session_state.improvement_history)
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download Improvement History",
        data=csv,
        file_name="improvement_history.csv",
        mime="text/csv",
        key="download_button"
    )