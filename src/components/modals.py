from dash import dcc, html
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
import dash_mantine_components as dmc

# Components provided to the About modal in the top bar of the app.
about_modal_children = [
    dcc.Markdown(
        '''
        ### About This App

        ---

        This app is a tool for backtesting and optimizing trading strategies. It utilizes a more
        sophisticated method called walk-forward optimization. Read below to find out more.

        #### What is Strategy Optimization?

        In the "Strategy Details" area you can choose from four algorithmic trading strategies. These
        strategies involve functions known as *indicators* which typically take asset prices and/or
        trading volume as input and output a value used for trading decisions. It's also common to
        use the values of one indicator as input for another.

        Indicators generally have one or more constants in their equations, known as *parameters*.
        The most common parameter for an indicator to have is a *period*. This is the number
        of most recent historical prices used as input. For example, a 20-period simple moving average
        has a value equal to the average of the last 20 prices.
        Different parameter values can be tested while holding the trading rules for buying and selling
        fixed to find the optimal value for a chosen data set. The most common metric to optimize
        for is the overall profit or *return* from using the strategy. This app also allows you to
        choose two other metrics to optimize for: maximizing the Sharpe ratio or minimizing the
        maximum drawdown incurred throughout the test. It's worth mentioning that one can also hold the
        parameter values fixed and change the trading rules when optimizing a strategy.

        #### Cross-Validation

        Generally speaking, walk-forward optimization is a type of cross-validation technique. In
        cross-validation one splits a data set into in-sample periods and out-of-sample periods. The
        model is optimized on the former and tested on the latter.
        It's standard practice to only separate the data into a single in-sample and out-of-sample period.
        For chronologically ordered data, known as *time-series data*, one might use the first 80%
        for optimizing and the last 20% for testing. The out-of-sample period is intended to emulate
        performing live trading right after optimization.

        ##### The Issue With Single Period Cross-Validation

        The main drawback to using a single in-sample and out-of-sample period or *window* is that
        there is more uncertainty in whether a model is overfit.
        Overfitting generally occurs when a model has too many degrees of freedom i.e. parameters
        being optimized such that it can fit the training data nearly perfectly. Ironically, such
        hyper-optimzed models tend to have some of the worst real-world performance. If only a single,
        relatively short out-of-sample period is used for the model validation, there's a higher chance that
        the model happens to perform well out-of-sample, only to produce very poor results in live trading.
        Walk-forward optimization seeks to address this by making out-of-sample results more in line with
        live trading results for a given optimization procedure.

        ###### An Intuitive Example of Overfitting

        Suppose that a person's sleeping was observed for an hour, during which time they only slept on
        their side. An optimization is then conducted to find the least wasteful mattress for this
        person which still accommodates their observed sleeping patterns. If we're allowed
        only one parameter for the optimization, we might choose the width of the bed. We could reduce
        the mattress from say a king size to a twin if they never used more than half the bed during this
        hour. However, if we were allowed to optimize with several parameters, we can create a mattress
        with complicated curves, like the one shown below.
        '''
    ),
    dmc.Center([
        dmc.Image(
            src='assets/overfit.png',
            caption=dmc.Text("An overfit mattress optimized for a side-sleeper.", style={'margin-right': '18%'}),
            alt="Overfitting Image",
            width='80%'
        )],
        style={'margin-left': '15%', 'margin-top': '18px', 'margin-bottom': '25px'}
    ),
    dcc.Markdown(
        '''
        This is likely the most optimized mattress as it seemingly fits the observed data and optimization
        criteria perfectly. The problem with this hyperoptimization is that once the person shifts their
        sleeping position, they're going to fall off the bed! We've optimized the mattress so much
        that it can only accommodate a very specific sleeping behavior. Analogously, if we over-optimize a
        trading strategy and market behavior changes even slightly, we might incur significant losses. Now,
        if we had observed the person for a longer period of time, different sleeping positions might be
        present in the in-sample data. However, in general, overfitting is not avoided by simply adding
        more data.

        #### Walk-Forward Optimization

        Walk-forward optimization is a way to address this issue, not by making overfitting the in-sample
        data more difficult, but by making it much less likely that overfitting produces strong results
        out-of-sample. The method creates overlapping windows to maximize the number of out-of-sample
        periods without shrinking the size of the in-sample periods. Each window involves an optimization on
        in-sample and testing on out-of-sample before moving on to the next window and reoptimizing.
        At the end, all the out-of-sample results are averaged to evaluate the overall performance across
        the time period. It's typical for the windows to overlap by an amount close to the in-sample length
        as to keep each out-of-sample period unique. You can view a walk-forward graph in the main
        tab labeled "Price History and Windows" and alter it in the "Window Splitting" section to get an
        understanding of how it works.
        '''
    )
]

