from app.core.loinc_map import LOINC_MAP

def parse_hl7(content: str):
    lines = content.strip().split("\n")
    observations = []

    for line in lines:
        if line.startswith("OBX"):
            fields = line.split("|")

            test = fields[3] if len(fields) > 3 else ""
            value = fields[5] if len(fields) > 5 else ""
            units = fields[6] if len(fields) > 6 else ""
            reference_range = fields[7] if len(fields) > 7 else ""
            flag = fields[8] if len(fields) > 8 else ""

            try:
                value = float(value)
            except:
                pass

            observations.append({
                "test": test,
                "value": value,
                "units": units,
                "reference_range": reference_range,
                "flag": flag,
                "loinc": LOINC_MAP.get(test, "unknown")
            })

    return {
        "observations": observations
    }
