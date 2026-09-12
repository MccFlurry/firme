"""Tolerant batch ingestion: JSON, CSV or dict rows into ``Sale`` objects.

Nothing here raises. Unknown columns land in ``Sale.extra``, broken rows are
reported in ``IngestReport.errors`` and skipped, and any ``label`` /
``etiqueta`` / ``resultado`` / ``es_buena`` / ``fraude`` column is normalized
to ``buena`` / ``mala``.
"""

from __future__ import annotations

import csv
import difflib
import io
import json
import math
import re
from collections.abc import Mapping

from pydantic import Field

from contracts.types import IngestReport, Sale
from engine.facts import normalize, plan_for_speed
from engine.llm import map_columns
from engine.rules import load_config


class SemanticIngestReport(IngestReport):
    """Mapping provenance without changing the frozen ingestion contract."""

    mapped_by_ai: dict[str, str] = Field(default_factory=dict)

# canonical Sale field -> accepted column names (es/en, accents optional, snake/camel)
FIELD_SYNONYMS = {
    "id": ["id", "sale id", "venta id", "codigo", "codigo venta", "venta", "sale"],
    "seller_id": ["seller id", "vendedor id", "id vendedor", "vendedor", "codigo vendedor",
                  "seller", "asesor", "asesor id", "agente", "agent id", "codigo asesor"],
    "channel": ["channel", "canal", "canal venta", "channel id", "canal de venta"],
    "customer_name": ["customer name", "nombre", "nombre cliente", "cliente", "nombre completo",
                      "full name", "customer", "nombre del cliente", "cliente nombre", "razon social"],
    "customer_doc": ["customer doc", "documento", "dni", "doc", "documento cliente",
                     "documento identidad", "customer document", "dni cliente", "num doc",
                     "numero documento", "documento de identidad"],
    "phone": ["phone", "telefono", "phone number", "telefono cliente", "celular",
              "celular cliente", "movil", "numero telefono", "numero de telefono"],
    "email": ["email", "correo", "correo electronico", "mail", "correo cliente"],
    "address": ["address", "direccion", "direccion cliente", "domicilio"],
    "district": ["district", "distrito", "zona", "district name", "distrito cliente", "cobertura"],
    "plan": ["plan", "plan id", "plan name", "nombre plan", "producto", "product", "servicio"],
    "price": ["price", "precio", "precio mensual", "monthly price", "precio plan", "tarifa",
              "costo", "costo mensual", "precio registrado"],
    "promo": ["promo", "promocion", "promo id", "promotion", "oferta", "promocion aplicada"],
    "install_date": ["install date", "fecha instalacion", "instalacion", "installation date",
                     "fecha de instalacion", "fecha instalacion prevista", "fecha de instalacion prevista"],
    "registered_at": ["registered at", "fecha registro", "registrado", "fecha", "fecha venta",
                      "registered", "created at", "fecha registrada", "fecha de registro", "fecha hora"],
    "fill_seconds": ["fill seconds", "tiempo llenado", "tiempo de llenado", "fill time",
                     "segundos llenado", "fill", "tiempo completado"],
    "consent_evidence": ["consent evidence", "consentimiento", "evidencia consentimiento",
                         "consent", "evidencia"],
    "promise_text": ["promise text", "promesa", "promesa texto", "promise", "texto promesa",
                     "oferta texto", "lo prometido", "promesa ofrecida"],
    "label": ["label", "etiqueta", "resultado", "es buena", "fraude", "etiqueta demo",
              "ground truth", "es mala", "resultado real"],
    "edits": ["edits", "ediciones", "edit history", "historial", "historial de cambios", "cambios"],
}

EXTRA_SYNONYMS = ["extra", "adicional", "adicionales", "datos adicionales"]
IGNORED_SYNONYMS: list[str] = []

