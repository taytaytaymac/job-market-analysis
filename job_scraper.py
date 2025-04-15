from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, Float, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timedelta
import time
from loguru import logger
import os
from dotenv import load_dotenv
import requests
import json
from urllib.parse import urljoin, quote
import schedule
import threading
from typing import List, Dict, Optional, Union
import re
from job_boards import DiceScraper, TechstarsScraper, BuiltInScraper, WelcomeToTheJungleScraper
from vc_firms import VC_FIRMS, CAREERS_PAGE_PATHS, JOB_BOARD_PLATFORMS
from difflib import SequenceMatcher
from thefuzz import fuzz
import itertools
import nltk
from nltk.corpus import wordnet
from nltk.tokenize import word_tokenize
from collections import defaultdict
from crunchbase_scraper import CrunchbaseScraper
from retry_requests import retry_session
from tenacity import retry, stop_after_attempt, wait_exponential
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# New imports for enhanced functionality
import pandas as pd
from fake_useragent import UserAgent
import aiohttp
import asyncio
from datetime import date

# Initialize user agent rotator
ua = UserAgent()

# Initialize retry session with exponential backoff
retry_session = retry_session(
    retries=3,
    backoff_factor=0.5,
    status_forcelist=[500, 502, 503, 504]
)

# Utility functions for enhanced scraping
async def fetch_page(url: str, session: aiohttp.ClientSession) -> str:
    """Fetch a page asynchronously with rotating user agents and retry logic"""
    headers = {'User-Agent': ua.random}
    try:
        async with session.get(url, headers=headers, timeout=30) as response:
            if response.status == 200:
                return await response.text()
            else:
                logger.warning(f"Non-200 status code {response.status} for {url}")
                return ""
    except asyncio.TimeoutError:
        logger.error(f"Timeout while fetching {url}")
        return ""
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        return ""

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def fetch_page_sync(url: str) -> str:
    """Synchronous version of fetch_page with retry logic"""
    headers = {'User-Agent': ua.random}
    try:
        response = retry_session.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.text
        else:
            logger.warning(f"Non-200 status code {response.status_code} for {url}")
            return ""
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        raise  # Re-raise to trigger retry

async def fetch_all_pages(urls: List[str]) -> List[str]:
    """Fetch multiple pages concurrently"""
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_page(url, session) for url in urls]
        return await asyncio.gather(*tasks)

def export_jobs_to_excel(jobs: List[Dict], filename: str = None) -> str:
    """Export jobs to Excel with formatting"""
    if not filename:
        filename = f"job_listings_{date.today().strftime('%Y%m%d')}.xlsx"
    
    df = pd.DataFrame(jobs)
    
    # Reorder and rename columns for better readability
    columns = {
        'title': 'Job Title',
        'company': 'Company',
        'location': 'Location',
        'salary': 'Salary Range',
        'experience_level': 'Experience Level',
        'job_type': 'Job Type',
        'remote': 'Remote',
        'url': 'Job URL',
        'date_posted': 'Date Posted',
        'skills': 'Required Skills'
    }
    
    df = df.reindex(columns=list(columns.keys()))
    df = df.rename(columns=columns)
    
    # Convert skills from JSON to readable format
    if 'skills' in df.columns:
        df['Required Skills'] = df['Required Skills'].apply(lambda x: ', '.join(x) if isinstance(x, list) else x)
    
    # Format datetime columns
    if 'Date Posted' in df.columns:
        df['Date Posted'] = pd.to_datetime(df['Date Posted']).dt.strftime('%Y-%m-%d')
    
    df.to_excel(filename, index=False, engine='openpyxl')
    return filename

# Load environment variables
load_dotenv()

# Database setup
Base = declarative_base()

