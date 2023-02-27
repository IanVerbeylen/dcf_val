import numpy as np
import pandas as pd

from dataloader.data_loader_inputs import DataLoaderInputs


############################## General ##############################

def country_list(data: DataLoaderInputs):
    """
    Args:
        DataLoaderInputs instance
    Returns:
        List of Countries for calculating equity risk premium
    """
    df = pd.read_csv(data.filepath_country_risk_premium)
    df = df.set_index('Country', drop=False)
    return list(df["Country"])

def region_list(data: DataLoaderInputs):
    """
    Args:
        DataLoaderInputs instance
    Returns:
        List of Regions for calculating country risk premium
    """
    df = pd.read_csv(data.filepath_country_risk_premium)
    return list(df["Region"].unique())

def industry_list(data: DataLoaderInputs) -> list[str]:
    """
    Args:
        DataLoaderInputs instance
    Returns:
        List of Industries for calculating beta        
    """
    df = pd.read_csv(data.filepath_industry_beta_us)
    return list(df["Industry Name"].unique())

############################## Company Data from User Input ##############################

def load_company_revenues_by_country_to_df(data: DataLoaderInputs) -> pd.DataFrame:
    """
    Args:
       DataLoaderInputs instance 
    Returns:
        Company revenues by country DataFrame
    """
    df = pd.read_excel(data.filepath_company_revenue_inputs, 'country', index_col="Country")
    return df.dropna()

def load_company_revenues_by_region_to_df(data: DataLoaderInputs) -> pd.DataFrame:
    """
    Args:
       DataLoaderInputs instance 
    Returns:
        Company revenues by Region DataFrame
    """
    df = pd.read_excel(data.filepath_company_revenue_inputs, 'region', index_col="Region")
    return df.dropna()

def load_company_revenues_by_industry_to_df(data: DataLoaderInputs) -> pd.DataFrame:
    """
    Args:
       DataLoaderInputs instance 
    Returns:
        Company revenues by Industry DataFrame
    """
    df = pd.read_excel(data.filepath_company_revenue_inputs, 'industry', index_col="Industry")
    return df.dropna()

########## Operating Leases ##########

def load_company_operating_leases_to_df(data: DataLoaderInputs) -> pd.DataFrame:
    """
    Args:
        DataLoaderInputs instance 
    Returns:
        Expected company operating leases
    """
    data = pd.read_excel(
        data.filepath_company_financials_inputs, 
        sheet_name="leases",
        index_col=0)
    return data

########## Research and Development Expenses ##########

def load_company_research_and_development_to_df(data: DataLoaderInputs) -> pd.DataFrame:
    """
    Args:
        DataLoaderInputs instance
    Returns:
        Historical company research and development expenses
    """
    data = pd.read_excel(
        data.filepath_company_financials_inputs, 
        sheet_name="r&d",
        index_col=0)
    data = data.dropna()
    return data

########## Historical Company Financials Data ##########

def load_historical_company_financials_to_df(data: DataLoaderInputs) -> pd.DataFrame:
    """
    Args:
        DataLoaderInputs instance
    Returns:
        Historical company financials from user inputs file
    """
    pd.read_excel(data.filepath_company_financials_inputs)

############################## Riskfree Rate ##############################

# could request long term government bond rate here from database or API

############################## Cost of Equity ##############################

########## ERP ##########

def equity_risk_premium_mature_market(data: DataLoaderInputs):
    """
    Args:
        DataLoaderInputs instance
    Returns:
        Mature market ERP
    Hard coded for now, normally comes from valuing S&P500 index
    """
    return data.erp_mature_market

def country_risk_equity_multiplier(data: DataLoaderInputs):
    """
    Args:
        DataLoaderInputs instance
    Returns:
        Country Risk Equity Multiplier from: 
            volatility of equity index of developing markets, 
            divided by volatility of equity index developed market
    Hard coded for now, normally comes from equity index data
    """
    return data.country_risk_equity_multiplier

##### Country Equity Risk premium #####

def load_base_ERP_data_to_df(data: DataLoaderInputs) -> pd.DataFrame:
    """
    Args:
        DataLoaderInputs instance
    Returns:
        DataFrame of GDP, Rating-based Default Spread, Corporate Tax Rate, and Regions of all countries
    """
    df = pd.read_csv(data.filepath_country_risk_premium)
    df = df.set_index('Country', drop=False)
    return df

def add_erp_to_country_risk_premium_df(data: DataLoaderInputs) -> pd.DataFrame:
    """
    Args: 
        DataLoaderInputs instance
    Returns:
        DataFrame of Equity Risk Premium for all countries
    """
    df = load_base_ERP_data_to_df(data)
    erp_mature_market = equity_risk_premium_mature_market(data)
    multiplier = country_risk_equity_multiplier(data)
    df["Country Risk Premium"] = df["Rating-based Default Spread"] * multiplier
    df["ERP"] = erp_mature_market + df["Country Risk Premium"]
    return df

