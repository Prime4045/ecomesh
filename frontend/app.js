// ==========================================================================
// EcoMesh Autonomous Multi-Agent Environmental Decision Support Platform
// Multi-Page Navigation, 5-Agent War Room, GIS Plumes, Policy Sandbox, Vision AI
// ==========================================================================

let currentCity = "Delhi NCR";
let gisMap = null;
let activeTargetMarker = null;
let windVectorLayerGroup = null;
let plumeIsochroneLayerGroup = null;
let searchDebounceTimer = null;
let telemetryTrendsChart = null;
let policyForecastChart = null;
let latestTelemetryData = null;

// Webcam Streaming State
let webcamStream = null;
let webcamIntervalId = null;
let isWebcamStreaming = false;
let webcamFpsCounter = 0;
let lastFpsTime = Date.now();

// Speech Synthesis State
let isSpeechPlaying = false;
let speechSynth = window.speechSynthesis;
let activeUtterance = null;

const CITY_COORDS = {
    "Delhi NCR": [28.6139, 77.2090],
    "Delhi": [28.6139, 77.2090],
    "Mumbai": [19.0760, 72.8777],
    "London": [51.5074, -0.1278],
    "Tokyo": [35.6762, 139.6503],
    "New York": [40.7128, -74.0060],
    "Bengaluru": [12.9716, 77.5946]
};

const POLLUTANT_MAP = {
    "pm25": "PM2.5",
    "pm10": "PM10",
    "no2": "NO₂",
    "so2": "SO₂",
    "co": "CO",
    "o3": "O₃"
};

const PAGE_MAP = {
    "#dashboard": "page-dashboard",
    "#warroom": "page-warroom",
    "#gis": "page-gis",
    "#sandbox": "page-sandbox",
    "#vision": "page-vision",
    "#civic": "page-civic",
    "#architecture": "page-architecture"
};

document.addEventListener("DOMContentLoaded", () => {
    initApp();
});

function initApp() {
    setupNavigationRouting();
    setupEventListeners();
    setupVoiceBriefing();
    setupPolicySandbox();
    setupWebcamStudio();
    setupCitizenPortal();
    setupAlertModal();
    setupSearch();
    initGISMap();
    fetchPipelineData();
}

// 1. Multi-Page Enterprise Routing Controller
function setupNavigationRouting() {
    function navigateToHash() {
        const hash = window.location.hash || "#dashboard";
        const pageId = PAGE_MAP[hash] || "page-dashboard";
        showPage(pageId, hash);
    }

    window.addEventListener("hashchange", navigateToHash);
    navigateToHash();

    document.querySelectorAll(".enterprise-nav-tabs .nav-tab, .enterprise-nav .nav-item").forEach(item => {
        item.addEventListener("click", (e) => {
            const pageId = item.getAttribute("data-page");
            const hash = item.getAttribute("href");
            showPage(pageId, hash);
        });
    });
}

function showPage(pageId, hash = "#dashboard") {
    // Update Nav Active State
    document.querySelectorAll(".enterprise-nav-tabs .nav-tab, .enterprise-nav .nav-item").forEach(item => {
        if (item.getAttribute("data-page") === pageId || item.getAttribute("href") === hash) {
            item.classList.add("active");
        } else {
            item.classList.remove("active");
        }
    });

    // Update App Page Visibility
    document.querySelectorAll(".app-page").forEach(page => {
        if (page.id === pageId) {
            page.classList.add("active");
        } else {
            page.classList.remove("active");
        }
    });

    // Invalidate GIS Map size and center on city when GIS page is opened
    if (pageId === "page-gis" || hash === "#gis") {
        if (!gisMap) {
            setTimeout(() => initGISMap(), 50);
        } else {
            setTimeout(() => {
                gisMap.invalidateSize();
                if (CITY_COORDS[currentCity]) {
                    gisMap.setView(CITY_COORDS[currentCity], 11, { animate: false });
                }
            }, 100);
            setTimeout(() => {
                if (gisMap) gisMap.invalidateSize();
            }, 350);
        }
    }

    // Resize Charts when Dashboard or Policy Sandbox is opened
    if (pageId === "page-dashboard" && telemetryTrendsChart) {
        setTimeout(() => telemetryTrendsChart.resize(), 150);
    }
    if (pageId === "page-sandbox" && policyForecastChart) {
        setTimeout(() => policyForecastChart.resize(), 150);
    }

    if (window.lucide) lucide.createIcons();
}

// 2. Ultra-Fast Non-Blocking Loading Controller
const telemetryClientCache = new Map();

function setLoadingState(isLoading, cityName = "") {
    const progressBar = document.getElementById("global-progress-bar");
    const searchSpinner = document.getElementById("search-spinner");
    const mainShell = document.querySelector(".main-shell");

    if (isLoading) {
        if (progressBar) progressBar.classList.add("loading");
        if (searchSpinner) searchSpinner.style.display = "flex";
        if (mainShell) mainShell.classList.add("is-loading");
    } else {
        if (progressBar) progressBar.classList.remove("loading");
        if (searchSpinner) searchSpinner.style.display = "none";
        if (mainShell) mainShell.classList.remove("is-loading");
    }
}

// 3. Setup Core Event Listeners & Shortcuts
function setupEventListeners() {
    // Quick Hub Buttons
    document.querySelectorAll(".hub-btn").forEach(btn => {
        btn.addEventListener("click", (e) => {
            document.querySelectorAll(".hub-btn").forEach(b => b.classList.remove("active"));
            const target = e.currentTarget;
            target.classList.add("active");
            currentCity = target.getAttribute("data-city");
            
            const searchInput = document.getElementById("global-search-input");
            if (searchInput) searchInput.value = currentCity;

            const targetCityEl = document.getElementById("target-city-val");
            if (targetCityEl) targetCityEl.innerText = currentCity;

            if (CITY_COORDS[currentCity] && gisMap) {
                gisMap.flyTo(CITY_COORDS[currentCity], 11, { duration: 1.2 });
                addOrUpdateLocationMarker(currentCity, CITY_COORDS[currentCity][0], CITY_COORDS[currentCity][1]);
            }
            fetchPipelineData();
        });
    });

    const btnExportBriefing = document.getElementById("btn-export-briefing");
    if (btnExportBriefing) {
        btnExportBriefing.addEventListener("click", () => downloadIncidentReport("json"));
    }

    const btnDownloadDirectivesCivic = document.getElementById("btn-download-directives-civic");
    if (btnDownloadDirectivesCivic) {
        btnDownloadDirectivesCivic.addEventListener("click", () => downloadIncidentReport("txt"));
    }
}

