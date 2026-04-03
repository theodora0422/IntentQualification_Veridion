import json

from src.candidate_generation import generate_candidates, print_candidates
from src.data_diagnostics import run
from src.file_loader import load_companies
from src.hard_filtering import filter_candidates_by_hard_constraints, print_filtered_candidates
from src.jsonl_normalize import normalize_companies
from src.query_parser import main_parse_query


def preview_companies(companies:list,n:int=3):
    #print first n normalized companies for debugging purposes
    max_items=min(n,len(companies))
    for i in range(max_items):
        company=companies[i]
        print(f"COMPANY {i+1}:")
        print(json.dumps(company.to_dict(), indent=2, ensure_ascii=False))

def preview_queries(queries:list[str]):
    for query in queries:
        parsed_query=main_parse_query(query)
        print(f"Raw Query: {query}")
        print(json.dumps(parsed_query.to_dict(),indent=2,ensure_ascii=False))


def main():
    companies_path="data/companies.jsonl"
    raw_companies=load_companies(companies_path)

    normalized_companies=normalize_companies(raw_companies)
    print(f"Normalized {len(normalized_companies)} companies")
    preview_companies(normalized_companies,n=3)

    #dataset diagnostics
    run(normalized_companies)

    test_queries=[
        "public software companies with more than 1000 employees in switzerland",
        "b2b saas companies providing hr solutions in europe",
        "fast-growing fintech companies competing with traditional banks in europe",
        "companies that could supply packaging materials for a cosmetics brand",
        "battery manufacturing companies in france",
    ]
    preview_queries(test_queries)

    for query in test_queries:
        parsed_query=main_parse_query(query)
        candidates=generate_candidates(parsed_query,normalized_companies)
        print_candidates(parsed_query,candidates)

        filtered_candidates=filter_candidates_by_hard_constraints(parsed_query,candidates)
        print_filtered_candidates(parsed_query,filtered_candidates)


if __name__ == "__main__":
    main()