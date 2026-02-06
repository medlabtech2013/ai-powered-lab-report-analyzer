import re

# --------------------------------------------
# Helper: Determine abnormal flag
# --------------------------------------------
def flag_result(value, reference_range):
    try:
        low, high = reference_range.split("-")
        low = float(low)
        high = float(high)
        value = float(value)

        if value < low:
            return "L"
        elif value > high:
            return "H"
        else:
            return "N"
    except:
        return "N"


# --------------------------------------------
# Main parser function
# --------------------------------------------
def parse_lab(content: str):
    """
    Parses HL7-like lab text and extracts:
    - test name
    - value
    - units
    - reference range
    - abnormal flag (H/L/N)
    """

    observations = []

    lines = content.splitlines()

    for line in lines:
        # Example HL7 OBX line:
        # OBX|1|NM|WBC||14.2|10^3/uL|4-11|H
        if line.startswith("OBX"):
            parts = line.split("|")

            try:
                test_name = parts[3]
                value = parts[5]
                units = parts[6]
                ref_range = parts[7]

                observation = {
                    "test": test_name,
                    "value": value,
                    "units": units,
                    "reference_range": ref_range,
                    "flag": flag_result(value, ref_range)
                }

                observations.append(observation)

            except IndexError:
                # Skip malformed lines
                continue

    return observations

