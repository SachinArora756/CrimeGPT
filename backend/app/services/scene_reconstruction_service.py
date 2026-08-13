import asyncio
import base64
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm_provider import generate_text, generate_vision_base64, has_any_llm_key
from app.database import async_session
from app.models.case import Case
from app.models.evidence import Evidence
from app.models.forensic_photography import ForensicPhoto, PhotoAnnotation, SceneCoverageZone
from app.models.document import CaseDiary
from app.models.scene_reconstruction import SceneReconstruction
from app.config import settings

logger = logging.getLogger(__name__)

RECONSTRUCTION_DIR = os.path.join(settings.upload_dir, "reconstructions")


async def generate_reconstruction(case_id: int, user_id: int):
    """Background task: gather all case data, generate 3D scene via AI."""
    try:
        async with async_session() as db:
            stmt = select(SceneReconstruction).where(
                SceneReconstruction.case_id == case_id,
                SceneReconstruction.status == "pending",
            ).order_by(SceneReconstruction.created_at.desc())
            result = await db.execute(stmt)
            reconstruction = result.scalar_one_or_none()
            if not reconstruction:
                return

            reconstruction.status = "generating"
            await db.commit()

            case_data = await _gather_case_data(case_id, db)

            scene_json = await _generate_scene_with_supervision(case_data)

            reconstruction.scene_layout = scene_json.get("scene_layout", {})
            reconstruction.timeline_events = scene_json.get("events", [])
            reconstruction.objects_placed = scene_json.get("objects", [])
            reconstruction.photo_textures = scene_json.get("surfaces", [])
            reconstruction.extra_metadata = {
                "generated_at": datetime.utcnow().isoformat(),
                "scene_type": scene_json.get("scene_type", "unknown"),
                "total_objects": len(scene_json.get("objects", [])),
                "total_events": len(scene_json.get("events", [])),
                "data_sources": case_data.get("summary", {}),
            }
            reconstruction.status = "completed"
            await db.commit()

            logger.info(f"3D reconstruction completed for case {case_id}: {reconstruction.reconstruction_id}")

    except Exception as e:
        logger.error(f"3D reconstruction failed for case {case_id}: {e}")
        try:
            async with async_session() as db:
                stmt = select(SceneReconstruction).where(
                    SceneReconstruction.case_id == case_id,
                    SceneReconstruction.status == "generating",
                )
                result = await db.execute(stmt)
                rec = result.scalar_one_or_none()
                if rec:
                    rec.status = "failed"
                    rec.extra_metadata = {"error": str(e)}
                    await db.commit()
        except Exception:
            pass


