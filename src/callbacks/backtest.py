from itertools import combinations
from math import atan, pi

from dash import html, Input, Output, State, dash_table
import dash_mantine_components as dmc
import numpy as np
import pandas as pd
import polars as pl
import vectorbt as vbt

import src.data.data as data

try:
    import my_config as config
except ImportError:
    import config

vbt.settings.stats_builder['metrics'] = ['sharpe_ratio', 'total_return', 'open_trade_pnl', 'total_trades', 'total_open_trades',
                                         'win_rate', 'avg_winning_trade', 'avg_losing_trade', 'expectancy',
                                         'avg_winning_trade_duration', 'avg_losing_trade_duration', 'max_gross_exposure']

# Adjusts window length based on the number of windows, providing a 75% overlap. Also used in plotting.py.
def overlap_factor(nwindows):
    factors = [.375, .5, .56, .6, .625, .64]
    if nwindows < 8:
        return factors[nwindows - 2]
    else:
        return (13 / (9 * pi)) * atan(nwindows)

# For creating a numpy.arange array with a closed interval instead of half-open.
def closed_arange(start, stop, step, dtype=None):
    array = np.arange(start, stop, step, dtype=dtype)
    if array[-1] + step <= stop:
        end_value = np.array(stop, ndmin=1, dtype=dtype)
        array = np.concatenate([array, end_value])
    return array