class Company(Base):
    """Company information including Crunchbase data"""
    __tablename__ = 'companies'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200))
    website = Column(String(500))
    crunchbase_url = Column(String(500))
    linkedin_url = Column(String(500))
    description = Column(Text)
    
    # Company Size Information
    employee_count = Column(Integer)
    employee_range = Column(String(100))  # e.g., "1-10", "11-50", "51-200", etc.
    
    # Funding Information
    total_funding = Column(Float)  # in USD
    last_funding_amount = Column(Float)  # in USD
    last_funding_date = Column(DateTime)
    last_funding_type = Column(String(100))  # e.g., "Series A", "Seed", etc.
    last_funding_investors = Column(JSON)  # List of investors in the last round
    
    # Company Stage and Status
    company_stage = Column(String(100))  # e.g., "Seed", "Early Stage", "Late Stage", etc.
    operating_status = Column(String(100))  # e.g., "Active", "Acquired", "Closed", etc.
    founded_date = Column(DateTime)
    
    # Industry and Category
    industry = Column(String(200))
    sub_industry = Column(String(200))
    company_type = Column(String(100))  # e.g., "Private", "Public", "Subsidiary"
    
    # Location
    headquarters = Column(String(200))
    regions = Column(JSON)  # List of regions where the company operates
    
    # Tracking
    last_updated = Column(DateTime, default=datetime.utcnow)
    data_source = Column(String(100))  # e.g., "Crunchbase", "Manual", etc.

class JobPosting(Base):
    __tablename__ = 'job_postings'
    
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'))  # Link to Company table
    title = Column(String(200))
    company = Column(String(200))
    location = Column(String(200))
    description = Column(Text)
    salary = Column(String(100))
    salary_min = Column(Float)  # Parsed minimum salary
    salary_max = Column(Float)  # Parsed maximum salary
    salary_currency = Column(String(10))  # e.g., "USD", "EUR", etc.
    url = Column(String(500))
    source = Column(String(100))
    date_posted = Column(DateTime)
    date_scraped = Column(DateTime, default=datetime.utcnow)
    experience_level = Column(String(100))
    job_type = Column(String(100))
    remote = Column(Boolean)
    skills = Column(JSON)  # Changed from Text to JSON
    department = Column(String(100))  # e.g., "Engineering", "Product", "Sales"
    
    # Relationship
    company_info = relationship("Company", backref="job_postings")

class VCPortfolioCompany(Base):
    __tablename__ = 'vc_portfolio_companies'
    
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'))  # Link to Company table
    name = Column(String(200))
    website = Column(String(500))
    careers_page = Column(String(500))
    vc_firm = Column(String(200))
    investment_date = Column(DateTime)
    investment_amount = Column(Float)  # in USD
    investment_type = Column(String(100))
    ownership_percentage = Column(Float)
    last_scraped = Column(DateTime)
    
    # Relationship
    company_info = relationship("Company", backref="vc_investments")

