let historyStore = {
    runs: []
};

async function analyze() {
    const deteriorationMeter = document.getElementById("deteriorationMeter");
    const deteriorationLabel = document.getElementById("deteriorationLabel");

    if (deteriorationMeter && deteriorationLabel) {
        deteriorationMeter.style.width = "0%";
        deteriorationLabel.textContent = "0%";
}
    const fileInput = document.getElementById("fileInput");
    const summaryDiv = document.getElementById("summary");
    const tbody = document.getElementById("results");
    const alertBox = document.getElementById("criticalAlert");
    const riskBadge = document.getElementById("riskBadge");
    const severityBanner = document.getElementById("severityBanner");
    severityBanner.textContent = "";
    severityBanner.style.backgroundColor = "transparent";
    severityBanner.style.color = "black";

    if (!fileInput.files.length) {
        alert("Please upload a file first.");
        return;
    }

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    const response = await fetch("/analyze", {
        method: "POST",
        body: formData
    });

    const data = await response.json();

    summaryDiv.textContent = data.summary || "—";
    tbody.innerHTML = "";

    alertBox.style.display = "none";
    alertBox.textContent = "";
    riskBadge.textContent = "";
   
    const riskMeterFill = document.getElementById("riskMeterFill");
    if (riskMeterFill) {
        riskMeterFill.style.width = "0%";
}


    let criticalMessages = [];
    let currentRun = {};

    const RISK_MODEL_VERSION = "v1.2";
    let scoringDetails = [];

    // ===== Process Observations =====
    data.observations.forEach(obs => {

        const row = document.createElement("tr");
        const cleanFlag = String(obs.flag || "").trim().toUpperCase();
        const testName = String(obs.test || "").trim().toUpperCase();
        const numericValue = Number(obs.value);

        // Critical thresholds
        if (testName === "WBC" && numericValue > 20) {
            criticalMessages.push("WBC exceeds 20 — urgent evaluation recommended.");
        }

        if (testName === "HGB" && numericValue < 7) {
            criticalMessages.push("Hemoglobin below 7 g/dL — possible transfusion threshold.");
        }

        if (cleanFlag === "H") row.classList.add("high-row");
        if (cleanFlag === "L") row.classList.add("low-row");

        row.innerHTML = `
            <td>${obs.test}</td>
            <td>${obs.value}</td>
            <td>${obs.units}</td>
            <td>${obs.reference_range || ""}</td>
            <td>${renderFlag(obs.flag)}</td>
            <td>${obs.loinc || ""}</td>
        `;

        tbody.appendChild(row);

        currentRun[obs.test] = {
            value: numericValue,
            reference: obs.reference_range
        };
    });

    // ===== Show Critical Alerts =====
    if (criticalMessages.length > 0) {
        alertBox.style.display = "block";
        alertBox.textContent = "CRITICAL: " + criticalMessages.join(" | ");
    }

    // ===== Risk Scoring =====
    let riskScore = 0;

if (currentRun["WBC"]?.value > 20) {
    riskScore += 2;
    scoringDetails.push("WBC > 20 (+2)");
}

if (currentRun["HGB"]?.value < 7) {
    riskScore += 2;
    scoringDetails.push("HGB < 7 (+2)");
}

if (currentRun["WBC"]?.value > 11) {
    riskScore += 1;
    scoringDetails.push("WBC > 11 (+1)");
}

if (currentRun["HGB"]?.value < 12) {
    riskScore += 1;
    scoringDetails.push("HGB < 12 (+1)");
}

let riskLevel = "LOW";

if (riskScore >= 3) {
    riskLevel = "HIGH";
    riskBadge.style.color = "#b91c1c";
}
else if (riskScore === 2) {
    riskLevel = "MODERATE";
    riskBadge.style.color = "#f59e0b";
}
else {
    riskBadge.style.color = "#16a34a";
}

riskBadge.textContent =
    `Risk Level: ${riskLevel} (Score: ${riskScore})`;



// Scale max score to 5 for visualization
const maxVisualScore = 5;
const normalized = Math.min(riskScore, maxVisualScore);
const percent = (normalized / maxVisualScore) * 100;

if (riskMeterFill) {
    riskMeterFill.style.width = percent + "%";

    if (riskScore >= 4) {
        riskMeterFill.style.backgroundColor = "#7f1d1d";
    }
    else if (riskScore === 3) {
        riskMeterFill.style.backgroundColor = "#dc2626";
    }
    else if (riskScore === 2) {
        riskMeterFill.style.backgroundColor = "#f59e0b";
    }
    else if (riskScore === 1) {
        riskMeterFill.style.backgroundColor = "#84cc16";
    }
    else {
        riskMeterFill.style.backgroundColor = "#16a34a";
    }
}

if (riskScore >= 4) {
    riskMeterFill.style.backgroundColor = "#7f1d1d"; // dark red
}
else if (riskScore === 3) {
    riskMeterFill.style.backgroundColor = "#dc2626"; // red
}
else if (riskScore === 2) {
    riskMeterFill.style.backgroundColor = "#f59e0b"; // amber
}
else if (riskScore === 1) {
    riskMeterFill.style.backgroundColor = "#84cc16"; // yellow-green
}
else {
    riskMeterFill.style.backgroundColor = "#16a34a"; // green
}

    // ===== Severity Banner =====
if (riskScore >= 3) {
    severityBanner.textContent = "🔴 High Clinical Concern";
    severityBanner.style.backgroundColor = "#fee2e2";
}
else if (riskScore === 2) {
    severityBanner.textContent = "🟡 Moderate Clinical Concern";
    severityBanner.style.backgroundColor = "#fef3c7";
}
else {
    severityBanner.textContent = "🟢 Clinically Stable";
    severityBanner.style.backgroundColor = "#dcfce7";
}

if (scoringDetails.length > 0) {
    summaryDiv.textContent +=
        ` [Model ${RISK_MODEL_VERSION}: ${scoringDetails.join(", ")}]`;
}

    // ===== Sepsis Pattern Detection =====
    const wbc = currentRun["WBC"]?.value;
    const hgb = currentRun["HGB"]?.value;

    if (wbc !== undefined && hgb !== undefined) {

        const abnormalWBC = (wbc > 12 || wbc < 4);
        const anemia = (hgb < 12);

        if (abnormalWBC && anemia) {
            summaryDiv.textContent += 
                " ⚠ Clinical pattern concerning for systemic inflammatory response.";
        }
    }

    // ===== Pattern Logic =====
    if (wbc > 11 && hgb < 12) {
        summaryDiv.textContent += " Pattern: leukocytosis + anemia detected.";
    }

    currentRun.meta = {
    riskScore: riskScore,
    riskLevel: riskLevel,
    modelVersion: RISK_MODEL_VERSION,
    deteriorationIndex: deteriorationIndex || 0
};

    historyStore.runs.push(currentRun);

// ===== Interval Deterioration Detection =====
if (historyStore.runs.length > 1) {

    calculate previous values
    calculate current values

    calculate wbcChange
    calculate hgbChange

    THEN calculate deteriorationIndex
}

    const previousRun = historyStore.runs[historyStore.runs.length - 2];

    const prevWBC = previousRun["WBC"]?.value;
    const prevHGB = previousRun["HGB"]?.value;

    const currWBC = currentRun["WBC"]?.value;
    const currHGB = currentRun["HGB"]?.value;

    if (prevWBC !== undefined && currWBC !== undefined) {
        const wbcChange = prevWBC !== 0
    ? ((currWBC - prevWBC) / prevWBC) * 100
    : 0;

        if (Math.abs(wbcChange) > 15) {
            summaryDiv.textContent +=
                " ⚠ Rapid WBC interval change detected.";

            severityBanner.textContent = "🚨 Acute Interval Deterioration";
            severityBanner.style.backgroundColor = "#7f1d1d";
            severityBanner.style.color = "white";
        }
    }

    if (prevHGB !== undefined && currHGB !== undefined) {
        const hgbChange = prevHGB !== 0
    ? ((currHGB - prevHGB) / prevHGB) * 100
    : 0;

        if (Math.abs(hgbChange) > 10) {
            summaryDiv.textContent +=
                " ⚠ Rapid hemoglobin interval change detected.";

            severityBanner.textContent = "🚨 Acute Interval Deterioration";
            severityBanner.style.backgroundColor = "#7f1d1d";
            severityBanner.style.color = "white";
        }
    }
}   // closes interval detection

