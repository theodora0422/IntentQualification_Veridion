from src.company_schema import CompanyProfile
from src.query_schema import QueryRepresentation


def normalize_text_for_match(value:str|None):
    #lowercase text and clean spaces
    if value is None:
        return ""
    value=value.lower().strip()
    parts=value.split()
    clean_parts=[]
    for part in parts:
        clean_parts.append(part)
    return " ".join(clean_parts)
def text_contains_term(text:str | None, term:str):
    normalized_text=normalize_text_for_match(text)
    normalized_term=normalize_text_for_match(term)
    if normalized_term=="":
        return False
    return normalized_term in normalized_text
def list_contains_term(values:list[str],term:str):
    for value in values:
        if text_contains_term(value,term):
            return True
    return False
def company_matches_term(company:CompanyProfile,term:str):
    #check if a company matches a semantic term in any important field
    if text_contains_term(company.primary_naics_label,term):
        return True
    if text_contains_term(company.description,term):
        return True
    if text_contains_term(company.full_profile,term):
        return True
    if list_contains_term(company.business_model,term):
        return True
    if list_contains_term(company.target_markets,term):
        return True
    if list_contains_term(company.core_offerings,term):
        return True
    return False
def get_required_terms(query:QueryRepresentation):
    #return semantic terms that should matter the most
    required_terms=[]
    generic_terms={
        "manufacturing",
        "retail",
        "enterprise",
        "service provider",
        "wholesale",
    }
    for term in query.industry_terms:
        if term not in generic_terms:
            if term not in required_terms:
                required_terms.append(term)
    if "packaging" in query.normalized_query:
        if "packaging" not in required_terms:
            required_terms.append("packaging")
    return required_terms
def get_supportive_terms(query:QueryRepresentation):
    #return semantic terms that help but not dominate the ranking
    supportive_terms=[]
    required_terms=get_required_terms(query)
    generic_supportive_terms={
        "manufacturing",
        "retail",
        "enterprise",
        "service provider",
        "wholesale",
    }
    for term in query.industry_terms:
        if term in generic_supportive_terms:
            continue
        if term in required_terms:
            continue
        if term not in supportive_terms:
            supportive_terms.append(term)
    for term in query.business_model_terms:
        if term in generic_supportive_terms:
            continue
        if term in required_terms:
            continue
        if term not in supportive_terms:
            supportive_terms.append(term)
    for term in query.target_market_terms:
        if term in generic_supportive_terms:
            continue
        if term in required_terms:
            continue
        if term not in supportive_terms:
            supportive_terms.append(term)
    return supportive_terms
def score_required_terms(query:QueryRepresentation,company:CompanyProfile):
    #strongly reward matching required terms and strongly penalize missing them
    score=0.0
    reasons=[]
    required_terms=get_required_terms(query)
    for term in required_terms:
        if company_matches_term(company,term):
            score=score+4.0
            reasons.append(f"matched required term: {term}")
        else:
            score=score-12.0
            reasons.append(f"missing required term: {term}")
    return score, reasons
def score_supportive_terms(query:QueryRepresentation,company:CompanyProfile):
    score=0.0
    reasons=[]
    supportive_terms=get_supportive_terms(query)
    for term in supportive_terms:
        if company_matches_term(company,term):
            score=score+0.5
            reasons.append(f"matched supportive term:{term}")
    return score,reasons
def score_hr_signal(company:CompanyProfile):
    score=0.0
    reasons=[]
    hr_terms=["human resources","hr","payroll","workforce","recruiting"]
    hr_match_count=0
    for term in hr_terms:
        if company_matches_term(company,term):
            hr_match_count+=1
    if hr_match_count>3:
        hr_match_count=3
    if hr_match_count>0:
        score=score+(hr_match_count*1.0)
        reasons.append(f"matched HR related signals: {hr_match_count}")
    return score,reasons