class TitleMatcher:
    """Advanced title matching utility class"""
    
    COMMON_TITLE_VARIATIONS = {
        'senior': ['sr', 'sr.', 'senior', 'lead'],
        'junior': ['jr', 'jr.', 'junior', 'entry'],
        'engineer': ['engineer', 'developer', 'programmer', 'coder'],
        'architect': ['architect', 'architecture'],
        'manager': ['manager', 'mgr', 'management', 'head'],
        'developer': ['developer', 'engineer', 'programmer'],
        'lead': ['lead', 'leader', 'senior', 'principal'],
        'principal': ['principal', 'staff', 'senior staff', 'distinguished'],
        'frontend': ['frontend', 'front-end', 'front end', 'ui', 'client-side'],
        'backend': ['backend', 'back-end', 'back end', 'server-side'],
        'fullstack': ['fullstack', 'full-stack', 'full stack', 'end-to-end'],
    }
    
    TITLE_COMPONENTS = {
        'level': ['junior', 'senior', 'lead', 'principal', 'staff', 'director'],
        'role': ['engineer', 'developer', 'architect', 'manager', 'analyst'],
        'specialty': ['frontend', 'backend', 'fullstack', 'devops', 'cloud'],
        'technology': ['python', 'java', 'javascript', 'react', 'node']
    }

    def __init__(self):
        self.variation_cache = {}
        self.synonym_cache = {}
        self._build_component_patterns()

    def _build_component_patterns(self):
        """Build regex patterns for title components"""
        self.component_patterns = {}
        for component, terms in self.TITLE_COMPONENTS.items():
            pattern = r'\b(' + '|'.join(map(re.escape, terms)) + r')\b'
            self.component_patterns[component] = re.compile(pattern, re.I)

    def _get_synonyms(self, word):
        """Get synonyms for a word using WordNet"""
        if word in self.synonym_cache:
            return self.synonym_cache[word]

        synonyms = set()
        for syn in wordnet.synsets(word):
            for lemma in syn.lemmas():
                if '_' not in lemma.name():  # Exclude multi-word synonyms
                    synonyms.add(lemma.name().lower())
        
        # Add common variations
        if word.lower() in self.COMMON_TITLE_VARIATIONS:
            synonyms.update(self.COMMON_TITLE_VARIATIONS[word.lower()])
        
        self.synonym_cache[word] = synonyms
        return synonyms

    def _extract_components(self, title):
        """Extract different components from a job title"""
        components = defaultdict(list)
        words = word_tokenize(title.lower())
        
        for word in words:
            for component, pattern in self.component_patterns.items():
                if pattern.search(word):
                    components[component].append(word)
        
        return components

    def _calculate_component_similarity(self, title1_components, title2_components):
        """Calculate similarity based on title components"""
        total_score = 0
        weights = {'level': 0.3, 'role': 0.4, 'specialty': 0.2, 'technology': 0.1}
        
        for component, weight in weights.items():
            set1 = set(title1_components.get(component, []))
            set2 = set(title2_components.get(component, []))
            
            if set1 and set2:
                intersection = len(set1.intersection(set2))
                union = len(set1.union(set2))
                score = intersection / union if union > 0 else 0
                total_score += score * weight
        
        return total_score * 100

    def _calculate_variation_similarity(self, title1, title2):
        """Calculate similarity considering common variations"""
        words1 = set(word_tokenize(title1.lower()))
        words2 = set(word_tokenize(title2.lower()))
        
        max_variation_score = 0
        for word1 in words1:
            for word2 in words2:
                variations1 = self.COMMON_TITLE_VARIATIONS.get(word1, {word1})
                variations2 = self.COMMON_TITLE_VARIATIONS.get(word2, {word2})
                if variations1.intersection(variations2):
                    max_variation_score += 1
        
        return (max_variation_score / max(len(words1), len(words2))) * 100

    def calculate_similarity(self, title1: str, title2: str) -> float:
        """
        Calculate the similarity between two job titles using multiple techniques
        """
        # Basic fuzzy string matching
        ratio = fuzz.ratio(title1.lower(), title2.lower())
        partial_ratio = fuzz.partial_ratio(title1.lower(), title2.lower())
        token_sort_ratio = fuzz.token_sort_ratio(title1.lower(), title2.lower())
        token_set_ratio = fuzz.token_set_ratio(title1.lower(), title2.lower())
        
        # Component-based matching
        title1_components = self._extract_components(title1)
        title2_components = self._extract_components(title2)
        component_similarity = self._calculate_component_similarity(title1_components, title2_components)
        
        # Variation-based matching
        variation_similarity = self._calculate_variation_similarity(title1, title2)
        
        # Synonym-based matching
        words1 = word_tokenize(title1.lower())
        words2 = word_tokenize(title2.lower())
        
        synonym_matches = 0
        total_words = max(len(words1), len(words2))
        
        for word1 in words1:
            synonyms1 = self._get_synonyms(word1)
            for word2 in words2:
                synonyms2 = self._get_synonyms(word2)
                if synonyms1.intersection(synonyms2):
                    synonym_matches += 1
        
        synonym_similarity = (synonym_matches / total_words) * 100 if total_words > 0 else 0
        
        # Calculate weighted final score
        weights = {
            'fuzzy_ratio': 0.15,
            'partial_ratio': 0.15,
            'token_sort_ratio': 0.1,
            'token_set_ratio': 0.1,
            'component_similarity': 0.2,
            'variation_similarity': 0.15,
            'synonym_similarity': 0.15
        }
        
        final_score = (
            ratio * weights['fuzzy_ratio'] +
            partial_ratio * weights['partial_ratio'] +
            token_sort_ratio * weights['token_sort_ratio'] +
            token_set_ratio * weights['token_set_ratio'] +
            component_similarity * weights['component_similarity'] +
            variation_similarity * weights['variation_similarity'] +
            synonym_similarity * weights['synonym_similarity']
        )
        
        return final_score

