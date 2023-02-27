import numpy as np
import pandas as pd

import adjustments.r_and_d as rd
import adjustments.operating_leases as opl
import options as opt
from model_data.model_inputs import ModelInputs
from cost_of_capital import wacc

######################################## DCF Support Functions ########################################

#################### Convergence Functions ####################

def converge_rates_between_period_ends(prior_stage_rate, target_rate, periods_in_stage) -> np.array:
    rates = np.linspace(prior_stage_rate, target_rate, periods_in_stage + 1)
    return rates[1:]
    
def forecast_rates_in_stage(n_periods, prior_stage_rate, target_rate, method) -> np.array:
    if method == "constant":
        return np.full(n_periods, target_rate) 
    elif method == "converge":
        return converge_rates_between_period_ends(prior_stage_rate, target_rate, n_periods)

def converge_rates_in_stage(start_rate, target_rate, n_periods) -> np.array:
    return np.linspace(start_rate, target_rate, n_periods)

#################### Valuation Drivers ####################

# Revenue Growth

def perpetual_growth_rate(data: ModelInputs) -> float:
    if data.is_perpetual_growth_rate_custom:
        return data.custom_perpetual_growth_rate
    else:
        if data.is_riskfree_rate_in_perpetuity_custom:
            return data.custom_riskfree_rate_in_perpetuity
        else:
            return wacc.riskfree_rate(data)

def forecast_revenue_growth_rates(data: ModelInputs) -> np.array:
    revenue_growth_stage_1 = np.array([data.growth_rate_stage_1] * data.stage_1_periods)
    revenue_growth_stage_2 = forecast_rates_in_stage(data.stage_2_periods, data.growth_rate_stage_1, 
                                                    data.growth_rate_target_stage_2, data.growth_method_stage_2)
    growth_rate_target_stage_3 = perpetual_growth_rate(data)
    revenue_growth_stage_3 = forecast_rates_in_stage(data.stage_3_periods, data.growth_rate_target_stage_2,
                                                    growth_rate_target_stage_3, data.growth_method_stage_3)
    revenue_growth_rates = np.concatenate((revenue_growth_stage_1, revenue_growth_stage_2, revenue_growth_stage_3))
    return revenue_growth_rates

# Operating Margin
def operating_margin(data: ModelInputs) -> np.array:
    converging_margins = np.linspace(data.operating_margin_year_one, data.operating_margin_target, data.operating_margin_convergence_year)
    n_periods_constant_margin = data.model_periods - data.operating_margin_convergence_year
    constant_margins = np.full(n_periods_constant_margin, data.operating_margin_target)
    operating_margins = np.concatenate((converging_margins, constant_margins))
    return operating_margins

# Reinvestment: Sales to Capital
def sales_to_capital_ratios(data: ModelInputs) -> np.array:
    sales_to_capital_stage_1 = np.array([data.sales_to_capital_stage_1] * data.stage_1_periods)
    sales_to_capital_stage_2 = forecast_rates_in_stage(data.stage_2_periods, data.sales_to_capital_stage_1,
                                    data.sales_to_capital_target_stage_2, data.sales_to_capital_method_stage_2)
    sales_to_capital_stage_3 = forecast_rates_in_stage(data.stage_3_periods, data.sales_to_capital_target_stage_2,
                                    data.sales_to_capital_target_stage_3, data.sales_to_capital_method_stage_3)
    return np.concatenate((sales_to_capital_stage_1, sales_to_capital_stage_2, sales_to_capital_stage_3))

def perpetual_risk_free_rate(data: ModelInputs) -> float:
    if data.is_riskfree_rate_in_perpetuity_custom:
        perp_rfr = data.custom_riskfree_rate_in_perpetuity
    else:
        perp_rfr = wacc.riskfree_rate(data)
    return perp_rfr

#################### Forecasting DCF Line Items ####################

def effective_tax_rate_base_year(data: ModelInputs) -> float:
    eff_tax_rate = data.paid_in_taxes / data.earnings_before_tax
    if data.is_tax_rate_base_year_custom:
        return data.custom_tax_rate
    elif eff_tax_rate > 1 or eff_tax_rate < 0:
        return data.marginal_tax_rate
    return eff_tax_rate

def forecast_tax_rates(data: ModelInputs) -> np.array:
    """  """
    eff_tax_r_base_year = effective_tax_rate_base_year(data)
    tax_rate_stage_1 = np.array([eff_tax_r_base_year] * data.stage_1_periods)
    tax_rates_stage_2 = np.array([eff_tax_r_base_year] * data.stage_2_periods)
    perpetual_tax_rate = eff_tax_r_base_year if data.tax_rate_in_perpetuity == "effective" else data.marginal_tax_rate 
    tax_rates_stage_3 = forecast_rates_in_stage(data.stage_3_periods, eff_tax_r_base_year, perpetual_tax_rate, 'converge')   
    return np.concatenate((tax_rate_stage_1, tax_rates_stage_2, tax_rates_stage_3))

