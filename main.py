import numpy as np
import pandas as pd
from pandas import DataFrame


def read_csv(file_path: str) -> pd.DataFrame:
    transaction_types = ['Bought To Cover', 'Sold Short', 'Bought To Open', 'Sold To Close', 'Option Expiration']
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
    df['transaction_types_sortkey'] = df['TransactionType'].map(
        {'Sold Short': 0, 'Bought To Cover': 1, 'Bought To Open': 2, 'Sold To Close': 3}
    )

    # Iterate over each unique symbol in the DataFrame
    for symbol in df['Symbol'].unique():
        # Filter the DataFrame for the current symbol
        symbol_df = df[df['Symbol'] == symbol].copy()

        # Sort the DataFrame by TransactionDate in descending order (most recent first)
        symbol_df = symbol_df.sort_values(by=['TransactionDate', 'transaction_types_sortkey'])

        # Select the relevant columns
        symbol_df = symbol_df[['TransactionDate', 'TransactionType', 'Quantity', 'Price', 'SecurityType']]

        # Store the DataFrame in the dictionary with the symbol as the key
        symbol_dict[symbol] = symbol_df

    return symbol_dict


def create_trades(symbol_df: dict[str: pd.DataFrame]) -> Exception | None | DataFrame:
    results = []

    for symbol, positions in symbol_df.items():
        # Sort the DataFrame by TransactionDate
        # positions.sort_values('TransactionDate', inplace=True)

        # Lists to store open positions
        open_trade = {}
        trade_size = 0
        remaining_quantity = 0


        # Only process trades for SPY
        if 'SPY' in symbol:
            # Iterate through each transaction

            for index, position in positions.iterrows():
                if 'Option Expiration' in position['TransactionType']:
                    position['TransactionType'] = 'Sold To Close' if open_trade[
                                                                         'Trade Side'] == 'Long' else 'Bought To Cover'

                transaction_type = position['TransactionType']
                quantity = position['Quantity']
                price = position['Price']
                transaction_date = position['TransactionDate']

                if transaction_type in ['Sold Short', 'Bought To Open']:
                    # Opening a trade (either short or long)
                    trade_size += quantity
                    remaining_quantity += quantity
                    if len(open_trade.keys()) == 0:
                        open_trade = {
                            'OpenDate': transaction_date,
                            'Trade Side': 'Short' if transaction_type == 'Sold Short' else 'Long',
                            'Quantity': quantity,
                            'Entry Price': price,
                        }
                    else:
                        open_trade['Entry Price'] = (
                                (open_trade['Entry Price'] * open_trade['Quantity'] + price * quantity)
                                / (open_trade['Quantity'] + quantity))
                        open_trade['Quantity'] += quantity
                elif transaction_type in ['Bought To Cover', 'Sold To Close']:
                    # Closing a trade (either covering a short or selling a long)
                    trade_side = 'Short' if transaction_type == 'Bought To Cover' else 'Long'
                    # Check if there is an open trade to close
                    if len(open_trade.keys()) == 0:
                        print('Error: No open trade to close')
                        return Exception('No open trade to close: ' + symbol)
                    # Only match trades with the same side
                    if open_trade['Trade Side'] != trade_side:
                        print('Error: Trade sides dont match')
                        return Exception('Trade sides dont match')

                    if 'Exit Price' in open_trade.keys():
                        open_trade['Exit Price'] = ((open_trade['Exit Price'] * abs(
                            trade_size - remaining_quantity) + price * abs(quantity))
                                                    / (abs(trade_size - remaining_quantity) + abs(quantity)))
                    else:
                        open_trade['Exit Price'] = price

                    if abs(open_trade['Quantity']) == abs(quantity):
                        remaining_quantity -= quantity
                        # Full close of the open trade
                        open_trade['Quantity'] += quantity
                        if open_trade['Quantity'] != 0:
                            print('Error: Trade was not closed properly')
                            return Exception('Trade was not closed properly')
                        # Append to results
                        pnl = ((open_trade['Entry Price'] - open_trade['Exit Price']) * abs(trade_size) *
                               (100.00 if position['SecurityType'] == 'OPTN' else 1.00))
                        if trade_side == 'Long':
                            pnl = -pnl  # Long trades are negative PnL

                        pnl_percent = pnl / (open_trade['Entry Price'] * abs(trade_size) *
                                             (100.00 if position['SecurityType'] == 'OPTN' else 1.00))
                        results.append({
                            'Symbol': symbol,
                            'OpenDate': open_trade['OpenDate'],
                            'CloseDate': transaction_date,
                            'Trade Status': ('Win' if pnl > 0 else 'Loss'),
                            'Trade Side': trade_side,
                            'PnL ($)': pnl,
                            'PnL (%)': pnl_percent,
                            'Entry Price': open_trade['Entry Price'],
                            'Exit Price': open_trade['Exit Price'],
                            'Trade Size': abs(trade_size),
                            'Holding Period': (transaction_date - open_trade['OpenDate']).days
                        })
                        trade_size = 0
                        open_trade = {}
                    elif abs(open_trade['Quantity']) > abs(quantity):
                        # Partial close of the open trade
                        remaining_quantity -= quantity
                        open_trade['Quantity'] += quantity
                    else:
                        print('Error: Trade was not closed properly: More quantity closed than opened')
                        return Exception('Trade was not closed properly: More quantity closed than opened')

            # Process any remaining open trades
            if len(open_trade.keys()) > 0:
                results.append({
                    'Symbol': symbol,
                    'OpenDate': open_trade['OpenDate'],
                    'CloseDate': None,
                    'Trade Status': 'Open',
                    'Trade Side': open_trade['Trade Side'],
                    'PnL ($)': None,
                    'PnL (%)': None,
                    'Entry Price': open_trade['Entry Price'],
                    'Exit Price': None,
                    'Trade Size': abs(trade_size),
                    'Holding Period': (transaction_date - open_trade['OpenDate']).days
                })

    # Convert results to DataFrame
    trades_df = pd.DataFrame(results,
                             columns=['Symbol', 'OpenDate', 'CloseDate', 'Trade Status', 'Trade Side', 'PnL ($)',
                                      'PnL (%)', 'Entry Price', 'Exit Price', 'Trade Size', 'Holding Period'])
    return trades_df


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    transactions = read_csv('data/trades_all.csv')

    print(transactions.head())  # Print the first few rows of the DataFrame
    symbol_based_df = create_symbol_based_dict(transactions)
    print(len(symbol_based_df))
    _trades = create_trades(symbol_based_df)
    if type(_trades) is not Exception and type(_trades) is not None:
        print(_trades.head())
        _trades.to_csv('data/portfolio_trades.csv', header=True, index=False)
    if type(_trades) is Exception:
        print(str(_trades))

    # See PyCharm help at https://www.jetbrains.com/help/pycharm/
