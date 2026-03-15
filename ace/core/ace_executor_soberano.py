from __future__ import annotations

import threading
import time
import traceback
from typing import Any, Dict, Optional


class ExecutorSoberano:
    def __init__(self, ace_runtime: Any):
        self.ace = ace_runtime
        self._boot_started = False
        self._threads = []

    def _log(self, level: str, event: str, detail: Any = "") -> None:
        try:
            self.ace.log(level, event, detail)
        except Exception:
            print(f"[ACE][{level}] {event} | {detail}")

    def _state(self) -> Dict[str, Any]:
        return getattr(self.ace, "ACE_STATE", {})

    def _queue(self):
        return getattr(self.ace, "TASK_QUEUE")

    def _lock(self):
        return getattr(self.ace, "TASK_LOCK")

    def _mark_task_memory(self, task: Dict[str, Any], status: str, reason: str = "") -> None:
        fn = getattr(self.ace, "mark_task_memory", None)
        if callable(fn):
            try:
                fn(task, status, reason)
            except Exception as e:
                self._log("WARN", "mark_task_memory_fail", str(e))

    def _register_performance(self, action_type: str, success: bool = True) -> None:
        fn = getattr(self.ace, "register_performance", None)
        if callable(fn):
            try:
                fn(action_type, success)
            except Exception as e:
                self._log("WARN", "register_performance_fail", str(e))

    def enqueue_task_soberano(
        self,
        task_type: str,
        trend: Optional[str] = None,
        style: Optional[str] = None,
        priority: float = 1.0,
        retries: int = 0,
    ) -> Dict[str, Any]:
        legacy_queue_task = getattr(self.ace, "queue_task", None)
        if callable(legacy_queue_task):
            legacy_queue_task(
                task_type=task_type,
                trend=trend,
                style=style,
                priority=priority,
                retries=retries,
            )
            with self._lock():
                qsize = len(self._queue())
            return {"ok": True, "queued": True, "queue_size": qsize}

        capturar_trend = getattr(self.ace, "capturar_trend_brasil", lambda: "disciplina e prosperidade")
        escolher_personalidade = getattr(self.ace, "escolher_personalidade", lambda: "direto")
        estimate_task_score = getattr(self.ace, "estimate_task_score", lambda t, tr: 1.0)
        ace_max_queue_size = getattr(self.ace, "ACE_MAX_QUEUE_SIZE", 3)

        with self._lock():
            if len(self._queue()) >= ace_max_queue_size:
                return {"ok": False, "queued": False, "reason": "queue_full", "queue_size": len(self._queue())}

            trend = trend or capturar_trend()
            style = style or escolher_personalidade()
            predictive_score = float(estimate_task_score(task_type, trend))
            final_priority = float(priority) * predictive_score

            task = {
                "id": int(time.time() * 1000),
                "type": task_type,
                "trend": trend,
                "style": style,
                "priority": final_priority,
                "raw_priority": float(priority),
                "predictive_score": predictive_score,
                "retries": retries,
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            }
            self._queue().append(task)
            self._queue().sort(key=lambda x: x["priority"], reverse=True)
            return {"ok": True, "queued": True, "task": task, "queue_size": len(self._queue())}

    def execute_task_soberano(self, task: Dict[str, Any]) -> Dict[str, Any]:
        task_type = task.get("type")

        try:
            if task_type in ("reel", "presenca"):
                dispatch = getattr(self.ace, "ace_sv_dispatch_reel", None)
                if callable(dispatch):
                    result = dispatch()
                else:
                    fabricar = getattr(self.ace, "fabricar_presenca_digital")
                    media_path, manifesto, publish_result = fabricar("REEL")
                    result = {
                        "ok": bool(getattr(publish_result, "get", lambda *_: False)("ok")),
                        "type": "reel",
                        "media_path": media_path,
                        "result": publish_result,
                        "text": manifesto,
                    }

                if result.get("ok"):
                    self._register_performance("reel", True)
                    self._mark_task_memory(task, "done", "sovereign_video_ok")
                else:
                    self._register_performance("reel", False)
                    self._mark_task_memory(task, "failed", result.get("result", {}).get("reason", "sovereign_video_fail"))
                return result

            if task_type == "carrossel":
                trend = task.get("trend")
                style = task.get("style")

                pick_trend = getattr(self.ace, "ace_pick_trend_sanitized", None) or getattr(self.ace, "capturar_trend_brasil")
                pick_style = getattr(self.ace, "ace_pick_style_smart", None) or getattr(self.ace, "escolher_personalidade")
                pick_hook = getattr(self.ace, "ace_pick_best_hook_smart", None) or getattr(self.ace, "get_best_saved_hook")
                llm = getattr(self.ace, "ace_router_generate_text", None) or getattr(self.ace, "gerar_texto_gpt")
                criar_carrossel = getattr(self.ace, "criar_carrossel")

                trend = trend or pick_trend()
                style = style or pick_style()
                hook = pick_hook(trend)

                prompt = f"""
Crie um carrossel de 5 slides em português do Brasil.
Tema: {trend}
Estilo: {style}
Hook: {hook}
Estrutura:
Slide 1 = Hook
Slide 2 = Problema
Slide 3 = Insight
Slide 4 = Solução
Slide 5 = CTA
"""
                body = llm(prompt)
                result = criar_carrossel(trend, [hook, str(body)[:220], "Insight", "Solução", "CTA"])
                payload = {"ok": bool(result.get("ok")), "type": "carrossel", "result": result}

                if payload.get("ok"):
                    self._register_performance("carrossel", True)
                    self._mark_task_memory(task, "done", "carousel_ok")
                else:
                    self._register_performance("carrossel", False)
                    self._mark_task_memory(task, "failed", result.get("reason", "carousel_fail"))
                return payload

            self._mark_task_memory(task, "failed", f"unknown_task_type:{task_type}")
            return {"ok": False, "error": f"tipo desconhecido: {task_type}"}

        except Exception as e:
            self._log("ERROR", "execute_task_soberano_fail", {"task": task, "error": str(e)})
            self._mark_task_memory(task, "failed", str(e))
            return {"ok": False, "error": str(e)}

    def queue_executor_loop_soberano(self) -> None:
        bad_task_threshold = float(getattr(self.ace, "BAD_TASK_THRESHOLD", 0.65))
        max_task_retries = int(getattr(self.ace, "MAX_TASK_RETRIES", 2))

        self._log("INFO", "queue_executor_soberano_start", "Executor soberano iniciado")

        while True:
            try:
                task = None
                with self._lock():
                    if self._queue():
                        task = self._queue().pop(0)

                if task:
                    if float(task.get("predictive_score", 1.0)) < bad_task_threshold:
                        self._mark_task_memory(task, "discarded", "low_predictive_score")
                        self._log("INFO", "task_discarded", task)
                        time.sleep(2)
                        continue

                    result = self.execute_task_soberano(task)
                    self._log("INFO", "queue_task_executed_soberano", result)

                    if not result.get("ok"):
                        retries = int(task.get("retries", 0))
                        if retries < max_task_retries:
                            fallback = "carrossel" if task.get("type") == "reel" else "reel"
                            self.enqueue_task_soberano(
                                task_type=fallback,
                                trend=task.get("trend"),
                                style=task.get("style"),
                                priority=max(0.5, float(task.get("raw_priority", 1.0)) - 0.12),
                                retries=retries + 1,
                            )
                        else:
                            self._mark_task_memory(task, "dead", "retry_limit_reached")

                time.sleep(4)

            except Exception:
                self._log("ERROR", "queue_executor_loop_soberano_fail", traceback.format_exc())
                time.sleep(10)

    def is_idle_soberano(self, minutes: int = 8) -> bool:
        ace_state = self._state()
        ts = ace_state.get("last_action_at")
        if not ts:
            return True
        try:
            import datetime as _dt
            last = _dt.datetime.fromisoformat(ts)
            return (_dt.datetime.now() - last).total_seconds() > minutes * 60
        except Exception:
            return True

    def recover_system_soberano(self) -> None:
        import gc
        try:
            gc.collect()
        except Exception:
            pass

        for name in ["iniciar_banco", "analisar_instagram", "analisar_comentarios", "detectar_trend_emergente"]:
            fn = getattr(self.ace, name, None)
            if callable(fn):
                try:
                    fn()
                except Exception:
                    pass

    def smart_force_action_soberano(self) -> Dict[str, Any]:
        capturar_trend = getattr(self.ace, "capturar_trend_brasil")
        escolher_personalidade = getattr(self.ace, "escolher_personalidade")
        get_recent_signal_score = getattr(self.ace, "get_recent_signal_score", lambda: 0.5)
        choose_best_content_type = getattr(self.ace, "choose_best_content_type", lambda: "reel")
        ace_force_secondary_task = bool(getattr(self.ace, "ACE_FORCE_SECONDARY_TASK", False))
        ace_max_queue_size = int(getattr(self.ace, "ACE_MAX_QUEUE_SIZE", 3))

        trend = capturar_trend()
        style = escolher_personalidade()
        signal = float(get_recent_signal_score())
        best_type = choose_best_content_type()

        with self._lock():
            qsize = len(self._queue())

        if qsize >= ace_max_queue_size:
            self._log("INFO", "smart_force_skipped_queue_full", {"qsize": qsize})
            return {"ok": True, "skipped": True, "reason": "queue_full", "queue_size": qsize}

        priority = 1.2 if self.is_idle_soberano(8) else 0.9
        priority *= (0.8 + signal)

        self.enqueue_task_soberano(
            task_type=best_type,
            trend=trend,
            style=style,
            priority=priority,
            retries=0,
        )

        if ace_force_secondary_task:
            with self._lock():
                qsize_after = len(self._queue())
            if qsize_after < ace_max_queue_size:
                secondary = "carrossel" if best_type == "reel" else "reel"
                self.enqueue_task_soberano(
                    task_type=secondary,
                    trend=trend,
                    style=style,
                    priority=max(0.5, priority - 0.2),
                    retries=0,
                )

        ace_state = self._state()
        ace_state["forced_actions"] = int(ace_state.get("forced_actions", 0)) + 1

        payload = {
            "ok": True,
            "queued_primary": best_type,
            "trend": trend,
            "style": style,
            "signal": signal,
        }
        self._log("INFO", "smart_force_action_soberano", payload)
        return payload

    def supervisor_loop_soberano(self) -> None:
        import datetime as _dt
        ace_render_safe_boot = bool(getattr(self.ace, "ACE_RENDER_SAFE_BOOT", False))
        ace_skip_first_supervisor_force = bool(getattr(self.ace, "ACE_SKIP_FIRST_SUPERVISOR_FORCE", False))
        render_url = getattr(self.ace, "RENDER_URL", None)
        requests_mod = getattr(self.ace, "requests", None)
        get_ig_token = getattr(self.ace, "get_ig_token", lambda: None)
        get_ig_id = getattr(self.ace, "get_ig_id", lambda: None)

        self._log("INFO", "supervisor_soberano_start", "Supervisor soberano iniciado")
        boot_done = False

        while True:
            try:
                ace_state = self._state()
                ace_state["last_cycle_at"] = _dt.datetime.now().isoformat()
                ace_state["symbiosis_level"] = min(1.0, float(ace_state.get("symbiosis_level", 0.0)) + 0.02)
                ace_state["mode"] = "SUPERVISIONANDO"
                ace_state["instagram_connected"] = bool(get_ig_token() and get_ig_id())

                self.recover_system_soberano()

                if not boot_done and not ace_skip_first_supervisor_force:
                    self._log("INFO", "boot_force_soberano", "Forçando ação imediata no boot")
                    self.smart_force_action_soberano()
                    boot_done = True
                else:
                    boot_done = True

                if self.is_idle_soberano(8) and not ace_render_safe_boot:
                    ace_state["idle_hits"] = int(ace_state.get("idle_hits", 0)) + 1
                    self._log("WARN", "idle_detected_soberano", "ACE online mas improdutivo; forçando ação")
                    self.smart_force_action_soberano()

                if (not ace_render_safe_boot) and render_url and requests_mod is not None:
                    try:
                        requests_mod.get(f"{render_url}/status", timeout=5)
                        ace_state["render_pings"] = int(ace_state.get("render_pings", 0)) + 1
                    except Exception:
                        pass

                time.sleep(45)

            except Exception:
                ace_state = self._state()
                ace_state["last_error"] = traceback.format_exc()[-1800:]
                self._log("ERROR", "supervisor_loop_soberano_fail", ace_state["last_error"])
                time.sleep(15)

    def boot_executor_soberano(self) -> None:
        if self._boot_started:
            return

        self._boot_started = True
        self._log("INFO", "boot_executor_soberano_start", "Inicializando executor soberano")

        t1 = threading.Thread(target=self.queue_executor_loop_soberano, daemon=True, name="ace_queue_executor_soberano")
        t2 = threading.Thread(target=self.supervisor_loop_soberano, daemon=True, name="ace_supervisor_soberano")
        t1.start()
        t2.start()
        self._threads.extend([t1, t2])

        ace_skip_boot_force = bool(getattr(self.ace, "ACE_SKIP_BOOT_FORCE", False))
        if not ace_skip_boot_force:
            try:
                self.smart_force_action_soberano()
            except Exception as e:
                self._log("WARN", "boot_executor_soberano_force_fail", str(e))

        self._log("INFO", "boot_executor_soberano_ok", "Supervisor e executor soberanos ativos")


def install_executor_soberano(ace_runtime: Any) -> ExecutorSoberano:
    executor = ExecutorSoberano(ace_runtime)

    ace_runtime.executor_soberano = executor
    ace_runtime.enqueue_task_soberano = executor.enqueue_task_soberano
    ace_runtime.execute_task_soberano = executor.execute_task_soberano
    ace_runtime.queue_executor_loop_soberano = executor.queue_executor_loop_soberano
    ace_runtime.smart_force_action_soberano = executor.smart_force_action_soberano
    ace_runtime.supervisor_loop_soberano = executor.supervisor_loop_soberano
    ace_runtime.boot_executor_soberano = executor.boot_executor_soberano

    return executor
