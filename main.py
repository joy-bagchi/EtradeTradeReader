import pandas as pd
import numpy as np


def read_csv(file_path: str) -> pd.DataFrame:
    transaction_types = ['Bought To Cover', 'Sold Short', 'Bought To Open', 'Sold To Close']
    columns = ['TransactionDate', 'TransactionType', 'SecurityType', 'Symbol', 'Quantity', 'Amount', 'Price',
               'Commission', 'Description']
    dtypes = {
        'TransactionType': pd.CategoricalDtype(categories=transaction_types),
        'SecurityType': pd.CategoricalDtype(),
        'Symbol': object,
        'Quantity': np.float64,
        'Amount': np.float64,
        'Price': np.float64,
        'Commission': np.float64,
        'Description': object
    }

    parse_dates = ['TransactionDate']
    converters = {'TransactionType': lambda x: x.strip(),
                  'Asset': lambda x: x.strip()
                  }
    print(columns)
    df = pd.read_csv(file_path,
                     dtype=dtypes,
                     parse_dates=parse_dates,
                     converters=converters,
                     usecols=columns,
                     skiprows=3
                     ).dropna()
    df = df[df['TransactionType'].isin(transaction_types)]

    return df


def create_symbol_based_dict(df: pd.DataFrame) -> dict:
    # Ensure TransactionDate is in datetime format
    df['TransactionDate'] = pd.to_datetime(df['TransactionDate'], format='%m/%d/%y')

    # Initialize an empty dictionary to store the data for each symbol
    symbol_dict = {}
    df['transaction_types_sortkey']  =  df['TransactionType'].map(
        {'Sold Short': 0, 'Bought To Cover': 1, 'Bought To Open': 2, 'Sold To Close': 3}
    )

    # Iterate over each unique symbol in the DataFrame
    for symbol in df['Symbol'].unique():
        # Filter the DataFrame for the current symbol
        symbol_df = df[df['Symbol'] == symbol].copy()

        # Sort the DataFrame by TransactionDate in descending order (most recent first)
        symbol_df = symbol_df.sort_values(by=['TransactionDate', 'transaction_types_sortkey'])

        # Select the relevant columns
        symbol_df = symbol_df[['TransactionDate', 'TransactionType', 'Quantity', 'Price']]

        # Store the DataFrame in the dictionary with the symbol as the key
        symbol_dict[symbol] = symbol_df

    return symbol_dict


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    transactions = read_csv('data/trades_all.csv')
    print(transactions.head())  # Print the first few rows of the DataFrame
    symbol_based_df = create_symbol_based_dict(transactions)
    print(len(symbol_based_df))
    for k in symbol_based_df.keys():
        print(k)
        print(symbol_based_df[k])
        print('-----------------')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
