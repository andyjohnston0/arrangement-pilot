// static/js/app.js

// Ableton Live color palette mapping (sample indexed colors to hex)
const ABLETON_COLOR_MAP = {
  10: '#b86a34',
  11: '#cc793d',
  12: '#e58c42',
  13: '#f26841',
  14: '#d9532f',
  15: '#e07634',
  17: '#d1893c',
  20: '#8ba644',
  21: '#6f9e38',
  22: '#7fa336',
  24: '#629339',
  25: '#548731',
  26: '#499b42',
  27: '#3ea854',
  31: '#2ea175',
  32: '#289e87',
  35: '#1f9999',
  38: '#2389a6',
  39: '#2d84ad',
  40: '#327fb5',
  41: '#00bcd4',
  42: '#3f78bd',
  43: '#4c6ec4',
  45: '#5d63cc',
  46: '#6d58cf',
  48: '#834ed4',
  50: '#9b44d9',
  53: '#b23ad9',
  54: '#bf34c9',
  60: '#d93690',
  61: '#cc357c',
  62: '#bf346b',
  68: '#e2e8f0'
};

function getTrackHexColor(colorId) {
  return ABLETON_COLOR_MAP[colorId] || '#00e5ff';
}

function getSectionCategory(name) {
  const lower = name.toLowerCase();
  if (lower.includes('intro') || lower.includes('outro') || lower.includes('deconstruction')) {
    return 'type-intro';
  }
  if (lower.includes('incline') || lower.includes('build') || lower.includes('evolution')) {
    return 'type-build';
  }
  if (lower.includes('break') || lower.includes('pit') || lower.includes('breather')) {
    return 'type-break';
  }
  return 'type-peak';
}

let allBlueprints = [];
let currentBlueprint = null;

// DOM Elements
const genreSelect = document.getElementById('genreSelect');
const blueprintSelect = document.getElementById('blueprintSelect');
const bpmInput = document.getElementById('bpmInput');
const resetBpmBtn = document.getElementById('resetBpmBtn');
const clipsToggle = document.getElementById('clipsToggle');
const toggleLabelText = document.getElementById('toggleLabelText');
const generateBtn = document.getElementById('generateBtn');

// Metadata DOM
const metaSubgenre = document.getElementById('metaSubgenre');
const metaDuration = document.getElementById('metaDuration');
const metaBars = document.getElementById('metaBars');
const metaTracks = document.getElementById('metaTracks');
const metaInfluences = document.getElementById('metaInfluences');

// Visualizer DOM
const timelineBlocks = document.getElementById('timelineBlocks');
const trackMatrix = document.getElementById('trackMatrix');

// Tabs DOM
const tabButtons = document.querySelectorAll('.tab-btn');
const tabPanes = document.querySelectorAll('.tab-pane');
const philosophyList = document.getElementById('philosophyList');
const walkthroughList = document.getElementById('walkthroughList');
const soundDesignGrid = document.getElementById('soundDesignGrid');
const tracksTableBody = document.getElementById('tracksTableBody');

// Agent Ingestor DOM
const blueprintJsonInput = document.getElementById('blueprintJsonInput');
const importBlueprintBtn = document.getElementById('importBlueprintBtn');
const loadTemplateBtn = document.getElementById('loadTemplateBtn');
const importStatusMsg = document.getElementById('importStatusMsg');

// --- Initialization ---
async function initApp() {
  setupTabs();
  setupEventListeners();
  await loadBlueprints();
}

function setupTabs() {
  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-tab');
      tabButtons.forEach(b => b.classList.remove('active'));
      tabPanes.forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(targetId).classList.add('active');
    });
  });
}

function setupEventListeners() {
  genreSelect.addEventListener('change', () => {
    filterBlueprintsDropdown();
  });

  blueprintSelect.addEventListener('change', () => {
    loadBlueprintDetail(blueprintSelect.value);
  });

  bpmInput.addEventListener('input', () => {
    updateDurationCalculation();
  });

  resetBpmBtn.addEventListener('click', () => {
    if (currentBlueprint) {
      bpmInput.value = currentBlueprint.bpm;
      updateDurationCalculation();
    }
  });

  clipsToggle.addEventListener('change', () => {
    toggleLabelText.textContent = clipsToggle.checked ? 'Colored Clips' : 'Markers Only';
  });

  generateBtn.addEventListener('click', handleExport);

  importBlueprintBtn.addEventListener('click', handleImportBlueprint);
  if (loadTemplateBtn) {
    loadTemplateBtn.addEventListener('click', handleLoadTemplateExample);
  }
}

