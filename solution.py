import json

from src.data_diagnostics import run
from src.file_loader import load_companies
from src.jsonl_normalize import normalize_companies


def preview_companies(companies:list,n:int=3):
    #print first n normalized companies for debugging purposes
    max_items=min(n,len(companies))
    for i in range(max_items):
        company=companies[i]
        print(f"COMPANY {i+1}:")
        print(json.dumps(company.to_dict(), indent=2, ensure_ascii=False))

def main():
    companies_path="data/companies.jsonl"
    raw_companies=load_companies(companies_path)

    normalized_companies=normalize_companies(raw_companies)
    print(f"Normalized {len(normalized_companies)} companies")
    preview_companies(normalized_companies,n=3)

    #dataset diagnostics
    run(normalized_companies)

if __name__ == "__main__":
    main()