from __future__ import annotations

import yaml
from pydantic import ValidationError

from jevops.policies.schema import PolicyConfig


class PolicyLoadError(Exception):
    pass


def load_policy_yaml(yaml_str: str) -> PolicyConfig:
    """Parse and validate a YAML policy definition."""
    try:
        data = yaml.safe_load(yaml_str)
    except yaml.YAMLError as e:
        raise PolicyLoadError(f"Invalid YAML: {e}") from e

    if not isinstance(data, dict):
        raise PolicyLoadError("Policy YAML must be a mapping")

    # Normalize rule conditions: single string `when:` → keep as string
    for rule in data.get("rules", []):
        when = rule.get("when")
        if isinstance(when, dict):
            # Already structured (all/any)
            pass
        elif isinstance(when, str):
            # Keep as string — engine handles this
            pass

    try:
        return PolicyConfig(**data)
    except ValidationError as e:
        raise PolicyLoadError(f"Policy validation error: {e}") from e
