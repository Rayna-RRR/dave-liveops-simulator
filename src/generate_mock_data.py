from pathlib import Path

import numpy as np
import pandas as pd


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PLAYER_COUNT = 10_000
SEED = 42


def scaled_beta(rng, size, alpha, beta, low, high):
    """Sample a bounded non-uniform distribution."""
    return low + rng.beta(alpha, beta, size=size) * (high - low)


def build_segment_players(rng, segment, count):
    """Generate a distinct behavior profile for each player segment."""
    if segment == "new_players":
        days_since_register = rng.integers(1, 15, size=count)
        last_login_days_ago = rng.integers(0, 5, size=count)
        is_payer = rng.random(count) < 0.08
        total_payment = np.where(is_payer, rng.gamma(1.4, 4.0, size=count), 0.0)
        avg_session_minutes = scaled_beta(rng, count, 2.2, 3.4, 8, 32)
        restaurant_level = scaled_beta(rng, count, 1.6, 4.2, 1, 8)
        collection_progress = scaled_beta(rng, count, 1.8, 5.5, 0.02, 0.25)
        vip_preference_score = scaled_beta(rng, count, 2.0, 4.8, 0.08, 0.42)
        event_sensitivity = scaled_beta(rng, count, 2.0, 2.8, 0.35, 0.68)
        churn_risk_score = scaled_beta(rng, count, 2.2, 2.4, 0.18, 0.56)
    elif segment == "returning_players":
        days_since_register = rng.integers(60, 361, size=count)
        last_login_days_ago = rng.integers(1, 12, size=count)
        is_payer = rng.random(count) < 0.24
        total_payment = np.where(is_payer, rng.gamma(2.1, 13.0, size=count), 0.0)
        avg_session_minutes = scaled_beta(rng, count, 2.4, 2.3, 16, 54)
        restaurant_level = scaled_beta(rng, count, 2.5, 2.2, 8, 28)
        collection_progress = scaled_beta(rng, count, 2.5, 2.0, 0.28, 0.82)
        vip_preference_score = scaled_beta(rng, count, 2.2, 2.5, 0.20, 0.72)
        event_sensitivity = scaled_beta(rng, count, 4.5, 1.8, 0.62, 0.98)
        churn_risk_score = scaled_beta(rng, count, 2.0, 2.5, 0.20, 0.58)
    elif segment == "active_non_payers":
        days_since_register = rng.integers(25, 241, size=count)
        last_login_days_ago = rng.integers(0, 4, size=count)
        is_payer = np.zeros(count, dtype=bool)
        total_payment = np.zeros(count)
        avg_session_minutes = scaled_beta(rng, count, 3.4, 1.7, 28, 92)
        restaurant_level = scaled_beta(rng, count, 2.8, 1.8, 10, 36)
        collection_progress = scaled_beta(rng, count, 3.2, 1.8, 0.42, 0.96)
        vip_preference_score = scaled_beta(rng, count, 2.0, 3.4, 0.12, 0.48)
        event_sensitivity = scaled_beta(rng, count, 2.8, 2.0, 0.44, 0.82)
        churn_risk_score = scaled_beta(rng, count, 1.8, 4.2, 0.06, 0.34)
    elif segment == "high_value_payers":
        days_since_register = rng.integers(90, 451, size=count)
        last_login_days_ago = rng.integers(0, 3, size=count)
        is_payer = np.ones(count, dtype=bool)
        total_payment = rng.lognormal(mean=5.1, sigma=0.55, size=count)
        avg_session_minutes = scaled_beta(rng, count, 2.8, 1.9, 30, 88)
        restaurant_level = scaled_beta(rng, count, 3.8, 1.4, 22, 50)
        collection_progress = scaled_beta(rng, count, 4.0, 1.4, 0.68, 1.0)
        vip_preference_score = scaled_beta(rng, count, 5.0, 1.3, 0.74, 0.99)
        event_sensitivity = scaled_beta(rng, count, 2.2, 2.3, 0.38, 0.78)
        churn_risk_score = scaled_beta(rng, count, 1.6, 4.5, 0.03, 0.22)
    else:
        days_since_register = rng.integers(40, 401, size=count)
        last_login_days_ago = rng.integers(8, 46, size=count)
        is_payer = rng.random(count) < 0.12
        total_payment = np.where(is_payer, rng.gamma(1.7, 11.0, size=count), 0.0)
        avg_session_minutes = scaled_beta(rng, count, 1.7, 3.3, 5, 26)
        restaurant_level = scaled_beta(rng, count, 2.0, 2.7, 5, 22)
        collection_progress = scaled_beta(rng, count, 1.9, 2.6, 0.14, 0.66)
        vip_preference_score = scaled_beta(rng, count, 1.8, 3.0, 0.10, 0.56)
        event_sensitivity = scaled_beta(rng, count, 3.2, 2.0, 0.52, 0.92)
        churn_risk_score = scaled_beta(rng, count, 4.5, 1.5, 0.68, 0.99)

    last_login_days_ago = np.minimum(last_login_days_ago, days_since_register)
    register_date = (
        pd.Timestamp.today().normalize() - pd.to_timedelta(days_since_register, unit="D")
    )

    segment_df = pd.DataFrame(
        {
            "register_date": register_date.strftime("%Y-%m-%d"),
            "days_since_register": days_since_register.astype(int),
            "last_login_days_ago": last_login_days_ago.astype(int),
            "segment": segment,
            "is_payer": is_payer,
            "total_payment": np.round(total_payment, 2),
            "avg_session_minutes": np.round(avg_session_minutes, 1),
            "restaurant_level": np.round(restaurant_level).astype(int),
            "collection_progress": np.round(collection_progress, 3),
            "vip_preference_score": np.round(vip_preference_score, 3),
            "event_sensitivity": np.round(event_sensitivity, 3),
            "churn_risk_score": np.round(churn_risk_score, 3),
        }
    )
    return segment_df


