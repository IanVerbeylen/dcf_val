from dataclasses import dataclass

@dataclass
class DataLoaderInputs:
    #### filepaths
    filepath_country_risk_premium: str = "data/erp_by_country.csv"
    filepath_industry_beta_us: str = "data/beta_us.csv"
    filepath_ev_to_sales_us: str = "data/DollarUS.xls"
    filepath_interest_coverage_ratio: str = "data/interest_coverage.csv"

    filepath_company_revenue_inputs: str = "data/revenue_data/company_revenue_inputs.xlsx"

    filepath_company_financials_inputs: str = "data/company_financials/company_financials_user_inputs.xlsx"

    # general financial variables
    marginal_tax_rate: float = 0.25

    ### Equity

    # rfr
    long_term_government_bond_rate: float = 0.0252


    # erp
    erp_mature_market: float = 0.0594 # temporary, until s&p500 erp model exists
    country_risk_equity_multiplier: float = 1.4106246 # temporary, until volatility from indices file exists