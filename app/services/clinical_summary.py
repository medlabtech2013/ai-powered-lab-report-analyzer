def generate_summary(observations):
    findings = []

    for obs in observations:
        if obs["flag"] == "H":
            if obs["test"] == "WBC":
                findings.append("leukocytosis")
        elif obs["flag"] == "L":
            if obs["test"] in ["HGB", "HCT"]:
                findings.append("anemia")

    if not findings:
        return "No clinically significant abnormalities detected."

    summary = "Findings suggest " + " and ".join(set(findings)) + "."
    return summary

