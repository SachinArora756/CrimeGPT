"""Timeline Reconstruction & Relationship Graph Service."""

import json
import asyncio
import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.forensic_toolkit import ForensicToolExecution, ExecutionStatus
from app.models.evidence import Evidence
from app.models.investigation_memory import InvestigationMemory, EvidenceCorrelation

logger = logging.getLogger(__name__)


async def reconstruct_timeline(case_id: int, db: AsyncSession) -> dict:
    """Reconstruct crime timeline from EXIF, metadata, evidence timestamps, and analysis."""
    evidence_stmt = select(Evidence).where(Evidence.case_id == case_id).order_by(Evidence.created_at)
    evidence_result = await db.execute(evidence_stmt)
    evidence_items = evidence_result.scalars().all()

    exec_stmt = (
        select(ForensicToolExecution)
        .where(ForensicToolExecution.case_id == case_id)
        .where(ForensicToolExecution.status == ExecutionStatus.COMPLETED)
    )
    exec_result = await db.execute(exec_stmt)
    executions = exec_result.scalars().all()

    timeline_events = []

    for evidence in evidence_items:
        timeline_events.append({
            "timestamp": evidence.created_at.isoformat() if evidence.created_at else None,
            "type": "evidence_uploaded",
            "title": f"Evidence uploaded: {evidence.original_filename}",
            "description": f"File type: {evidence.file_type}, Size: {evidence.file_size} bytes",
            "source": "system",
            "evidence_id": evidence.id,
            "confidence": 1.0,
        })

    for exe in executions:
        if not exe.output_data:
            continue

        if exe.tool_key == "image_exif":
            exif_data = exe.output_data
            date_taken = exif_data.get("date_taken") or exif_data.get("datetime_original")
            gps = exif_data.get("gps") or exif_data.get("gps_coordinates")

            if date_taken:
                desc = f"Photo captured"
                if gps:
                    desc += f" at GPS: {gps.get('latitude', 'N/A')}, {gps.get('longitude', 'N/A')}"
                timeline_events.append({
                    "timestamp": date_taken,
                    "type": "photo_captured",
                    "title": "Photo/image captured",
                    "description": desc,
                    "source": exe.tool_key,
                    "evidence_id": exe.evidence_id,
                    "confidence": 0.9,
                    "metadata": {"gps": gps} if gps else {},
                })

        elif exe.tool_key == "digital_metadata":
            meta = exe.output_data
            created = meta.get("created_at") or meta.get("file_created")
            modified = meta.get("modified_at") or meta.get("file_modified")

            if created:
                timeline_events.append({
                    "timestamp": created,
                    "type": "file_created",
                    "title": "File originally created",
                    "description": f"Digital file creation timestamp",
                    "source": exe.tool_key,
                    "evidence_id": exe.evidence_id,
                    "confidence": 0.7,
                })
            if modified and modified != created:
                timeline_events.append({
                    "timestamp": modified,
                    "type": "file_modified",
                    "title": "File last modified",
                    "description": "File modification detected",
                    "source": exe.tool_key,
                    "evidence_id": exe.evidence_id,
                    "confidence": 0.7,
                })

        elif exe.tool_key == "audio_transcribe":
            transcription = exe.output_data.get("transcription", exe.output_data.get("text", ""))
            if transcription:
                timeline_events.append({
                    "timestamp": exe.created_at.isoformat() if exe.created_at else None,
                    "type": "audio_evidence",
                    "title": "Audio evidence transcribed",
                    "description": f"Transcription ({len(transcription)} chars): {transcription[:100]}...",
                    "source": exe.tool_key,
                    "evidence_id": exe.evidence_id,
                    "confidence": 0.85,
                })

        elif exe.tool_key in ("face_recognize", "fingerprint_match", "dna_search"):
            matches_count = exe.output_data.get("matches_found", 0)
            if matches_count > 0:
                timeline_events.append({
                    "timestamp": exe.completed_at.isoformat() if exe.completed_at else exe.created_at.isoformat(),
                    "type": "suspect_identified",
                    "title": f"Suspect identified via {exe.tool_key.replace('_', ' ')}",
                    "description": f"{matches_count} match(es) found in criminal database",
                    "source": exe.tool_key,
                    "evidence_id": exe.evidence_id,
                    "confidence": exe.confidence_score or 0.8,
                })

        elif exe.tool_key == "weapon_detect":
            weapons_count = exe.output_data.get("weapons_detected", len(exe.output_data.get("detections", [])))
            if weapons_count > 0:
                timeline_events.append({
                    "timestamp": exe.created_at.isoformat() if exe.created_at else None,
                    "type": "weapon_found",
                    "title": f"Weapon detected in evidence",
                    "description": f"{weapons_count} weapon(s) identified",
                    "source": exe.tool_key,
                    "evidence_id": exe.evidence_id,
                    "confidence": exe.confidence_score or 0.7,
                })

    timeline_events.sort(key=lambda e: e.get("timestamp") or "9999")

    for i, event in enumerate(timeline_events):
        event["order"] = i + 1

    return {
        "events": timeline_events,
        "total_events": len(timeline_events),
        "sources": list(set(e["source"] for e in timeline_events)),
        "time_span": {
            "earliest": timeline_events[0]["timestamp"] if timeline_events else None,
            "latest": timeline_events[-1]["timestamp"] if timeline_events else None,
        },
    }