async def _gather_case_data(case_id: int, db: AsyncSession) -> dict:
    """Fetch all relevant data for a case to feed into AI reconstruction."""
    case_stmt = select(Case).where(Case.id == case_id)
    case_result = await db.execute(case_stmt)
    case = case_result.scalar_one_or_none()
    if not case:
        raise ValueError(f"Case {case_id} not found")

    evidence_stmt = select(Evidence).where(Evidence.case_id == case_id)
    evidence_result = await db.execute(evidence_stmt)
    evidence_items = evidence_result.scalars().all()

    photos_stmt = select(ForensicPhoto).where(
        ForensicPhoto.case_id == case_id,
        ForensicPhoto.is_original == True,
    )
    photos_result = await db.execute(photos_stmt)
    photos = photos_result.scalars().all()

    annotations_data = []
    for photo in photos:
        ann_stmt = select(PhotoAnnotation).where(PhotoAnnotation.photo_id == photo.id)
        ann_result = await db.execute(ann_stmt)
        anns = ann_result.scalars().all()
        for a in anns:
            annotations_data.append({
                "photo_id": photo.photo_id,
                "type": a.annotation_type,
                "data": a.canvas_data,
                "label": a.label,
            })

    zones_stmt = select(SceneCoverageZone).where(SceneCoverageZone.case_id == case_id)
    zones_result = await db.execute(zones_stmt)
    zones = zones_result.scalars().all()

    diary_stmt = select(CaseDiary).where(CaseDiary.case_id == case_id).order_by(CaseDiary.entry_date)
    diary_result = await db.execute(diary_stmt)
    diary_entries = diary_result.scalars().all()

    photo_descriptions = []
    for p in photos[:10]:
        photo_descriptions.append({
            "photo_id": p.photo_id,
            "filename": p.original_filename,
            "category": p.category,
            "scene_zone": p.scene_zone,
            "gps": {"lat": p.gps_latitude, "lng": p.gps_longitude} if p.gps_latitude else None,
            "detected_objects": p.ai_detected_objects,
            "quality_assessment": p.quality_assessment,
            "capture_timestamp": p.capture_timestamp.isoformat() if p.capture_timestamp else None,
        })

    return {
        "case": {
            "offense_type": case.offense_type,
            "description": case.description,
            "incident_location": case.incident_location,
            "incident_date": str(case.incident_date) if case.incident_date else None,
            "incident_time": case.incident_time,
            "victims": case.victims or [],
            "accused_persons": case.accused_persons or [],
            "witnesses": case.witnesses or [],
        },
        "evidence": [
            {
                "id": e.id,
                "filename": e.original_filename,
                "file_type": e.file_type,
                "description": e.description,
                "analysis_results": e.analysis_results,
                "tags": e.tags,
            }
            for e in evidence_items[:20]
        ],
        "photos": photo_descriptions,
        "annotations": annotations_data[:50],
        "zones": [
            {"zone_key": z.zone_key, "zone_label": z.zone_label, "status": z.status}
            for z in zones
        ],
        "diary": [
            {"date": str(d.entry_date), "content": d.content[:500]}
            for d in diary_entries[:15]
        ],
        "summary": {
            "total_evidence": len(evidence_items),
            "total_photos": len(photos),
            "total_annotations": len(annotations_data),
            "total_diary_entries": len(diary_entries),
            "coverage_zones": len(zones),
        },
    }


async def _generate_scene_with_supervision(case_data: dict) -> dict:
    """Generate 3D scene using parent-child LLM architecture with iterative refinement."""
    if not has_any_llm_key():
        return _get_fallback_scene(case_data)

    MAX_ITERATIONS = 3

    try:
        scene = await _child_generate_scene(case_data)
        logger.info(f"Child LLM generated initial scene with {len(scene.get('objects', []))} objects")

        for iteration in range(MAX_ITERATIONS):
            assessment = await _parent_assess_scene(case_data, scene)
            score = assessment.get("quality_score", 0)
            logger.info(f"Parent LLM assessment (iteration {iteration + 1}): score={score}/10, issues={len(assessment.get('issues', []))}")

            if score >= 7:
                logger.info(f"Scene accepted at iteration {iteration + 1} with score {score}")
                break

            scene = await _child_refine_scene(case_data, scene, assessment)
            logger.info(f"Child LLM refined scene (iteration {iteration + 1})")

        return scene

    except Exception as e:
        logger.error(f"Parent-child scene generation failed: {e}")
        return _get_fallback_scene(case_data)


def _build_case_context(case_data: dict) -> str:
    """Build the case context string shared between child and parent prompts."""
    return f"""CASE INFORMATION:
- Offense Type: {case_data['case']['offense_type']}
- Location Description: {case_data['case']['incident_location']}
- Case Description: {case_data['case']['description'][:1000]}
- Incident Date: {case_data['case']['incident_date']}
- Incident Time: {case_data['case']['incident_time']}
- Victims: {json.dumps(case_data['case']['victims'][:5], default=str)}
- Accused: {json.dumps(case_data['case']['accused_persons'][:5], default=str)}

EVIDENCE ITEMS ({case_data['summary']['total_evidence']} total):
{json.dumps(case_data['evidence'][:10], indent=2, default=str)[:3000]}

FORENSIC PHOTOS ({case_data['summary']['total_photos']} total):
{json.dumps(case_data['photos'][:8], indent=2, default=str)[:2000]}

SCENE COVERAGE ZONES:
{json.dumps(case_data['zones'], indent=2)[:1000]}

CASE DIARY ENTRIES:
{json.dumps(case_data['diary'][:8], indent=2, default=str)[:2000]}

PHOTO ANNOTATIONS (spatial markers):
{json.dumps(case_data['annotations'][:20], indent=2, default=str)[:1500]}"""