updateTestSelector();
updateRunCount();
drawTrendChart();

}   // ✅ THIS closes analyze()

function renderFlag(flag) {
    if (!flag) return "";

    const cleanFlag = String(flag).trim().toUpperCase();

    if (cleanFlag === "H")
        return `<span class="flag-badge flag-high">H</span>`;

    if (cleanFlag === "L")
        return `<span class="flag-badge flag-low">L</span>`;

    return "";
}

// ===== Predictive Deterioration Index =====
let deteriorationIndex = 0;

if (historyStore.runs.length > 1) {

    const wbcHistory = historyStore.runs
        .map(run => run["WBC"]?.value)
        .filter(v => v !== undefined);

    const hgbHistory = historyStore.runs
        .map(run => run["HGB"]?.value)
        .filter(v => v !== undefined);

    const wbcSlope = calculateSlope(wbcHistory);
    const hgbSlope = calculateSlope(hgbHistory);

    // Weighting logic
    if (wbcSlope > 1) deteriorationIndex += 30;
    if (wbcSlope > 2) deteriorationIndex += 20;

    if (hgbSlope < -0.5) deteriorationIndex += 25;
    if (hgbSlope < -1) deteriorationIndex += 25;

    // Cap index
    deteriorationIndex = Math.min(deteriorationIndex, 100);

    if (deteriorationIndex >= 50) {
        summaryDiv.textContent +=
            ` 🚨 Predictive deterioration risk elevated (${deteriorationIndex}%).`;

        severityBanner.textContent = "⚠ Predictive Clinical Deterioration";
        severityBanner.style.backgroundColor = "#7c2d12";
        severityBanner.style.color = "white";
    }
}

