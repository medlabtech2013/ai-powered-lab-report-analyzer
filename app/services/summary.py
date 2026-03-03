def generate_summary(observations):
    if not observations:
        return "No valid laboratory observations detected."

    messages = []

    for obs in observations:
        if obs["flag"] == "H":
            messages.append(f'{obs["test"]} is above normal range.')
        elif obs["flag"] == "L":
            messages.append(f'{obs["test"]} is below normal range.')

    if not messages:
        return "All values are within normal limits."

    return " ".join(messages)

