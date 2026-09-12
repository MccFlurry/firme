"""Trusted YAML rules and traceable evidence."""

from pathlib import Path

import yaml

from contracts.types import Evidence

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"
SEVERITIES = ("baja", "media", "alta", "bloqueante")
STRENGTHS = ("linguistica", "estadistica", "determinista")


def load_config(name: str):
    with (CONFIG_DIR / f"{name}.yaml").open(encoding="utf-8") as stream:
        return yaml.safe_load(stream)


def evaluate_rules(facts: dict, rules: list[dict]) -> list[Evidence]:
    evidence = []
    for rule in rules:
        # ponytail: eval on trusted YAML; swap for simpleeval if rules ever come from users
        if eval(rule["condition"], {"__builtins__": {}}, facts):
            evidence.append(Evidence(
                rule_id=rule["id"], rule_name=rule["name"], edge=rule["edge"],
                condition=rule["condition"], values={key: facts.get(key) for key in rule["inputs"]},
                severity=rule["severity"], strength=rule["strength"],
                message=rule["message"].format(**facts), source=rule["source"],
                origin=rule["origen"], impacts=rule["impacts"],
            ))
    return evidence
