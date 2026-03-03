from app.core.loinc_map import LOINC_MAP

def parse_lab(content: str):
    observations = []
    lines = content.splitlines()

    for line in lines:
        if not line.startswith("OBX|"):
            continue

        fields = line.split("|")

        # Minimum HL7 OBX length check
        if len(fields) < 8:
            continue

        test = fields[3].strip()
        raw_value = fields[5].strip()
        units = fields[6].strip()
        ref_range = fields[7].strip()

        # Skip incomplete observations
        if not test or not raw_value or not ref_range:
            continue

        try:
            value = float(raw_value)
            ref_low, ref_high = map(float, ref_range.split("-"))
        except ValueError:
            # Non-numeric or malformed data
            continue

        if value < ref_low:
            flag = "L"
        elif value > ref_high:
            flag = "H"
        else:
            flag = "N"

        observations.append({
            "test": test,
            "value": value,
            "units": units,
            "reference_range": ref_range,
            "flag": flag,
            "loinc": LOINC_MAP.get(test, "unknown")
        })

    return observations