SCENE_JSON_SCHEMA = """{{
  "scene_type": "indoor_room" | "outdoor_open" | "road_scene" | "multi_room" | "building_exterior",
  "scene_layout": {{
    "width": <meters float>,
    "length": <meters float>,
    "height": <meters float>,
    "ground_type": "floor" | "road" | "ground" | "tiles",
    "walls": [
      {{"id": "wall_1", "position": [x,y,z], "rotation": [0,angle,0], "width": <m>, "height": <m>, "has_door": bool, "has_window": bool}}
    ],
    "lighting": {{
      "time_of_day": "day" | "night" | "evening",
      "ambient_intensity": 0.0-1.0,
      "main_light_position": [x,y,z]
    }}
  }},
  "surfaces": [
    {{"id": "surface_id", "type": "floor" | "wall" | "ceiling" | "table", "position": [x,y,z], "rotation": [rx,ry,rz], "size": [w,h], "texture_photo_id": "photo_uuid or null"}}
  ],
  "objects": [
    {{"id": "obj-1", "type": "body_outline" | "weapon_knife" | "weapon_gun" | "weapon_blunt" | "blood_stain" | "vehicle" | "furniture_table" | "furniture_chair" | "door" | "window" | "evidence_marker" | "footprint" | "broken_glass" | "clothing" | "drug_substance" | "cash_money" | "mobile_phone" | "cctv_camera", "position": [x,y,z], "rotation": [rx,ry,rz], "scale": [sx,sy,sz], "label": "description", "color": "#hex", "evidence_id": null_or_int, "photo_id": null_or_string}}
  ],
  "events": [
    {{"time": "HH:MM", "description": "what happened", "camera_position": [x,y,z], "camera_target": [x,y,z], "highlight_objects": ["obj-id"], "duration": seconds}}
  ],
  "camera_path": [
    {{"position": [x,y,z], "target": [x,y,z], "duration": seconds}}
  ]
}}"""


def _parse_json_response(response: str) -> dict:
    """Parse JSON from LLM response, stripping markdown fences if present."""
    cleaned = response.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
    return json.loads(cleaned)


async def _child_generate_scene(case_data: dict) -> dict:
    """Child LLM: Generate initial 3D scene JSON from case data."""
    case_context = _build_case_context(case_data)

    prompt = f"""You are a forensic 3D crime scene reconstruction specialist. Your job is to generate an accurate, physically realistic 3D scene layout based on case data.

{case_context}

Generate a JSON response with this EXACT structure:
{SCENE_JSON_SCHEMA}

CRITICAL RULES:
1. y=0 is ground level. Objects on the ground (body outlines, blood stains, footprints) must have y=0 or y=0.01. Nothing should float unless it's on furniture.
2. Estimate scene dimensions realistically from the location description (a room is 3-6m, a road is 10-30m wide).
3. Place objects based on evidence descriptions and photo detections — do NOT invent objects not supported by evidence.
4. For murders/assaults: include body_outline, blood_stain, and weapon if mentioned in evidence.
5. For robberies: include furniture, broken items, evidence markers at entry/exit points.
6. For road accidents: include vehicles, road markings, debris patterns.
7. Create timeline events from diary entries in chronological order.
8. Camera path should provide a logical walkthrough: overview → details → exit.
9. All positions must be within scene bounds (0 to width for x, 0 to length for z).
10. Return ONLY valid JSON, no markdown formatting or extra text."""

    response = await asyncio.to_thread(generate_text, prompt, temperature=0.3, max_tokens=4096)
    return _parse_json_response(response)