# CONTRATO-DE-DATOS.md §4: keep Anexo 1 fields under their canonical names.
CONTRACT_FIELDS = {
    "promesa_declarada": "promise_text", "precio_mensual": "price",
    "cliente_documento": "customer_doc", "telefono_1": "phone", "correo_electronico": "email",
    "direccion": "address", "nombre_asesor": "seller_id", "canal": "channel",
    "fecha_hora_registro": "registered_at", "ediciones_registro": "edits",
    **{name: f"extra.{name}" for name in (
        "velocidad_contratada", "telefono_2", "equipo", "plazo_estimado_instalacion",
        "confirmacion_titular", "confirmacion_titular_ts", "plazo_vigencia", "forma_entrega_recibo",
        "forma_pago", "forma_pago_instalacion", "cargo_instalacion_costo", "cargo_instalacion_cuotas",
        "tenencia", "etapa", "nombre_condominio", "torre", "departamento", "score_crediticio",
        "catalogo_referencia_id", "acta_instalacion_ts",
    )},
}
for _name, _field in CONTRACT_FIELDS.items():
    FIELD_SYNONYMS.setdefault(_field, []).append(_name)
for _name in ("veredicto_esperado", "familia", "comparador"):
    FIELD_SYNONYMS[f"extra.{_name}"] = [_name]

LABEL_POSITIVE = {"buena", "good", "valida", "valido", "ok", "si", "yes", "sano",
                  "true", "1", "correcta", "aprobada", "aprobado", "pasa"}
LABEL_NEGATIVE = {"mala", "bad", "fraude", "no", "false", "0", "incorrecta",
                  "fraudulenta", "rechazada", "rechazado", "desaprobada", "revisar"}

_SYNONYM_INDEX: dict[str, str] = {}
for _field, _names in FIELD_SYNONYMS.items():
    for _name in [_field, *_names]:
        _SYNONYM_INDEX.setdefault(normalize(_name), _field)
_EXTRA_KEYS = {normalize(name) for name in EXTRA_SYNONYMS}
_IGNORED_KEYS = {normalize(name) for name in IGNORED_SYNONYMS}
_MAPPABLE_FIELDS = list(FIELD_SYNONYMS)


def _is_ignored(column: str) -> bool:
    return normalize(column) in _IGNORED_KEYS


def _match_column(column: str) -> str | None:
    key = normalize(re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", column))
    if not key:
        return None
    if key in _SYNONYM_INDEX:
        return _SYNONYM_INDEX[key]
    if key in _EXTRA_KEYS:
        return "extra"
    close = difflib.get_close_matches(key, list(_SYNONYM_INDEX), n=1, cutoff=0.75)
    if close:
        return _SYNONYM_INDEX[close[0]]
    return None


def _to_float(value):
    if isinstance(value, bool):
        return None
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError, OverflowError):
        return None


def _to_int(value):
    if isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        try:
            return int(float(value))
        except (TypeError, ValueError, OverflowError):
            return None


def _normalize_label(value):
    if value is None:
        return None
    key = normalize(str(value))
    if key in LABEL_POSITIVE:
        return "buena"
    if key in LABEL_NEGATIVE:
        return "mala"
    return None


def _parse_extra(value):
    if isinstance(value, Mapping):
        return dict(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            data = json.loads(text)
        except (json.JSONDecodeError, TypeError, ValueError):
            return None
        if isinstance(data, Mapping):
            return dict(data)
    return None


def _coerce(field: str, raw):
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return None
    if field == "price":
        return _to_float(raw)
    if field == "fill_seconds":
        return _to_int(raw)
    if field == "label":
        return _normalize_label(raw)
    if field == "edits":
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except (json.JSONDecodeError, TypeError, ValueError):
                return []
        return [{**edit, "field": CONTRACT_FIELDS.get(edit.get("field"), edit.get("field"))}
                if isinstance(edit, dict) else edit for edit in raw] if isinstance(raw, list) else []
    if field in {"extra.velocidad_contratada", "extra.plazo_estimado_instalacion",
                 "extra.cargo_instalacion_cuotas", "extra.score_crediticio"}:
        return _to_int(raw)
    if field == "extra.cargo_instalacion_costo":
        return _to_float(raw)
    return raw


def _json_rows(text: str):
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, TypeError, ValueError):
        return None
    if isinstance(data, dict):
        for key in ("ventas", "sales", "rows", "data"):
            if isinstance(data.get(key), list):
                return data[key]
        return None
    return data if isinstance(data, list) else None


