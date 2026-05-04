def calc_buy_cost(price: float, shares: float, cfg: dict) -> float:
    """買入總成本（含手續費 + 滑價）"""
    slip = cfg["slippage_rate"]
    comm_rate = cfg["buy_commission_rate"]
    min_comm = cfg["min_commission"]
    exec_price = price * (1 + slip)
    amount = exec_price * shares
    commission = max(min_comm, amount * comm_rate)
    return amount + commission


def calc_sell_proceeds(price: float, shares: float, cfg: dict) -> float:
    """賣出淨收入（扣手續費 + 滑價 + 證交稅）"""
    slip = cfg["slippage_rate"]
    comm_rate = cfg["sell_commission_rate"]
    tax_rate = cfg["sell_tax_rate"]
    min_comm = cfg["min_commission"]
    exec_price = price * (1 - slip)
    amount = exec_price * shares
    commission = max(min_comm, amount * comm_rate)
    tax = amount * tax_rate
    return amount - commission - tax


def calc_buy_exec_price(price: float, cfg: dict) -> float:
    return price * (1 + cfg["slippage_rate"])


def calc_sell_exec_price(price: float, cfg: dict) -> float:
    return price * (1 - cfg["slippage_rate"])