async def build_relationship_graph(case_id: int, db: AsyncSession) -> dict:
    """Build an interactive relationship graph linking entities across the case."""
    memory_stmt = select(InvestigationMemory).where(InvestigationMemory.case_id == case_id)
    memory_result = await db.execute(memory_stmt)
    memories = memory_result.scalars().all()

    corr_stmt = select(EvidenceCorrelation).where(EvidenceCorrelation.case_id == case_id)
    corr_result = await db.execute(corr_stmt)
    correlations = corr_result.scalars().all()

    evidence_stmt = select(Evidence).where(Evidence.case_id == case_id)
    ev_result = await db.execute(evidence_stmt)
    evidence_map = {e.id: e for e in ev_result.scalars().all()}

    exec_stmt = (
        select(ForensicToolExecution)
        .where(ForensicToolExecution.case_id == case_id)
        .where(ForensicToolExecution.status == ExecutionStatus.COMPLETED)
        .where(ForensicToolExecution.tool_key == "face_recognize")
    )
    exec_result = await db.execute(exec_stmt)
    face_executions = exec_result.scalars().all()

    nodes = []
    edges = []
    node_ids = set()

    case_node_id = f"case_{case_id}"
    nodes.append({
        "id": case_node_id,
        "type": "case",
        "label": f"Case #{case_id}",
        "data": {},
    })
    node_ids.add(case_node_id)

    for ev_id, ev in evidence_map.items():
        node_id = f"evidence_{ev_id}"
        nodes.append({
            "id": node_id,
            "type": "evidence",
            "label": ev.original_filename,
            "data": {"file_type": ev.file_type, "file_size": ev.file_size},
        })
        node_ids.add(node_id)
        edges.append({
            "source": case_node_id,
            "target": node_id,
            "type": "contains",
            "label": "contains",
        })

    suspects_seen = set()
    for exe in face_executions:
        if not exe.output_data:
            continue
        for match in exe.output_data.get("matches", []):
            cid = match.get("criminal_id")
            name = match.get("full_name", "Unknown")
            if cid and cid not in suspects_seen:
                suspects_seen.add(cid)
                node_id = f"suspect_{cid}"
                nodes.append({
                    "id": node_id,
                    "type": "suspect",
                    "label": name,
                    "data": {
                        "criminal_id": cid,
                        "wanted_status": match.get("wanted_status"),
                        "danger_level": match.get("danger_level"),
                    },
                })
                node_ids.add(node_id)

            if cid and exe.evidence_id:
                edges.append({
                    "source": f"evidence_{exe.evidence_id}",
                    "target": f"suspect_{cid}",
                    "type": "identifies",
                    "label": f"face match ({match.get('similarity', 0):.0%})",
                    "confidence": match.get("similarity", 0),
                })

    vehicles_seen = set()
    for mem in memories:
        if mem.finding_type == "vehicle":
            data = mem.finding_data or {}
            vkey = f"{data.get('color', '')}_{data.get('label', '')}".lower()
            if vkey not in vehicles_seen:
                vehicles_seen.add(vkey)
                node_id = f"vehicle_{mem.id}"
                nodes.append({
                    "id": node_id,
                    "type": "vehicle",
                    "label": f"{data.get('color', '')} {data.get('label', 'Vehicle')}".strip(),
                    "data": data,
                })
                node_ids.add(node_id)
                edges.append({
                    "source": f"evidence_{mem.evidence_id}",
                    "target": node_id,
                    "type": "contains_vehicle",
                    "label": "vehicle detected",
                })

        elif mem.finding_type == "weapon":
            data = mem.finding_data or {}
            node_id = f"weapon_{mem.id}"
            nodes.append({
                "id": node_id,
                "type": "weapon",
                "label": data.get("weapon_type", "Weapon"),
                "data": data,
            })
            node_ids.add(node_id)
            edges.append({
                "source": f"evidence_{mem.evidence_id}",
                "target": node_id,
                "type": "contains_weapon",
                "label": "weapon found",
            })

        elif mem.finding_type == "plate":
            data = mem.finding_data or {}
            plate_num = data.get("plate_number", "")
            if plate_num:
                node_id = f"plate_{plate_num}"
                if node_id not in node_ids:
                    nodes.append({
                        "id": node_id,
                        "type": "license_plate",
                        "label": plate_num,
                        "data": data,
                    })
                    node_ids.add(node_id)
                edges.append({
                    "source": f"evidence_{mem.evidence_id}",
                    "target": node_id,
                    "type": "plate_detected",
                    "label": "plate found",
                })

    for corr in correlations:
        source_node = f"evidence_{corr.source_evidence_id}"
        target_node = f"evidence_{corr.target_evidence_id}"
        if source_node in node_ids and target_node in node_ids:
            edges.append({
                "source": source_node,
                "target": target_node,
                "type": "correlated",
                "label": corr.correlation_type.replace("same_", "shared "),
                "confidence": corr.confidence,
            })

    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "suspects": len(suspects_seen),
            "vehicles": len(vehicles_seen),
            "evidence_items": len(evidence_map),
        },
    }
