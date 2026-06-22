import billing_policy


def test_grandfathers_loyal_customers_onto_the_pro_cap():
    result = billing_policy.quoteSubscription(
        account={'plan': 'legacy', 'yearsActive': 7},
        usage={'projects': 18, 'seats': 4},
    )
    assert result == {'tier': 'pro', 'monthlyUsd': 49, 'requiresReview': False}


def test_flags_enterprise_usage_before_charging():
    result = billing_policy.quoteSubscription(
        account={'plan': 'team', 'yearsActive': 1},
        usage={'projects': 91, 'seats': 42},
    )
    assert result == {
        'tier': 'enterprise',
        'monthlyUsd': None,
        'requiresReview': True,
        'reason': 'seat_count',
    }
