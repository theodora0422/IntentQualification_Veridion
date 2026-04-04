import json
import time

from src.company_schema import CompanyProfile
from src.query_schema import QueryRepresentation


def should_use_llm(query:QueryRepresentation,reranked_candidates:list[tuple],min_results_threshold:int=3):
    #I use llm if the query is strong-reasoning,or the candidate list is too small or the top final scores are weak/negative
    if query.query_type=="strong-reasoning":
        return True
    if len(reranked_candidates)==0:
        return False
    if len(reranked_candidates)<min_results_threshold:
        return True
    #if the best candidates still have very weak scores the llm should help
    best_final_score=reranked_candidates[0][2]
    if best_final_score<=0:
        return True
    return False

def build_company_summary(company:CompanyProfile):
    #build a summary for the llm prompt
    summary_lines=[]
    summary_lines.append(f"Name: {company.operational_name}")
    summary_lines.append(f"Website: {company.website}")
    summary_lines.append(f"Country: {company.country_code}")
    summary_lines.append(f"Region: {company.region_name}")
    summary_lines.append(f"Town: {company.town}")
    summary_lines.append(f"Year Founded: {company.year_founded}")
    summary_lines.append(f"Employee Count: {company.employee_count}")
    summary_lines.append(f"Revenue: {company.revenue}")
    summary_lines.append(f"Is Public: {company.is_public}")
    summary_lines.append(f"Primary NAICS: {company.primary_naics_label}")
    summary_lines.append(f"Business Model: {company.business_model}")
    summary_lines.append(f"Target Markets: {company.target_markets}")
    summary_lines.append(f"Core Offerings: {company.core_offerings}")
    summary_lines.append(f"Description: {company.description}")
    return "\n".join(summary_lines)
def build_llm_prompt(query:QueryRepresentation,company:CompanyProfile,candidate_score:float,final_score:float,scoring_reasons:list[str]):
    company_summary=build_company_summary(company)
    reasons_text=""
    for reason in scoring_reasons:
        reasons_text=reasons_text+"- "+reason+"\n"
    prompt = f"""
    You are evaluating whether a company truly matches a user query.

    Return ONLY a valid JSON object.
    Do not include markdown.
    Do not include code fences.
    Do not include extra text.

    Allowed labels:
    - strong_match
    - possible_match
    - weak_match
    - not_match

    Scoring guidance:
    - strong_match = clear and direct fit
    - possible_match = plausible but incomplete or indirect fit
    - weak_match = weak evidence
    - not_match = does not satisfy the query

    User query:
    {query.raw_query}

    Parsed query type:
    {query.query_type}

    Current pipeline scores:
    - candidate_score: {candidate_score}
    - final_score: {final_score}

    Current pipeline reasons:
    {reasons_text}

    Company profile:
    {company_summary}

    Return JSON with this exact schema:
    {{
      "label": "strong_match" | "possible_match" | "weak_match" | "not_match",
      "llm_score": integer from 0 to 10,
      "explanation": "short explanation"
    }}
    """.strip()
    return prompt
def parse_llm_response(raw_response: str):
    fallback = {
        "label": "weak_match",
        "llm_score": 3,
        "explanation": "LLM response could not be parsed"
    }

    if raw_response is None:
        return fallback

    raw_response = raw_response.strip()
    if raw_response == "":
        return fallback

    if raw_response.startswith("```"):
        raw_response = raw_response.strip("`")
        raw_response = raw_response.replace("json\n", "", 1).strip()

    try:
        parsed = json.loads(raw_response)
        label = parsed.get("label")
        llm_score = parsed.get("llm_score")
        explanation = parsed.get("explanation")

        valid_labels = ["strong_match", "possible_match", "weak_match", "not_match"]
        if label not in valid_labels:
            label = "weak_match"

        if not isinstance(llm_score, int):
            llm_score = 3

        if not isinstance(explanation, str):
            explanation = "No explanation provided"

        return {
            "label": label,
            "llm_score": llm_score,
            "explanation": explanation,
        }
    except Exception:
        return fallback
def llm_label_to_score(label:str):
    if label=="strong_match":
        return 6.0
    if label=="possible_match":
        return 2.5
    if label=="weak_match":
        return -1.0
    if label=="not_match":
        return -6.0
    return 0.0
def safe_call_llm(call_llm,prompt):
    for _ in range(3):
        try:
            return call_llm(prompt)
        except Exception as e:
            if "429" in str(e):
                time.sleep(10)
            else:
                break
    return None
def rerank_with_llm(query:QueryRepresentation,reranked_candidates:list[tuple[CompanyProfile,float,float,dict,list[str]]],call_llm,top_k_for_llm:int=5):
    output=[]
    max_items=min(top_k_for_llm,len(reranked_candidates))
    for i in range(max_items):
        company,candidate_score,final_score,evaluation,reasons=reranked_candidates[i]
        prompt=build_llm_prompt(query,company,candidate_score,final_score,reasons)
        raw_response=safe_call_llm(call_llm,prompt)
        llm_result=parse_llm_response(raw_response)
        if "LLM unavailable" in llm_result["explanation"]:
            llm_adjusted_score = final_score

            output.append(
                (
                    company,
                    candidate_score,
                    final_score,
                    llm_adjusted_score,
                    evaluation,
                    reasons,
                    llm_result,
                )
            )
            continue
        llm_bonus=llm_label_to_score(llm_result["label"])
        llm_adjusted_score=final_score+llm_bonus+(llm_result["llm_score"]*0.2)
        output.append((company,candidate_score,final_score,llm_adjusted_score,evaluation,reasons,llm_result))
    output.sort(key=lambda item:item[3],reverse=True)
    return output
def print_llm_reranked_candidates(query:QueryRepresentation,llm_candidates:list[tuple[CompanyProfile,float,float,float,dict,list[str],dict]],top_k:int=5):
    print(f"\n\nLLM Final Ranking for query: {query.raw_query}")
    max_items=min(top_k,len(llm_candidates))
    for i in range(max_items):
        company,candidate_score,final_score,llm_adjusted_score,evaluation,reasons,llm_result=llm_candidates[i]
        print(f"\nRank {i + 1}")
        print(f"Name: {company.operational_name}")
        print(f"Website: {company.website}")
        print(f"Country: {company.country_code}")
        print(f"Primary NAICS: {company.primary_naics_label}")
        print(f"Candidate Score: {candidate_score}")
        print(f"Final Score Before LLM: {final_score}")
        print(f"Final Score After LLM: {llm_adjusted_score}")
        print(f"LLM Label: {llm_result['label']}")
        print(f"LLM Score: {llm_result['llm_score']}")
        print(f"LLM Explanation: {llm_result['explanation']}")
        print(f"Has Uncertainty: {evaluation['has_uncertainty']}")
        print(f"Reasons: {reasons}")