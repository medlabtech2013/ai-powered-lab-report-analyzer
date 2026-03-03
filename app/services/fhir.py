def build_fhir_bundle(observations):
    entries = []

    for obs in observations:
        entry = {
            "resource": {
                "resourceType": "Observation",
                "status": "final",
                "code": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": obs.get("loinc", "unknown"),
                            "display": obs["test"]
                        }
                    ],
                    "text": obs["test"]
                },
                "valueQuantity": {
                    "value": obs["value"],
                    "unit": obs["units"]
                },
                "referenceRange": [
                    {
                        "low": {"value": float(obs["reference_range"].split("-")[0])},
                        "high": {"value": float(obs["reference_range"].split("-")[1])}
                    }
                ],
                "interpretation": [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                                "code": obs["flag"]
                            }
                        ]
                    }
                ]
            }
        }

        entries.append(entry)

    return {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": entries
    }

