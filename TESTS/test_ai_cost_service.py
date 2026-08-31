from datetime import datetime, timezone
from decimal import Decimal

from SERVICIOS.ai_cost_service import AICostLedger, AIPricingRegistry


PRICING = {
    "pricing_version": "TEST-V1",
    "effective_from": "2026-01-01",
    "currency": "USD",
    "source": "fixture",
    "models": {
        "luna": {"input_per_million": "1", "cached_input_per_million": "0.1", "cache_write_per_million": "2", "output_per_million": "4"},
        "terra": {"input_per_million": "2", "cached_input_per_million": "0.2", "cache_write_per_million": "3", "output_per_million": "8"},
    },
    "tools": {"web_search": {"per_call": "0.01"}},
}


def ledger(tmp_path):
    return AICostLedger(tmp_path, AIPricingRegistry(PRICING), now_provider=lambda: datetime(2026, 8, 27, 12, tzinfo=timezone.utc))


def test_luna_plus_web_search_uses_real_usage_and_exact_decimal(tmp_path) -> None:
    result = ledger(tmp_path).record(
        operation_id="PRICE-1", operation_type="PRICE_WEB_SEARCH", provider="OPENAI", model="luna",
        usage={"input_tokens": 2_000, "cached_input_tokens": 500, "cache_write_tokens": 250, "output_tokens": 500, "reasoning_tokens": 100, "total_tokens": 2_500},
        tools={"web_search": 1}, external_response_id="resp-1",
    )
    # 1250*1/M + 500*0.1/M + 250*2/M + 500*4/M + one search.
    assert Decimal(result["total_cost_usd"]) == Decimal("0.01380000")
    assert result["pricing_version"] == "TEST-V1"
    assert result["items"][0]["reasoning_tokens"] == 100


def test_luna_terra_and_two_searches_accumulate_under_parent_operation(tmp_path) -> None:
    costs = ledger(tmp_path)
    first = costs.record(operation_id="PRICE-2", operation_type="PRICE_WEB_SEARCH", provider="OPENAI", model="luna", usage={"input_tokens": 1_000, "output_tokens": 250}, tools={"web_search": 1}, external_response_id="resp-luna")
    result = costs.record(operation_id="PRICE-2", operation_type="PRICE_WEB_SEARCH", provider="OPENAI", model="terra", usage={"input_tokens": 1_000, "output_tokens": 250}, tools={"web_search": 1}, external_response_id="resp-terra")
    assert Decimal(result["total_cost_usd"]) == Decimal("0.02600000")
    assert Decimal(first["incremental_cost_usd"]) + Decimal(result["incremental_cost_usd"]) == Decimal("0.02600000")
    assert len(result["items"]) == 4


def test_cache_has_zero_incremental_cost_and_does_not_repeat_history(tmp_path) -> None:
    costs = ledger(tmp_path)
    costs.record(operation_id="PRICE-3", operation_type="PRICE_WEB_SEARCH", provider="OPENAI", model="luna", usage={"input_tokens": 1_000}, tools={"web_search": 1}, external_response_id="resp-cache")
    cached = costs.zero_cost(operation_id="PRICE-CACHED", operation_type="PRICE_WEB_SEARCH", cache_hit=True)
    assert Decimal(cached["incremental_cost_usd"]) == 0
    assert costs.aggregate()["events"] == 1


def test_failed_provider_usage_is_persisted_and_idempotent(tmp_path) -> None:
    costs = ledger(tmp_path)
    kwargs = dict(operation_id="FAIL-1", operation_type="ARTICLE_AI", provider="OPENAI", model="luna", usage={"input_tokens": 1_000, "output_tokens": 100}, external_response_id="resp-failed", status="failed")
    first = costs.record(**kwargs)
    second = costs.record(**kwargs)
    assert Decimal(first["total_cost_usd"]) > 0
    assert second["incremental_cost_usd"] == "0.00000000"
    assert costs.aggregate()["events"] == 1


def test_aggregate_is_exact_and_supports_operational_periods(tmp_path) -> None:
    costs = ledger(tmp_path)
    for index, input_tokens in enumerate((10_000, 20_000, 5_000), 1):
        costs.record(operation_id=f"OP-{index}", operation_type="TEST", provider="OPENAI", model="luna", usage={"input_tokens": input_tokens}, external_response_id=f"resp-{index}", session_id="SESSION", capability="PRICE_WEB_SEARCH")
    assert costs.aggregate(session_id="SESSION")["total_cost_usd"] == "0.03500000"
    assert costs.aggregate(session_id="SESSION", period="today")["total_cost_usd"] == "0.03500000"
    assert costs.aggregate(session_id="SESSION", period="week")["events"] == 3
    assert costs.aggregate(session_id="SESSION", period="month")["by_capability"] == {"PRICE_WEB_SEARCH": "0.03500000"}
