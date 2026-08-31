from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import os
from pathlib import Path
from threading import RLock
from typing import Any


USD_QUANTUM = Decimal("0.00000001")
DEFAULT_AI_PRICING_REGISTRY = {
    "pricing_version": "OPENAI-2026-08-27-STANDARD",
    "effective_from": "2026-08-27",
    "currency": "USD",
    "source": "OpenAI API pricing documentation",
    "models": {
        "gpt-5.6-luna": {"input_per_million": "0.20", "cached_input_per_million": "0.02", "cache_write_per_million": "0.25", "output_per_million": "1.20"},
        "gpt-5.6-terra": {"input_per_million": "2.00", "cached_input_per_million": "0.20", "cache_write_per_million": "2.50", "output_per_million": "12.00"},
        "gpt-5.6-sol": {"input_per_million": "4.00", "cached_input_per_million": "0.40", "cache_write_per_million": "5.00", "output_per_million": "20.00"},
    },
    "tools": {"web_search": {"per_call": "0.01"}},
}


def _decimal(value: Any) -> Decimal:
    return Decimal(str(value or "0"))


class AIPricingRegistry:
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        value = config
        if value is None:
            raw = str(os.getenv("HOST_AI_PRICING_REGISTRY_JSON") or "").strip()
            if raw:
                try: value = json.loads(raw)
                except (TypeError, ValueError): value = None
        self.config = dict(value or DEFAULT_AI_PRICING_REGISTRY)

    @property
    def version(self) -> str: return str(self.config.get("pricing_version") or "UNVERSIONED")

    def calculate(self, *, provider: str, model: str, usage: dict[str, Any], tools: dict[str, int] | None = None) -> dict[str, Any]:
        prices = dict((self.config.get("models") or {}).get(model) or {})
        input_tokens = int(usage.get("input_tokens") or 0)
        cached_tokens = min(input_tokens, int(usage.get("cached_input_tokens") or 0))
        cache_write_tokens = min(input_tokens, int(usage.get("cache_write_tokens") or 0))
        regular_tokens = max(0, input_tokens - cached_tokens - cache_write_tokens)
        output_tokens = int(usage.get("output_tokens") or 0)
        model_cost = (
            _decimal(regular_tokens) * _decimal(prices.get("input_per_million"))
            + _decimal(cached_tokens) * _decimal(prices.get("cached_input_per_million"))
            + _decimal(cache_write_tokens) * _decimal(prices.get("cache_write_per_million", prices.get("input_per_million")))
            + _decimal(output_tokens) * _decimal(prices.get("output_per_million"))
        ) / Decimal(1_000_000)
        items = [{"provider": provider, "model": model, **{key: int(usage.get(key) or 0) for key in ("input_tokens", "cached_input_tokens", "cache_write_tokens", "output_tokens", "reasoning_tokens", "total_tokens")}, "tool": None, "quantity": 1, "cost_usd": str(model_cost.quantize(USD_QUANTUM, rounding=ROUND_HALF_UP))}]
        total = model_cost
        for tool, quantity in (tools or {}).items():
            tool_cost = _decimal(quantity) * _decimal(((self.config.get("tools") or {}).get(tool) or {}).get("per_call"))
            total += tool_cost
            items.append({"provider": provider, "model": model, "tool": tool, "quantity": int(quantity), "cost_usd": str(tool_cost.quantize(USD_QUANTUM, rounding=ROUND_HALF_UP))})
        return {"items": items, "total_cost_usd": str(total.quantize(USD_QUANTUM, rounding=ROUND_HALF_UP)), "currency": "USD", "pricing_version": self.version, "pricing_effective_from": str(self.config.get("effective_from") or ""), "pricing_source": str(self.config.get("source") or "configured"), "label": "Coste calculado según tarifas configuradas"}


