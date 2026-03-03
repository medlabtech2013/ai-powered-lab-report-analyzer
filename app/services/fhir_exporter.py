def generate_fhir_bundle(patient, dob, mrn, observations):
    return {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": mrn,
                    "name": [{"text": patient}],
                    "birthDate": dob
                }
            }
        ] + [
            {
                "resource": {
                    "resourceType": "Observation",
                    "status": "final",
                    "code": {
                        "coding": [{"code": o["loinc"], "display": o["test"]}]
                    },
                    "valueString": o["value"]
                }
            }
            for o in observations
        ]
    }