// ===== Deterioration Meter Visualization =====
const deteriorationMeter = document.getElementById("deteriorationMeter");
const deteriorationLabel = document.getElementById("deteriorationLabel");

if (deteriorationMeter && deteriorationLabel) {

    deteriorationMeter.style.width = deteriorationIndex + "%";
    deteriorationLabel.textContent = deteriorationIndex + "%";

    if (deteriorationIndex >= 70) {
        deteriorationMeter.style.backgroundColor = "#7f1d1d"; // dark red
    }
    else if (deteriorationIndex >= 50) {
        deteriorationMeter.style.backgroundColor = "#dc2626"; // red
    }
    else if (deteriorationIndex >= 30) {
        deteriorationMeter.style.backgroundColor = "#f59e0b"; // amber
    }
    else if (deteriorationIndex > 0) {
        deteriorationMeter.style.backgroundColor = "#84cc16"; // yellow-green
    }
    else {
        deteriorationMeter.style.backgroundColor = "#16a34a"; // green
    }
}

function updateTestSelector() {
    const selector = document.getElementById("testSelector");

    if (!historyStore.runs.length) return;

    const tests = Object.keys(historyStore.runs[0]);

    selector.innerHTML = "";

    tests.forEach(test => {
        const option = document.createElement("option");
        option.value = test;
        option.textContent = test;
        selector.appendChild(option);
    });
}

function updateRunCount() {
    const runCount = document.getElementById("runCount");
    runCount.textContent = `Total Runs: ${historyStore.runs.length}`;
}

