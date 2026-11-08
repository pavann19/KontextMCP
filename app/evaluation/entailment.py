"""Model-judge calibration with explicit expected logical labels; never a legal oracle."""
import json
import httpx

CASES=[
("Systems in group A must produce logs.","Group A systems must produce logs.","ENTAILED"),
("Systems in group A must produce logs.","Group A systems do not need to produce logs.","CONTRADICTED"),
("Systems in group A must produce logs.","The logs must be kept for six years.","UNKNOWN"),
("Only group B is exempt from record keeping.","Every group is exempt from record keeping.","CONTRADICTED"),
("Systeme der Gruppe A müssen Protokolle erstellen.","Gruppe A muss Protokolle erstellen.","ENTAILED"),
("Systeme der Gruppe A müssen Protokolle erstellen.","Gruppe A muss keine Protokolle erstellen.","CONTRADICTED"),
("Systeme der Gruppe A müssen Protokolle erstellen.","Die Protokolle müssen sechs Jahre aufbewahrt werden.","UNKNOWN"),
("The document says nothing about disclosure.","Disclosure is mandatory.","UNKNOWN")]


def calibrate(url,model):
    rows=[]
    schema={"type":"object","properties":{"label":{"type":"string","enum":["ENTAILED","CONTRADICTED","UNKNOWN"]}},"required":["label"],"additionalProperties":False}
    for premise,claim,expected in CASES:
        try:
            response=httpx.post(url+"/api/generate",json={"model":model,"stream":False,"format":schema,"system":"Classify whether the claim follows from the premise alone. Use ENTAILED, CONTRADICTED or UNKNOWN. Do not use outside knowledge.","prompt":json.dumps({"premise":premise,"claim":claim}),"options":{"temperature":0,"num_predict":64,"num_ctx":2048},"keep_alive":"2m"},timeout=90)
            response.raise_for_status();raw=response.json()["response"];label=json.loads(raw).get("label")
            if label not in {"ENTAILED","CONTRADICTED","UNKNOWN"}:label="INVALID"
        except Exception as exc:raw=type(exc).__name__;label="INVALID"
        rows.append({"premise":premise,"claim":claim,"expected":expected,"predicted":label,"raw":raw})
    accuracy=sum(r["expected"]==r["predicted"] for r in rows)/len(rows)
    return {"status":"MEASURED","model":model,"cases":len(rows),"accuracy":accuracy,"suitable_as_sole_legal_validator":False,"scope":"Frozen synthetic logical calibration, not independent legal annotations or proof of legal correctness","results":rows}