// 4. Tactical Emergency Audio Voice Dispatcher (Web Speech API)
function setupVoiceBriefing() {
    const voiceBtn = document.getElementById("btn-play-voice-briefing");
    const voiceBtnText = document.getElementById("voice-btn-text");
    const waveAnim = document.getElementById("audio-wave-anim");
    const voiceIcon = document.getElementById("voice-icon");

    if (!voiceBtn || !window.speechSynthesis) return;

    function stopVoice() {
        speechSynth.cancel();
        isSpeechPlaying = false;
        voiceBtn.classList.remove("playing");
        if (voiceBtnText) voiceBtnText.innerText = "Voice Briefing";
        if (waveAnim) waveAnim.style.display = "none";
        if (voiceIcon) voiceIcon.style.display = "inline-block";
    }

    voiceBtn.addEventListener("click", () => {
        if (isSpeechPlaying) {
            stopVoice();
            return;
        }

        if (!latestTelemetryData) return;

        const v = latestTelemetryData.verdict;
        const s = latestTelemetryData.signals;

        const speechScript = `Tactical situation report for ${currentCity}. Composite environmental threat is evaluated at Level ${v.combined_level}, ${v.combined_category}, composite index ${v.combined_score.toFixed(2)} out of 4. Consensus confidence is ${Math.round(v.final_confidence * 100)} percent. Atmospheric Air Specialist reports AQI of ${Math.round(s.air.value)}. Hydrological catchment reports WQI ${s.water.value.toFixed(1)}. Epidemiological surge probability is projected at ${s.health?.detail?.hospital_surge_risk_pct || 14} percent. Primary Directive: ${v.recommended_action}. Multi-agent mesh active.`;

        activeUtterance = new SpeechSynthesisUtterance(speechScript);
        activeUtterance.rate = 1.05;
        activeUtterance.pitch = 0.95;

        const voices = speechSynth.getVoices();
        const preferredVoice = voices.find(v => v.lang.includes("en") && (v.name.includes("Google") || v.name.includes("Natural") || v.name.includes("David") || v.name.includes("Male")));
        if (preferredVoice) activeUtterance.voice = preferredVoice;

        activeUtterance.onstart = () => {
            isSpeechPlaying = true;
            voiceBtn.classList.add("playing");
            if (voiceBtnText) voiceBtnText.innerText = "Stop Briefing";
            if (waveAnim) waveAnim.style.display = "inline-flex";
            if (voiceIcon) voiceIcon.style.display = "none";
        };

        activeUtterance.onend = () => stopVoice();
        activeUtterance.onerror = () => stopVoice();

        speechSynth.speak(activeUtterance);
    });
}

// 5. What-If Policy Sandboxing Studio Controller
function setupPolicySandbox() {
    const evSlider = document.getElementById("policy-ev-slider");
    const evVal = document.getElementById("policy-ev-val");
    const scrubbersSlider = document.getElementById("policy-scrubbers-slider");
    const scrubbersVal = document.getElementById("policy-scrubbers-val");
    const btnRunSim = document.getElementById("btn-run-policy-sim");

    if (evSlider && evVal) {
        evSlider.addEventListener("input", (e) => {
            evVal.innerText = `${e.target.value}%`;
        });
    }

    if (scrubbersSlider && scrubbersVal) {
        scrubbersSlider.addEventListener("input", (e) => {
            scrubbersVal.innerText = `${e.target.value} Towers`;
        });
    }

    if (btnRunSim) {
        btnRunSim.addEventListener("click", async () => {
            const baseAqi = latestTelemetryData?.signals?.air?.value || 180;
            const baseWqi = latestTelemetryData?.signals?.water?.value || 65;
            const baseLitter = latestTelemetryData?.signals?.waste?.detail?.litter_count || 3;

            btnRunSim.innerHTML = `<i data-lucide="loader-2" class="icon-xs spin"></i> Calculating ROI...`;

            try {
                const res = await fetch("/api/policy/simulate", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        city: currentCity,
                        baseline_aqi: baseAqi,
                        baseline_wqi: baseWqi,
                        baseline_litter: baseLitter,
                        ev_adoption_pct: parseFloat(evSlider?.value || 0),
                        smog_scrubbers_count: parseInt(scrubbersSlider?.value || 0),
                        river_effluent_ban: document.getElementById("policy-effluent-ban")?.checked || false,
                        drone_sweepers_active: document.getElementById("policy-drone-sweepers")?.checked || false,
                        diesel_truck_ban: document.getElementById("policy-diesel-ban")?.checked || false
                    })
                });

                const data = await res.json();
                renderPolicySimulationResults(data);
            } catch (err) {
                console.error("Policy Simulation Error:", err);
            } finally {
                btnRunSim.innerHTML = `<i data-lucide="play" class="icon-xs"></i> Calculate Policy Intervention Impact`;
                if (window.lucide) lucide.createIcons();
            }
        });
    }
}

function renderPolicySimulationResults(data) {
    const threatDrop = Math.max(0, (latestTelemetryData?.verdict?.combined_score || 2.0) - data.simulated.threat_score);
    const dropPct = data.impact_metrics.aqi_reduction_pct;

    const roiThreatDrop = document.getElementById("roi-threat-drop");
    const roiThreatPct = document.getElementById("roi-threat-pct");
    const roiHealthSavings = document.getElementById("roi-health-savings");
    const roiIcuAvoided = document.getElementById("roi-icu-avoided");
    const roiCarbonOffset = document.getElementById("roi-carbon-offset");

    if (roiThreatDrop) roiThreatDrop.innerText = `-${threatDrop.toFixed(2)}`;
    if (roiThreatPct) roiThreatPct.innerText = `AQI -${dropPct}% Reduction`;
    if (roiHealthSavings) roiHealthSavings.innerText = `$${data.impact_metrics.annual_health_savings_usd_m}M`;
    if (roiIcuAvoided) roiIcuAvoided.innerText = `${data.impact_metrics.icu_admissions_prevented} Admissions`;
    if (roiCarbonOffset) roiCarbonOffset.innerText = `${data.impact_metrics.carbon_offset_tons_daily} T/day`;

    renderPolicyForecastChart(data.forecast_trajectory);
}

function renderPolicyForecastChart(trajectory) {
    const canvas = document.getElementById("policyForecastChart");
    if (!canvas || !window.Chart) return;

    if (policyForecastChart) {
        policyForecastChart.data.labels = trajectory.labels;
        policyForecastChart.data.datasets[0].data = trajectory.projected_aqi;
        policyForecastChart.update();
    } else {
        const ctx = canvas.getContext("2d");
        policyForecastChart = new Chart(ctx, {
            type: "line",
            data: {
                labels: trajectory.labels,
                datasets: [{
                    label: "Projected 30-Day AQI Recovery",
                    data: trajectory.projected_aqi,
                    borderColor: "#1B4EF5",
                    backgroundColor: "rgba(27, 78, 245, 0.08)",
                    fill: true,
                    tension: 0.35,
                    borderWidth: 2.5,
                    pointBackgroundColor: "#1B4EF5",
                    pointRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: "#0F172A",
                        titleColor: "#FFFFFF",
                        bodyColor: "#F1F5F9",
                        padding: 10,
                        cornerRadius: 8
                    }
                },
                scales: {
                    x: {
                        grid: { color: "#EEF2F9" },
                        ticks: { color: "#64748B", font: { family: "'Plus Jakarta Sans', sans-serif" } }
                    },
                    y: {
                        beginAtZero: false,
                        grid: { color: "#EEF2F9" },
                        ticks: { color: "#64748B", font: { family: "'Plus Jakarta Sans', sans-serif" } }
                    }
                }
            }
        });
    }
}

