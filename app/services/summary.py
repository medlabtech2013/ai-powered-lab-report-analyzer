def generate_summary(observations):
    """
    Generates a basic clinical summary from parsed lab observations.
    """

    if not observations:
        return "No lab observations found."

    abnormal = []

    for obs in observations:
        try:
            value = float(obs["value"])
            ref_low, ref_high = map(float, obs["reference_range"].split("-"))

            if value < ref_low:
                abnormal.append(f"{obs['test']} is below normal range.")
            elif value > ref_high:
                abnormal.append(f"{obs['test']} is above normal range.")
        except Exception:
            continue

    if not abnormal:
        return "All lab values are within normal limits."

    return " ".join(abnormal)
