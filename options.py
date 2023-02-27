import math

from scipy.stats import norm

from dataloader import data_loader
from model_data.model_inputs import ModelInputs
from cost_of_capital import wacc


def adjusted_K(data: ModelInputs):
    return data.strike_price_option

def dividend_adjusted_interest_rate(data: ModelInputs):
    return wacc.t_bond_rate(data) - data.annualised_dividend_yield_stock

def adjusted_S(data: ModelInputs, val_per_option):
    """  """
    return(wacc.equity_market_value(data) + val_per_option * data.n_options) / (data.n_shares + data.n_options)

def calc_d_1(data: ModelInputs, val_per_option):
    """  """
    adj_K = adjusted_K(data)
    adj_S = adjusted_S(data, val_per_option)
    variance = data.std_stock**2
    div_adj_int_rate = dividend_adjusted_interest_rate(data)
    expiration = data.option_expiration_in_years
    return (
        (math.log(adj_S/adj_K) + (div_adj_int_rate + variance/2)*expiration) /
        (variance**0.5 * expiration**0.5)
    )

def calc_N_d_1(data, val_per_option):
    """  """
    N_d_1 = calc_d_1(data, val_per_option)
    return norm.cdf(N_d_1)


def calc_d_2(data: ModelInputs, val_per_option):
    """  """
    d_1 = calc_d_1(data, val_per_option)
    variance = data.std_stock**2
    expiration = data.option_expiration_in_years
    return d_1 - variance**0.5 * expiration**0.5

def calc_N_d_2(data: ModelInputs, val_per_option):
    """  """
    N_d_2 = calc_d_2(data, val_per_option)
    return norm.cdf(N_d_2)
    
def value_per_option_formula(data: ModelInputs, adj_S, val_per_option):
    """  """
    dividend = data.annualised_dividend_yield_stock
    expiration = data.option_expiration_in_years
    adj_K = adjusted_K(data)
    N_d_1 = calc_N_d_1(data, val_per_option)
    N_d_2 = calc_N_d_2(data, val_per_option)
    t_bond = data_loader.request_t_bond_rate(data)
    return math.exp((0-dividend) * expiration) * adj_S * N_d_1 - adj_K * math.exp((0-t_bond) * expiration) * N_d_2

def value_per_option(data: ModelInputs):
    """ Iterative process """
    adj_S = data.price_per_share
    val_per_option = 0
    iter_count = 0
    while iter_count < 2000:
        adj_S = adjusted_S(data, val_per_option)
        val_per_option = value_per_option_formula(data, adj_S, val_per_option)
        iter_count += 1
    return val_per_option

def total_options_value_pre_tax(data: ModelInputs):
    return value_per_option(data) * data.n_options

def total_options_value_pre_tax_adjusted_for_vesting(data: ModelInputs):
    total_options_val_pt = total_options_value_pre_tax(data)
    if data.adjust_option_value_for_vesting:
        return total_options_val_pt * data.option_vesting_probability
    return total_options_val_pt

def total_options_value_after_tax(data: ModelInputs):
    total_options_value_pre_tax = total_options_value_pre_tax_adjusted_for_vesting(data)
    if data.adjust_option_value_for_taxes:
        return total_options_value_pre_tax * (1 - data.options_tax_rate)
    else:
        return total_options_value_pre_tax