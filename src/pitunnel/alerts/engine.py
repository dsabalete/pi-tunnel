"""Alert engine for PiTunnel sensor monitoring."""

from __future__ import annotations

import re
import sqlite3
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


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
    - Enforce per-rule cooldown periods using SQLite state
    - Dispatch startup notification once on bot init
    """

    def __init__(self, config_path: str = "config.yaml", db_path: str = "db.sqlite3"):
        self.config_path = config_path
        self.db_path = db_path
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

        Updates last_sent_ts in SQLite if the rule just triggered
        (i.e. not suppressed). Returns False and updates timestamp
        when the cooldown period has elapsed.
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.cursor()
            # Ensure table and schema exist
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS alert_history (
                    rule_id TEXT NOT NULL,
                    sensor_id TEXT NOT NULL,
                    last_sent_ts REAL NOT NULL
                )
                """
            )

            now = time.time()

            # Get existing timestamp for this rule
            row = cur.execute(
                "SELECT last_sent_ts FROM alert_history WHERE rule_id = ?",
                (rule_id,),
            ).fetchone()

            if row is None:
                # First occurrence – record timestamp and return False (not suppressed)
                cur.execute(
                    "INSERT INTO alert_history (rule_id, sensor_id, last_sent_ts) VALUES (?, ?, ?)",
                    (rule_id, "unknown", now),
                )
                conn.commit()
                return False

            # Determine cooldown from config
            cooldown_sec = self._rule_cooldown_seconds(rule_id)
            elapsed = now - row[0]

            if elapsed < cooldown_sec:
                # Still within cooldown – suppress, do NOT update timestamp
                return True

            # Cooldown elapsed – update timestamp and allow
            cur.execute(
                "UPDATE alert_history SET last_sent_ts = ? WHERE rule_id = ?",
                (now, rule_id),
            )
            conn.commit()
            return False
        finally:
            conn.close()

    def _rule_cooldown_seconds(self, rule_id: str) -> float:
        """Return cooldown period in seconds for the given rule id by re-loading config."""
        rules = self.load_rules()
        for rule in rules:
            if rule.rule_id == rule_id:
                return rule.cooldown_min * 60
        # Default fallback
        return 60 * 60  # 1 hour

    def record_startup_notification(self) -> None:
        """Mark that the startup notification has been sent.

        Should be called once when the bot starts up.
        """
        self._startup_notification_sent = True

    def should_send_startup(self) -> bool:
        """Return True if the startup notification has not been sent yet."""
        return not self._startup_notification_sent