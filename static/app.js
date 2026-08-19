const API = "/api";

const state = {
  mode: "single", // "single" | "compare"
  selected: [],   // array of role labels
  meta: null,
};

async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.json();
}

function fmtPct(pct) {
  return `${Number(pct).toFixed(1)}%`;
}

function sampleBadgeClass(label) {
  const map = {
    "Limited observations": "low",
    "Emerging signal": "mid-low",
    "Moderate evidence": "mid",
    "Strong observed sample": "high",
  };
  return map[label] || "mid";
}

// ---------- Meta / role list ----------

async function loadMeta() {
  const meta = await fetchJSON(`${API}/meta`);
  state.meta = meta;

  document.getElementById("meta-roles").textContent = meta.role_count;
  document.getElementById("meta-industries").textContent = meta.industry_count;
  document.getElementById("meta-postings").textContent = meta.total_postings_analyzed.toLocaleString();
  document.getElementById("meta-updated").textContent = meta.last_updated || "—";

  renderRoleGroups(meta.roles);
}

function renderRoleGroups(roles) {
  const byIndustry = {};
  for (const role of roles) {
    (byIndustry[role.industry] ??= []).push(role);
  }

  const container = document.getElementById("role-groups");
  container.innerHTML = "";

  for (const industry of Object.keys(byIndustry).sort()) {
    const group = document.createElement("div");

    const label = document.createElement("p");
    label.className = "role-group-label";
    label.textContent = industry;
    group.appendChild(label);

    const chips = document.createElement("div");
    chips.className = "role-chips";

    for (const role of byIndustry[industry]) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "role-chip";
      btn.textContent = role.display_name;
      btn.dataset.label = role.label;
      btn.addEventListener("click", () => onRoleChipClick(role.label));
      chips.appendChild(btn);
    }

    group.appendChild(chips);
    container.appendChild(group);
  }
}

function syncChipSelectionUI() {
  document.querySelectorAll(".role-chip").forEach((chip) => {
    chip.classList.toggle("is-selected", state.selected.includes(chip.dataset.label));
  });
}

// ---------- Mode toggle ----------

document.querySelectorAll(".mode-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".mode-btn").forEach((b) => b.classList.remove("is-active"));
    btn.classList.add("is-active");
    state.mode = btn.dataset.mode;
    state.selected = [];
    syncChipSelectionUI();

    const isCompare = state.mode === "compare";
    document.getElementById("compare-hint").hidden = !isCompare;
    document.getElementById("single-view").hidden = isCompare;
    document.getElementById("compare-view").hidden = !isCompare;

    document.getElementById("single-empty").hidden = false;
    document.getElementById("single-content").hidden = true;
    document.getElementById("compare-empty").hidden = false;
    document.getElementById("heat-grid-wrap").hidden = true;
    document.getElementById("compare-summary").hidden = true;
  });
});

// ---------- Role selection behavior ----------

function onRoleChipClick(label) {
  if (state.mode === "single") {
    state.selected = [label];
    syncChipSelectionUI();
    loadSingleRole(label);
    return;
  }

  // compare mode: toggle, cap at 4
  const idx = state.selected.indexOf(label);
  if (idx >= 0) {
    state.selected.splice(idx, 1);
  } else {
    if (state.selected.length >= 4) {
      state.selected.shift(); // drop oldest selection to make room
    }
    state.selected.push(label);
  }
  syncChipSelectionUI();

  if (state.selected.length >= 2) {
    loadComparison(state.selected);
  } else {
    document.getElementById("compare-empty").hidden = false;
    document.getElementById("heat-grid-wrap").hidden = true;
    document.getElementById("compare-summary").hidden = true;
  }
}

// ---------- Single role view ----------

