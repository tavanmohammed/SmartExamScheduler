
"use strict";

// The frontend is served from the same FastAPI server.
const API = window.location.origin;

const algorithms = [
  "Auto",
  "Basic Backtracking",
  "MRV",
  "Forward Checking",
  "MRV + Forward Checking",
  "MRV + FC + LCV",
  "MRV + FC + Degree",
  "MRV + FC + Degree + Adaptive LCV"
];

let latestTimetable = [];
let comparisonTimer = null;

const $ = (id) => document.getElementById(id);

function showPage(page) {
  document.querySelectorAll(".page").forEach((section) => {
    section.classList.toggle("active", section.id === page);
  });

  document.querySelectorAll(".nav-btn").forEach((button) => {
    button.classList.toggle(
      "active",
      button.dataset.page === page
    );
  });

  const titles = {
    dashboard: "Dashboard",
    upload: "Upload Dataset",
    manual: "Manual Input",
    timetable: "Exam Timetable",
    comparison: "AI Comparison"
  };

  $("page-title").textContent = titles[page] || "Dashboard";
}

document.querySelectorAll("[data-page]").forEach((button) => {
  button.addEventListener("click", () => {
    showPage(button.dataset.page);
  });
});

function notify(text, error = false) {
  const message = $("message");
  message.hidden = false;
  message.textContent = text;
  message.className = error
    ? "message error"
    : "message success";
}

function setDownload(id, path) {
  const link = $(id);

  if (!path) {
    link.removeAttribute("href");
    link.classList.add("disabled");
    return;
  }

  link.href = new URL(path, API).href;
  link.classList.remove("disabled");
}

function cell(row, value) {
  const td = document.createElement("td");
  td.textContent = value ?? "—";
  row.appendChild(td);
}

async function apiRequest(path, options = {}) {
  let response;

  try {
    response = await fetch(new URL(path, API), options);
  } catch (error) {
    throw new Error(
      "Cannot connect to FastAPI. Is your backend running?"
    );
  }

  const contentType = response.headers.get("content-type") || "";

  const body = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const detail = body?.detail || body?.message || body;

    throw new Error(
      typeof detail === "string"
        ? detail
        : JSON.stringify(detail)
    );
  }

  return body;
}

// -------------------------------------
// API CONNECTION
// -------------------------------------

async function checkBackend() {
  try {
    await apiRequest("/openapi.json");
    $("api-status").textContent = "● Backend connected";
  } catch (error) {
    $("api-status").textContent = "● Backend unavailable";
  }
}

// -------------------------------------
// ALGORITHM DROPDOWN
// -------------------------------------

function initializeAlgorithms() {
  const select = $("upload-algorithm");

  algorithms.forEach((name) => {
    const option = document.createElement("option");
    option.value = name;
    option.textContent = name;
    select.appendChild(option);
  });
}

// -------------------------------------
// EXCEL / JSON / ZIP UPLOAD
// -------------------------------------

$("upload-form").addEventListener("submit", async (event) => {
  event.preventDefault();

  const file = $("file-input").files[0];

  if (!file) {
    notify("Please select a dataset file.", true);
    return;
  }

  const form = new FormData();

  form.append("file", file);
  form.append("algorithm", $("upload-algorithm").value);

  form.append("timeout_seconds", $("timeout").value);
  form.append(
    "compare_timeout_seconds",
    $("compare-timeout").value
  );

  form.append("compare_algorithms", $("compare").checked);

  form.append("start_date", $("start-date").value);
  form.append("end_date", $("end-date").value);

  form.append("start_time", $("start-time").value);
  form.append("end_time", $("end-time").value);

  form.append(
    "include_saturday",
    $("saturday").checked
  );

  form.append(
    "include_sunday",
    $("sunday").checked
  );

  form.append(
    "excluded_dates",
    $("excluded-dates").value
  );

  const button = $("upload-submit");
  button.disabled = true;
  button.textContent = "Generating timetable...";

  notify("Processing your university dataset...");

  try {
    const data = await apiRequest("/schedule/upload", {
      method: "POST",
      body: form
    });

    displayResults(data);
  } catch (error) {
    notify(error.message, true);
  } finally {
    button.disabled = false;
    button.textContent = "Generate Exam Schedule";
  }
});

// -------------------------------------
// SAMPLE MANUAL JSON
// -------------------------------------

