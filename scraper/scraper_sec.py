import requests
import pandas as pd
import os
import time

# Constants
BASE_URL = "https://data.sec.gov/api/"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/"
XBRL_CONCEPT_URL = BASE_URL + "xbrl/companyconcept/"
XBRL_FACTS_URL = BASE_URL + "xbrl/companyfacts/"
HEADERS = {"User-Agent": "Santiago santiagomartinezc96@gmail.com"}

def get_cik_from_name(company_name):
    """Search for the CIK of a company based on its name. Skip if not found."""
    try:
        response = requests.get(f"https://www.sec.gov/edgar/search/company.json?q={company_name}", headers=HEADERS)
        response.raise_for_status()
        data = response.json()

        # Extract CIK if available
        if data['hits']['total']['value'] > 0:
            cik = data['hits']['hits'][0]['_source']['cik']
            return str(cik).zfill(10)  # Ensure CIK is 10 digits with leading zeros
        else:
            print(f"No CIK found for {company_name}")
            return None
    except requests.exceptions.HTTPError as e:
        print(f"Error fetching CIK for {company_name}: {e}")
        return None

def get_company_submissions(cik):
    """Retrieve the submission history of a company based on CIK"""
    url = f"{SUBMISSIONS_URL}CIK{cik}.json"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def get_company_facts(cik):
    """Retrieve all company facts data"""
    url = f"{XBRL_FACTS_URL}CIK{cik}.json"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def fetch_data_for_company(company_name):
    """Fetch and organize data for a company based on its name."""
    cik = get_cik_from_name(company_name)
    if not cik:
        return None  # Skip this company if no CIK found

    print(f"Fetching data for {company_name} (CIK: {cik})")
    try:
        submissions_data = get_company_submissions(cik)
        company_facts_data = get_company_facts(cik)
    except Exception as e:
        print(f"Error fetching data for CIK {cik}: {e}")
        return None

    company_data = []
    # Extract filing data
    for form in submissions_data['filings']['recent']['form']:
        filing = {
            "cik": cik,
            "company_name": company_name,
            "form_type": form,
            "date_filed": submissions_data['filings']['recent']['filingDate'][submissions_data['filings']['recent']['form'].index(form)],
            "report_period": submissions_data['filings']['recent']['reportDate'][submissions_data['filings']['recent']['form'].index(form)]
        }
        company_data.append(filing)

    # Extract financial facts data
    for fact_key, fact_value in company_facts_data['facts'].items():
        for concept_key, concept_value in fact_value.items():
            for fact in concept_value.get('units', {}).values():
                for fact_instance in fact:
                    financial_data = {
                        "cik": cik,
                        "company_name": company_name,
                        "taxonomy": fact_key,
                        "concept": concept_key,
                        "amount": fact_instance.get('val'),
                        "unit": fact_instance.get('uom'),
                        "end_date": fact_instance.get('end')
                    }
                    company_data.append(financial_data)
    
    return company_data

def save_to_csv(data, filename="recursive/sec/sec.csv"):
    """Save extracted data to a CSV file"""
    # Ensure the directory exists
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print(f"Data saved to {filename}")

# Company name list (replace with desired company names)
company_names = ["Apple Inc", "Microsoft Corp"]  # Example company names

# Main script
all_data = []
for name in company_names:
    company_data = fetch_data_for_company(name)
    if company_data:
        all_data.extend(company_data)
    time.sleep(1)  # Respectful delay to avoid overwhelming the API

# Save collected data to the specified path
save_to_csv(all_data)
