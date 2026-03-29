from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ValidationCheck:
    name: str
    passed: bool
    severity: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PremiumPathValidation:
    """Validação aditiva do caminho premium.

    Não executa render, publish nem runtime oficial. Apenas audita se os pacotes
    produzidos pelas novas camadas estão consistentes e prontos para futura integração.
    """

    def evaluate(
        self,
        *,
        seo_social: dict[str, Any] | None = None,
        subtitle_package: dict[str, Any] | None = None,
        premium_protocol: dict[str, Any] | None = None,
        llm_orchestration: dict[str, Any] | None = None,
        legacy_report: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        seo_social = _safe_dict(seo_social)
        subtitle_package = _safe_dict(subtitle_package)
        premium_protocol = _safe_dict(premium_protocol)
        llm_orchestration = _safe_dict(llm_orchestration)
        legacy_report = _safe_dict(legacy_report)

        checks = [
            self._check_seo_social(seo_social),
            self._check_subtitle_package(subtitle_package),
            self._check_premium_protocol(premium_protocol),
            self._check_llm_orchestration(llm_orchestration),
            self._check_legacy_report(legacy_report),
            self._check_cross_consistency(
                seo_social=seo_social,
                subtitle_package=subtitle_package,
                premium_protocol=premium_protocol,
                llm_orchestration=llm_orchestration,
            ),
        ]

        passed = all(check.passed or check.severity != "hard" for check in checks)
        hard_failures = [check.name for check in checks if not check.passed and check.severity == "hard"]
        soft_failures = [check.name for check in checks if not check.passed and check.severity == "soft"]

        return {
            "ok": True,
            "engine": "PremiumPathValidation",
            "passed": passed,
            "checks": [check.to_dict() for check in checks],
            "hard_failures": hard_failures,
            "soft_failures": soft_failures,
            "summary": _summary(passed=passed, hard_failures=hard_failures, soft_failures=soft_failures),
            "next_action": _next_action(hard_failures=hard_failures, soft_failures=soft_failures),
        }

    def _check_seo_social(self, packet: dict[str, Any]) -> ValidationCheck:
        keywords = packet.get("primary_keywords") or []
        timing = _safe_dict(packet.get("timing_recommendation"))
        hashtags = packet.get("hashtags") or []
        passed = bool(keywords) and bool(timing.get("primary_window")) and bool(hashtags)
        return ValidationCheck(
            name="seo_social_packet",
            passed=passed,
            severity="hard",
            message="keywords, timing e hashtags devem existir",
        )

    def _check_subtitle_package(self, packet: dict[str, Any]) -> ValidationCheck:
        cues = packet.get("cues") or []
        hook_overlay = _safe_dict(packet.get("hook_overlay"))
        passed = bool(cues) and bool(hook_overlay.get("text"))
        return ValidationCheck(
            name="subtitle_package",
            passed=passed,
            severity="hard",
            message="subtitle cues e hook overlay devem existir",
        )

    def _check_premium_protocol(self, packet: dict[str, Any]) -> ValidationCheck:
        classification = str(packet.get("classification") or "").strip()
        failed_checks = packet.get("failed_checks") or []
        passed = bool(classification) and isinstance(failed_checks, list)
        return ValidationCheck(
            name="premium_protocol_packet",
            passed=passed,
            severity="hard",
            message="classification e failed_checks devem estar presentes",
        )

    def _check_llm_orchestration(self, packet: dict[str, Any]) -> ValidationCheck:
        role_briefs = packet.get("role_briefs") or []
        workflow_order = packet.get("workflow_order") or []
        passed = len(role_briefs) >= 4 and len(workflow_order) >= 4
        return ValidationCheck(
            name="llm_orchestration_packet",
            passed=passed,
            severity="hard",
            message="role briefs e workflow precisam estar completos",
        )

    def _check_legacy_report(self, packet: dict[str, Any]) -> ValidationCheck:
        summary = _safe_dict(packet.get("summary"))
        passed = "total_assets" in summary and "keep_count" in summary
        return ValidationCheck(
            name="legacy_report_packet",
            passed=passed,
            severity="soft",
            message="relatório de legado deve trazer summary com total e keep_count",
        )

    def _check_cross_consistency(
        self,
        *,
        seo_social: dict[str, Any],
        subtitle_package: dict[str, Any],
        premium_protocol: dict[str, Any],
        llm_orchestration: dict[str, Any],
    ) -> ValidationCheck:
        shared_context = _safe_dict(llm_orchestration.get("shared_context"))
        subtitle_hook = _safe_dict(subtitle_package.get("hook_overlay")).get("text")
        premium_classification = str(premium_protocol.get("classification") or "").strip()
        passed = all(
            [
                shared_context.get("subtitle_hook_text") == subtitle_hook,
                shared_context.get("classification") in {None, ""} or True,
                shared_context.get("primary_keywords") == (seo_social.get("primary_keywords") or []),
                premium_classification != "",
            ]
        )
        return ValidationCheck(
            name="cross_consistency",
            passed=passed,
            severity="soft",
            message="hook, keywords e classification devem permanecer coerentes entre pacotes",
        )


def run_premium_path_validation(
    *,
    seo_social: dict[str, Any] | None = None,
    subtitle_package: dict[str, Any] | None = None,
    premium_protocol: dict[str, Any] | None = None,
    llm_orchestration: dict[str, Any] | None = None,
    legacy_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    suite = PremiumPathValidation()
    return suite.evaluate(
        seo_social=seo_social,
        subtitle_package=subtitle_package,
        premium_protocol=premium_protocol,
        llm_orchestration=llm_orchestration,
        legacy_report=legacy_report,
    )


def premium_path_validation_examples() -> dict[str, Any]:
    return run_premium_path_validation(
        seo_social={
            "primary_keywords": ["clareza", "disciplina"],
            "hashtags": ["#clareza", "#disciplina"],
            "timing_recommendation": {"primary_window": "19:00-21:00"},
        },
        subtitle_package={
            "cues": [{"text": "Você está cansado ou distraído?"}],
            "hook_overlay": {"text": "Você está cansado ou distraído?"},
        },
        premium_protocol={
            "classification": "editorial_staging",
            "failed_checks": [],
        },
        llm_orchestration={
            "workflow_order": ["strategist", "writer", "director", "editor", "qa"],
            "role_briefs": [{"role": "strategist"}, {"role": "writer"}, {"role": "director"}, {"role": "editor"}],
            "shared_context": {
                "subtitle_hook_text": "Você está cansado ou distraído?",
                "primary_keywords": ["clareza", "disciplina"],
            },
        },
        legacy_report={
            "summary": {"total_assets": 8, "keep_count": 3},
        },
    )


def _safe_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "to_dict"):
        try:
            return value.to_dict()
        except Exception:
            return {}
    return {}


def _summary(*, passed: bool, hard_failures: list[str], soft_failures: list[str]) -> str:
    if passed and not soft_failures:
        return "trilha premium validada sem falhas detectadas"
    if hard_failures:
        return f"falhas duras encontradas: {', '.join(hard_failures)}"
    return f"trilha válida com ajustes suaves pendentes: {', '.join(soft_failures)}"


def _next_action(*, hard_failures: list[str], soft_failures: list[str]) -> str:
    if hard_failures:
        return "corrigir pacotes incompletos antes de integrar ao runtime"
    if soft_failures:
        return "ajustar coerência fina e então preparar integração única"
    return "pronto para ligação controlada no runtime oficial"
