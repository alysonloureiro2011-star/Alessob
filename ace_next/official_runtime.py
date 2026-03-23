*** Begin Patch
*** Update File: ace_next/official_runtime.py
@@
 try:
     from .performance_store import PerformanceStore
     from .learning_loop import build_learning_loop_summary
     from .post_performance_contract import build_post_performance_contract
     from .performance_ingest import collect_real_performance_metrics
     from .reflection_memory import build_reflection_memory
     from .attention_metrics import build_attention_metrics
     from .experiment_registry import ExperimentRegistry, build_experiment_record
     from .episodic_performance_memory import EpisodicPerformanceMemory, build_episode_record
     from .performance_summary import build_performance_summary
+    from .resonance_engine import build_resonance_engine
+    from .reward_prediction_layer import build_reward_prediction
+    from .thompson_sampler import build_thompson_sampler
 except Exception as exc:
     MEASUREMENT_STACK_IMPORT_ERROR = f"{type(exc).__name__}: {exc}"
     PerformanceStore = None
     build_learning_loop_summary = None
     build_post_performance_contract = None
@@
     build_reflection_memory = None
     build_attention_metrics = None
     ExperimentRegistry = None
     build_experiment_record = None
     EpisodicPerformanceMemory = None
     build_episode_record = None
     build_performance_summary = None
+    build_resonance_engine = None
+    build_reward_prediction = None
+    build_thompson_sampler = None
@@
     def _measurement_fallback(self, *, reason: str):
         post_performance_contract = {"ok": False, "error": reason}
         performance_ingest = {
             "ok": False,
             "attempted": False,
@@
         attention_metrics = {
             "ok": False,
             "source_status": "ingest_error",
             "breakdown": {},
             "available_inputs": [],
             "notes": [reason],
         }
+        resonance_engine = {
+            "ok": False,
+            "resonance_score": None,
+            "reasons": [reason],
+        }
+        reward_prediction = {
+            "ok": False,
+            "reward_prediction_score": None,
+            "reasons": [reason],
+        }
+        thompson_sampler = {
+            "ok": False,
+            "selected_variant": None,
+            "confidence_level": "low",
+            "decision_state": "collecting",
+            "posterior_mean": None,
+            "winner_candidate": False,
+            "reasons": [reason],
+        }
+        decision_core_summary = {
+            "ok": False,
+            "resonance_score": None,
+            "reward_prediction_score": None,
+            "selected_variant": None,
+            "confidence_level": "low",
+            "experiment_decision_state": "collecting",
+            "posterior_mean": None,
+            "winner_candidate": False,
+            "reasons": [reason],
+        }
         experiment_registry = {"ok": False, "error": reason}
         episodic_performance_memory = {"ok": False, "error": reason}
         reflection_memory = {
             "ok": False,
             "status": "ingest_error",
@@
         performance_summary = {"ok": False, "error": reason}
         return (
             post_performance_contract,
             performance_ingest,
             attention_metrics,
+            resonance_engine,
+            reward_prediction,
+            thompson_sampler,
+            decision_core_summary,
             experiment_registry,
             episodic_performance_memory,
             reflection_memory,
             learning_loop,
             performance_summary,
         )
@@
         if (
             MEASUREMENT_STACK_IMPORT_ERROR
             or not PerformanceStore
             or not build_learning_loop_summary
             or not build_post_performance_contract
             or not collect_real_performance_metrics
             or not build_reflection_memory
             or not build_attention_metrics
             or not ExperimentRegistry
             or not build_experiment_record
             or not EpisodicPerformanceMemory
             or not build_episode_record
             or not build_performance_summary
+            or not build_resonance_engine
+            or not build_reward_prediction
+            or not build_thompson_sampler
         ):
             fallback = self._measurement_fallback(reason=f"measurement_stack_import_error: {MEASUREMENT_STACK_IMPORT_ERROR or 'unknown'}")
             return (*fallback, {"ok": False, "error": MEASUREMENT_STACK_IMPORT_ERROR or "measurement_stack_unavailable"})
@@
             record["real_metrics"] = real_metrics
             record["performance_ingest"] = performance_ingest
             record["attention_metrics"] = attention_metrics
+            resonance_engine = build_resonance_engine(record=record)
+            reward_prediction = build_reward_prediction(
+                record=record,
+                resonance_engine=resonance_engine,
+            )
+            thompson_sampler = build_thompson_sampler(
+                record=record,
+                reward_prediction=reward_prediction,
+                conservative_mode=True,
+            )
+            decision_core_summary = {
+                "resonance_score": resonance_engine.get("resonance_score"),
+                "reward_prediction_score": reward_prediction.get("reward_prediction_score"),
+                "selected_variant": thompson_sampler.get("selected_variant"),
+                "confidence_level": thompson_sampler.get("confidence_level"),
+                "experiment_decision_state": thompson_sampler.get("decision_state"),
+                "posterior_mean": thompson_sampler.get("posterior_mean"),
+                "winner_candidate": thompson_sampler.get("winner_candidate"),
+                "conservative_mode": thompson_sampler.get("conservative_mode"),
+            }
+            record["resonance_engine"] = resonance_engine
+            record["reward_prediction"] = reward_prediction
+            record["sampler_decision"] = thompson_sampler
+            record["decision_core_summary"] = decision_core_summary
             record["post_performance"] = {
                 "status": real_metrics.get("source_status"),
                 "source": real_metrics.get("source_endpoint"),
                 "metrics": {
@@
             performance_summary = build_performance_summary(
                 performance_store=performance_store,
                 learning_loop=learning_loop,
                 experiment_registry=experiment_registry,
                 episodic_performance_memory=episodic_performance_memory,
                 attention_metrics=attention_metrics,
                 real_metrics_contract=real_metrics,
                 performance_ingest=performance_ingest,
                 publish_result=publish_result,
                 reflection_memory=reflection_memory,
                 probe_context=probe_context,
+                resonance_engine=resonance_engine,
+                reward_prediction=reward_prediction,
+                thompson_sampler=thompson_sampler,
+                decision_core_summary=decision_core_summary,
             )
             return (
                 record,
                 performance_ingest,
                 attention_metrics,
+                resonance_engine,
+                reward_prediction,
+                thompson_sampler,
+                decision_core_summary,
                 experiment_registry,
                 episodic_performance_memory,
                 reflection_memory,
                 learning_loop,
                 performance_summary,
                 performance_store,
             )
@@
         (
             post_performance_contract,
             performance_ingest,
             attention_metrics,
+            resonance_engine,
+            reward_prediction,
+            thompson_sampler,
+            decision_core_summary,
             experiment_registry,
             episodic_performance_memory,
             reflection_memory,
             learning_loop,
             performance_summary,
@@
             "performance_ingest": performance_ingest,
             "real_metrics_contract": performance_ingest.get("real_metrics") if isinstance(performance_ingest, dict) else None,
             "attention_metrics": attention_metrics,
+            "resonance_engine": resonance_engine,
+            "reward_prediction": reward_prediction,
+            "thompson_sampler": thompson_sampler,
+            "decision_core_summary": decision_core_summary,
             "experiment_registry": experiment_registry,
             "episodic_performance_memory": episodic_performance_memory,
             "reflection_memory": reflection_memory,
             "learning_loop": learning_loop,
             "performance_summary": performance_summary,
*** End Patch
