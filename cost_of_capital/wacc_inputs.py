from dataclasses import dataclass

import pandas as pd

from dataloader import data_loader
from dataloader.data_loader_inputs import DataLoaderInputs

d_inputs = DataLoaderInputs()

@dataclass 
class WaccInputs(DataLoaderInputs):

    # company inputs
    country_incorporation: str = "Belgium"

    ##### Equity

    ### Cost of Equity & Cost of Debt
    
    # Riskfree Rate for Equity and Debt
    adjust_riskfree_rate_for_country_default_spread: bool = False

    # ERP & Country Default Spread for Equity and Debt
    country_revenues: pd.DataFrame = data_loader.load_company_revenues_by_country_to_df(d_inputs)
    region_revenues: pd.DataFrame = data_loader.load_company_revenues_by_region_to_df(d_inputs)
    erp_geo_method: str = "region" # country or region

    # beta
    industry_revenues: pd.DataFrame = data_loader.load_company_revenues_by_industry_to_df(d_inputs)

    ### Weight of Equity


    ##### Debt

    ### Cost of Debt

    # Company Default Spread for Debt
    operating_income: float = 710000
    interest_expense: float = 101.7

    ### Weight of Debt


    ##### Preferred Stock: Cost and Market Value
    price_per_preferred_share: float = 70
    dividend_preferred_share: float = 5
    n_preferred_shares: int = 0

    ### Market Value Equity & Debt
 
    # Market Value Equity
    n_shares: int = 246400
    price_per_share: float = 31.75

    ##### Market Value Debt
    # Straight Debt
    debt_book_value: float = 2343500
    debt_maturity: float = 5

    convertible_bond_book_value: float = 0 # there could be more than one convertible bond, user then has to calc totals and maturity
    convertible_bond_maturity: float = 0     # alternative, convertible bond is a list of convertible bond (data)class instances
    convertible_bond_interest_expense: float = 0

    # Operating Leases
    adjust_for_operating_leases: bool = False
    n_periods_of_future_operating_leases_in_financials: int = 5
    operating_lease_expenses: pd.DataFrame = data_loader.load_company_operating_leases_to_df(d_inputs)

    # Research & Development
    adjust_for_research_and_development: bool = True
    research_and_development_life: int = 4
    research_and_development_expenses: pd.DataFrame = data_loader.load_company_research_and_development_to_df(d_inputs)