let historyStore = { runs: [] };
let trendChart = null;

function calculateRisk(currentRun) {

    let riskScore = 0;
    let scoringDetails = [];   // ← ADD THIS BACK

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

    return {
        riskScore,
        scoringDetails
    };
}

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
    const riskMeterFill = document.getElementById("riskMeterFill");
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
   
    let criticalMessages = [];
    let currentRun = {};    

    let deteriorationIndex = 0;

    const RISK_MODEL_VERSION = "v1.2";

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

        currentRun[testName] = {
            value: numericValue,
            reference: obs.reference_range
        };
    });

    const riskResult = calculateRisk(currentRun);
    let riskScore = riskResult.riskScore;
    let scoringDetails = riskResult.scoringDetails;

    // ===== Show Critical Alerts =====
    if (criticalMessages.length > 0) {
        alertBox.style.display = "block";
        alertBox.textContent = "CRITICAL: " + criticalMessages.join(" | ");
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

if (riskScore >= 3) {
    deteriorationIndex += 30;
}

    let wbcSlope = 0;
    let hgbSlope = 0;
    let rapidWBCChange = false;
    let rapidHGBChange = false;

currentRun._timestamp = new Date().toISOString();
historyStore.runs.push(currentRun);

// Trend-weighted deterioration
const wbcTrendValues = historyStore.runs
    .map(run => run["WBC"]?.value)
    .filter(v => v !== undefined);

const hgbTrendValues = historyStore.runs
    .map(run => run["HGB"]?.value)
    .filter(v => v !== undefined);

if (wbcTrendValues.length > 2) {
    wbcSlope = calculateSlope(wbcTrendValues);
    if (wbcSlope > 1) {
        deteriorationIndex += 20;
    }
}

if (hgbTrendValues.length > 2) {
    hgbSlope = calculateSlope(hgbTrendValues);
    if (hgbSlope < -0.5) {
        deteriorationIndex += 20;
    }
}

// ===== Interval Deterioration Detection =====
if (historyStore.runs.length >= 2) {

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
            deteriorationIndex += 40;
            rapidWBCChange = true;
            summaryDiv.textContent += " ⚠ Rapid WBC interval change detected.";
        }
    }

    if (prevHGB !== undefined && currHGB !== undefined) {

        const hgbChange = prevHGB !== 0
            ? ((currHGB - prevHGB) / prevHGB) * 100
            : 0;

        if (Math.abs(hgbChange) > 10) {
            deteriorationIndex += 30;
            rapidHGBChange = true;
            summaryDiv.textContent += " ⚠ Rapid hemoglobin interval change detected.";
        }
    }
}


deteriorationIndex = Math.min(deteriorationIndex, 100);

const probabilityResult = calculateDeteriorationProbability({
    riskScore,
    wbcSlope,
    hgbSlope,
    rapidWBCChange,
    rapidHGBChange
});

const probabilityPercent = Math.round(probabilityResult.probability * 100);

currentRun.meta = {
    riskScore: riskScore,
    riskLevel: riskLevel,
    modelVersion: RISK_MODEL_VERSION,
    deteriorationIndex: deteriorationIndex
};

updateTestSelector();
updateRunCount();
drawTrendChart();

if (deteriorationMeter && deteriorationLabel) {

    deteriorationMeter.style.width = deteriorationIndex + "%";
    deteriorationLabel.textContent = deteriorationIndex + "%";

    if (deteriorationIndex >= 70) {
        deteriorationMeter.style.backgroundColor = "#7f1d1d";
    }
    else if (deteriorationIndex >= 50) {
        deteriorationMeter.style.backgroundColor = "#dc2626";
    }
    else if (deteriorationIndex >= 30) {
        deteriorationMeter.style.backgroundColor = "#f59e0b";
    }
    else if (deteriorationIndex > 0) {
        deteriorationMeter.style.backgroundColor = "#84cc16";
    }
    else {
        deteriorationMeter.style.backgroundColor = "#16a34a";
    }
}
const probabilityPanel = document.getElementById("probabilityPanel");

if (probabilityPanel) {

    let confidenceLevel = "Low";

    if (probabilityPercent >= 70) confidenceLevel = "High";
    else if (probabilityPercent >= 40) confidenceLevel = "Moderate";

    probabilityPanel.innerHTML = `
        <strong>Predicted Deterioration Probability:</strong> ${probabilityPercent}%<br>
        <strong>Model Confidence:</strong> ${confidenceLevel}<br>
        <strong>Model Version:</strong> v1.3-beta
        <hr>
        <strong>Probability Contributors:</strong><br>
        ${probabilityResult.contributors.join("<br>")}
    `;
}

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

// ===== Deterioration Meter Visualization =====


