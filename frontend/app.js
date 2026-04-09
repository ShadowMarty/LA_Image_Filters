const controls = {
  preset: document.getElementById("preset"),
  strength: document.getElementById("strength"),
  hue: document.getElementById("hue"),
  exposure: document.getElementById("exposure"),
  contrast: document.getElementById("contrast"),
  saturation: document.getElementById("saturation"),
  vibrance: document.getElementById("vibrance"),
  temperature: document.getElementById("temperature"),
  tint: document.getElementById("tint"),
  gamma: document.getElementById("gamma"),
  sharpen: document.getElementById("sharpen"),
  vignette: document.getElementById("vignette"),
  pca_k: document.getElementById("pca_k"),
  preview_max: document.getElementById("preview_max"),
  grayscale: document.getElementById("grayscale"),
  least_squares: document.getElementById("least_squares"),
};

const fileInput = document.getElementById("fileInput");
const originalPreview = document.getElementById("originalPreview");
const filteredPreview = document.getElementById("filteredPreview");
const statusText = document.getElementById("statusText");
const resetBtn = document.getElementById("resetBtn");
const downloadBtn = document.getElementById("downloadBtn");
const previewGrid = document.querySelector(".preview-grid");
const tooltip = document.getElementById("smartTooltip");
const viewButtons = {
  split: document.getElementById("viewSplitBtn"),
  original: document.getElementById("viewOriginalBtn"),
  edited: document.getElementById("viewEditedBtn"),
};
const toggleCaptionsBtn = document.getElementById("toggleCaptionsBtn");

let activeFile = null;
let requestId = 0;
let captionsEnabled = true;

const defaults = {
  preset: "Cinematic",
  strength: 1,
  hue: 0,
  exposure: 0,
  contrast: 0,
  saturation: 0,
  vibrance: 0,
  temperature: 0,
  tint: 0,
  gamma: 1,
  sharpen: 0,
  vignette: 0,
  pca_k: 3,
  preview_max: 1280,
  grayscale: false,
  least_squares: false,
};

function debounce(fn, wait = 220) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), wait);
  };
}

function setStatus(message, type = "") {
  statusText.textContent = message;
  statusText.className = `status ${type}`.trim();
}

function formatNumber(value, decimals = 6) {
  const num = Number(value);
  if (!Number.isFinite(num)) return "-";
  if (Math.abs(num) >= 1e6) return num.toExponential(3);
  return num.toFixed(decimals);
}

function renderTable(elementId, matrix) {
  const table = document.getElementById(elementId);
  if (!Array.isArray(matrix)) {
    table.innerHTML = "";
    return;
  }
  table.innerHTML = matrix
    .map((row) => `<tr>${row.map((v) => `<td>${Number(v).toFixed(4)}</td>`).join("")}</tr>`)
    .join("");
}

function renderList(elementId, values) {
  const el = document.getElementById(elementId);
  el.innerHTML = (values || []).map((v, i) => `<li>c${i + 1}: ${Number(v).toFixed(6)}</li>`).join("");
}

function renderMathExpression(element, expression) {
  if (!element || !expression) return;
  element.innerHTML = "";
  
  // Wait for KaTeX to be ready
  if (!window.katex) {
    console.warn("KaTeX not loaded yet", expression);
    setTimeout(() => renderMathExpression(element, expression), 50);
    return;
  }
  
  try {
    window.katex.render(expression, element, {
      throwOnError: false,
      displayMode: false,
      strict: false,
      output: "htmlAndMathml"
    });
  } catch (e) {
    console.error("KaTeX render error:", e, expression);
    element.innerHTML = expression;
  }
}

function renderMathById(id, expression) {
  renderMathExpression(document.getElementById(id), expression);
}

function renderTooltipMath(rawText) {
  tooltip.textContent = "";
  const source = String(rawText || "").replace(/\\\\/g, "\\").trim();
  if (!source) return;

  if (!window.katex || !window.katex.renderToString) {
    tooltip.textContent = source;
    return;
  }

  const tokenPattern = /(\$\$[\s\S]+?\$\$|\$[^$\n]+?\$)/g;
  let lastIndex = 0;
  let hasMath = false;

  for (const match of source.matchAll(tokenPattern)) {
    hasMath = true;
    const token = match[0];
    const start = match.index ?? 0;

    if (start > lastIndex) {
      tooltip.appendChild(document.createTextNode(source.slice(lastIndex, start)));
    }

    const displayMode = token.startsWith("$$");
    const expression = token.slice(displayMode ? 2 : 1, displayMode ? -2 : -1).trim();

    if (!expression) {
      tooltip.appendChild(document.createTextNode(token));
    } else {
      const rendered = document.createElement("span");
      try {
        rendered.innerHTML = window.katex.renderToString(expression, {
          throwOnError: false,
          strict: false,
          displayMode,
          trust: false,
          output: "htmlAndMathml",
        });
      } catch (e) {
        rendered.textContent = token;
      }
      tooltip.appendChild(rendered);
    }

    lastIndex = start + token.length;
  }

  if (!hasMath || lastIndex < source.length) {
    tooltip.appendChild(document.createTextNode(source.slice(lastIndex)));
  }
}

