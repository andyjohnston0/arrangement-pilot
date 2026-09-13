import io
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file
from engine.blueprint_loader import list_blueprints, get_blueprint, get_genres
from engine.als_generator import generate_als

app = Flask(__name__)

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
    filename = f"{safe_name}_{int(bpm_override or bp.get('bpm', 130))}bpm.als"

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
