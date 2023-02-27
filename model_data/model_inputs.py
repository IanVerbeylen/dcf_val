from dataclasses import dataclass

from cost_of_capital.wacc_inputs import WaccInputs

@dataclass
class ModelInputs(WaccInputs):
    """ Variables which are not depending on wacc calculations and are not valuation drivers,
    can be inputted in the wacc_inputs: e.g. financial statement items 
    (can't be in data_loader_inputs, because they depend on files loaded)
    maybe rename the wacc_inputs then, because it wouldn't cover solely wacc inputs anymore """
    # general inputs
    n_stages_in_model: int = 3
    stage_1_periods: int = 1
    stage_2_periods: int = 4
    stage_3_periods: int = 5
    model_periods: int = 10

    ### valuation drivers: growth, operating margin, sales to capital (reinvestment)
    
    # Revenue Growth:
    # Currently constant growth in stage 2, gradual convergence towards target growth rate in stage 3
    # This is a choice of the user: constant growth rate or gradual convergence for stage 2 or 3
    # implementation: done
    growth_method_stage_2: str = "constant"
    growth_method_stage_3: str = "converge"
    growth_rate_stage_1: float = 0.05
    growth_rate_target_stage_2: float = 0.05
    # growth_rate_target_stage_3: riskfree rate or custom rate if less than rfr, more than rfr can't happen

    # Operating Margin:
    operating_margin_year_one: float = 0.03
    operating_margin_target: float = 0.035
    operating_margin_convergence_year: int = 3

    # Reinvestment: Sales to Capital Ratio => Growth Efficiency
    sales_to_capital_method_stage_2: str = "constant"
    sales_to_capital_method_stage_3: str = "constant"
    sales_to_capital_stage_1: float = 5.5
    sales_to_capital_target_stage_2: float = 5.25
    sales_to_capital_target_stage_3: float = 5

    ### Forecasting DCF Line Items

    # Balance Sheet
    net_operating_loss: float = 0 # not linked from stockrow data, NOL is off-balance sheet item,
                                    # might do "Deferred Tax Assets" / marginal tax rate as approximation
                                    # otherwise user can input this manually, to be seen
                                    # "Net Deferred Tax Asset": https://breakingintowallstreet.com/kb/accounting/net-operating-losses/
    minority_interests: float = 49600 # not in stockrow data, but found on balance sheet

    # Income Statement
    revenues: float = 25435500
    earnings_before_tax: float = 710000
    paid_in_taxes: float = 137600

    # Tax Rate
    is_tax_rate_base_year_custom: bool = False
    custom_base_year_tax_rate: float = 0.25
    tax_rate_in_perpetuity: str = "marginal" # effective or marginal tax rate

    # Cost of Capital (wacc)
    wacc_method_stage_2: str = "constant"
    wacc_method_stage_3: str = "converge"
    wacc_target_stage_2: float = 0.1                       # wacc_stage_1
    # Damodaran: "In stable growth, I will assume that your firm will have 
    # a cost of capital similar to that of typical mature companies (riskfree rate + 4.5%)

    # Book Value Equity & Cash
    equity_book_value: float = 3566100
    cash_and_equivalents: float = 1239900

    # Off-Balance Sheet Items
    non_operating_assets: float = 0

    ### Options
    are_options_outstanding: bool = False
    strike_price_option: float = 22.68
    option_expiration_in_years: float = 2.53     # expiration date or earlier to correct for early expiration
    std_stock: float = 0.305 # annualized
    annualised_dividend_yield_stock = 0.015
    n_options : int = 520

    # adjustments
    adjust_option_value_for_taxes: bool = False
    tax_rate_option_value_adjustment: float = 0.25
    adjust_option_value_for_vesting: bool = False
    option_vesting_probability: float = 0.9
    options_tax_rate: float = 0.25

    ##### Default Model Assumptions

    # growth in perpetuity -> default is equal to riskfree rate
    is_perpetual_growth_rate_custom: bool = False
    custom_perpetual_growth_rate: float = -0.05

    # Cost of Capital in perpetuity -> default is equal to average cost of capital of mature market firms + 4.5%
    is_wacc_target_stage_3_custom: bool = False
    wacc_target_stage_3_custom: float = 0.075
    mature_market_company_wacc_vs_rfr_spread: float = 0.045

    # Return on Capital after year 10 -> default is equal to cost of capital in perpetuity
    is_roc_in_perpetuity_custom: bool = False
    custom_roc_in_perpetuity: float = 0.10

    # Probability of Failure -> default is no chance of failure
    probability_of_failure: float = 0
    failure_proceeds_calculation_method: str = "fair value" # (book value or fair value) book value of capital or estimated fair value for the company
    failure_proceeds_pct_of_value: float = 0.5

    # Riskfree Rate in perpetuity -> default is current riskfree rate
    is_riskfree_rate_in_perpetuity_custom: bool = True
    custom_riskfree_rate_in_perpetuity: float = 0.02

    # Cash valuation -> default is that cash is a neutral asset (you trust management will invest/use cash wisely),
    #             no cash is trapped in foreign countries and/or subject to additional tax liability
    is_cash_value_custom: bool = False
    cash_concern_type: str = "mistrust"      # (mistrust or trapped) manager mistrust or cash trapped in foreign country
    cash_discount_pct: float = 0.5          # cash discount factor because of manager mistrust
    trapped_cash: float = 50             # if cash trapped in foreign countries and additional tax will have to be paid to repatriate
    # amount of entire cash balance (if you mistrust management), or amount of trapped cash subject to future taxes
    tax_rate_trapped_cash: float = 0.25