def cost_of_capital_array(data: ModelInputs) -> np.array:
    wacc_stage_1 = wacc.cost_of_capital(data)
    cost_of_capital_stage_1 = np.array([wacc_stage_1] * data.stage_1_periods)
    cost_of_capital_stage_2 = forecast_rates_in_stage(data.stage_2_periods, wacc_stage_1,
                                    data.wacc_target_stage_2, data.wacc_method_stage_2)
    
    if data.is_wacc_target_stage_3_custom:
        wacc_target_stage_3 = data.wacc_target_stage_3_custom
    else:
        wacc_target_stage_3 = wacc.riskfree_rate(data) + data.mature_market_company_wacc_vs_rfr_spread
    
    cost_of_capital_stage_3 = forecast_rates_in_stage(data.stage_3_periods, data.wacc_target_stage_2,
                                    wacc_target_stage_3, data.wacc_method_stage_3)
    return np.concatenate((cost_of_capital_stage_1, cost_of_capital_stage_2, cost_of_capital_stage_3))

def adjusted_invested_capital(data: ModelInputs) -> float:
    value_research_asset = rd.value_research_asset(data)
    value_operating_leases = opl.debt_value_operating_leases(data)
    invested_capital = (data.equity_book_value + data.debt_book_value - data.cash_and_equivalents 
                        + value_research_asset + value_operating_leases)
    return invested_capital

def adjusted_operating_income(data: ModelInputs) -> float:
    operating_income_lease_adjustment = opl.adjust_operating_income_for_operating_lease(data)
    operating_income_research_and_development_adjustment = rd.adjust_operating_income_for_research_and_development(data)
    return data.operating_income + operating_income_lease_adjustment + operating_income_research_and_development_adjustment

#################### DCF Model ####################

def df_free_cashflow_forecast(data: ModelInputs) -> pd.DataFrame:

    base_year = {
        'Revenue Growth Rate': np.nan, 
        'Revenues': data.revenues, 
        'Operating Margin': data.operating_income / data.revenues, 
        'Operating Income': data.operating_income, 
        'Net Operating Loss': data.net_operating_loss, 
        'Operating Income corrected for NOL': data.operating_income, 
        'Tax Rate': effective_tax_rate_base_year(data), 
        'Taxes Paid': data.paid_in_taxes,
        'After-Tax Operating Income': data.operating_income - data.paid_in_taxes,
        'Sales to Capital Ratio': np.nan,
        'Reinvestment': np.nan,
        'Adjusted Invested Capital': adjusted_invested_capital(data), 
        'ROIC': (data.operating_income - data.paid_in_taxes) / adjusted_invested_capital(data), 
        'FCFF': np.nan, 
        'Cost of Capital': np.nan, 
        'Cumulative Discount Factor': np.nan, 
        'Discounted FCFF': np.nan
    }

    filler_data = np.full((12, len(base_year)), np.nan, dtype='float64')
    df = pd.DataFrame(filler_data, columns=base_year.keys())
    df.index.name = 'Year'
    df = df.rename(lambda x: f'{x:.0f}')
    df = df.rename({'0': 'Base Year', '11': 'Terminal Year'})

    df.loc['Base Year'] = base_year.values()
    
    df.loc['1':'10', 'Revenue Growth Rate'] = forecast_revenue_growth_rates(data)
    df.loc['Terminal Year', 'Revenue Growth Rate'] = perpetual_growth_rate(data)

    df.loc['1':'10', 'Revenues'] = data.revenues * (1 + df['Revenue Growth Rate']).agg(np.nancumprod)
    df.loc['Terminal Year', 'Revenues'] = df.loc['10', 'Revenues'] * (1 + df.loc['Terminal Year', 'Revenue Growth Rate'])
    
    df.loc['1':'10', 'Operating Margin'] = operating_margin(data)
    df.loc['Terminal Year', 'Operating Margin'] = df.loc['10', 'Operating Margin']

    df['Operating Income'] = df['Revenues'] * df['Operating Margin']
    df.loc['Terminal Year', 'Operating Income'] = df.loc['Terminal Year', 'Revenues'] * df.loc['Terminal Year', 'Operating Margin'] 

    df['Net Operating Loss'] = data.net_operating_loss - df['Operating Income'].shift(1).agg(np.nancumsum)
    df['Net Operating Loss'] = df['Net Operating Loss'].apply(lambda x: x if x > 0 else 0)
    df.loc['Base Year', 'Net Operating Loss'] = data.net_operating_loss
    
    df['Operating Income corrected for NOL'] = (df['Operating Income'] - df['Net Operating Loss']).apply(lambda x: x if x > 0 else 0)
    
    df.loc['1':'10', 'Tax Rate'] = forecast_tax_rates(data)
    df.loc['Terminal Year', 'Tax Rate'] = data.marginal_tax_rate

    df['Taxes Paid'] = df['Operating Income corrected for NOL'] * df['Tax Rate']

    df['After-Tax Operating Income'] = df['Operating Income'] - df['Taxes Paid']

    df.loc['1':'10', 'Sales to Capital Ratio'] = sales_to_capital_ratios(data)

    df['Reinvestment'] = (df['Revenues'] - df['Revenues'].shift(1)) / df['Sales to Capital Ratio']

    df.loc['1':'10', 'Adjusted Invested Capital'] = adjusted_invested_capital(data) + df['Reinvestment'].agg(np.nancumsum)

    df['ROIC'] = df['After-Tax Operating Income'] / df['Adjusted Invested Capital']
 
    df.loc['1':'10', 'Cost of Capital'] = cost_of_capital_array(data)
    df.loc['Terminal Year', 'Cost of Capital'] = df.loc['10', 'Cost of Capital']
    
    if data.is_roc_in_perpetuity_custom:
        df.loc['Terminal Year', 'ROIC'] = data.custom_roc_in_perpetuity
    else: 
        df.loc['Terminal Year', 'ROIC'] = df.loc['10', 'Cost of Capital']
    reinvestment_rate_terminal_year = df.loc['Terminal Year', 'Revenue Growth Rate'] / df.loc['Terminal Year', 'ROIC']
    df.loc['Terminal Year', 'Reinvestment'] = reinvestment_rate_terminal_year * df.loc['Terminal Year', 'After-Tax Operating Income']
    
    df['FCFF'] = df['After-Tax Operating Income'] - df['Reinvestment']
    
    df['Cumulative Discount Factor'] = (1/(1 + df['Cost of Capital'])).agg(np.nancumprod)
    df.loc['Terminal Year', 'Cumulative Discount Factor'] = df.loc['10', 'Cumulative Discount Factor']
    
    df['Discounted FCFF'] = df['FCFF'] * df['Cumulative Discount Factor']
    df.loc['Terminal Year', 'Discounted FCFF'] = np.nan

    return df