// --- Data Fetching ---
async function loadBlueprints() {
  try {
    const res = await fetch('/api/blueprints');
    allBlueprints = await res.json();

    // Populate genres
    const genres = Array.from(new Set(allBlueprints.map(b => b.genre)));
    genreSelect.innerHTML = '<option value="ALL">All Genres</option>';
    genres.forEach(g => {
      const opt = document.createElement('option');
      opt.value = g;
      opt.textContent = g;
      genreSelect.appendChild(opt);
    });

    filterBlueprintsDropdown();
  } catch (err) {
    console.error('Failed to load blueprints:', err);
  }
}

function filterBlueprintsDropdown() {
  const selectedGenre = genreSelect.value;
  const filtered = selectedGenre === 'ALL'
    ? allBlueprints
    : allBlueprints.filter(b => b.genre === selectedGenre);

  blueprintSelect.innerHTML = '';
  filtered.forEach(bp => {
    const opt = document.createElement('option');
    opt.value = bp.id;
    opt.textContent = `[${bp.subgenre || bp.genre}] ${bp.name} (${bp.bpm} BPM)`;
    blueprintSelect.appendChild(opt);
  });

  if (filtered.length > 0) {
    // Prefer raw_hypnotic_chlar as starting default if present
    const defaultBp = filtered.find(b => b.id === 'raw_hypnotic_chlar') || filtered[0];
    blueprintSelect.value = defaultBp.id;
    loadBlueprintDetail(defaultBp.id);
  }
}

async function loadBlueprintDetail(id) {
  try {
    const res = await fetch(`/api/blueprints/${id}`);
    currentBlueprint = await res.json();
    renderBlueprint(currentBlueprint);
  } catch (err) {
    console.error(`Failed to load blueprint ${id}:`, err);
  }
}

// --- Rendering ---
function renderBlueprint(bp) {
  // 1. Controls
  bpmInput.value = bp.bpm;

  // 2. Meta Strip
  metaSubgenre.textContent = `${bp.genre} / ${bp.subgenre}`;
  metaBars.textContent = `${bp.total_bars} bars`;
  metaTracks.textContent = `${bp.tracks.length} tracks`;
  updateDurationCalculation();

  metaInfluences.innerHTML = '';
  (bp.influences || []).forEach(inf => {
    const tag = document.createElement('span');
    tag.className = 'influence-tag';
    tag.textContent = inf;
    metaInfluences.appendChild(tag);
  });

  // 3. Arrangement Timeline Blocks
  renderTimeline(bp);

  // 4. Track Activity Matrix
  renderMatrix(bp);

  // 5. Production Guide & Walkthrough
  renderWalkthrough(bp);

  // 6. Sound Design Recipes
  renderSoundDesign(bp);

  // 7. Track List & Annotations
  renderTracksTable(bp);
}

function updateDurationCalculation() {
  if (!currentBlueprint) return;
  const bpm = parseFloat(bpmInput.value) || currentBlueprint.bpm || 130;
  const totalBars = currentBlueprint.total_bars || 0;
  const totalBeats = totalBars * 4;
  const totalSeconds = (totalBeats / bpm) * 60;
  const mins = Math.floor(totalSeconds / 60);
  const secs = Math.floor(totalSeconds % 60);
  metaDuration.textContent = `${mins}m ${secs < 10 ? '0' : ''}${secs}s`;
}

function renderTimeline(bp) {
  timelineBlocks.innerHTML = '';
  const totalBars = bp.total_bars || 1;

  bp.sections.forEach(sec => {
    const block = document.createElement('div');
    const widthPercent = (sec.bars / totalBars) * 100;
    const catClass = getSectionCategory(sec.name);

    block.className = `timeline-block ${catClass}`;
    block.style.flex = `${sec.bars} 0 0`;
    block.title = `${sec.name}\nDuration: ${sec.bars} bars\nActive: ${sec.active_tracks.join(', ')}\n${sec.description}`;

    block.innerHTML = `
      <div class="block-title">${sec.name}</div>
      <div class="block-bars">${sec.bars} bars</div>
    `;

    timelineBlocks.appendChild(block);
  });
}

