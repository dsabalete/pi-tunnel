"""Alert engine for PiTunnel sensor monitoring."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from pitunnel.storage.history import History


@dataclass
class AlertRule:
    """Configuration for a single alert rule."""
    rule_id: str
    sensor_id: str
    when: str  # expression like "> 27.5", "< 10", "== 1"
    cooldown_min: int = 60
    enabled: bool = True


@dataclass
class AlertResult:
    """Result of evaluating a single rule against a reading."""
    rule_id: str
    sensor_id: str
    triggered: bool
    message: Optional[str] = None


@dataclass
class EngineResult:
    """Result of running the full alert engine."""
    triggered: List[AlertResult] = field(default_factory=list)
    suppressed: List[AlertResult] = field(default_factory=list)
    startup_notification: bool = False


class AlertEngine:
    """Evaluates sensor readings against configured alert rules.

    Responsibilities:
    - Evaluate rule expressions against reading values
    - Enforce per-rule cooldown periods using unified History storage
    - Dispatch startup notification once on bot init
    """

    def __init__(
        self,
        config_path: str = "config.yaml",
        db_path: str = "db.sqlite3",
        history: Optional[History] = None,
    ):
        self.config_path = config_path
        self.db_path = db_path
        self.history = history
        self._startup_notification_sent = False

    def load_rules(self) -> List[AlertRule]:
        """Load alert rules from configuration file.

        Returns list of AlertRule objects. Returns empty list if config
        does not exist or has no alerts section.
        """
        try:
            import yaml
        except ImportError:
            return []

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
        except Exception:
            return []

        rules_cfg = cfg.get("alerts", {}).get("rules", [])
        rules: List[AlertRule] = []
        for rcfg in rules_cfg or []:
            rule = AlertRule(
                rule_id=rcfg.get("rule_id", "unknown"),
                sensor_id=rcfg.get("sensor_id", "unknown"),
                when=rcfg.get("when", ""),
                cooldown_min=int(rcfg.get("cooldown_min", 60)),
                enabled=bool(rcfg.get("enabled", True)),
            )
            rules.append(rule)
        return rules

    def evaluate_rules(self, readings: List[Dict[str, Any]]) -> EngineResult:
        """Evaluate all rules against the provided sensor readings.

        Args:
            readings: List of dicts with at least `sensor_id` and `value` keys.

        Returns:
            EngineResult with triggered and suppressed rule results.
        """
        rules = self.load_rules()
        triggered: List[AlertResult] = []
        suppressed: List[AlertResult] = []

        for rule in rules:
            if not rule.enabled:
                continue

            # Find matching reading
            reading = None
            for r in readings:
                if r.get("sensor_id") == rule.sensor_id:
                    reading = r
                    break

            if reading is None or reading.get("value") is None:
                # No reading for this sensor – skip
                continue

            value = reading["value"]
            triggered_flag = self._eval_expression(rule.when, value)

            if triggered_flag:
                # Check cooldown
                suppressed_flag = self._check_cooldown(rule.rule_id)
                if suppressed_flag:
                    suppressed.append(
                        AlertResult(
                            rule_id=rule.rule_id,
                            sensor_id=rule.sensor_id,
                            triggered=True,
                            message=f"Rule {rule.rule_id} suppressed by cooldown",
                        )
                    )
                else:
                    # Log the alert to history
                    if self.history is not None:
                        self.history.log_alert(
                            rule_id=rule.rule_id,
                            sensor_id=rule.sensor_id,
                            value=value,
                        )
                    triggered.append(
                        AlertResult(
                            rule_id=rule.rule_id,
                            sensor_id=rule.sensor_id,
                            triggered=True,
                            message=f"Alert triggered for {rule.sensor_id}: {rule.when}",
                        )
                    )

        return EngineResult(triggered=triggered, suppressed=suppressed)

    def _eval_expression(self, expression: str, value: Any) -> bool:
        """Safely evaluate a simple comparison expression.

        Supported formats from config: "> 27.5", "< 10", ">= 5", "<= 3", "== 1", "!= 0"
        The expression is combined as `value <op> threshold` and evaluated.

        Args:
            expression: e.g. "> 27.5"
            value: the reading value to compare

        Returns:
            True if the expression holds, False otherwise.
        """
        # Parse the expression: operator and threshold
        m = re.fullmatch(r"\s*([><=!]+)\s+([\d.eE+\-]+)\s*", expression)
        if m is None:
            raise ValueError(f"Invalid expression format: {expression!r}")

        op = m.group(1)
        threshold = float(m.group(2))

        # Map operator to comparison
        if op == ">":
            return value > threshold
        if op == "<":
            return value < threshold
        if op == ">=":
            return value >= threshold
        if op == "<=":
            return value <= threshold
        if op == "==":
            return value == threshold
        if op == "!=":
            return value != threshold

        # Should not reach here
        return False

    def _check_cooldown(self, rule_id: str) -> bool:
        """Return True if the rule is currently suppressed by cooldown.

        Uses History.get_last_alert_ts() for cooldown tracking.
        Returns False and updates timestamp when the cooldown period has elapsed.
        """
        if self.history is None:
            # No history logger - no cooldown enforcement
            return False

        last_ts = self.history.get_last_alert_ts(rule_id)
        if last_ts is None:
            # No previous alert - not suppressed
            return False

        # Find the rule to get its cooldown
        rules = self.load_rules()
        cooldown_sec = 60 * 60  # Default 1 hour
        for rule in self.load_rules():
            if rule.rule_id == rule_id:
                cooldown_sec = rule.cooldown_min * 60
                break

        now = time.time()
        elapsed = now - last_ts

        if elapsed < cooldown_sec:
            # Still within cooldown – suppress
            return True

        # Cooldown elapsed – allow
        return False

    def record_startup_notification(self) -> None:
        """Mark that the startup notification has been sent.

        Should be called once when the bot starts up.
        """
        self._startup_notification_sent = True

    def should_send_startup(self) -> bool:
        """Return True if the startup notification has not been sent yet."""
        return not self._startup_notification_sent