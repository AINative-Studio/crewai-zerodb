"""
crewai_zerodb/models.py

Pydantic models + deterministic filter/tag builders for the CrewAI ↔ ZeroDB integration.

Design constraints:
- ZeroDB Vectors: (namespace, vectors, metadata[list[dict]], filter: dict)
- ZeroDB Memory:  (content/title/tags/priority/metadata) + list/search
- Do NOT assume “tables”; everything is JSON metadata + tags.

Compatibility:
- Pydantic v2 (recommended). If you're on v1, see note at bottom.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Sequence, Tuple, Union
from uuid import uuid4

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


# ------------------------------------------------------------------------------
# Constants / Namespace Registry
# ------------------------------------------------------------------------------

class ZeroDBNamespace(str, Enum):
    PLAYBOOKS = "sales_playbooks"
    CASE_STUDIES = "sales_cases"
    ACCOUNTS = "accounts"
    LEADS = "leads"
    OUTREACH_HISTORY = "outreach_history"
    RUN_ARTIFACTS = "crew_runs"


ZERODB_NAMESPACE_MAP: Dict[str, str] = {
    "PLAYBOOKS": ZeroDBNamespace.PLAYBOOKS.value,
    "CASE_STUDIES": ZeroDBNamespace.CASE_STUDIES.value,
    "ACCOUNTS": ZeroDBNamespace.ACCOUNTS.value,
    "LEADS": ZeroDBNamespace.LEADS.value,
    "OUTREACH_HISTORY": ZeroDBNamespace.OUTREACH_HISTORY.value,
    "RUN_ARTIFACTS": ZeroDBNamespace.RUN_ARTIFACTS.value,
}


# ------------------------------------------------------------------------------
# Enums (stages, channels, types)
# ------------------------------------------------------------------------------

Stage = Literal["research", "outreach", "followup"]
Channel = Literal["email", "linkedin", "sms", "call", "other"]

VectorType = Literal[
    "playbook",
    "case_study",
    "account_note",
    "lead_note",
    "outreach",
    "trace",
]

TraceType = Literal["run_summary", "task_summary", "tool_call"]
OutreachStatus = Literal["draft", "sent", "reply_received", "no_reply"]

SourceType = Literal["agent", "human", "import", "internal", "url", "file"]


# ------------------------------------------------------------------------------
# Tag utilities
# ------------------------------------------------------------------------------

def tag(k: str, v: str) -> str:
    k = (k or "").strip()
    v = (v or "").strip()
    if not k or not v:
        raise ValueError("Tag key/value cannot be empty")
    if ":" in k:
        raise ValueError("Tag key must not include ':'")
    return f"{k}:{v}"


def ensure_tag_list(tags: Optional[Sequence[str]]) -> List[str]:
    if not tags:
        return []
    # de-dupe while preserving order
    seen = set()
    out: List[str] = []
    for t in tags:
        if not t or ":" not in t:
            raise ValueError(f"Invalid tag '{t}'. Expected format 'key:value'.")
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


# ------------------------------------------------------------------------------
# Shared Base Models
# ------------------------------------------------------------------------------

class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=False)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SharedVectorMeta(_Base):
    """
    Required on ALL vector metadata entries.
    """
    type: VectorType
    ts: datetime = Field(default_factory=utc_now)
    tags: List[str] = Field(default_factory=list)

    @field_validator("tags")
    @classmethod
    def _validate_tags(cls, v: List[str]) -> List[str]:
        return ensure_tag_list(v)


class SalesScopeMeta(_Base):
    """
    Sales scope identifiers used across memory + vectors.
    """
    account_id: Optional[str] = None
    lead_id: Optional[str] = None

    @model_validator(mode="after")
    def _require_at_least_account_or_lead(self):
        # We allow neither for global artifacts (e.g., playbooks/cases).
        # For account/lead/outreach/trace, those models enforce it.
        return self


class CrewScopeMeta(_Base):
    """
    CrewAI scope identifiers used for run artifacts/traces and optionally for notes.
    """
    crew_id: Optional[str] = None
    agent_id: Optional[str] = None
    run_id: Optional[str] = None
    task_id: Optional[str] = None


# ------------------------------------------------------------------------------
# Vector Metadata Models (per namespace)
# ------------------------------------------------------------------------------

class PlaybookVectorMeta(SharedVectorMeta):
    """
    Namespace: sales_playbooks
    """
    type: Literal["playbook"] = "playbook"

    doc_id: str
    title: str
    source: Literal["internal", "url", "file"]
    url: Optional[str] = None
    section: Optional[str] = None
    chunk_index: int = 0

    # Optional scalars for tighter filtering (preferred over tags if you want strict filters)
    persona: Optional[str] = None
    vertical: Optional[str] = None


class CaseStudyVectorMeta(SharedVectorMeta):
    """
    Namespace: sales_cases
    """
    type: Literal["case_study"] = "case_study"

    doc_id: str
    title: str
    source: Literal["internal", "url", "file"]
    url: Optional[str] = None
    section: Optional[str] = None
    chunk_index: int = 0

    account_id: Optional[str] = None
    industry: Optional[str] = None
    vertical: Optional[str] = None
    persona: Optional[str] = None
    metrics: Optional[List[str]] = None


class AccountNoteVectorMeta(SharedVectorMeta, SalesScopeMeta, CrewScopeMeta):
    """
    Namespace: accounts
    """
    type: Literal["account_note"] = "account_note"

    title: Optional[str] = None
    source: Literal["agent", "human", "import"] = "agent"
    stage: Stage = "research"

    @model_validator(mode="after")
    def _require_account_id(self):
        if not self.account_id:
            raise ValueError("account_id is required for AccountNoteVectorMeta")
        return self


class LeadNoteVectorMeta(SharedVectorMeta, SalesScopeMeta, CrewScopeMeta):
    """
    Namespace: leads
    """
    type: Literal["lead_note"] = "lead_note"

    source: Literal["agent", "human", "import"] = "agent"
    stage: Stage = "research"

    @model_validator(mode="after")
    def _require_lead_and_account(self):
        if not self.lead_id:
            raise ValueError("lead_id is required for LeadNoteVectorMeta")
        if not self.account_id:
            raise ValueError("account_id is required for LeadNoteVectorMeta")
        return self


class OutreachVectorMeta(SharedVectorMeta, SalesScopeMeta, CrewScopeMeta):
    """
    Namespace: outreach_history
    """
    type: Literal["outreach"] = "outreach"

    artifact_id: str = Field(default_factory=lambda: f"out_{uuid4().hex}")
    channel: Channel = "email"
    variant: Optional[str] = None
    status: OutreachStatus = "draft"

    @model_validator(mode="after")
    def _require_account_and_lead(self):
        if not self.account_id:
            raise ValueError("account_id is required for OutreachVectorMeta")
        if not self.lead_id:
            raise ValueError("lead_id is required for OutreachVectorMeta")
        return self


class TraceVectorMeta(SharedVectorMeta, SalesScopeMeta, CrewScopeMeta):
    """
    Namespace: crew_runs
    """
    type: Literal["trace"] = "trace"

    trace_type: TraceType
    tool_call_id: Optional[str] = None
    stage: Stage
    ok: bool = True
    duration_ms: Optional[int] = None

    # optional scalar for stricter tool filtering (tags also work)
    tool_name: Optional[str] = None

    @model_validator(mode="after")
    def _require_run_and_crew(self):
        if not self.run_id:
            raise ValueError("run_id is required for TraceVectorMeta")
        if not self.crew_id:
            raise ValueError("crew_id is required for TraceVectorMeta")
        if self.trace_type == "tool_call" and not self.tool_call_id:
            raise ValueError("tool_call_id is required when trace_type == 'tool_call'")
        return self


# Union helper (if you want type hints that cover all vector metas)
AnyVectorMeta = Union[
    PlaybookVectorMeta,
    CaseStudyVectorMeta,
    AccountNoteVectorMeta,
    LeadNoteVectorMeta,
    OutreachVectorMeta,
    TraceVectorMeta,
]


# ------------------------------------------------------------------------------
# Memory Models (ZeroDB Memory API compatible)
# ------------------------------------------------------------------------------

MemoryEntity = Literal["account", "lead", "run"]
MemoryType = Literal["preference", "objection", "decision", "next_step", "summary"]

class MemoryPriority(str, Enum):
    """
    Mirror the SDK's MemoryPriority enum.
    Adjust values if your SDK differs, but keep semantics the same.
    """
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SharedMemoryMeta(_Base):
    """
    Put run/task identifiers here so we can post-filter after semantic memory.search().
    """
    crew_id: Optional[str] = None
    agent_id: Optional[str] = None
    run_id: Optional[str] = None
    task_id: Optional[str] = None

    account_id: Optional[str] = None
    lead_id: Optional[str] = None

    source: Literal["agent", "human", "import"] = "agent"
    ts: datetime = Field(default_factory=utc_now)


class MemoryRecord(_Base):
    """
    Canonical in-app representation of a memory write request.
    This maps 1:1 to zerodb.memory.create(...) inputs.
    """
    content: str
    title: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    priority: MemoryPriority = MemoryPriority.MEDIUM
    metadata: SharedMemoryMeta = Field(default_factory=SharedMemoryMeta)

    @field_validator("tags")
    @classmethod
    def _validate_tags(cls, v: List[str]) -> List[str]:
        return ensure_tag_list(v)

    @model_validator(mode="after")
    def _enforce_minimum_tag_facets(self):
        # Enforce: stage:* and type:* and entity:* in tags
        keys = {t.split(":", 1)[0] for t in self.tags}
        for required in ("stage", "type", "entity"):
            if required not in keys:
                raise ValueError(f"MemoryRecord.tags must include '{required}:*'")
        return self


# ------------------------------------------------------------------------------
# Deterministic Tag Builders (Memory)
# ------------------------------------------------------------------------------

def build_memory_tags(
    *,
    entity: MemoryEntity,
    mtype: MemoryType,
    stage: Stage,
    account_id: Optional[str] = None,
    lead_id: Optional[str] = None,
    channel: Optional[Channel] = None,
    status: Optional[str] = None,
    persona: Optional[str] = None,
    vertical: Optional[str] = None,
    extras: Optional[Sequence[str]] = None,
) -> List[str]:
    """
    Canonical tag set. Use these tags in MemoryRecord.tags so memory.list() is deterministic.
    """
    tags = [
        tag("entity", entity),
        tag("type", mtype),
        tag("stage", stage),
    ]
    if account_id:
        tags.append(tag("account", account_id))
    if lead_id:
        tags.append(tag("lead", lead_id))
    if channel:
        tags.append(tag("channel", channel))
    if status:
        tags.append(tag("status", status))
    if persona:
        tags.append(tag("persona", persona))
    if vertical:
        tags.append(tag("vertical", vertical))
    if extras:
        tags.extend(extras)
    return ensure_tag_list(tags)


# ------------------------------------------------------------------------------
# Vector Filter Builders (ZeroDB vectors.search filter dicts)
# ------------------------------------------------------------------------------

class VectorFilter(_Base):
    """
    ZeroDB filter dict wrapper (for sanity + easy .model_dump()).
    Keep it as a flat mapping of scalars (portable across implementations).
    """
    # Common
    type: Optional[str] = None
    stage: Optional[str] = None

    # Sales scope
    account_id: Optional[str] = None
    lead_id: Optional[str] = None

    # Crew scope
    crew_id: Optional[str] = None
    run_id: Optional[str] = None
    task_id: Optional[str] = None

    # Specific
    channel: Optional[str] = None
    status: Optional[str] = None
    trace_type: Optional[str] = None
    tool_call_id: Optional[str] = None
    persona: Optional[str] = None
    vertical: Optional[str] = None
    tool_name: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.model_dump().items() if v is not None}


# --- Namespace-specific deterministic filter recipes ---

def filter_playbooks(*, persona: Optional[str] = None, vertical: Optional[str] = None) -> Dict[str, Any]:
    f = VectorFilter(type="playbook", persona=persona, vertical=vertical)
    return f.as_dict()

def filter_case_studies(*, vertical: Optional[str] = None, persona: Optional[str] = None) -> Dict[str, Any]:
    f = VectorFilter(type="case_study", vertical=vertical, persona=persona)
    return f.as_dict()

def filter_account_notes(*, account_id: str, stage: Optional[Stage] = None) -> Dict[str, Any]:
    f = VectorFilter(type="account_note", account_id=account_id, stage=stage)
    return f.as_dict()

def filter_lead_notes(*, account_id: str, lead_id: str, stage: Optional[Stage] = None) -> Dict[str, Any]:
    f = VectorFilter(type="lead_note", account_id=account_id, lead_id=lead_id, stage=stage)
    return f.as_dict()

def filter_outreach_history(
    *,
    account_id: str,
    lead_id: str,
    channel: Optional[Channel] = None,
    status: Optional[OutreachStatus] = None,
) -> Dict[str, Any]:
    f = VectorFilter(type="outreach", account_id=account_id, lead_id=lead_id, channel=channel, status=status)
    return f.as_dict()

def filter_run_traces(
    *,
    run_id: Optional[str] = None,
    account_id: Optional[str] = None,
    lead_id: Optional[str] = None,
    trace_type: Optional[TraceType] = None,
    task_id: Optional[str] = None,
    tool_call_id: Optional[str] = None,
    tool_name: Optional[str] = None,
) -> Dict[str, Any]:
    f = VectorFilter(
        type="trace",
        run_id=run_id,
        account_id=account_id,
        lead_id=lead_id,
        trace_type=trace_type,
        task_id=task_id,
        tool_call_id=tool_call_id,
        tool_name=tool_name,
    )
    return f.as_dict()


# ------------------------------------------------------------------------------
# Stage-aware search plans (exact namespace order + filters)
# ------------------------------------------------------------------------------

class NamespaceSearchPlanItem(_Base):
    namespace: ZeroDBNamespace
    filter: Dict[str, Any] = Field(default_factory=dict)
    top_k: int = 8


class StageSearchPlan(_Base):
    stage: Stage
    items: List[NamespaceSearchPlanItem]


def build_stage_search_plan(
    *,
    stage: Stage,
    account_id: Optional[str] = None,
    lead_id: Optional[str] = None,
    vertical: Optional[str] = None,
    persona: Optional[str] = None,
    run_id: Optional[str] = None,
    per_namespace_top_k: int = 6,
) -> StageSearchPlan:
    """
    Returns the exact search order described in the spec, with deterministic filters.
    """
    if stage == "research":
        items = [
            NamespaceSearchPlanItem(
                namespace=ZeroDBNamespace.PLAYBOOKS,
                filter=filter_playbooks(persona=persona, vertical=vertical),
                top_k=per_namespace_top_k,
            ),
            NamespaceSearchPlanItem(
                namespace=ZeroDBNamespace.CASE_STUDIES,
                filter=filter_case_studies(vertical=vertical, persona=persona),
                top_k=per_namespace_top_k,
            ),
        ]
        if account_id:
            items.append(
                NamespaceSearchPlanItem(
                    namespace=ZeroDBNamespace.ACCOUNTS,
                    filter=filter_account_notes(account_id=account_id),
                    top_k=per_namespace_top_k,
                )
            )
        return StageSearchPlan(stage=stage, items=items)

    if stage == "outreach":
        if not (account_id and lead_id):
            raise ValueError("outreach stage requires account_id and lead_id")
        items = [
            NamespaceSearchPlanItem(
                namespace=ZeroDBNamespace.OUTREACH_HISTORY,
                filter=filter_outreach_history(account_id=account_id, lead_id=lead_id),
                top_k=per_namespace_top_k,
            ),
            NamespaceSearchPlanItem(
                namespace=ZeroDBNamespace.LEADS,
                filter=filter_lead_notes(account_id=account_id, lead_id=lead_id),
                top_k=per_namespace_top_k,
            ),
            NamespaceSearchPlanItem(
                namespace=ZeroDBNamespace.PLAYBOOKS,
                filter=filter_playbooks(persona=persona, vertical=vertical),
                top_k=per_namespace_top_k,
            ),
            NamespaceSearchPlanItem(
                namespace=ZeroDBNamespace.CASE_STUDIES,
                filter=filter_case_studies(vertical=vertical, persona=persona),
                top_k=max(2, per_namespace_top_k // 2),
            ),
        ]
        return StageSearchPlan(stage=stage, items=items)

    # followup
    if not (account_id and lead_id):
        raise ValueError("followup stage requires account_id and lead_id")
    items = [
        NamespaceSearchPlanItem(
            namespace=ZeroDBNamespace.OUTREACH_HISTORY,
            filter=filter_outreach_history(account_id=account_id, lead_id=lead_id),
            top_k=per_namespace_top_k,
        ),
        NamespaceSearchPlanItem(
            namespace=ZeroDBNamespace.LEADS,
            filter=filter_lead_notes(account_id=account_id, lead_id=lead_id),
            top_k=per_namespace_top_k,
        ),
        NamespaceSearchPlanItem(
            namespace=ZeroDBNamespace.PLAYBOOKS,
            filter=filter_playbooks(persona=persona, vertical=vertical),
            top_k=per_namespace_top_k,
        ),
        NamespaceSearchPlanItem(
            namespace=ZeroDBNamespace.RUN_ARTIFACTS,
            # Use run_id if continuing same run; otherwise account+lead scoping.
            filter=filter_run_traces(
                run_id=run_id,
                account_id=None if run_id else account_id,
                lead_id=None if run_id else lead_id,
            ),
            top_k=max(4, per_namespace_top_k),
        ),
    ]
    return StageSearchPlan(stage=stage, items=items)


# ------------------------------------------------------------------------------
# Memory “facet recall” recipes (deterministic)
# ------------------------------------------------------------------------------

class MemoryFacetQuery(_Base):
    tags: List[str]
    priority_min: Optional[MemoryPriority] = None  # app-enforced; SDK may only support exact priority filter
    limit: int = 10


def facet_lead_preferences(*, account_id: str, lead_id: str) -> MemoryFacetQuery:
    return MemoryFacetQuery(
        tags=build_memory_tags(
            entity="lead",
            mtype="preference",
            stage="outreach",
            account_id=account_id,
            lead_id=lead_id,
        ),
        priority_min=MemoryPriority.HIGH,
        limit=10,
    )

def facet_open_objections(*, account_id: str, lead_id: str) -> MemoryFacetQuery:
    return MemoryFacetQuery(
        tags=build_memory_tags(
            entity="lead",
            mtype="objection",
            stage="followup",
            account_id=account_id,
            lead_id=lead_id,
        ),
        priority_min=MemoryPriority.MEDIUM,
        limit=10,
    )

def facet_next_steps(*, account_id: str, lead_id: str) -> MemoryFacetQuery:
    return MemoryFacetQuery(
        tags=build_memory_tags(
            entity="lead",
            mtype="next_step",
            stage="followup",
            account_id=account_id,
            lead_id=lead_id,
        ),
        priority_min=MemoryPriority.HIGH,
        limit=10,
    )


# ------------------------------------------------------------------------------
# Pydantic v1 note
# ------------------------------------------------------------------------------
"""
If you're on pydantic v1:
- Replace ConfigDict usage with inner class Config
- Replace @field_validator with @validator
- Replace @model_validator with @root_validator
- Replace model_dump() with dict()
Everything else (schemas, builders) stays the same.
"""