class JobFilter:
    def __init__(self, keywords: List[str], locations: List[str], 
                 exclude_keywords: List[str] = None, 
                 min_salary: int = None,
                 job_types: List[str] = None,
                 experience_levels: List[str] = None):
        self.keywords = [k.lower() for k in keywords]
        self.locations = [l.lower() for l in locations]
        self.exclude_keywords = [k.lower() for k in (exclude_keywords or [])]
        self.min_salary = min_salary
        self.job_types = [t.lower() for t in (job_types or [])]
        self.experience_levels = [e.lower() for e in (experience_levels or [])]
        
        # Initialize fuzzy matcher
        self.fuzzy_matcher = FuzzyMatcher()
        
        # Compile regex patterns for faster matching
        self.keyword_patterns = [re.compile(r'\b' + re.escape(k) + r'\b', re.IGNORECASE) 
                               for k in keywords]
        self.exclude_patterns = [re.compile(r'\b' + re.escape(k) + r'\b', re.IGNORECASE) 
                               for k in (exclude_keywords or [])]
    
    def matches(self, job: Dict[str, Any]) -> bool:
        """Check if a job matches the filter criteria"""
        if not job:
            return False
            
        # Check title and description
        title = job.get('title', '').lower()
        description = job.get('description', '').lower()
        location = job.get('location', '').lower()
        
        # Check for excluded keywords
        if any(pattern.search(title) or pattern.search(description) 
               for pattern in self.exclude_patterns):
            return False
            
        # Check for required keywords
        if not any(pattern.search(title) or pattern.search(description) 
                  for pattern in self.keyword_patterns):
            return False
            
        # Check location
        if self.locations and not any(loc in location for loc in self.locations):
            return False
            
        # Check salary if specified
        if self.min_salary:
            salary = job.get('salary', 0)
            if isinstance(salary, str):
                # Extract numeric value from salary string
                salary = re.findall(r'\d+', salary)
                salary = int(salary[0]) if salary else 0
            if salary < self.min_salary:
                return False
                
        # Check job type if specified
        if self.job_types:
            job_type = job.get('job_type', '').lower()
            if not any(t in job_type for t in self.job_types):
                return False
                
        # Check experience level if specified
        if self.experience_levels:
            experience = job.get('experience', '').lower()
            if not any(e in experience for e in self.experience_levels):
                return False
                
        return True