# Information modals for the sidebar labels
data_modal_children = [
    dcc.Markdown(
        '''
        ### Information About Asset Data

        ---

        #### Choosing an Asset

        The assets you can choose from for backtesting in this app are the most traded ETFs tracking
        the S&P 500, Nasdaq 100, Dow Jones Industral Average, and Russell 2000 indexes. The price of
        each ETF represents a fraction of the underlying index that it tracks, such as 1/10th of the
        S&P 500 Index price in the case of the SPY ETF. However, the price data is unadjusted for
        dividend payouts, causing it to deviate slightly from this ratio.

        #### Choosing a Timeframe

        Unless using tick data where every single trade is saved, asset price data is almost always
        aggregated using a set period or "timeframe". Open, High, Low, Close (OHLC) is the standard
        way to aggregate price data, and using a 1-day timeframe (1d) is by far the most common.
        In this case, the open price will be the first trade of the day, the close price will be the
        last recorded trade of the day, and the high and low prices will be the single highest and
        lowest trades recorded throughout the day. This means every data point has 4 price values.
        With the timeframe dropdown, you can choose from data aggregated every 15 minutes, 1 hour, or 1 day.

        As an aside, all the strategies provided in this app use the closing price values for their
        inputs, as is standard. This is likely because, on the daily timeframe, the close of the trading
        day sees very large spikes in trading volume. Therefore, this price carry more overall
        significance to investors who entered and exited positions that day.

        #### Visualizing Price Data

        The "Price History and Windows" tab of this app displays the OHLC data for you as a bar chart.
        The image below shows how the bars in a bar chart represent each price.
        '''
    ),
    dmc.Center([
        dmc.Image(
            src='assets/bars.png',
            alt="Bar chart structure",
            width='75%',
        )],
        style={'margin-left': '15%', 'margin-bottom': '20px'}
    ),
    dcc.Markdown(
        '''
        Each data point is represented as a vertical line or bar, where the top of the bar represents
        the high price and the bottom the low price. Additionally, each bar has two horizontal lines
        extending from it. On the left side, the line is at the opening price, and on the right side,
        at the closing price. Furthermore, the bar is colored green or red based on whether the closing
        price is higher or lower than the opening price respectively. Note that looking at the price
        data isn't necessary to use this app, but it can provide more context to the results.
        '''
    )
]

window_modal_children = [
    dcc.Markdown(
        '''
        ### Walk-Forward Optimization Parameters

        ---

        *For a short explanation of what walk-forward optimization is, you can click the "About"
        button in the header of the app.*

        #### Choosing the Number of Windows

        This app is as much a tool for testing an effective schema for walk-forward optimization as
        it is for testing indicator strategies. In general, the number of windows should be considered
        in proportion to how many data points there are in the total data set. If too few price points
        exist in each window, it's likely that not enough trades will be taken for the test to have
        significance. This number will vary for each strategy, given there can be sizeable differences
        in the number of trades produced. Furthermore, a strategy may only become active under a certain
        set of market conditions. To evaluate this, you can view how many trades were taken in each
        out-of-sample window in the backtest results tabs.

        #### Choosing the In-Sample Percentage

        Additionally, you have the freedom to choose what ratio of each window is in-sample and
        optimized on versus out-of-sample and tested on. Again, making either section too small
        can result in a loss of statistical significance. It is common practice in cross-validation
        to make the out-of-sample size about 20% of the in-sample size, or a ratio of 4:1. However,
        this is not a hard rule and it is recommended to experiment with the ratio in this app.

        #### Step Size

        An additional parameter which isn't currently adjustable by the user is the step size or
        conversely, the overlap size of the windows. This is the number of data points that each
        in-sample + out-of-sample window is moved forward by. This app uses a fixed step size
        of 25% of the window size, giving a 75% overlap between windows. This means that each window
        shares a considerable amount of data with the previous one. However, in the context of entering
        and existing positions, the same data with different data preceding it may produce different
        results. Each out-of-sample set will be unique and effectively mimic testing the effectiveness of
        the optimization methodology on fresh data or live trading performance. Note that in walk-forward
        optimization, each out-of-sample set will eventually become a part of an in-sample set to be
        optimized against.
        '''
    )
]

