import json
import os
import re
import time

from src.candidate_generation import generate_candidates, print_candidates
from src.data_diagnostics import run
from src.file_loader import load_companies
from src.final_scoring import rerank_filtered_candidates, print_reranked_candidates
from src.hard_filtering import filter_candidates_by_hard_constraints, print_filtered_candidates
from src.jsonl_normalize import normalize_companies
from src.llm_reranker import should_use_llm, rerank_with_llm, print_llm_reranked_candidates
from src.genai_client import call_openai_llm_with_json_schema
from src.query_parser import main_parse_query

def ensure_output_dir(path:str):
    os.makedirs(path,exist_ok=True)
def normalize_file_name(text:str):
    text=text.lower().strip()
    text=re.sub(r"[^a-z0-9]+","_",text)
    text=re.sub(r"_+","_",text)
    return text.strip("_")
def write_text(path:str,content:str):
    with open(path,"w",encoding="utf-8") as f:
        f.write(content)
def serialize_candidates(candidates:list[tuple],top_k:int|None=None):
    lines=[]
    if top_k is None:
        items=candidates
    else:
        items=candidates[:top_k]
    for i,item in enumerate(items,start=1):
        company=item[0]
        candidate_score=item[1]
        lines.append(f"Rank {i}")
        lines.append(f"Name: {company.operational_name}")
        lines.append(f"Website: {company.website}")
        lines.append(f"Primary NAICS: {company.primary_naics_label}")
        lines.append(f"Candidate Score: {candidate_score}")
        lines.append("")
    if not lines:
        return "No candidates found.\n"
    return "\n".join(lines)
def serialize_filtered_candidates(filtered_candidates:list[tuple],top_k:int|None=None):
    lines=[]
    if top_k is None:
        items=filtered_candidates
    else:
        items=filtered_candidates[:top_k]
    for i,item in enumerate(items,start=1):
        company,candidate_score,evaluation=item
        lines.append(f"Rank {i}")
        lines.append(f"Name: {company.operational_name}")
        lines.append(f"Website: {company.website}")
        lines.append(f"Country: {company.country_code}")
        lines.append(f"Primary NAICS: {company.primary_naics_label}")
        lines.append(f"Employee Count: {company.employee_count}")
        lines.append(f"Revenue: {company.revenue}")
        lines.append(f"Year Founded: {company.year_founded}")
        lines.append(f"Is Public: {company.is_public}")
        lines.append(f"Candidate Score: {candidate_score}")
        lines.append(f"Passed All: {evaluation['passed_all']}")
        lines.append(f"Has Uncertainty: {evaluation['has_uncertainty']}")
        lines.append(f"Reasons: {evaluation['reasons']}")
        lines.append("")
    if not lines:
        return "No filtered candidates found.\n"
    return "\n".join(lines)
def serialize_reranked_candidates(reranked_candidates:list[tuple],top_k:int|None=None):
    lines=[]
    if top_k is None:
        items=reranked_candidates
    else:
        items=reranked_candidates[:top_k]
    for i,item in enumerate(items,start=1):
        company,candidate_score,final_score,evaluation,reasons=item
        lines.append(f"Rank {i}")
        lines.append(f"Name: {company.operational_name}")
        lines.append(f"Website: {company.website}")
        lines.append(f"Country: {company.country_code}")
        lines.append(f"Primary NAICS: {company.primary_naics_label}")
        lines.append(f"Employee Count: {company.employee_count}")
        lines.append(f"Revenue: {company.revenue}")
        lines.append(f"Year Founded: {company.year_founded}")
        lines.append(f"Is Public: {company.is_public}")
        lines.append(f"Candidate Score: {candidate_score}")
        lines.append(f"Final Score: {final_score}")
        lines.append(f"Has Uncertainty: {evaluation['has_uncertainty']}")
        lines.append(f"Reasons: {reasons}")
        lines.append("")
    if not lines:
        return "No reranked candidates found\n"
    return "\n".join(lines)
