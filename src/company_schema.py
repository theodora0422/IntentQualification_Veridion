from typing import Optional


class CompanyProfile:
    # normalized representation of a company; all stages must work
    # with this structure instead of the raw JSONL; all the params are fields in the jsonl

    website:Optional[str]
    operational_name:Optional[str]
    year_founded:Optional[float]
    address:Optional[str]
    employee_count:Optional[float]
    revenue:Optional[float]

    country_code: Optional[str]
    region_name:Optional[str]
    town:Optional[str]
    # primary_naics and secondary_naics are two dicts composed of code and label
    primary_naics_code:Optional[str]
    primary_naics_label:Optional[str]
    secondary_naics_code:Optional[str]
    secondary_naics_label:Optional[str]

    description:Optional[str]
    business_model:list[str]
    core_offerings:list[str]
    target_markets:list[str]
    is_public:Optional[bool]
    full_profile:str

    def __init__(self,website,operational_name,year_founded,employee_count,revenue,is_public,country_code,region_name,
                 town,primary_naics_code,primary_naics_label,secondary_naics_code,secondary_naics_label,description,
                 business_model,target_markets,core_offerings,full_profile):
       self.website=website
       self.operational_name=operational_name
       self.year_founded=year_founded
       self.employee_count=employee_count
       self.revenue=revenue
       self.is_public=is_public
       self.country_code=country_code
       self.region_name=region_name
       self.town=town
       self.primary_naics_code=primary_naics_code
       self.primary_naics_label=primary_naics_label
       self.secondary_naics_code=secondary_naics_code
       self.secondary_naics_label=secondary_naics_label
       self.description=description
       self.business_model=business_model
       self.core_offerings=core_offerings
       self.target_markets=target_markets
       self.full_profile=full_profile

    def to_dict(self):
        return {
            "website":self.website,
            "operational_name":self.operational_name,
            "year_founded":self.year_founded,
            "employee_count":self.employee_count,
            "revenue":self.revenue,
            "is_public":self.is_public,
            "country_code":self.country_code,
            "region_name":self.region_name,
            "town":self.town,
            "primary_naics_code":self.primary_naics_code,
            "primary_naics_label":self.primary_naics_label,
            "secondary_naics_code":self.secondary_naics_code,
            "secondary_naics_label":self.secondary_naics_label,
            "description":self.description,
            "business_model":self.business_model,
            "core_offerings":self.core_offerings,
            "target_markets":self.target_markets,
            "full_profile":self.full_profile,
        }