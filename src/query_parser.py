import re

from src.query_schema import QueryRepresentation

COUNTRY_ALIASES={
    "switzerland":"ch",
    "swiss":"ch",
    "france":"fr",
    "french":"fr",
    "germany":"de",
    "german":"de",
    "romania":"ro",
    "romanian":"ro",
    "united states":"us",
    "usa":"us",
    "us":"us",
    "china":"cn",
    "sweden":"se",
    "europe":"europe",
    "european":"europe",
}
INDUSTRY_KEYWORDS=[
    "software",
    "pharmaceutical",
    "pharma",
    "battery",
    "construction",
    "fintech",
    "logistics",
    "transportation",
    "energy",
    "automotive",
    "real estate",
    "manufacturing",
    "healthcare",
    "cosmetics",
    "retail",
]
BUSINESS_MODEL_KEYWORDS=[
    "b2b",
    "b2c",
    "business-to-business",
    "business-to-consumer",
    "saas",
    "enterprise",
    "retail",
    "wholesale",
    "manufacturer",
    "manufacturing",
    "service provider",
]
RELATIONAL_KEYWORDS=[
    "competing with",
    "compete with",
    "supplier",
    "suppliers",
    "supply",
    "supplying",
    "could supply",
    "using",
    "similar platforms",
    "components for",
    "for a",
    "for an",
]
VAGUE_KEYWORDS=[
    "fast-growing",
    "critical",
    "similar",
    "traditional",
    "clean",
    "innovative",
]
TARGET_MARKET_KEYWORDS=[
    "healthcare",
    "energy",
    "industrial",
    "transportation",
    "automotive",
    "cosmetics",
    "pharmaceuticals",
    "consumer goods",
    "agriculture",
    "real estate",
    "logistics",
]
CAPABILITY_KEYWORDS=[
    "packaging",
    "packaging materials",
    "bottle",
    "bottles",
    "container",
    "containers",
    "glass",
    "plastic",
    "paperboard",
    "mold",
]
def normalize_query_text(query:str):
    #lowercase and clean whitespace
    if query is None:
        return ""
    query=query.lower().strip()
    parts=query.split()
    clean_parts=[]
    for part in parts:
        clean_parts.append(part)
    clean_query=" ".join(clean_parts)
    return clean_query
def find_country_codes(normalized_query:str):
    #detect country codes and region terms
    country_codes=[]
    region_terms=[]
    for alias, code in COUNTRY_ALIASES.items():
        if alias in normalized_query:
            if code=="europe":
                if "europe" not in region_terms:
                    region_terms.append("europe")
            else:
                if code not in country_codes:
                    country_codes.append(code)
    return country_codes,region_terms
def find_keywords(normalized_query:str,keyword_list:list[str]):
    #return all keywords from keyword_list that appear in the query
    found_keywords=[]
    for keyword in keyword_list:
        if keyword in normalized_query:
            found_keywords.append(keyword)
    return found_keywords
def parse_public_status(normalized_query:str):
    #detect if the query asks for public companies
    if "public" in normalized_query:
        return True
    if "private" in normalized_query:
        return False
    return None
def parse_employee_constraints(normalized_query:str):
    min_employee_count=None
    max_employee_count=None
    min_match=re.search(r"(more than|over)\s+(\d+)\s+employees",normalized_query)
    if min_match is not None:
        min_employee_count=float(min_match.group(2))
    max_match=re.search(r"(less than|under)\s+(\d+)\s+employees",normalized_query)
    if max_match is not None:
        max_employee_count=float(max_match.group(2))
    return min_employee_count,max_employee_count
def parse_revenue_constraints(normalized_query:str):
    min_revenue=None
    max_revenue=None
    min_match=re.search(r"revenue\s+(more than|over)\s+(\d+)",normalized_query)
    if min_match is not None:
        min_revenue=float(min_match.group(2))
    max_match=re.search(r"revenue\s+(less than|under)\s+(\d+)",normalized_query)
    if max_match is not None:
        max_revenue=float(max_match.group(2))
    return min_revenue,max_revenue
def parse_year_constraints(normalized_query:str):
    min_year_founded=None
    max_year_founded=None
    after_match=re.search(r"founded after\s+(\d{4})",normalized_query)
    if after_match is not None:
        min_year_founded=float(after_match.group(1))
    before_match=re.search(r"founded before\s+(\d{4})",normalized_query)
    if before_match is not None:
        max_year_founded=float(before_match.group(1))
    return min_year_founded,max_year_founded
def classify_query(country_codes:list[str],region_terms:list[str],industry_terms:list[str],business_model_terms:list[str],
                   relational_terms:list[str],vague_terms:list[str],is_public,min_employee_count,max_employee_count,min_revenue,
                   max_revenue,min_year_founded,max_year_founded):
    #rule based query classification: strong-reasoning if strong relational or vague languages exists, mixed if both structured
    #and semantic signals exist and structured otherwise

    has_structured_signal=False
    has_semantic_signal=False
    has_reasoning_signal=False
    if len(country_codes)>0 or len(region_terms)>0:
        has_structured_signal=True
    if is_public is not None:
        has_structured_signal=True
    if min_employee_count is not None or max_employee_count is not None:
        has_structured_signal=True
    if min_revenue is not None or max_revenue is not None:
        has_structured_signal=True
    if min_year_founded is not None or max_year_founded is not None:
        has_structured_signal=True
    if len(industry_terms)>0 or len(business_model_terms)>0:
        has_semantic_signal=True
    if len(relational_terms)>0 or len(vague_terms)>0:
        has_reasoning_signal=True
    if has_reasoning_signal:
        return "strong-reasoning"
    if has_structured_signal and has_semantic_signal:
        return "mixed"
    return "structured"

def main_parse_query(query:str):
    normalized_query=normalize_query_text(query)
    country_codes,region_terms=find_country_codes(normalized_query)
    industry_terms=find_keywords(normalized_query,INDUSTRY_KEYWORDS)
    business_model_terms=find_keywords(normalized_query,BUSINESS_MODEL_KEYWORDS)
    target_market_terms=find_keywords(normalized_query,TARGET_MARKET_KEYWORDS)
    capability_terms=find_keywords(normalized_query,CAPABILITY_KEYWORDS)
    relational_terms=find_keywords(normalized_query,RELATIONAL_KEYWORDS)
    vague_terms=find_keywords(normalized_query,VAGUE_KEYWORDS)
    is_public=parse_public_status(normalized_query)
    min_employee_count,max_employee_count=parse_employee_constraints(normalized_query)
    min_revenue,max_revenue=parse_revenue_constraints(normalized_query)
    min_year_founded,max_year_founded=parse_year_constraints(normalized_query)
    query_type=classify_query(
        country_codes, region_terms, industry_terms, business_model_terms, relational_terms, vague_terms, is_public, min_employee_count, max_employee_count, min_revenue, max_revenue, min_year_founded, max_year_founded
    )
    query_representation=QueryRepresentation(
        query,normalized_query, query_type, country_codes, region_terms, industry_terms, business_model_terms, target_market_terms, capability_terms,relational_terms, vague_terms, is_public, min_employee_count, max_employee_count, min_revenue, max_revenue, min_year_founded, max_year_founded
    )
    return query_representation
