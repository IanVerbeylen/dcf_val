
import numpy as np
import pandas as pd
import numpy_financial as npf

from dataloader import data_loader
from cost_of_capital.wacc_inputs import WaccInputs
from adjustments import operating_leases as opl

data = WaccInputs()

########## Country Risk ##########



################################################################################
#                             Riskfree Rate                                    #
################################################################################

def riskfree_rate(data: WaccInputs):
    """ riskfree rate according to typical default spread from country bond rating
    (currently not using cds spread or default spread from dollar denominated government bond)
    (currently not using the differential inflation formula)"""
    bond_rate = data.long_term_government_bond_rate
    erp_df = data_loader.load_base_ERP_data_to_df(data)
    if data.adjust_riskfree_rate_for_country_default_spread:
        country_default_spread = erp_df.loc[data.country_incorporation, "Rating-based Default Spread"]
        return bond_rate - country_default_spread
    else:
        return bond_rate

################################################################################
#                             ERP: Equity Risk Premium                         #
################################################################################

##### Country Equity Risk premium #####

def company_erp_operating_countries_df(data: WaccInputs) -> pd.DataFrame:
    # operating_countries = []
    # for country in data.country_revenues.keys():
    #     operating_countries.append(country.name)
    # operating_countries

    # df = pd.DataFrame({"Revenues": data.country_revenues.values()}, index=operating_countries)
    # df.index.name = "Country"
    df = data_loader.load_company_revenues_by_country_to_df(data)
    df = df.dropna()

    erp_df = data_loader.load_and_create_country_erp_df(data)
    df["ERP"] = pd.merge(df, erp_df, how='inner', left_index=True, right_index=True)["ERP"]
    df["Weight"] = df["Revenues"].apply(lambda x: x / df['Revenues'].sum()) 
    df["Weighted ERP"] = df["ERP"] * df["Weight"]
    return df

def company_erp_operating_countries(data: WaccInputs) -> float:
    df = company_erp_operating_countries_df(data)
    weighted_erp = df["Weighted ERP"].agg(np.nansum)
    return weighted_erp

##### Region Equity Risk premium #####

def company_erp_operating_regions_df(data: WaccInputs) -> pd.DataFrame:
    # regions = []
    # for region in data.region_revenues.keys():
    #     regions.append(region.name)

    # df = pd.DataFrame({"Revenues": data.region_revenues.values()}, index=regions)
    # df.index.name = "Region"

    region_erp_df = data_loader.create_region_erp_series(data)

    revenue_df = data_loader.load_company_revenues_by_region_to_df(data)

    df = pd.merge(revenue_df, region_erp_df, left_on="Region", right_on="Region", how="left")
    df["Weight"] = df["Revenues"].apply(lambda x: x / df["Revenues"].sum())
    return df

def company_erp_operating_regions(data: WaccInputs) -> float:
    df = company_erp_operating_regions_df(data)
    weighted_erp = df.apply(lambda row: (row["Weight"] * row["Region ERP"]), axis=1).agg(np.sum)
    return weighted_erp

def company_erp(data: WaccInputs):
    """User picks a method: country or region"""
    if data.erp_geo_method == "country":
        erp = company_erp_operating_countries(data)
    elif data.erp_geo_method == "region":
        erp = company_erp_operating_regions(data)
    return erp

################################################################################
#                             Company Levered Beta                             #
################################################################################

def company_revenues_by_industry_df(data: WaccInputs):
    # businesses = []
    # for business in data.business_revenues.keys():
    #     businesses.append(business.name)
    # businesses

    # df = pd.DataFrame({"Revenues": data.business_revenues.values()}, index=businesses)
    # df.index.name = "Business"
    df = data_loader.load_company_revenues_by_industry_to_df(data)
    df = df.dropna()
    df.index.name = "Business"
    return df
    
def company_beta_df(data: WaccInputs):
    df = data_loader.load_company_revenues_by_industry_to_df(data)
    beta_df = data_loader.load_and_wrangle_industry_beta_df(data)
    beta_df = beta_df[["Unlevered Beta Corrected For Cash", "EV/Sales"]]

    df = pd.merge(df, beta_df, left_on="Industry", right_on="Industry", how="left")
    df["Estimated Value"] = df["Revenues"] * df["EV/Sales"]
    df["Weight"] = df["Estimated Value"].apply(lambda x: x / df["Estimated Value"].sum())
    return df

def unlevered_beta_operating_assets(data: WaccInputs):
    df = company_beta_df(data)
    return (df["Weight"] * df["Unlevered Beta Corrected For Cash"]).sum()

def levered_beta_operating_assets(data: WaccInputs):
    unlevered_beta = unlevered_beta_operating_assets(data)
    mv_equity = equity_market_value(data)
    mv_debt = total_debt_market_value(data)
    d_e = mv_debt / mv_equity
    return unlevered_beta * (1 + (1 - data.marginal_tax_rate) * d_e)

def cost_of_equity(data: WaccInputs):
    rfr = riskfree_rate(data)
    erp = company_erp(data)
    beta_lev = levered_beta_operating_assets(data)
    return rfr + beta_lev * erp