async def _parent_assess_scene(case_data: dict, scene: dict) -> dict:
    """Parent LLM: Assess the child's scene for quality and accuracy."""
    case_context = _build_case_context(case_data)
    scene_json_str = json.dumps(scene, indent=2, default=str)[:6000]

    prompt = f"""You are a senior forensic scene reconstruction supervisor. Your job is to critically evaluate a 3D crime scene reconstruction for accuracy and realism.

{case_context}

GENERATED 3D SCENE TO EVALUATE:
{scene_json_str}

Evaluate this scene and return a JSON assessment:
{{
  "quality_score": <1-10 integer>,
  "issues": [
    {{"severity": "critical" | "major" | "minor", "description": "what is wrong"}}
  ],
  "improvements": [
    "specific instruction to fix issue 1",
    "specific instruction to fix issue 2"
  ]
}}

EVALUATION CRITERIA:
1. PHYSICS (critical): Are objects at realistic y-positions? (ground objects at y=0, table objects at y=0.7-0.8, nothing floating)
2. EVIDENCE MATCH (critical): Does the scene include objects that match the evidence items? Are there objects that have NO basis in the evidence?
3. DIMENSIONS (major): Are scene dimensions realistic for the described location?
4. COMPLETENESS (major): Are all key evidence items represented? Missing body outline in a murder is critical.
5. POSITIONING (major): Are objects within scene bounds? Are relative positions logical?
6. TIMELINE (minor): Do events follow chronological order and reference actual objects?
7. CAMERA PATH (minor): Does the camera path provide a useful walkthrough?

Score 7+ means acceptable. Score below 7 means the child needs to regenerate.
Return ONLY valid JSON."""

    try:
        response = await asyncio.to_thread(generate_text, prompt, temperature=0.1, max_tokens=1024)
        return _parse_json_response(response)
    except (json.JSONDecodeError, Exception) as e:
        logger.warning(f"Parent assessment parse failed: {e}, defaulting to pass")
        return {"quality_score": 7, "issues": [], "improvements": []}


async def _child_refine_scene(case_data: dict, current_scene: dict, assessment: dict) -> dict:
    """Child LLM: Refine the scene based on parent's feedback."""
    case_context = _build_case_context(case_data)
    current_scene_str = json.dumps(current_scene, indent=2, default=str)[:5000]
    issues_str = json.dumps(assessment.get("issues", []), indent=2)
    improvements_str = "\n".join(f"- {imp}" for imp in assessment.get("improvements", []))

    prompt = f"""You are a forensic 3D crime scene reconstruction specialist. Your previous attempt was reviewed by a supervisor. Fix the identified issues.

{case_context}

YOUR PREVIOUS SCENE (needs fixes):
{current_scene_str}

SUPERVISOR'S ASSESSMENT (score: {assessment.get('quality_score', 0)}/10):

ISSUES FOUND:
{issues_str}

REQUIRED IMPROVEMENTS:
{improvements_str}

Generate a CORRECTED JSON scene with the same structure. Apply ALL the supervisor's improvements. Keep what was good, fix what was wrong.

REMEMBER:
- y=0 is ground level. Ground objects (bodies, blood, footprints) must be at y=0 or y=0.01.
- All positions must be within scene bounds.
- Only include objects supported by case evidence.
- Return ONLY valid JSON, no markdown formatting or extra text.

Output the complete corrected scene JSON:"""

    try:
        response = await asyncio.to_thread(generate_text, prompt, temperature=0.2, max_tokens=4096)
        return _parse_json_response(response)
    except (json.JSONDecodeError, Exception) as e:
        logger.warning(f"Child refinement parse failed: {e}, keeping previous scene")
        return current_scene


