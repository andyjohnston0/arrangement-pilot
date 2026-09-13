import copy
import gzip
import io
import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, Optional

DEFAULT_TEMPLATE_PATH = Path(__file__).parent.parent / "TrainingTemplate.als"

def _create_midi_clip(clip_id: int, start_time: float, duration_beats: float, name: str, color_id: int) -> ET.Element:
    t_str = f"{start_time:g}"
    end_str = f"{start_time + duration_beats:g}"
    dur_str = f"{duration_beats:g}"

    clip = ET.Element("MidiClip", {"Id": str(clip_id), "Time": t_str})
    ET.SubElement(clip, "LomId", {"Value": "0"})
    ET.SubElement(clip, "LomIdView", {"Value": "0"})
    ET.SubElement(clip, "CurrentStart", {"Value": t_str})
    ET.SubElement(clip, "CurrentEnd", {"Value": end_str})
    
    loop = ET.SubElement(clip, "Loop")
    ET.SubElement(loop, "LoopStart", {"Value": "0"})
    ET.SubElement(loop, "LoopEnd", {"Value": dur_str})
    ET.SubElement(loop, "StartRelative", {"Value": "0"})
    ET.SubElement(loop, "LoopOn", {"Value": "false"})
    ET.SubElement(loop, "OutMarker", {"Value": dur_str})
    ET.SubElement(loop, "HiddenLoopStart", {"Value": "0"})
    ET.SubElement(loop, "HiddenLoopEnd", {"Value": dur_str})
    
    ET.SubElement(clip, "Name", {"Value": name})
    ET.SubElement(clip, "Annotation", {"Value": ""})
    ET.SubElement(clip, "Color", {"Value": str(color_id)})
    ET.SubElement(clip, "LaunchMode", {"Value": "0"})
    ET.SubElement(clip, "LaunchQuantisation", {"Value": "0"})
    
    ts = ET.SubElement(clip, "TimeSignature")
    tss = ET.SubElement(ts, "TimeSignatures")
    rts = ET.SubElement(tss, "RemoteableTimeSignature", {"Id": "0"})
    ET.SubElement(rts, "Numerator", {"Value": "4"})
    ET.SubElement(rts, "Denominator", {"Value": "4"})
    ET.SubElement(rts, "Time", {"Value": "0"})
    
    env = ET.SubElement(clip, "Envelopes")
    ET.SubElement(env, "Envelopes")
    
    stp = ET.SubElement(clip, "ScrollerTimePreserver")
    ET.SubElement(stp, "LeftTime", {"Value": t_str})
    ET.SubElement(stp, "RightTime", {"Value": end_str})

    tsel = ET.SubElement(clip, "TimeSelection")
    ET.SubElement(tsel, "AnchorTime", {"Value": t_str})
    ET.SubElement(tsel, "OtherTime", {"Value": end_str})
    
    ET.SubElement(clip, "Disabled", {"Value": "false"})
    ET.SubElement(clip, "VelocityAmount", {"Value": "0"})
    ET.SubElement(clip, "FreezeStart", {"Value": "0"})
    ET.SubElement(clip, "FreezeEnd", {"Value": "0"})
    ET.SubElement(clip, "IsWarped", {"Value": "true"})
    ET.SubElement(clip, "TakeId", {"Value": "1"})
    ET.SubElement(clip, "Notes")
    return clip