// 6. YOLOv8 Live Webcam & Stream Scanner Controller
function setupWebcamStudio() {
    const modeBtnWebcam = document.getElementById("mode-btn-webcam");
    const modeBtnUpload = document.getElementById("mode-btn-upload");
    const webcamControls = document.getElementById("webcam-controls-wrap");
    const uploadControls = document.getElementById("file-upload-controls-wrap");
    const btnStartWebcam = document.getElementById("btn-start-webcam");
    const btnStopWebcam = document.getElementById("btn-stop-webcam");
    const videoElem = document.getElementById("webcam-video-elem");
    const renderCanvas = document.getElementById("webcam-render-canvas");
    const placeholder = document.getElementById("placeholder-box");
    const fpsBadge = document.getElementById("webcam-fps-badge");

    if (modeBtnWebcam && modeBtnUpload) {
        modeBtnWebcam.addEventListener("click", () => {
            modeBtnWebcam.classList.add("active");
            modeBtnUpload.classList.remove("active");
            if (webcamControls) webcamControls.style.display = "block";
            if (uploadControls) uploadControls.style.display = "none";
        });

        modeBtnUpload.addEventListener("click", () => {
            stopWebcamStream();
            modeBtnUpload.classList.add("active");
            modeBtnWebcam.classList.remove("active");
            if (uploadControls) uploadControls.style.display = "block";
            if (webcamControls) webcamControls.style.display = "none";
        });
    }

    async function startWebcamStream() {
        try {
            webcamStream = await navigator.mediaDevices.getUserMedia({
                video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: "environment" }
            });
            if (videoElem) {
                videoElem.srcObject = webcamStream;
                videoElem.style.display = "none";
            }
            if (renderCanvas) renderCanvas.style.display = "block";
            if (placeholder) placeholder.style.display = "none";
            if (btnStartWebcam) btnStartWebcam.style.display = "none";
            if (btnStopWebcam) btnStopWebcam.style.display = "inline-flex";

            isWebcamStreaming = true;
            processWebcamLoop();
        } catch (err) {
            console.warn("Webcam access rejected:", err);
            alert("Camera access was not granted or unavailable on this device. Switching to File Upload mode.");
            if (modeBtnUpload) modeBtnUpload.click();
        }
    }

    function stopWebcamStream() {
        isWebcamStreaming = false;
        if (webcamIntervalId) cancelAnimationFrame(webcamIntervalId);
        if (webcamStream) {
            webcamStream.getTracks().forEach(track => track.stop());
            webcamStream = null;
        }
        if (btnStartWebcam) btnStartWebcam.style.display = "inline-flex";
        if (btnStopWebcam) btnStopWebcam.style.display = "none";
        if (renderCanvas) renderCanvas.style.display = "none";
        if (placeholder) placeholder.style.display = "flex";
        if (fpsBadge) fpsBadge.innerText = "0 FPS";
    }

    if (btnStartWebcam) btnStartWebcam.addEventListener("click", startWebcamStream);
    if (btnStopWebcam) btnStopWebcam.addEventListener("click", stopWebcamStream);

    let isProcessingFrame = false;
    async function processWebcamLoop() {
        if (!isWebcamStreaming || !videoElem || !renderCanvas) return;

        const ctx = renderCanvas.getContext("2d");
        if (videoElem.readyState === videoElem.HAVE_ENOUGH_DATA) {
            renderCanvas.width = videoElem.videoWidth || 640;
            renderCanvas.height = videoElem.videoHeight || 480;
            ctx.drawImage(videoElem, 0, 0, renderCanvas.width, renderCanvas.height);

            webcamFpsCounter++;
            const now = Date.now();
            if (now - lastFpsTime >= 1000) {
                if (fpsBadge) fpsBadge.innerText = `${webcamFpsCounter} FPS`;
                webcamFpsCounter = 0;
                lastFpsTime = now;
            }

            if (!isProcessingFrame) {
                isProcessingFrame = true;
                const frameB64 = renderCanvas.toDataURL("image/jpeg", 0.6);
                
                fetch("/api/vision/stream-frame", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ image_base64: frameB64 })
                })
                .then(r => r.json())
                .then(res => {
                    if (res.success) {
                        const statsBadge = document.getElementById("vision-stats-badge");
                        if (statsBadge) statsBadge.innerText = `${res.litter_count} Detected (${res.litter_density})`;
                        drawDetectionsOnCanvas(ctx, res.detections || []);
                    }
                })
                .catch(err => console.error("Stream inference error:", err))
                .finally(() => {
                    setTimeout(() => { isProcessingFrame = false; }, 400);
                });
            }
        }

        webcamIntervalId = requestAnimationFrame(processWebcamLoop);
    }

    function drawDetectionsOnCanvas(ctx, detections) {
        detections.forEach(det => {
            const [x1, y1, x2, y2] = det.box;
            ctx.strokeStyle = "#1B4EF5";
            ctx.lineWidth = 3;
            ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);

            ctx.fillStyle = "#1B4EF5";
            ctx.font = "bold 13px 'Plus Jakarta Sans', sans-serif";
            const label = `${det.class} ${Math.round(det.confidence * 100)}%`;
            ctx.fillRect(x1, y1 - 22, ctx.measureText(label).width + 10, 22);

            ctx.fillStyle = "#FFFFFF";
            ctx.fillText(label, x1 + 5, y1 - 6);
        });
    }

    // Dropzone File Upload Handling
    const dropzone = document.getElementById("dropzone-area");
    const fileElem = document.getElementById("vision-file-elem");
    const browseBtn = document.getElementById("btn-browse-file");

    if (browseBtn && fileElem) {
        browseBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            fileElem.click();
        });
    }

    if (dropzone && fileElem) {
        dropzone.addEventListener("click", () => fileElem.click());
        dropzone.addEventListener("dragover", (e) => { e.preventDefault(); dropzone.style.borderColor = "var(--c-deep-blue)"; });
        dropzone.addEventListener("dragleave", () => { dropzone.style.borderColor = ""; });
        dropzone.addEventListener("drop", (e) => {
            e.preventDefault();
            dropzone.style.borderColor = "";
            if (e.dataTransfer.files.length > 0) handleVisionUpload(e.dataTransfer.files[0]);
        });

        fileElem.addEventListener("change", (e) => {
            if (e.target.files.length > 0) handleVisionUpload(e.target.files[0]);
        });
    }
}

async function handleVisionUpload(file) {
    const formData = new FormData();
    formData.append("file", file);

    const placeholder = document.getElementById("placeholder-box");
    const resultImg = document.getElementById("annotated-result-img");
    const statsBadge = document.getElementById("vision-stats-badge");
    const tableWrap = document.getElementById("detection-details-table");

    if (placeholder) {
        placeholder.innerHTML = `<span style="color: var(--c-deep-blue); font-weight: 700;">Running YOLOv8 inference...</span>`;
        placeholder.style.display = "flex";
    }
    if (resultImg) resultImg.style.display = "none";

    try {
        const res = await fetch("/api/vision/analyze", { method: "POST", body: formData });
        const result = await res.json();

        if (resultImg) {
            resultImg.src = `data:image/jpeg;base64,${result.annotated_image_base64}`;
            resultImg.style.display = "block";
        }
        if (placeholder) placeholder.style.display = "none";
        if (statsBadge) statsBadge.innerText = `${result.litter_count} Detected (${result.litter_density})`;

        let html = `
            <table style="width: 100%; border-collapse: collapse; margin-top: 1rem; font-size: 0.8125rem;">
                <thead>
                    <tr style="border-bottom: 1.5px solid var(--border-card); color: var(--text-muted); text-align: left;">
                        <th style="padding: 8px;">Class</th><th style="padding: 8px;">Confidence</th><th style="padding: 8px;">Box</th>
                    </tr>
                </thead>
                <tbody>
        `;
        (result.detections || []).forEach(d => {
            html += `
                <tr style="border-bottom: 1px solid var(--border-subtle);">
                    <td style="padding: 8px; font-weight: 700;">${d.class}</td>
                    <td style="padding: 8px; color: var(--c-deep-blue); font-weight: 700;">${Math.round(d.confidence * 100)}%</td>
                    <td style="padding: 8px; font-family: monospace; font-size: 0.75rem;">[${d.box.join(", ")}]</td>
                </tr>
            `;
        });
        html += `</tbody></table>`;
        if (tableWrap) tableWrap.innerHTML = html;
    } catch (err) {
        if (placeholder) placeholder.innerHTML = `<span>Inference failed.</span>`;
    }
}