function renderMatrix(bp) {
  trackMatrix.innerHTML = '';
  const sections = bp.sections;

  bp.tracks.forEach(track => {
    const row = document.createElement('div');
    row.className = 'matrix-row';

    const hexColor = getTrackHexColor(track.color);

    const label = document.createElement('div');
    label.className = 'matrix-track-label';
    label.title = `${track.name}: ${track.annotation}`;
    label.innerHTML = `
      <span class="matrix-track-dot" style="background-color: ${hexColor}"></span>
      <span>${track.name}</span>
    `;
    row.appendChild(label);

    const cellsWrap = document.createElement('div');
    cellsWrap.className = 'matrix-cells';

    sections.forEach(sec => {
      const cell = document.createElement('div');
      const isActive = sec.active_tracks.includes(track.name);
      cell.className = `matrix-cell ${isActive ? 'active' : ''}`;
      cell.style.flex = `${sec.bars} 0 0`;
      if (isActive) {
        cell.style.setProperty('--track-color', hexColor);
      }
      cell.title = `${track.name} in ${sec.name}: ${isActive ? 'Active' : 'Muted'}`;
      cellsWrap.appendChild(cell);
    });

    row.appendChild(cellsWrap);
    trackMatrix.appendChild(row);
  });
}

function renderWalkthrough(bp) {
  const guide = bp.production_guide || {};

  // Philosophy
  philosophyList.innerHTML = '';
  const philosophies = guide.philosophy || [];
  if (philosophies.length === 0) {
    philosophyList.innerHTML = `
      <div class="philosophy-card" style="border-left-color: var(--text-dim); color: var(--text-muted);">
        <span>No philosophy notes specified for this blueprint. You can include custom ideas under <code>production_guide.philosophy</code> in the JSON.</span>
      </div>
    `;
  } else {
    philosophies.forEach(phil => {
      const card = document.createElement('div');
      card.className = 'philosophy-card';
      card.innerHTML = `<span>${phil}</span>`;
      philosophyList.appendChild(card);
    });
  }

  // Step-by-Step
  walkthroughList.innerHTML = '';
  const steps = guide.step_by_step_walkthrough || [];
  if (steps.length === 0) {
    walkthroughList.innerHTML = `
      <div class="step-card" style="border-color: var(--border-dim); color: var(--text-muted);">
        <p class="step-detail">No step-by-step walkthrough specified. You can add production stages under <code>production_guide.step_by_step_walkthrough</code> in your blueprint.</p>
      </div>
    `;
  } else {
    steps.forEach(st => {
      const card = document.createElement('div');
      card.className = 'step-card';
      card.innerHTML = `
        <div class="step-num">${st.step}</div>
        <div class="step-content">
          <h4 class="step-title">${st.title}</h4>
          <p class="step-detail">${st.detail}</p>
        </div>
      `;
      walkthroughList.appendChild(card);
    });
  }
}

function renderSoundDesign(bp) {
  soundDesignGrid.innerHTML = '';
  const soundDesign = (bp.production_guide && bp.production_guide.sound_design) || {};
  const entries = Object.entries(soundDesign);

  if (entries.length === 0) {
    soundDesignGrid.innerHTML = `
      <div class="recipe-card" style="grid-column: 1 / -1; border-top-color: var(--border-bright);">
        <h4 class="recipe-title">No Recipes Defined</h4>
        <p class="recipe-text">Add sound design recipes to this blueprint under <code>production_guide.sound_design</code>.</p>
      </div>
    `;
  } else {
    entries.forEach(([title, recipe]) => {
      const card = document.createElement('div');
      card.className = 'recipe-card';
      card.innerHTML = `
        <h4 class="recipe-title">${title}</h4>
        <p class="recipe-text">${recipe}</p>
      `;
      soundDesignGrid.appendChild(card);
    });
  }
}

