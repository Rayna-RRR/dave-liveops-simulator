from pathlib import Path

import pandas as pd


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_FILE_CANDIDATES = {
    "players.csv": ["players.csv"],
    "event_templates.csv": ["event_templates.csv", "event_templetes.csv"],
    "ab_test_results.csv": ["ab_test_results.csv"],
}


def resolve_data_path(filename):
    """Resolve a project data file, allowing a small typo fallback where useful."""
    for candidate in DATA_FILE_CANDIDATES.get(filename, [filename]):
        candidate_path = DATA_DIR / candidate
        if candidate_path.exists():
            return candidate_path
    raise FileNotFoundError(f"未找到数据文件：{filename}")


def load_csv(filename, required_columns=None):
    """Load a CSV and validate its required columns."""
    data_path = resolve_data_path(filename)
    dataframe = pd.read_csv(data_path)

    if dataframe.empty:
        raise ValueError(f"数据文件为空：{data_path.name}")

    required_columns = required_columns or []
    missing_columns = [column for column in required_columns if column not in dataframe.columns]
    if missing_columns:
        raise ValueError(f"{data_path.name} 缺少字段：{', '.join(missing_columns)}")

    return dataframe


def parse_boolean_series(series):
    """Normalize common boolean representations to True/False."""
    if pd.api.types.is_bool_dtype(series):
        return series.fillna(False)

    normalized = series.astype(str).str.strip().str.lower()
    parsed = normalized.map(
        {
            "true": True,
            "false": False,
            "1": True,
            "0": False,
            "yes": True,
            "no": False,
            "y": True,
            "n": False,
        }
    )
    return parsed.fillna(False).astype(bool)


def load_players_data():
    """Load player data with stable boolean parsing."""
    dataframe = load_csv(
        "players.csv",
        required_columns=[
            "player_id",
            "segment",
            "is_payer",
            "total_payment",
            "avg_session_minutes",
            "churn_risk_score",
        ],
    )
    dataframe["is_payer"] = parse_boolean_series(dataframe["is_payer"])
    return dataframe


def load_event_templates_data():
    """Load event template data with a typo-safe filename fallback."""
    return load_csv(
        "event_templates.csv",
        required_columns=[
            "event_name",
            "target_segment",
            "inflation_risk",
        ],
    )


def load_ab_test_results_data():
    """Load A/B test results with required post-analysis fields."""
    return load_csv(
        "ab_test_results.csv",
        required_columns=[
            "event_name",
            "segment",
            "variant",
            "participation_rate",
            "dau_uplift",
            "d1_retention_uplift",
            "d7_retention_uplift",
            "payment_conversion_uplift",
            "arppu_uplift",
            "reward_cost",
            "inflation_risk",
        ],
    )
