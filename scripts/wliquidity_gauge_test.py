from brownie import accounts, interface, Contract, chain
from brownie import (
    WLiquidityGauge
)


def almostEqual(a, b):
    thresh = 0.01
    return a <= b + thresh * abs(b) and a >= b - thresh * abs(b)


def setup_transfer(asset, fro, to, amt):
    print(f'sending from {fro} {amt} {asset.name()} to {to}')
    asset.transfer(to, amt, {'from': fro})


def main():
    admin = accounts[0]

    alice = accounts[1]
    bob = accounts[2]

    dai = interface.IERC20Ex('0x6B175474E89094C44Da98b954EedeAC495271d0F')
    usdc = interface.IERC20Ex('0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48')
    usdt = interface.IERC20Ex('0xdAC17F958D2ee523a2206206994597C13D831ec7')
    btc = interface.IERC20Ex('0x2260fac5e5542a773aa44fbcfedf7c193bc2c599')
    renbtc = interface.IERC20Ex('0xeb4c2781e4eba804ce9a9803c67d0893436bb27d')
    crv = interface.IERC20Ex('0xD533a949740bb3306d119CC777fa900bA034cd52')

    lp_3pool = interface.IERC20Ex('0x6c3f90f043a72fa612cbac8115ee7e52bde6e490')
    lp_btc = interface.IERC20Ex('0x49849c98ae39fff122806c06791fa73784fb3675')
    pool_3pool = interface.ICurvePool('0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7')
    pool_btc = interface.ICurvePool('0x93054188d876f558f4a66B2EF1d97d16eDf0895B')
    registry = interface.ICurveRegistry(
        '0x7d86446ddb609ed0f5f8684acf30380a356b2b4c')

    gauge = accounts.at(
        '0xbFcF63294aD7105dEa65aA58F8AE5BE2D9d0952A', force=True)
    wgauge = WLiquidityGauge.deploy(
        registry, '0xD533a949740bb3306d119CC777fa900bA034cd52', {'from': admin})

    # set approval
    dai.approve(wgauge, 2**256-1, {'from': alice})
    usdc.approve(wgauge, 2**256-1, {'from': alice})
    usdt.approve(wgauge, 2**256-1, {'from': alice})
    renbtc.approve(wgauge, 2**256-1, {'from': alice})
    btc.approve(wgauge, 2**256-1, {'from': alice})
    lp_3pool.approve(wgauge, 2**256-1, {'from': alice})
    lp_3pool.approve(gauge, 2**256-1, {'from': alice})
    lp_btc.approve(wgauge, 2**256-1, {'from': alice})
    lp_btc.approve(gauge, 2**256-1, {'from': alice})

    dai.approve(wgauge, 2**256-1, {'from': bob})
    usdc.approve(wgauge, 2**256-1, {'from': bob})
    usdt.approve(wgauge, 2**256-1, {'from': bob})
    renbtc.approve(wgauge, 2**256-1, {'from': bob})
    btc.approve(wgauge, 2**256-1, {'from': bob})
    lp_3pool.approve(wgauge, 2**256-1, {'from': bob})
    lp_3pool.approve(gauge, 2**256-1, {'from': bob})
    lp_btc.approve(wgauge, 2**256-1, {'from': bob})
    lp_btc.approve(gauge, 2**256-1, {'from': bob})

    # setup initial funds to alice
    setup_transfer(dai, accounts.at('0xc3d03e4f041fd4cd388c549ee2a29a9e5075882f',
                                    force=True), alice, 10**6 * 10**18)
    setup_transfer(usdc, accounts.at('0xa191e578a6736167326d05c119ce0c90849e84b7',
                                     force=True), alice, 10**6 * 10**6)
    setup_transfer(usdt, accounts.at('0xbe0eb53f46cd790cd13851d5eff43d12404d33e8',
                                     force=True), alice, 10**6 * 10**6)
    setup_transfer(renbtc, accounts.at('0x53463cd0b074e5fdafc55dce7b1c82adf1a43b2e',
                                       force=True), alice, 10**2 * 10**8)
    setup_transfer(btc, accounts.at('0x2bf792ffe8803585f74e06907900c2dc2c29adcb',
                                    force=True), alice, 10**2 * 10**8)

    setup_transfer(dai, accounts.at('0xc3d03e4f041fd4cd388c549ee2a29a9e5075882f',
                                    force=True), bob, 10**6 * 10**18)
    setup_transfer(usdc, accounts.at('0xa191e578a6736167326d05c119ce0c90849e84b7',
                                     force=True), bob, 10**6 * 10**6)
    setup_transfer(usdt, accounts.at('0xbe0eb53f46cd790cd13851d5eff43d12404d33e8',
                                     force=True), bob, 10**6 * 10**6)
    setup_transfer(renbtc, accounts.at('0x53463cd0b074e5fdafc55dce7b1c82adf1a43b2e',
                                       force=True), bob, 10**2 * 10**8)
    setup_transfer(btc, accounts.at('0x2bf792ffe8803585f74e06907900c2dc2c29adcb',
                                    force=True), bob, 10**2 * 10**8)
    # steal some LP from the staking pool
    setup_transfer(lp_3pool, accounts.at(
        '0x8038c01a0390a8c547446a0b2c18fc9aefecc10c', force=True), alice, 10**6 * 10**18)
    setup_transfer(lp_btc, accounts.at(
        '0x9aa8f427a17d6b0d91b6262989edc7d45d6aedf8', force=True), alice, 100 * 10**18)

    setup_transfer(lp_3pool, accounts.at(
        '0x8038c01a0390a8c547446a0b2c18fc9aefecc10c', force=True), bob, 10**6 * 10**18)
    setup_transfer(lp_btc, accounts.at(
        '0x9aa8f427a17d6b0d91b6262989edc7d45d6aedf8', force=True), bob, 100 * 10**18)

    # register gauges
    wgauge.registerGauge(0, 0, {'from': admin})
    wgauge.registerGauge(9, 0, {'from': admin})

    ######################################################################
    # Check encoding and decoding ids
    print('######################################################################')
    print('Case 1.')

    # check 3pool
    pid = 0
    gid = 0
    crvPerShare = 210
    encoded_id = wgauge.encodeId(pid, gid, crvPerShare)
    print('encoded id', encoded_id)
    assert (encoded_id >> 248) == pid
    assert (encoded_id >> 240) & ((1 << 8) - 1) == gid
    assert (encoded_id & ((1 << 240) - 1)) == crvPerShare

    d_pid, d_gid, d_crvPerShare = wgauge.decodeId(encoded_id)
    print('decoded pid', d_pid)
    print('decoded gid', d_gid)
    print('decoded crvPerShare', d_crvPerShare)
    assert d_pid == pid
    assert d_gid == gid
    assert d_crvPerShare == crvPerShare

    # check renbtc pool
    pid = 9
    gid = 0
    crvPerShare = 100
    encoded_id = wgauge.encodeId(pid, gid, crvPerShare)
    print('encoded id', encoded_id)
    assert (encoded_id >> 248) == pid
    assert (encoded_id >> 240) & ((1 << 8) - 1) == gid
    assert (encoded_id & ((1 << 240) - 1)) == crvPerShare

    d_pid, d_gid, d_crvPerShare = wgauge.decodeId(encoded_id)
    print('decoded pid', d_pid)
    print('decoded gid', d_gid)
    print('decoded crvPerShare', d_crvPerShare)
    assert d_pid == pid
    assert d_gid == gid
    assert d_crvPerShare == crvPerShare

    ######################################################################
    # check getUnderlying

    pid = 0
    gid = 0
    crvPerShare = 200
    id_num = wgauge.encodeId(pid, gid, crvPerShare)
    lpToken = wgauge.getUnderlying(id_num)
    print('lpToken', lpToken)
    assert lpToken == lp_3pool

    pid = 9
    gid = 0
    crvPerShare = 100
    id_num = wgauge.encodeId(pid, gid, crvPerShare)
    lpToken = wgauge.getUnderlying(id_num)
    print('lpToken', lpToken)
    assert lpToken == lp_btc

    ######################################################################
    # check mint & burn
    print('######################################################################')
    print('Case 2.')

    pid = 0
    gid = 0
    amt = 10**18

    print('alice lp 3pool balance', lp_3pool.balanceOf(alice))

    # mint
    tx = wgauge.mint(pid, gid, amt, {'from': alice})
    encoded_id = tx.return_value
    print('tx status', tx.status)
    print('encoded id', encoded_id)
    gauge, prevAccCrvPerShare = wgauge.gauges(pid, gid)
    print('gauge', gauge)
    print('prevAccCrvPerShare', prevAccCrvPerShare)
    print('alice wlp_3pool balance', wgauge.balanceOf(alice, encoded_id))
    assert tx.status == 1
    assert wgauge.balanceOf(alice, encoded_id) == amt

    chain.sleep(20000)

    # burn exact
    prevCrvBalance = crv.balanceOf(alice)
    tx = wgauge.burn(encoded_id, amt, {'from': alice})

    print('tx status', tx.status)
    print('alice wlp_3pool balance', wgauge.balanceOf(alice, encoded_id))

    print('alice crv balance', crv.balanceOf(alice))
    receivedCrv = crv.balanceOf(alice) - prevCrvBalance

    assert tx.status == 1
    assert tx.return_value == pid
    assert wgauge.balanceOf(alice, encoded_id) == 0  # remove all

    # check reward same as staking directly
    prevCrv = crv.balanceOf(alice)
    print('alice lp_3pool balance', interface.IERC20Ex(lp_3pool).balanceOf(alice))
    gauge, _ = wgauge.gauges(pid, gid)
    tx = interface.ILiquidityGauge(gauge).deposit(amt, {'from': alice})
    chain.sleep(20000)
    minter = interface.ILiquidityGaugeMinter(interface.ILiquidityGauge(gauge).minter())
    print('minter', minter)
    tx = minter.mint(gauge, {'from': alice})
    print('tx status', tx.status)
    tx = interface.ILiquidityGauge(gauge).withdraw(amt, {'from': alice})
    receivedCrvFromGauge = crv.balanceOf(alice) - prevCrv
    print('receivedCrvFromGauge', receivedCrvFromGauge)
    assert almostEqual(receivedCrv, receivedCrvFromGauge)

    ######################################################################
    # check mint & burn max_int

    print('######################################################################')
    print('Case 3.')

    pid = 0
    gid = 0
    amt = 10**18

    print('alice lp 3pool balance', lp_3pool.balanceOf(alice))

    # mint alice
    tx = wgauge.mint(pid, gid, amt, {'from': alice})
    encoded_id = tx.return_value
    print('tx status', tx.status)
    print('encoded id', encoded_id)
    gauge, prevAccCrvPerShare = wgauge.gauges(pid, gid)
    print('gauge', gauge)
    print('prevAccCrvPerShare', prevAccCrvPerShare)
    print('alice wlp_3pool balance', wgauge.balanceOf(alice, encoded_id))
    assert tx.status == 1
    assert wgauge.balanceOf(alice, encoded_id) == amt

    # mint bob
    prevCrvBob = crv.balanceOf(bob)
    print('bob lp_3pool balance', interface.IERC20Ex(lp_3pool).balanceOf(bob))
    gauge, _ = wgauge.gauges(pid, gid)
    tx = interface.ILiquidityGauge(gauge).deposit(amt, {'from': bob})

    chain.sleep(10000)

    # burn max_int alice
    prevCrvBalance = crv.balanceOf(alice)
    tx = wgauge.burn(encoded_id, 2**256-1, {'from': alice})

    print('tx status', tx.status)
    print('alice wlp_3pool balance', wgauge.balanceOf(alice, encoded_id))

    print('alice crv balance', crv.balanceOf(alice))
    receivedCrv = crv.balanceOf(alice) - prevCrvBalance

    assert tx.status == 1
    assert tx.return_value == pid
    assert wgauge.balanceOf(alice, encoded_id) == 0  # remove all

    # burn all bob
    minter = interface.ILiquidityGaugeMinter(interface.ILiquidityGauge(gauge).minter())
    print('minter', minter)
    tx = minter.mint(gauge, {'from': bob})
    print('tx status', tx.status)
    tx = interface.ILiquidityGauge(gauge).withdraw(amt, {'from': bob})
    receivedCrvFromGauge = crv.balanceOf(bob) - prevCrvBob

    print('receivedCrv', receivedCrv)
    print('receivedCrvFromGauge', receivedCrvFromGauge)
    assert almostEqual(receivedCrv, receivedCrvFromGauge)

    ######################################################################
    # check mint & burn (try more than available--revert, half, then remaining)

    print('######################################################################')
    print('Case 4.')

    pid = 0
    gid = 0
    amt = 10**18

    print('alice lp 3pool balance', lp_3pool.balanceOf(alice))

    # mint alice
    tx = wgauge.mint(pid, gid, amt, {'from': alice})
    encoded_id = tx.return_value
    print('tx status', tx.status)
    print('encoded id', encoded_id)
    gauge, prevAccCrvPerShare = wgauge.gauges(pid, gid)
    print('gauge', gauge)
    print('prevAccCrvPerShare', prevAccCrvPerShare)
    print('alice wlp_3pool balance', wgauge.balanceOf(alice, encoded_id))
    assert tx.status == 1
    assert wgauge.balanceOf(alice, encoded_id) == amt

    # mint bob
    prevCrvBob = crv.balanceOf(bob)
    print('bob lp_3pool balance', interface.IERC20Ex(lp_3pool).balanceOf(bob))
    gauge, _ = wgauge.gauges(pid, gid)
    tx = interface.ILiquidityGauge(gauge).deposit(amt, {'from': bob})

    chain.sleep(10000)

    # burn too much (expected failed)
    prevCrvBalance = crv.balanceOf(alice)
    try:
        tx = wgauge.burn(encoded_id, amt + 1, {'from': alice})
        assert tx.status == 0
    except:
        pass

    print('alice wlpusdt balance', wgauge.balanceOf(alice, encoded_id))
    print('alice crv balance', crv.balanceOf(alice))
    assert prevCrvBalance == crv.balanceOf(alice)
    assert wgauge.balanceOf(alice, encoded_id) == amt

    # burn half alice
    prevCrvBalance = crv.balanceOf(alice)
    tx = wgauge.burn(encoded_id, amt // 2, {'from': alice})

    print('tx status', tx.status)
    print('alice wlp_3pool balance', wgauge.balanceOf(alice, encoded_id))
    print('amt - amt//2', amt - amt//2)

    print('alice crv balance', crv.balanceOf(alice))

    assert tx.status == 1
    assert tx.return_value == pid
    assert wgauge.balanceOf(alice, encoded_id) == amt - amt // 2  # remove half

    # burn half bob
    minter = interface.ILiquidityGaugeMinter(interface.ILiquidityGauge(gauge).minter())
    print('minter', minter)
    tx = minter.mint(gauge, {'from': bob})
    print('tx status', tx.status)
    tx = interface.ILiquidityGauge(gauge).withdraw(amt // 2, {'from': bob})

    chain.sleep(10000)

    # burn remaining alice
    tx = wgauge.burn(encoded_id, 2**256-1, {'from': alice})

    print('tx status', tx.status)
    print('alice wlp_3pool balance', wgauge.balanceOf(alice, encoded_id))

    print('alice crv balance', crv.balanceOf(alice))
    receivedCrv = crv.balanceOf(alice) - prevCrvBalance

    assert tx.status == 1
    assert tx.return_value == pid

    # burn remaining bob
    tx = minter.mint(gauge, {'from': bob})
    print('tx status', tx.status)
    tx = interface.ILiquidityGauge(gauge).withdraw(amt - amt // 2, {'from': bob})
    receivedCrvFromGauge = crv.balanceOf(bob) - prevCrvBob

    print('receivedCrv alice', receivedCrv)
    print('receivedCrvFromGauge bob', receivedCrvFromGauge)

    assert wgauge.balanceOf(alice, encoded_id) == 0  # remove all

    # check reward same as staking directly
    assert almostEqual(receivedCrv, receivedCrvFromGauge)