strategy_modal_children = [
    dcc.Markdown(
        '''
        ### Price-Based Indicator Strategies

        ---

        #### SMA Crossover

        The SMA crossover is the prototypical indicator strategy, and many of the strategies provided
        here build upon its core concept.

        Most indicators are mathematical functions, with the **Simple Moving Average** (SMA) being
        one of the most centrally important and simplest. An SMA with period $n$ is an equal-weighted
        average taken over the previous $n$ price values:

        $$
        SMA_n(x) = \\frac{1}{n} \\sum^{n}_{i=1} x_i \\: .
        $$

        Traditionally, closing prices are used within the context of finance. However, any set of
        real values will produce a real analytic function. As price points are progressively input
        into the function, across a selected date range, the value is updated by dropping the oldest
        price and adding the newest. Before $n$ price points have been input, the function is considered undefined.

        For an **SMA crossover strategy**, two SMAs with different periods are used. When the SMA with
        the shorter period or "fast SMA" crosses above the other "slow SMA", a buy/short-cover trade is placed
        and when it crosses below, a sell/short-sell trade is placed. The strategy generally seeks to
        capture the beginning of a longer trend and exit as it's ending.
        ''',
        mathjax=True
    ),
    dmc.Center([
        dmc.Image(
            src='assets/sma.jpeg',
            caption="An SMA crossover producing a buy signal. Source: Investopedia.com",
            alt="SMA crossover example",
            opacity=0.9,
            width='95%'
        )],
        style={'margin-left': '5%', 'margin-top': '18px', 'margin-bottom': '25px'}
    ),
    dcc.Markdown(
        '''
        ##### Things to Note:

        - The magnitude of the difference in the periods of the two SMAs will determine how sensitive
        the strategy is to price oscillations.
        * While untraditional, if the strategy is a losing one then the trade directions of the strategy
        can be inverted, and in theory, the returns.
        - For additional information, you can read the following
        [article on Investopedia.](https://www.investopedia.com/terms/g/goldencross.asp
        "Golden Cross Pattern Explained With Examples and Charts")

        &nbsp;

        #### EMA Crossover

        The EMA crossover applies the same trading rules for entering and exiting a position as the SMA
        crossover but with **Exponential Moving Averages** (EMAs) instead. An $n$ period EMA evaluated
        at the $i^{th}$ data point is calculated recursively as:

        $$
        EMA_n(x_i) = \\frac{2}{n+1} * x_i + (1-\\frac{2}{n+1}) * EMA_n(x_{i-1}) \\:,
        $$

        where $x_i$ is typically the closing price at point i. Since the period $n \\geq 1$, the weighting
        factor $0 < \\frac{2}{n+1} \\leq 1$. Thus, the most recent price value is always weighted more
        heavily than the previous EMA value. Since the function is calculated recursively, the contributions
        from older EMA values fall off in a compounding fashion. The initial value of the EMA is generally
        defined to be the initial price: $EMA_n(x_0)=x_0$.

        ##### Things to Note:

        - The EMA crossover is by design more sensitive to price oscillations than the SMA crossover.
        - Two EMAs will typically have more crossovers than two SMAs with the same periods.
        - Large and sudden price changes will be reflected more quickly in the EMA than in the SMA.

        &nbsp;

        #### MACD Crossover

        The **Moving Average Convergence Divergence** (MACD) is a classic indicator that can be used as
        part of a more complicated crossover strategy. It traditionally utilizes EMAs with periods
        9, 12, and 26 to derive two new functions: the **MACD line** and the **signal line**.
        The MACD line is the difference between the 12-period and 26-period EMAs:

        $$
        MACD_{12,26}(x_i) = EMA_{12}(x_i) - EMA_{26}(x_i) \\:.
        $$

        The signal line, denoted as $S(x)$, is the 9-period EMA of the MACD line:

        $$
        S(x_i) = EMA_{9}(MACD_{12,26}(x_i)) \\:.
        $$

        In other words, the MACD line is the total difference between two EMAs and the signal line is
        an exponentially weighted average of the recent differences between them. When the current
        difference between the EMAs is greater than the exponentially averaged recent differences,
        the MACD line will be above the signal line and vice versa.

        Although there are multiple common trade entry and exit principles based upon the MACD indicator,
        the most common is with crossovers. When the MACD line crosses above the signal line a
        buy/short-cover trade is placed and when it crosses below a sell/short-sell trade is placed.
        ''',
        mathjax=True,
        link_target="_blank"
    ),
    dmc.Center([
        dmc.Image(
            src='assets/macd.jpeg',
            caption="MACD and signal lines produced from a fast EMA (orange) and a slow EMA (blue). Source: Investopedia.com",
            alt="MACD example",
            opacity=0.9,
            width='95%'
        )],
        style={'margin-left': '5%', 'margin-top': '18px', 'margin-bottom': '25px'}
    ),
    dcc.Markdown(
        '''
        ##### Things to Note:

        - Since the MACD indicator uses EMAs and they have relatively short periods, the strategy can target
        a much shorter timeframe using the same price data than an SMA crossover can, for example.
        - A sharp change in price direction can create a crossover relatively quickly.
        - For additional information, you can read the following
        [article on Investopedia.](https://www.investopedia.com/terms/m/macd.asp
        "MACD Indicator Explained, with Formula, Examples, and Limitations")

        &nbsp;

        #### RSI

        The **Relative Strength Index** (RSI) is a momentum indicator intended to help identify
        overbought or oversold conditions. Generally, values above 70 may suggest that an asset is
        overbought and due for a downward correction, while values below 30 may suggest that an asset
        is oversold and due for an upward correction. To calculate the RSI one must first average
        the upward moves $U$ and the absolute value of the downward moves $D$ over the period of the
        indicator. There's more than one common choice for how the averages of $U$ and $D$ are taken,
        however, the historic choice is an exponential moving average with period 14. For a period
        $n$, the average of the upward price movements at point $i$ would be calculated recursively as

        $$
        U_{i}(x) = \\frac{1}{n} * x_i + \\frac{n-1}{n} * U_{i-1}(x) \\:,
        $$

        where $x_i$ is the change in price at data point $i$. The downward price movements are calculated
        the same but using the absolute values to obtain a positive value. The RSI is then calculated as

        $$
        RSI = 100 - \\frac{100}{1 + \\dfrac{U}{D}} \\:.
        $$

        It's straightforward to show that the RSI is bounded from below at 0: given $U$ and $D$ are
        positive, the RSI is minimized by $U=0$ resulting in $RSI=0$ . This occurs when there are
        only downward moves within the indicator period. The upper bound is defined to be 100 if $D=0$ ,
        given the RSI would be undefined otherwise. This is a sensible choice, given in the limit that
        $D \\rightarrow 0$ , $RSI \\rightarrow 100$ . The image below is an example of RSI plotted under
        a price chart.
        ''',
        mathjax=True,
        link_target="_blank"
    ),
    dmc.Center([
        dmc.Image(
            src='assets/rsi.png',
            caption="RSI plotted below a price chart. Source: Investopedia.com",
            alt="RSI example",
            opacity=0.9,
            width='95%'
        )],
        style={'margin-left': '5%', 'margin-top': '18px', 'margin-bottom': '25px'}
    ),
    dcc.Markdown(
        '''
        For more information on how to contextually use RSI values, you can read the following
        [article on Investopedia.](https://www.investopedia.com/terms/r/rsi.asp
        "Relative Strength Index (RSI) Indicator Explained With Formula")
        ''',
        link_target="_blank"
    )
]

