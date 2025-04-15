import json
from pathlib import Path
from datetime import datetime, timedelta
import random

def create_sample_data():
    # Create data directory
    data_dir = Path('data')
    data_dir.mkdir(exist_ok=True)
    
    # Sample job data
    jobs = []
    companies = ['Google', 'Microsoft', 'Apple', 'Amazon', 'Meta', 'Netflix', 'Tesla', 'SpaceX']
    sources = ['LinkedIn', 'Indeed', 'Company Website']
    locations = ['San Francisco', 'New York', 'Seattle', 'Austin', 'Remote']
    
    # Generate 100 sample jobs
    for i in range(100):
        company = random.choice(companies)
        job = {
            'title': f'Software Engineer {random.choice(["", "Senior", "Lead"])}',
            'company': company,
            'location': random.choice(locations),
            'salary': random.randint(80000, 250000),
            'source': random.choice(sources),
            'date_posted': (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
            'url': f'https://example.com/jobs/{i}',
            'description': f'Exciting opportunity at {company} for a software engineer position.'
        }
        jobs.append(job)
    
    # Save jobs to file
    with open(data_dir / 'jobs.json', 'w') as f:
        json.dump(jobs, f, indent=2)
    
    # Create stats
    stats = {
        'total_jobs': len(jobs),
        'last_updated': datetime.now().isoformat(),
        'sources': {source: sum(1 for job in jobs if job['source'] == source) for source in sources},
        'categories': {
            'Software Engineer': sum(1 for job in jobs if 'Software Engineer' in job['title']),
            'Senior Software Engineer': sum(1 for job in jobs if 'Senior Software Engineer' in job['title']),
            'Lead Software Engineer': sum(1 for job in jobs if 'Lead Software Engineer' in job['title'])
        }
    }
    
    # Save stats to file
    with open(data_dir / 'stats.json', 'w') as f:
        json.dump(stats, f, indent=2)
    
    print("Sample data created successfully!")

if __name__ == '__main__':
    create_sample_data() 