class JobScraper:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.storage = JobStorage()
        self.filter = JobFilter(
            keywords=config.get('keywords', []),
            locations=config.get('locations', []),
            exclude_keywords=config.get('excluded_keywords', []),
            min_salary=config.get('min_salary'),
            job_types=config.get('job_types', []),
            experience_levels=config.get('experience_levels', [])
        )
        
    def scrape(self):
        """Main scraping method"""
        try:
            # Initialize scrapers based on config
            scrapers = []
            if self.config.get('use_linkedin'):
                scrapers.append(LinkedInScraper(self.config))
            if self.config.get('use_indeed'):
                scrapers.append(IndeedScraper(self.config))
                
            # Run scrapers in parallel
            with ThreadPoolExecutor(max_workers=len(scrapers)) as executor:
                futures = [executor.submit(scraper.scrape) for scraper in scrapers]
                for future in as_completed(futures):
                    jobs = future.result()
                    for job in jobs:
                        if self.filter.matches(job):
                            self.storage.save_job(job)
                            
            logger.info(f"Scraping completed. Total jobs: {self.storage.get_stats()['total_jobs']}")
            
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            
    def get_jobs(self, filter: JobFilter = None) -> List[Dict[str, Any]]:
        """Get jobs matching filter criteria"""
        return self.storage.get_jobs(filter)
        
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics"""
        return self.storage.get_stats()

class JobStorage:
    def __init__(self, storage_dir: str = 'data'):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.jobs_file = self.storage_dir / 'jobs.json'
        self.stats_file = self.storage_dir / 'stats.json'
        self._load_data()
        
    def _load_data(self):
        """Load existing data from storage"""
        try:
            if self.jobs_file.exists():
                with open(self.jobs_file, 'r') as f:
                    self.jobs = json.load(f)
            else:
                self.jobs = []
                
            if self.stats_file.exists():
                with open(self.stats_file, 'r') as f:
                    self.stats = json.load(f)
            else:
                self.stats = {
                    'total_jobs': 0,
                    'last_updated': None,
                    'sources': {},
                    'categories': {}
                }
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            self.jobs = []
            self.stats = {
                'total_jobs': 0,
                'last_updated': None,
                'sources': {},
                'categories': {}
            }
            
    def save_job(self, job: Dict[str, Any]) -> bool:
        """Save a job to storage"""
        try:
            # Validate job data
            if not self._validate_job(job):
                return False
                
            # Check for duplicates
            if not self._is_duplicate(job):
                self.jobs.append(job)
                self._update_stats(job)
                self._save_data()
                return True
            return False
        except Exception as e:
            logger.error(f"Error saving job: {e}")
            return False
            
    def _validate_job(self, job: Dict[str, Any]) -> bool:
        """Validate job data"""
        required_fields = ['title', 'company', 'location', 'url']
        return all(field in job for field in required_fields)
        
    def _is_duplicate(self, job: Dict[str, Any]) -> bool:
        """Check if job is a duplicate"""
        return any(
            j['url'] == job['url'] or 
            (j['title'] == job['title'] and j['company'] == job['company'])
            for j in self.jobs
        )
        
    def _update_stats(self, job: Dict[str, Any]):
        """Update statistics"""
        self.stats['total_jobs'] = len(self.jobs)
        self.stats['last_updated'] = datetime.now().isoformat()
        
        # Update source stats
        source = job.get('source', 'unknown')
        self.stats['sources'][source] = self.stats['sources'].get(source, 0) + 1
        
        # Update category stats
        category = job.get('category', 'unknown')
        self.stats['categories'][category] = self.stats['categories'].get(category, 0) + 1
        
    def _save_data(self):
        """Save all data to storage"""
        try:
            with open(self.jobs_file, 'w') as f:
                json.dump(self.jobs, f, indent=2)
            with open(self.stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving data: {e}")
            
    def get_jobs(self, filter: JobFilter = None) -> List[Dict[str, Any]]:
        """Get jobs matching filter criteria"""
        if filter:
            return [job for job in self.jobs if filter.matches(job)]
        return self.jobs
        
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics"""
        return self.stats

if __name__ == "__main__":
    # Example usage with enhanced fuzzy matching
    filters = JobFilter(
        min_salary=100000,
        remote=True,
        required_skills=['python', 'sql'],
        posted_within_days=7,
        
        # Basic title filtering
        title_includes=['senior', 'lead'],
        title_excludes=['junior', 'intern'],
        
        # Complex pattern matching
        title_patterns=[
            {
                'required_words': ['engineer', 'developer'],
                'position_level': ['senior', 'lead', 'staff', 'principal'],
                'technologies': ['python', 'java', 'golang'],
                'specialization': ['backend', 'frontend', 'fullstack']
            },
            {
                'required_words': ['architect'],
                'technologies': ['cloud', 'aws', 'azure'],
                'specialization': ['solutions', 'systems', 'enterprise']
            }
        ],
        
        # Position level matching
        position_levels=[
            'senior', 'lead', 'staff', 'principal', 'architect',
            'manager', 'director', 'head of', 'vp'
        ],
        
        # Technology stack matching
        technologies=[
            'python', 'java', 'javascript', 'typescript', 'golang',
            'react', 'angular', 'vue', 'node.js', 'django', 'flask',
            'aws', 'azure', 'gcp', 'kubernetes', 'docker'
        ],
        
        # Specialization matching
        specializations=[
            'backend', 'frontend', 'fullstack', 'devops', 'sre',
            'machine learning', 'data science', 'security', 'mobile'
        ],
        
        # Fuzzy matching with common variations
        fuzzy_title_matches=[
            "Senior Software Engineer",
            "Lead Backend Developer",
            "Principal Engineer",
            "Technical Architect",
            "Engineering Manager",
            "Staff Software Engineer",
            "Senior Full Stack Developer",
            "DevOps Engineer",
            "Machine Learning Engineer",
            "Data Scientist"
        ],
        fuzzy_threshold=80  # Minimum similarity score (0-100)
    )
    
    scraper = JobScraper(
        job_type="software engineer",
        location="San Francisco, CA",
        database_url="sqlite:///jobs.db",
        filters=filters
    )
    
    # Start scheduled scraping
    scraper.start_scheduled_scraping() 