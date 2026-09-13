import io
import os
import time
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file
from engine.blueprint_loader import list_blueprints, get_blueprint, get_genres
from engine.als_generator import generate_als

app = Flask(__name__)

EXPORTS_DIR = Path(__file__).parent / "exports"
MAX_EXPORTS = 5

def save_and_rotate_export(filename: str, als_data: bytes) -> Path:
    """Save generated ALS to exports folder and retain only the latest MAX_EXPORTS files."""
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    target_path = EXPORTS_DIR / filename

    with open(target_path, "wb") as f:
        f.write(als_data)

    # Sort all .als files in exports/ by modification time (oldest first)
    als_files = sorted(
        [p for p in EXPORTS_DIR.glob("*.als") if p.is_file()],
        key=lambda p: p.stat().st_mtime
    )

    # Remove oldest until count <= MAX_EXPORTS
    while len(als_files) > MAX_EXPORTS:
        oldest = als_files.pop(0)
        try:
            oldest.unlink()
            print(f"[Rotation] Removed oldest export: {oldest.name}")
        except Exception as e:
            print(f"[Rotation] Error removing {oldest.name}: {e}")

    return target_path

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/genres", methods=["GET"])
def api_genres():
    return jsonify(get_genres())

@app.route("/api/blueprints", methods=["GET"])
def api_blueprints():
    return jsonify(list_blueprints())

@app.route("/api/blueprints/<blueprint_id>", methods=["GET"])
def api_blueprint_detail(blueprint_id):
    bp = get_blueprint(blueprint_id)
    if bp is None:
        return jsonify({"error": "Blueprint not found"}), 404
    return jsonify(bp)

@app.route("/api/exports", methods=["GET"])
def api_list_exports():
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(
        [p for p in EXPORTS_DIR.glob("*.als") if p.is_file()],
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    return jsonify([{
        "name": p.name,
        "size_kb": round(p.stat().st_size / 1024, 1),
        "mtime": p.stat().st_mtime
    } for p in files])

@app.route("/api/open_exports", methods=["POST"])
def api_open_exports():
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    try:
        os.startfile(str(EXPORTS_DIR))
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/generate", methods=["POST"])
def api_generate():
    data = request.get_json() or {}
    blueprint_id = data.get("blueprint_id")
    if not blueprint_id:
        return jsonify({"error": "Missing blueprint_id"}), 400

    bp = get_blueprint(blueprint_id)
    if not bp:
        return jsonify({"error": f"Blueprint '{blueprint_id}' not found"}), 404

    bpm_override = data.get("bpm")
    if bpm_override is not None:
        try:
            bpm_override = float(bpm_override)
        except (ValueError, TypeError):
            bpm_override = None

    include_clips = data.get("include_clips", True)

    try:
        als_data = generate_als(
            blueprint=bp,
            bpm_override=bpm_override,
            include_clips=include_clips
        )
    except Exception as e:
        return jsonify({"error": f"Failed to generate ALS: {str(e)}"}), 500

    safe_name = bp.get("id", "arrangement").replace(" ", "_")
    bpm_val = int(bpm_override or bp.get("bpm", 130))
    filename = f"{safe_name}_{bpm_val}bpm.als"

    # Automatically save to exports/ folder and rotate oldest when > 5
    save_and_rotate_export(filename, als_data)

    return send_file(
        io.BytesIO(als_data),
        mimetype="application/octet-stream",
        as_attachment=True,
        download_name=filename
    )

@app.route("/api/import_blueprint", methods=["POST"])
def api_import_blueprint():
    data = request.get_json()
    if not data or "id" not in data or "name" not in data or "tracks" not in data or "sections" not in data:
        return jsonify({"error": "Invalid blueprint schema. Must contain id, name, tracks, and sections."}), 400

    import json
    genre = data.get("genre", "Techno").lower().strip()
    target_dir = Path(__file__).parent / "blueprints" / genre
    target_dir.mkdir(parents=True, exist_ok=True)

    safe_id = "".join(c for c in data["id"] if c.isalnum() or c in ("_", "-")).lower()
    file_path = target_dir / f"{safe_id}.json"

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    return jsonify({"success": True, "id": safe_id, "message": f"Blueprint '{data['name']}' saved successfully."})

if __name__ == "__main__":
    print("Starting Arrangement Pilot on http://localhost:5000 ...")
    app.run(host="127.0.0.1", port=5000, debug=True)