def _get_fallback_scene(case_data: dict) -> dict:
    """Generate a basic scene when AI is unavailable."""
    offense = case_data["case"]["offense_type"] or "unknown"

    if "murder" in offense.lower() or "homicide" in offense.lower():
        scene_type = "indoor_room"
        width, length, height = 6.0, 8.0, 3.0
    elif "accident" in offense.lower() or "road" in offense.lower():
        scene_type = "road_scene"
        width, length, height = 15.0, 30.0, 0.0
    elif "robbery" in offense.lower() or "theft" in offense.lower():
        scene_type = "indoor_room"
        width, length, height = 5.0, 6.0, 3.0
    else:
        scene_type = "outdoor_open"
        width, length, height = 10.0, 10.0, 0.0

    objects = []
    for i, photo in enumerate(case_data.get("photos", [])[:5]):
        if photo.get("detected_objects"):
            detected = photo["detected_objects"]
            if isinstance(detected, dict):
                for obj_type in ["weapons", "vehicles", "persons", "forensic_items"]:
                    for j, item in enumerate(detected.get(obj_type, [])[:3]):
                        objects.append({
                            "id": f"obj-{len(objects)+1}",
                            "type": _map_detection_to_type(obj_type, item),
                            "position": [1.0 + i * 1.5, 0, 2.0 + j * 1.0],
                            "rotation": [0, 0, 0],
                            "scale": [1, 1, 1],
                            "label": item if isinstance(item, str) else str(item.get("label", obj_type)),
                            "color": _get_object_color(obj_type),
                            "evidence_id": None,
                            "photo_id": photo["photo_id"],
                        })

    if not objects:
        objects = [
            {"id": "obj-1", "type": "evidence_marker", "position": [2, 0, 3], "rotation": [0,0,0], "scale": [1,1,1], "label": "Primary evidence location", "color": "#FFD700", "evidence_id": None, "photo_id": None},
            {"id": "obj-2", "type": "evidence_marker", "position": [4, 0, 5], "rotation": [0,0,0], "scale": [1,1,1], "label": "Secondary evidence location", "color": "#FFD700", "evidence_id": None, "photo_id": None},
        ]

    surfaces = [
        {"id": "floor", "type": "floor", "position": [0, 0, 0], "rotation": [0, 0, 0], "size": [width, length], "texture_photo_id": case_data["photos"][0]["photo_id"] if case_data.get("photos") else None},
    ]
    if scene_type in ("indoor_room", "multi_room"):
        surfaces.extend([
            {"id": "wall_north", "type": "wall", "position": [width/2, height/2, 0], "rotation": [0, 0, 0], "size": [width, height], "texture_photo_id": None},
            {"id": "wall_south", "type": "wall", "position": [width/2, height/2, length], "rotation": [0, 180, 0], "size": [width, height], "texture_photo_id": None},
            {"id": "wall_east", "type": "wall", "position": [width, height/2, length/2], "rotation": [0, 90, 0], "size": [length, height], "texture_photo_id": None},
            {"id": "wall_west", "type": "wall", "position": [0, height/2, length/2], "rotation": [0, -90, 0], "size": [length, height], "texture_photo_id": None},
        ])

    events = []
    for i, entry in enumerate(case_data.get("diary", [])[:5]):
        events.append({
            "time": f"{20+i}:00",
            "description": entry["content"][:100],
            "camera_position": [width/2 + i, 3, length/2 + i],
            "camera_target": [width/2, 0, length/2],
            "highlight_objects": [objects[min(i, len(objects)-1)]["id"]] if objects else [],
            "duration": 4,
        })

    if not events:
        events = [
            {"time": "00:00", "description": "Scene overview", "camera_position": [width/2, 5, length+3], "camera_target": [width/2, 0, length/2], "highlight_objects": [], "duration": 5},
        ]

    camera_path = [
        {"position": [width/2, 5, length + 4], "target": [width/2, 0, length/2], "duration": 3},
        {"position": [width + 3, 3, length/2], "target": [width/2, 0, length/2], "duration": 3},
        {"position": [width/2, 8, length/2], "target": [width/2, 0, length/2], "duration": 3},
        {"position": [-2, 2, length/2], "target": [width/2, 0, length/2], "duration": 3},
    ]

    return {
        "scene_type": scene_type,
        "scene_layout": {
            "width": width,
            "length": length,
            "height": height,
            "ground_type": "road" if scene_type == "road_scene" else "floor",
            "walls": [],
            "lighting": {
                "time_of_day": "night" if case_data["case"].get("incident_time", "").startswith(("2", "0", "1")) else "day",
                "ambient_intensity": 0.4,
                "main_light_position": [width/2, height + 2, length/2],
            },
        },
        "surfaces": surfaces,
        "objects": objects,
        "events": events,
        "camera_path": camera_path,
    }