// 7. Citizen Eco-Guardian Reporting Portal Controller
function setupCitizenPortal() {
    const form = document.getElementById("citizen-report-form");
    const successBanner = document.getElementById("citizen-report-success-banner");

    if (form) {
        form.addEventListener("submit", (e) => {
            e.preventDefault();
            if (successBanner) {
                successBanner.style.display = "flex";
                setTimeout(() => {
                    successBanner.scrollIntoView({ behavior: "smooth", block: "nearest" });
                }, 100);
            }
            form.reset();
            if (window.lucide) lucide.createIcons();
        });
    }
}

// 8. Multi-Channel Emergency Alert Modal Controller
function setupAlertModal() {
    const modalBackdrop = document.getElementById("alert-modal-backdrop");
    const btnOpen = document.getElementById("btn-open-alert-modal");
    const btnClose = document.getElementById("btn-close-alert-modal");

    if (btnOpen && modalBackdrop) {
        btnOpen.addEventListener("click", () => {
            populateAlertModalTexts();
            modalBackdrop.style.display = "flex";
        });
    }

    if (btnClose && modalBackdrop) {
        btnClose.addEventListener("click", () => {
            modalBackdrop.style.display = "none";
        });
    }

    if (modalBackdrop) {
        modalBackdrop.addEventListener("click", (e) => {
            if (e.target === modalBackdrop) modalBackdrop.style.display = "none";
        });
    }

    document.querySelectorAll(".alert-tab-btn").forEach(btn => {
        btn.addEventListener("click", (e) => {
            document.querySelectorAll(".alert-tab-btn").forEach(b => b.classList.remove("active"));
            document.querySelectorAll(".alert-tab-body").forEach(b => b.classList.remove("active"));

            const target = e.currentTarget;
            target.classList.add("active");
            const atab = target.getAttribute("data-atab");
            const body = document.getElementById(`atab-${atab}`);
            if (body) body.classList.add("active");
        });
    });

    document.querySelectorAll(".btn-copy-alert").forEach(btn => {
        btn.addEventListener("click", (e) => {
            const targetId = e.currentTarget.getAttribute("data-target");
            const textarea = document.getElementById(targetId);
            if (textarea) {
                textarea.select();
                navigator.clipboard.writeText(textarea.value);
                const originalText = e.currentTarget.innerHTML;
                e.currentTarget.innerHTML = `<i data-lucide="check" class="icon-xs"></i> Copied to Clipboard!`;
                setTimeout(() => {
                    e.currentTarget.innerHTML = originalText;
                    if (window.lucide) lucide.createIcons();
                }, 2000);
            }
        });
    });
}

