from src.company_schema import CompanyProfile
from src.query_schema import QueryRepresentation


def check_country_constraint(query:QueryRepresentation,company:CompanyProfile):
    #passed if the candidate passes the check, uncertain if the result is uncertain bcs data is missing, reason-explanation
    if len(query.country_codes)==0:
        return True,False,"no country contraint"
    if company.country_code is None:
        return True,True,"missing country_code"
    if company.country_code in query.country_codes:
        return True, False,"country match"
    return False,False,"country mismatch"
def check_public_constraint(query:QueryRepresentation,company:CompanyProfile):
    if query.is_public is None:
        return True, False, "no public/private constraint"
    if company.is_public is None:
        return True, True, "missing is_public"
    if company.is_public == query.is_public:
        return True,False,"public/private match"
    return False,False,"public/private mismatch"
def check_min_employee_constraint(query:QueryRepresentation,company:CompanyProfile):
    if query.min_employee_count is None:
        return True,False,"no minimum employee constraint"
    if company.employee_count is None:
        return True, True,"missing employee_count"
    if company.employee_count>=query.min_employee_count:
        return True, False,"employee_count satisfies minimum"
    return False, False,"employee_count below minimum"
def check_max_employee_constraint(query:QueryRepresentation,company:CompanyProfile):
    if query.max_employee_count is None:
        return True, False, "no maximum employee constraint"
    if company.employee_count is None:
        return True, True, "missing employee_count"
    if company.employee_count<=query.max_employee_count:
        return True, False, "employee_count satisfies maximum"
    return False, False, "employee_count above maximum"
def check_min_revenue_constraint(query:QueryRepresentation,company:CompanyProfile):
    if query.min_revenue is None:
        return True, False, "no minimum revenue constraint"
    if company.revenue is None:
        return True, True, "missing revenue"
    if company.revenue >= query.min_revenue:
        return True, False, "revenue satisfies minimum"
    return False, False, "revenue below minimum"
def check_max_revenue_constraint(query:QueryRepresentation,company:CompanyProfile):
    if query.max_revenue is None:
        return True, False, "no maximum revenue constraint"
    if company.revenue is None:
        return True, True, "missing revenue"
    if company.revenue<=query.max_revenue:
        return True, False,"revenue satisfies maximum"
    return False,False,"revenue above maximum"
def check_min_year_constraint(query:QueryRepresentation,company:CompanyProfile):
    if query.min_year_founded is None:
        return True, False,"no minimum founded year constraint"
    if company.year_founded is None:
        return True,True,"missing year_founded"
    if company.year_founded>=query.min_year_founded:
        return True,False,"year_founded satisfies minimum"
    return False, False, "year_founded below minimum"
def check_max_year_constraint(query:QueryRepresentation,company:CompanyProfile):
    if query.max_year_founded is None:
        return True,False, "no maximum founded year constraint"
    if company.year_founded is None:
        return True,True, "missing year_founded"
    if company.year_founded<=query.max_year_founded:
        return True,False,"year_founded satisfies maximum"
    return False,False,"year_founded above maximum"
def evaluate_hard_constraints(query:QueryRepresentation,company:CompanyProfile):
    #evaluate all hard constraints for one company
    checks=[]
    checks.append(check_country_constraint(query,company))
    checks.append(check_public_constraint(query,company))
    checks.append(check_min_employee_constraint(query,company))
    checks.append(check_max_employee_constraint(query,company))
    checks.append(check_min_revenue_constraint(query, company))
    checks.append(check_max_revenue_constraint(query,company))
    checks.append(check_min_year_constraint(query, company))
    checks.append(check_max_year_constraint(query, company))
    passed_all=True
    has_uncertainty=False
    reasons=[]
    for passed,uncertain,reason in checks:
        reasons.append(reason)
        if uncertain:
            has_uncertainty=True
        if not passed:
            passed_all=False
    return {
        "passed_all":passed_all,
        "has_uncertainty":has_uncertainty,
        "reasons":reasons,
    }
def filter_candidates_by_hard_constraints(query:QueryRepresentation,candidates:list[tuple[CompanyProfile,float]]):
    #keep only candidates that do not explicitly violate hard constraints
    filtered_candidates=[]
    for company,candidate_score in candidates:
        evaluation=evaluate_hard_constraints(query, company)
        if evaluation["passed_all"]:
            filtered_candidates.append((company,candidate_score,evaluation))
    return filtered_candidates
def print_filtered_candidates(query:QueryRepresentation,filtered_candidates:list[tuple[CompanyProfile,float,dict]],top_k:int=10):
    print(f"Filterred candidated for query:{query.raw_query}")
    max_items=min(top_k,len(filtered_candidates))
    for i in range(max_items):
        company,score,evaluation=filtered_candidates[i]
        print(f"\nRank {i+1}")
        print(f"Name: {company.operational_name}")
        print(f"Website: {company.website}")
        print(f"Country: {company.country_code}")
        print(f"Primary NAICS: {company.primary_naics_label}")
        print(f"Employee Count: {company.employee_count}")
        print(f"Revenue: {company.revenue}")
        print(f"Year Founded: {company.year_founded}")
        print(f"Is Public: {company.is_public}")
        print(f"Candidate Score: {score}")
        print(f"Has Uncertainty: {evaluation['has_uncertainty']}")
        print(f"Reasons: {evaluation['reasons']}")


