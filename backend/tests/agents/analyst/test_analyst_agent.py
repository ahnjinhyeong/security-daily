from typing import Any

import pytest

from security_daily.agents.analyst.schemas import AnalystOutput
from pydantic import ValidationError


def valid_payload() -> dict[str, Any]:
    return {
        "importance": "중요하다.",
        "attack_scenario": "POSSIBLE: 공격 가능성이 있다.",
        "security_actions": ["패치 확인", "패치 확인", "로그 점검"],
        "key_concepts": [{"name": "RCE", "description": "원격 코드 실행"}],
        "related_security_info": [],
    }


def test_analyst_output_cleans_duplicates() -> None:
    output = AnalystOutput.model_validate(valid_payload())
    assert output.security_actions == ["패치 확인", "로그 점검"]


@pytest.mark.parametrize("field", ["security_actions", "key_concepts", "related_security_info"])
def test_analyst_output_rejects_more_than_five_items(field: str) -> None:
    payload = valid_payload()
    if field == "security_actions":
        payload[field] = [f"조치 {i}" for i in range(6)]
    elif field == "key_concepts":
        payload[field] = [{"name": str(i), "description": "설명"} for i in range(6)]
    else:
        payload[field] = [{"type": "CVE", "value": f"CVE-2026-{i:04d}"} for i in range(6)]
    with pytest.raises(ValidationError):
        AnalystOutput.model_validate(payload)