const example = {
  departments: {
    Engineering: ["Software Engineering"]
  },

  students: {
    S001: {
      department: "Engineering",
      program: "Software Engineering",
      year: 2,
      courses: ["EX001", "EX002"]
    },
    S002: {
      department: "Engineering",
      program: "Software Engineering",
      year: 2,
      courses: ["EX001", "EX003"]
    },
    S003: {
      department: "Engineering",
      program: "Software Engineering",
      year: 2,
      courses: ["EX002", "EX003"]
    }
  },

  exams: {
    EX001: {
      course_code: "SOFE201",
      name: "Data Structures",
      department: "Engineering",
      programs: ["Software Engineering"],
      professor_id: "P001",
      duration_minutes: 120,
      room_type: "classroom"
    },

    EX002: {
      course_code: "SOFE202",
      name: "Operating Systems",
      department: "Engineering",
      programs: ["Software Engineering"],
      professor_id: "P001",
      duration_minutes: 120,
      room_type: "classroom"
    },

    EX003: {
      course_code: "MATH201",
      name: "Discrete Mathematics",
      department: "Engineering",
      programs: ["Software Engineering"],
      professor_id: "P002",
      duration_minutes: 120,
      room_type: "classroom"
    }
  },

  professors: {
    P001: {
      name: "Professor One",
      unavailable_days: []
    },
    P002: {
      name: "Professor Two",
      unavailable_days: []
    }
  },

  rooms: {
    ROOM_01: {
      exam_capacity: 30,
      room_type: "classroom"
    },
    ROOM_02: {
      exam_capacity: 30,
      room_type: "classroom"
    }
  },

  period: {
    start_date: "2026-12-07",
    end_date: "2026-12-11",
    start_time: "09:00",
    end_time: "15:00",
    include_saturday: false,
    include_sunday: false,
    excluded_dates: "",
    slot_minutes: 180
  },

  algorithm: "Auto",
  timeout_seconds: 30,
  compare_algorithms: true,
  compare_timeout_seconds: 30
};

$("load-example").addEventListener("click", () => {
  $("manual-json").value = JSON.stringify(example, null, 2);
});

$("format-json").addEventListener("click", () => {
  try {
    const parsed = JSON.parse($("manual-json").value);
    $("manual-json").value = JSON.stringify(parsed, null, 2);
  } catch (error) {
    notify("Invalid JSON: " + error.message, true);
  }
});

// -------------------------------------
// MANUAL SCHEDULING
// -------------------------------------

$("manual-form").addEventListener("submit", async (event) => {
  event.preventDefault();

  let payload;

  try {
    payload = JSON.parse($("manual-json").value);
  } catch (error) {
    notify("Invalid manual JSON: " + error.message, true);
    return;
  }

  const button = $("manual-submit");
  button.disabled = true;
  button.textContent = "Generating timetable...";

  notify("Running the manual scheduling algorithm...");

  try {
    const data = await apiRequest("/schedule/manual", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });

    displayResults(data);
  } catch (error) {
    notify(error.message, true);
  } finally {
    button.disabled = false;
    button.textContent = "Generate Manual Timetable";
  }
});

// -------------------------------------
// MAIN RESULTS
// -------------------------------------

function displayResults(data) {
  const result = data.result || data;

  const success = result.success ?? data.success ?? false;
  const status = result.status ?? data.status ?? "UNKNOWN";
  const algorithm = result.algorithm ?? data.algorithm ?? "—";

  const validation = result.validation ?? data.validation;

  latestTimetable = Array.isArray(data.timetable)
    ? data.timetable
    : [];

  $("stat-exams").textContent = latestTimetable.length;

  $("stat-time").textContent =
    result.execution_time != null
      ? Number(result.execution_time).toFixed(3) + " s"
      : "—";

  $("stat-algorithm").textContent = algorithm;

  $("stat-validation").textContent =
    validation?.valid === true
      ? "Valid"
      : validation?.valid === false
        ? "Invalid"
        : "Not checked";

  $("timetable-summary").textContent =
    `${latestTimetable.length} exams | ${algorithm} | ${status}`;

  renderTimetable(latestTimetable);

  setDownload("excel-link", data.download_excel);
  setDownload("csv-link", data.download_csv);

  if (comparisonTimer) {
    clearTimeout(comparisonTimer);
    comparisonTimer = null;
  }

  $("comparison-body").replaceChildren();
  $("comparison-chart").replaceChildren();

  setDownload("comparison-excel", null);
  setDownload("comparison-csv", null);

  $("comparison-status").textContent =
    data.comparison_status || "Not requested";

  if (data.comparison_status_url) {
    pollComparison(data.comparison_status_url);
  } else if (data.algorithm_comparison) {
    renderComparison(data.algorithm_comparison);
  }

  if (success) {
    notify("Timetable generated successfully!");
    showPage("timetable");
  } else {
    notify(
      `Scheduling result: ${status}. No complete timetable found.`,
      true
    );
    showPage("dashboard");
  }
}

// -------------------------------------
// TIMETABLE TABLE
// -------------------------------------