function updateTestSelector() {
    const selector = document.getElementById("testSelector");
    selector.innerHTML = "";

    if (!historyStore.runs.length) return;

    // ✅ Find the first run that actually has test results
    const runWithTests = historyStore.runs.find(run => {
        if (!run) return false;

        return Object.keys(run).some(k => {
            if (k === "meta") return false;
            const v = run[k]?.value;
            return Number.isFinite(v); // allows 0 too
        });
    });

    if (!runWithTests) return;

    // ✅ Build dropdown options from that good run
    Object.keys(runWithTests).forEach(key => {
        if (key === "meta") return;

        const v = runWithTests[key]?.value;
        if (!Number.isFinite(v)) return;

        const option = document.createElement("option");
        option.value = key;
        option.textContent = key;
        selector.appendChild(option);
    });

    // ✅ Set a default selection and draw
    if (selector.options.length > 0) {
        selector.selectedIndex = 0;
        drawTrendChart();
    }

    selector.onchange = () => drawTrendChart();
}

function toggleDarkMode(){
  document.body.classList.toggle("dark");
  drawTrendChart();
}

function updateRunCount() {
    const runCount = document.getElementById("runCount");
    runCount.textContent = `Total Runs: ${historyStore.runs.length}`;
}

function downloadChartPNG(){
  const canvas = document.getElementById("trendChart");
  if (!canvas) return;
  const link = document.createElement("a");
  link.download = "trend_chart.png";
  link.href = canvas.toDataURL("image/png");
  link.click();
}

