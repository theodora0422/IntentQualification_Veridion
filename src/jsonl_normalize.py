import ast
from typing import Any

from src.company_schema import CompanyProfile


def literal_eval(value:Any):
    # some fields are store as Python dict, and I try to parse them
    if value is None:
        return None
    if isinstance(value, dict) or isinstance(value, list):
        return value
    if not isinstance(value,str):
        return value
    new_value=value.strip()
    if new_value=="":
        return None
    try:
        # the fields use '' instead of " ", which is Python syntax, so, we need to convert Python-like string to Python onjects
        # and this is why I used ast (it is the only solution to not lose data)
        parsed_value=ast.literal_eval(new_value)
        return parsed_value
    except Exception as e:
        return value
def normalize_text(value:Any):
    #converts a value to a clean single line string
    if value is None:
        return ""
    if not isinstance(value,str):
        value=str(value)
    value=value.strip()
    parts=value.split()
    cleaned_parts=[]
    for part in parts:
        cleaned_parts.append(part)
    new_text=" ".join(cleaned_parts)
    return new_text
def normalize_list(value:Any):
    # normalize a list that should contain a list of strings
    result=[]
    if value is None:
        return result
    if isinstance(value,list):
        for item in value:
            new_item=normalize_text(item)
            if new_item!="":
                result.append(new_item)
        return result
    if isinstance(value,str):
        parsed_value=literal_eval(value)
        if isinstance(parsed_value,list):
            for item in parsed_value:
                new_item=normalize_text(item)
                if new_item!="":
                    result.append(new_item)
            return result
        new_value=normalize_text(value)
        if new_value!="":
            result.append(new_value)
    return result
def normalize_float(value:Any):
    #converts a value to a float if possible
    if value is None:
        return None
    try:
        return float(value)
    except Exception as e:
        return None
def parse_address(address:Any):
    result={
        "country_code":None,
        "region_name":None,
        "town":None,
    }
    parsed_address=literal_eval(address)
    if not isinstance(parsed_address,dict):
        return result
    result["country_code"]=parsed_address.get("country_code")
    result["region_name"]=parsed_address.get("region_name")
    result["town"]=parsed_address.get("town")
    return result
def parse_naics(naics:Any):
    result:dict[str,str|None]={
        "code":None,
        "label":None,
    }
    parsed_naics=literal_eval(naics)
    if not isinstance(parsed_naics,dict):
        return result
    code=parsed_naics.get("code")
    label=parsed_naics.get("label")
    if code is not None:
        result["code"]=normalize_text(code)
    if label is not None:
        result["label"]=normalize_text(label)
    return result
def build_full_profile(operational_name:str|None,description:str,primary_naics_label:str|None,secondary_naics_label:str|None,business_model:list[str],target_markets:list[str],core_offerings:list[str]):
    text_parts=[]
    if operational_name is not None and operational_name!="":
        text_parts.append(operational_name)
    if description!="":
        text_parts.append(description)
    if primary_naics_label is not None and primary_naics_label!="":
        text_parts.append(primary_naics_label)
    if secondary_naics_label is not None and secondary_naics_label!="":
        text_parts.append(secondary_naics_label)
    if len(business_model)>0:
        business_text=""
        for index,item in enumerate(business_model):
            if index==0:
                business_text=item
            else:
                business_text=business_text+ " | "+item
        text_parts.append(business_text)
    if len(target_markets)>0:
        target_markets_text=""
        for index,item in enumerate(target_markets):
            if index==0:
                target_markets_text=item
            else:
                target_markets_text=target_markets_text+" | "+item
        text_parts.append(target_markets_text)
    if len(core_offerings)>0:
        core_offerings_text=""
        for index,item in enumerate(core_offerings):
            if index==0:
                core_offerings_text=item
            else:
                core_offerings_text=core_offerings_text+" | "+item
        text_parts.append(core_offerings_text)
    final_text=""
    for index,part in enumerate(text_parts):
        if index==0:
            final_text=part
        else:
            final_text=final_text+"\n"+part
    return final_text.strip()
def normalize_company(company:dict)->CompanyProfile:
    # convert one raw company dict to a normalized CompanyProfile
    address=parse_address(company.get("address"))
    primary_naics=parse_naics(company.get("primary_naics"))
    secondary_naics=parse_naics(company.get("secondary_naics"))
    website=normalize_text(company.get("website"))
    operational_name=normalize_text(company.get("operational_name"))
    description=normalize_text(company.get("description"))
    business_model=normalize_list(company.get("business_model"))
    target_markets=normalize_list(company.get("target_markets"))
    core_offerings=normalize_list(company.get("core_offerings"))

    if website =="":
        website=None
    if operational_name=="":
        operational_name=None
    full_profile=build_full_profile(operational_name=operational_name,description=description,primary_naics_label=primary_naics["label"],secondary_naics_label=secondary_naics["label"],business_model=business_model,target_markets=target_markets,core_offerings=core_offerings)
    company_normalized=CompanyProfile(website=website,operational_name=operational_name,year_founded=normalize_float(company.get("year_founded")),
                                      employee_count=normalize_float(company.get("employee_count")),
                                      revenue=normalize_float(company.get("revenue")),
                                      is_public=company.get("is_public"),
                                      country_code=address["country_code"],
                                      region_name=address["region_name"],
                                      town=address["town"],
                                      primary_naics_code=primary_naics["code"],
                                      primary_naics_label=primary_naics["label"],
                                      secondary_naics_code=secondary_naics["code"],
                                      secondary_naics_label=secondary_naics["label"],
                                      description=description,
                                      business_model=business_model,
                                      target_markets=target_markets,
                                      core_offerings=core_offerings,
                                      full_profile=full_profile)
    return company_normalized

def normalize_companies(companies:list[dict])->list[CompanyProfile]:
    normalized_companies=[]
    for company in companies:
        try:
            normalized_company=normalize_company(company)
            normalized_companies.append(normalized_company)
        except Exception as e:
            company_name=company.get("operational_name")
            print(f"Failed to normalize company '{company_name}':{e}")
    return normalized_companies