from dash import Dash, dcc, html, Input, Output
import dash_daq as daq
import plotly.express as px
import pandas as pd

app = Dash(__name__)

### Where the electric model df_agg pickles are:
save_dir = "../electric_model_outputs"

# # Read in the electric models
# electric_model_1 = pd.read_pickle(f"{save_dir}/electric_model_1_dfaggregate.pkl")
# electric_model_2 = pd.read_pickle(f"{save_dir}/electric_model_2_dfaggregate.pkl")
# electric_model_3 = pd.read_pickle(f"{save_dir}/electric_model_3_dfaggregate.pkl")

electric_model_1 = pd.read_pickle(f"{save_dir}/electric_model_alltransit_dfaggregate.pkl")
electric_model_2 = pd.read_pickle(f"{save_dir}/electric_model_allmicro_dfaggregate.pkl")
electric_model_3 = pd.read_pickle(f"{save_dir}/electric_model_mix_dfaggregate.pkl")

df = pd.read_csv('https://plotly.github.io/datasets/country_indicators.csv')


available_electric_models = {"Electric Model 1 - Max Transit":electric_model_1
                             ,"Electric Model 2 - Max Micro-mobility":electric_model_2
                             ,"Electric Model 3 - Mix of Everything":electric_model_3}

charging_time_method = sorted(electric_model_1.PEV_DELAY.dropna().unique())
trans_methods = sorted(electric_model_1.TransMode.dropna().unique())


###### Electricity Consumption in NYC
# https://engineering.mit.edu/engage/ask-an-engineer/how-many-wind-turbines-would-it-take-to-power-all-of-new-york-city/
# The city’s five boroughs, plus Westchester, consumed around 
# 60 thousand gigawatt-hours of electricity last year, according to ConEdison. 
# That’s 60 billion kilowatt-hours a year.

# 60 billion / 365 = 164mm kilowatt hours per day in region
# 164 * 20% (rough estimate) = 32,800,000 kwh per day in Manhattan


# print(available_electric_models.keys())

app.layout = html.Div(children=[   
    html.Div([
            dcc.RadioItems(
                list(available_electric_models.keys()),
                list(available_electric_models.keys())[0],
                id='electric_model_of_choice_idx'
            ),
            dcc.Dropdown(
                charging_time_method,
                "Earliest",
                id='pev_delay_choice'
            ),
            daq.BooleanSwitch(
                    id='include_manhattan_consumption'
                    ,label='Include estimated Manhattan electricity consumption?'
                    , on=False),
            # ,
            # dcc.Checklist(
            #     options=trans_methods,
            #     value=trans_methods,
            #     id='trans_mode_choice',
            #     inline=True
            # )
        ], style={'display': 'inline-block'})
    ,html.Div(dcc.Graph(id='indicator-graphic'))
    ,html.Div(id='total_kwh_daily')
    ])



@app.callback(
    Output('indicator-graphic', 'figure'),
    Output('total_kwh_daily','children'),
    Input('electric_model_of_choice_idx','value'),
    Input('pev_delay_choice', 'value'),
    Input('include_manhattan_consumption','on')
    # Input('trans_mode_choice', 'value')
    )
def update_electricity_graph(electric_model_of_choice_idx,pev_delay_choice,include_manhattan_consumption):
    # trans_mode_choice
    # print(f"Electric model of choice",electric_model_of_choice_idx,available_electric_models[electric_model_of_choice_idx].shape)
    # print(f"TransModels of choice",trans_mode_choice)
    df_plot = available_electric_models[electric_model_of_choice_idx]
    # df_plot = df_plot[df_plot['TransMode'].isin(trans_mode_choice)]
    # print(df_plot.head(5))
    df_plot = df_plot[df_plot["PEV_DELAY"]==pev_delay_choice]
    gb_plot = df_plot.groupby(by=["Charge_Hour","TransMode"]).agg({"Energy":"sum"}).reset_index()
    # print(gb_plot)

    total_kwh = gb_plot.Energy.sum()

    # print(f"manhattan energy consumption: {include_manhattan_consumption}")

    
    fig = px.line(gb_plot,x='Charge_Hour',y='Energy',color='TransMode'\
        ,labels=dict(Charge_Hour="Hour of Day", TransMode="Mode of Transit", Energy="Total kWH"))
    fig.update_yaxes(ticklabelposition="inside top", title=None)

    if include_manhattan_consumption:
        # gb_plot["Energy"] = gb_plot["Energy"] + 32800000
        fig.add_hline(y=32800000/24) #estimated kwh daily in Manhattan hourly  


    #### ToDo: Maybe somebody else can figure out the right distribution of kwh by hour for Manhattan?

    return fig,f"Total kwh added by the electric commute for 1 day: {round(total_kwh):,}"




if __name__ == '__main__':
    app.run_server(debug=True)