function renderStaticMath() {
  document.querySelectorAll(".math-inline[data-latex]").forEach((el) => {
    const latex = el.getAttribute("data-latex") || "";
    renderMathExpression(el, latex);
  });
  
  // Also auto-render any elements with class math-inline
  if (window.renderMathInElement) {
    try {
      window.renderMathInElement(document.body, {
        delimiters: [
          {left: "$$", right: "$$", display: true},
          {left: "$", right: "$", display: false},
          {left: "\\[", right: "\\]", display: true},
          {left: "\\(", right: "\\)", display: false}
        ],
        throwOnError: false,
        strict: false
      });
    } catch (e) {
      console.error("Auto-render error:", e);
    }
  }
}

function updateMathTiles(metrics = null) {
  const strength = Number(controls.strength.value);
  const hue = Number(controls.hue.value);
  const grayscaleEnabled = controls.grayscale.checked;
  const leastSquaresEnabled = metrics ? Boolean(metrics.least_squares_applied) : controls.least_squares.checked;

  renderMathById("transformMain", `T=(1-${strength.toFixed(2)})I+${strength.toFixed(2)}R_{${hue.toFixed(0)}^\\circ}T_p`);
  if (metrics) {
    renderMathById("transformSub", `\\operatorname{rank}(T)=${metrics.rank},\\;\\det(T)=${Number(metrics.determinant).toFixed(3)}`);
  } else {
    renderMathById("transformSub", "v' = Tv");
  }

  if (grayscaleEnabled) {
    renderMathById("projectionMain", "\\operatorname{proj}_u(v)=\\frac{v\\cdot u}{u\\cdot u}u");
    renderMathById("projectionSub", "u=[0.299,0.587,0.114]^T");
  } else {
    renderMathById("projectionMain", "v_{out}=v'");
    renderMathById("projectionSub", "\\text{Projection disabled}");
  }

  renderMathById("leastSquaresMain", "\\hat{X}=\\arg\\min_X \\lVert AX-B\\rVert_F^2");
  renderMathById("leastSquaresSub", leastSquaresEnabled ? "X_{out}=X\\hat{X}" : "\\hat{X}\\;\\text{computed only}");

  renderMathById("covarianceMain", "C=\\frac{1}{N-1}X_c^TX_c");
  if (metrics) {
    const lambda1 = Number((metrics.eigenvalues || [0])[0] || 0).toFixed(4);
    const pc1 = (Number(metrics.principal_variance || 0) * 100).toFixed(2);
    renderMathById("covarianceSub", `\\lambda_1=${lambda1},\\;\\rho_1=${pc1}\\%`);
  } else {
    renderMathById("covarianceSub", "\\text{Awaiting image data}");
  }
}

function updateOutputs() {
  Object.keys(controls).forEach((key) => {
    const out = document.getElementById(`${key}Out`);
    if (!out) return;
    out.textContent = Number(controls[key].value).toFixed(
      key === "hue" || key === "pca_k" || key === "preview_max" ? 0 : 2,
    );
  });
  updateMathTiles();
}

function attachSmartTooltips() {
  const targets = document.querySelectorAll("[data-tip]");
  const gap = 12;

  const placeTooltip = (rect) => {
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    const tw = tooltip.offsetWidth || 260;
    const th = tooltip.offsetHeight || 80;
    const spaces = {
      right: vw - rect.right,
      left: rect.left,
      bottom: vh - rect.bottom,
      top: rect.top,
    };

    let x;
    let y;
    if (spaces.right > tw + gap) {
      x = rect.right + gap;
      y = Math.min(Math.max(rect.top, 8), vh - th - 8);
    } else if (spaces.left > tw + gap) {
      x = rect.left - tw - gap;
      y = Math.min(Math.max(rect.top, 8), vh - th - 8);
    } else if (spaces.bottom > th + gap) {
      x = Math.min(Math.max(rect.left, 8), vw - tw - 8);
      y = rect.bottom + gap;
    } else {
      x = Math.min(Math.max(rect.left, 8), vw - tw - 8);
      y = Math.max(rect.top - th - gap, 8);
    }

    tooltip.style.left = `${x}px`;
    tooltip.style.top = `${y}px`;
  };

  targets.forEach((target) => {
    target.addEventListener("mouseenter", () => {
      if (!captionsEnabled) return;
      const text = target.getAttribute("data-tip");
      if (!text) return;

      renderTooltipMath(text);
      tooltip.classList.add("show");
      placeTooltip(target.getBoundingClientRect());
      requestAnimationFrame(() => placeTooltip(target.getBoundingClientRect()));
    });
    target.addEventListener("mousemove", () => {
      if (!captionsEnabled || !tooltip.classList.contains("show")) return;
      placeTooltip(target.getBoundingClientRect());
    });
    target.addEventListener("mouseleave", () => {
      tooltip.classList.remove("show");
    });
  });
}

