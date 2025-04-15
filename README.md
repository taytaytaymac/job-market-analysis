# Job Market Analysis Dashboard

A comprehensive job market analysis tool that scrapes, stores, and visualizes job postings from various sources.

## Features

- Job scraping from multiple sources (LinkedIn, Indeed, etc.)
- Data storage and management
- Interactive dashboard with:
  - Job distribution by source
  - Salary analysis
  - Company hiring trends
  - Job posting patterns
- Export capabilities (Excel, HTML reports)

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/job-market-analysis.git
cd job-market-analysis
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize sample data:
```bash
python init_data.py
```

## Usage

### Dashboard
```bash
streamlit run run_visualizer.py -- --mode dashboard
```

### Generate Report
```bash
python run_visualizer.py --mode report --output job_report.html
```

### Export to Excel
```bash
python run_visualizer.py --mode excel --output jobs.xlsx
```

## Deployment

This project is deployed on Streamlit Cloud. You can access the live dashboard at:
[Your Streamlit Cloud URL]

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 