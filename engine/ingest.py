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
from collections.abc import Mapping

from contracts.types import IngestReport, Sale
from engine.facts import normalize

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

LABEL_POSITIVE = {"buena", "good", "valida", "valido", "ok", "si", "yes", "sano",
                  "true", "1", "correcta", "aprobada", "aprobado"}
LABEL_NEGATIVE = {"mala", "bad", "fraude", "no", "false", "0", "incorrecta",
                  "fraudulenta", "rechazada", "rechazado", "desaprobada"}

_SYNONYM_INDEX: dict[str, str] = {}
for _field, _names in FIELD_SYNONYMS.items():
    for _name in _names:
        _SYNONYM_INDEX.setdefault(normalize(_name), _field)
_EXTRA_KEYS = {normalize(name) for name in EXTRA_SYNONYMS}
_IGNORED_KEYS = {normalize(name) for name in IGNORED_SYNONYMS}
_MAPPABLE_FIELDS = list(FIELD_SYNONYMS)


def _is_ignored(column: str) -> bool:
    return normalize(column) in _IGNORED_KEYS


def _match_column(column: str) -> str | None:
    key = normalize(column)
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
        return raw if isinstance(raw, list) else []
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

    sales: list[Sale] = []
    errors: list[str] = []
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
                values[field] = _coerce(field, raw)
            if "consent_evidence" not in mapped.values():
                # The source never exposes consent: the absence signal cannot be computed, only reported.
                extra["consent_not_in_source"] = True
            if extra:
                values["extra"] = extra
            values["id"] = str(values.get("id") or "")
            sales.append(Sale.model_validate(values))
        except Exception as exc:  # noqa: BLE001 — a batch must survive any row
            errors.append(f"Fila {index}: {exc}")

    report = IngestReport(
        mapped=mapped,
        unrecognized=unrecognized,
        missing=[field for field in _MAPPABLE_FIELDS if field not in mapped.values()],
        rows=len(sales),
        errors=errors,
    )
    return sales, report
