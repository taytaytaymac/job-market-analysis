"""
Configuration for major VC firms and their portfolio pages
"""

VC_FIRMS = [
    {
        "name": "Sequoia",
        "portfolio_url": "https://www.sequoiacap.com/companies/",
        "company_selector": "div.company-card",
        "name_selector": "h3.company-name",
        "website_selector": "a.company-link"
    },
    {
        "name": "Andreessen Horowitz",
        "portfolio_url": "https://a16z.com/portfolio/",
        "company_selector": "div.portfolio-company",
        "name_selector": "h2.company-name",
        "website_selector": "a.website-link"
    },
    {
        "name": "Y Combinator",
        "portfolio_url": "https://www.ycombinator.com/companies/",
        "company_selector": "div.company",
        "name_selector": "div.company-name",
        "website_selector": "a.company-website"
    },
    {
        "name": "Accel",
        "portfolio_url": "https://www.accel.com/companies",
        "company_selector": "div.portfolio-company",
        "name_selector": "h3.company-title",
        "website_selector": "a.company-link"
    },
    {
        "name": "Benchmark",
        "portfolio_url": "https://www.benchmark.com/companies",
        "company_selector": "div.company-item",
        "name_selector": "h2.company-name",
        "website_selector": "a.company-url"
    },
    {
        "name": "Kleiner Perkins",
        "portfolio_url": "https://www.kleinerperkins.com/companies/",
        "company_selector": "div.company-card",
        "name_selector": "h3.company-name",
        "website_selector": "a.company-link"
    },
    {
        "name": "Greylock",
        "portfolio_url": "https://greylock.com/portfolio/",
        "company_selector": "div.portfolio-company",
        "name_selector": "h3.company-title",
        "website_selector": "a.website-link"
    },
    {
        "name": "First Round",
        "portfolio_url": "https://firstround.com/companies/",
        "company_selector": "div.company",
        "name_selector": "h2.company-name",
        "website_selector": "a.company-site"
    },
    # Additional top-tier VCs
    {
        "name": "Tiger Global",
        "portfolio_url": "https://www.tigerglobal.com/portfolio",
        "company_selector": "div.portfolio-item",
        "name_selector": "h3.company-title",
        "website_selector": "a.website"
    },
    {
        "name": "Lightspeed",
        "portfolio_url": "https://lsvp.com/portfolio/",
        "company_selector": "div.portfolio-company",
        "name_selector": "h3.company-name",
        "website_selector": "a.company-link"
    },
    {
        "name": "NEA",
        "portfolio_url": "https://www.nea.com/portfolio",
        "company_selector": "div.portfolio-item",
        "name_selector": "div.company-name",
        "website_selector": "a.website-link"
    },
    {
        "name": "Founders Fund",
        "portfolio_url": "https://foundersfund.com/portfolio",
        "company_selector": "div.portfolio-company",
        "name_selector": "h2.name",
        "website_selector": "a.website"
    },
    {
        "name": "Index Ventures",
        "portfolio_url": "https://www.indexventures.com/companies/",
        "company_selector": "div.company-card",
        "name_selector": "h3.company-name",
        "website_selector": "a.company-link"
    },
    {
        "name": "Bessemer",
        "portfolio_url": "https://www.bvp.com/companies",
        "company_selector": "div.company-item",
        "name_selector": "h3.company-name",
        "website_selector": "a.company-url"
    },
    {
        "name": "General Catalyst",
        "portfolio_url": "https://www.generalcatalyst.com/portfolio/",
        "company_selector": "div.portfolio-company",
        "name_selector": "h3.name",
        "website_selector": "a.website"
    },
    {
        "name": "Khosla Ventures",
        "portfolio_url": "https://www.khoslaventures.com/portfolio",
        "company_selector": "div.portfolio-item",
        "name_selector": "h3.company-name",
        "website_selector": "a.website-link"
    },
    {
        "name": "Battery Ventures",
        "portfolio_url": "https://www.battery.com/portfolio/",
        "company_selector": "div.company",
        "name_selector": "h3.name",
        "website_selector": "a.link"
    },
    {
        "name": "Insight Partners",
        "portfolio_url": "https://www.insightpartners.com/portfolio/",
        "company_selector": "div.portfolio-company",
        "name_selector": "h3.company-name",
        "website_selector": "a.website"
    },
    {
        "name": "Coatue",
        "portfolio_url": "https://www.coatue.com/portfolio",
        "company_selector": "div.portfolio-item",
        "name_selector": "h3.company-name",
        "website_selector": "a.website-link"
    },
    {
        "name": "Thrive Capital",
        "portfolio_url": "https://thrivecap.com/portfolio",
        "company_selector": "div.company",
        "name_selector": "div.name",
        "website_selector": "a.website"
    }
]

# Common paths to check for careers/jobs pages
CAREERS_PAGE_PATHS = [
    "/careers",
    "/jobs",
    "/work-with-us",
    "/join-us",
    "/company/careers",
    "/about/careers",
    "/about/jobs",
    "/opportunities",
    "/work-here",
    "/positions",
    "/job-openings"
]

# Common job board platforms used by startups
JOB_BOARD_PLATFORMS = {
    "greenhouse.io": {
        "job_selector": "div.opening",
        "title_selector": "a.opening-title",
        "location_selector": "span.location"
    },
    "lever.co": {
        "job_selector": "div.posting",
        "title_selector": "h5.posting-title",
        "location_selector": "span.location"
    },
    "workday.com": {
        "job_selector": "li.job-item",
        "title_selector": "a.job-title",
        "location_selector": "span.location"
    },
    "ashbyhq.com": {
        "job_selector": "div.job-posting",
        "title_selector": "div.job-title",
        "location_selector": "div.job-location"
    }
} 