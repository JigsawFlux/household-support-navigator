import src.explainer as explainer
from src.rules.base import RuleResult


class _Resp:
    def __init__(self, content: str):
        self.content = content


class _FakeLLM:
    def __init__(self, content: str):
        self._content = content

    def invoke(self, _messages):
        return _Resp(self._content)


def _sample_results():
    return [
        RuleResult(
            entitlement="Pension Credit",
            eligible=True,
            reason="Household income is below threshold.",
            source_url="https://www.gov.uk/pension-credit/eligibility",
            confidence="medium",
        ),
        RuleResult(
            entitlement="Healthy Start",
            eligible=False,
            reason="No qualifying benefit reported.",
            source_url="https://www.healthystart.nhs.uk/",
            confidence="medium",
        ),
    ]


def test_explain_results_uses_llm_output(monkeypatch):
    monkeypatch.setattr(
        explainer, "get_llm", lambda temperature=0.0: _FakeLLM("Pension Credit: you may qualify...")
    )
    output = explainer.explain_results(_sample_results())
    assert "Pension Credit" in output


def test_explain_results_falls_back_on_llm_failure(monkeypatch):
    def _raise(*_args, **_kwargs):
        raise RuntimeError("LLM unavailable")

    monkeypatch.setattr(explainer, "get_llm", _raise)
    output = explainer.explain_results(_sample_results())
    assert "Pension Credit" in output
    assert "gov.uk/pension-credit" in output


def test_fallback_template_includes_all_entitlements():
    output = explainer._fallback_template(_sample_results())
    assert "Pension Credit" in output
    assert "Healthy Start" in output
    assert "Documents you may need" in output


def test_explain_results_falls_back_on_empty_llm_response(monkeypatch):
    monkeypatch.setattr(explainer, "get_llm", lambda temperature=0.0: _FakeLLM("   "))
    output = explainer.explain_results(_sample_results())
    assert "Pension Credit" in output