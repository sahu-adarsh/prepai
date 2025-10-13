from fastapi import APIRouter, HTTPException
from app.models.session import TranscriptResponse, TranscriptMessage, EndSessionResponse
from app.services.s3_service import S3Service
from datetime import datetime

router = APIRouter(prefix="/api/interviews", tags=["interviews"])
s3_service = S3Service()

@router.get("/{session_id}/transcript", response_model=TranscriptResponse)
async def get_transcript(session_id: str):
    """Get full interview transcript"""
    try:
        session_data = s3_service.get_session(session_id)

        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")

        transcript_messages = [
            TranscriptMessage(
                role=msg.get("role", ""),
                content=msg.get("content", ""),
                timestamp=msg.get("timestamp", "")
            )
            for msg in session_data.get("transcript", [])
        ]

        return TranscriptResponse(
            session_id=session_id,
            transcript=transcript_messages
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{session_id}/end", response_model=EndSessionResponse)
async def end_interview(session_id: str):
    """End interview session and generate report"""
    try:
        session_data = s3_service.get_session(session_id)

        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")

        # Update session status
        session_data["status"] = "completed"
        session_data["ended_at"] = datetime.utcnow().isoformat()

        success = s3_service.save_session(session_data)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to end session")

        # TODO: Generate performance report using Bedrock Agent
        # This will be implemented in Phase 3

        return EndSessionResponse(
            session_id=session_id,
            status="completed",
            report_url=None  # Will be populated when report generation is implemented
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
