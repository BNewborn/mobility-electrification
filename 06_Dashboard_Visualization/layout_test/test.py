import dash
import copy
from dash import Dash, dcc, html, Input, Output, ClientsideFunction
import plotly.graph_objects as go
import plotly.express as px
import dash_daq as daq
import pandas as pd
import numpy as np
from pandas.api.types import CategoricalDtype


app = dash.Dash(
    __name__,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
app.title = "TECNYC"

server = app.server
app.config.suppress_callback_exceptions = True


side_bar = html.Div(
            className="side_bar",
            children=[
                html.Img(src=app.get_asset_url("NYU_Short_RGB_Color.png")),
                ]
        )


app.layout = html.Div([
    side_bar,
    dcc.Tabs(
        id="tabs-with-classes",
        value='tab-1',
        parent_className='custom-tabs',
        className='custom-tabs-container',
        children=[
            dcc.Tab(
                label='MAIN',
                value='tab-1',
                className='custom-tab',
                selected_className='custom-tab--selected'
            ),
            dcc.Tab(
                label='DETAIL',
                value='tab-2',
                className='custom-tab',
                selected_className='custom-tab--selected'
            ),
            dcc.Tab(
                label='MODEL',
                value='tab-3', className='custom-tab',
                selected_className='custom-tab--selected'
            ),
        ]),
    html.Div(id='tabs-content-classes', className="tab_contents")
], className="app_container")

@app.callback(Output('tabs-content-classes', 'children'),
              Input('tabs-with-classes', 'value'))
def render_content(tab):
    if tab == 'tab-1':
        return html.Div([
            html.Div([html.H3('MAP')], className="map card_container"),
            html.Div([html.H3('ENERGY')], className="energy card_container"),
            html.Div([html.H3('COLOR + INTRO')], className="color_plus_intro card_container"),
            html.Div([html.H3('SHARE')], className="share card_container"),
            html.Div([html.H3('REGION')], className="region card_container"),
        ],className="tab1_content")
    elif tab == 'tab-2':
        return html.Div([
            html.Div([html.H3('MAP')], className="map card_container"),
            html.Div([html.H3('ENERGY')], className="energy card_container"),
            html.Div([html.H3('FLOW')], className="flow card_container"),
            html.Div([html.H3('FLAG')], className="flag card_container"),
            html.Div([html.H3('SHARE')], className="share card_container"),
            html.Div([html.H3('REGION')], className="region card_container"),
        ],className="tab2_content")
    elif tab == 'tab-3':
        return html.Div([
            html.Div([html.H3('COMMUTER MODEL')], className="commuter_model card_container"),
            html.Div([html.H3('ELECTRICAL MODEL')], className="electrical_model card_container"),
        ],className="tab3_content")


# Run the server
if __name__ == "__main__":
    app.run_server(debug=True)