# Arrangement Pilot 🎛️
### Intelligent Arrangement Template Generator for Ableton Live 12

**Arrangement Pilot** is a lightweight local application designed for electronic music producers to escape the 8-bar loop trap. It generates structured, DJ-ready arrangement templates directly exported into native **Ableton Live 12 project files (`.als`)**.

---

## Key Features

1. **Ableton Live 12 Native Output**:
   - **Timeline Cue Locators (Markers)**: Positioned at exact 16/32/64 bar phrase transitions (DJ Intro, Groove Incline, Hypnotic Peak, Breakdown, Climax, Outro).
   - **Pre-Configured Tracks**: Fully colored according to Ableton Live's official palette and named.
   - **In-DAW Track Annotations**: Production tips embedded directly into Ableton's `<Annotation>` field. When you click or hover over a track in Ableton Live 12, the production tip appears right inside **Ableton's Info View**!
   - **Visual Arrangement Blocks (Toggleable)**: Colored arrangement MIDI clips that visually show which tracks are active, building, or muted across each section.

2. **Curated Raw & Hypnotic Techno Blueprints**:
   - **Chlär / Alarico Style**: 140 BPM, driving polyrhythmic grooves, 5/16 meter percussion, continuous modular builds, extended DJ intro/outro.
   - **Oscar Mulero / Lewis Fautzi Style**: 136 BPM, dark cavernous atmosphere, deep tectonic sub rumble, evolving modular textures, subtle 32-bar filter sweeps.
   - **Temudo / Cravo Style**: 137 BPM, clinical transients, syncopated pocket grooves, sharp call-and-response bleeps, sudden mutes.
   - **Classic Deep House**: 124 BPM, Rhodes chords, 909/707 swing, soulful walking bassline (demonstrating multi-genre capability).

3. **Complete Production Guide & Walkthrough**:
   - **Core Philosophy & Key Ideas**: Sound design principles (e.g. groove through micro-variation, avoiding EDM-style drops, polyrhythm displacement).
   - **Sound Design Recipes**: Exact recipes for Kick + Sub Rumble chains, FM modular bleeps, cavernous send reverbs, and swing percussion grids.
   - **Step-by-Step Implementation Guide**: Clear, numbered walkthrough taking you from a blank project to a finished club-ready track.

4. **Extensible Blueprint System**:
   - Easily drop new `.json` files into `blueprints/<genre>/`.
   - Built-in **AI Agent Ingestor** tab to paste new track breakdowns or arrangements.

---

## Quick Start

### 1. Launch the Local Web App
Double-click `run_app.bat` or run in terminal:
```bash
python app.py
```
Open your browser at: **`http://localhost:5000`**

### 2. Ready-to-Open Projects
Three pre-generated Ableton Live 12 templates are already saved in the project root:
- `Chlar_Raw_Hypnotic_140bpm.als`
- `Mulero_Cavernous_Modular_136bpm.als`
- `Temudo_Clinical_Syncopated_137bpm.als`

Double-click any `.als` file to open it directly in Ableton Live 12!

---

## Adding New Genres / Blueprints
Create a JSON file in `blueprints/<genre>/your_style.json` following this schema:
```json
{
  "id": "unique_id",
  "name": "Display Title",
  "genre": "Techno",
  "subgenre": "Raw / Hypnotic",
  "bpm": 140,
  "influences": ["Artist A", "Artist B"],
  "production_guide": {
    "philosophy": ["Philosophy point 1", "Philosophy point 2"],
    "sound_design": { "Kick & Rumble": "Recipe...", "Synths": "Recipe..." },
    "step_by_step_walkthrough": [
      { "step": 1, "title": "Title", "detail": "Details..." }
    ]
  },
  "tracks": [
    { "name": "Kick", "color": 13, "annotation": "909 punch kick..." }
  ],
  "sections": [
    { "name": "DJ Intro", "bars": 32, "active_tracks": ["Kick", "Sub Rumble"] }
  ]
}
```
