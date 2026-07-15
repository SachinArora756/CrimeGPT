"""
AI Investigation Copilot Router

Provides endpoints for creating investigation sessions, uploading evidence,
sending messages, and streaming live investigation progress via SSE.
"""

import os
import uuid
import json
import tempfile
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.database import get_db
from app.services.auth_service import get_current_user, require_min_role
from app.models.user import User, UserRole
from app.models.ai_investigation import AIInvestigationSession, AIInvestigationMessage
from app.schemas.ai_investigation import (
    CreateSessionRequest,
    SendMessageRequest,
    MessageResponse,
    SessionResponse,
    SessionDetailResponse,
    UploadResponse,
)
from app.services.ai_investigation_service import (
    classify_evidence,
    get_tools_for_classification,
    run_investigation,
    handle_followup_message,
    EVIDENCE_DIR,
)
from app.services.detective_chat_service import enhanced_detective_chat, explain_tool_result

router = APIRouter()


@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    body: CreateSessionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_min_role(UserRole.SUB_INSPECTOR)),
):
    """Create a new AI investigation session."""
    session_id = str(uuid.uuid4())
    session = AIInvestigationSession(
        session_id=session_id,
        user_id=current_user.id,
        case_id=body.case_id,
        title=body.title or "New Investigation",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return SessionResponse(
        session_id=session.session_id,
        title=session.title,
        case_id=session.case_id,
        status=session.status,
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=0,
    )


@router.get("/sessions", response_model=list[SessionResponse])
async def list_sessions(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_min_role(UserRole.SUB_INSPECTOR)),
):
    """List the current user's investigation sessions."""
    stmt = (
        select(AIInvestigationSession)
        .where(
            AIInvestigationSession.user_id == current_user.id,
            AIInvestigationSession.status != "archived",
        )
        .order_by(desc(AIInvestigationSession.updated_at))
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    sessions = result.scalars().all()

    responses = []
    for s in sessions:
        count_stmt = select(func.count()).where(AIInvestigationMessage.session_id == s.id)
        count_result = await db.execute(count_stmt)
        msg_count = count_result.scalar() or 0

        responses.append(SessionResponse(
            session_id=s.session_id,
            title=s.title,
            case_id=s.case_id,
            status=s.status,
            created_at=s.created_at,
            updated_at=s.updated_at,
            message_count=msg_count,
        ))

    return responses


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_min_role(UserRole.SUB_INSPECTOR)),
):
    """Get a session with all messages."""
    stmt = select(AIInvestigationSession).where(
        AIInvestigationSession.session_id == session_id,
        AIInvestigationSession.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    msgs_stmt = (
        select(AIInvestigationMessage)
        .where(AIInvestigationMessage.session_id == session.id)
        .order_by(AIInvestigationMessage.created_at)
    )
    msgs_result = await db.execute(msgs_stmt)
    messages = msgs_result.scalars().all()

    return SessionDetailResponse(
        session_id=session.session_id,
        title=session.title,
        case_id=session.case_id,
        status=session.status,
        created_at=session.created_at,
        updated_at=session.updated_at,
        messages=[
            MessageResponse(
                message_id=m.message_id,
                role=m.role,
                content=m.content,
                attachments=m.attachments if isinstance(m.attachments, list) else ([m.attachments] if m.attachments else None),
                tool_executions=m.tool_executions if isinstance(m.tool_executions, list) else ([m.tool_executions] if m.tool_executions else None),
                metadata=m.metadata_,
                created_at=m.created_at,
            )
            for m in messages
        ],
    )


@router.delete("/sessions/{session_id}")
async def archive_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_min_role(UserRole.SUB_INSPECTOR)),
):
    """Archive (soft-delete) a session."""
    stmt = select(AIInvestigationSession).where(
        AIInvestigationSession.session_id == session_id,
        AIInvestigationSession.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.status = "archived"
    session.updated_at = datetime.utcnow()
    await db.commit()
    return {"status": "archived", "session_id": session_id}


@router.post("/sessions/{session_id}/upload", response_model=UploadResponse)
async def upload_evidence(
    session_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_min_role(UserRole.SUB_INSPECTOR)),
):
    """Upload evidence to a session and classify it."""
    stmt = select(AIInvestigationSession).where(
        AIInvestigationSession.session_id == session_id,
        AIInvestigationSession.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    upload_id = str(uuid.uuid4())
    upload_dir = os.path.join(EVIDENCE_DIR, session_id, upload_id)
    os.makedirs(upload_dir, exist_ok=True)

    original_filename = file.filename or "uploaded_file"
    safe_filename = "".join(c for c in original_filename if c.isalnum() or c in "._- ")[:255]
    if not safe_filename:
        safe_filename = "uploaded_file"

    file_path = os.path.join(upload_dir, safe_filename)
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    classification = classify_evidence(file_path, original_filename)

    message_id = str(uuid.uuid4())
    msg = AIInvestigationMessage(
        message_id=message_id,
        session_id=session.id,
        role="user",
        content=f"Uploaded evidence: {original_filename}",
        attachments=[{
            "file_path": file_path,
            "original_filename": original_filename,
            "file_type": classification["type"],
            "mime_type": classification["mime_type"],
            "classification": classification,
            "upload_id": upload_id,
        }],
    )
    db.add(msg)
    session.updated_at = datetime.utcnow()

    if session.title == "New Investigation":
        session.title = f"Investigation: {original_filename}"

    await db.commit()

    return UploadResponse(
        file_path=file_path,
        original_filename=original_filename,
        file_type=classification["type"],
        classification=classification,
        message_id=message_id,
    )


@router.post("/sessions/{session_id}/investigate")
async def investigate(
    session_id: str,
    message: str = Form(""),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_min_role(UserRole.SUB_INSPECTOR)),
):
    """
    Trigger investigation on the most recent upload in this session.
    Returns SSE stream with live progress events.
    """
    stmt = select(AIInvestigationSession).where(
        AIInvestigationSession.session_id == session_id,
        AIInvestigationSession.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    last_upload_stmt = (
        select(AIInvestigationMessage)
        .where(
            AIInvestigationMessage.session_id == session.id,
            AIInvestigationMessage.role == "user",
            AIInvestigationMessage.attachments.isnot(None),
        )
        .order_by(desc(AIInvestigationMessage.created_at))
        .limit(1)
    )
    upload_result = await db.execute(last_upload_stmt)
    upload_msg = upload_result.scalar_one_or_none()

    if not upload_msg or not upload_msg.attachments:
        raise HTTPException(status_code=400, detail="No evidence uploaded in this session yet")

    attachments = upload_msg.attachments if isinstance(upload_msg.attachments, list) else [upload_msg.attachments]
    attachment = attachments[0]
    file_path = attachment["file_path"]
    original_filename = attachment["original_filename"]

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Evidence file not found on disk")

    async def sse_generator():
        all_events = []
        async for event in run_investigation(
            file_path=file_path,
            original_filename=original_filename,
            user_message=message or None,
            user_id=current_user.id,
            case_id=session.case_id,
            db=db,
        ):
            all_events.append(event)
            event_name = event.get("event", "message")
            data_json = json.dumps(event.get("data", {}), default=str)
            yield f"event: {event_name}\ndata: {data_json}\n\n"

        final_event = all_events[-1] if all_events else None
        if final_event and final_event.get("event") == "complete":
            complete_data = final_event["data"]
            assistant_msg_id = str(uuid.uuid4())
            assistant_msg = AIInvestigationMessage(
                message_id=assistant_msg_id,
                session_id=session.id,
                role="assistant",
                content=complete_data.get("report", ""),
                tool_executions=complete_data.get("tool_results"),
                metadata_={
                    "classification": complete_data.get("classification"),
                    "criminal_matches": complete_data.get("criminal_matches"),
                },
            )
            db.add(assistant_msg)
            session.updated_at = datetime.utcnow()
            await db.commit()

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/sessions/{session_id}/message")
async def send_message(
    session_id: str,
    body: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_min_role(UserRole.SUB_INSPECTOR)),
):
    """Send a follow-up message in an existing session."""
    stmt = select(AIInvestigationSession).where(
        AIInvestigationSession.session_id == session_id,
        AIInvestigationSession.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not body.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    user_msg_id = str(uuid.uuid4())
    user_msg = AIInvestigationMessage(
        message_id=user_msg_id,
        session_id=session.id,
        role="user",
        content=body.message,
    )
    db.add(user_msg)
    await db.flush()

    msgs_stmt = (
        select(AIInvestigationMessage)
        .where(AIInvestigationMessage.session_id == session.id)
        .order_by(AIInvestigationMessage.created_at)
    )
    msgs_result = await db.execute(msgs_stmt)
    all_messages = msgs_result.scalars().all()

    history = [
        {
            "role": m.role,
            "content": m.content,
            "tool_executions": m.tool_executions,
        }
        for m in all_messages
    ]

    chat_result = await enhanced_detective_chat(
        case_id=session.case_id,
        session_messages=history,
        user_message=body.message,
        db=db,
    )

    response_text = chat_result["response"]

    assistant_msg_id = str(uuid.uuid4())
    assistant_msg = AIInvestigationMessage(
        message_id=assistant_msg_id,
        session_id=session.id,
        role="assistant",
        content=response_text,
        metadata_={"sources": chat_result.get("sources", []), "confidence": chat_result.get("confidence", 0)},
    )
    db.add(assistant_msg)
    session.updated_at = datetime.utcnow()
    await db.commit()

    return {
        "user_message": {
            "message_id": user_msg_id,
            "role": "user",
            "content": body.message,
            "created_at": datetime.utcnow().isoformat(),
        },
        "assistant_message": {
            "message_id": assistant_msg_id,
            "role": "assistant",
            "content": response_text,
            "created_at": datetime.utcnow().isoformat(),
            "sources": chat_result.get("sources", []),
            "confidence": chat_result.get("confidence", 0),
            "context_used": chat_result.get("context_used", {}),
        },
    }


@router.get("/tool-explanation/{execution_id}")
async def get_tool_explanation(
    execution_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_min_role(UserRole.SUB_INSPECTOR)),
):
    """Get an AI-generated explanation of a specific tool's findings."""
    result = await explain_tool_result(
        tool_key="",
        execution_id=execution_id,
        db=db,
    )
    return result


