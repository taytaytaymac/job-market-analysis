import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
from typing import Dict, Optional
import time
from loguru import logger
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class CrunchbaseScraper:
    """Scraper for Crunchbase company information"""
    
    def __init__(self, driver):
        self.driver = driver
        self.base_url = "https://www.crunchbase.com"
        
    def find_company_url(self, company_name: str) -> Optional[str]:
        """Find the Crunchbase URL for a company"""
        try:
            search_url = f"{self.base_url}/search/organizations/field/organizations/name/{company_name}"
            self.driver.get(search_url)
            
            # Wait for search results
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "search-results"))
            )
            
            # Find the first matching result
            results = self.driver.find_elements(By.CSS_SELECTOR, ".search-result")
            if results:
                link = results[0].find_element(By.CSS_SELECTOR, "a")
                return link.get_attribute("href")
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding Crunchbase URL for {company_name}: {str(e)}")
            return None

    def scrape_company_info(self, url: str) -> Dict:
        """Scrape company information from Crunchbase"""
        try:
            self.driver.get(url)
            time.sleep(2)  # Allow dynamic content to load
            
            # Basic company info
            info = {
                'crunchbase_url': url,
                'name': self._get_text('.profile-name'),
                'description': self._get_text('.description'),
                'website': self._get_href('.website'),
                'linkedin_url': self._get_href('.linkedin'),
                'headquarters': self._get_text('.headquarters'),
                'company_type': self._get_text('.company-type'),
                'founded_date': self._parse_date(self._get_text('.founded-date')),
                'operating_status': self._get_text('.operating-status')
            }
            
            # Employee information
            employee_info = self._get_text('.employee-count')
            info.update(self._parse_employee_info(employee_info))
            
            # Funding information
            funding_info = self._scrape_funding_info()
            info.update(funding_info)
            
            # Industry and category
            info.update({
                'industry': self._get_text('.industry-category'),
                'sub_industry': self._get_text('.sub-industry')
            })
            
            # Regions
            regions = self.driver.find_elements(By.CSS_SELECTOR, '.regions .region')
            info['regions'] = [region.text for region in regions]
            
            return info
            
        except Exception as e:
            logger.error(f"Error scraping company info from {url}: {str(e)}")
            return {}

    def _get_text(self, selector: str) -> str:
        """Get text content from an element"""
        try:
            element = self.driver.find_element(By.CSS_SELECTOR, selector)
            return element.text.strip()
        except:
            return ""

    def _get_href(self, selector: str) -> str:
        """Get href attribute from an element"""
        try:
            element = self.driver.find_element(By.CSS_SELECTOR, selector)
            return element.get_attribute('href')
        except:
            return ""

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string into datetime object"""
        try:
            return datetime.strptime(date_str, '%B %d, %Y')
        except:
            return None

    def _parse_employee_info(self, employee_info: str) -> Dict:
        """Parse employee count information"""
        result = {
            'employee_count': None,
            'employee_range': None
        }
        
        if not employee_info:
            return result
            
        # Try to extract exact count
        count_match = re.search(r'(\d+)\s+employees?', employee_info)
        if count_match:
            result['employee_count'] = int(count_match.group(1))
            
        # Extract range
        range_match = re.search(r'(\d+[-–]\d+)', employee_info)
        if range_match:
            result['employee_range'] = range_match.group(1)
            
        return result

    def _scrape_funding_info(self) -> Dict:
        """Scrape funding information"""
        try:
            funding_info = {
                'total_funding': None,
                'last_funding_amount': None,
                'last_funding_date': None,
                'last_funding_type': None,
                'last_funding_investors': [],
                'company_stage': None
            }
            
            # Total funding
            total_funding_elem = self.driver.find_element(By.CSS_SELECTOR, '.total-funding')
            if total_funding_elem:
                funding_info['total_funding'] = self._parse_money(total_funding_elem.text)
            
            # Latest funding round
            latest_round = self.driver.find_element(By.CSS_SELECTOR, '.latest-round')
            if latest_round:
                funding_info.update({
                    'last_funding_amount': self._parse_money(self._get_text('.round-amount')),
                    'last_funding_date': self._parse_date(self._get_text('.round-date')),
                    'last_funding_type': self._get_text('.round-type')
                })
                
                # Investors in latest round
                investors = latest_round.find_elements(By.CSS_SELECTOR, '.investor')
                funding_info['last_funding_investors'] = [inv.text for inv in investors]
            
            # Company stage
            funding_info['company_stage'] = self._determine_company_stage(
                funding_info['last_funding_type'],
                funding_info['total_funding']
            )
            
            return funding_info
            
        except Exception as e:
            logger.error(f"Error scraping funding info: {str(e)}")
            return {}

    def _parse_money(self, money_str: str) -> Optional[float]:
        """Parse money string into float value"""
        try:
            # Remove currency symbols and convert to number
            amount = re.sub(r'[^\d.]', '', money_str)
            
            # Handle different scales
            multiplier = 1
            if 'K' in money_str:
                multiplier = 1000
            elif 'M' in money_str:
                multiplier = 1000000
            elif 'B' in money_str:
                multiplier = 1000000000
                
            return float(amount) * multiplier
        except:
            return None

    def _determine_company_stage(self, funding_type: str, total_funding: Optional[float]) -> str:
        """Determine company stage based on funding information"""
        if not funding_type and not total_funding:
            return "Unknown"
            
        if funding_type:
            funding_type = funding_type.lower()
            if 'seed' in funding_type:
                return "Seed Stage"
            elif 'series a' in funding_type:
                return "Early Stage"
            elif 'series b' in funding_type:
                return "Mid Stage"
            elif any(x in funding_type for x in ['series c', 'series d', 'series e']):
                return "Late Stage"
            elif 'ipo' in funding_type:
                return "Public"
                
        if total_funding:
            if total_funding < 1000000:
                return "Seed Stage"
            elif total_funding < 10000000:
                return "Early Stage"
            elif total_funding < 50000000:
                return "Mid Stage"
            else:
                return "Late Stage"
                
        return "Unknown" 