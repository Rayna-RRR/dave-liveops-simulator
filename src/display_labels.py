SEGMENT_ORDER = [
    "new_players",
    "returning_players",
    "active_non_payers",
    "high_value_payers",
    "churn_risk_players",
]


SEGMENT_LABELS = {
    "new_players": "新玩家",
    "returning_players": "回流玩家",
    "active_non_payers": "活跃非付费玩家",
    "high_value_payers": "高价值付费玩家",
    "churn_risk_players": "流失风险玩家",
}


EVENT_ORDER = [
    "tuna_festival",
    "vip_visit",
    "ingredient_subsidy",
    "returner_pack",
]


EVENT_LABELS = {
    "tuna_festival": "金枪鱼节",
    "vip_visit": "VIP客人来访",
    "ingredient_subsidy": "食材补贴周",
    "returner_pack": "回流召回礼包",
}


AB_METRIC_LABELS = {
    "participation_rate": "参与率",
    "dau_uplift": "DAU提升",
    "d1_retention_uplift": "D1留存提升",
    "d7_retention_uplift": "D7留存提升",
    "payment_conversion_uplift": "付费转化提升",
    "arppu_uplift": "ARPPU提升",
}


def get_segment_label(segment_key):
    """Return a stable Chinese label for a player segment."""
    return SEGMENT_LABELS.get(segment_key, "未映射分层")


def get_event_label(event_key):
    """Return a stable Chinese label for an event."""
    return EVENT_LABELS.get(event_key, "未映射活动")
