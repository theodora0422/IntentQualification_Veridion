from typing import Optional


class QueryRepresentation:
    #structured internal representation of a user query
    #used for candidate generation, filtering, scoring and LLM
    raw_query:str
    normalized_query:str
    query_type:str
    country_codes:list[str]
    region_terms:list[str]
    industry_terms:list[str]
    business_model_terms:list[str]
    target_market_terms:list[str]
    relational_terms:list[str]
    vague_terms:list[str]
    is_public:Optional[bool]
    min_employee_count:Optional[float]
    max_employee_count:Optional[float]
    min_revenue:Optional[float]
    max_revenue:Optional[float]
    min_year_founded:Optional[float]
    max_year_founded:Optional[float]

    def __init__(self,raw_query:str,normalized_query:str,query_type:str,country_codes:list[str],region_terms:list[str],
                 industry_terms:list[str],business_model_terms:list[str],target_market_terms:list[str],relational_terms:list[str],
                 vague_terms:list[str],is_public:Optional[bool],min_employee_count:Optional[float],max_employee_count:Optional[float],
                 min_revenue:Optional[float],max_revenue:Optional[float],min_year_founded:Optional[float],max_year_founded:Optional[float]):
        self.raw_query=raw_query
        self.normalized_query=normalized_query
        self.query_type=query_type
        self.country_codes=country_codes
        self.region_terms=region_terms
        self.industry_terms=industry_terms
        self.business_model_terms=business_model_terms
        self.target_market_terms=target_market_terms
        self.relational_terms=relational_terms
        self.vague_terms=vague_terms
        self.is_public=is_public
        self.min_employee_count=min_employee_count
        self.max_employee_count=max_employee_count
        self.min_revenue=min_revenue
        self.max_revenue=max_revenue
        self.min_year_founded=min_year_founded
        self.max_year_founded=max_year_founded
    def to_dict(self):
        return{
            "raw_query":self.raw_query,
            "normalized_query":self.normalized_query,
            "query_type":self.query_type,
            "country_codes":self.country_codes,
            "region_terms":self.region_terms,
            "industry_terms":self.industry_terms,
            "business_model_terms":self.business_model_terms,
            "target_markets_terms":self.target_market_terms,
            "relational_terms":self.relational_terms,
            "vague_terms":self.vague_terms,
            "is_public":self.is_public,
            "min_employee_count":self.min_employee_count,
            "max_employee_count":self.max_employee_count,
            "min_revenue":self.min_revenue,
            "max_revenue":self.max_revenue,
            "min_year_founded":self.min_year_founded,
            "max_year_founded":self.max_year_founded,
        }