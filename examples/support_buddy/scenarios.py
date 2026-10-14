"""Example payloads for the Support Buddy X9000 integration."""

SCENARIOS = {
    "start_session": {
        "action_type": "start_devin_session",
        "action": {
            "session_type": "investigation",
            "target_repo": "acme/backend",
            "branch": "fix/timeout-issue",
        },
        "objective": "Investigate recurring database timeout errors in production",
        "state": {"incident_id": "INC-5678", "severity": "P2"},
        "evidence": {"error_count_24h": 142, "affected_users": 23},
    },
    "create_pr": {
        "action_type": "create_pr",
        "action": {
            "repo": "acme/backend",
            "title": "Fix: Increase connection pool timeout to 30s",
            "base": "main",
            "head": "fix/timeout-issue",
            "files_changed": 2,
            "lines_added": 5,
            "lines_removed": 2,
        },
        "objective": "Submit fix for database timeout issue",
        "state": {"incident_id": "INC-5678", "investigation_complete": True},
        "evidence": {
            "root_cause_identified": True,
            "tests_passing": True,
            "similar_fix_successful": True,
        },
    },
    "send_customer_response": {
        "action_type": "send_email",
        "action": {
            "to": "enterprise-client@example.com",
            "subject": "Re: Database timeout issues [INC-5678]",
            "body": "We've identified the root cause and deployed a fix. "
                    "The connection pool timeout has been increased. "
                    "Please let us know if you see any further issues.",
        },
        "objective": "Notify customer that their reported issue has been resolved",
        "state": {"incident_id": "INC-5678", "fix_deployed": True},
        "evidence": {"fix_verified_in_staging": True, "monitoring_green": True},
    },
    "escalate_incident": {
        "action_type": "escalate_incident",
        "action": {
            "incident_id": "INC-9999",
            "target_team": "database-infra",
            "severity_override": "P1",
            "reason": "Cascading failures detected across multiple services",
        },
        "objective": "Escalate incident to specialized team due to scope expansion",
        "state": {"current_severity": "P2", "affected_services": 5},
        "evidence": {"cascade_detected": True, "auto_remediation_failed": True},
    },
    "retry_investigation": {
        "action_type": "start_devin_session",
        "action": {
            "session_type": "investigation",
            "target_repo": "acme/backend",
            "branch": "investigate/memory-leak",
            "scope": "expanded",
        },
        "objective": "Re-investigate with broader scope after initial investigation was inconclusive",
        "state": {"previous_attempt": True, "inconclusive_reason": "root cause not in backend repo"},
        "evidence": {"memory_growth_confirmed": True, "heap_dump_collected": True},
    },
}