def generate_players(seed=SEED):
    """Create a mixed player population with clear segment differences."""
    rng = np.random.default_rng(seed)
    segment_counts = {
        "new_players": 1800,
        "returning_players": 2000,
        "active_non_payers": 2600,
        "high_value_payers": 1200,
        "churn_risk_players": 2400,
    }
    if sum(segment_counts.values()) != PLAYER_COUNT:
        raise ValueError("Segment counts must add up to PLAYER_COUNT.")

    player_frames = [
        build_segment_players(rng, segment, count)
        for segment, count in segment_counts.items()
    ]
    players = pd.concat(player_frames, ignore_index=True)
    players = players.sample(frac=1.0, random_state=seed).reset_index(drop=True)
    players.insert(0, "player_id", [f"P{idx:05d}" for idx in range(1, len(players) + 1)])
    return players


def generate_event_templates():
    """Define a small catalog of event types for the simulator."""
    return pd.DataFrame(
        [
            {
                "event_id": "EVT001",
                "event_name": "tuna_festival",
                "event_type": "activity_driver",
                "target_segment": "active_non_payers",
                "reward_cost_level": "medium",
                "expected_activity_boost": 0.14,
                "expected_retention_boost": 0.03,
                "expected_conversion_boost": 0.01,
                "inflation_risk": 0.31,
            },
            {
                "event_id": "EVT002",
                "event_name": "vip_visit",
                "event_type": "monetization_push",
                "target_segment": "high_value_payers",
                "reward_cost_level": "high",
                "expected_activity_boost": 0.05,
                "expected_retention_boost": 0.02,
                "expected_conversion_boost": 0.06,
                "inflation_risk": 0.26,
            },
            {
                "event_id": "EVT003",
                "event_name": "ingredient_subsidy",
                "event_type": "economy_stimulus",
                "target_segment": "new_players",
                "reward_cost_level": "high",
                "expected_activity_boost": 0.09,
                "expected_retention_boost": 0.03,
                "expected_conversion_boost": 0.02,
                "inflation_risk": 0.67,
            },
            {
                "event_id": "EVT004",
                "event_name": "returner_pack",
                "event_type": "reactivation_offer",
                "target_segment": "churn_risk_players",
                "reward_cost_level": "medium",
                "expected_activity_boost": 0.08,
                "expected_retention_boost": 0.08,
                "expected_conversion_boost": 0.02,
                "inflation_risk": 0.37,
            },
        ]
    )


