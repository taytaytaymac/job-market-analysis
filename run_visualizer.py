import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import datetime
import time
from job_visualizer import JobVisualizer
from scraper_manager import ScraperManager

def main():
    st.set_page_config(
        page_title="Job Market Analysis",
        page_icon="📊",
        layout="wide"
    )
    
    # Initialize session state
    if 'visualizer' not in st.session_state:
        st.session_state.visualizer = JobVisualizer()
    if 'manager' not in st.session_state:
        st.session_state.manager = ScraperManager()
    
    # Sidebar for mode selection
    st.sidebar.title("Navigation")
    mode = st.sidebar.radio(
        "Select Mode",
        ["Dashboard", "Scraper Manager", "Reports"]
    )
    
    if mode == "Dashboard":
        show_dashboard()
    elif mode == "Scraper Manager":
        show_scraper_manager()
    else:
        show_reports()

def show_dashboard():
    st.title("Job Market Analysis Dashboard")
    
    # Get data from visualizer
    df = pd.DataFrame(st.session_state.visualizer.jobs)
    
    # Overview metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Jobs", len(df))
    with col2:
        st.metric("Unique Companies", df['company'].nunique())
    with col3:
        st.metric("Average Salary", f"${df['salary'].mean():,.0f}")
    
    # Filters
    st.sidebar.header("Filters")
    sources = st.sidebar.multiselect(
        "Select Sources",
        options=df['source'].unique(),
        default=df['source'].unique()
    )
    
    # Filter data
    df_filtered = df[df['source'].isin(sources)]
    
    # Job distribution by source
    st.subheader("Job Distribution by Source")
    fig = px.pie(
        df_filtered,
        names='source',
        title='Job Distribution by Source'
    )
    st.plotly_chart(fig)
    
    # Salary distribution
    st.subheader("Salary Distribution")
    fig = px.histogram(
        df_filtered,
        x='salary',
        nbins=30,
        title='Salary Distribution'
    )
    st.plotly_chart(fig)
    
    # Top companies
    st.subheader("Top Companies by Job Postings")
    top_companies = df_filtered['company'].value_counts().head(10)
    fig = px.bar(
        x=top_companies.index,
        y=top_companies.values,
        title='Top 10 Companies by Job Postings'
    )
    st.plotly_chart(fig)
    
    # Job posting trends
    st.subheader("Job Posting Trends")
    df_filtered['date_posted'] = pd.to_datetime(df_filtered['date_posted'])
    daily_postings = df_filtered.groupby('date_posted').size()
    fig = px.line(
        x=daily_postings.index,
        y=daily_postings.values,
        title='Daily Job Postings'
    )
    st.plotly_chart(fig)

def show_scraper_manager():
    st.title("Job Scraper Manager")
    
    # Control buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Start Scraping"):
            if st.session_state.manager.start_scraping():
                st.success("Scraping started successfully!")
            else:
                st.warning("Scraping is already running!")
    with col2:
        if st.button("Stop Scraping"):
            if st.session_state.manager.stop_scraping():
                st.success("Scraping stopped successfully!")
            else:
                st.warning("No scraping process is running!")
    
    # Status display
    st.header("Status")
    status = st.session_state.manager.get_status()
    if status == 'Running':
        st.info("🟢 Scraping is currently running")
    else:
        st.info("🔴 Scraping is stopped")
    
    # Progress information
    if st.session_state.manager.scraper:
        progress = st.session_state.manager.scraper.get_progress()
        
        # Progress metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Jobs Found", progress['jobs_found'])
        with col2:
            st.metric("Jobs Saved", progress['jobs_saved'])
        with col3:
            st.metric("Errors", progress['errors'])
        with col4:
            if progress.get('jobs_per_minute'):
                st.metric("Jobs/Minute", f"{progress['jobs_per_minute']:.1f}")
        
        # Progress bar
        if progress['total_pages'] > 0:
            progress_percent = (progress['current_page'] / progress['total_pages']) * 100
            st.progress(progress_percent / 100)
            st.text(f"Page {progress['current_page']} of {progress['total_pages']}")
        
        # Time information
        if progress.get('start_time'):
            elapsed = progress.get('elapsed_time', 0)
            remaining = progress.get('estimated_time_remaining', 0)
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Elapsed Time", f"{elapsed/60:.1f} minutes")
            with col2:
                if remaining > 0:
                    st.metric("Estimated Time Remaining", f"{remaining/60:.1f} minutes")
    
    # Configuration
    st.header("Configuration")
    
    # Keywords
    st.subheader("Keywords")
    keywords = st.text_area(
        "Enter keywords (one per line)",
        value='\n'.join(st.session_state.manager.config['keywords'])
    ).split('\n')
    
    # Locations
    st.subheader("Locations")
    locations = st.text_area(
        "Enter locations (one per line)",
        value='\n'.join(st.session_state.manager.config['locations'])
    ).split('\n')
    
    # Excluded Keywords
    st.subheader("Excluded Keywords")
    excluded_keywords = st.text_area(
        "Enter keywords to exclude (one per line)",
        value='\n'.join(st.session_state.manager.config['excluded_keywords'])
    ).split('\n')
    
    # Salary and Job Types
    col1, col2 = st.columns(2)
    with col1:
        min_salary = st.number_input(
            "Minimum Salary",
            value=st.session_state.manager.config['min_salary'],
            step=10000
        )
    with col2:
        job_types = st.multiselect(
            "Job Types",
            options=['Full-time', 'Part-time', 'Contract', 'Internship'],
            default=st.session_state.manager.config['job_types']
        )
    
    # Experience Levels
    experience_levels = st.multiselect(
        "Experience Levels",
        options=['Entry Level', 'Mid Level', 'Senior', 'Lead'],
        default=st.session_state.manager.config['experience_levels']
    )
    
    # Scraper Sources
    st.subheader("Scraper Sources")
    col1, col2 = st.columns(2)
    with col1:
        use_linkedin = st.checkbox(
            "Use LinkedIn",
            value=st.session_state.manager.config['use_linkedin']
        )
    with col2:
        use_indeed = st.checkbox(
            "Use Indeed",
            value=st.session_state.manager.config['use_indeed']
        )
    
    # Scraping Schedule
    st.subheader("Scraping Schedule")
    scrape_interval = st.number_input(
        "Scraping Interval (minutes)",
        value=st.session_state.manager.config['scrape_interval_minutes'],
        min_value=15,
        step=15
    )
    
    # Save Configuration
    if st.button("Save Configuration"):
        st.session_state.manager.config.update({
            'keywords': keywords,
            'locations': locations,
            'excluded_keywords': excluded_keywords,
            'min_salary': min_salary,
            'job_types': job_types,
            'experience_levels': experience_levels,
            'use_linkedin': use_linkedin,
            'use_indeed': use_indeed,
            'scrape_interval_minutes': scrape_interval
        })
        st.session_state.manager.save_config()
        st.success("Configuration saved successfully!")

def show_reports():
    st.title("Reports")
    
    # Export options
    st.header("Export Data")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Export to Excel"):
            filename = st.session_state.visualizer.export_to_excel()
            st.success(f"Data exported to {filename}")
    with col2:
        if st.button("Generate HTML Report"):
            filename = st.session_state.visualizer.create_report()
            st.success(f"Report generated: {filename}")
    
    # Report preview
    st.header("Report Preview")
    df = pd.DataFrame(st.session_state.visualizer.jobs)
    st.dataframe(df)

if __name__ == "__main__":
    main() 