def serialize_llm_reranked_candidates(llm_candidates:list[tuple],top_k:int | None=None):
    lines=[]
    if top_k is None:
        items=llm_candidates
    else:
        items=llm_candidates[:top_k]
    for i,item in enumerate(items,start=1):
        company,candidate_score,final_score,llm_adjusted_score,evaluation,reasons,llm_result=item
        lines.append(f"Rank {i}")
        lines.append(f"Name: {company.operational_name}")
        lines.append(f"Website: {company.website}")
        lines.append(f"Country: {company.country_code}")
        lines.append(f"Primary NAICS: {company.primary_naics_label}")
        lines.append(f"Candidate Score: {candidate_score}")
        lines.append(f"Final Score Before LLM: {final_score}")
        lines.append(f"Final Score After LLM: {llm_adjusted_score}")
        lines.append(f"LLM Label: {llm_result['label']}")
        lines.append(f"LLM Score: {llm_result['llm_score']}")
        lines.append(f"LLM Explanation: {llm_result['explanation']}")
        lines.append(f"Has Uncertainty: {evaluation['has_uncertainty']}")
        lines.append(f"Reasons: {reasons}")
        lines.append("")
    if not lines:
        return "No LLM reranked candidates found\n"
    return "\n".join(lines)


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

    test_queries = [
        "Logistic companies in Romania",
        "Public software companies with more than 1,000 employees.",
        "Food and beverage manufacturers in France",
        "Companies that could supply packaging materials for a direct-to-consumer cosmetics brand",
        "Construction companies in the United States with revenue over $50 million",
        "Pharmaceutical companies in Switzerland",
        "B2B SaaS companies providing HR solutions in Europe",
        "Clean energy startups founded after 2018 with fewer than 200 employees",
        "Fast-growing fintech companies competing with traditional banks in Europe.",
        "E-commerce companies using Shopify or similar platforms",
        "Renewable energy equipment manufacturers in Scandinavia",
        "Companies that manufacture or supply critical components for electric vehicle battery production",
    ]
    preview_queries(test_queries)

    output_dir="outputs"
    ensure_output_dir(output_dir)

    for query in test_queries:
        parsed_query=main_parse_query(query)
        query_slug=normalize_file_name(query)
        query_dir=os.path.join(output_dir,query_slug)
        ensure_output_dir(query_dir)
        write_text(os.path.join(query_dir,"01_parsed_query.json"),json.dumps(parsed_query.to_dict(),indent=2,ensure_ascii=False))
        candidates=generate_candidates(parsed_query,normalized_companies,top_k=100)
        write_text(os.path.join(query_dir,"02_candidates.txt"),serialize_candidates(candidates,top_k=100))
        serialize_candidates(candidates,top_k=100)
        filtered_candidates=filter_candidates_by_hard_constraints(parsed_query,candidates)
        write_text(os.path.join(query_dir,"03_filtered_candidates.txt"),serialize_filtered_candidates(filtered_candidates,top_k=100))
        reranked_candidates=rerank_filtered_candidates(parsed_query,filtered_candidates)
        write_text(os.path.join(query_dir,"04_reranked_candidates.txt"),serialize_reranked_candidates(reranked_candidates,top_k=100))

        print(f"\n Query: {query}")
        print(f"candidates: {len(candidates)}")
        print(f"filtered_candidates: {len(filtered_candidates)}")
        print(f"reranked_candidates: {len(reranked_candidates)}")
        print_reranked_candidates(parsed_query,reranked_candidates)
        if should_use_llm(parsed_query,reranked_candidates):
            llm_candidates=rerank_with_llm(parsed_query,reranked_candidates,call_openai_llm_with_json_schema,3)
            write_text(os.path.join(query_dir,"05_llm_reranked_candidates.txt"),serialize_llm_reranked_candidates(llm_candidates,top_k=100))
            print_llm_reranked_candidates(parsed_query,llm_candidates,top_k=5)
        else:
            write_text(os.path.join(query_dir,"05_llm_reranked_candidates.txt"),"LLM reranking was skipped for this query\n")

if __name__ == "__main__":
    main()