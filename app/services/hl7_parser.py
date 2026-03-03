from datetime import datetime

def parse_hl7(hl7_text: str):
    lines = hl7_text.strip().split("\n")

    patient_name = "Unknown"
    dob = "Unknown"
    mrn = "Unknown"
    observations = []
    summary = ""

    for line in lines:
        fields = line.split("|")

        # PID segment (Patient Info)
        if line.startswith("PID"):
            # MRN
            if len(fields) > 3:
                mrn = fields[3]

            # Name (Last^First)
            if len(fields) > 5:
                name_parts = fields[5].split("^")
                if len(name_parts) >= 2:
                    patient_name = f"{name_parts[1]} {name_parts[0]}"

            # DOB
            if len(fields) > 7:
                raw_dob = fields[7]
                if len(raw_dob) == 8:
                    dob = f"{raw_dob[0:4]}-{raw_dob[4:6]}-{raw_dob[6:8]}"

        # OBX segment (Lab Results)
        if line.startswith("OBX"):
            test = fields[3] if len(fields) > 3 else ""
            value = fields[5] if len(fields) > 5 else ""
            units = fields[6] if len(fields) > 6 else ""
            reference = fields[7] if len(fields) > 7 else ""
            flag = fields[8] if len(fields) > 8 else ""

            observations.append({
                "test": test,
                "value": value,
                "units": units,
                "reference": reference,
                "flag": flag
            })

            if flag == "H":
                summary += f"{test} is above normal range. "
            elif flag == "L":
                summary += f"{test} is below normal range. "

    return {
        "patient_name": patient_name,
        "dob": dob,
        "mrn": mrn,
        "summary": summary.strip(),
        "observations": observations,
        "run_date": datetime.now().strftime("%Y-%m-%d")
    }