function renderTracksTable(bp) {
  tracksTableBody.innerHTML = '';
  bp.tracks.forEach(track => {
    const hexColor = getTrackHexColor(track.color);
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><span class="track-color-pill" style="background-color: ${hexColor}"></span></td>
      <td class="track-name-cell">${track.name}</td>
      <td class="track-tip-cell">${track.annotation || 'Standard arrangement track.'}</td>
    `;
    tracksTableBody.appendChild(tr);
  });
}

// --- Export Handler ---
async function handleExport() {
  if (!currentBlueprint) return;

  const originalBtnHtml = generateBtn.innerHTML;
  generateBtn.disabled = true;
  generateBtn.innerHTML = `
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin">
      <circle cx="12" cy="12" r="10" stroke-dasharray="32" stroke-dashoffset="12"/>
    </svg>
    Building ALS...
  `;

  try {
    const bpm = parseFloat(bpmInput.value) || currentBlueprint.bpm;
    const includeClips = clipsToggle.checked;

    const response = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        blueprint_id: currentBlueprint.id,
        bpm: bpm,
        include_clips: includeClips
      })
    });

    if (!response.ok) {
      const err = await response.json();
      alert('Export failed: ' + (err.error || 'Server error'));
      return;
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${currentBlueprint.id}_${Math.round(bpm)}bpm.als`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    a.remove();
  } catch (err) {
    console.error('Export request failed:', err);
    alert('Export error. Check console.');
  } finally {
    generateBtn.disabled = false;
    generateBtn.innerHTML = originalBtnHtml;
  }
}

// --- Import Blueprint Handler ---
async function handleImportBlueprint() {
  const jsonText = blueprintJsonInput.value.trim();
  if (!jsonText) {
    importStatusMsg.className = 'status-msg error';
    importStatusMsg.textContent = 'Please paste a valid JSON schema first.';
    return;
  }

  try {
    const payload = JSON.parse(jsonText);
    importStatusMsg.textContent = 'Uploading...';

    const res = await fetch('/api/import_blueprint', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const result = await res.json();
    if (res.ok) {
      importStatusMsg.className = 'status-msg success';
      importStatusMsg.textContent = 'Imported! Refreshing library...';
      blueprintJsonInput.value = '';
      await loadBlueprints();
      blueprintSelect.value = result.id;
      loadBlueprintDetail(result.id);
    } else {
      importStatusMsg.className = 'status-msg error';
      importStatusMsg.textContent = 'Error: ' + (result.error || 'Failed');
    }
  } catch (err) {
    importStatusMsg.className = 'status-msg error';
    importStatusMsg.textContent = 'Invalid JSON: ' + err.message;
  }
}

// --- Load Template Example Handler ---
function handleLoadTemplateExample() {
  const exampleBlueprint = {
    "id": "my_new_genre_blueprint",
    "name": "Hypnotic Minimal Groove",
    "genre": "Techno",
    "subgenre": "Minimal / Hypnotic",
    "bpm": 138,
    "time_signature": "4/4",
    "description": "Clean, hypnotic stripped-back groove focusing on deep sub rolls and evolving micro-textures.",
    "influences": ["Rrose", "Lucy", "Donato Dozzy"],
    "production_guide": {
      "philosophy": [
        "Space and decay times shape the arrangement more than drum layers.",
        "Gradual 32-bar filter movements keep listeners immersed in the hypnosis.",
        "Keep low-end locked in mono below 100Hz."
      ],
      "sound_design": {
        "Sub Roll": "Sine wave with light saturation and sidechain ducking keyed to kick.",
        "Modular Texture": "FM synth with slow random LFO modulating decay time."
      },
      "step_by_step_walkthrough": [
        {
          "step": 1,
          "title": "Establish Fundamental Groove",
          "detail": "Set BPM to 138. Dial in a short punchy kick and the rolling sub foundation."
        },
        {
          "step": 2,
          "title": "Build Micro-Rhythms",
          "detail": "Add 16th hats with subtle swing and polyrhythmic percussion accents."
        },
        {
          "step": 3,
          "title": "Automate Energy along the Timeline",
          "detail": "Use the markers to guide when to open the filter and when to mute the kick."
        }
      ]
    },
    "tracks": [
      { "name": "Kick", "color": 16, "annotation": "Punchy 909 kick transient." },
      { "name": "Sub Roll", "color": 14, "annotation": "Rolling sine sub with sidechain ducking." },
      { "name": "Closed Hats", "color": 22, "annotation": "16th rolling hats with 55% swing." },
      { "name": "Hypnotic Bleep", "color": 41, "annotation": "Slowly modulated FM bleep arpeggio." },
      { "name": "Ambient Drone", "color": 45, "annotation": "Cavernous stereo background drone." }
    ],
    "sections": [
      { "name": "DJ Intro", "bars": 32, "active_tracks": ["Kick", "Sub Roll", "Closed Hats"] },
      { "name": "Groove Build", "bars": 32, "active_tracks": ["Kick", "Sub Roll", "Closed Hats", "Hypnotic Bleep"] },
      { "name": "Main Peak", "bars": 64, "active_tracks": ["Kick", "Sub Roll", "Closed Hats", "Hypnotic Bleep", "Ambient Drone"] },
      { "name": "Breakdown", "bars": 16, "active_tracks": ["Hypnotic Bleep", "Ambient Drone"] },
      { "name": "Climax", "bars": 64, "active_tracks": ["Kick", "Sub Roll", "Closed Hats", "Hypnotic Bleep", "Ambient Drone"] },
      { "name": "DJ Outro", "bars": 32, "active_tracks": ["Kick", "Sub Roll", "Closed Hats"] }
    ]
  };

  blueprintJsonInput.value = JSON.stringify(exampleBlueprint, null, 2);
  importStatusMsg.className = 'status-msg';
  importStatusMsg.textContent = 'Template loaded! Edit any field and click Import.';
}

// Start
document.addEventListener('DOMContentLoaded', initApp);
