import pandas as pd

from cost_of_capital.wacc_inputs import WaccInputs

def amortization_table_research_and_development(data: WaccInputs):
    df = data.research_and_development_expenses
    df['Unamortized Portion'] = 1 + df.index.values / data.research_and_development_life
    df['Value Unamortized Portion'] = df['R&D Expenses'] * df['Unamortized Portion']
    df['Amortization This Year'] = df['R&D Expenses'].apply(lambda x: x / data.research_and_development_life)
    df.loc[0, 'Amortization This Year'] = 0
    df = df.reset_index(names="Year")
    df.loc[0, "Year"] = "Current Year"
    df = df.set_index("Year")
    return df

# Functions serving to adjust invested capital and operating income
def value_research_asset(data: WaccInputs):
    if not data.adjust_for_research_and_development:
        return 0
    else:
        df = amortization_table_research_and_development(data)
        return df['Value Unamortized Portion'].sum()

def amortization_current_year(data: WaccInputs):
    df = amortization_table_research_and_development(data)
    return df['Amortization This Year'].sum()

def select_research_and_development_expense_current_year(data: WaccInputs):
    df = amortization_table_research_and_development(data)
    return df.loc['Current Year', 'R&D Expenses']

def adjust_operating_income_for_research_and_development(data: WaccInputs):
    if not data.adjust_for_research_and_development:
        return 0
    else:
        research_and_development_expense_current_year = select_research_and_development_expense_current_year(data)
        amortization_asset_current_year = amortization_current_year(data)
        return research_and_development_expense_current_year - amortization_asset_current_year

def tax_effect_research_and_development_expensing(data: WaccInputs):
    if not data.adjust_for_research_and_development:
        return 0
    else:
        operating_income_adjustment = adjust_operating_income_for_research_and_development(data)
        return data.marginal_tax_rate * operating_income_adjustment
