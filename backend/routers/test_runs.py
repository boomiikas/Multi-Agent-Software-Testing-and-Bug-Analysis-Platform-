from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from ..models.user import UserDocument
from ..schemas.test_run import RunCreate, RunStatusUpdate, TestRunResponse
from ..services.test_run_service import TestRunService
from ..security.dependencies import get_current_user


router = APIRouter(tags=["runs"])


def get_test_run_service() -> TestRunService:
    return TestRunService()


@router.post("/api/runs", response_model=TestRunResponse, status_code=status.HTTP_201_CREATED)
async def start_run(
    payload: RunCreate,
    current_user: UserDocument = Depends(get_current_user),
    service: TestRunService = Depends(get_test_run_service),
):
    run = await service.create_run(payload, current_user)
    return TestRunResponse(**run.model_dump())


@router.get("/api/runs", response_model=List[TestRunResponse])
async def list_runs(
    projectId: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    current_user: UserDocument = Depends(get_current_user),
    service: TestRunService = Depends(get_test_run_service),
):
    runs = await service.list_runs(projectId, current_user, limit=limit)
    return [TestRunResponse(**r.model_dump()) for r in runs]


@router.get("/api/runs/{run_id}", response_model=TestRunResponse)
async def get_run_status(
    run_id: str,
    current_user: UserDocument = Depends(get_current_user),
    service: TestRunService = Depends(get_test_run_service),
):
    run = await service.get_run(run_id, current_user)
    return TestRunResponse(**run.model_dump())


@router.patch("/api/runs/{run_id}/status", response_model=TestRunResponse)
async def update_run_status(
    run_id: str,
    payload: RunStatusUpdate,
    current_user: UserDocument = Depends(get_current_user),
    service: TestRunService = Depends(get_test_run_service),
):
    updated = await service.update_run_status(run_id, payload, current_user)
    return TestRunResponse(**updated.model_dump())


@router.post("/api/runs/{run_id}/cancel")
async def cancel_run(
    run_id: str,
    current_user: UserDocument = Depends(get_current_user),
    service: TestRunService = Depends(get_test_run_service),
):
    success = await service.cancel_run(run_id, current_user)
    return {"success": success}


@router.post("/api/runs/{run_id}/restart", response_model=TestRunResponse, status_code=status.HTTP_201_CREATED)
async def restart_run(
    run_id: str,
    current_user: UserDocument = Depends(get_current_user),
    service: TestRunService = Depends(get_test_run_service),
):
    new_run = await service.restart_run(run_id, current_user)
    return TestRunResponse(**new_run.model_dump())


@router.get("/api/projects/{project_id}/runs", response_model=List[TestRunResponse])
async def list_project_runs(
    project_id: str,
    limit: int = Query(50, ge=1, le=200),
    current_user: UserDocument = Depends(get_current_user),
    service: TestRunService = Depends(get_test_run_service),
):
    runs = await service.list_runs(project_id, current_user, limit=limit)
    return [TestRunResponse(**r.model_dump()) for r in runs]


@router.get("/api/runs/{run_id}/report")
async def get_run_report(
    run_id: str,
    raw: bool = Query(False),
    format: Optional[str] = Query(None, description="Export format: 'markdown', 'json', or 'html'"),
    current_user: UserDocument = Depends(get_current_user),
    service: TestRunService = Depends(get_test_run_service),
):
    from fastapi.responses import PlainTextResponse, HTMLResponse, JSONResponse
    run = await service.get_run(run_id, current_user)
    report_text = run.report or "No report has been generated yet for this run."

    # Markdown export
    if raw or (format and format.lower() == "markdown"):
        return PlainTextResponse(
            content=report_text,
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename=test_report_{run_id[:8]}.md"} if format == "markdown" else {},
        )

    # Printable HTML / PDF view
    if format and format.lower() == "html":
        # Render a clean, styled HTML report suitable for browser print-to-PDF
        safe_html = report_text.replace("\n", "<br/>").replace("# ", "<h1>").replace("## ", "<h2>").replace("### ", "<h3>")
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8"/>
    <title>AgentQA Test Report - {run_id}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #1e293b; max-width: 900px; margin: 40px auto; padding: 0 20px; }}
        h1, h2, h3 {{ color: #0f172a; margin-top: 1.5em; }}
        .header {{ border-bottom: 2px solid #e2e8f0; padding-bottom: 16px; margin-bottom: 24px; }}
        .badge {{ display: inline-block; padding: 4px 10px; border-radius: 9999px; font-size: 12px; font-weight: 600; text-transform: uppercase; }}
        .badge-completed {{ background: #dcfce7; color: #166534; }}
        .badge-failed {{ background: #fee2e2; color: #991b1b; }}
        .meta-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; background: #f8fafc; padding: 16px; border-radius: 8px; margin: 20px 0; }}
        .btn-print {{ background: #2563eb; color: white; padding: 8px 16px; border-radius: 6px; text-decoration: none; border: none; cursor: pointer; float: right; font-weight: 500; }}
        @media print {{ .btn-print {{ display: none; }} body {{ margin: 0; padding: 0; }} }}
    </style>
</head>
<body>
    <button class="btn-print" onclick="window.print()">Print / Save as PDF</button>
    <div class="header">
        <h1>AgentQA Executive Quality & Test Report</h1>
        <p>Run ID: <code>{run_id}</code> | Project ID: <code>{run.projectId}</code></p>
        <span class="badge badge-{'completed' if run.status == 'completed' else 'failed'}">{run.status}</span>
    </div>
    <div class="meta-grid">
        <div><strong>Duration:</strong> {run.duration or 0}s</div>
        <div><strong>Execution Start:</strong> {run.startTime}</div>
        <div><strong>Steps Completed:</strong> {run.stepsCompleted}/9</div>
        <div><strong>Agent:</strong> {run.agent}</div>
    </div>
    <div class="report-body">
        {safe_html}
    </div>
</body>
</html>"""
        return HTMLResponse(content=html_content)

    # Standard JSON report
    return {
        "runId": run.id,
        "projectId": run.projectId,
        "status": run.status,
        "duration": run.duration,
        "report": report_text,
        "metrics": run.metrics,
        "limitations": run.limitations,
        "apiExecution": run.apiExecution,
        "securityExecution": run.securityExecution,
        "rcaDiagnoses": run.rcaDiagnoses,
        "retryHistory": run.retryHistory,
        "screenshots": run.screenshots,
        "artifacts": run.artifacts,
        "startTime": run.startTime,
        "endTime": run.endTime,
    }


@router.get("/api/runs/{run_id}/artifacts/{filename}")
async def get_run_artifact(
    run_id: str,
    filename: str,
    current_user: UserDocument = Depends(get_current_user),
    service: TestRunService = Depends(get_test_run_service),
):
    import os
    import mimetypes
    from fastapi import HTTPException
    from fastapi.responses import FileResponse

    # Prevent path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename: path traversal is strictly prohibited.",
        )

    # Verify authorization
    await service.get_run(run_id, current_user)

    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    run_dir = os.path.abspath(os.path.join(root_dir, "agent_outputs", "runs", run_id))
    target_path = os.path.abspath(os.path.join(run_dir, filename))

    # Path safety check
    if not target_path.startswith(run_dir):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Path traversal detected.",
        )

    if not os.path.isfile(target_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact '{filename}' not found for run {run_id}.",
        )

    media_type, _ = mimetypes.guess_type(target_path)
    return FileResponse(target_path, media_type=media_type or "application/octet-stream", filename=filename)