function drawTrendChart() {
    const canvas = document.getElementById("trendChart");
    const ctx = canvas.getContext("2d");
    const insightBox = document.getElementById("trendInsight");

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (!historyStore.runs.length) return;

    const selector = document.getElementById("testSelector");
    const selectedTest = selector.value;

    const values = historyStore.runs
        .map(run => run[selectedTest]?.value)
        .filter(val => val !== undefined);

    const references = historyStore.runs[0][selectedTest]?.reference;

    if (!values.length) return;

    const padding = 50;
    const chartHeight = canvas.height - padding * 2;
    const chartWidth = canvas.width - padding * 2;

    const minVal = Math.min(...values);
    const maxVal = Math.max(...values);

    const buffer = (maxVal - minVal) === 0 ? 1 : (maxVal - minVal) * 0.1;

    const adjustedMin = minVal - buffer;
    const adjustedMax = maxVal + buffer;

    const scale = chartHeight / (adjustedMax - adjustedMin);

    // 🔹 Draw Reference Range Band
    if (references) {
        const parts = references.split("-");
        if (parts.length === 2) {
            const refMin = parseFloat(parts[0]);
            const refMax = parseFloat(parts[1]);

            const yRefMin = canvas.height - padding - ((refMin - minVal) * scale);
            const yRefMax = canvas.height - padding - ((refMax - minVal) * scale);

            ctx.fillStyle = "rgba(34,197,94,0.15)";
            ctx.fillRect(
                padding,
                Math.min(yRefMin, yRefMax),
                chartWidth,
                Math.abs(yRefMax - yRefMin)
            );
        }
    }

    ctx.strokeStyle = "#2563eb";
    ctx.lineWidth = 2;
    ctx.beginPath();

    values.forEach((val, i) => {
        const x = padding + (i * (chartWidth / (values.length - 1 || 1)));
        const y = canvas.height - padding - ((val - adjustedMin) * scale);

        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);

        ctx.beginPath();
        ctx.arc(x, y, 5, 0, 2 * Math.PI);
        ctx.fillStyle = "#2563eb";
        ctx.fill();
    });

    ctx.stroke();

    // 🔹 Run Labels
    ctx.fillStyle = "#000";
    values.forEach((_, i) => {
        const x = padding + (i * (chartWidth / (values.length - 1 || 1)));
        ctx.fillText(`Run ${i + 1}`, x - 15, canvas.height - 15);
    });

        // 🔹 Advanced Clinical Insight Logic

    let insight = "";
    let severityClass = "";

    const firstVal = values[0];
    const lastVal = values[values.length - 1];

    const deltaPercent = ((lastVal - firstVal) / firstVal) * 100;

    const reference = historyStore.runs[0][selectedTest]?.reference;

    let refMin = null;
    let refMax = null;

    if (reference && reference.includes("-")) {
        const parts = reference.split("-");
        refMin = parseFloat(parts[0]);
        refMax = parseFloat(parts[1]);
    }

    const persistentHigh = values.every(v => refMax !== null && v > refMax);
    const persistentLow = values.every(v => refMin !== null && v < refMin);

    if (persistentHigh) {
        insight = `${selectedTest} remains persistently elevated across ${values.length} runs. Consider inflammatory, infectious, or hematologic causes.`;
        severityClass = "high-row";
    }
    else if (persistentLow) {
        insight = `${selectedTest} remains persistently below reference range across ${values.length} runs. Consider anemia, marrow suppression, or chronic disease.`;
        severityClass = "low-row";
    }
    else if (Math.abs(deltaPercent) > 10 && values.length > 1) {
        const direction = deltaPercent > 0 ? "increased" : "decreased";
        insight = `${selectedTest} has ${direction} by ${Math.abs(deltaPercent).toFixed(1)}% across ${values.length} runs. Significant interval change detected.`;
        severityClass = "";
    }
    else if (values.length > 1) {
        insight = `${selectedTest} shows stable values across ${values.length} runs with no significant interval change.`;
        severityClass = "";
    }
    else {
        insight = `Only one run available for ${selectedTest}.`;
    }

    insightBox.textContent = insight;
    insightBox.className = "summary-box " + severityClass;
    }

function clearHistory() {
    historyStore.runs = [];
    document.getElementById("runCount").textContent = "";
    document.getElementById("testSelector").innerHTML = "";
    drawTrendChart();
}

function downloadPDF() {
    window.location.href = "/download/pdf";
}

function downloadFHIR() {
    window.location.href = "/download/fhir";
}

function calculateSlope(values) {
    if (values.length < 2) return 0;

    const first = values[0];
    const last = values[values.length - 1];

    return (last - first) / values.length;
}
