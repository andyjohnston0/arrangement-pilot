# engine/blueprint_loader.py
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

BLUEPRINTS_DIR = Path(__file__).parent.parent / 'blueprints'

def get_blueprints_dir() -> Path:
    return BLUEPRINTS_DIR

def list_blueprints() -> List[Dict[str, Any]]:
    blueprints = []
    base_dir = get_blueprints_dir()
    if not base_dir.exists():
        return []

    for file_path in base_dir.rglob('*.json'):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                total_bars = sum(s.get('bars', 0) for s in data.get('sections', []))
                blueprints.append({
                    'id': data.get('id', file_path.stem),
                    'name': data.get('name', 'Untitled'),
                    'genre': data.get('genre', 'General'),
                    'subgenre': data.get('subgenre', ''),
                    'bpm': data.get('bpm', 130),
                    'time_signature': data.get('time_signature', '4/4'),
                    'description': data.get('description', ''),
                    'influences': data.get('influences', []),
                    'total_bars': total_bars,
                    'track_count': len(data.get('tracks', [])),
                    'section_count': len(data.get('sections', []))
                })
        except Exception as e:
            print(f'Error reading blueprint {file_path}: {e}')

    return sorted(blueprints, key=lambda b: (b['genre'], b['subgenre'], b['name']))

def get_blueprint(blueprint_id: str) -> Optional[Dict[str, Any]]:
    base_dir = get_blueprints_dir()
    for file_path in base_dir.rglob('*.json'):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get('id') == blueprint_id or file_path.stem == blueprint_id:
                    total_bars = sum(s.get('bars', 0) for s in data.get('sections', []))
                    data['total_bars'] = total_bars
                    return data
        except Exception as e:
            print(f'Error loading blueprint {file_path}: {e}')
    return None

def get_genres() -> Dict[str, List[str]]:
    blueprints = list_blueprints()
    genres = {}
    for bp in blueprints:
        g = bp['genre']
        sg = bp['subgenre']
        if g not in genres:
            genres[g] = set()
        if sg:
            genres[g].add(sg)
    return {g: sorted(list(sgs)) for g, sgs in genres.items()}