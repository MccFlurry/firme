"""Shared contract between /engine, /app and /confirm.

Frozen after Phase 1. Nobody edits this file without telling the other two.
Every field on Sale is optional except `id`: ingestion must never crash on
unknown or missing input. Money is in soles (S/). Timestamps are ISO-8601 strings.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Decision = Literal["APROBAR", "REVISAR", "RETENER", "ABSTENERSE"]
Severity = Literal["baja", "media", "alta", "bloqueante"]
Strength = Literal["determinista", "estadistica", "linguistica"]
Origin = Literal["SUPUESTO_DEMO", "PUBLICO"]
Edge = Literal[
    "promesa-catalogo",
    "promesa-registro",
    "catalogo-registro",
    "registro-entrega",
    "identidad",
    "senal",
]
ConfirmationStatus = Literal["pendiente", "confirmada", "corregida", "desconocida", "silencio"]
LlmMode = Literal["llm", "determinista"]


class Promise(BaseModel):
    """What the seller says was offered, normalized to catalog vocabulary."""

    plan: str | None = None  # catalog plan id, e.g. "fibra_200"
    speed_mbps: int | None = None
    price: float | None = None  # monthly price promised, S/
    promo: str | None = None  # catalog promo id
    install_days: int | None = None  # "te instalan en N días"
    claims: list[str] = Field(default_factory=list)  # "sin contrato", "velocidad garantizada", ...
    raw_text: str = ""
    source: Literal["llm", "deterministic", "structured"] = "structured"


class FieldEdit(BaseModel):
    field: str
    at: str
    old: str | None = None
    new: str | None = None


class Sale(BaseModel):
    """The sale as recorded in the system."""

    id: str
    seller_id: str | None = None
    channel: str | None = None  # call_center | campo | web | tienda
    customer_name: str | None = None
    customer_doc: str | None = None  # synthetic DNI
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    district: str | None = None  # zone id in config/catalog.yaml coverage
    plan: str | None = None  # catalog plan id
    price: float | None = None  # monthly price recorded, S/
    promo: str | None = None  # catalog promo id
    install_date: str | None = None  # ISO date
    registered_at: str | None = None  # ISO datetime
    fill_seconds: int | None = None  # form fill time measured client-side
    edits: list[FieldEdit] = Field(default_factory=list)
    consent_evidence: str | None = None  # grabacion | firma | sms | None
    promise_text: str | None = None  # natural-language promise
    promise: Promise | None = None  # normalized promise (engine fills it)
    label: Literal["buena", "mala"] | None = None  # ground truth when the batch has it
    extra: dict = Field(default_factory=dict)  # unrecognized input fields, kept for display


class Confirmation(BaseModel):
    sale_id: str
    token: str
    status: ConfirmationStatus = "pendiente"
    note: str | None = None
    created_at: str
    expires_at: str
    responded_at: str | None = None


class Context(BaseModel):
    """Cross-sale context: history for collisions and bursts, confirmation state, clock."""

    history: list[Sale] = Field(default_factory=list)  # other sales the system knows
    confirmation: Confirmation | None = None
    now: str | None = None  # ISO datetime; None means real clock


class Evidence(BaseModel):
    rule_id: str
    rule_name: str
    edge: Edge
    condition: str  # condition text exactly as written in config/rules.yaml
    values: dict  # the facts the condition read, with their actual values
    severity: Severity
    strength: Strength
    message: str  # rendered, Spanish, for the screen
    source: str  # where the rule comes from (document, link, mentor)
    origin: Origin
    impacts: dict[str, float]  # outcome id -> probability contribution


class Counterfactual(BaseModel):
    changes: list[dict]  # [{"field": ..., "from": ..., "to": ..., "reason": ...}]
    resulting_decision: Decision
    resulting_cost: float
    text: str  # "Si el precio fuera S/ 89 (tarifario), esta venta pasaría."


class Alert(BaseModel):
    recipient: str  # "Supervisor de ventas" | "Calidad de venta" | "Despacho e instalaciones"
    urgency: Literal["alta", "media", "baja"]
    deadline: str  # ISO datetime, before the install window closes
    action: str  # concrete, one sentence


class Verdict(BaseModel):
    sale_id: str
    decision: Decision
    expected_cost: float  # S/ expected if the sale goes through unreviewed
    review_cost: float  # S/ cost of one review, from config/costs.yaml
    outcome_probs: dict[str, float]  # outcome id -> probability
    outcome_costs: dict[str, float]  # outcome id -> S/
    severity: Severity | None  # max severity among evidence
    strength: Strength | None  # strongest evidence type
    evidence: list[Evidence]
    counterfactual: Counterfactual | None
    missing_fields: list[str]  # fields whose absence degraded the decision
    abstain_reason: str | None = None
    llm_mode: LlmMode
    recoverable_per_minute: float  # queue priority: recoverable S/ per review minute
    alert: Alert | None
    config_origins: dict[str, Origin] = Field(default_factory=dict)  # rule_id -> origin
    promise: Promise | None = None


class IngestReport(BaseModel):
    mapped: dict[str, str]  # input column -> Sale field
    unrecognized: list[str]
    missing: list[str]  # Sale fields the batch never provided
    rows: int
    errors: list[str]  # per-row problems, never raised


class Event(BaseModel):
    sale_id: str
    at: str
    kind: str  # registrada | evaluada | enlace_generado | confirmada | corregida | desconocida | silencio | editada | aviso
    detail: str