def add_weighted_erp_to_country_premium_df(data: DataLoaderInputs) -> pd.DataFrame:
    """
    Args:
        DataLoaderInputs instance
    Returns:
        DataFrame of Equity Risk Premium for all countries with weighted ERP column
    """
    df = add_erp_to_country_risk_premium_df(data)
    columns = ["Region", "GDP (in billions)"]
    df["Region GDP (in billions)"] = df[columns].groupby("Region").transform(np.sum)
    df["GDP pct. of Region"] = df['GDP (in billions)'] / df['Region GDP (in billions)']
    df["Weighted ERP"] = df["ERP"] * df["GDP pct. of Region"]
    return df

def load_and_create_country_erp_df(data: DataLoaderInputs) -> pd.DataFrame:
    """
    Args:
        DataLoaderInputs instance
    Returns:
        DataFrame of ERP and weighted ERP for all countries
    """
    df = add_weighted_erp_to_country_premium_df(data)
    return df

##### Region Equity Risk premium #####

def region_equity_risk_premium(data: DataLoaderInputs) -> pd.Series:
    """
    Args:
        DataLoaderInputs instance
    Returns:
        Weighted region ERP series
    """
    df = load_and_create_country_erp_df(data)
    columns = ["Region", "Weighted ERP"]
    region_erp = df[columns].groupby("Region").apply(lambda x: x["Weighted ERP"].sum())
    return region_erp

def add_global_erp_to_region_series(data: DataLoaderInputs) -> tuple[str, pd.Series]:
    """
    Args:
        DataLoaderInputs instance
    Returns:
        Weighted region ERP series, including global ERP row
    """
    df = load_and_create_country_erp_df(data)
    df["GDP pct of world"] = df["GDP (in billions)"] / df["GDP (in billions)"].sum()
    world_erp = (df["ERP"] * df["GDP pct of world"]).sum()
    return ('Global', world_erp)

def create_region_erp_series(data: DataLoaderInputs) -> pd.Series:
    """
    Args:
        DataLoaderInputs instance
    Returns:
        Region ERP series
    """
    region_erp = region_equity_risk_premium(data)
    region, erp = add_global_erp_to_region_series(data)
    region_erp[region] = erp
    region_erp.name = "Region ERP"
    return region_erp

########## Beta ##########

def industry_beta_df_from_csv(data: DataLoaderInputs) -> pd.DataFrame:
    """
    Args:
        DataLoaderInputs instance
    Returns:
        Industry beta DataFrame from csv file
    """
    df = pd.read_csv(data.filepath_industry_beta_us)
    columns = pd.Series(df.columns).apply(lambda x: x.strip())
    df.columns = columns
    df = df.rename({"Industry Name": "Industry"}, axis=1).set_index("Industry")
    return df

def add_unlevered_beta_corrected_for_cash_to_df(data: DataLoaderInputs) -> pd.DataFrame:
    """
    Args:
        DataLoaderInputs instance
    Returns:
        Industry beta DataFrame with unlevered beta corrected for cash column
    """
    df = industry_beta_df_from_csv(data)
    df["Unlevered Beta"] = df.apply(lambda row: row["Levered Beta"] / (1 + (1 - data.marginal_tax_rate) * row["D/E Ratio"]), axis=1)
    df["Unlevered Beta Corrected For Cash"] = df["Unlevered Beta"] / (1 - df["Cash/Firm value"])
    return df

def ev_sales_df_from_data(data: DataLoaderInputs) -> pd.Series:
    """
    Args:
        DataLoaderInputs instance
    Returns:
        Industry beta DataFrame with 'EV to Sales' column
    """
    filepath = data.filepath_ev_to_sales_us
    df = pd.read_excel(filepath, sheet_name="Industry Averages", skiprows=7, index_col=0)
    df.index.name = "Industry"
    df["EV/Sales"] = df["Enteprise Value ($ millions)"] / df["Revenues ($ millions)"]
    return df["EV/Sales"]

def combine_industry_beta_df_and_ev_sales_df(data: DataLoaderInputs) -> pd.DataFrame:
    """
    Args:
        DataLoaderInputs instance
    Returns:
        Industry beta DataFrame, combined with 'EV to Sales' DataFrame
    """
    beta_df = add_unlevered_beta_corrected_for_cash_to_df(data)
    ev_sales_df = ev_sales_df_from_data(data)
    df = pd.merge(beta_df, ev_sales_df, left_on="Industry", right_on="Industry")
    return df

def load_and_wrangle_industry_beta_df(data: DataLoaderInputs) -> pd.DataFrame:
    """
    Args:
        DataLoaderInputs instance
    Returns:
        Industry beta DataFrame for calculating company beta
    """
    df = combine_industry_beta_df_and_ev_sales_df(data)
    return df

############################## Cost of Debt ##############################

########## Country Default Spread  ##########

# Code already in ERP DataFrames functions for Cost of Equity

########## Company Default Spread  ##########

def load_interest_coverage_ratio_to_df(data: DataLoaderInputs) -> pd.DataFrame:
    """
    Args:
        DataLoaderInputs instance
    Returns:
        Interest Coverate Ratio DataFrame
    """
    df = pd.read_csv(data.filepath_interest_coverage_ratio)
    df = df.rename({"Rating is": "Rating", "Spread is": "Spread"}, axis=1)
    df["Spread"] = pd.to_numeric(df["Spread"].str.strip("%")) / 100
    return df

############################## Other ##############################

def clean_columns(df: pd.DataFrame) -> pd.Series:
    return pd.Series(df.columns).str.strip().replace(r'\s+', ' ', regex=True)