@router.get("/cases/{case_id}/hypotheses")
async def get_case_hypotheses(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_min_role(UserRole.SUB_INSPECTOR)),
):
    """Generate investigation hypotheses for a case."""
    from app.services.hypothesis_service import get_case_hypotheses as _get_hypotheses
    return await _get_hypotheses(case_id, db)


@router.get("/cases/{case_id}/contradictions")
async def get_case_contradictions(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_min_role(UserRole.SUB_INSPECTOR)),
):
    """Detect contradictions across evidence for a case."""
    from app.services.contradiction_service import detect_contradictions, build_confidence_dashboard
    from app.models.forensic_toolkit import ForensicToolExecution, ExecutionStatus

    exec_stmt = (
        select(ForensicToolExecution)
        .where(ForensicToolExecution.case_id == case_id)
        .where(ForensicToolExecution.status == ExecutionStatus.COMPLETED)
    )
    exec_result = await db.execute(exec_stmt)
    executions = exec_result.scalars().all()

    tool_results = []
    criminal_matches = []
    for exe in executions:
        result = {
            "tool_key": exe.tool_key,
            "status": "completed",
            "confidence": exe.confidence_score,
            "output_data": exe.output_data,
            "execution_id": exe.id,
        }
        tool_results.append(result)
        if exe.tool_key == "face_recognize" and exe.output_data:
            for match in exe.output_data.get("matches", []):
                criminal_matches.append(match)

    contradictions = await detect_contradictions(tool_results, criminal_matches)
    confidence = build_confidence_dashboard(tool_results, criminal_matches, contradictions.get("contradictions", []))

    return {
        "contradictions": contradictions,
        "confidence_dashboard": confidence,
    }


