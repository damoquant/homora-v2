import pytest


@pytest.fixture(scope='module')
def ufactory(a, MockUniswapV2Factory):
    return MockUniswapV2Factory.deploy(a[0], {'from': a[0]})


@pytest.fixture(scope='module')
def urouter(a, ufactory, weth, MockUniswapV2Router02):
    return MockUniswapV2Router02.deploy(ufactory, weth, {'from': a[0]})
