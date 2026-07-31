const API_BASE = "https://zenn-methods.onrender.com";

let currentFileId = null;
let selectedFile = null;

const fileInput = document.getElementById("fileInput");
const chooseFileBtn = document.getElementById("chooseFileBtn");
const fileName = document.getElementById("fileName");
const uploadBtn = document.getElementById("uploadBtn");
const statusBox = document.getElementById("statusBox");
const analysisBox = document.getElementById("analysisBox");
const analysisContent = document.getElementById("analysisContent");
const optimizeBtn = document.getElementById("optimizeBtn");
const resultBox = document.getElementById("resultBox");
const beforeContent = document.getElementById("beforeContent");
const afterContent = document.getElementById("afterContent");
const downloadBtn = document.getElementById("downloadBtn");
const progressWrapper = document.getElementById("progressWrapper");
const progressBar = document.getElementById("progressBar");
const complianceOverall = document.getElementById("complianceOverall");
const complianceList = document.getElementById("complianceList");

function showStatus(message, isError = false) {
  statusBox.textContent = message;
  statusBox.classList.remove("hidden");
  statusBox.style.color = isError ? "#ff6b6b" : "#eee";
}

chooseFileBtn.addEventListener("click", () => fileInput.click());

fileInput.addEventListener("change", () => {
  if (fileInput.files.length > 0) {
    selectedFile = fileInput.files[0];
    fileName.textContent = selectedFile.name;
    uploadBtn.disabled = false;
  }
});

uploadBtn.addEventListener("click", () => {
  if (!selectedFile) return;

  showStatus("Mengupload video...");
  uploadBtn.disabled = true;
  progressWrapper.classList.remove("hidden");
  progressBar.style.width = "0%";

  const formData = new FormData();
  formData.append("file", selectedFile);

  const xhr = new XMLHttpRequest();

  xhr.upload.addEventListener("progress", (event) => {
    if (event.lengthComputable) {
      const percent = Math.round((event.loaded / event.total) * 100);
      progressBar.style.width = `${percent}%`;
      showStatus(`Mengupload... ${percent}%`);
    }
  });

  xhr.addEventListener("load", async () => {
    progressWrapper.classList.add("hidden");

    if (xhr.status >= 200 && xhr.status < 300) {
      const data = JSON.parse(xhr.responseText);
      currentFileId = data.file_id;
      showStatus(`Upload berhasil: ${data.original_filename}`);
      await analyzeVideo(currentFileId);
    } else {
      const err = JSON.parse(xhr.responseText);
      showStatus(`Error: ${err.detail}`, true);
      uploadBtn.disabled = false;
    }
  });

  xhr.addEventListener("error", () => {
    progressWrapper.classList.add("hidden");
    showStatus("Error: Upload gagal (koneksi bermasalah)", true);
    uploadBtn.disabled = false;
  });

  xhr.open("POST", `${API_BASE}/upload`);
  xhr.send(formData);
});

async function analyzeVideo(fileId) {
  showStatus("Menganalisis video...");

  try {
    const res = await fetch(`${API_BASE}/analyze/${fileId}`);
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Analisis gagal");
    }

    const data = await res.json();
    analysisContent.textContent = JSON.stringify(data.analysis, null, 2);
    renderCompliance(data.tiktok_compliance);
    analysisBox.classList.remove("hidden");
    showStatus("Analisis selesai. Silakan tinjau hasilnya lalu klik Optimalkan.");
  } catch (err) {
    showStatus(`Error: ${err.message}`, true);
  }
}

const ICONS = {
  pass: "✔",
  warning: "⚠",
  fail: "✘",
};

const LABELS = {
  pass: "Sesuai Standar TikTok",
  warning: "Perlu Diperhatikan",
  fail: "Tidak Sesuai Standar",
};

function renderCompliance(compliance) {
  if (!compliance) return;

  // Badge status keseluruhan
  complianceOverall.textContent = LABELS[compliance.overall_status] || compliance.overall_status;
  complianceOverall.className = `compliance-overall ${compliance.overall_status}`;

  // List per-kategori
  complianceList.innerHTML = "";

  compliance.checks.forEach((check) => {
    const li = document.createElement("li");

    const icon = document.createElement("span");
    icon.className = `compliance-icon ${check.level}`;
    icon.textContent = ICONS[check.level] || "•";

    const textWrapper = document.createElement("div");
    const categoryLabel = document.createElement("span");
    categoryLabel.className = "compliance-category";
    categoryLabel.textContent = check.category.replace(/_/g, " ") + ": ";

    const message = document.createTextNode(check.message);

    textWrapper.appendChild(categoryLabel);
    textWrapper.appendChild(message);

    li.appendChild(icon);
    li.appendChild(textWrapper);
    complianceList.appendChild(li);
  });
}

optimizeBtn.addEventListener("click", async () => {
  if (!currentFileId) return;

  showStatus("Mengoptimalkan video...");
  optimizeBtn.disabled = true;

  try {
    const res = await fetch(`${API_BASE}/optimize/${currentFileId}`, {
      method: "POST",
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Optimasi gagal");
    }

    const data = await res.json();
    beforeContent.textContent = JSON.stringify(data.before, null, 2);
    afterContent.textContent = JSON.stringify(data.after, null, 2);
    resultBox.classList.remove("hidden");
    showStatus("Optimasi selesai!");
  } catch (err) {
    showStatus(`Error: ${err.message}`, true);
  } finally {
    optimizeBtn.disabled = false;
  }
});

downloadBtn.addEventListener("click", () => {
  if (!currentFileId) return;
  window.open(`${API_BASE}/download/${currentFileId}`, "_blank");
});