@router.get("/cases/{case_id}/timeline")
async def get_case_timeline(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_min_role(UserRole.SUB_INSPECTOR)),
):
    """Reconstruct the investigation timeline for a case."""
    from app.services.timeline_reconstruction_service import reconstruct_timeline
    return await reconstruct_timeline(case_id, db)


@router.get("/cases/{case_id}/relationship-graph")
async def get_relationship_graph(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_min_role(UserRole.SUB_INSPECTOR)),
):
    """Build the entity relationship graph for a case."""
    from app.services.timeline_reconstruction_service import build_relationship_graph
    return await build_relationship_graph(case_id, db)


@router.get("/cases/{case_id}/executive-summary")
async def get_executive_summary(
    case_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_min_role(UserRole.SUB_INSPECTOR)),
):
    """Generate an executive investigation summary report."""
    from app.services.hypothesis_service import get_case_hypotheses as _get_hypotheses
    from app.services.contradiction_service import detect_contradictions, build_confidence_dashboard
    from app.services.executive_summary_service import generate_executive_summary
    from app.models.forensic_toolkit import ForensicToolExecution, ExecutionStatus
    from app.models.investigation_memory import EvidenceCorrelation

    exec_stmt = (
        select(ForensicToolExecution)
        .where(ForensicToolExecution.case_id == case_id)
        .where(ForensicToolExecution.status == ExecutionStatus.COMPLETED)
    )
    exec_result = await db.execute(exec_stmt)
    executions = exec_result.scalars().all()

    tool_results = []
    criminal_matches = []
    for exe in executions:
        tool_results.append({
            "tool_key": exe.tool_key,
            "status": "completed",
            "confidence": exe.confidence_score,
            "output_data": exe.output_data,
        })
        if exe.tool_key == "face_recognize" and exe.output_data:
            for match in exe.output_data.get("matches", []):
                criminal_matches.append(match)

    hypotheses = await _get_hypotheses(case_id, db)
    contradictions = await detect_contradictions(tool_results, criminal_matches)
    confidence = build_confidence_dashboard(
        tool_results, criminal_matches, contradictions.get("contradictions", []), hypotheses.get("hypotheses"),
    )

    corr_stmt = select(EvidenceCorrelation).where(EvidenceCorrelation.case_id == case_id)
    corr_result = await db.execute(corr_stmt)
    correlations = [
        {"correlation_type": c.correlation_type, "confidence": c.confidence, "details": c.details}
        for c in corr_result.scalars().all()
    ]

    return await generate_executive_summary(
        case_id=case_id,
        hypotheses=hypotheses,
        contradictions=contradictions,
        confidence_dashboard=confidence,
        completeness={},
        correlations=correlations,
        db=db,
    )


