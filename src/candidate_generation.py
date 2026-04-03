from src.company_schema import CompanyProfile
from src.query_schema import QueryRepresentation


def normalize_text_for_match(value:str|None):
    #lowercase and remove extra spaces
    if value is None:
        return ""
    value=value.lower().strip()
    parts=value.split()
    clean_parts=[]
    for part in parts:
        clean_parts.append(part)
    return " ".join(clean_parts)

def text_contains_term(text:str,term:str):
    #check if a normalized text contains a normalized term
    normalized_text=normalize_text_for_match(text)
    normalized_term=normalize_text_for_match(term)
    if normalized_term=="":
        return False
    return normalized_term in normalized_text
def company_matches_term(company:CompanyProfile,term:str):
    if text_contains_term(company.primary_naics_label,term):
        return True
    if text_contains_term(company.description,term):
        return True
    if text_contains_term(company.full_profile,term):
        return True
    if count_matches_in_list(company.business_model,[term])>0:
        return True
    if count_matches_in_list(company.target_markets,[term])>0:
        return True
    if count_matches_in_list(company.core_offerings,[term])>0:
        return True
    return False
def get_required_terms_for_candidate_generation(query:QueryRepresentation):
    #return the most important semantic terms for candidate generation
    required_terms=[]
    generic_terms={
        "manufacturing",
        "retail",
        "enterprise",
        "service provider",
        "wholesale",
        "cosmetics",
    }
    for term in query.industry_terms:
        if term not in generic_terms:
            if term not in required_terms:
                required_terms.append(term)
    if "packaging" in query.normalized_query:
        if "packaging" not in required_terms:
            required_terms.append("packaging")
    return required_terms
def matches_any_required_term(query:QueryRepresentation,company:CompanyProfile):
    required_terms=get_required_terms_for_candidate_generation(query)
    if len(required_terms)==0:
        return True
    for term in required_terms:
        if company_matches_term(company,term):
            return True
    return False
def count_matches_in_list(values:list[str],query_terms:list[str]):
    #count how many query terms appear in a list of company values
    match_count=0
    for query_term in query_terms:
        found=False
        for value in values:
            if text_contains_term(value,query_term):
                found=True
                break
        if found:
            match_count=match_count+1
    return match_count
def count_matches_in_text(text:str,query_terms:list[str]):
    #how many query terms appear inside one text field
    match_count=0
    for query_term in query_terms:
        if text_contains_term(text,query_term):
            match_count=match_count+1
    return match_count
def score_geography(query:QueryRepresentation,company:CompanyProfile):
    #reward country match, later can be expanded on regions
    score=0.0
    if len(query.country_codes)>0:
        if company.country_code in query.country_codes:
            score=score+3.0
        else:
            #if a query explicitly asks for a specific country and company is elsewhere, I strongly penalize it already at candidate stage
            score=score-2.0
    if len(query.region_terms)>0:
        #for now, region handling stauc lightweight, later i can map countries to regions
        if "europe" in query.region_terms:
            if company.country_code is not None:
                score=score+0.5
    return score
def score_industry(query:QueryRepresentation,company:CompanyProfile):
    #industry score basen on primary NAICS label, description, full profile
    score=0.0
    for industry_term in query.industry_terms:
        matched=False
        if company.primary_naics_label is not None:
            if text_contains_term(company.primary_naics_label,industry_term):
                score=score+3.0
                matched=True
        if not matched and company.description is not None:
            if text_contains_term(company.description,industry_term):
                score=score+1.5
                matched=True
        if not matched and company.full_profile is not None:
            if text_contains_term(company.full_profile,industry_term):
                score=score+1.0
    return score
def score_business_model(query:QueryRepresentation,company:CompanyProfile):
    score=0.0
    match_count=count_matches_in_list(company.business_model,query.business_model_terms)
    score=score+(match_count*2.0)
    return score
def score_target_markets(query:QueryRepresentation,company:CompanyProfile):
    score=0.0
    match_count=count_matches_in_list(company.target_markets,query.target_market_terms)
    score=score+(match_count*2.0)
    return score
def score_core_offerings(query:QueryRepresentation,company:CompanyProfile):
    score=0.0
    all_query_terms=[]
    all_query_terms.extend(query.industry_terms)
    all_query_terms.extend(query.business_model_terms)
    all_query_terms.extend(query.target_market_terms)
    all_query_terms.extend(query.relational_terms)
    match_count=count_matches_in_list(company.core_offerings,all_query_terms)
    score=score+(match_count*1.5)
    return score
def score_full_text_overlap(query:QueryRepresentation,company:CompanyProfile):
    score=0.0
    all_query_terms=[]
    all_query_terms.extend(query.industry_terms)
    all_query_terms.extend(query.business_model_terms)
    all_query_terms.extend(query.target_market_terms)
    all_query_terms.extend(query.relational_terms)
    all_query_terms.extend(query.vague_terms)
    match_count=count_matches_in_text(company.full_profile,all_query_terms)
    score=score+(match_count*0.75)
    return score
def score_public_status(query:QueryRepresentation,company:CompanyProfile):
    score=0.0
    if query.is_public is None:
        return score
    if company.is_public==query.is_public:
        score=score+2.0
    else:
        score=score-1.5
    return score
def score_candidate(query:QueryRepresentation,company:CompanyProfile):
    score=0.0
    score=score+score_geography(query,company)
    score=score+score_industry(query, company)
    score=score+score_business_model(query, company)
    score=score+score_target_markets(query, company)
    score=score+score_core_offerings(query,company)
    score=score+score_full_text_overlap(query,company)
    score=score+score_public_status(query, company)
    return score
def generate_candidates(query:QueryRepresentation,companies:list[CompanyProfile],top_k:int=50):
    #score all candidates and return top_k
    scored_candidates=[]
    for company in companies:
        #for structured and mixed queries require at least one required semantic match otheerwise the candidate pool gets filled with
        #country matches or generic companies
        if query.query_type in ["structured","mixed"]:
            if not matches_any_required_term(query, company):
                continue
        candidate_score=score_candidate(query, company)
        scored_candidates.append((company,candidate_score))
    scored_candidates.sort(key=lambda item:item[1],reverse=True)
    if top_k<len(scored_candidates):
        return scored_candidates[:top_k]
    return scored_candidates
def print_candidates(query:QueryRepresentation,candidates:list[tuple[CompanyProfile,float]],top_k:int=15):
    print(f"Candidates for query: {query.raw_query}")
    max_items=min(top_k,len(candidates))
    for i in range(max_items):
        company,score=candidates[i]
        print(f"\nRank {i+1}")
        print(f"Name: {company.operational_name}")
        print(f"Website: {company.website}")
        print(f"Primary NAICS: {company.primary_naics_label}")
        print(f"Business Model: {company.business_model}")
        print(f"Target Markets: {company.target_markets}")
        print(f"Score: {score}")




