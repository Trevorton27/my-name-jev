"""Analytical aggregation queries using Polars for decision data."""

from __future__ import annotations

from typing import Any

import polars as pl


def decisions_to_dataframe(decisions: list[dict[str, Any]]) -> pl.DataFrame:
    """Convert decision dicts to a Polars DataFrame."""
    if not decisions:
        return pl.DataFrame()
    return pl.DataFrame(decisions)


def disposition_by_action_type(df: pl.DataFrame) -> dict[str, dict[str, int]]:
    """Group disposition counts by action_type."""
    if df.is_empty():
        return {}
    result = df.group_by(["action_type", "disposition"]).agg(pl.count().alias("count")).sort("action_type")
    output: dict[str, dict[str, int]] = {}
    for row in result.iter_rows(named=True):
        at = row["action_type"]
        if at not in output:
            output[at] = {}
        output[at][row["disposition"]] = row["count"]
    return output


def confidence_band_metrics(
    df: pl.DataFrame, confidence_col: str = "confidence", bands: int = 5
) -> list[dict[str, Any]]:
    """Compute metrics by confidence band."""
    if df.is_empty() or confidence_col not in df.columns:
        return []

    df_with_band = df.with_columns((pl.col(confidence_col) * bands).cast(pl.Int32).clip(0, bands - 1).alias("band"))
    result = (
        df_with_band.group_by("band")
        .agg(
            [
                pl.count().alias("count"),
                pl.col(confidence_col).mean().alias("avg_confidence"),
            ]
        )
        .sort("band")
    )
    return result.to_dicts()