# This callback creates the tables within the tabular results section.
def simulation_callback(app, cache):
    @app.callback(
        [
            Output('results_div', 'children'),
            Output('insample_div', 'children'),
            Output('outsample_div', 'children'),
            Output('run_button', 'loading')
        ],
        [
            Input('run_button', 'n_clicks'),
            Input('session-id', 'data'),
            State('strategy_drop', 'value'),
            State('nwindows', 'value'),
            State('insample', 'value'),
            State('timeframe', 'value'),
            State('asset', 'value'),
            State('date_range', 'value'),
            State('trade_direction', 'value'),
            State({'type': 'slider'}, 'value'),
            State('metric_drop', 'value'),
        ]
    )
    def perform_backtest(n_clicks, session_id, selected_strategy, nwindows, insample, selected_timeframe,
                         selected_asset, dates, selected_direction, selected_range, selected_metric):
        df = data.cached_df(cache, selected_timeframe, selected_asset, dates[0], dates[1])

        if config.data_type == 'postgres':
            close = df.select(pl.col(['date', 'close'])).to_pandas()
            close = close.set_index('date')
        elif config.data_type == 'yfinance':
            close = df['close']
            close = close.astype({'close': 'double'})

        # Split the data into walk-forward windows to be looped through.
        window_kwargs = dict(n=nwindows, set_lens=(insample / 100,),
                             window_len=round(len(df) / ((1 - overlap_factor(nwindows)) * nwindows)))
        (in_price, in_dates), (out_price, out_dates) = close.vbt.rolling_split(**window_kwargs, plot=False)

        # The portfolio calculations use a 24 hour trading day. This can effectively be corrected by inflating the time interval.
        trading_day_conversion = 24 / 6.5
        if selected_timeframe == '1d':
            time_interval = '1d'
        else:
            time_interval = "{}{}".format(round(int(selected_timeframe[:-1]) * trading_day_conversion, 4), 'm')

        pf_kwargs = dict(direction=selected_direction, freq=time_interval, init_cash=100, fees=0.000, slippage=0.000)

        if selected_strategy == 'SMA Crossover':
            columns_list = ["Fast SMA Period", "Slow SMA Period"]
            optimal_columns_list = ["Window", "Optimal Fast SMA Period", "Optimal Slow SMA Period",
                                    "Optimal Return [%]", "Return [%]", "Average Return [%]", "Benchmark Return [%]"]

            parameter_values = closed_arange(selected_range[0], selected_range[1], 10, np.int16)

            def backtest_windows(price, sma_periods, all_periods=True):
                if all_periods is True:
                    fast_sma, slow_sma = vbt.IndicatorFactory.from_talib('SMA').run_combs(price, sma_periods)
                else:
                    fast_sma = vbt.IndicatorFactory.from_talib('SMA').run(price, sma_periods[0], per_column=True)
                    slow_sma = vbt.IndicatorFactory.from_talib('SMA').run(price, sma_periods[1], per_column=True)
                entries = fast_sma.real_crossed_above(slow_sma.real)
                exits = fast_sma.real_crossed_below(slow_sma.real)
                return vbt.Portfolio.from_signals(price, entries, exits, **pf_kwargs)

        elif selected_strategy == 'EMA Crossover':
            columns_list = ["Fast EMA Period", "Slow EMA Period"]
            optimal_columns_list = ["Window", "Optimal Fast EMA Period", "Optimal Slow EMA Period",
                                    "Optimal Return [%]", "Return [%]", "Average Return [%]", "Benchmark Return [%]"]

            parameter_values = closed_arange(selected_range[0], selected_range[1], 10, np.int16)

            def backtest_windows(price, ema_periods, all_periods=True):
                if all_periods is True:
                    fast_ema, slow_ema = vbt.IndicatorFactory.from_talib('EMA').run_combs(price, ema_periods)
                else:
                    fast_ema = vbt.IndicatorFactory.from_talib('EMA').run(price, ema_periods[0], per_column=True)
                    slow_ema = vbt.IndicatorFactory.from_talib('EMA').run(price, ema_periods[1], per_column=True)
                entries = fast_ema.real_crossed_above(slow_ema.real)
                exits = fast_ema.real_crossed_below(slow_ema.real)
                return vbt.Portfolio.from_signals(price, entries, exits, **pf_kwargs)

        # elif selected_strategy == 'MACD':

        elif selected_strategy == 'RSI':
            columns_list = ["RSI Entry Value", "RSI Exit Value"]
            optimal_columns_list = ["Window", "Optimal RSI Entry Value", "Optimal RSI Exit Value",
                                    "Optimal Return [%]", "Return [%]", "Average Return [%]", "Benchmark Return [%]"]

            raw_parameter_values = closed_arange(selected_range[0], selected_range[1], 2, np.int16)
            # Generate all entry and exit combinations, with entry value < exit value by default, and splitting them into seperate lists.
            # For the crossover strategies this was already done for us by the .run_combs function for the period parameters.
            parameter_combinations = list(combinations(raw_parameter_values, 2))
            parameter_values_entries = [parameter_combinations[i][0] for i in range(len(parameter_combinations))]
            parameter_values_exits = [parameter_combinations[i][1] for i in range(len(parameter_combinations))]
            parameter_values = [parameter_values_entries, parameter_values_exits]

            def backtest_windows(price, entry_exit_values, dummy_variable=None):
                rsi = vbt.IndicatorFactory.from_talib('RSI').run(price, 14)
                entries = rsi.real_crossed_below(entry_exit_values[0])
                exits = rsi.real_crossed_above(entry_exit_values[1])
                return vbt.Portfolio.from_signals(price, entries, exits, **pf_kwargs)

        # A function to group by window index so we can properly access the various metrics for each window.
        def get_optimal_parameters(accessed_metric):
            if selected_metric == 'max_drawdown':
                indexed_parameters = accessed_metric[accessed_metric.groupby("split_idx").idxmin()].index
            else:
                indexed_parameters = accessed_metric[accessed_metric.groupby("split_idx").idxmax()].index

            first_parameters = indexed_parameters.get_level_values(indexed_parameters.names[0]).to_numpy()
            second_parameters = indexed_parameters.get_level_values(indexed_parameters.names[1]).to_numpy()
            return np.array([first_parameters, second_parameters])

        # Testing all parameter combinations on the in-sample windows and getting optimal parameters.
        # The deep.getattr function is used to provide the portfolio metric to optimize on in a variable way.
        pf_insample = backtest_windows(in_price, parameter_values)
        outsample_parameters = get_optimal_parameters(pf_insample.deep_getattr(selected_metric))

        # Testing the extracted parameters on the out-of-sample windows.
        pf_outsample = backtest_windows(out_price, outsample_parameters, False)

        # Testing all parameter combinations on the out-of-sample windows for comparison purposes.
        pf_outsample_optimized = backtest_windows(out_price, parameter_values)
        optimal_parameters = get_optimal_parameters(pf_outsample_optimized.deep_getattr(selected_metric))

        # Caching the calculated portfolios for use in backtest_plotting_callback, using the uuid4 as the label.
        pickled_portfolio = pf_outsample.dumps()
        cache.set(session_id, pickled_portfolio, timeout=7200)
        print(f'stored session id: {session_id}')

        # Creating the dataframes for the viewing the backtest results.
        outsample_df = pf_outsample.stats(agg_func=None)
        outsample_df = outsample_df.reset_index(drop=True)
        outsample_df = outsample_df.rename(columns={"Total Return [%]": "Return [%]", "Total Open Trades": "Open Trades",
                                                    "Expectancy": "Expectancy [%]", "Max Gross Exposure [%]": "Exposure [%]"})

        window_number = pd.DataFrame(np.arange(1, nwindows + 1), columns=["Window"], dtype=np.int16)
        params_df = pd.DataFrame(outsample_parameters.transpose(), columns=columns_list, dtype=np.int16)
        outsample_maxdrawdowns = pd.Series(pf_outsample.max_drawdown().values * 100, name='Max Drawdown [%]')
        outsample_df = pd.concat([window_number, params_df, outsample_maxdrawdowns, outsample_df], axis=1).round(2)

        optimal_params_df = pd.DataFrame(optimal_parameters.transpose(), dtype=np.int16)
        outsample_returns = pd.Series(pf_outsample.total_return().values * 100)
        optimal_returns = pf_outsample_optimized.stats('total_return', agg_func=None).groupby("split_idx").max().reset_index(drop=True)
        average_returns = pf_outsample_optimized.stats('total_return', agg_func=None).groupby("split_idx").mean().reset_index(drop=True)
        benchmark_returns = pf_outsample_optimized.stats('benchmark_return', agg_func=None).groupby('split_idx').mean().reset_index(drop=True)
        comparison_df = pd.concat([window_number, optimal_params_df, optimal_returns, outsample_returns, average_returns, benchmark_returns], axis=1).round(2)
        comparison_df.columns = optimal_columns_list

        # Defining dash components for displaying the formatted data.
        outsample_dates = pd.DataFrame(out_dates[0])
        outsample_num_days = len(outsample_dates['split_0'].dt.date.unique())

        averages_table = dmc.Table(
            [
                html.Tbody(
                    [
                        html.Tr([html.Td("Annualized return"), html.Td(f"{round(pf_outsample.total_return().mean() * 100 * (252 / outsample_num_days), 3)}%")]),
                        html.Tr([html.Td("Average return per window"), html.Td(f"{round(pf_outsample.total_return().mean()*100,2)}%")]),
                        html.Tr([html.Td("Average Sharpe ratio"), html.Td(f"{round(pf_outsample.sharpe_ratio().mean()*100,2)}")]),
                        html.Tr([html.Td("Average max drawdown"), html.Td(f"{round(pf_outsample.max_drawdown().mean()*100,2)}%")]),
                    ]
                )
            ],
            highlightOnHover=True
        )

        def create_table(df):
            columns, values = df.columns, df.values
            header = [html.Tr([html.Th(col) for col in columns])]
            rows = [html.Tr([html.Td(cell) for cell in row]) for row in values]
            table = [html.Thead(header), html.Tbody(rows)]
            return table

        # insample_table = dmc.Table(create_table(outsample_df), highlightOnHover=True, withColumnBorders=True)
        outsample_table = dmc.Table(create_table(comparison_df), highlightOnHover=True, withColumnBorders=True)

        insample_table = dash_table.DataTable(
            data=outsample_df.to_dict('records'),
            columns=[{'name': str(i), 'id': str(i)} for i in outsample_df.columns],
            # style_as_list_view=True,
            style_header={
                'backgroundColor': 'rgba(30, 30, 30, 00)',
                'color': 'white',
                'fontWeight': 'bold'
            },
            style_data={
                'backgroundColor': 'rgba(50, 50, 50, 00)',
                'color': 'white'
            },
            style_table={
                'overflowX': 'scroll'
            },
            # fixed_columns={'headers': True, 'data': 1},
            cell_selectable=False,
            tooltip_header={'Expectancy [%]': {'value': 'testing'}},
            fill_width=True,
            # css=[{"selector": ".dash-spreadsheet", "rule": 'font-family: "monospace"'}],
            # columns=['Avg Winning Trade Duration': {'type': 'datetime'}]
            style_cell={'padding': '5px'},
            # style_header={
            #     'backgroundColor': 'white',
            #     'fontWeight': 'bold'
            # },
            style_cell_conditional=[{'textAlign': 'left'}],
        )

        return averages_table, insample_table, outsample_table, False