function setViewMode(mode) {
  previewGrid.classList.remove("mode-split", "mode-original", "mode-edited");
  previewGrid.classList.add(`mode-${mode}`);
  Object.entries(viewButtons).forEach(([key, button]) => {
    if (button) button.classList.toggle("active", key === mode);
  });
}

function toggleCaptions() {
  captionsEnabled = !captionsEnabled;
  document.body.classList.toggle("show-captions", captionsEnabled);
  toggleCaptionsBtn.textContent = `Math Captions: ${captionsEnabled ? "On" : "Off"}`;
  // Hide tooltip when turning captions off
  if (!captionsEnabled) {
    tooltip.classList.remove("show");
  }
}

function collectFormData() {
  const fd = new FormData();
  fd.append("file", activeFile);
  Object.entries(controls).forEach(([key, ctrl]) => {
    const val = ctrl.type === "checkbox" ? ctrl.checked : ctrl.value;
    fd.append(key, String(val));
  });
  return fd;
}

async function applyFilters() {
  if (!activeFile) return;
  const current = ++requestId;
  setStatus("Applying filters...", "loading");

  try {
    const response = await fetch("/api/apply", { method: "POST", body: collectFormData() });
    const payload = await response.json();
    if (current !== requestId) return;
    if (!response.ok) throw new Error(payload.error || "Failed to process image.");

    filteredPreview.src = payload.image;
    downloadBtn.href = payload.image;
    downloadBtn.classList.remove("disabled");

    const m = payload.metrics;
    document.getElementById("rankValue").textContent = m.rank;
    document.getElementById("nullityValue").textContent = m.nullity;
    document.getElementById("detValue").textContent = formatNumber(m.determinant);
    document.getElementById("condValue").textContent = formatNumber(m.condition_number, 2);
    document.getElementById("invValue").textContent = m.invertible ? "Yes" : "No";
    document.getElementById("traceValue").textContent = formatNumber(m.trace);
    document.getElementById("frobValue").textContent = formatNumber(m.frobenius_norm);
    document.getElementById("pc1Value").textContent = `${formatNumber(Number(m.principal_variance) * 100, 2)}%`;
    document.getElementById("rangeValue").textContent = formatNumber(m.dynamic_range);

    renderTable("matrixTable", m.matrix);
    renderTable("rrefTable", m.rref);
    renderTable("covTable", m.covariance);
    renderTable("lsTable", m.least_squares_matrix);
    renderList("eigenList", m.eigenvalues);
    renderList("varianceList", m.explained_variance);
    renderList("dominantList", m.dominant_eigenvector);
    renderList("meanList", m.mean_rgb);
    renderList("stdList", m.std_rgb);
    updateMathTiles(m);
    setStatus(`Preview updated (${payload.width} x ${payload.height}).`, "ok");
  } catch (err) {
    setStatus(err.message || "Something went wrong.", "error");
  }
}

const applyDebounced = debounce(applyFilters, 220);

async function loadPresets() {
  const fallback = ["Identity", "Sepia", "Cinematic", "Vintage", "Teal and Gold", "Noir", "Cool", "Warm", "No Red"];
  try {
    const response = await fetch("/api/presets");
    const payload = await response.json();
    const presets = payload.presets || fallback;
    controls.preset.innerHTML = presets.map((name) => `<option value="${name}">${name}</option>`).join("");
    controls.preset.value = defaults.preset;
  } catch {
    controls.preset.innerHTML = fallback.map((name) => `<option value="${name}">${name}</option>`).join("");
  }
}

function resetControls() {
  Object.entries(defaults).forEach(([key, val]) => {
    if (controls[key].type === "checkbox") controls[key].checked = val;
    else controls[key].value = val;
  });
  updateOutputs();
  applyDebounced();
}

fileInput.addEventListener("change", () => {
  const file = fileInput.files && fileInput.files[0];
  if (!file) return;
  activeFile = file;
  originalPreview.src = URL.createObjectURL(file);
  updateOutputs();
  applyFilters();
});

Object.values(controls).forEach((ctrl) => {
  ctrl.addEventListener("input", () => {
    updateOutputs();
    applyDebounced();
  });
  ctrl.addEventListener("change", applyDebounced);
});

resetBtn.addEventListener("click", resetControls);
downloadBtn.addEventListener("click", (event) => {
  if (downloadBtn.classList.contains("disabled")) event.preventDefault();
});
viewButtons.split.addEventListener("click", () => setViewMode("split"));
viewButtons.original.addEventListener("click", () => setViewMode("original"));
viewButtons.edited.addEventListener("click", () => setViewMode("edited"));
toggleCaptionsBtn.addEventListener("click", toggleCaptions);

// Wait for KaTeX to load before initializing
function initializeApp() {
  if (!window.katex || !window.renderMathInElement) {
    setTimeout(initializeApp, 100);
    return;
  }
  
  loadPresets();
  updateOutputs();
  renderStaticMath();
  attachSmartTooltips();
  setViewMode("split");
  // Ensure captions start ON
  document.body.classList.add("show-captions");
  toggleCaptionsBtn.textContent = "Math Captions: On";
}

initializeApp();