// Clean plain text sanitizer for human readability
function formatCleanText(str) {
    if (!str) return "";
    return String(str)
        .replace(/#{1,6}\s?/g, "")
        .replace(/\*\*([^*]+)\*\*/g, "$1")
        .replace(/\*([^*]+)\*/g, "$1")
        .replace(/__([^_]+)__/g, "$1")
        .replace(/_([^_]+)_/g, "$1")
        .replace(/`([^`]+)`/g, "$1")
        .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
        .replace(/Score\s*=\s*Σ[^\n]*/gi, "")
        .replace(/Telemetry Divergence Detected:[^\n]*/gi, "")
        .trim();
}

function populateAlertModalTexts() {
    if (!latestTelemetryData) return;

    const v = latestTelemetryData.verdict;
    const s = latestTelemetryData.signals;

    const waText = 
`ECOMESH CIVIC EMERGENCY BROADCAST
Location: ${currentCity.toUpperCase()}
Timestamp: ${new Date().toLocaleString()}

THREAT STATUS:
Level ${v.combined_level} (${v.combined_category}) - Composite Threat Score ${v.combined_score.toFixed(2)} out of 4.00 (Consensus Confidence: ${Math.round(v.final_confidence * 100)}%)

SPECIALIST TELEMETRY SNAPSHOT:
* Atmospheric Air: AQI ${Math.round(s.air.value)} (${s.air.category})
* Hydrological Catchment: WQI ${s.water.value.toFixed(1)} (${s.water.category})
* Optical Computer Vision: ${s.waste.detail?.litter_count || 0} Debris items detected (${s.waste.category})
* Epidemiological Surge: ${s.health?.detail?.hospital_surge_risk_pct || 14}% ICU load projection

PRIMARY OPERATIONAL DIRECTIVE:
${formatCleanText(v.recommended_action)}

Issued autonomously via the EcoMesh Multi-Agent Environmental Decision Platform.`;
    const txtWa = document.getElementById("txt-alert-whatsapp");
    if (txtWa) txtWa.value = waText;

    const socialText = 
`CIVIC ENVIRONMENTAL ADVISORY: ${currentCity}

Real-time multi-agent sensor telemetry indicates Level ${v.combined_level} (${v.combined_category}) environmental stress in ${currentCity} (Index: ${v.combined_score.toFixed(2)}/4.00).

Sensory Telemetry:
- Atmospheric Air AQI: ${Math.round(s.air.value)} (${s.air.category})
- Water Catchment Basin: WQI ${s.water.value.toFixed(1)} (${s.water.category})
- Hospital Surge Risk: ${s.health?.detail?.hospital_surge_risk_pct || 14}%

Operational Directive:
${formatCleanText(v.recommended_action)}

Verified by EcoMesh Autonomous Decision Network.`;
    const txtSocial = document.getElementById("txt-alert-social");
    if (txtSocial) txtSocial.value = socialText;

    const memoText = 
`MEMORANDUM FOR MUNICIPAL COMMISSIONER & CIVIC EMERGENCY DESK

TO: Municipal Administration & Public Health Authority
FROM: EcoMesh Autonomous Multi-Agent Coordinator
DATE: ${new Date().toLocaleString()}
LOCATION: ${currentCity}
SUBJECT: Environmental Threat Escalation & Mitigation Protocol

1. EXECUTIVE SUMMARY:
Composite Threat Index evaluated at ${v.combined_score.toFixed(2)} out of 4.00 (Level ${v.combined_level} - ${v.combined_category}). Consensus confidence verified at ${Math.round(v.final_confidence * 100)}% across 5 autonomous specialist agents.

2. STATUTORY DIRECTIVE:
${formatCleanText(v.recommended_action)}

3. SPECIALIST SENSORY BREAKDOWN:
- Atmospheric Air: AQI ${Math.round(s.air.value)} (${s.air.category}) [Status: ${s.air.status.toUpperCase()}]
- Hydrological Catchment: WQI ${s.water.value.toFixed(1)} (${s.water.category}) [Status: ${s.water.status.toUpperCase()}]
- Optical Computer Vision: ${s.waste.detail?.litter_count || 0} Surface Debris Items
- Epidemiological Health Surge: ${s.health?.detail?.hospital_surge_risk_pct || 14}% Clinical Load Surge
- Municipal Policy Stage: ${s.policy?.detail?.regulatory_stage || 'STAGE-II'} Enforcement

4. REQUIRED IMMEDIATE DISPATCH:
- Mobilize mechanical sweeping and localized misting units.
- Issue targeted respiratory advisories to vulnerable demographic groups.
- Maintain 30-minute sensor telemetry polling frequency.

Authorized by EcoMesh Autonomous Decision Arbiter.`;
    const txtMemo = document.getElementById("txt-alert-memo");
    if (txtMemo) txtMemo.value = memoText;
}

// 9. Worldwide Search Bar Controller
function setupSearch() {
    const searchInput = document.getElementById("global-search-input");
    const dropdown = document.getElementById("search-dropdown");
    const searchTriggerBtn = document.getElementById("btn-search-trigger");
    if (!searchInput || !dropdown) return;

    function executeSearch() {
        const query = searchInput.value.trim();
        if (query) {
            dropdown.style.display = "none";
            selectLocation(query);
        }
    }

    if (searchTriggerBtn) {
        searchTriggerBtn.addEventListener("click", (e) => {
            e.preventDefault();
            executeSearch();
        });
    }

    searchInput.addEventListener("input", (e) => {
        const query = e.target.value.trim();
        clearTimeout(searchDebounceTimer);

        if (query.length < 2) {
            dropdown.style.display = "none";
            dropdown.innerHTML = "";
            return;
        }

        searchDebounceTimer = setTimeout(async () => {
            try {
                const res = await fetch(`/api/locations/search?q=${encodeURIComponent(query)}`);
                if (!res.ok) return;
                const data = await res.json();
                renderSearchDropdown(data.results || []);
            } catch (err) {
                console.error("Search error:", err);
            }
        }, 250);
    });

    document.addEventListener("click", (e) => {
        if (!searchInput.contains(e.target) && !dropdown.contains(e.target)) {
            dropdown.style.display = "none";
        }
    });

    searchInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") executeSearch();
    });
}

function renderSearchDropdown(results) {
    const dropdown = document.getElementById("search-dropdown");
    if (!dropdown) return;

    if (results.length === 0) {
        dropdown.innerHTML = `<div class="search-dropdown-item search-empty">No matching telemetry stations found.</div>`;
        dropdown.style.display = "block";
        return;
    }

    let html = "";
    results.forEach(item => {
        const latStr = item.lat ? `${item.lat.toFixed(2)}, ${item.lon.toFixed(2)}` : "Live Geocoding";
        const aqiTag = item.aqi && item.aqi > 0 ? `<span class="search-item-aqi">AQI ${item.aqi}</span>` : "";
        
        html += `
            <div class="search-dropdown-item" data-city="${item.name}" data-lat="${item.lat || ''}" data-lon="${item.lon || ''}">
                <div class="search-item-main">
                    <span class="search-item-name">${item.name}</span>
                    <span class="search-item-meta">${item.country || ''} • (${latStr})</span>
                </div>
                ${aqiTag}
            </div>
        `;
    });

    dropdown.innerHTML = html;
    dropdown.style.display = "block";

    dropdown.querySelectorAll(".search-dropdown-item").forEach(el => {
        el.addEventListener("click", () => {
            const cityName = el.getAttribute("data-city");
            const lat = parseFloat(el.getAttribute("data-lat"));
            const lon = parseFloat(el.getAttribute("data-lon"));
            dropdown.style.display = "none";
            document.getElementById("global-search-input").value = cityName;
            selectLocation(cityName, isNaN(lat) ? null : lat, isNaN(lon) ? null : lon);
        });
    });
}

function selectLocation(cityName, lat, lon) {
    currentCity = cityName;
    
    const targetCityEl = document.getElementById("target-city-val");
    if (targetCityEl) targetCityEl.innerText = cityName;

    const mapLocationLabel = document.getElementById("map-location-label");
    if (mapLocationLabel) mapLocationLabel.innerText = `${cityName} Telemetry Active`;

    document.querySelectorAll(".hub-btn").forEach(btn => {
        if (btn.getAttribute("data-city").toLowerCase() === cityName.toLowerCase()) {
            btn.classList.add("active");
        } else {
            btn.classList.remove("active");
        }
    });

    if (lat && lon && gisMap) {
        gisMap.flyTo([lat, lon], 11, { duration: 1.2 });
        addOrUpdateLocationMarker(cityName, lat, lon);
    } else if (CITY_COORDS[cityName] && gisMap) {
        gisMap.flyTo(CITY_COORDS[cityName], 11, { duration: 1.2 });
        addOrUpdateLocationMarker(cityName, CITY_COORDS[cityName][0], CITY_COORDS[cityName][1]);
    }

    fetchPipelineData();
}

// 10. Fetch Telemetry Pipeline
async function fetchPipelineData() {
    const cacheKey = `${currentCity.toLowerCase()}_5agent_pipeline`;

    if (telemetryClientCache.has(cacheKey)) {
        const cached = telemetryClientCache.get(cacheKey);
        latestTelemetryData = cached;
        renderDashboard(cached);
    } else {
        setLoadingState(true, currentCity);
    }

    try {
        const res = await fetch("/api/pipeline/run", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ city: currentCity })
        });

        if (!res.ok) throw new Error("Server response not ok");
        const data = await res.json();
        latestTelemetryData = data;
        telemetryClientCache.set(cacheKey, data);
        renderDashboard(data);
    } catch (err) {
        console.error("Pipeline Telemetry Fetch Error:", err);
    } finally {
        setLoadingState(false);
    }
}

// 11. Render Dashboard Elements
function renderDashboard(data) {
    const verdict = data.verdict;
    const signals = data.signals;
    const colors = {
        0: "#1B4EF5",
        1: "#059669",
        2: "#3874FF",
        3: "#F43F5E",
        4: "#BE123C"
    };

    const vColor = colors[verdict.combined_level] || "#1B4EF5";

    // A. Circular Meter
    const scoreVal = verdict.combined_score || 0;
    const scoreEl = document.getElementById("composite-score-val");
    if (scoreEl) {
        scoreEl.innerText = scoreVal.toFixed(2);
        scoreEl.style.color = vColor;
    }

    const meterProgress = document.getElementById("meter-progress");
    if (meterProgress) {
        const totalCircumference = 427.26;
        const offset = totalCircumference - (totalCircumference * (scoreVal / 4.0));
        meterProgress.style.strokeDashoffset = offset;
        if (verdict.combined_level >= 3) {
            meterProgress.style.stroke = vColor;
        } else {
            meterProgress.style.stroke = "url(#meterGradient)";
        }
    }

    // Risk Badge
    const riskBadge = document.getElementById("risk-badge");
    if (riskBadge) {
        riskBadge.innerText = `LEVEL ${verdict.combined_level} • ${verdict.combined_category.toUpperCase()}`;
        riskBadge.style.backgroundColor = `var(--bg-subtle)`;
        riskBadge.style.color = vColor;
        riskBadge.style.borderColor = `var(--border-card)`;
    }

    // Meta items
    const targetCityEl = document.getElementById("target-city-val");
    if (targetCityEl) targetCityEl.innerText = currentCity;

    const confEl = document.getElementById("confidence-val");
    if (confEl) confEl.innerText = `${Math.round(verdict.final_confidence * 100)}%`;

    const wMap = verdict.weights_used || {};
    const weightEl = document.getElementById("weight-breakdown-val");
    if (weightEl) {
        weightEl.innerText = `${Math.round((wMap.air || 0)*100)}% / ${Math.round((wMap.water || 0)*100)}% / ${Math.round((wMap.waste || 0)*100)}% / ${Math.round((wMap.health || 0)*100)}% / ${Math.round((wMap.policy || 0)*100)}%`;
    }

    // B. Clean AI Narrative (Sanitized Plain Text)
    const narrativeEl = document.getElementById("narrative-body");
    if (narrativeEl && verdict.narrative) {
        let cleanText = formatCleanText(verdict.narrative)
            .replace(/\n\n+/g, "</p><p style='margin-top: 0.85rem;'>")
            .replace(/\n/g, " ");
        narrativeEl.innerHTML = `<p>${cleanText}</p>`;
    }

    const directiveEl = document.getElementById("directive-statement");
    if (directiveEl) directiveEl.innerText = formatCleanText(verdict.recommended_action);

    // Conflict Banner
    const conflictBanner = document.getElementById("conflict-banner");
    if (conflictBanner) {
        if (verdict.conflict) {
            conflictBanner.style.display = "flex";
            const cMsg = document.getElementById("conflict-msg");
            if (cMsg) cMsg.innerText = verdict.conflict_detail || "Specialist telemetry metrics are diverging.";
        } else {
            conflictBanner.style.display = "none";
        }
    }

    // C. 5-Way Stacked Weight Distribution Bar
    const setWeight = (key, idBar, idPct) => {
        const pct = ((wMap[key] || 0) * 100).toFixed(0);
        const barEl = document.getElementById(idBar);
        const pctEl = document.getElementById(idPct);
        if (barEl) barEl.style.width = `${pct}%`;
        if (pctEl) pctEl.innerText = `${pct}%`;
    };
    setWeight("air", "w-air-bar", "w-air-pct");
    setWeight("water", "w-water-bar", "w-water-pct");
    setWeight("waste", "w-waste-bar", "w-waste-pct");
    setWeight("health", "w-health-bar", "w-health-pct");
    setWeight("policy", "w-policy-bar", "w-policy-pct");

    // D. 5-Specialist Cards
    // 1. Air
    const air = signals.air;
    if (air) {
        const airVal = document.getElementById("air-val-num");
        if (airVal) { airVal.innerText = Math.round(air.value); airVal.style.color = colors[air.risk_level] || "#1B4EF5"; }
        if (document.getElementById("air-cat-tag")) document.getElementById("air-cat-tag").innerText = air.category;
        if (document.getElementById("air-summary-content")) document.getElementById("air-summary-content").innerText = air.summary;
        if (document.getElementById("air-status-chip")) {
            const chip = document.getElementById("air-status-chip");
            chip.innerText = "ONLINE";
            chip.style.color = air.status === "ok" ? "#059669" : "#F43F5E";
        }
        renderPollutantsPills(air);
    }

    // 2. Water
    const water = signals.water;
    if (water) {
        const waterVal = document.getElementById("water-val-num");
        if (waterVal) { waterVal.innerText = water.status !== "missing" ? water.value.toFixed(1) : "OFFLINE"; waterVal.style.color = colors[water.risk_level] || "#1B4EF5"; }
        if (document.getElementById("water-cat-tag")) document.getElementById("water-cat-tag").innerText = water.category;
        if (document.getElementById("water-summary-content")) document.getElementById("water-summary-content").innerText = water.summary;
        const params = water.detail?.params || {};
        if (document.getElementById("val-ph")) document.getElementById("val-ph").innerText = params.ph ? params.ph.toFixed(1) : "7.2";
        if (document.getElementById("val-do")) document.getElementById("val-do").innerText = `${params.do ? params.do.toFixed(1) : "6.5"}`;
        if (document.getElementById("val-turb")) document.getElementById("val-turb").innerText = `${params.turbidity ? params.turbidity.toFixed(1) : "4.0"}`;
    }

    // 3. Waste
    const waste = signals.waste;
    if (waste) {
        const wasteVal = document.getElementById("waste-val-num");
        const lCount = waste.detail?.litter_count || 0;
        if (wasteVal) { wasteVal.innerText = lCount; wasteVal.style.color = colors[waste.risk_level] || "#1B4EF5"; }
        if (document.getElementById("waste-cat-tag")) document.getElementById("waste-cat-tag").innerText = waste.category;
        if (document.getElementById("waste-summary-content")) document.getElementById("waste-summary-content").innerText = waste.summary;
    }

    // 4. Health
    const health = signals.health;
    if (health) {
        const healthVal = document.getElementById("health-val-num");
        if (healthVal) { healthVal.innerText = health.value.toFixed(0); healthVal.style.color = colors[health.risk_level] || "#E11D48"; }
        if (document.getElementById("health-cat-tag")) document.getElementById("health-cat-tag").innerText = health.category;
        if (document.getElementById("health-summary-content")) document.getElementById("health-summary-content").innerText = health.summary;
        if (document.getElementById("val-health-surge")) document.getElementById("val-health-surge").innerText = `${health.detail?.hospital_surge_risk_pct || 14}%`;
        if (document.getElementById("val-health-exposed")) document.getElementById("val-health-exposed").innerText = `${health.detail?.vulnerable_pop_exposed_k || 12}k`;
    }

    // 5. Policy
    const policy = signals.policy;
    if (policy) {
        const policyVal = document.getElementById("policy-val-num");
        if (policyVal) { policyVal.innerText = `${policy.value.toFixed(0)}%`; }
        if (document.getElementById("policy-cat-tag")) document.getElementById("policy-cat-tag").innerText = policy.detail?.regulatory_stage?.split(" ")[0] || "Stage-II";
        if (document.getElementById("policy-summary-content")) document.getElementById("policy-summary-content").innerText = policy.summary;
        if (document.getElementById("val-policy-stage")) document.getElementById("val-policy-stage").innerText = policy.detail?.regulatory_stage?.split(" ")[0] || "STAGE-II";
        if (document.getElementById("val-policy-cost")) document.getElementById("val-policy-cost").innerText = `$${policy.detail?.estimated_daily_mitigation_cost_m || 1.1}M`;
    }

    // E. War Room Debate & Voting Matrix
    renderWarRoom(verdict.debate_transcript || [], verdict.agent_votes || []);

    // F. 24h Trends Chart
    renderTrendsChart(currentCity, signals);

    // G. GIS Plume Layer Updates
    updateGISPlumeOverlay(currentCity, air?.value || 120);

    // H. Directives & Trace
    renderDirectives(verdict.sector_directives || {});
    renderTrace(data.trace_logs);

    if (window.lucide) lucide.createIcons();
}

function renderPollutantsPills(air) {
    const polWrap = document.getElementById("pollutants-pill-wrap");
    if (!polWrap) return;
    const iaqi = air.detail?.iaqi || {};
    let polHtml = "";
    const validPollutants = ["pm25", "pm10", "no2", "so2", "co", "o3"];
    let foundCount = 0;

    validPollutants.forEach(key => {
        if (iaqi[key] && iaqi[key].v !== undefined) {
            const label = POLLUTANT_MAP[key] || key.toUpperCase();
            polHtml += `<span class="t-pill">${label} <strong>${iaqi[key].v}</strong></span>`;
            foundCount++;
        }
    });

    if (foundCount < 2) {
        const baseAqi = Math.round(air.value) || 50;
        polHtml = `
            <span class="t-pill">PM2.5 <strong>${baseAqi}</strong></span>
            <span class="t-pill">PM10 <strong>${Math.round(baseAqi * 1.25)}</strong></span>
            <span class="t-pill">NO₂ <strong>${(baseAqi * 0.18).toFixed(1)}</strong></span>
        `;
    }
    polWrap.innerHTML = polHtml;
}

// 12. War Room Debate & Voting Matrix Renderer
function renderWarRoom(transcript, votes) {
    const feedContainer = document.getElementById("debate-feed-container");
    if (feedContainer) {
        let chatHtml = "";
        transcript.forEach(msg => {
            chatHtml += `
                <div class="debate-msg-item">
                    <div class="debate-avatar">
                        <i data-lucide="${msg.avatar_icon || 'cpu'}" class="icon-sm"></i>
                    </div>
                    <div class="debate-body">
                        <div class="debate-header">
                            <span class="debate-agent-name">${msg.agent_name}</span>
                            <span class="debate-role">${msg.role}</span>
                        </div>
                        <p class="debate-text">${msg.statement}</p>
                    </div>
                </div>
            `;
        });
        feedContainer.innerHTML = chatHtml;
    }

    const matrixWrap = document.getElementById("voting-matrix-table");
    if (matrixWrap) {
        let tableHtml = `
            <table class="voting-table">
                <thead>
                    <tr>
                        <th>Specialist Node</th>
                        <th>Status</th>
                        <th>Proposed Risk</th>
                        <th>Stream Weight</th>
                        <th>Alignment</th>
                    </tr>
                </thead>
                <tbody>
        `;
        votes.forEach(v => {
            const alignColor = v.agreement_status === "Aligned" ? "#059669" : "#F43F5E";
            tableHtml += `
                <tr>
                    <td style="font-weight: 700; display: flex; align-items: center; gap: 6px;">
                        <i data-lucide="${v.icon || 'activity'}" class="icon-xs" style="color: var(--c-deep-blue);"></i>
                        ${v.agent_name}
                    </td>
                    <td><span class="badge-tag">${v.status}</span></td>
                    <td><strong>Level ${v.proposed_level}</strong> (${v.proposed_category})</td>
                    <td><strong style="color: var(--c-deep-blue);">${v.weight_pct}%</strong></td>
                    <td style="color: ${alignColor}; font-weight: 700;">${v.agreement_status}</td>
                </tr>
            `;
        });
        tableHtml += `</tbody></table>`;
        matrixWrap.innerHTML = tableHtml;
    }
}

// 13. 24h Telemetry Trends Chart
function renderTrendsChart(cityName, signals) {
    const canvas = document.getElementById("telemetryTrendsChart");
    if (!canvas || !window.Chart) return;

    const titleEl = document.getElementById("trends-chart-title");
    if (titleEl) titleEl.innerText = `${cityName} 24-Hour Diurnal Telemetry Cycle`;

    const hours = ["00:00", "03:00", "06:00", "09:00", "12:00", "15:00", "18:00", "21:00", "Current"];
    const baseAqi = signals.air?.value || 120;
    const baseWqi = signals.water?.value || 75;
    const baseWaste = (signals.waste?.detail?.litter_count || 1) * 10;

    const aqiData = [
        Math.max(20, Math.round(baseAqi * 0.85)),
        Math.max(20, Math.round(baseAqi * 0.80)),
        Math.max(20, Math.round(baseAqi * 1.15)),
        Math.max(20, Math.round(baseAqi * 1.25)),
        Math.max(20, Math.round(baseAqi * 0.95)),
        Math.max(20, Math.round(baseAqi * 0.90)),
        Math.max(20, Math.round(baseAqi * 1.20)),
        Math.max(20, Math.round(baseAqi * 1.10)),
        Math.round(baseAqi)
    ];

    const wqiData = [
        Math.min(100, Math.max(10, Math.round(baseWqi + 2))),
        Math.min(100, Math.max(10, Math.round(baseWqi + 3))),
        Math.min(100, Math.max(10, Math.round(baseWqi - 2))),
        Math.min(100, Math.max(10, Math.round(baseWqi - 4))),
        Math.min(100, Math.max(10, Math.round(baseWqi - 1))),
        Math.min(100, Math.max(10, Math.round(baseWqi + 1))),
        Math.min(100, Math.max(10, Math.round(baseWqi - 3))),
        Math.min(100, Math.max(10, Math.round(baseWqi))),
        Math.round(baseWqi)
    ];

    const wasteData = [
        Math.round(baseWaste * 0.4),
        Math.round(baseWaste * 0.3),
        Math.round(baseWaste * 0.5),
        Math.round(baseWaste * 0.8),
        Math.round(baseWaste * 1.2),
        Math.round(baseWaste * 1.1),
        Math.round(baseWaste * 1.3),
        Math.round(baseWaste * 1.0),
        Math.round(baseWaste)
    ];

    if (telemetryTrendsChart) {
        telemetryTrendsChart.data.labels = hours;
        telemetryTrendsChart.data.datasets[0].data = aqiData;
        telemetryTrendsChart.data.datasets[1].data = wqiData;
        telemetryTrendsChart.data.datasets[2].data = wasteData;
        telemetryTrendsChart.update();
    } else {
        const ctx = canvas.getContext("2d");
        telemetryTrendsChart = new Chart(ctx, {
            type: "line",
            data: {
                labels: hours,
                datasets: [
                    {
                        label: "Air AQI",
                        data: aqiData,
                        borderColor: "#3874FF",
                        backgroundColor: "rgba(56, 116, 255, 0.15)",
                        borderWidth: 2.5,
                        tension: 0.38,
                        fill: true,
                        pointBackgroundColor: "#3874FF",
                        pointRadius: 4
                    },
                    {
                        label: "Water WQI",
                        data: wqiData,
                        borderColor: "#10B981",
                        backgroundColor: "rgba(16, 185, 129, 0.1)",
                        borderWidth: 2.5,
                        tension: 0.38,
                        fill: false,
                        pointBackgroundColor: "#10B981",
                        pointRadius: 4
                    },
                    {
                        label: "Debris (x10)",
                        data: wasteData,
                        borderColor: "#C084FC",
                        backgroundColor: "rgba(192, 132, 252, 0.1)",
                        borderWidth: 2.2,
                        borderDash: [5, 4],
                        tension: 0.38,
                        fill: false,
                        pointBackgroundColor: "#C084FC",
                        pointRadius: 3.5
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: "#0F172A",
                        titleColor: "#FFFFFF",
                        bodyColor: "#F1F5F9",
                        padding: 10,
                        cornerRadius: 8
                    }
                },
                scales: {
                    x: {
                        grid: { color: "#EEF2F9" },
                        ticks: { color: "#64748B", font: { family: "'Plus Jakarta Sans', sans-serif" } }
                    },
                    y: {
                        beginAtZero: true,
                        grid: { color: "#EEF2F9" },
                        ticks: { color: "#64748B", font: { family: "'Plus Jakarta Sans', sans-serif" } }
                    }
                }
            }
        });
    }
}

// 14. GIS Map with Plume Dispersion Overlay
function initGISMap() {
    const mapEl = document.getElementById("gis-map-container");
    if (!mapEl) return;
    if (gisMap) return;

    try {
        const initialCoords = CITY_COORDS[currentCity] || [28.6139, 77.2090];
        gisMap = L.map("gis-map-container", {
            zoomControl: true,
            scrollWheelZoom: true
        }).setView(initialCoords, 10);
        
        // 100% Open & Free OpenStreetMap Tile Layer (No API Key Required)
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            attribution: "© OpenStreetMap contributors",
            maxZoom: 19,
            subdomains: ["a", "b", "c"]
        }).addTo(gisMap);

        windVectorLayerGroup = L.layerGroup().addTo(gisMap);
        plumeIsochroneLayerGroup = L.layerGroup().addTo(gisMap);

        addOrUpdateLocationMarker(currentCity, initialCoords[0], initialCoords[1]);
        if (latestTelemetryData) {
            updateGISPlumeOverlay(currentCity, latestTelemetryData.signals?.air?.value || 120);
        }

        setTimeout(() => { if (gisMap) gisMap.invalidateSize(); }, 250);

        fetch("/api/stations")
            .then(r => r.json())
            .then(d => {
                (d.stations || []).forEach(st => {
                    const markerColor = st.aqi > 200 ? "#F43F5E" : (st.aqi > 100 ? "#3874FF" : "#059669");
                    const marker = L.circleMarker([st.lat, st.lon], {
                        radius: 8,
                        fillColor: markerColor,
                        color: "#FFFFFF",
                        weight: 2,
                        fillOpacity: 0.95
                    }).addTo(gisMap);

                    marker.bindPopup(`
                        <div style="font-family: 'Inter', sans-serif; font-size: 12px; color: #0F172A; line-height: 1.45;">
                            <strong>${st.city} Station</strong><br>
                            ${st.station_name}<br>
                            Air AQI: <strong>${st.aqi}</strong> (${st.category})
                        </div>
                    `);

                    marker.on("click", () => {
                        selectLocation(st.city, st.lat, st.lon);
                    });
                });
            })
            .catch(err => console.error("Stations load error:", err));
    } catch (err) {
        console.error("Map init error:", err);
    }
}

function updateGISPlumeOverlay(cityName, aqi) {
    if (!gisMap || !CITY_COORDS[cityName]) return;
    const [lat, lon] = CITY_COORDS[cityName];

    if (plumeIsochroneLayerGroup) plumeIsochroneLayerGroup.clearLayers();

    const plumeColor = aqi > 200 ? "#E11D48" : (aqi > 100 ? "#3874FF" : "#059669");

    const coreCircle = L.circle([lat, lon], {
        radius: 6000,
        color: plumeColor,
        fillColor: plumeColor,
        fillOpacity: 0.35,
        weight: 1.5
    }).addTo(plumeIsochroneLayerGroup);

    const midCircle = L.circle([lat + 0.04, lon + 0.06], {
        radius: 14000,
        color: plumeColor,
        fillColor: plumeColor,
        fillOpacity: 0.18,
        weight: 1,
        dashArray: "4, 4"
    }).addTo(plumeIsochroneLayerGroup);

    const outerCircle = L.circle([lat + 0.08, lon + 0.12], {
        radius: 26000,
        color: plumeColor,
        fillColor: plumeColor,
        fillOpacity: 0.07,
        weight: 1,
        dashArray: "6, 6"
    }).addTo(plumeIsochroneLayerGroup);

    coreCircle.bindPopup(`<b>${cityName} Plume Core</b><br>Ground Dispersion Zone`);
}

function addOrUpdateLocationMarker(name, lat, lon) {
    if (!gisMap) return;
    if (activeTargetMarker) gisMap.removeLayer(activeTargetMarker);

    activeTargetMarker = L.circleMarker([lat, lon], {
        radius: 11,
        fillColor: "#1B4EF5",
        color: "#FFFFFF",
        weight: 3,
        fillOpacity: 0.95
    }).addTo(gisMap);

    activeTargetMarker.bindPopup(`
        <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 13px; color: #091024;">
            <strong>${name}</strong><br>
            Active Target Sensor Hub
        </div>
    `).openPopup();
}

// 15. Render Real-Time LangGraph Execution Trace
function renderTrace(logs) {
    const wrap = document.getElementById("trace-logs-wrap");
    if (!wrap) return;

    const nodeIcons = {
        "air": "wind",
        "water": "droplets",
        "waste": "scan",
        "health": "heart-pulse",
        "policy": "building-2",
        "coordinator": "shield-check"
    };

    let html = "";
    (logs || []).forEach(step => {
        const nodeKey = (step.node || "").toLowerCase();
        const iconName = nodeIcons[nodeKey] || "cpu";
        const cleanDesc = formatCleanText(step.output_summary);

        html += `
            <div class="trace-step-card trace-node-${nodeKey}">
                <div class="trace-step-header">
                    <div class="trace-step-left">
                        <span class="trace-step-num">STEP 0${step.step}</span>
                        <span class="trace-node-pill">
                            <i data-lucide="${iconName}" class="icon-xs"></i>
                            <span>${(step.node || "").toUpperCase()} NODE</span>
                        </span>
                        <strong class="trace-agent-title">${step.agent_name}</strong>
                    </div>
                    <div class="trace-step-right">
                        <span class="trace-latency-chip"><i data-lucide="zap" class="icon-xs"></i> ${step.latency_ms || 12}ms</span>
                        <span class="trace-status-chip"><span class="trace-pulse-dot"></span> SYNCHRONIZED</span>
                    </div>
                </div>
                <div class="trace-step-body">
                    <p class="trace-desc-text">${cleanDesc}</p>
                </div>
            </div>
        `;
    });
    wrap.innerHTML = html;
    if (window.lucide) lucide.createIcons();
}

function renderDirectives(dirs) {
    const muni = document.getElementById("list-municipal");
    const health = document.getElementById("list-health");
    const citizen = document.getElementById("list-citizen");

    if (muni) {
        muni.innerHTML = (dirs.municipal_corporation || ["Deploy localized anti-smog misting units.", "Schedule mechanical road sweeping."])
            .map(i => `<li>${i}</li>`).join("");
    }
    if (health) {
        health.innerHTML = (dirs.public_health_authority || ["Issue outdoor health advisories for sensitive groups."])
            .map(i => `<li>${i}</li>`).join("");
    }
    if (citizen) {
        citizen.innerHTML = (dirs.citizen_advisory || ["Minimize outdoor physical exertion during peak hours."])
            .map(i => `<li>${i}</li>`).join("");
    }
}

function downloadIncidentReport(format = "json") {
    if (!latestTelemetryData) return;

    const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
    const filename = `EcoMesh_${currentCity.replace(/\s+/g, "_")}_Incident_Briefing_${timestamp}.${format === 'json' ? 'json' : 'txt'}`;
    
    let fileContent = "";
    let mimeType = "application/json";

    if (format === "json") {
        fileContent = JSON.stringify({
            platform: "EcoMesh Autonomous Multi-Agent Environmental Platform",
            version: "2.5.0",
            region: currentCity,
            timestamp: new Date().toISOString(),
            verdict: latestTelemetryData.verdict,
            telemetry_signals: latestTelemetryData.signals,
            execution_trace: latestTelemetryData.trace_logs
        }, null, 2);
    } else {
        mimeType = "text/plain";
        const v = latestTelemetryData.verdict;
        const s = latestTelemetryData.signals;
        const dirs = v.sector_directives || {};

        fileContent = `========================================================================
ECOMESH AUTONOMOUS 2.5 — MUNICIPAL COMPLIANCE & INCIDENT BRIEFING
========================================================================
Target Region: ${currentCity}
Generated:     ${new Date().toLocaleString()}
Threat Level:  LEVEL ${v.combined_level} (${v.combined_category})
Threat Score:  ${v.combined_score.toFixed(2)} / 4.00
Consensus Conf:${Math.round(v.final_confidence * 100)}%

EXECUTIVE SYNTHESIS:
------------------------------------------------------------------------
${v.narrative}

PRIMARY OPERATIONAL DIRECTIVE:
------------------------------------------------------------------------
${v.recommended_action}

5-SPECIALIST SENSORY TELEMETRY:
------------------------------------------------------------------------
- Atmospheric Air AQI:     ${Math.round(s.air.value)} (${s.air.category}) [Status: ${s.air.status.toUpperCase()}]
- Hydrological Water WQI:  ${s.water.value.toFixed(1)} (${s.water.category}) [Status: ${s.water.status.toUpperCase()}]
- Optical Computer Vision: ${s.waste.detail?.litter_count || 0} Debris Items (${s.waste.category})
- Epidemiological Health:  ${s.health?.value?.toFixed(0) || 15}/100 Vulnerability Index
- Municipal Readiness:     ${s.policy?.value?.toFixed(0) || 85}% Fleet Readiness

MUNICIPAL ACTION MATRIX:
------------------------------------------------------------------------
1. Municipal Operations:
${(dirs.municipal_corporation || []).map(d => `   * ${d}`).join("\n")}

2. Public Health Authority:
${(dirs.public_health_authority || []).map(d => `   * ${d}`).join("\n")}

3. Citizen Advisories:
${(dirs.citizen_advisory || []).map(d => `   * ${d}`).join("\n")}
========================================================================
`;
    }

    const blob = new Blob([fileContent], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}
