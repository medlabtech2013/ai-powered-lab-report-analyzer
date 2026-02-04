# AI-Powered Lab Report Analyzer

## Overview
A healthcare-focused backend application that analyzes laboratory reports,
flags abnormal values, and generates structured clinical summaries using
FHIR-compatible data models.

## Key Features
- Upload raw lab reports (TXT)
- Detect abnormal lab values using clinical thresholds
- Generate human-readable interpretations
- Output FHIR Observation resources
- REST API built with FastAPI

## Technologies
- Python
- FastAPI
- Uvicorn
- Clinical rule-based logic
- FHIR JSON structure

## Example Input
WBC 14.2
HGB 10.1
PLT 220

## Example Output
- Elevated WBC
- Low Hemoglobin
- Normal Platelet Count
- FHIR Observation Bundle

## Disclaimer
For educational and portfolio demonstration purposes only.
Not intended for clinical use.