async function loadSingleRole(label) {
  const data = await fetchJSON(`${API}/roles/${encodeURIComponent(label)}`);

  document.getElementById("single-empty").hidden = true;
  document.getElementById("single-content").hidden = false;
  document.getElementById("single-role-name").textContent = data.display_name;
  document.getElementById("single-role-sub").innerHTML =
    `${data.industry} · ${data.total_postings} postings · as of ${data.run_date} ` +
    `<span class="sample-badge sample-badge--${sampleBadgeClass(data.sample_size_label)}">${data.sample_size_label}</span>`;

  const maxPct = Math.max(...data.skills.map((s) => s.pct), 1);
  const list = document.getElementById("skill-bars");
  list.innerHTML = "";

  for (const s of data.skills) {
    const li = document.createElement("li");
    li.className = "skill-bar-row";

    const label_ = document.createElement("span");
    label_.className = "skill-bar-label";
    label_.textContent = s.skill.replace(/_/g, " ");

    const track = document.createElement("span");
    track.className = "skill-bar-track";
    const fill = document.createElement("span");
    fill.className = "skill-bar-fill";
    fill.style.width = `${(s.pct / maxPct) * 100}%`;
    track.appendChild(fill);

    const pct = document.createElement("span");
    pct.className = "skill-bar-pct";
    pct.textContent = `${s.count}/${data.total_postings} · ${fmtPct(s.pct)}`;

    li.append(label_, track, pct);
    list.appendChild(li);
  }

  await loadPostings(label);
}

async function loadPostings(label) {
  const data = await fetchJSON(`${API}/roles/${encodeURIComponent(label)}/postings`);
  const block = document.getElementById("postings-block");
  const emptyMsg = document.getElementById("postings-empty");
  const list = document.getElementById("postings-list");

  if (!data.postings || data.postings.length === 0) {
    block.hidden = true;
    emptyMsg.hidden = false;
    return;
  }

  emptyMsg.hidden = true;
  block.hidden = false;
  list.innerHTML = "";

  for (const p of data.postings) {
    const li = document.createElement("li");
    const a = document.createElement("a");
    a.className = "posting-row";
    a.href = p.url;
    a.target = "_blank";
    a.rel = "noopener noreferrer";

    const metaParts = [p.company, p.location, p.date_posted].filter(Boolean);
    a.innerHTML = `
      <span class="posting-arrow">↗</span>
      <span class="posting-title">${p.title}</span>
      <span class="posting-meta">${metaParts.join(" · ")}</span>
    `;
    li.appendChild(a);
    list.appendChild(li);
  }
}

// ---------- Compare / heat grid view ----------

function heatColor(pct, maxPct) {
  // Amber intensity scaled to this comparison's own max, so the grid
  // stays legible whether the shared skills top out at 5% or 40%.
  const t = Math.min(pct / maxPct, 1);
  const alpha = 0.15 + t * 0.55;
  return `rgba(232, 163, 61, ${alpha.toFixed(2)})`;
}

function renderCompareSummary(roleSkillLists) {
  const summaryEl = document.getElementById("compare-summary");

  const skillSets = roleSkillLists.map(
    (r) => new Set(r.skills.map((s) => s.skill))
  );

  const common = [...skillSets[0]].filter((skill) =>
    skillSets.every((set) => set.has(skill))
  );

  const differentiators = roleSkillLists.map((role, i) => {
    const otherSkills = new Set(
      skillSets.filter((_, j) => j !== i).flatMap((set) => [...set])
    );
    const unique = role.skills
      .filter((s) => !otherSkills.has(s.skill))
      .map((s) => s.skill);
    return { display_name: role.display_name, unique };
  });

  let html = "";

  if (common.length > 0) {
    html += `<div class="compare-summary-row">
      <span class="compare-summary-label">Common to all selected roles</span>
      <span class="compare-summary-tags">${common.map((s) => `<span class="tag tag--common">${s.replace(/_/g, " ")}</span>`).join("")}</span>
    </div>`;
  }

  for (const d of differentiators) {
    if (d.unique.length === 0) continue;
    html += `<div class="compare-summary-row">
      <span class="compare-summary-label">Only in ${d.display_name}</span>
      <span class="compare-summary-tags">${d.unique.map((s) => `<span class="tag tag--unique">${s.replace(/_/g, " ")}</span>`).join("")}</span>
    </div>`;
  }

  if (!html) {
    summaryEl.hidden = true;
    return;
  }

  summaryEl.innerHTML = html;
  summaryEl.hidden = false;
}