def score_packaging_signal(company:CompanyProfile):
    score=0.0
    reasons=[]
    packaging_terms=[
        "packaging",
        "bottle",
        "bottles",
        "container",
        "containers",
        "glass",
        "plastic",
        "paperboard",
        "mold",

    ]
    packaging_match_count=0
    for term in packaging_terms:
        if company_matches_term(company,term):
            packaging_match_count+=1
    if packaging_match_count>0:
        score=score+(packaging_match_count*1.0)
        reasons.append(f"matched packaging related signals: {packaging_match_count}")
    return score,reasons
def score_fintech_signal(company:CompanyProfile):
    score=0.0
    reasons=[]
    fintech_terms=[
        "financial",
        "payments",
        "banking",
        "credit",
        "transactions",
        "fintech",
    ]
    fintech_match_count=0
    for term in fintech_terms:
        if company_matches_term(company, term):
            fintech_match_count+=1
    if fintech_match_count>0:
        score=score+(fintech_match_count*1.0)
        reasons.append(f"matched fintech-related signals: {fintech_match_count}")
    return score,reasons
def score_uncertainty_penalty(evaluation:dict):
    score=0.0
    reasons=[]
    if evaluation["has_uncertainty"]:
        score=score-1.5
        reasons.append("uncertainty penalty due to missing hard constraint data")
    return score, reasons
def score_final_candidate(query:QueryRepresentation,company:CompanyProfile,candidate_score:float,evaluation:dict):
    #start from broad candidate score, reinforce required semantic matches, add query-specific helper signals, penalize uncertainty
    final_score=candidate_score
    reasons=[f"base candidate score: {candidate_score}"]
    required_score,required_reasons=score_required_terms(query, company)
    final_score=final_score+required_score
    reasons.extend(required_reasons)
    supportive_score,supportive_reasons=score_supportive_terms(query, company)
    final_score=final_score+supportive_score
    reasons.extend(supportive_reasons)
    query_text=query.normalized_query

    if "hr" in query_text or "human resources" in query_text:
        hr_score,hr_reasons=score_hr_signal(company)
        final_score=final_score+hr_score
        reasons.extend(hr_reasons)
    if "packaging" in query_text:
        packaging_score,packaging_reasons=score_packaging_signal(company)
        final_score+=packaging_score
    if "fintech" in query_text or "banks" in query_text or "bank" in query_text:
        fintech_score,fintech_reasons=score_fintech_signal(company)
        final_score+=fintech_score
        reasons.extend(fintech_reasons)
    uncertainty_score,uncertainty_reasons=score_uncertainty_penalty(evaluation)
    final_score+=uncertainty_score
    reasons.extend(uncertainty_reasons)
    return final_score,reasons
def rerank_filtered_candidates(query:QueryRepresentation,filtered_candidates:list[tuple[CompanyProfile,float,dict]]):
    reranked_candidates=[]
    for company,candidate_score,evaluation in filtered_candidates:
        final_score,reasons=score_final_candidate(query,company, candidate_score, evaluation)
        reranked_candidates.append((company,candidate_score,final_score,evaluation,reasons))
    reranked_candidates.sort(key=lambda item:item[2],reverse=True)
    return reranked_candidates
def print_reranked_candidates(query:QueryRepresentation,reranked_candidates:list[tuple[CompanyProfile,float,float,dict,list[str]]],top_k:int=10):
    print(f"\nFinal Ranking for query: {query.raw_query}")
    max_items=min(top_k,len(reranked_candidates))
    for i in range(max_items):
        company,candidate_score,final_score,evaluation,reasons=reranked_candidates[i]
        print(f"\nRank {i+1}")
        print(f"Name:{company.operational_name}")
        print(f"Website: {company.website}")
        print(f"Country: {company.country_code}")
        print(f"Primary NAICS: {company.primary_naics_label}")
        print(f"Employee Count: {company.employee_count}")
        print(f"Revenue: {company.revenue}")
        print(f"Year Founded: {company.year_founded}")
        print(f"Is Public: {company.is_public}")
        print(f"Candidate Score: {candidate_score}")
        print(f"Final Score: {final_score}")
        print(f"Has Uncertainty: {evaluation['has_uncertainty']}")
        print(f"Reasons: {reasons}")