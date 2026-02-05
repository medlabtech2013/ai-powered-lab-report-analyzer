def parse_lab(content: str):
    """
    Accepts:
    - Simple lab text: Glucose: 95
    - HL7-ish segments
    """

    results = []

    lines = content.splitlines()

    for line in lines:
        line = line.strip()

        if not line:
            continue

        # Handle simple "Test: Value" format
        if ":" in line:
            parts = line.split(":", 1)
            test = parts[0].strip()
            value = parts[1].strip()

            results.append({
                "test": test,
                "value": value
            })

        # Handle HL7 OBX segment (basic)
        elif line.startswith("OBX"):
            fields = line.split("|")
            if len(fields) >= 6:
                test = fields[3].split("^")[1] if "^" in fields[3] else fields[3]
                value = fields[5]

                results.append({
                    "test": test,
                    "value": value
                })

    return results