def terminal_value(data: ModelInputs):
    df = df_free_cashflow_forecast(data)
    perp_growth_rate = perpetual_growth_rate(data)
    terminal_val = df.loc['Terminal Year', 'FCFF'] / (df.loc['Terminal Year', 'Cost of Capital'] - perp_growth_rate)
    return terminal_val

def discount_terminal_value(data: ModelInputs):
    df = df_free_cashflow_forecast(data)
    terminal_val = terminal_value(data)
    discounted_terminal_val = terminal_val * df.loc['10', 'Cumulative Discount Factor']
    return discounted_terminal_val

def sum_of_discounted_cashflows(data: ModelInputs):
    df = df_free_cashflow_forecast(data)
    pv_forecasted_cashflows = df['Discounted FCFF'].agg(np.nansum)
    discounted_terminal_value = discount_terminal_value(data)
    return pv_forecasted_cashflows + discounted_terminal_value

def value_operating_assets(data: ModelInputs):
    """ prob failure to be included later """
    discounted_cashflows = sum_of_discounted_cashflows(data)
    if data.failure_proceeds_calculation_method == "book value":
        bankruptcy_proceeds = data.failure_proceeds_pct_of_value * (data.equity_book_value + data.debt_book_value)
    elif data.failure_proceeds_calculation_method == "fair value":
        bankruptcy_proceeds = data.failure_proceeds_pct_of_value * discounted_cashflows

    return discounted_cashflows * (1 - data.probability_of_failure) + bankruptcy_proceeds * data.probability_of_failure

def cash_value(data: ModelInputs) -> float:
    cash = data.cash_and_equivalents
    if data.is_cash_value_custom:
        cash = cash - data.trapped_cash * data.tax_rate_trapped_cash
        cash = cash * (1 - data.cash_discount_pct)
    return cash

def value_equity(data: ModelInputs):
    val_op_assets = value_operating_assets(data)
    cash = cash_value(data)
    value_equity = val_op_assets - data.debt_book_value - data.minority_interests + cash + data.non_operating_assets
    return value_equity

def value_equity_in_common_stock(data: ModelInputs):
    equity_val = value_equity(data)
    if data.are_options_outstanding:
        options_val = opt.total_options_value_after_tax(data)
        return equity_val - options_val
    return equity_val

def value_per_share(data: ModelInputs):
    value_common_stock = value_equity_in_common_stock(data)
    val_per_share = value_common_stock / data.n_shares
    return val_per_share

def share_value_and_upside(data: ModelInputs):
    """"""
    val_per_share = value_per_share(data)
    upside = val_per_share / data.price_per_share - 1
    return val_per_share, upside

def display_price_value_summary(data: ModelInputs):
    value_per_share, upside = share_value_and_upside(data)
    

    print(f'Current Price: ${data.price_per_share:,.2f}')
    print(f'Estimated Value: ${value_per_share:,.2f}')
    print(f'Potential upside for the stock: {upside:.2%}')

def valuation_report(data: ModelInputs):
    wacc_df = wacc.cost_of_capital_df(data)
    styled_wacc_df = wacc_df.style.format({
        'Market Value': '${:,.0f}',
        'Weight': '{:.2%}',
        "Cost of Component": '{:.2%}'
    })
    cost_of_capital = wacc.cost_of_capital(data)

    print(f'Cost of Capital: {cost_of_capital:.2%}')

    return styled_wacc_df
    


