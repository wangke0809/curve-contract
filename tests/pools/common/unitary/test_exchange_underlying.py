from itertools import combinations_with_replacement

import pytest
from pytest import approx

pytestmark = [pytest.mark.usefixtures("add_initial_liquidity", "approve_bob"), pytest.mark.lending]


@pytest.mark.itercoins("sending", "receiving")
@pytest.mark.parametrize("fee,admin_fee", combinations_with_replacement([0, 0.04, 0.1337, 0.5], 2))
def test_exchange_underlying(
    bob,
    swap,
    underlying_coins,
    sending,
    receiving,
    fee,
    admin_fee,
    underlying_decimals,
    set_fees,
    get_admin_balances,
):
    if fee or admin_fee:
        set_fees(10**10 * fee, 10**10 * admin_fee)

    amount = 10**underlying_decimals[sending]
    underlying_coins[sending]._mint_for_testing(bob, amount, {'from': bob})
    swap.exchange_underlying(sending, receiving, amount, 0, {'from': bob})

    assert underlying_coins[sending].balanceOf(bob) == 0

    received = underlying_coins[receiving].balanceOf(bob)
    assert 0.9999-fee < received / 10**underlying_decimals[receiving] < 1-fee

    expected_admin_fee = 10**underlying_decimals[receiving] * fee * admin_fee
    admin_fees = get_admin_balances()

    if expected_admin_fee:
        assert expected_admin_fee / admin_fees[receiving] == approx(1, rel=1e-3)
    else:
        assert admin_fees[receiving] <= 1


@pytest.mark.itercoins("sending", "receiving")
def test_min_dy_underlying(bob, swap, underlying_coins, sending, receiving, underlying_decimals):
    amount = 10**underlying_decimals[sending]
    underlying_coins[sending]._mint_for_testing(bob, amount, {'from': bob})

    min_dy = swap.get_dy(sending, receiving, amount)
    swap.exchange_underlying(sending, receiving, amount, min_dy - 1, {'from': bob})

    assert abs(underlying_coins[receiving].balanceOf(bob) - min_dy) <= 1