# Column names:
'''
metrics['average_return_values'] : "In-Sample Average (%)"
metrics['average_sharpe_values'] : "In-Sample Average Sharpe Ratio"
metrics['average_maxdrawdown_values'] : "In-Sample Average Max Drawdown (%)"
metrics['max_return_values'] : "In-sample Return (%)"
metrics['max_sharpe_values'] : "In-sample Maximized Sharpe Ratio"
metrics['min_maxdrawdown_values'] : "In-sample Minimized Max Drawdown (%)"
metrics['realized_returns'] : "Return (%)"
metrics['realized_sharpe'] : "Sharpe Ratio"
metrics['realized_maxdrawdown'] : "Max Drawdown (%)"
metrics['difference_in_returns'] : "Difference from In-Sample (%)"
metrics['difference_in_sharpe'] : "Difference from In-Sample"
metrics['difference_in_maxdrawdown'] : "Difference from In-Sample (%)"
metrics['average_return_values_h'] : "Out-of-Sample Average (%)"
metrics['average_sharpe_values_h'] : "Out-of-Sample Average Sharpe Ratio"
metrics['average_maxdrawdown_values_h'] : "Out-of-Sample Average Max Drawdown (%)"
metrics['max_return_values_h'] : "Out-of-Sample Maximum Return (%)"
metrics['max_sharpe_values_h'] : "Out-of-Sample Maximum Sharpe Ratio"
metrics['min_maxdrawdown_values_h'] : "Out-of-sample Minimum Max Drawdown (%)"
'''

# html.Tr([html.Td("Difference in return from in-sample"), html.Td(f"{round(mean(difference_in_returns), 3)}%")]),
# html.Tr([html.Td("Difference in Sharpe ratio from in-sample"), html.Td(f"{round(mean(difference_in_sharpe), 3)}")]),
# html.Tr([html.Td("Difference in max drawdown from in-sample"), html.Td(f"{round(mean(difference_in_maxdrawdown), 3)}%")])

# insample_table = dash_table.DataTable(
#     data=insample_df.to_dict('records'),
#     columns=[{'name': str(i), 'id': str(i)} for i in insample_df.columns],
#     style_as_list_view=True,
#     style_header={
#         'backgroundColor': 'rgb(30, 30, 30)',
#         'color': 'white'
#     },
#     style_data={
#         'backgroundColor': 'rgb(50, 50, 50)',
#         'color': 'white'
#     },
# )
