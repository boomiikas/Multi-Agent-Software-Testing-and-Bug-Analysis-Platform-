from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from ..models.test_run import RunStatus, coerce_iso


ALLOWED_TRANSITIONS = {
    RunStatus.PENDING: [RunStatus.RUNNING, RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED],
    RunStatus.RUNNING: [RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED],
    RunStatus.COMPLETED: [],  # terminal
    RunStatus.FAILED: [],     # terminal
    RunStatus.CANCELLED: [],  # terminal
}


class RunCreate(BaseModel):
    projectId: str = Field(..., min_length=1)


class RunStatusUpdate(BaseModel):
    status: RunStatus
    stepsCompleted: Optional[int] = Field(None, ge=0, le=9)
    currentStage: Optional[str] = None
    errorTrace: Optional[str] = None
    report: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None


class TestRunResponse(BaseModel):
    id: str
    runId: Optional[str] = None
    projectId: str
    projectName: Optional[str] = None
    status: str
    agent: str = "TestMaster-v3"
    currentStage: Optional[str] = None
    stepsCompleted: int = 0
    totalSteps: int = 9
    logs: List[Dict[str, Any]] = Field(default_factory=list)
    errorTrace: Optional[str] = None
    report: Optional[str] = None
    screenshots: List[str] = Field(default_factory=list)
    artifacts: Dict[str, str] = Field(default_factory=dict)
    stageTimings: Dict[str, float] = Field(default_factory=dict)
    findings: Dict[str, Any] = Field(default_factory=dict)
    apiExecution: Optional[Dict[str, Any]] = None
    securityExecution: Optional[Dict[str, Any]] = None
    rcaDiagnoses: List[Dict[str, Any]] = Field(default_factory=list)
    retryHistory: List[Dict[str, Any]] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    cancelled: bool = False
    metrics: Dict[str, Any] = Field(default_factory=dict)
    duration: Optional[int] = None
    startTime: str
    endTime: Optional[str] = None
    createdAt: str

    model_config = {"extra": "ignore"}

    @field_validator("createdAt", "startTime", "endTime", mode="before")
    @classmethod
    def validate_timestamps(cls, v: Any) -> Optional[str]:
        return coerce_iso(v)

    def model_post_init(self, __context: Any) -> None:
        if not self.runId:
            self.runId = self.id
