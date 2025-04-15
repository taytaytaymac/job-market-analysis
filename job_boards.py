from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import quote
import time
from typing import List, Dict

class DiceScraper:
    @staticmethod
    def scrape(driver, job_type: str, location: str, page: int = 1) -> List[Dict]:
        """Scrape job postings from Dice"""
        jobs = []
        try:
            base_url = f"https://www.dice.com/jobs?q={quote(job_type)}&location={quote(location)}&page={page}"
            driver.get(base_url)
            
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "card-title"))
            )
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            job_cards = soup.find_all("div", class_="job-card")
            
            for card in job_cards:
                jobs.append({
                    "title": card.find("h5", class_="card-title").get_text(strip=True),
                    "company": card.find("div", class_="company-name").get_text(strip=True),
                    "location": card.find("span", class_="location").get_text(strip=True),
                    "description": card.find("div", class_="card-description").get_text(strip=True),
                    "url": "https://www.dice.com" + card.find("a")["href"],
                    "source": "Dice"
                })
            
        except Exception as e:
            print(f"Error scraping Dice: {str(e)}")
        
        return jobs

class TechstarsScraper:
    @staticmethod
    def scrape(driver, job_type: str, location: str) -> List[Dict]:
        """Scrape job postings from Techstars"""
        jobs = []
        try:
            base_url = "https://jobs.techstars.com/jobs"
            driver.get(base_url)
            
            # Input search criteria
            search_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "search-input"))
            )
            search_input.send_keys(job_type)
            
            time.sleep(2)  # Allow results to load
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            job_cards = soup.find_all("div", class_="job-card")
            
            for card in job_cards:
                location_text = card.find("div", class_="location").get_text(strip=True)
                if location.lower() in location_text.lower():
                    jobs.append({
                        "title": card.find("h3", class_="job-title").get_text(strip=True),
                        "company": card.find("div", class_="company-name").get_text(strip=True),
                        "location": location_text,
                        "url": card.find("a")["href"],
                        "source": "Techstars"
                    })
            
        except Exception as e:
            print(f"Error scraping Techstars: {str(e)}")
        
        return jobs

class BuiltInScraper:
    @staticmethod
    def scrape(driver, job_type: str, location: str, page: int = 1) -> List[Dict]:
        """Scrape job postings from BuiltIn"""
        jobs = []
        try:
            # Convert location to BuiltIn's format (e.g., "san-francisco" for San Francisco)
            builtin_location = location.lower().replace(" ", "-")
            base_url = f"https://{builtin_location}.builtin.com/jobs?search={quote(job_type)}&page={page}"
            driver.get(base_url)
            
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "job-item"))
            )
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            job_cards = soup.find_all("div", class_="job-item")
            
            for card in job_cards:
                jobs.append({
                    "title": card.find("h2", class_="job-title").get_text(strip=True),
                    "company": card.find("div", class_="company-name").get_text(strip=True),
                    "location": card.find("div", class_="job-location").get_text(strip=True),
                    "description": card.find("div", class_="job-description").get_text(strip=True),
                    "url": "https://{builtin_location}.builtin.com" + card.find("a")["href"],
                    "source": f"BuiltIn {location}"
                })
            
        except Exception as e:
            print(f"Error scraping BuiltIn: {str(e)}")
        
        return jobs

class WelcomeToTheJungleScraper:
    @staticmethod
    def scrape(driver, job_type: str, location: str, page: int = 1) -> List[Dict]:
        """Scrape job postings from Welcome to the Jungle"""
        jobs = []
        try:
            base_url = f"https://www.welcometothejungle.com/en/jobs?query={quote(job_type)}&page={page}"
            driver.get(base_url)
            
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "job-card"))
            )
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            job_cards = soup.find_all("div", class_="job-card")
            
            for card in job_cards:
                job_location = card.find("div", class_="location").get_text(strip=True)
                if location.lower() in job_location.lower():
                    jobs.append({
                        "title": card.find("h3", class_="job-title").get_text(strip=True),
                        "company": card.find("div", class_="company-name").get_text(strip=True),
                        "location": job_location,
                        "description": card.find("div", class_="job-description").get_text(strip=True),
                        "url": "https://www.welcometothejungle.com" + card.find("a")["href"],
                        "source": "Welcome to the Jungle"
                    })
            
        except Exception as e:
            print(f"Error scraping Welcome to the Jungle: {str(e)}")
        
        return jobs

# Add more job board scrapers as needed 