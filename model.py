import requests
import streamlit as st
import datetime
import pandas as pd
import random  

# Groq API Configuration
GROQ_API_KEY = "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"

# Initialize session state for tracking measures and improvements
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
        "model1": "You are a student advisor chatbot. Provide numbered, specific preventive measures for student dropout.",
        "model2": "You are an analytics bot that evaluates student improvement based on implemented measures."
    }
    
    data = {
        "messages": [
            {"role": "system", "content": system_message[model_type]},
            {"role": "user", "content": prompt}
        ],
        "model": "mixtral-8x7b-32768"
    }
    
    try:
        response = requests.post(groq_api_url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error: {str(e)}"

def calculate_improvement(measure_type, initial_rate):
    """
    Calculate improvement based on the type of measure implemented
    Returns: (improvement_percentage, feedback)
    """
    measure_lower = measure_type.lower()
    
    # Base improvement ranges for different types of measures
    improvements = {
        "counseling": (10, 20, "Individual counseling sessions showed positive results"),
        "mentoring": (15, 25, "Mentoring program demonstrated significant impact"),
        "academic support": (20, 30, "Academic support services improved performance"),
        "financial aid": (25, 35, "Financial assistance helped retain students"),
        "engagement": (15, 25, "Increased engagement improved attendance"),
        "monitoring": (10, 20, "Regular monitoring helped early intervention")
    }
    
    # Find matching measure type
    for key, (min_imp, max_imp, feedback) in improvements.items():
        if key in measure_lower:
            improvement = random.uniform(min_imp, max_imp)
            return improvement, feedback
    
    # Default if no specific match
    return random.uniform(5, 15), "General improvement observed"

def generate_improvement_report(measure, initial_rate, improvement_percentage, feedback):
    prompt = f"""
    Generate a detailed improvement report for:
    Measure implemented: {measure}
    Initial dropout rate: {initial_rate}%
    Improvement: {improvement_percentage:.1f}%
    Feedback: {feedback}
    
    Include:
    1. Analysis of the measure's effectiveness
    2. Specific improvements observed
    3. Recommendations for further enhancement
    4. Future outlook
    """
    return get_groq_response(prompt, "model2")

# Streamlit UI
st.title("Student Dropout Prevention and Improvement Tracking System")

# Main interface tabs
tab1, tab2 = st.tabs(["Get Preventive Measures", "Track Improvement"])

# Tab 1: Get Preventive Measures
with tab1:
    st.header("Dropout Prevention Analysis")
    
    initial_rate = st.number_input(
        "Current Dropout Rate (%):",
        0, 100, 0,
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
            
            # Store measures for later use
            st.session_state.implemented_measures.append({
                "date": datetime.datetime.now(),
                "rate": initial_rate,
                "measures": measures.split('\n')  # Split into individual measures
            })

# Tab 2: Track Improvement
with tab2:
    st.header("Improvement Tracking")
    
    if not st.session_state.implemented_measures:
        st.warning("Please get preventive measures first in Tab 1")
    else:
        last_measures = st.session_state.implemented_measures[-1]
        st.write("### Select a measure to implement:")
        
        # Create radio buttons for each measure
        selected_measure = st.radio(
            "Available measures:",
            last_measures["measures"],
            key="measure_radio"
        )
        
        if selected_measure:
            st.write("### Analyzing Improvement")
            st.write(f"Initial dropout rate: {last_measures['rate']}%")
            
            # Calculate improvement based on the selected measure
            improvement_percentage, feedback = calculate_improvement(selected_measure, last_measures["rate"])
            new_rate = max(0, last_measures["rate"] - (last_measures["rate"] * improvement_percentage / 100))
            
            # Generate and display report
            report = generate_improvement_report(
                selected_measure,
                last_measures["rate"],
                improvement_percentage,
                feedback
            )
            
            # Display metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "Initial Rate",
                    f"{last_measures['rate']}%"
                )
            with col2:
                st.metric(
                    "Current Rate",
                    f"{new_rate:.1f}%",
                    f"-{improvement_percentage:.1f}%"
                )
            with col3:
                st.metric(
                    "Improvement",
                    f"{improvement_percentage:.1f}%"
                )
            
            st.write("### Improvement Report")
            st.write(report)
            
            # Store improvement history
            st.session_state.improvement_history.append({
                "date": datetime.datetime.now(),
                "measure": selected_measure,
                "initial_rate": last_measures["rate"],
                "final_rate": new_rate,
                "improvement": improvement_percentage,
                "feedback": feedback
            })

# Sidebar for history
with st.sidebar:
    st.header("Improvement History")
    if st.session_state.improvement_history:
        for entry in reversed(st.session_state.improvement_history):
            with st.expander(f"Measure: {entry['measure'][:50]}..."):
                st.write(f"Date: {entry['date'].strftime('%Y-%m-%d %H:%M')}")
                st.write(f"Initial Rate: {entry['initial_rate']}%")
                st.write(f"Final Rate: {entry['final_rate']:.1f}%")
                st.write(f"Improvement: {entry['improvement']:.1f}%")
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