################################################################################
#                             Debt                                             #
################################################################################

def country_default_spread(data: WaccInputs):
    df = data_loader.load_base_ERP_data_to_df(data)
    country = data.country_incorporation
    return df.loc[country, "Rating-based Default Spread"]

def company_default_spread(data: WaccInputs):
    """might have a user-defined extra term if much revenue from low-risk countries (val slide 109)"""
    df = data_loader.load_interest_coverage_ratio_to_df(data)
    interest_coverage_ratio = data.operating_income / data.interest_expense 
    df["Company Spread"] = df.apply(lambda x: (interest_coverage_ratio > x["lower bound"]) & (interest_coverage_ratio <= x["upper bound"]), axis=1)
    return (df["Company Spread"] * df["Spread"]).sum()

def pre_tax_cost_of_debt(data: WaccInputs):
    rfr = riskfree_rate(data)
    country_def_spread = country_default_spread(data)
    company_def_spread = company_default_spread(data)
    return rfr + country_def_spread + company_def_spread

def after_tax_cost_of_debt(data: WaccInputs):
    pt_cod = pre_tax_cost_of_debt(data)
    return pt_cod * (1 - data.marginal_tax_rate)

################################################################################
#                             Preferred Stock                                  #
################################################################################

def cost_preferred_stock(data: WaccInputs):
    return data.dividend_preferred_share / data.price_per_preferred_share

################################################################################
#                  Market Value Equity, Debt, Preferred Stock                  #
################################################################################

# Equity
def equity_market_value(data: WaccInputs) -> float:
    return data.n_shares * data.price_per_share

# Debt
def straight_debt_market_value(data: WaccInputs) -> float:
    pt_cost_of_debt = pre_tax_cost_of_debt(data)
    npv_debt_book_value = data.debt_book_value / (1 + pt_cost_of_debt)**data.debt_maturity
    pv_interest_payments = npf.pv(pt_cost_of_debt, data.debt_maturity, -data.interest_expense)
    straight_debt_market_value = npv_debt_book_value + pv_interest_payments
    return straight_debt_market_value

def market_value_equity_and_debt_in_convertible_bond(data: WaccInputs) -> tuple[float, float]:
    pt_cod = pre_tax_cost_of_debt(data)
    npv_convertible_bond = data.convertible_bond_book_value / (1 + pt_cod) ** data.convertible_bond_maturity
    pv_interest_payments = npf.pv(pt_cod, data.convertible_bond_maturity, -data.convertible_bond_interest_expense)
    debt_value_in_convertible_bond = npv_convertible_bond + pv_interest_payments
    equity_value_in_convertible_bond_equity_value = data.convertible_bond_book_value - debt_value_in_convertible_bond

    return (equity_value_in_convertible_bond_equity_value, debt_value_in_convertible_bond)

def total_debt_market_value(data: WaccInputs):
    straight_debt_mv = straight_debt_market_value(data)
    debt_value_operating_leases = opl.debt_value_operating_leases(data)
    _, debt_in_conv_bond = market_value_equity_and_debt_in_convertible_bond(data)
    total_debt = straight_debt_mv + debt_value_operating_leases  + debt_in_conv_bond
    return total_debt

# Preferred Stock
def preferred_stock_market_value(data: WaccInputs):
    return data.n_preferred_shares * data.price_per_preferred_share

################################################################################
#                             Cost of Capital                                  #
################################################################################

def cost_of_equity_debt_preferred_stock(data: WaccInputs) -> tuple[float, float, float]:
    coe = cost_of_equity(data)
    cod = after_tax_cost_of_debt(data)
    cps = cost_preferred_stock(data)
    return coe, cod, cps

def market_value_equity_debt_preferred_stock(data: WaccInputs) -> tuple[float, float, float]:
    mv_equity = equity_market_value(data)
    mv_debt = total_debt_market_value(data)
    mv_pref_stock = preferred_stock_market_value(data)
    return (mv_equity, mv_debt, mv_pref_stock)

def cost_of_capital_df(data: WaccInputs):
    mv_equity, mv_debt, mv_pref_stock = market_value_equity_debt_preferred_stock(data)
    coe, cod, cps = cost_of_equity_debt_preferred_stock(data)
    df = pd.DataFrame(index=["Equity", "Debt", "Preferred Stock"])
    df["Market Value"] = [mv_equity, mv_debt, mv_pref_stock]
    df["Weight"] = df["Market Value"].apply(lambda x: x / df["Market Value"].sum())
    df["Cost of Component"] = [coe, cod, cps]
    return df

def cost_of_capital(data: WaccInputs):
    df = cost_of_capital_df(data)
    return (df["Weight"] * df["Cost of Component"]).sum()

def cost_of_capital_report(data: WaccInputs):
    wacc_df = cost_of_capital_df(data)
    styled_wacc_df = wacc_df.style.format({
        'Market Value': '${:,.0f}',
        'Weight': '{:.2%}',
        "Cost of Component": '{:.2%}'
    })
    wacc = cost_of_capital(data)

    print(f'Cost of Capital: {wacc:.2%}')

    return styled_wacc_df


