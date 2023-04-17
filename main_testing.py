from dash import Dash, html, dcc, Input, Output, dash_table
import dash_bootstrap_components as dbc
from dash_bootstrap_components.themes import DARKLY
import plotly.graph_objects as go
import vectorbt as vbt
import yfinance

from src.components.calendar import date_calendar
from src.components.dropdowns import asset_dropdown, timeframe_dropdown, metric_dropdown
from src.components.choose_strat import form, strategy_dropdown
from src.components.choose_window import nwindows_input, insample_dropdown
#from . tabs import parameters_tabs

dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"

app = Dash(__name__, external_stylesheets=[DARKLY, dbc_css])

server = app.server

####Layout Formating#####
app_heading = html.H3("Backtesting Parameter Optimization", style={'textAlign': 'center', 'color': '#7FDBFF'})

#price_plot = dcc.Loading(children=[html.Div(id="plot_div")], type="circle")
price_plot = dcc.Loading(type="circle", id='plot_div')

data_button = dbc.Button(
    "Load Data",
    id='load_data_button',
    color='info',
    size='lg',
    className='mr-1',
    n_clicks=0
)

main_row = html.Div(
    [   
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Row(asset_dropdown),
                        dbc.Row(timeframe_dropdown),
                        dbc.Row(date_calendar),
                        dbc.Row(nwindows_input),
                        dbc.Row(insample_dropdown),
           #         ]
          #      ),
        #        dbc.Col(
         #           [
                        dbc.Row(strategy_dropdown),
                        dbc.Row(form),
                        dbc.Row(metric_dropdown)
                    ]
                ),
                dbc.Col(
                    [
                        price_plot
                    ]
                )
            ]
        )
    ]
)

app.layout = html.Div(
    [
        app_heading,
        main_row
    ]
)

# Data callback
@app.callback(
        Output('plot_div', 'children'),
    [
        Input('timeframe', 'value'),
        Input('asset', 'value'),
        Input('date_range', 'start_date'),
        Input('date_range', 'end_date')
    ]
)
def make_table(selected_timeframe, selected_asset, start_date, end_date):    
    df = yfinance.download(
        tickers=selected_asset, 
        start=start_date, 
        end=end_date, 
        interval=selected_timeframe
    )
    df.drop(columns = ['Adj Close'], inplace = True)
    df.columns = ['open', 'high', 'low', 'close', 'volume']

    if df.empty:
        return dbc.Alert(
            "You have requested too large of a date range for your selected timeframe. "
            "For Yahoo Finance 15m data is only available within the last 60 days. "
            "1h data is only available within the last 730 days. ",
            id='alert',
            dismissable=True,
            color='danger'
        )
    else:
        if selected_timeframe=='1d':
            breaks = dict(bounds=['sat', 'mon'])
        else:
            breaks = dict(bounds=[16, 9.5], pattern='hour') #intraday chart needs hour rangebreaks

        fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['open'], high=df['high'], low=df['low'], close=df['close'])])
        fig.update_layout(
            xaxis=dict(rangeslider=dict(visible=False)),
            plot_bgcolor='rgba(0,50,90,100)', 
            paper_bgcolor='rgba(0,50,90,10)',
            font_color='white',
            margin=dict(l=20, r=20, t=20, b=20))
        fig.update_xaxes(
            rangebreaks=[dict(bounds=['sat', 'mon']), breaks],
            gridcolor='rgba(20,20,90,100)')
        fig.update_yaxes(gridcolor='rgba(20,20,90,100)', automargin=True)
        return dcc.Graph(figure=fig)


# Strategy callback
@app.callback(
    Output('strategy_form', 'children'),
    Input('strategy_drop', 'value')
)
def update_strategy_children(selected_strategy):
    if selected_strategy == 'SMA Crossover':
        return html.Div(
            [
                dbc.Label("minimum period of the first SMA (10-210)"),
                dbc.Input(type='number', value=50, min=10, max=210, step=1),
                dbc.Label("maximum period of the first SMA (10-210)"),
                dbc.Input(type='number', value=100, min=10, max=210, step=1),
                dbc.Label("minimum period of the second SMA (10-210)"),
                dbc.Input(type='number', value=50, min=10, max=210, step=1),
                dbc.Label("maximum period of the second SMA (10-210)"),
                dbc.Input(type='number', value=100, min=10, max=210, step=1)
            ],
            className="dbc"
        )
    elif selected_strategy == 'EMA Crossover':
        return html.Div(
            [
                dbc.Label("minimum period of the first EMA (10-210)"),
                dbc.Input(type='number', value=50, min=10, max=210, step=1),
                dbc.Label("maximum period of the first EMA (10-210)"),
                dbc.Input(type='number', value=100, min=10, max=210, step=1),
                dbc.Label("minimum period of the second EMA (10-210)"),
                dbc.Input(type='number', value=50, min=10, max=210, step=1),
                dbc.Label("maximum period of the second EMA (10-210)"),
                dbc.Input(type='number', value=100, min=10, max=210, step=1)
            ],
            className="dbc"
        )
    
    elif selected_strategy == 'RSI':
        return html.Div(
            [
                dbc.Label("minimum entry value for the RSI (10-40)"),
                dbc.Input(type='number', value=20, min=10, max=40, step=1),
                dbc.Label("maximum entry value for the RSI (20-50)"),
                dbc.Input(type='number', value=40, min=20, max=50, step=1),
                dbc.Label("minimum exit value for the RSI (50-80)"),
                dbc.Input(type='number', value=60, min=50, max=80, step=1),
                dbc.Label("maximum exit value for the RSI (60-99)"),
                dbc.Input(type='number', value=80, min=60, max=99, step=1)
            ],
            className='dbc'
        )
    
    elif selected_strategy == 'MACD':
        return html.Div(
            [
                dbc.Label("Choose a window for the MACD"),
                dcc.Dropdown(options=['5','10','20','50','100'], value='5', id='macd_window'),
            ],
            className="dbc"
        )
    

if __name__ == '__main__':
    app.run_server(debug=True, port=8061)



# Code for the optimization results table

# return dash_table.DataTable(
# data = df.to_dict('records'), 
# columns = [{"name": i, "id": i,} for i in (df.columns)],
# style_header={
#     'backgroundColor': 'rgb(30, 30, 30)',
#     'color': 'white'
# },
# style_data={
#     'backgroundColor': 'rgb(50, 50, 50)',
#     'color': 'white'
# },
# style_as_list_view=True
# )