async function loadComparison(labels) {
  const [compareData, ...roleSkillLists] = await Promise.all([
    fetchJSON(`${API}/compare?roles=${labels.map(encodeURIComponent).join(",")}`),
    ...labels.map((l) => fetchJSON(`${API}/roles/${encodeURIComponent(l)}?top=50`)),
  ]);

  document.getElementById("compare-empty").hidden = true;
  const wrap = document.getElementById("heat-grid-wrap");
  wrap.hidden = false;

  renderCompareSummary(roleSkillLists);

  const data = compareData;
  const headRow = document.getElementById("heat-grid-head");
  headRow.innerHTML = "<th>Skill</th>" + data.roles.map((r) => `<th>${r.display_name}</th>`).join("");

  const allPcts = data.skills.flatMap((s) => Object.values(s.by_role));
  const maxPct = Math.max(...allPcts, 1);

  const body = document.getElementById("heat-grid-body");
  body.innerHTML = "";

  if (data.skills.length === 0) {
    body.innerHTML = `<tr><td colspan="${data.roles.length + 1}" class="heat-cell is-empty">No skills shared across the selected roles.</td></tr>`;
    return;
  }

  for (const s of data.skills) {
    const tr = document.createElement("tr");
    const th = document.createElement("th");
    th.scope = "row";
    th.textContent = s.skill.replace(/_/g, " ");
    tr.appendChild(th);

    for (const role of data.roles) {
      const td = document.createElement("td");
      const pct = s.by_role[role.label];
      if (pct === undefined) {
        td.className = "heat-cell is-empty";
        td.textContent = "—";
      } else {
        td.className = "heat-cell";
        td.textContent = fmtPct(pct);
        td.style.background = heatColor(pct, maxPct);
      }
      tr.appendChild(td);
    }
    body.appendChild(tr);
  }
}

// ---------- Search ----------

let searchDebounce;
document.getElementById("search-input").addEventListener("input", (e) => {
  clearTimeout(searchDebounce);
  const q = e.target.value.trim();
  if (!q) {
    document.getElementById("search-results").innerHTML = "";
    return;
  }
  searchDebounce = setTimeout(() => runSearch(q), 200);
});

async function runSearch(q) {
  const data = await fetchJSON(`${API}/search?q=${encodeURIComponent(q)}`);
  const list = document.getElementById("search-results");
  list.innerHTML = "";

  if (data.results.length === 0) {
    list.innerHTML = `<li class="search-result-row"><span>No matches for "${q}"</span></li>`;
    return;
  }

  for (const r of data.results.slice(0, 25)) {
    const li = document.createElement("li");
    li.className = "search-result-row";
    li.innerHTML = `
      <span>${r.skill.replace(/_/g, " ")} <span class="search-result-role">— ${r.role_display_name}</span></span>
      <span class="search-result-pct">${fmtPct(r.pct)}</span>
    `;
    list.appendChild(li);
  }
}

async function loadSnapshot() {
  const snap = await fetchJSON(`${API}/snapshot`);

  const skillsList = document.getElementById("snapshot-skills");
  skillsList.innerHTML = snap.top_skills
    .map(
      (s) => `<li class="snapshot-row">
        <span class="snapshot-row-main">${s.skill.replace(/_/g, " ")}<span class="snapshot-row-sub">${s.role_display_name}</span></span>
        <span class="snapshot-row-value">${fmtPct(s.pct)}</span>
      </li>`
    )
    .join("");

  const rolesList = document.getElementById("snapshot-roles");
  rolesList.innerHTML = snap.most_active_roles
    .map(
      (r) => `<li class="snapshot-row">
        <span class="snapshot-row-main">${r.display_name}</span>
        <span class="snapshot-row-value">${r.total_postings}</span>
      </li>`
    )
    .join("");
}

// ---------- Init ----------

Promise.all([loadMeta(), loadSnapshot()]).catch((err) => {
  console.error(err);
  document.querySelector(".lede").textContent =
    "Couldn't load data from the API. Make sure the backend is running.";
});
