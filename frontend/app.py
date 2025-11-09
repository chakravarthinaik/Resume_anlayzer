import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime

# Configure the Streamlit app
st.set_page_config(
    page_title="Resume Analyzer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Constants
API_BASE_URL = "http://localhost:8000"

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'current_analysis' not in st.session_state:
    st.session_state.current_analysis = None
if 'page' not in st.session_state:
    st.session_state.page = 'login'

def login_user(username, password):
    try:
        response = requests.post(f"{API_BASE_URL}/auth/login", json={"username": username, "password": password})
        if response.status_code == 200:
            st.session_state.authenticated = True
            st.session_state.username = username
            st.session_state.page = 'analyze'
            return True, "Login successful!"
        else:
            return False, response.json().get("detail", "Login failed")
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def register_user(username, password, confirm_password, email):
    try:
        if password != confirm_password:
            st.error("Passwords do not match.")
            return
        response = requests.post(f"{API_BASE_URL}/auth/register", json={
            "username": username,
            "password": password,
            "confirm_password": confirm_password,
            "email": email
        })
        if response.status_code == 200:
            st.success("Registration successful! Please log in.")
            #st.session_state.page = 'login'
            return True, "Registration successful! Please login."
        else:
            return False, response.json().get("detail", "Registration failed")
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def upload_resume(resume_file, job_desc_file, threshold):
    try:
        files = {
            "resume_file": (resume_file.name, resume_file.getvalue(), "application/pdf"),
            "job_description": (job_desc_file.name, job_desc_file.getvalue(), "application/pdf")
        }
        data = {"recommended_store": threshold}
        
        response = requests.post(
            f"{API_BASE_URL}/resume/upload_resume",
            files=files,
            data=data
        )
        
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, response.json().get("detail", "Upload failed")
    except Exception as e:
        return False, f"Upload error: {str(e)}"

def get_analysis_by_id(file_id):
    """Get analysis results by file ID"""
    try:
        response = requests.get(f"{API_BASE_URL}/resume/get_analysis/{file_id}")
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, response.json().get("detail", "Analysis not found")
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def display_analysis_results(analysis_data):
    """Display analysis results in an enhanced tile and tabular format"""
    if not analysis_data or 'analysis' not in analysis_data:
        st.error("❌ No analysis data available")
        return
    
    analysis = analysis_data['analysis']
    
    # Header with Analysis ID
    st.markdown("### 📊 Resume Analysis Report")
    
    # Key Information Tiles
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # File Info Tile
        with st.container():
            st.markdown("""
            <div style='background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center;'>
                <h4 style='color: #000000; margin-bottom: 10px;'>📄 File Info</h4>
                <p style='color: #000000; margin: 5px 0;'><strong>ID:</strong> {}</p>
                <p style='color: #000000; margin: 5px 0;'><strong>File:</strong> {}</p>
            </div>
            """.format(
                analysis_data.get('file_id', 'N/A')[:8] + "...",
                analysis_data.get('filename', 'N/A')
            ), unsafe_allow_html=True)
    
    with col2:
        # Overall Score Tile
        overall_score = analysis.get('overall_score', 0)
        score_color = "#28a745" if overall_score >= 80 else "#ffc107" if overall_score >= 60 else "#dc3545"
        with st.container():
            st.markdown(f"""
            <div style='background-color: {score_color}20; padding: 20px; border-radius: 10px; text-align: center; border-left: 5px solid {score_color};'>
                <h4 style='color: #000000; margin-bottom: 10px;'>📈 Overall Score</h4>
                <h2 style='color: {score_color}; margin: 0;'>{overall_score}/100</h2>
                <p style='color: #000000; margin-top: 5px;'>Resume Quality</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col3:
        # Resume Style Tile
        style_score = analysis.get('resume_styling_score', 0)
        style_color = "#28a745" if style_score >= 8 else "#ffc107" if style_score >= 6 else "#dc3545"
        with st.container():
            st.markdown(f"""
            <div style='background-color: {style_color}20; padding: 20px; border-radius: 10px; text-align: center; border-left: 5px solid {style_color};'>
                <h4 style='color: #000000; margin-bottom: 10px;'>✍️ Style Score</h4>
                <h2 style='color: {style_color}; margin: 0;'>{style_score}/10</h2>
                <p style='color: #000000; margin-top: 5px;'>Formatting & Grammar</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col4:
        # Recommendation Status Tile
        recommended_count = 0
        total_count = 0
        if 'evaluations' in analysis:
            for eval_item in analysis['evaluations']:
                for role, details in eval_item.items():
                    total_count += 1
                    if details.get('status', '').lower() == 'recommended':
                        recommended_count += 1
        
        rec_color = "#28a745" if recommended_count > 0 else "#dc3545"
        with st.container():
            st.markdown(f"""
            <div style='background-color: {rec_color}20; padding: 20px; border-radius: 10px; text-align: center; border-left: 5px solid {rec_color};'>
                <h4 style='color: #000000; margin-bottom: 10px;'>🎯 Recommendations</h4>
                <h2 style='color: {rec_color}; margin: 0;'>{recommended_count}/{total_count}</h2>
                <p style='color: #000000; margin-top: 5px;'>Recommended Roles</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Candidate Summary Section
    if analysis.get('summary'):
        st.markdown("### 👤 Candidate Profile")
        with st.container():
            st.markdown(f"""
            <div style='background-color: #e3f2fd; padding: 15px; border-radius: 8px; border-left: 4px solid #2196f3;'>
                <p style='margin: 0; font-size: 16px; color: #000000;'>{analysis['summary']}</p>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("")
    
    # Overall Assessment
    if analysis.get('overall_summary'):
        st.markdown("### 📋 Overall Assessment")
        with st.container():
            st.markdown(f"""
            <div style='background-color: #fff3e0; padding: 15px; border-radius: 8px; border-left: 4px solid #ff9800;'>
                <p style='margin: 0; font-size: 16px; color: #000000;'><strong>{analysis['overall_summary']}</strong></p>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("")
    
    # Job Role Evaluations - Enhanced Cards
    if 'evaluations' in analysis and analysis['evaluations']:
        st.markdown("### 🎯 Job Role Analysis")
        
        for evaluation in analysis['evaluations']:
            for role, details in evaluation.items():
                status = details.get('status', 'unknown').lower()
                score = details.get('score', 0)
                
                # Determine colors based on status and score
                if status == 'recommended':
                    bg_color = "#d4edda"
                    border_color = "#28a745"
                    status_icon = "✅"
                    status_text = "RECOMMENDED"
                else:
                    bg_color = "#f8d7da"
                    border_color = "#dc3545"
                    status_icon = "❌"
                    status_text = "NOT RECOMMENDED"
                
                # Score color
                score_color = "#28a745" if score >= 70 else "#ffc107" if score >= 50 else "#dc3545"
                
                with st.container():
                    st.markdown(f"""
                    <div style='background-color: {bg_color}; padding: 20px; border-radius: 10px; border: 2px solid {border_color}; margin-bottom: 20px;'>
                        <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;'>
                            <h3 style='margin: 0; color: #000000;'>{status_icon} {role}</h3>
                            <div style='text-align: right;'>
                                <span style='background-color: {score_color}; color: white; padding: 8px 16px; border-radius: 20px; font-weight: bold;'>
                                    {score}/100
                                </span>
                                <br>
                                <small style='color: #000000; font-weight: bold;'>{status_text}</small>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Skills Analysis in columns
                col1, col2 = st.columns(2)
                
                with col1:
                    if details.get('matchedSkills'):
                        st.markdown("**✅ Matched Skills:**")
                        st.success(details['matchedSkills'])
                
                with col2:
                    if details.get('missing'):
                        st.markdown("**❌ Missing Skills:**")
                        st.error(details['missing'])
                
                # Assessment and Suggestions
                if details.get('summary'):
                    st.markdown("**📝 Assessment:**")
                    st.info(details['summary'])
                
                if details.get('suggest'):
                    st.markdown("**💡 Improvement Suggestions:**")
                    st.warning(details['suggest'])
                
                st.markdown("---")
    
    # Skills Analysis - Enhanced Table Format
    if 'skills' in analysis and analysis['skills']:
        st.markdown("### 🛠️ Skills Assessment")
        
        # Create skills dataframe
        skills_df = pd.DataFrame(analysis['skills'])
        skills_df['Proficiency'] = skills_df['score'].apply(
            lambda x: "Expert" if x >= 8 else "Advanced" if x >= 6 else "Intermediate" if x >= 4 else "Beginner"
        )
        skills_df['Progress'] = skills_df['score'] / 10
        
        # Display skills in a more visual way
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("#### Skills Proficiency Chart")
            st.bar_chart(skills_df.set_index('skill')['score'])
        
        with col2:
            st.markdown("#### Skills Summary")
            for _, skill_row in skills_df.iterrows():
                skill_name = skill_row['skill']
                skill_score = skill_row['score']
                proficiency = skill_row['Proficiency']
                
                # Color coding for skill levels
                if skill_score >= 8:
                    color = "#28a745"
                elif skill_score >= 6:
                    color = "#ffc107"
                elif skill_score >= 4:
                    color = "#17a2b8"
                else:
                    color = "#dc3545"
                
                st.markdown(f"""
                <div style='margin-bottom: 10px; padding: 12px; background-color: #ffffff; border-radius: 5px; border: 2px solid {color}; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                    <strong style='color: #000000; font-size: 14px;'>{skill_name}</strong><br>
                    <small style='color: #333333; font-size: 12px;'>{proficiency} ({skill_score}/10)</small>
                </div>
                """, unsafe_allow_html=True)
        
        # Skills table
        st.markdown("#### Detailed Skills Table")
        
        # Format the dataframe for better display
        display_df = skills_df.copy()
        display_df['Score'] = display_df['score'].apply(lambda x: f"{x}/10")
        display_df = display_df[['skill', 'Score', 'Proficiency']].rename(columns={'skill': 'Skill'})
        
        # Style the dataframe
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
    
    # Work Experience Summary (if available)
    if 'work_experience' in analysis and analysis['work_experience']:
        st.markdown("### 💼 Work Experience Summary")
        
        exp_data = []
        for exp in analysis['work_experience']:
            exp_data.append({
                'Company': exp.get('company', 'N/A'),
                'Position': exp.get('job_title', 'N/A'),
                'Duration': f"{exp.get('start_date', 'N/A')} - {exp.get('end_date', 'N/A')}",
                'Key Skills': ', '.join(exp.get('responsibilities', [])[:2]) + '...' if exp.get('responsibilities') else 'N/A'
            })
        
        if exp_data:
            exp_df = pd.DataFrame(exp_data)
            st.dataframe(exp_df, use_container_width=True, hide_index=True)
    
    # Education Summary (if available)
    if 'education' in analysis and analysis['education']:
        st.markdown("### 🎓 Education")
        
        for edu in analysis['education']:
            degree = edu.get('degree', 'N/A')
            college = edu.get('college', 'N/A')
            duration = f"{edu.get('start_year', 'N/A')} - {edu.get('end_year', 'N/A')}"
            
            st.markdown(f"""
            <div style='background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #6c757d;'>
                <h5 style='margin: 0; color: #000000;'>{degree}</h5>
                <p style='margin: 5px 0 0 0; color: #000000;'>{college} | {duration}</p>
            </div>
            """, unsafe_allow_html=True)


def show_auth_screen():
    """Show login/registration screen"""
    st.title("🔐 Resume Analyzer")
    st.write("Please login or register to continue")
    
    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        st.subheader("Login to your account")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_btn = st.form_submit_button("� Login", type="primary")
            
            if login_btn:
                if username and password:
                    with st.spinner("Logging in..."):
                        success, message = login_user(username, password)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                else:
                    st.error("Please enter both username and password")

    with tab2:
        st.subheader("Create a new account")
        with st.form("register_form"):
            reg_username = st.text_input("Choose Username")
            reg_email = st.text_input("Email Address")
            reg_password = st.text_input("Choose Password", type="password")
            reg_confirm = st.text_input("Confirm Password", type="password")
            register_btn = st.form_submit_button("📝 Register", type="primary")
            
            if register_btn:
                if reg_username and reg_email and reg_password and reg_confirm:
                    if reg_password == reg_confirm:
                        with st.spinner("Creating account..."):
                            success, message = register_user(reg_username, reg_password, reg_confirm, reg_email)
                            if success:
                                st.success(message)
                            else:
                                st.error(message)
                    else:
                        st.error("Passwords do not match")
                else:
                    st.error("Please fill in all fields")

def show_main_app():
    """Show main application screen"""
    # Header with user info and logout
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        st.write(f"👋 Welcome, **{st.session_state.username}**")
    with col3:
        if st.button("🚪 Logout", type="secondary"):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.current_analysis = None
            st.rerun()
    
    st.write('---')

    tab1, tab2 = st.tabs(["📤 Upload Resume", "🔍 Search by ID"])

    with tab1:
        st.header("Upload Resume for Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📄 Resume File")
            resume_file = st.file_uploader("Upload Resume (PDF)", type=['pdf'])
        
        with col2:
            st.subheader("📋 Job Description")
            job_desc_file = st.file_uploader("Upload Job Description (PDF)", type=['pdf'])

        threshold = st.slider("Recommendation Threshold", 0, 100, 70)
        st.info(f"Roles scoring {threshold}+ will be marked as recommended")

        if st.button("🚀 Analyze Resume", type="primary", disabled=not (resume_file and job_desc_file)):
            with st.spinner("Analyzing resume... Please wait"):
                success, result = upload_resume(resume_file, job_desc_file, threshold)
                if success:
                    st.success("✅ Analysis completed!")
                    st.session_state.current_analysis = result
                    
                    # Show results immediately
                    st.subheader("📊 Analysis Results")
                    display_analysis_results(result)
                else:
                    st.error(f"❌ Analysis failed: {result}")

    with tab2:
        st.header("Search Previous Analysis")
        
        file_id = st.text_input("Enter Analysis ID")

        if st.button("🔍 Search", type="primary", disabled=not file_id):
            with st.spinner("Fetching analysis... Please wait"):
                success, result = get_analysis_by_id(file_id)
                if success:
                    st.success("✅ Analysis found!")
                    st.session_state.current_analysis = result
                    
                    # Show results
                    st.subheader("📊 Analysis Results")
                    display_analysis_results(result)
                else:
                    st.error(f"❌ Fetch failed: {result}")


def main():
    """Main application function"""
    if not st.session_state.authenticated:
        show_auth_screen()
    else:
        #st.write(f"Welcome, {st.session_state.username}!")
        show_main_app()

if __name__ == "__main__":
    main()