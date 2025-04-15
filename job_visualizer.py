import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import streamlit as st
from typing import List, Dict, Any
import json
from pathlib import Path

class JobVisualizer:
    def __init__(self, storage_dir: str = 'data'):
        self.storage_dir = Path(storage_dir)
        self.jobs_file = self.storage_dir / 'jobs.json'
        self.stats_file = self.storage_dir / 'stats.json'
        self._load_data()
        
    def _load_data(self):
        """Load job data from storage"""
        try:
            with open(self.jobs_file, 'r') as f:
                self.jobs = json.load(f)
            with open(self.stats_file, 'r') as f:
                self.stats = json.load(f)
        except Exception as e:
            print(f"Error loading data: {e}")
            self.jobs = []
            self.stats = {}
            
    def create_dashboard(self):
        """Create an interactive Streamlit dashboard"""
        st.title("Job Market Analysis Dashboard")
        
        # Convert jobs to DataFrame
        df = pd.DataFrame(self.jobs)
        
        # Sidebar filters
        st.sidebar.header("Filters")
        sources = st.sidebar.multiselect(
            "Select Sources",
            options=df['source'].unique(),
            default=df['source'].unique()
        )
        
        # Filter data
        df_filtered = df[df['source'].isin(sources)]
        
        # Overview metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Jobs", len(df_filtered))
        with col2:
            st.metric("Unique Companies", df_filtered['company'].nunique())
        with col3:
            st.metric("Average Salary", f"${df_filtered['salary'].mean():,.0f}")
            
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
        
    def create_report(self, output_file: str = 'job_report.html'):
        """Create a comprehensive HTML report"""
        df = pd.DataFrame(self.jobs)
        
        # Create the report
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Job Distribution by Source',
                'Salary Distribution',
                'Top Companies',
                'Job Posting Trends'
            )
        )
        
        # Add plots
        fig.add_trace(
            go.Pie(
                labels=df['source'].value_counts().index,
                values=df['source'].value_counts().values
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Histogram(x=df['salary']),
            row=1, col=2
        )
        
        top_companies = df['company'].value_counts().head(10)
        fig.add_trace(
            go.Bar(
                x=top_companies.index,
                y=top_companies.values
            ),
            row=2, col=1
        )
        
        df['date_posted'] = pd.to_datetime(df['date_posted'])
        daily_postings = df.groupby('date_posted').size()
        fig.add_trace(
            go.Scatter(
                x=daily_postings.index,
                y=daily_postings.values,
                mode='lines'
            ),
            row=2, col=2
        )
        
        # Update layout
        fig.update_layout(
            height=800,
            width=1200,
            title_text="Job Market Analysis Report",
            showlegend=True
        )
        
        # Save the report
        fig.write_html(output_file)
        return output_file
        
    def export_to_excel(self, output_file: str = 'jobs.xlsx'):
        """Export job data to Excel with formatting"""
        df = pd.DataFrame(self.jobs)
        
        # Create Excel writer
        writer = pd.ExcelWriter(output_file, engine='xlsxwriter')
        df.to_excel(writer, sheet_name='Jobs', index=False)
        
        # Get workbook and worksheet
        workbook = writer.book
        worksheet = writer.sheets['Jobs']
        
        # Add some formatting
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1
        })
        
        # Format the header
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            
        # Auto-adjust columns' width
        for idx, col in enumerate(df):
            series = df[col]
            max_len = max((
                series.astype(str).map(len).max(),
                len(str(series.name))
            )) + 1
            worksheet.set_column(idx, idx, max_len)
            
        writer.close()
        return output_file 