def generate_als(
    blueprint: Dict[str, Any],
    bpm_override: Optional[float] = None,
    include_clips: bool = True,
    template_path: Optional[Path] = None
) -> bytes:
    path = template_path or DEFAULT_TEMPLATE_PATH
    if not path.exists():
        raise FileNotFoundError(f"Base Ableton template not found at {path}")

    with gzip.open(path, "rb") as f:
        xml_data = f.read()

    root = ET.fromstring(xml_data)
    live_set = root.find("LiveSet")
    if live_set is None:
        raise ValueError("Invalid Ableton file: LiveSet not found")

    next_pointee_el = live_set.find("NextPointeeId")
    current_id = 60000
    if next_pointee_el is not None and "Value" in next_pointee_el.attrib:
        try:
            current_id = max(current_id, int(next_pointee_el.attrib["Value"]) + 100)
        except ValueError:
            pass

    # 1. Update BPM
    bpm = bpm_override if bpm_override is not None else blueprint.get("bpm", 130)
    for tempo_manual in live_set.findall(".//MainTrack/DeviceChain/Mixer/Tempo/Manual"):
        tempo_manual.set("Value", str(bpm))
    for scene_tempo in live_set.findall(".//Scenes//Tempo"):
        if "Value" in scene_tempo.attrib:
            scene_tempo.set("Value", str(bpm))

    # 2. Update Locators
    locators_container = live_set.find("Locators/Locators")
    if locators_container is None:
        locs = live_set.find("Locators")
        if locs is None:
            locs = ET.SubElement(live_set, "Locators")
        locators_container = ET.SubElement(locs, "Locators")
    else:
        locators_container.clear()

    current_beat = 0.0
    sections = blueprint.get("sections", [])
    for idx, sec in enumerate(sections):
        bars = sec.get("bars", 16)
        sec_name = sec.get("name", f"Section {idx + 1}")
        sec_desc = sec.get("description", "")
        locator = ET.SubElement(locators_container, "Locator", {"Id": str(current_id)})
        current_id += 1
        ET.SubElement(locator, "LomId", {"Value": "0"})
        ET.SubElement(locator, "Time", {"Value": str(current_beat)})
        ET.SubElement(locator, "Name", {"Value": f"{sec_name}"})
        ET.SubElement(locator, "Annotation", {"Value": sec_desc})
        ET.SubElement(locator, "IsSongStart", {"Value": "true" if idx == 0 else "false"})
        current_beat += bars * 4.0

    # 3. Build Tracks
    tracks_container = live_set.find("Tracks")
    if tracks_container is None:
        raise ValueError("Tracks container not found in LiveSet")

    prototype_track = None
    for child in tracks_container:
        if child.tag == "MidiTrack":
            prototype_track = copy.deepcopy(child)
            break

    if prototype_track is None:
        raise ValueError("No MidiTrack prototype found in base template")

    events_elem = prototype_track.find(".//ArrangerAutomation/Events")
    if events_elem is not None:
        events_elem.clear()

    # Collect all Pointee IDs (>= 1000) from the prototype to remap them uniquely per track
    prototype_pointee_ids = set()
    for el in prototype_track.iter():
        if "Id" in el.attrib and (el.attrib["Id"].isdigit() and int(el.attrib["Id"]) >= 1000):
            prototype_pointee_ids.add(el.attrib["Id"])

    tracks_container.clear()
    blueprint_tracks = blueprint.get("tracks", [])
    for t_data in blueprint_tracks:
        track_name = t_data.get("name", "Track")
        track_color = t_data.get("color", 13)
        track_annot = t_data.get("annotation", "")
        
        new_track = copy.deepcopy(prototype_track)
        new_track.set("Id", str(current_id))
        current_id += 1

        # Remap all internal Pointee IDs so Ableton Live 12 never encounters duplicate IDs
        for el in new_track.iter():
            if el is not new_track and "Id" in el.attrib:
                if el.attrib["Id"] in prototype_pointee_ids or (el.attrib["Id"].isdigit() and int(el.attrib["Id"]) >= 1000):
                    el.attrib["Id"] = str(current_id)
                    current_id += 1
        
        name_elem = new_track.find("Name")
        if name_elem is not None:
            user_name = name_elem.find("UserName")
            if user_name is not None:
                user_name.set("Value", track_name)
            eff_name = name_elem.find("EffectiveName")
            if eff_name is not None:
                eff_name.set("Value", track_name)
            annot_elem = name_elem.find("Annotation")
            if annot_elem is not None:
                annot_elem.set("Value", track_annot)
            else:
                ET.SubElement(name_elem, "Annotation", {"Value": track_annot})

        color_elem = new_track.find("Color")
        if color_elem is not None:
            color_elem.set("Value", str(track_color))

        if include_clips:
            arr_events = new_track.find(".//ArrangerAutomation/Events")
            if arr_events is not None:
                arr_events.clear()
                clip_time = 0.0
                for sec in sections:
                    bars = sec.get("bars", 16)
                    dur_beats = bars * 4.0
                    active_tracks = sec.get("active_tracks", [])
                    if track_name in active_tracks:
                        clip_name = f"{track_name} [{sec.get('name', 'Part')}]"
                        clip = _create_midi_clip(
                            clip_id=current_id,
                            start_time=clip_time,
                            duration_beats=dur_beats,
                            name=clip_name,
                            color_id=track_color
                        )
                        current_id += 1
                        arr_events.append(clip)
                    clip_time += dur_beats

        tracks_container.append(new_track)

    if next_pointee_el is not None:
        next_pointee_el.set("Value", str(current_id + 100))

    xml_out = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    out_buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=out_buffer, mode="wb") as gz_file:
        gz_file.write(xml_out)
    return out_buffer.getvalue()