def _csv_rows(text: str):
    try:
        dialect = csv.Sniffer().sniff(text[:8192], delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel
    raw = [row for row in csv.reader(io.StringIO(text), dialect) if row and any(cell.strip() for cell in row)]
    if not raw:
        return []
    header = [cell.strip() for cell in raw[0]]
    rows = []
    for line in raw[1:]:
        if len(line) != len(header):
            rows.append(f"Fila CSV con {len(line)} columnas, se esperaban {len(header)}.")
            continue
        rows.append({name: cell.strip() for name, cell in zip(header, line)})
    return rows


def _to_rows(payload, filename: str | None):
    if isinstance(payload, list):
        return payload
    if isinstance(payload, (bytes, bytearray)):
        text = payload.decode("utf-8", errors="replace")
    else:
        text = str(payload)
    text = text.strip()
    if not text:
        return []
    name = (filename or "").lower()
    if name.endswith(".csv"):
        return _csv_rows(text)
    rows = _json_rows(text)
    if rows is not None:
        return rows
    if name.endswith(".json"):
        return ["No se pudo interpretar el contenido como JSON."]
    return _csv_rows(text)


def parse(payload: str | bytes | list[dict], filename: str | None = None) -> tuple[list[Sale], IngestReport]:
    raw_rows = _to_rows(payload, filename)

    columns: list[str] = []
    for row in raw_rows:
        if isinstance(row, Mapping):
            for key in row:
                if key not in columns:
                    columns.append(key)

    mapped: dict[str, str] = {}
    unrecognized: list[str] = []
    for column in columns:
        if _is_ignored(column):
            continue
        field = _match_column(column)
        if field:
            mapped[column] = field
        else:
            unrecognized.append(column)

    sample = {column: next((row[column] for row in raw_rows
                           if isinstance(row, Mapping) and row.get(column) not in (None, "")), None)
              for column in unrecognized}
    mapped_by_ai = {}
    for column, field in map_columns(unrecognized, sample).items():
        if field not in mapped.values():
            mapped[column] = field
            mapped_by_ai[column] = field
    unrecognized = [column for column in unrecognized if column not in mapped_by_ai]

    sales: list[Sale] = []
    errors: list[str] = []
    catalog = load_config("catalog")
    for index, row in enumerate(raw_rows, start=1):
        if not isinstance(row, Mapping):
            errors.append(str(row) if isinstance(row, str) else f"Fila {index}: no es un objeto.")
            continue
        values: dict = {}
        extra: dict = {}
        try:
            for column, raw in row.items():
                if _is_ignored(column):
                    continue
                field = mapped.get(column)
                if field is None:
                    extra[column] = raw
                    continue
                if field == "extra":
                    parsed = _parse_extra(raw)
                    if parsed is not None:
                        extra.update(parsed)
                    else:
                        extra[column] = raw
                    continue
                if field.startswith("extra."):
                    extra[field[6:]] = _coerce(field, raw)
                    continue
                values[field] = _coerce(field, raw)
                if field == "label" and normalize(str(raw)) == "abstencion":
                    extra["veredicto_esperado"] = "abstención"
            if "veredicto_esperado" in extra:
                expected = extra["veredicto_esperado"]
                values["label"] = _normalize_label(expected)
                if normalize(str(expected)) == "abstencion":
                    extra["veredicto_esperado"] = "abstención"
            if not values.get("plan"):
                values["plan"] = plan_for_speed(extra.get("velocidad_contratada"), catalog["plans"])
            if "consent_evidence" not in mapped.values():
                # The source never exposes consent: the absence signal cannot be computed, only reported.
                extra["consent_not_in_source"] = True
            if extra:
                values["extra"] = extra
            values["id"] = str(values.get("id") or "")
            sales.append(Sale.model_validate(values))
        except Exception as exc:  # noqa: BLE001 — a batch must survive any row
            errors.append(f"Fila {index}: {exc}")

    report = SemanticIngestReport(
        mapped=mapped,
        mapped_by_ai=mapped_by_ai,
        unrecognized=unrecognized,
        missing=[field for field in _MAPPABLE_FIELDS if field not in mapped.values()],
        rows=len(sales),
        errors=errors,
    )
    return sales, report
