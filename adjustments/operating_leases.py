import pandas as pd
import numpy_financial as npf

from cost_of_capital.wacc_inputs import WaccInputs
from cost_of_capital import wacc


def select_operating_leases_current_year(data: WaccInputs) -> float:
    df = data.operating_lease_expenses
    return df.loc['Current Year', 'Lease Commitment']

def remove_current_year_from_operating_leases_df(data: WaccInputs) -> pd.DataFrame:
    df = data.operating_lease_expenses
    df = df.drop('Current Year')
    return df

def estimate_years_embedded_in_commitment_year_6_and_beyond(data: WaccInputs) -> float:
    df = remove_current_year_from_operating_leases_df(data)
    return df.loc['6 and Beyond', 'Lease Commitment'] / df.loc[:5, 'Lease Commitment'].mean()

def estimate_yearly_commitment_year_6_and_beyond(data: WaccInputs) -> float:
    df = remove_current_year_from_operating_leases_df(data)
    years_embedded_in_year_6_estimate = estimate_years_embedded_in_commitment_year_6_and_beyond(data)
    return  df.loc['6 and Beyond', 'Lease Commitment'] / years_embedded_in_year_6_estimate

def add_discounted_lease_commitments_to_operating_leases_df(data: WaccInputs) -> pd.DataFrame:
    df = remove_current_year_from_operating_leases_df(data)
    years_embedded_in_year_6_estimate = estimate_years_embedded_in_commitment_year_6_and_beyond(data)
    yearly_commitment_year_6_and_beyond = estimate_yearly_commitment_year_6_and_beyond(data)
    pt_cod = wacc.pre_tax_cost_of_debt(data)
    df['Pre-Tax Cost of Debt'] = pt_cod
    df['Cumulative Discount Factor'] = 1/(1 + df['Pre-Tax Cost of Debt']).cumprod()
    df['Present Value'] = df['Lease Commitment'] * df['Cumulative Discount Factor']
    df.loc['6 and Beyond', 'Present Value'] = npf.pv(
        pt_cod, 
        years_embedded_in_year_6_estimate,
        -yearly_commitment_year_6_and_beyond
    ) * df.loc[5, 'Cumulative Discount Factor']
    return df

def create_operating_leases_df(data: WaccInputs) -> pd.DataFrame:
    df = add_discounted_lease_commitments_to_operating_leases_df(data)
    return df

def debt_value_operating_leases(data: WaccInputs):
    if not data.adjust_for_operating_leases:
        return 0
    else:
        df = create_operating_leases_df(data)
        return df["Present Value"].sum()

############ Depreciation Leased Assets ############
def operating_lease_asset_life(data: WaccInputs):
    """ Asset life: first 5 years (hardcoded) + years embedded in year 6 estimate """
    years_embedded_in_year_6_estimate = estimate_years_embedded_in_commitment_year_6_and_beyond(data)
    asset_life = data.n_periods_of_future_operating_leases_in_financials + years_embedded_in_year_6_estimate
    return asset_life

def yearly_depreciation_leased_asset(data: WaccInputs):
    df = create_operating_leases_df(data)
    asset_life = operating_lease_asset_life(data)
    depreciation_leased_asset = df['Present Value'].sum() / asset_life
    return depreciation_leased_asset

############ Adjustments to Operating Income & Total Debt ############
def adjust_operating_income_for_operating_lease(data: WaccInputs):
    operating_lease_expense_current_year = select_operating_leases_current_year(data)
    depreciation = yearly_depreciation_leased_asset(data)
    if data.adjust_for_operating_leases:
        return operating_lease_expense_current_year - depreciation
    else:
        return 0

def adjust_total_debt_for_operating_leases(data: WaccInputs):
    adjustment_to_total_debt = debt_value_operating_leases(data) # to be added to invested capital
    return adjustment_to_total_debt

def adjust_depreciation_for_operating_leases(data: WaccInputs):
    if data.adjust_for_operating_leases:
        return yearly_depreciation_leased_asset(data)
    else:
        return 0
