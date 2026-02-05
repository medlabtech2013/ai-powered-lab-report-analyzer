def parse_lab(content: str):
    results = []

    for line in content.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue  # skip empty or invalid lines

        test, value = line.split(":", 1)

        results.append({
            "test": test.strip(),
            "value": value.strip()
        })

    return results