@router.post("/cases/{case_id}/evidence/{evidence_id}/reanalyze")
async def reanalyze_evidence(
    case_id: int,
    evidence_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_min_role(UserRole.SUB_INSPECTOR)),
):
    """Check readiness for re-analysis of evidence with updated models."""
    from app.services.executive_summary_service import reanalyze_evidence as _reanalyze
    return await _reanalyze(case_id, evidence_id, db)


@router.post("/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    current_user: User = Depends(require_min_role(UserRole.SUB_INSPECTOR)),
):
    """Transcribe voice audio to text using Whisper for officer dictation."""
    allowed_types = {
        "audio/webm", "audio/ogg", "audio/wav", "audio/mp4",
        "audio/mpeg", "audio/x-wav", "audio/wave", "audio/mp3",
        "video/webm",
    }
    content_type = audio.content_type or ""
    if content_type not in allowed_types:
        raise HTTPException(400, f"Unsupported audio format: {content_type}")

    suffix = ".webm" if "webm" in content_type else ".wav"
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp_path = tmp.name
            content = await audio.read()
            if len(content) > 25 * 1024 * 1024:
                raise HTTPException(413, "Audio file too large (max 25MB)")
            tmp.write(content)

        from app.services.forensic_tools_service import run_audio_transcribe

        result, _ = await run_audio_transcribe(tmp_path, {"model": "base"})

        return {
            "text": result.get("transcription", ""),
            "language": result.get("language", "en"),
            "duration": result.get("duration_seconds"),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Transcription failed: {str(e)}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