def generate_ab_test_results(seed=SEED):
    """Build event x segment x variant rows with segment-specific performance."""
    rng = np.random.default_rng(seed + 7)

    fit_map = {
        "tuna_festival": {
            "new_players": 0.72,
            "returning_players": 0.66,
            "active_non_payers": 1.00,
            "high_value_payers": 0.54,
            "churn_risk_players": 0.40,
        },
        "vip_visit": {
            "new_players": 0.20,
            "returning_players": 0.58,
            "active_non_payers": 0.30,
            "high_value_payers": 1.00,
            "churn_risk_players": 0.24,
        },
        "ingredient_subsidy": {
            "new_players": 1.00,
            "returning_players": 0.60,
            "active_non_payers": 0.78,
            "high_value_payers": 0.42,
            "churn_risk_players": 0.36,
        },
        "returner_pack": {
            "new_players": 0.18,
            "returning_players": 0.88,
            "active_non_payers": 0.34,
            "high_value_payers": 0.28,
            "churn_risk_players": 1.00,
        },
    }
    event_profiles = {
        "tuna_festival": {
            "base_participation": 0.36,
            "base_dau": 0.13,
            "base_d1": 0.022,
            "base_d7": 0.014,
            "base_payment": 0.004,
            "base_arppu": 0.018,
            "base_reward_cost": 44,
            "base_inflation": 0.30,
            "variant_boost": 1.05,
            "variant_cost": 1.08,
            "variant_risk": 0.03,
        },
        "vip_visit": {
            "base_participation": 0.20,
            "base_dau": 0.05,
            "base_d1": 0.016,
            "base_d7": 0.012,
            "base_payment": 0.030,
            "base_arppu": 0.095,
            "base_reward_cost": 72,
            "base_inflation": 0.24,
            "variant_boost": 1.07,
            "variant_cost": 1.10,
            "variant_risk": 0.04,
        },
        "ingredient_subsidy": {
            "base_participation": 0.29,
            "base_dau": 0.09,
            "base_d1": 0.026,
            "base_d7": 0.017,
            "base_payment": 0.007,
            "base_arppu": 0.025,
            "base_reward_cost": 66,
            "base_inflation": 0.60,
            "variant_boost": 1.06,
            "variant_cost": 1.14,
            "variant_risk": 0.06,
        },
        "returner_pack": {
            "base_participation": 0.27,
            "base_dau": 0.11,
            "base_d1": 0.060,
            "base_d7": 0.048,
            "base_payment": 0.010,
            "base_arppu": 0.032,
            "base_reward_cost": 58,
            "base_inflation": 0.34,
            "variant_boost": 1.09,
            "variant_cost": 1.12,
            "variant_risk": 0.05,
        },
    }
    segment_sample_base = {
        "new_players": 950,
        "returning_players": 1100,
        "active_non_payers": 1450,
        "high_value_payers": 700,
        "churn_risk_players": 1000,
    }

    rows = []
    test_index = 1
    for event_name, segment_fits in fit_map.items():
        profile = event_profiles[event_name]
        for segment, fit in segment_fits.items():
            fit_scale = 0.42 + 0.78 * fit
            sample_size = int(
                segment_sample_base[segment]
                * (0.85 + 0.35 * fit)
                * rng.uniform(0.92, 1.08)
            )

            metrics = {
                "participation_rate": profile["base_participation"] * fit_scale,
                "dau_uplift": profile["base_dau"] * fit_scale,
                "d1_retention_uplift": profile["base_d1"] * fit_scale,
                "d7_retention_uplift": profile["base_d7"] * fit_scale,
                "payment_conversion_uplift": profile["base_payment"] * fit_scale,
                "arppu_uplift": profile["base_arppu"] * fit_scale,
            }

            for variant in ["A", "B"]:
                variant_multiplier = 1.0
                cost_multiplier = 1.0
                inflation_offset = 0.0
                if variant == "B":
                    variant_multiplier = profile["variant_boost"] * rng.uniform(0.98, 1.03)
                    cost_multiplier = profile["variant_cost"] * rng.uniform(0.98, 1.04)
                    inflation_offset = profile["variant_risk"]

                participation_rate = np.clip(
                    metrics["participation_rate"] * variant_multiplier
                    + rng.normal(0.0, 0.012),
                    0.04,
                    0.82,
                )
                dau_uplift = np.clip(
                    metrics["dau_uplift"] * variant_multiplier + rng.normal(0.0, 0.006),
                    -0.01,
                    0.25,
                )
                d1_retention_uplift = np.clip(
                    metrics["d1_retention_uplift"] * variant_multiplier
                    + rng.normal(0.0, 0.004),
                    -0.005,
                    0.16,
                )
                d7_retention_uplift = np.clip(
                    metrics["d7_retention_uplift"] * variant_multiplier
                    + rng.normal(0.0, 0.004),
                    -0.005,
                    0.12,
                )
                payment_conversion_uplift = np.clip(
                    metrics["payment_conversion_uplift"] * variant_multiplier
                    + rng.normal(0.0, 0.002),
                    -0.01,
                    0.10,
                )
                arppu_uplift = np.clip(
                    metrics["arppu_uplift"] * variant_multiplier + rng.normal(0.0, 0.008),
                    -0.03,
                    0.22,
                )

                reward_cost = (
                    profile["base_reward_cost"]
                    * sample_size
                    * participation_rate
                    / 100.0
                    * cost_multiplier
                )
                inflation_risk = np.clip(
                    profile["base_inflation"]
                    + (1.0 - fit) * 0.06
                    + inflation_offset
                    + rng.normal(0.0, 0.015),
                    0.08,
                    0.95,
                )

                rows.append(
                    {
                        "test_id": f"AB{test_index:03d}",
                        "event_name": event_name,
                        "segment": segment,
                        "variant": variant,
                        "sample_size": sample_size,
                        "participation_rate": round(participation_rate, 3),
                        "dau_uplift": round(dau_uplift, 3),
                        "d1_retention_uplift": round(d1_retention_uplift, 3),
                        "d7_retention_uplift": round(d7_retention_uplift, 3),
                        "payment_conversion_uplift": round(payment_conversion_uplift, 3),
                        "arppu_uplift": round(arppu_uplift, 3),
                        "reward_cost": round(reward_cost, 2),
                        "inflation_risk": round(inflation_risk, 3),
                    }
                )
                test_index += 1

    return pd.DataFrame(rows)


def save_mock_data():
    """Write all generated CSV outputs into the data folder."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    players = generate_players()
    event_templates = generate_event_templates()
    ab_test_results = generate_ab_test_results()

    players.to_csv(DATA_DIR / "players.csv", index=False)
    event_templates.to_csv(DATA_DIR / "event_templates.csv", index=False)
    ab_test_results.to_csv(DATA_DIR / "ab_test_results.csv", index=False)

    print(f"Saved {len(players)} rows to {DATA_DIR / 'players.csv'}")
    print(f"Saved {len(event_templates)} rows to {DATA_DIR / 'event_templates.csv'}")
    print(f"Saved {len(ab_test_results)} rows to {DATA_DIR / 'ab_test_results.csv'}")


if __name__ == "__main__":
    save_mock_data()