function drawTrendChart() {
    const canvas = document.getElementById("trendChart");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    const insightBox = document.getElementById("trendInsight");
    const banner = document.getElementById("trendAlertBanner"); // optional (we add HTML later)

    // ===== Helpers =====
    const clear = () => ctx.clearRect(0, 0, canvas.width, canvas.height);

    const formatTime = (iso) => {
        try {
            const d = new Date(iso);
            return d.toLocaleString([], { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });
        } catch {
            return "";
        }
    };

    // ===== Pull selection =====
    if (!historyStore.runs.length) {
        clear();
        if (insightBox) insightBox.textContent = "No runs available yet.";
        canvas.onmousemove = null;
        return;
    }

    const selector = document.getElementById("testSelector");
    const selectedTest = selector?.value;
    if (!selectedTest) return;

    // Keep alignment across runs (nulls kept)
    const series = historyStore.runs.map(run => {
        const v = run?.[selectedTest]?.value;
        return Number.isFinite(v) ? v : null;
    });

    // Filter for stats
    const values = series.filter(v => v !== null);
    if (!values.length) {
        clear();
        if (insightBox) insightBox.textContent = `No numeric values found for ${selectedTest}.`;
        canvas.onmousemove = null;
        return;
    }

    // Labels: timestamps if present, else Run #
    const labels = historyStore.runs.map((run, i) => run?._timestamp ? formatTime(run._timestamp) : `Run ${i + 1}`);

    const references = historyStore.runs.find(r => r?.[selectedTest]?.reference)?.[selectedTest]?.reference;

    // ===== Parse reference range once =====
    let refMin = null;
    let refMax = null;

    if (references && typeof references === "string") {
        const normalized = references.replace(/[–—]/g, "-");
        const cleaned = normalized.replace(/[^\d\.\-]/g, "");
        const parts = cleaned.split("-");

        if (parts.length === 2) {
            const min = parseFloat(parts[0]);
            const max = parseFloat(parts[1]);
            if (Number.isFinite(min) && Number.isFinite(max)) {
                refMin = min;
                refMax = max;
            }
        }
    }

    // ===== Layout =====
    clear();

    const padding = 60;
    const chartHeight = canvas.height - padding * 2;
    const chartWidth = canvas.width - padding * 2;

    let minVal = Math.min(...values);
    let maxVal = Math.max(...values);

    if (refMin !== null) minVal = Math.min(minVal, refMin);
    if (refMax !== null) maxVal = Math.max(maxVal, refMax);

    const buffer = (maxVal - minVal) === 0 ? 1 : (maxVal - minVal) * 0.12;
    const adjustedMin = minVal - buffer;
    const adjustedMax = maxVal + buffer;
    const scale = chartHeight / (adjustedMax - adjustedMin);

    const xForIndex = (i) => padding + (i * (chartWidth / (series.length - 1 || 1)));
    const yForValue = (val) => canvas.height - padding - ((val - adjustedMin) * scale);

    // ===== Persistent abnormal detection =====
    const abnormalHighCount = (refMax !== null) ? values.filter(v => v > refMax).length : 0;
    const abnormalLowCount  = (refMin !== null) ? values.filter(v => v < refMin).length : 0;

    const persistentHigh =
        values.length > 1 && refMax !== null && (abnormalHighCount / values.length) >= 0.7;

    const persistentLow =
        values.length > 1 && refMin !== null && (abnormalLowCount / values.length) >= 0.7;

    // ===== Reference band + limit lines =====
    if (refMin !== null && refMax !== null) {
        const yMin = yForValue(refMin);
        const yMax = yForValue(refMax);

        // band
        ctx.fillStyle = "rgba(34,197,94,0.12)";
        ctx.fillRect(padding, Math.min(yMin, yMax), chartWidth, Math.abs(yMax - yMin));

        // upper line
        ctx.strokeStyle = "#dc2626";
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(padding, yMax);
        ctx.lineTo(padding + chartWidth, yMax);
        ctx.stroke();

        // lower line
        ctx.strokeStyle = "#2563eb";
        ctx.beginPath();
        ctx.moveTo(padding, yMin);
        ctx.lineTo(padding + chartWidth, yMin);
        ctx.stroke();
    }

    // ===== Y-axis ticks (simple) =====
    ctx.fillStyle = "#111";
    ctx.font = "12px Arial";

    const ticks = 5;
    for (let t = 0; t <= ticks; t++) {
        const pct = t / ticks;
        const v = adjustedMax - (pct * (adjustedMax - adjustedMin));
        const y = padding + (pct * chartHeight);

        ctx.globalAlpha = 0.12;
        ctx.strokeStyle = "#111";
        ctx.beginPath();
        ctx.moveTo(padding, y);
        ctx.lineTo(padding + chartWidth, y);
        ctx.stroke();
        ctx.globalAlpha = 1;

        ctx.fillText(v.toFixed(1), 10, y + 4);
    }

    // ===== Trend line (glow) =====
    if (persistentHigh) { ctx.shadowColor = "#dc2626"; ctx.shadowBlur = 16; }
    else if (persistentLow) { ctx.shadowColor = "#2563eb"; ctx.shadowBlur = 16; }
    else { ctx.shadowBlur = 0; }

    ctx.strokeStyle = "#2563eb";
    ctx.lineWidth = 2.8;
    ctx.beginPath();

    let started = false;
    series.forEach((val, i) => {
        if (val === null) return;
        const x = xForIndex(i);
        const y = yForValue(val);

        if (!started) {
            ctx.moveTo(x, y);
            started = true;
        } else {
            ctx.lineTo(x, y);
        }
    });

    ctx.stroke();
    ctx.shadowBlur = 0;

    // ===== Data points (colored + bigger if abnormal) =====
    const points = []; // store for hover

    series.forEach((val, i) => {
        if (val === null) return;

        const x = xForIndex(i);
        const y = yForValue(val);

        let color = "#16a34a";
        let radius = 6;

        if (refMax !== null && val > refMax) { color = "#dc2626"; radius = 9; }
        else if (refMin !== null && val < refMin) { color = "#2563eb"; radius = 9; }

        ctx.beginPath();
        ctx.arc(x, y, radius, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();

        ctx.lineWidth = 2;
        ctx.strokeStyle = "#ffffff";
        ctx.stroke();

        points.push({ x, y, val, label: labels[i], color });
    });

    // ===== X labels (sparse to avoid clutter) =====
    ctx.fillStyle = "#111";
    ctx.font = "11px Arial";
    const step = Math.ceil(series.length / 6);
    labels.forEach((lab, i) => {
        if (i % step !== 0 && i !== labels.length - 1) return;
        const x = xForIndex(i);
        ctx.fillText(lab, x - 25, canvas.height - 18);
    });

    // ===== Velocity / trend slope =====
    const firstVal = values[0];
    const lastVal = values[values.length - 1];
    const delta = lastVal - firstVal;
    const deltaPct = firstVal !== 0 ? (delta / firstVal) * 100 : 0;

    const velocity = (values.length > 1) ? (delta / (values.length - 1)) : 0;

    // ===== Alert banner =====
    let alertText = "";
    let alertType = ""; // "danger" | "warn" | "ok"

    if (persistentHigh) {
        alertText = `Persistent HIGH trend detected for ${selectedTest}.`;
        alertType = "danger";
    } else if (persistentLow) {
        alertText = `Persistent LOW trend detected for ${selectedTest}.`;
        alertType = "warn";
    } else if (Math.abs(deltaPct) > 20 && values.length > 1) {
        alertText = `Rapid change detected: ${deltaPct.toFixed(1)}% over ${values.length} results.`;
        alertType = "warn";
    } else {
        alertText = `Trend appears stable.`;
        alertType = "ok";
    }

    if (banner) {
        banner.textContent = alertText;
        banner.className = `trend-banner ${alertType}`;
    }

    // ===== Insight text =====
    let insight = "";

    if (persistentHigh) {
        insight = `${selectedTest} remains persistently elevated across ${values.length} data points. `;
    } else if (persistentLow) {
        insight = `${selectedTest} remains persistently below range across ${values.length} data points. `;
    } else if (values.length > 1) {
        insight = `${selectedTest} changed ${delta >= 0 ? "up" : "down"} by ${Math.abs(delta).toFixed(2)} (${Math.abs(deltaPct).toFixed(1)}%). `;
    } else {
        insight = `Only one value available for ${selectedTest}. `;
    }

    insight += `Velocity: ${velocity.toFixed(2)} per run.`;

    if (insightBox) {
        insightBox.textContent = insight;
        insightBox.className = "summary-box " + (persistentHigh ? "high-row" : persistentLow ? "low-row" : "");
    }

    // ===== Hover tooltip (NO redraw recursion) =====
    canvas.onmousemove = function (event) {
        const rect = canvas.getBoundingClientRect();
        const mx = event.clientX - rect.left;
        const my = event.clientY - rect.top;

        // redraw base clean (safe: calling this would recurse)
        // Instead: just clear tooltip area by re-drawing the whole chart ONCE via requestAnimationFrame
        // We'll do a lightweight approach: detect hover; if no hover, do nothing.
        let hovered = null;

        for (const p of points) {
            const d = Math.sqrt((mx - p.x) ** 2 + (my - p.y) ** 2);
            if (d < 10) { hovered = p; break; }
        }

        // If no hover, just change cursor and exit
        canvas.style.cursor = hovered ? "pointer" : "default";
        if (!hovered) return;

        // Draw tooltip box
        ctx.save();
        ctx.font = "13px Arial";
        const text = `${selectedTest}: ${hovered.val} (${hovered.label})`;
        const pad = 8;
        const w = ctx.measureText(text).width + pad * 2;
        const h = 28;

        const tx = Math.min(hovered.x + 12, canvas.width - w - 10);
        const ty = Math.max(hovered.y - 40, 10);

        ctx.globalAlpha = 0.92;
        ctx.fillStyle = "#111";
        ctx.fillRect(tx, ty, w, h);

        ctx.globalAlpha = 1;
        ctx.fillStyle = "#fff";
        ctx.fillText(text, tx + pad, ty + 19);
        ctx.restore();
   };
}          // ✅ CLOSES drawTrendChart

function clearHistory() {
    historyStore.runs = [];
    const runCount = document.getElementById("runCount");
    const selector = document.getElementById("testSelector");
    if (runCount) runCount.textContent = "";
    if (selector) selector.innerHTML = "";
    const canvas = document.getElementById("trendChart");
    if (canvas) canvas.onmousemove = null;
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

    let totalChange = 0;

    for (let i = 1; i < values.length; i++) {
        totalChange += values[i] - values[i - 1];
    }

    return totalChange / (values.length - 1);
}

function calculateDeteriorationProbability(inputs) {

    let probability = 0;
    let contributors = [];

    // Risk contribution
    const riskContribution = inputs.riskScore * 0.10;
    probability += riskContribution;
    if (riskContribution > 0)
        contributors.push(`+${Math.round(riskContribution * 100)}% Risk Score contribution`);

    // Trend contribution
    if (inputs.wbcSlope > 1) {
        probability += 0.15;
        contributors.push("+15% Upward WBC trend");
    }

    if (inputs.hgbSlope < -0.5) {
        probability += 0.15;
        contributors.push("+15% Downward HGB trend");
    }

    // Interval contribution
    if (inputs.rapidWBCChange) {
        probability += 0.20;
        contributors.push("+20% Rapid WBC interval change");
    }

    if (inputs.rapidHGBChange) {
        probability += 0.15;
        contributors.push("+15% Rapid HGB interval change");
    }

    probability = Math.min(probability, 1);

    return {
        probability,
        contributors
    };
}

function renderTrendChart(testName, values) {
    const canvas = document.getElementById("trendChart");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");

    if (trendChart) {
        trendChart.destroy();
    }

    if (!values || values.length === 0) {
        return;
    }

    const labels = values.map((_, index) => `Run ${index + 1}`);

    trendChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: labels,
            datasets: [{
                label: testName,
                data: values,
                borderWidth: 2,
                tension: 0.3,
                fill: false,
                pointRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });
}

// ===============================
// DOWNLOAD PDF (WITH CHART IMAGE)
// ===============================
async function downloadPDF() {
    const canvas = document.getElementById("trendChart");

    let chartImage = null;

    if (canvas) {
        chartImage = canvas.toDataURL("image/png");
    }

    const response = await fetch("/download/pdf", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ chartImage })
    });

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = "AI_Lab_Intelligence_Report.pdf";
    a.click();
}
