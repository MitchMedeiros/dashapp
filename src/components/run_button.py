import dash_bootstrap_components as dbc

run_strategy_button = dbc.Button(
    "Load Data",
    id='load_data_button',
    color='info',
    size='lg',
    n_clicks=0
)