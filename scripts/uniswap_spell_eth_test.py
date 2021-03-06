from brownie import accounts, interface, Contract
from brownie import (
    HomoraBank, ProxyOracle, SimpleOracle, UniswapV2Oracle, UniswapV2SpellV1, WERC20
)


def almostEqual(a, b):
    thresh = 0.01
    return a <= b + thresh * abs(b) and a >= b - thresh * abs(b)


def setup_bank_hack(homora):
    donator = accounts[5]
    fake = accounts.at(homora.address, force=True)
    controller = interface.IComptroller(
        '0x3d5BC3c8d13dcB8bF317092d84783c2697AE9258')
    creth = interface.ICEtherEx('0xD06527D5e56A3495252A528C4987003b712860eE')
    creth.mint({'value': '90 ether', 'from': donator})
    creth.transfer(fake, creth.balanceOf(donator), {'from': donator})
    controller.enterMarkets([creth], {'from': fake})


def setup_transfer(asset, fro, to, amt):
    print(f'sending from {fro} {amt} {asset.name()} to {to}')
    asset.transfer(to, amt, {'from': fro})


def main():
    admin = accounts[0]

    alice = accounts[1]
    usdt = interface.IERC20Ex('0xdAC17F958D2ee523a2206206994597C13D831ec7')
    weth = interface.IERC20Ex('0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2')

    lp = interface.IERC20Ex('0x0d4a11d5EEaaC28EC3F61d100daF4d40471f1852')
    crusdt = interface.ICErc20('0x797AAB1ce7c01eB727ab980762bA88e7133d2157')
    router = interface.IUniswapV2Router02(
        '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D')

    werc20 = WERC20.deploy({'from': admin})

    simple_oracle = SimpleOracle.deploy({'from': admin})
    simple_oracle.setETHPx([usdt, weth], [
                           9011535487953795006625883219171279625142296, 2**112])

    uniswap_oracle = UniswapV2Oracle.deploy(simple_oracle, {'from': admin})
    oracle = ProxyOracle.deploy({'from': admin})
    oracle.setWhitelistERC1155([werc20], True, {'from': admin})
    oracle.setOracles(
        [
            '0xdAC17F958D2ee523a2206206994597C13D831ec7',  # USDT
            '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',  # WETH
            '0x0d4a11d5EEaaC28EC3F61d100daF4d40471f1852',  # USDT-WETH
        ],
        [
            [simple_oracle, 10000, 10000, 10000],
            [simple_oracle, 10000, 10000, 10000],
            [uniswap_oracle, 10000, 10000, 10000],
        ],
        {'from': admin},
    )

    homora = HomoraBank.deploy({'from': admin})
    homora.initialize(oracle, 1000, {'from': admin})  # 10% fee
    setup_bank_hack(homora)
    homora.addBank(usdt, crusdt, {'from': admin})

    # setup initial funds 10^5 USDT + 10^4 WETH to alice
    setup_transfer(usdt, accounts.at(
        '0xbe0eb53f46cd790cd13851d5eff43d12404d33e8', force=True), alice, 10**5 * 10**6)
    setup_transfer(weth, accounts.at(
        '0x397ff1542f962076d0bfe58ea045ffa2d347aca0', force=True), alice, 10**4 * 10**18)

    # setup initial funds 10^6 USDT + 10^5 WETH to homora bank
    setup_transfer(usdt, accounts.at(
        '0xbe0eb53f46cd790cd13851d5eff43d12404d33e8', force=True), homora, 10**6 * 10**6)
    setup_transfer(weth, accounts.at(
        '0x397ff1542f962076d0bfe58ea045ffa2d347aca0', force=True), homora, 10**4 * 10**18)

    # check alice's funds
    print(f'Alice usdt balance {usdt.balanceOf(alice)}')
    print(f'Alice weth balance {weth.balanceOf(alice)}')

    # Steal some LP from the staking pool
    lp.transfer(alice, 1*10**17, {'from': accounts.at(
        '0x767ecb395def19ab8d1b2fcc89b3ddfbed28fd6b', force=True)})
    lp.transfer(homora, 2*10**17, {'from': accounts.at(
        '0x767ecb395def19ab8d1b2fcc89b3ddfbed28fd6b', force=True)})

    # set approval
    usdt.approve(homora, 2**256-1, {'from': alice})
    usdt.approve(crusdt, 2**256-1, {'from': alice})
    weth.approve(homora, 2**256-1, {'from': alice})
    lp.approve(homora, 2**256-1, {'from': alice})

    uniswap_spell = UniswapV2SpellV1.deploy(
        homora, werc20, router, {'from': admin})
    # first time call to reduce gas
    uniswap_spell.getPair(weth, usdt, {'from': admin})

    #####################################################################################
    print('=========================================================================')
    print('Case 1.')

    prevABal = usdt.balanceOf(alice)
    prevBBal = weth.balanceOf(alice)
    prevETHBal = alice.balance()
    prevLPBal = lp.balanceOf(alice)
    prevLPBal_bank = lp.balanceOf(homora)
    prevLPBal_werc20 = lp.balanceOf(werc20)

    if interface.IUniswapV2Pair(lp).token0() == usdt:
        prevARes, prevBRes, _ = interface.IUniswapV2Pair(lp).getReserves()
    else:
        prevBRes, prevARes, _ = interface.IUniswapV2Pair(lp).getReserves()

    usdt_amt = 400 * 10**6
    weth_amt = 10**18
    eth_amt = 10**18
    lp_amt = 1 * 10**16
    borrow_usdt_amt = 1000 * 10**6
    borrow_weth_amt = 0

    tx = homora.execute(
        0,
        uniswap_spell,
        uniswap_spell.addLiquidity.encode_input(
            usdt,  # token 0
            weth,  # token 1
            [usdt_amt,  # supply USDT
             weth_amt,   # supply WETH
             lp_amt,  # supply LP
             borrow_usdt_amt,  # borrow USDT
             borrow_weth_amt,  # borrow WETH
             0,  # borrow LP tokens
             0,  # min USDT
             0],  # min WETH
        ),
        {'from': alice, 'value': eth_amt}
    )

    position_id = tx.return_value
    print('position_id', position_id)

    curABal = usdt.balanceOf(alice)
    curBBal = weth.balanceOf(alice)
    curETHBal = alice.balance()
    curLPBal = lp.balanceOf(alice)
    curLPBal_bank = lp.balanceOf(homora)
    curLPBal_werc20 = lp.balanceOf(werc20)

    if interface.IUniswapV2Pair(lp).token0() == usdt:
        curARes, curBRes, _ = interface.IUniswapV2Pair(lp).getReserves()
    else:
        curBRes, curARes, _ = interface.IUniswapV2Pair(lp).getReserves()

    print('spell lp balance', lp.balanceOf(uniswap_spell))
    print('Alice delta A balance', curABal - prevABal)
    print('Alice delta B balance', curBBal - prevBBal)
    print('add liquidity gas', tx.gas_used)
    print('bank lp balance', curLPBal_bank)

    _, _, _, totalDebt, totalShare = homora.getBankInfo(usdt)
    print('bank usdt totalDebt', totalDebt)
    print('bank usdt totalShare', totalShare)

    print('bank prev LP balance', prevLPBal_bank)
    print('bank cur LP balance', curLPBal_bank)

    print('werc20 prev LP balance', prevLPBal_werc20)
    print('werc20 cur LP balance', curLPBal_werc20)

    # alice
    assert almostEqual(curABal - prevABal, -usdt_amt), 'incorrect USDT amt'
    assert almostEqual(curBBal - prevBBal, -weth_amt), 'incorrect WETH amt'
    assert almostEqual(curETHBal - prevETHBal, -eth_amt), 'incorrect ETH amt'
    assert curLPBal - prevLPBal == -lp_amt, 'incorrect LP amt'

    # spell
    assert usdt.balanceOf(uniswap_spell) == 0, 'non-zero spell USDT balance'
    assert weth.balanceOf(uniswap_spell) == 0, 'non-zero spell WETH balance'
    assert uniswap_spell.balance() == 0, 'non-zero spell ETH balance'
    assert lp.balanceOf(uniswap_spell) == 0, 'non-zero spell LP balance'
    assert totalDebt == borrow_usdt_amt

    # check balance and pool reserves
    assert curABal - prevABal - borrow_usdt_amt == - \
        (curARes - prevARes), 'not all USDT tokens go to LP pool'
    assert curBBal - prevBBal - borrow_weth_amt - eth_amt == - \
        (curBRes - prevBRes), 'not all WETH tokens go to LP pool'

    #####################################################################################
    print('=========================================================================')
    print('Case 2.')

    # remove liquidity from the same position
    prevABal = usdt.balanceOf(alice)
    prevBBal = weth.balanceOf(alice)
    prevLPBal = lp.balanceOf(alice)
    prevLPBal_bank = lp.balanceOf(homora)
    prevLPBal_werc20 = lp.balanceOf(werc20)
    prevETHBal = alice.balance()

    if interface.IUniswapV2Pair(lp).token0() == usdt:
        prevARes, prevBRes, _ = interface.IUniswapV2Pair(lp).getReserves()
    else:
        prevBRes, prevARes, _ = interface.IUniswapV2Pair(lp).getReserves()

    lp_take_amt = 1 * 10**16
    lp_want = 1 * 10**15
    usdt_repay = 2**256-1  # max
    weth_repay = 0

    real_usdt_repay = homora.borrowBalanceStored(position_id, usdt)

    tx = homora.execute(
        position_id,
        uniswap_spell,
        uniswap_spell.removeLiquidity.encode_input(
            usdt,  # token 0
            weth,  # token 1
            [lp_take_amt,  # take out LP tokens
             lp_want,   # withdraw LP tokens to wallet
             usdt_repay,  # repay USDT
             weth_repay,   # repay WETH
             0,   # repay LP
             0,   # min USDT
             0],  # min WETH
        ),
        {'from': alice}
    )

    curABal = usdt.balanceOf(alice)
    curBBal = weth.balanceOf(alice)
    curLPBal = lp.balanceOf(alice)
    curLPBal_bank = lp.balanceOf(homora)
    curLPBal_werc20 = lp.balanceOf(werc20)
    curETHBal = alice.balance()

    if interface.IUniswapV2Pair(lp).token0() == usdt:
        curARes, curBRes, _ = interface.IUniswapV2Pair(lp).getReserves()
    else:
        curBRes, curARes, _ = interface.IUniswapV2Pair(lp).getReserves()

    print('spell lp balance', lp.balanceOf(uniswap_spell))
    print('spell usdt balance', usdt.balanceOf(uniswap_spell))
    print('spell weth balance', weth.balanceOf(uniswap_spell))
    print('Alice delta A balance', curABal - prevABal)
    print('Alice delta B balance', curBBal - prevBBal)
    print('Alice delta LP balance', curLPBal - prevLPBal)
    print('remove liquidity gas', tx.gas_used)
    print('bank delta lp balance', curLPBal_bank - prevLPBal_bank)
    print('bank total lp balance', curLPBal_bank)

    _, _, _, totalDebt, totalShare = homora.getBankInfo(usdt)
    print('bank usdt totalDebt', totalDebt)
    print('bank usdt totalShare', totalShare)

    print('LP want', lp_want)

    print('bank delta LP amount', curLPBal_bank - prevLPBal_bank)
    print('LP take amount', lp_take_amt)

    print('prev werc20 LP balance', prevLPBal_werc20)
    print('cur werc20 LP balance', curLPBal_werc20)

    # alice
    assert almostEqual(curBBal - prevBBal, 0), 'incorrect WETH amt'
    assert almostEqual(curLPBal - prevLPBal, lp_want), 'incorrect LP amt'

    # werc20
    assert almostEqual(curLPBal_werc20 - prevLPBal_werc20, -
                       lp_take_amt), 'incorrect werc20 LP amt'

    # spell
    assert usdt.balanceOf(uniswap_spell) == 0, 'non-zero spell USDT balance'
    assert weth.balanceOf(uniswap_spell) == 0, 'non-zero spell WETH balance'
    assert uniswap_spell.balance() == 0, 'non-zero spell ETH balance'
    assert lp.balanceOf(uniswap_spell) == 0, 'non-zero spell LP balance'

    # check balance and pool reserves
    assert almostEqual(curABal - prevABal + real_usdt_repay, -
                       (curARes - prevARes)), 'inconsistent USDT from withdraw'
    assert almostEqual(curBBal - prevBBal,
                       0), 'inconsistent WETH from withdraw'
    assert almostEqual(curETHBal - prevETHBal + weth_repay, -
                       (curBRes - prevBRes)), 'inconsistent ETH from withdraw'

    return tx
