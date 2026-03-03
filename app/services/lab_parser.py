import re

def parse_lab(text: str):
    observations = []

    lines = text.splitlines()
    for line in lines:
        match = re.match(r"(\w+)\s+([\d.]+)\s+([\w/]+)\s+\(([\d.-]+)\)", line)
        if match:
            test, value, units, ref = match.groups()

            low, high = ref.split("-")
            value_f = float(value)

            flag = "N"
            if value_f < float(low):
                flag = "L"
            elif value_f > float(high):
                flag = "H"

            observations.append({
                "test": test,
                "value": value,
                "units": units,
                "reference_range": ref,
                "flag": flag
            })

    return observations
