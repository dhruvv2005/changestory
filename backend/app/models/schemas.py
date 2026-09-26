from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class ChangeSummary(BaseModel):
    files_changed: int = 0
    lines_added: int = 0
    lines_deleted: int = 0
    symbols_changed: int = 0
    symbols_affected: int = 0
    potential_risks: int = 0
    test_recommendations: int = 0


class Symbol(BaseModel):
    id: str
    name: str
    qualified_name: str
    type: Literal["function", "method", "class", "async_function", "async_method"]
    file_path: str
    start_line: int
    end_line: int
    parent_class: Optional[str] = None


class RelationshipEvidence(BaseModel):
    file_path: str
    line: int
    snippet: str


class Relationship(BaseModel):
    source: str
    target: str
    relationship: str = "calls"
    evidence: Optional[RelationshipEvidence] = None


class Evidence(BaseModel):
    id: str
    kind: Literal["changed_line", "symbol_def", "call_site", "test_ref", "file_change"]
    file_path: str
    line_start: int
    line_end: int
    symbol: Optional[str] = None
    description: str


class Risk(BaseModel):
    id: str
    severity: Literal["low", "medium", "high"]
    title: str
    description: str
    related_symbols: List[str] = Field(default_factory=list)
    evidence_ids: List[str] = Field(default_factory=list)
    is_potential: bool = True


class TestRecommendation(BaseModel):
    __test__ = False
    id: str
    title: str
    reason: str
    related_symbols: List[str] = Field(default_factory=list)
    evidence_ids: List[str] = Field(default_factory=list)
    confidence: Literal["high", "medium", "low"]
    test_file: Optional[str] = None
    test_symbol: Optional[str] = None


class FileChange(BaseModel):
    file_path: str
    status: Literal["modified", "added", "deleted", "renamed"]
    lines_added: int = 0
    lines_deleted: int = 0
    changed_lines: List[int] = Field(default_factory=list)
    added_lines: List[int] = Field(default_factory=list)
    deleted_lines: List[int] = Field(default_factory=list)
    related_symbols: List[str] = Field(default_factory=list)
    evidence_ids: List[str] = Field(default_factory=list)


class VerificationResult(BaseModel):
    status: Literal["passed", "failed", "error", "not_run"]
    passed: List[str] = Field(default_factory=list)
    failed: List[str] = Field(default_factory=list)
    duration_seconds: float = 0.0
    summary: str


class Explanation(BaseModel):
    symbol: str
    file: str
    lines: str
    caller_count: int
    affected_symbols: List[str] = Field(default_factory=list)
    text: str


class ProjectContext(BaseModel):
    name: str
    root: Optional[str] = None
    git_root: Optional[str] = None
    analysis_mode: Literal["local", "sample", "diff_only"] = "local"


class ChangeStoryReport(BaseModel):
    schema_version: str = "1.0"
    session_id: str
    timestamp: Optional[str] = None
    project: Optional[ProjectContext] = None
    change_summary: ChangeSummary
    files: List[FileChange] = Field(default_factory=list)
    changed_symbols: List[Symbol] = Field(default_factory=list)
    affected_symbols: List[Symbol] = Field(default_factory=list)
    relationships: List[Relationship] = Field(default_factory=list)
    evidence: List[Evidence] = Field(default_factory=list)
    risks: List[Risk] = Field(default_factory=list)
    test_recommendations: List[TestRecommendation] = Field(default_factory=list)
    verification: Optional[VerificationResult] = None
    limitations: List[str] = Field(default_factory=list)
    explanations: List[Explanation] = Field(default_factory=list)


class AnalyzeRequest(BaseModel):
    diff_text: str
    repository_path: Optional[str] = None
    source_mode: Literal["sample", "local", "diff_only"] = "sample"


class VerifyRequest(BaseModel):
    session_id: str
    source_mode: Literal["sample", "local"] = "sample"
