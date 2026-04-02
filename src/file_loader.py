import json
import os


def load_companies(path:str):
    # read JSON file and return a list of raw company dictionaries
    companies=[]
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found:{path}")
    with open(path,"r",encoding="utf-8") as f:
        ct_lines=0
        for line in f:
            ct_lines+=1
            line=line.strip()
            if line=="":
                continue
            try:
                company=json.loads(line)
                companies.append(company)
            except Exception as e:
                print(f"Invalid json on line {ct_lines}: {e}")
    return companies