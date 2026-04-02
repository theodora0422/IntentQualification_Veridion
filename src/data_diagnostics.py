from src.company_schema import CompanyProfile


def count_missing_string_field(companies:list[CompanyProfile],field_name:str):
    #count how many companies have a missing string field
    count=0
    for company in companies:
        value=getattr(company,field_name)
        if value is None:
            count+=1
        elif isinstance(value,str) and value.strip()=="":
            count+=1
    return count
def count_missing_numeric_field(companies:list[CompanyProfile],field_name:str):
    #count how many companies have a missing numeric field
    count=0
    for company in companies:
        value=getattr(company,field_name)
        if value is None:
            count+=1
    return count
def count_missing_list_field(companies:list[CompanyProfile],field_name:str):
    #count how many companies have an empty list field
    count=0
    for company in companies:
        value=getattr(company,field_name)
        if value is None:
            count+=1
        elif isinstance(value,list) and len(value)==0:
            count+=1
    return count
def count_booleans_values(companies:list[CompanyProfile],field_name:str):
    result={
        "true":0,
        "false":0,
        "missing":0,
    }
    for company in companies:
        value=getattr(company,field_name)
        if value is True:
            result["true"]=result["true"]+1
        elif value is False:
            result["false"]=result["false"]+1
        else:
            result["missing"]=result["missing"]+1
    return result
def count_top_values(companies:list[CompanyProfile],field_name:str,top_k:int=5):
    #count the most frequest values for a field
    counts={}
    for company in companies:
        value=getattr(company,field_name)
        if value is None:
            continue
        if not isinstance(value,str):
            continue
        value=value.strip()
        if value=="":
            continue
        if value not in counts:
            counts[value]=0
        counts[value]=counts[value]+1
    sorted_counts=sorted(counts.items(),key=lambda item:item[1],reverse=True)
    return sorted_counts[:top_k]
def compute_stats(companies:list[CompanyProfile],field_name:str):
    values=[]
    for company in companies:
        value=getattr(company,field_name)
        if value is not None:
            values.append(value)
    if len(values)==0:
        return{
            "count":0,
            "min":None,
            "max":None,
            "avg":None,
        }
    total=0.0
    minimum=values[0]
    maximum=values[0]
    for value in values:
        total=total+value
        if value<minimum:
            minimum=value
        if value>maximum:
            maximum=value
    average=total/len(values)
    return {
        "count":len(values),
        "min":minimum,
        "max":maximum,
        "avg":average
    }
def print_missing_value(companies:list[CompanyProfile]):
    #print how many missing values we have
    total=len(companies)
    print("Missing values")
    fields_to_check=[
        ("operational_name", "string"),
        ("website", "string"),
        ("description", "string"),
        ("country_code", "string"),
        ("region_name", "string"),
        ("town", "string"),
        ("primary_naics_label", "string"),
        ("secondary_naics_label", "string"),
        ("year_founded", "numeric"),
        ("employee_count", "numeric"),
        ("revenue", "numeric"),
        ("business_model", "list"),
        ("target_markets", "list"),
        ("core_offerings", "list"),
    ]

    for field_name,field_type in fields_to_check:
        if field_type=="string":
            missing_count=count_missing_string_field(companies,field_name)
        elif field_type=="numeric":
            missing_count=count_missing_numeric_field(companies,field_name)
        elif field_type=="list":
            missing_count=count_missing_list_field(companies,field_name)
        else:
            missing_count=0
        missing_percentage=0.0
        if total>0:
            missing_percentage=(missing_count/total)*100.0
        print(f"{field_name}:missing  {missing_count}/{total} ({missing_percentage:.2f}%)")
    boolean_stats=count_booleans_values(companies,"is_public")
    print(f"is_public: true={boolean_stats['true']},false={boolean_stats['false']},missing={boolean_stats['missing']}")

def print_top_countries(companies:list[CompanyProfile],top_k=5):
    #the most common country codes
    print("Top countries")
    top_values=count_top_values(companies,"country_code",top_k)
    for value, count in top_values:
        print(f"{value}:{count}")
def print_top_primary_naics(companies:list[CompanyProfile],top_k:int=5):
    print("Top primary naics labels")
    top_values=count_top_values(companies,"primary_naics_label",top_k)
    for value,count in top_values:
        print(f"{value}:{count}")
def print_numeric_summary(companies:list[CompanyProfile]):
    print("Numeric summary")
    numeric_fields=["year_founded","employee_count","revenue"]
    for field_name in numeric_fields:
        stats=compute_stats(companies,field_name)
        print(f"\nField:{field_name} non missing count: {stats['count']}")
        print(f" min: {stats['min']} max: {stats['max']} avg: {stats['avg']}")
def run(companies:list[CompanyProfile]):
    print("Datatset Diagnostics")
    print(f"Total normalized companies: {len(companies)}")
    print_missing_value(companies)
    print_top_countries(companies)
    print_top_primary_naics(companies)
    print_numeric_summary(companies)