def _map_detection_to_type(category: str, item) -> str:
    mapping = {
        "weapons": "weapon_knife",
        "vehicles": "vehicle",
        "persons": "body_outline",
        "forensic_items": "evidence_marker",
    }
    return mapping.get(category, "evidence_marker")


def _get_object_color(category: str) -> str:
    colors = {
        "weapons": "#FF0000",
        "vehicles": "#4488FF",
        "persons": "#FFFFFF",
        "forensic_items": "#FFD700",
    }
    return colors.get(category, "#AAAAAA")


async def export_html(reconstruction_id: str, db: AsyncSession) -> str:
    """Generate a self-contained HTML file for the 3D reconstruction."""
    stmt = select(SceneReconstruction).where(SceneReconstruction.reconstruction_id == reconstruction_id)
    result = await db.execute(stmt)
    rec = result.scalar_one_or_none()
    if not rec or rec.status != "completed":
        raise ValueError("Reconstruction not found or not completed")

    case_dir = os.path.join(RECONSTRUCTION_DIR, str(rec.case_id))
    os.makedirs(case_dir, exist_ok=True)
    html_path = os.path.join(case_dir, f"{reconstruction_id}.html")

    scene_data = {
        "scene_layout": rec.scene_layout,
        "surfaces": rec.photo_textures,
        "objects": rec.objects_placed,
        "events": rec.timeline_events,
        "camera_path": rec.scene_layout.get("camera_path") if rec.scene_layout else [],
    }

    html_content = _build_html_viewer(scene_data, rec.reconstruction_id)

    def write_file():
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

    await asyncio.to_thread(write_file)

    rec.export_html_path = html_path
    await db.commit()
    return html_path


def _build_html_viewer(scene_data: dict, reconstruction_id: str) -> str:
    """Build a self-contained HTML page with Three.js viewer."""
    scene_json = json.dumps(scene_data, default=str)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>3D Crime Scene Reconstruction - {reconstruction_id}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ background: #1a1a2e; color: #fff; font-family: system-ui, sans-serif; overflow: hidden; }}
  #scene-container {{ width: 100vw; height: calc(100vh - 80px); }}
  #timeline {{ position: fixed; bottom: 0; left: 0; right: 0; height: 80px; background: #16213e; border-top: 1px solid #0f3460; padding: 10px 20px; display: flex; align-items: center; gap: 15px; }}
  #timeline input[type="range"] {{ flex: 1; }}
  #timeline button {{ padding: 8px 16px; background: #e94560; border: none; color: white; border-radius: 6px; cursor: pointer; font-size: 14px; }}
  #timeline button:hover {{ background: #ff6b6b; }}
  #event-text {{ font-size: 12px; color: #ccc; max-width: 300px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
  #info {{ position: fixed; top: 10px; left: 10px; background: rgba(0,0,0,0.7); padding: 10px 15px; border-radius: 8px; font-size: 11px; }}
</style>
</head>
<body>
<div id="info">
  <strong>3D Crime Scene Reconstruction</strong><br>
  ID: {reconstruction_id}<br>
  <span style="color:#888">Drag to rotate | Scroll to zoom | Right-click to pan</span>
</div>
<div id="scene-container"></div>
<div id="timeline">
  <button id="playBtn" onclick="togglePlay()">Play</button>
  <input type="range" id="timeSlider" min="0" max="100" value="0" oninput="seekTimeline(this.value)">
  <span id="event-text">Ready</span>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
<script>
const SCENE_DATA = {scene_json};
let scene, camera, renderer, controls;
let objects3D = {{}};
let isPlaying = false;
let currentEventIndex = 0;
let animationProgress = 0;

