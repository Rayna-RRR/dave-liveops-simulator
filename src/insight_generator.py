def calculate_variant_score(result_row):
    """Score a variant with a simple uplift-minus-risk rule."""
    activation_score = result_row["participation_rate"] + result_row["dau_uplift"]
    retention_score = result_row["d1_retention_uplift"] + result_row["d7_retention_uplift"]
    monetization_score = (
        result_row["payment_conversion_uplift"] * 1.2 + result_row["arppu_uplift"]
    )
    risk_penalty = result_row["inflation_risk"] * 0.10 + min(
        result_row["reward_cost"] / 3000.0, 0.12
    )
    return activation_score + retention_score + monetization_score - risk_penalty


def select_best_variant(variant_df):
    """Pick the stronger A/B row for the current filter."""
    scored_df = variant_df.copy()
    scored_df["overall_score"] = scored_df.apply(calculate_variant_score, axis=1)
    return scored_df.sort_values("overall_score", ascending=False).iloc[0]


def infer_primary_goal(result_row):
    """Infer whether the result is mainly activation, retention, or monetization driven."""
    goal_scores = {
        "促活": result_row["participation_rate"] + result_row["dau_uplift"],
        "留存": result_row["d1_retention_uplift"] + result_row["d7_retention_uplift"],
        "拉收": result_row["payment_conversion_uplift"] + result_row["arppu_uplift"],
    }
    return max(goal_scores, key=goal_scores.get)


def generate_postmortem_insights(result_row, segment_label):
    """Generate deterministic postmortem conclusions and actions."""
    conclusions = []
    actions = []

    primary_goal = infer_primary_goal(result_row)
    if primary_goal == "促活":
        conclusions.append("该方案更偏向促活，对活跃度提升更明显。")
    elif primary_goal == "留存":
        conclusions.append("该方案更偏向留存，短中期留存改善相对更突出。")
    else:
        conclusions.append("该方案更偏向拉收，对付费转化与付费深度更有帮助。")

    if result_row["d7_retention_uplift"] >= 0.04:
        conclusions.append("该方案对D7留存改善明显，具备一定长线运营价值。")
    elif result_row["d7_retention_uplift"] >= 0.015:
        conclusions.append("该方案对D7留存有一定改善，但长线效果仍需继续观察。")
    else:
        conclusions.append("该方案对D7留存改善有限，长线效果一般。")

    if (
        result_row["payment_conversion_uplift"] >= 0.02
        or result_row["arppu_uplift"] >= 0.06
    ):
        conclusions.append(f"该方案对付费转化有一定拉动，更适合{segment_label}。")
    else:
        conclusions.append("该方案对变现指标拉动相对有限，更适合作为行为刺激方案。")

    if result_row["reward_cost"] >= 220 or result_row["inflation_risk"] >= 0.60:
        conclusions.append("奖励投放成本偏高，建议搭配资源回收机制控制通胀风险。")
    elif result_row["reward_cost"] <= 110 and result_row["inflation_risk"] < 0.35:
        conclusions.append("该方案资源消耗相对可控，适合做更高频的小规模验证。")
    else:
        conclusions.append("该方案成本与风险处于中位区间，适合阶段性投放后再观察。")

    if result_row["participation_rate"] >= 0.30 and result_row["d7_retention_uplift"] < 0.02:
        conclusions.append("该方案更适合用于阶段性召回，而非长期常驻活动。")
    elif result_row["d1_retention_uplift"] >= 0.03 and result_row["d7_retention_uplift"] >= 0.03:
        conclusions.append("该方案在短期与中期留存上表现较均衡，适合纳入常规活动池。")

    if result_row["inflation_risk"] >= 0.60:
        actions.append("建议缩减高价值奖励投放比例，并增加兑换门槛或回收链路。")
    else:
        actions.append("建议先按当前节奏小范围复用，再持续追踪资源消耗表现。")

    if primary_goal == "促活":
        actions.append("建议优先投放给近期活跃下滑人群，强化回流触达与短周期曝光。")
    elif primary_goal == "留存":
        actions.append("建议与连续登录、阶段任务或成长目标联动，放大留存收益。")
    else:
        actions.append("建议优先绑定高价值礼包或限时商店，提升转化效率与付费深度。")

    if result_row["d7_retention_uplift"] < 0.015:
        actions.append("建议下一轮补充更强的中后期目标设计，避免活动热度快速回落。")
    elif result_row["payment_conversion_uplift"] < 0.01 and primary_goal != "拉收":
        actions.append("建议将变现点后置，先保证行为参与，再测试更轻量的付费触发。")

    return {
        "primary_goal": primary_goal,
        "conclusions": conclusions[:5],
        "actions": actions[:3],
    }
