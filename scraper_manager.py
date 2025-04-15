import streamlit as st
import json
from pathlib import Path
from datetime import datetime
import time
from job_scraper import JobScraper, JobFilter
import threading
import queue
import plotly.express as px
from fuzzywuzzy import fuzz
from typing import List, Dict, Any

class FuzzyMatcher:
    """Helper class for fuzzy string matching"""
    def __init__(self, threshold: int = 80):
        self.threshold = threshold
        
    def match(self, text: str, patterns: List[str]) -> bool:
        """Check if text matches any pattern with fuzzy matching"""
        for pattern in patterns:
            if fuzz.ratio(text.lower(), pattern.lower()) >= self.threshold:
                return True
        return False
        
    def best_match(self, text: str, patterns: List[str]) -> str:
        """Return the best matching pattern"""
        best_score = 0
        best_match = ""
        for pattern in patterns:
            score = fuzz.ratio(text.lower(), pattern.lower())
            if score > best_score:
                best_score = score
                best_match = pattern
        return best_match if best_score >= self.threshold else ""

class ScraperManager:
    def __init__(self):
        self.config_file = Path('config.json')
        self.load_config()
        self.scraper = None
        self.scraping_thread = None
        self.scraping_queue = queue.Queue()
        self.fuzzy_matcher = FuzzyMatcher()
        
        # Define all available options
        self.available_job_types = [
            'Full-time', 'Part-time', 'Contract', 'Internship',
            'Temporary', 'Volunteer', 'Other'
        ]
        
        self.available_experience_levels = [
            'Entry Level', 'Mid Level', 'Senior', 'Lead',
            'Manager', 'Director', 'Executive'
        ]
        
        self.available_industries = [
            'Technology', 'Finance', 'Healthcare', 'Education',
            'Manufacturing', 'Retail', 'Government', 'Non-profit',
            'Other'
        ]
        
        self.available_remote_options = [
            'Remote', 'Hybrid', 'On-site', 'Flexible'
        ]
        
        self.available_salary_ranges = [
            '0-50000', '50000-100000', '100000-150000',
            '150000-200000', '200000+'
        ]
        
        self.available_education_levels = [
            'High School', 'Associate', 'Bachelor', 'Master',
            'PhD', 'None Required'
        ]
        
        self.available_skills = [
            'Python', 'Java', 'JavaScript', 'SQL', 'AWS',
            'Docker', 'Kubernetes', 'React', 'Node.js',
            'Machine Learning', 'Data Science', 'DevOps'
        ]
        
        # VC-specific options
        self.available_vc_stages = [
            'Pre-seed', 'Seed', 'Series A', 'Series B',
            'Series C', 'Series D+', 'Growth', 'Late Stage'
        ]
        
        self.available_vc_focus_areas = [
            'Enterprise', 'Consumer', 'FinTech', 'HealthTech',
            'EdTech', 'AI/ML', 'SaaS', 'Marketplace',
            'Infrastructure', 'Security', 'Blockchain'
        ]
        
        self.available_vc_fund_sizes = [
            'Micro (<$10M)', 'Small ($10M-$50M)', 'Medium ($50M-$200M)',
            'Large ($200M-$1B)', 'Mega (>$1B)'
        ]
        
        self.available_vc_roles = [
            'Investment Analyst', 'Associate', 'Senior Associate',
            'Principal', 'Venture Partner', 'Partner',
            'General Partner', 'Managing Partner'
        ]
        
        # Example VC companies for each category
        self.vc_examples = {
            'Pre-seed': ['Y Combinator', '500 Startups', 'Techstars'],
            'Seed': ['Sequoia Capital', 'Andreessen Horowitz', 'Accel'],
            'Series A': ['Bessemer Venture Partners', 'Index Ventures', 'Greylock'],
            'Series B': ['Tiger Global', 'Coatue', 'Insight Partners'],
            'Series C+': ['SoftBank Vision Fund', 'Temasek', 'General Atlantic'],
            'Enterprise': ['Sequoia Capital', 'Bessemer', 'Insight Partners'],
            'Consumer': ['Andreessen Horowitz', 'Index Ventures', 'First Round'],
            'FinTech': ['Ribbit Capital', 'QED Investors', 'Fin Capital'],
            'HealthTech': ['Venrock', 'OrbiMed', 'RA Capital'],
            'EdTech': ['Reach Capital', 'GSV Ventures', 'Learn Capital'],
            'AI/ML': ['Data Collective', 'Two Sigma Ventures', 'AI Fund'],
            'SaaS': ['Bessemer', 'Sapphire Ventures', 'Insight Partners'],
            'Marketplace': ['Andreessen Horowitz', 'Index Ventures', 'First Round'],
            'Infrastructure': ['Sequoia Capital', 'Bessemer', 'Insight Partners'],
            'Security': ['ForgePoint Capital', 'AllegisCyber', 'TenEleven Ventures'],
            'Blockchain': ['Paradigm', 'Polychain Capital', 'Pantera Capital']
        }
        
    def load_config(self):
        """Load or create default configuration"""
        if not self.config_file.exists():
            self.config = {
                'keywords': ['software engineer', 'developer'],
                'locations': ['San Francisco', 'Remote'],
                'excluded_keywords': ['senior', 'lead'],
                'min_salary': 100000,
                'max_salary': None,
                'job_types': ['Full-time'],
                'experience_levels': ['Entry Level', 'Mid Level'],
                'industries': [],
                'remote_options': ['Remote', 'Hybrid'],
                'education_levels': [],
                'required_skills': [],
                'use_linkedin': True,
                'use_indeed': True,
                'use_dice': True,
                'use_glassdoor': True,
                'use_monster': True,
                'scrape_interval_minutes': 60,
                'max_jobs_per_search': 100,
                'date_posted': 'Any time',
                'sort_by': 'relevance',
                # VC-specific config
                'vc_stages': [],
                'vc_focus_areas': [],
                'vc_fund_sizes': [],
                'vc_roles': [],
                'vc_keywords': ['venture capital', 'vc', 'startup', 'fund'],
                'exclude_non_vc': True
            }
            self.save_config()
        else:
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
                
    def save_config(self):
        """Save current configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
            
    def start_scraping(self):
        """Start the scraping process in a separate thread"""
        if self.scraping_thread is None or not self.scraping_thread.is_alive():
            self.scraper = JobScraper(self.config)
            self.scraping_thread = threading.Thread(target=self._run_scraping)
            self.scraping_thread.daemon = True
            self.scraping_thread.start()
            return True
        return False
        
    def stop_scraping(self):
        """Stop the scraping process"""
        if self.scraper and self.scraping_thread and self.scraping_thread.is_alive():
            self.scraper.stop()
            self.scraping_thread.join(timeout=5)
            return True
        return False
        
    def _run_scraping(self):
        """Run the scraping process and update status"""
        try:
            self.scraper.scrape()
            self.scraping_queue.put(('success', 'Scraping completed successfully'))
        except Exception as e:
            self.scraping_queue.put(('error', str(e)))
            
    def get_status(self):
        """Get current scraping status"""
        if self.scraping_thread and self.scraping_thread.is_alive():
            return 'Running'
        return 'Stopped'
        
    def run_ui(self):
        """Run the Streamlit UI"""
        st.title("Job Scraper Manager")
        
        # Configuration Section
        st.header("Configuration")
        
        # Basic Search Parameters
        st.subheader("Basic Search Parameters")
        col1, col2 = st.columns(2)
        
        with col1:
            self.config['keywords'] = st.text_area(
                "Keywords (one per line)",
                value='\n'.join(self.config['keywords']),
                help="Enter job titles, skills, or other keywords to search for"
            ).split('\n')
            
            self.config['locations'] = st.text_area(
                "Locations (one per line)",
                value='\n'.join(self.config['locations']),
                help="Enter cities, states, or countries to search in"
            ).split('\n')
            
            self.config['excluded_keywords'] = st.text_area(
                "Excluded Keywords (one per line)",
                value='\n'.join(self.config['excluded_keywords']),
                help="Enter keywords to exclude from results"
            ).split('\n')
            
        with col2:
            col1, col2 = st.columns(2)
            with col1:
                self.config['min_salary'] = st.number_input(
                    "Minimum Salary",
                    value=self.config['min_salary'],
                    step=10000,
                    help="Minimum annual salary in USD"
                )
            with col2:
                self.config['max_salary'] = st.number_input(
                    "Maximum Salary",
                    value=self.config.get('max_salary', None),
                    step=10000,
                    help="Maximum annual salary in USD"
                )
            
            self.config['job_types'] = st.multiselect(
                "Job Types",
                options=self.available_job_types,
                default=self.config['job_types'],
                help="Select the types of employment"
            )
            
            self.config['experience_levels'] = st.multiselect(
                "Experience Levels",
                options=self.available_experience_levels,
                default=self.config['experience_levels'],
                help="Select the experience levels to include"
            )
        
        # VC Company Filters
        st.subheader("VC Company Filters")
        col1, col2 = st.columns(2)
        
        with col1:
            self.config['vc_stages'] = st.multiselect(
                "Investment Stages",
                options=self.available_vc_stages,
                default=self.config.get('vc_stages', []),
                help="Select the investment stages of interest"
            )
            
            self.config['vc_focus_areas'] = st.multiselect(
                "Focus Areas",
                options=self.available_vc_focus_areas,
                default=self.config.get('vc_focus_areas', []),
                help="Select the industries or sectors of focus"
            )
            
            self.config['vc_roles'] = st.multiselect(
                "VC Roles",
                options=self.available_vc_roles,
                default=self.config.get('vc_roles', []),
                help="Select specific VC roles to target"
            )
            
        with col2:
            self.config['vc_fund_sizes'] = st.multiselect(
                "Fund Sizes",
                options=self.available_vc_fund_sizes,
                default=self.config.get('vc_fund_sizes', []),
                help="Select the fund sizes of interest"
            )
            
            self.config['vc_keywords'] = st.text_area(
                "VC Keywords (one per line)",
                value='\n'.join(self.config.get('vc_keywords', [])),
                help="Additional keywords to identify VC companies"
            ).split('\n')
            
            self.config['exclude_non_vc'] = st.checkbox(
                "Exclude Non-VC Companies",
                value=self.config.get('exclude_non_vc', True),
                help="Filter out companies that are not VC-backed or VC firms"
            )
        
        # Advanced Filters
        st.subheader("Advanced Filters")
        col1, col2 = st.columns(2)
        
        with col1:
            self.config['industries'] = st.multiselect(
                "Industries",
                options=self.available_industries,
                default=self.config.get('industries', []),
                help="Select specific industries to focus on"
            )
            
            self.config['remote_options'] = st.multiselect(
                "Remote Options",
                options=self.available_remote_options,
                default=self.config.get('remote_options', []),
                help="Select preferred work location types"
            )
            
            self.config['education_levels'] = st.multiselect(
                "Education Levels",
                options=self.available_education_levels,
                default=self.config.get('education_levels', []),
                help="Select required education levels"
            )
            
        with col2:
            self.config['required_skills'] = st.multiselect(
                "Required Skills",
                options=self.available_skills,
                default=self.config.get('required_skills', []),
                help="Select skills that should be required"
            )
            
            self.config['date_posted'] = st.selectbox(
                "Date Posted",
                options=['Any time', '24 hours', '3 days', '7 days', '30 days'],
                index=['Any time', '24 hours', '3 days', '7 days', '30 days'].index(
                    self.config.get('date_posted', 'Any time')
                ),
                help="Filter by when the job was posted"
            )
            
            self.config['sort_by'] = st.selectbox(
                "Sort By",
                options=['relevance', 'date', 'salary'],
                index=['relevance', 'date', 'salary'].index(
                    self.config.get('sort_by', 'relevance')
                ),
                help="How to sort the results"
            )
        
        # Scraper Sources
        st.subheader("Scraper Sources")
        col1, col2 = st.columns(2)
        with col1:
            self.config['use_linkedin'] = st.checkbox(
                "Use LinkedIn",
                value=self.config['use_linkedin'],
                help="Include LinkedIn in the search"
            )
            self.config['use_indeed'] = st.checkbox(
                "Use Indeed",
                value=self.config['use_indeed'],
                help="Include Indeed in the search"
            )
        with col2:
            self.config['use_dice'] = st.checkbox(
                "Use Dice",
                value=self.config.get('use_dice', True),
                help="Include Dice in the search"
            )
            self.config['use_glassdoor'] = st.checkbox(
                "Use Glassdoor",
                value=self.config.get('use_glassdoor', True),
                help="Include Glassdoor in the search"
            )
        
        # Scraping Settings
        st.subheader("Scraping Settings")
        col1, col2 = st.columns(2)
        with col1:
            self.config['scrape_interval_minutes'] = st.number_input(
                "Scraping Interval (minutes)",
                value=self.config['scrape_interval_minutes'],
                min_value=15,
                step=15,
                help="How often to run the scraper"
            )
        with col2:
            self.config['max_jobs_per_search'] = st.number_input(
                "Maximum Jobs per Search",
                value=self.config.get('max_jobs_per_search', 100),
                min_value=10,
                step=10,
                help="Maximum number of jobs to collect per search"
            )
        
        # Save Configuration
        if st.button("Save Configuration"):
            self.save_config()
            st.success("Configuration saved successfully!")
            
        # Scraping Controls
        st.header("Scraping Controls")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Start Scraping"):
                if self.start_scraping():
                    st.success("Scraping started successfully!")
                else:
                    st.warning("Scraping is already running!")
                    
        with col2:
            if st.button("Stop Scraping"):
                if self.stop_scraping():
                    st.success("Scraping stopped successfully!")
                else:
                    st.warning("No scraping process is running!")
                    
        # Status Display
        st.header("Status")
        status = self.get_status()
        if status == 'Running':
            st.info("🟢 Scraping is currently running")
        else:
            st.info("🔴 Scraping is stopped")
            
        # Display any messages from the scraping process
        try:
            while not self.scraping_queue.empty():
                msg_type, message = self.scraping_queue.get_nowait()
                if msg_type == 'success':
                    st.success(message)
                else:
                    st.error(message)
        except queue.Empty:
            pass
            
        # Statistics
        st.header("Statistics")
        if self.scraper:
            stats = self.scraper.get_stats()
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Jobs", stats.get('total_jobs', 0))
            with col2:
                st.metric("Last Updated", stats.get('last_updated', 'Never'))
            with col3:
                st.metric("Sources", len(stats.get('sources', {})))
                
        # Job Sources Distribution
        if self.scraper and stats.get('sources'):
            st.subheader("Job Distribution by Source")
            sources = stats['sources']
            fig = px.pie(
                values=list(sources.values()),
                names=list(sources.keys()),
                title='Job Distribution by Source'
            )
            st.plotly_chart(fig)

if __name__ == '__main__':
    manager = ScraperManager()
    manager.run_ui() 