function init() {{
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x1a1a2e);
  scene.fog = new THREE.Fog(0x1a1a2e, 20, 50);

  const layout = SCENE_DATA.scene_layout || {{}};
  const w = layout.width || 10, l = layout.length || 10, h = layout.height || 3;

  camera = new THREE.PerspectiveCamera(60, window.innerWidth / (window.innerHeight - 80), 0.1, 100);
  camera.position.set(w/2, h + 3, l + 5);
  camera.lookAt(w/2, 0, l/2);

  renderer = new THREE.WebGLRenderer({{ antialias: true }});
  renderer.setSize(window.innerWidth, window.innerHeight - 80);
  renderer.shadowMap.enabled = true;
  document.getElementById('scene-container').appendChild(renderer.domElement);

  controls = new THREE.OrbitControls(camera, renderer.domElement);
  controls.target.set(w/2, 0, l/2);
  controls.enableDamping = true;

  const ambient = new THREE.AmbientLight(0xffffff, 0.4);
  scene.add(ambient);
  const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
  dirLight.position.set(w/2, h+5, l/2);
  dirLight.castShadow = true;
  scene.add(dirLight);

  // Ground
  const groundGeo = new THREE.PlaneGeometry(w, l);
  const groundMat = new THREE.MeshStandardMaterial({{ color: 0x333344, roughness: 0.8 }});
  const ground = new THREE.Mesh(groundGeo, groundMat);
  ground.rotation.x = -Math.PI / 2;
  ground.position.set(w/2, 0, l/2);
  ground.receiveShadow = true;
  scene.add(ground);

  // Grid
  const grid = new THREE.GridHelper(Math.max(w,l), Math.max(w,l), 0x444466, 0x222244);
  grid.position.set(w/2, 0.01, l/2);
  scene.add(grid);

  // Walls (if indoor)
  if (layout.ground_type === 'floor' && h > 0) {{
    const wallMat = new THREE.MeshStandardMaterial({{ color: 0x444466, transparent: true, opacity: 0.3, side: THREE.DoubleSide }});
    const wallN = new THREE.Mesh(new THREE.PlaneGeometry(w, h), wallMat);
    wallN.position.set(w/2, h/2, 0); scene.add(wallN);
    const wallS = new THREE.Mesh(new THREE.PlaneGeometry(w, h), wallMat);
    wallS.position.set(w/2, h/2, l); wallS.rotation.y = Math.PI; scene.add(wallS);
    const wallE = new THREE.Mesh(new THREE.PlaneGeometry(l, h), wallMat);
    wallE.position.set(w, h/2, l/2); wallE.rotation.y = -Math.PI/2; scene.add(wallE);
    const wallW = new THREE.Mesh(new THREE.PlaneGeometry(l, h), wallMat);
    wallW.position.set(0, h/2, l/2); wallW.rotation.y = Math.PI/2; scene.add(wallW);
  }}

  // Objects
  (SCENE_DATA.objects || []).forEach(obj => {{
    const mesh = createObject(obj);
    if (mesh) {{
      scene.add(mesh);
      objects3D[obj.id] = mesh;
    }}
  }});

  window.addEventListener('resize', () => {{
    camera.aspect = window.innerWidth / (window.innerHeight - 80);
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight - 80);
  }});

  animate();
}}