class AICostLedger:
    _lock = RLock()

    def __init__(self, base_dir: Path | str, pricing: AIPricingRegistry | None = None, now_provider=lambda: datetime.now(timezone.utc)) -> None:
        self.path = Path(base_dir).resolve() / "DATOS" / "telemetry" / "ai_cost_events.jsonl"
        self.pricing = pricing or AIPricingRegistry(); self.now_provider = now_provider

    def record(self, *, operation_id: str, operation_type: str, provider: str, model: str, usage: dict[str, Any], tools: dict[str, int] | None = None, request_id: str = "", session_id: str = "", capability: str = "", entity_type: str = "", entity_id: str = "", external_response_id: str = "", status: str = "completed") -> dict[str, Any]:
        now = self.now_provider().isoformat(timespec="seconds")
        fingerprint_source = external_response_id or json.dumps({"operation_id": operation_id, "provider": provider, "model": model, "usage": usage, "tools": tools or {}}, sort_keys=True)
        event_id = "AICOST-" + hashlib.sha256(fingerprint_source.encode()).hexdigest()[:24]
        with self._lock:
            existing = next((item for item in self._read() if item.get("event_id") == event_id), None)
            if existing: return self.operation(str(existing.get("operation_id") or operation_id), incremental=False)
            calculated = self.pricing.calculate(provider=provider, model=model, usage=usage, tools=tools)
            event = {"event_id": event_id, "operation_id": operation_id, "operation_type": operation_type, "request_id": request_id, "session_id": session_id, "capability": capability, "entity_type": entity_type, "entity_id": entity_id, "provider": provider, "model": model, "usage": dict(usage), "tools": dict(tools or {}), "status": status, "recorded_at": now, **calculated}
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle: handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
        result = self.operation(operation_id, incremental=False)
        result["incremental_cost_usd"] = str(calculated.get("total_cost_usd") or "0.00000000")
        return result

    def zero_cost(self, *, operation_id: str, operation_type: str, cache_hit: bool = False) -> dict[str, Any]:
        return {"operation_id": operation_id, "operation_type": operation_type, "items": [], "total_cost_usd": "0.00000000", "currency": "USD", "pricing_version": self.pricing.version, "cache_hit": cache_hit, "incremental_cost_usd": "0.00000000", "label": "Coste adicional" if cache_hit else "Coste calculado según tarifas configuradas"}

    def operation(self, operation_id: str, *, incremental: bool = True) -> dict[str, Any]:
        values = [item for item in self._read() if item.get("operation_id") == operation_id]
        items = [detail for event in values for detail in event.get("items") or []]
        total = sum((_decimal(event.get("total_cost_usd")) for event in values), Decimal("0"))
        return {"operation_id": operation_id, "operation_type": str(values[0].get("operation_type") or "") if values else "", "started_at": str(values[0].get("recorded_at") or "") if values else "", "finished_at": str(values[-1].get("recorded_at") or "") if values else "", "items": items, "total_cost_usd": str(total.quantize(USD_QUANTUM)), "incremental_cost_usd": str(total.quantize(USD_QUANTUM)) if incremental else "0.00000000", "currency": "USD", "pricing_version": str(values[-1].get("pricing_version") or self.pricing.version) if values else self.pricing.version, "cache_hit": False, "label": "Coste calculado según tarifas configuradas"}

    def aggregate(self, *, session_id: str = "", entity_type: str = "", entity_id: str = "", period: str = "") -> dict[str, Any]:
        values = self._read()
        period_key = str(period or "").strip().lower()
        if period_key in {"today", "week", "month"}:
            now = self.now_provider()
            if period_key == "today": cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0)
            elif period_key == "week": cutoff = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
            else: cutoff = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            values = [item for item in values if self._event_time(item) >= cutoff]
        if session_id: values = [item for item in values if item.get("session_id") == session_id]
        if entity_type: values = [item for item in values if item.get("entity_type") == entity_type]
        if entity_id: values = [item for item in values if item.get("entity_id") == entity_id]
        total = sum((_decimal(item.get("total_cost_usd")) for item in values), Decimal("0"))
        by_model: dict[str, Decimal] = {}; by_capability: dict[str, Decimal] = {}; by_operation: dict[str, Decimal] = {}
        for item in values:
            cost = _decimal(item.get("total_cost_usd")); model = str(item.get("model") or ""); capability = str(item.get("capability") or item.get("operation_type") or ""); operation = str(item.get("operation_id") or "")
            by_model[model] = by_model.get(model, Decimal("0")) + cost; by_capability[capability] = by_capability.get(capability, Decimal("0")) + cost; by_operation[operation] = by_operation.get(operation, Decimal("0")) + cost
        return {"total_cost_usd": str(total.quantize(USD_QUANTUM)), "currency": "USD", "period": period_key or "all", "pricing_versions": sorted({str(item.get("pricing_version") or "") for item in values}), "events": len(values), "by_model": {k: str(v.quantize(USD_QUANTUM)) for k, v in by_model.items()}, "by_capability": {k: str(v.quantize(USD_QUANTUM)) for k, v in by_capability.items()}, "by_operation": {k: str(v.quantize(USD_QUANTUM)) for k, v in by_operation.items()}}

    @staticmethod
    def _event_time(item: dict[str, Any]) -> datetime:
        try:
            value = datetime.fromisoformat(str(item.get("recorded_at") or ""))
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        except ValueError:
            return datetime.min.replace(tzinfo=timezone.utc)

    def _read(self) -> list[dict[str, Any]]:
        if not self.path.exists(): return []
        result = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            try: value = json.loads(line)
            except (TypeError, ValueError): continue
            if isinstance(value, dict): result.append(value)
        return result


__all__ = ["AIPricingRegistry", "AICostLedger", "DEFAULT_AI_PRICING_REGISTRY"]
