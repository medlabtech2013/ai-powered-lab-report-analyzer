# 🏥 CliniSight AI™  
### Clinical Intelligence Platform  
**Powered by PrecisionPoint Medical Center**

---

## 🚀 Overview

CliniSight AI™ is a clinical intelligence engine that transforms structured laboratory data into actionable risk insights.

Built to parse HL7 laboratory messages and generate executive-level clinical reports, the platform delivers:

- Risk scoring & deterioration indexing  
- Feature importance analysis (rule driver transparency)  
- Confidence interval estimation  
- Trend visualization  
- FHIR-compatible JSON export  
- SHA-256 digital authenticity verification  
- QR-based verification portal  
- Persistent report storage with SQLite  

This system demonstrates enterprise-grade clinical reporting architecture.

---

## 🧠 Core Capabilities

### 🔎 HL7 Parsing Engine
Parses structured lab results and extracts:
- Patient demographics
- Observations
- Reference ranges
- Flags

### 📊 Risk Intelligence Engine
- WBC/HGB rule-based scoring
- Deterioration index calculation
- Probability estimation
- Confidence interval generation
- Feature importance (driver contributions)

### 📄 Executive PDF Reporting
- Landscape executive layout
- Hospital branding
- Accreditation badge
- Risk banner (color-coded)
- Feature importance table
- Model performance metrics
- Digital authenticity signature
- Embedded QR verification
- Trend visualization

### 🔐 Verification Portal
Every report includes:
- SHA-256 hash
- Persistent storage in SQLite
- Verification endpoint
- Official branded verification page

---

## 🏗 Architecture

FastAPI backend  
SQLite persistent registry  
ReportLab PDF engine  
QR verification  
Static asset branding  
HL7 parser module  

---

## 📂 Project Structure

```
app/
    main.py
parser.py
frontend/
static/assets/
data/reports.db
```

---

## 🧪 Example Workflow

1. Upload HL7 file
2. Analyze lab results
3. Generate executive PDF
4. Scan QR code
5. Verify authenticity via web portal

---

## 🔐 Digital Integrity

Every generated report includes:

- Unique Report ID
- SHA-256 signature
- Database-stored snapshot
- Recomputed hash verification
- QR-based authenticity validation

This ensures tamper-resistant clinical reporting.

---

## ⚙️ Deployment

### Local

```bash
uvicorn app.main:app --reload
```

### Production (Render)

Deploy as FastAPI service with persistent disk for SQLite storage.

---

## 📈 Future Roadmap

- Logistic regression risk model
- Feature importance bar visualization
- Trend persistence database
- User authentication & audit logs
- Clinical validation pipeline
- FHIR export schema expansion

---

## ⚠ Disclaimer

CliniSight AI™ is a clinical decision support prototype.  
It is not a substitute for physician judgment.  
Clinical validation is required before real-world deployment.

---

## 🏢 Developed By

**Branden Bryant**  
Clinical Informatics & Healthcare Data Analyst  
AI Systems & Risk Modeling  

CliniSight AI™ Clinical Intelligence Platform  
© 2026 PrecisionPoint Medical Center