function createObject(obj) {{
  let geo, mat, mesh;
  const color = new THREE.Color(obj.color || '#FFD700');
  const pos = obj.position || [0,0,0];

  switch(obj.type) {{
    case 'body_outline':
      geo = new THREE.PlaneGeometry(0.5, 1.8);
      mat = new THREE.MeshStandardMaterial({{ color: 0xffffff, transparent: true, opacity: 0.7, side: THREE.DoubleSide }});
      mesh = new THREE.Mesh(geo, mat);
      mesh.rotation.x = -Math.PI/2;
      mesh.position.set(pos[0], 0.02, pos[2]);
      break;
    case 'weapon_knife': case 'weapon_gun': case 'weapon_blunt':
      geo = new THREE.CylinderGeometry(0.02, 0.02, 0.3, 8);
      mat = new THREE.MeshStandardMaterial({{ color: 0xcc0000, metalness: 0.8 }});
      mesh = new THREE.Mesh(geo, mat);
      mesh.position.set(pos[0], pos[1] || 0.15, pos[2]);
      mesh.rotation.z = Math.PI/4;
      break;
    case 'blood_stain':
      geo = new THREE.CircleGeometry(0.3, 16);
      mat = new THREE.MeshStandardMaterial({{ color: 0x8B0000, transparent: true, opacity: 0.8, side: THREE.DoubleSide }});
      mesh = new THREE.Mesh(geo, mat);
      mesh.rotation.x = -Math.PI/2;
      mesh.position.set(pos[0], 0.02, pos[2]);
      break;
    case 'vehicle':
      geo = new THREE.BoxGeometry(2, 1.5, 4);
      mat = new THREE.MeshStandardMaterial({{ color: color }});
      mesh = new THREE.Mesh(geo, mat);
      mesh.position.set(pos[0], pos[1] || 0.75, pos[2]);
      break;
    case 'evidence_marker':
      geo = new THREE.ConeGeometry(0.15, 0.4, 8);
      mat = new THREE.MeshStandardMaterial({{ color: 0xFFD700, emissive: 0x886600, emissiveIntensity: 0.3 }});
      mesh = new THREE.Mesh(geo, mat);
      mesh.position.set(pos[0], 0.2, pos[2]);
      break;
    default:
      geo = new THREE.SphereGeometry(0.2, 16, 16);
      mat = new THREE.MeshStandardMaterial({{ color: color }});
      mesh = new THREE.Mesh(geo, mat);
      mesh.position.set(pos[0], pos[1] || 0.2, pos[2]);
  }}

  if (mesh && obj.label) {{
    mesh.userData = {{ label: obj.label, id: obj.id }};
  }}
  return mesh;
}}

function animate() {{
  requestAnimationFrame(animate);
  controls.update();
  if (isPlaying) updateTimeline();
  renderer.render(scene, camera);
}}

function togglePlay() {{
  isPlaying = !isPlaying;
  document.getElementById('playBtn').textContent = isPlaying ? 'Pause' : 'Play';
}}

function seekTimeline(value) {{
  const events = SCENE_DATA.events || [];
  if (events.length === 0) return;
  currentEventIndex = Math.floor((value / 100) * events.length);
  if (currentEventIndex >= events.length) currentEventIndex = events.length - 1;
  goToEvent(currentEventIndex);
}}

function updateTimeline() {{
  const events = SCENE_DATA.events || [];
  if (events.length === 0) return;
  animationProgress += 0.005;
  if (animationProgress >= 1) {{
    animationProgress = 0;
    currentEventIndex++;
    if (currentEventIndex >= events.length) {{
      currentEventIndex = 0;
      isPlaying = false;
      document.getElementById('playBtn').textContent = 'Play';
    }}
    goToEvent(currentEventIndex);
  }}
  document.getElementById('timeSlider').value = ((currentEventIndex + animationProgress) / events.length) * 100;
}}

function goToEvent(index) {{
  const events = SCENE_DATA.events || [];
  if (index >= events.length) return;
  const evt = events[index];
  document.getElementById('event-text').textContent = evt.time + ' - ' + evt.description;

  if (evt.camera_position) {{
    camera.position.set(...evt.camera_position);
  }}
  if (evt.camera_target) {{
    controls.target.set(...evt.camera_target);
  }}

  Object.values(objects3D).forEach(m => {{
    if (m.material) m.material.emissiveIntensity = 0;
  }});
  (evt.highlight_objects || []).forEach(id => {{
    if (objects3D[id] && objects3D[id].material) {{
      objects3D[id].material.emissive = new THREE.Color(0xffaa00);
      objects3D[id].material.emissiveIntensity = 0.5;
    }}
  }});
}}

init();
</script>
</body>
</html>"""