# Used to create the Data Selection, Window Splitting, and Strategy Details headings with info modals.
def sidebar_label(label_text, label_id, modal_children, modal_id, icon_id,
                  styling={'margin-left': '25px', 'margin-bottom': '10px'}):
    return dbc.Stack(
        [
            dmc.Text(
                label_text,
                variant='gradient',
                gradient={'from': '#52b1ff', 'to': '#739dff', 'deg': 45},
                style={'margin-left': 'auto', 'font-size': '22px'},
                id=label_id
            ),
            html.Div(
                [
                    dmc.Modal(
                        children=modal_children,
                        centered=True,
                        zIndex=100,
                        size='xl',
                        id=modal_id
                    ),
                    dmc.ActionIcon(
                        DashIconify(icon='ri:question-mark', width=18, height=15),
                        color='dark',
                        size='sm',
                        radius='xl',
                        variant='filled',
                        style={'margin-bottom': '2px'},
                        id=icon_id
                    )
                ],
                style={'margin-right': 'auto'}
            )
        ],
        direction='horizontal',
        gap=2,
        style=styling
    )

data_label = sidebar_label("Data Selection", 'data_label_text', data_modal_children, 'modal_1', 'icon_1',
                           {'margin-left': '25px', 'margin-top': '10px', 'margin-bottom': '10px'})

window_label = sidebar_label("Window Splitting", 'window_label_text', window_modal_children, 'modal_2', 'icon_2')

strategy_label = sidebar_label("Strategy Details", 'strategy_label_text', strategy_modal_children, 'modal_3', 'icon_3')