function renderTimetable(rows) {
  const body = $("timetable-body");
  body.replaceChildren();

  if (!rows.length) {
    const tr = document.createElement("tr");
    const td = document.createElement("td");

    td.colSpan = 7;
    td.textContent = "No timetable available.";

    tr.appendChild(td);
    body.appendChild(tr);
    return;
  }

  rows.forEach((exam) => {
    const tr = document.createElement("tr");

    cell(tr, exam.exam_id);
    cell(tr, exam.course_id ?? exam.course_code);
    cell(tr, exam.date);
    cell(tr, exam.start_time);
    cell(tr, exam.end_time);
    cell(tr, exam.room_id);
    cell(tr, exam.professor_id);

    body.appendChild(tr);
  });
}

$("timetable-search").addEventListener("input", (event) => {
  const query = event.target.value.toLowerCase();

  const filtered = latestTimetable.filter((exam) => {
    return Object.values(exam)
      .join(" ")
      .toLowerCase()
      .includes(query);
  });

  renderTimetable(filtered);
});

// -------------------------------------
// BACKGROUND COMPARISON
// -------------------------------------

async function pollComparison(statusPath) {
  const maxAttempts = 120;
  let attempts = 0;

  async function check() {
    try {
      const data = await apiRequest(statusPath);

      const status = String(
        data.comparison_status ?? data.status ?? "PENDING"
      ).toUpperCase();

      $("comparison-status").textContent = status;

      setDownload(
        "comparison-excel",
        data.download_algorithms_excel
      );

      setDownload(
        "comparison-csv",
        data.download_algorithms_csv
      );

      const results =
        data.algorithm_comparison ??
        data.comparison ??
        data.report ??
        data.results;

      if (results) {
        renderComparison(results);
      }

      if (["COMPLETED", "COMPLETE", "DONE", "SUCCESS"].includes(status)) {
        if (!data.download_algorithms_excel && data.job_id) {
          setDownload(
            "comparison-excel",
            `/schedule/download/${data.job_id}/algorithms`
          );
          setDownload(
            "comparison-csv",
            `/schedule/download/${data.job_id}/algorithms/csv`
          );
        }

        notify("Algorithm comparison completed.");
        return;
      }

      if (["FAILED", "ERROR"].includes(status)) {
        notify(
          data.error || "Algorithm comparison failed.",
          true
        );
        return;
      }

      attempts++;

      if (attempts < maxAttempts) {
        comparisonTimer = setTimeout(check, 3000);
      } else {
        $("comparison-status").textContent =
          "Still processing. Refresh to check later.";
      }
    } catch (error) {
      $("comparison-status").textContent =
        "Could not retrieve comparison status.";
      notify(error.message, true);
    }
  }

  check();
}

// -------------------------------------
// COMPARISON RESULTS
// -------------------------------------

function renderComparison(payload) {
  // Supports arrays and common report wrappers.
  let rows = Array.isArray(payload)
    ? payload
    : payload?.algorithms ??
      payload?.results ??
      payload?.comparison ??
      [];

  if (!Array.isArray(rows) && typeof rows === "object") {
    rows = Object.entries(rows).map(([name, value]) => ({
      algorithm: name,
      ...value
    }));
  }

  if (!Array.isArray(rows)) return;

  const body = $("comparison-body");
  const chart = $("comparison-chart");

  body.replaceChildren();
  chart.replaceChildren();

  const maxTime = Math.max(
    1,
    ...rows.map((r) => Number(r.execution_time ?? r.time ?? 0))
  );

  rows.forEach((item) => {
    const name = item.algorithm ?? item.name ?? "Unknown";
    const status = item.status ?? "—";
    const seconds = Number(
      item.execution_time ?? item.time ?? 0
    );

    const tr = document.createElement("tr");

    cell(tr, name);
    cell(tr, status);
    cell(tr, seconds.toFixed(3));
    cell(tr, item.assignments_attempted ?? item.assignments);
    cell(tr, item.backtracks);

    body.appendChild(tr);

    const wrapper = document.createElement("div");
    wrapper.className = "chart-row";

    const title = document.createElement("span");
    title.textContent = name;

    const track = document.createElement("div");
    track.className = "bar-track";

    const bar = document.createElement("div");
    bar.className = "bar";
    bar.style.width = `${(seconds / maxTime) * 100}%`;

    const label = document.createElement("strong");
    label.textContent = seconds.toFixed(2) + " s";

    track.appendChild(bar);

    wrapper.append(title, track, label);
    chart.appendChild(wrapper);
  });
}

// -------------------------------------
// INITIALIZATION
// -------------------------------------

initializeAlgorithms();
$("manual-json").value = JSON.stringify(example, null, 2);
checkBackend();
