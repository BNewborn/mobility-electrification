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

layout = dict(
    # autosize=True,
    # automargin=True,
    height=320,
    margin=dict(l=35, r=20, b=20, t=20),
    hovermode="closest",
    plot_bgcolor="rgba(0, 0, 0, 0)",
    paper_bgcolor="rgba(0, 0, 0, 0)",
    legend=dict(font=dict(size=10), orientation="h", y=-0.15),
    # title="Satellite Overview"
)

### read the orginal data
save_dir = "./commuter_model_outputs"
commuter_model_1 = pd.read_pickle(f"{save_dir}/commuter_model_alltransit_dfaggregate.pkl")
commuter_model_2 = pd.read_pickle(f"{save_dir}/commuter_model_allmicro_dfaggregate.pkl")
commuter_model_3 = pd.read_pickle(f"{save_dir}/commuter_model_mix_dfaggregate.pkl")
subregion_reference = pd.read_csv(f"{save_dir}/subregion_reference_table.csv",index_col=0)
location_test = pd.read_csv(f"{save_dir}/location_test.csv",index_col=0)

save_dir_e = "./electric_model_outputs/old_version"
electric_model_1 = pd.read_pickle(f"{save_dir_e}/electric_model_alltransit_dfaggregate.pkl")
electric_model_2 = pd.read_pickle(f"{save_dir_e}/electric_model_allmicro_dfaggregate.pkl")
electric_model_3 = pd.read_pickle(f"{save_dir_e}/electric_model_mix_dfaggregate.pkl")

### pre-processing, helper functions
mode_dict_1 = {'Auto, truck, or van':'Autos',
               'Long-distance train or commuter train':'CommuterRail',
               'Subway or elevated':'Subway',
               'Walked only':'Walk',
               'Light rail, streetcar, or trolley (Carro público in PR)':'Other',
               'Ferryboat':'Ferry',
               'Worked at home':'WFH',
              }
mode_dict_2 = {'AutoOccupants':'Autos', 'No option':'Other'}
mode_dict_3 = {'Other':'Other',
               'WFH':'WFH',
               'CommuterRail':'Transit',
               'Autos':'Car',
               'Bicycle':'Micro',
               'Bus':'Transit',
               'Ferry':'Transit',
               'Subway':'Transit',
               'Taxicab':'Car',
               'Motorcycle':'Car',
               'Walk':'Micro',
               'Escooter':'Micro',
              }
def df_processing(df):    
    df = df[df['COMMUTE_DIRECTION_MANHATTAN']=='in']
    df = df.merge(right=subregion_reference, on=["PUMAKEY_HOME"])
    df['LEAVE_WORK_HOUR'] = (df['ARRIVES_AT_WORK_HOUR'] + np.ceil(df['HRS_WK_DAILY']).astype(int))%24
    df['Current'] = df["MODE_TRANSP_TO_WORK"].replace(mode_dict_1)
    df['Reassigned'] = df["First_Assignment"].replace(mode_dict_2)
    df['Current_Parent'] = df["Current"].replace(mode_dict_3)
    df['Reassigned_Parent'] = df["Reassigned"].replace(mode_dict_3)
    df['MNY_RES'] = df['PUMAKEY_HOME'].apply(lambda x: 1 if x.startswith('36_038') else 0)
    df['distance_row_sum'] = df['DISTANCE_KM']*df['PERWT']
    return df


def flag_assign(df):
    flags = [c for c in commuter_model_3 if c.startswith('FLAG_')]
    data=[['Autos',df[df['FLAG_AUTO']==1]['PERWT'].sum()],
          ['Bicycle',df[df['FLAG_EBIKE']==1]['PERWT'].sum()],
          ['Bus',df[df['FLAG_EBUSES']==1]['PERWT'].sum()],
          ['CommuterRail',df[df['FLAG_COMMUTERRAIL']==1]['PERWT'].sum()],
          ['Ferry',df[df['FLAG_FERRY']==1]['PERWT'].sum()],
          ['Motorcycle',df[df['FLAG_MOTORCYCLE']==1]['PERWT'].sum()],
          ['Subway',df[df['FLAG_SUBWAY']==1]['PERWT'].sum()],
          ['Taxicab',df[df['FLAG_TAXICAB']==1]['PERWT'].sum()],
          ['WFH',df[df['FLAG_WFH']==1]['PERWT'].sum()],
          ['Walk',df[df['FLAG_WALK']==1]['PERWT'].sum()],
          ['Escooter',df[df['FLAG_ESCOOTER']==1]['PERWT'].sum()]]
    flag_df = pd.DataFrame(data, columns=['Mode','Eligible'])
    Reassigned = df.groupby(by=["Reassigned"]).agg({"PERWT":"sum"}).reset_index()\
                   .rename({'Reassigned':'Mode','PERWT':'Reassigned'},axis=1)
    flag_df = flag_df.merge(right=Reassigned, on=["Mode"], how='outer').fillna(0)
    flag_df.sort_values('Eligible',inplace=True)  
    return flag_df


def subregion(df):
    subregion = df.groupby(by=["Subregion","Reassigned"]).agg({"PERWT":"sum"}).reset_index()
    order = CategoricalDtype(['Mid Hud','CT','Outer NJ','Low Hud','LI',
                              'Inner NJ','Non-MNY Boroughs','Manhattan'],ordered=True)
    subregion['Subregion'] = subregion['Subregion'].astype(order)
    subregion.sort_values('Subregion',inplace=True)
    return subregion

def traffic_flow(df):
    in_agg = df.rename({'ARRIVES_AT_WORK_HOUR':'Hour'},axis=1)\
               .groupby(by=["Hour"]).agg({"PERWT":"sum"}).reset_index().astype(int)
    in_agg['Dir'] = 'in'
    out_agg = df.rename({'LEAVE_WORK_HOUR':'Hour'},axis=1)\
                .groupby(by=["Hour"]).agg({"PERWT":"sum"}).reset_index().astype(int)
    out_agg['Dir'] = 'out'
    flow = pd.concat([in_agg, out_agg])
    return flow


def e_profile_hold_space(df):
    e_tmp_profile = df[df['FLOW_DIR']!='ALL']
    e_tmp_profile = e_tmp_profile.groupby(by=["Charge_Hour","PEV_DELAY"]).agg({"Energy":"sum"}).reset_index()
    e_tmp_profile['Energy'] = e_tmp_profile['Energy']/1000
    return e_tmp_profile

commuter_model_1 = df_processing(commuter_model_1)
commuter_model_2 = df_processing(commuter_model_2)
commuter_model_3 = df_processing(commuter_model_3)


### 
available_commuter_models = {"Max Transit":commuter_model_1,
                             "Max Micro-mobility":commuter_model_2, 
                             "Mix of Everything":commuter_model_3}
available_electric_models = {"Max Transit":electric_model_1,
                             "Max Micro-mobility":electric_model_2,
                             "Mix of Everything":electric_model_3}

charging_time_method = sorted(electric_model_1.PEV_DELAY.dropna().unique())




def description_card():
    """

    :return: A Div containing dashboard title & descriptions.
    """
    return html.Div(
        id="description-card",
        children=[
            html.Br(),
            html.H5("The Electric Commute"),
            html.H3("Envisioning 100% Electrified Mobility in New York City"),
            html.P("Explore the ramifications of a 100% electric commute in New York City. Select any of the preset scenarios or click Customize to envision your own 100% e-Mobility."),
            html.Br(),
        ],
    )

def generate_control_card():
    """
    :return: A Div containing controls for graphs.
    """
    return html.Div(
        id="control-card",
        children=[
            html.P("Select One Scenario"),
            dcc.RadioItems(
                list(available_commuter_models.keys()),
                list(available_commuter_models.keys())[0],
                id='commuter_model_of_choice_idx',
            ),
            dcc.RadioItems(
                ["Customize (placeholder)"], id='Customize',
            ),
            html.Br(),
            html.P("Tavel Modes Constraints (placeholder)"),
            dcc.Dropdown(
                id="mode-limit-select",
                options=["Limit one","Limit two","Limit three"],
                value="Limit one",
                multi=False,
            ),
            html.Br(),
            html.P("Charging Preferences (placeholder)"),
            dcc.Dropdown(
                id="charge-prefer-select",
                options=["Limit one","Limit two","Limit three"],
                value="Limit one",
                multi=False,
            ),          
            html.Br(),
            html.P("Micro-Mobility Region (placeholder)"),
            dcc.Dropdown(
                id="friendly_region",
                options=["NYC","NJ","LI","HH","HHH"],
                multi=True,
                value=["NYC","NJ","LI"],
                className="dcc_control",
            ), 
            html.Br(),
            html.A(html.Button("Custom", id="simulate")),
        ],
    )


app.layout = html.Div(
    id="app-container",
    # style={"display": "flex", "flex-direction": "column"},
    children=[
        # Banner
        html.Div(
            id="banner",
            className="banner",
            children=[html.Img(src=app.get_asset_url("NYU_Short_RGB_Color.png"))],
        ),
        # Left column
        html.Div(
            id="left-column",
            className="three columns",
            children=[description_card()
            , generate_control_card()
            ]
        ),
        
        # 1st row
        html.Div(
            id="first_row",
            className="row flex-display",
            children=[
                # map panel
                html.Div(
                    id="traffic_card",
                    className="pretty_container six columns",
                    children=[
                        html.B("Manhattan Workers’ Place of Residence by Travel Mode (+input)"),
                        dcc.Graph(id="map_graphic"),
                    ],
                ),
                # electrical panel (info)
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [html.H6(id="total_energy_text"), html.P("Daily Energy")],
                                    id="wells",
                                    className="mini_container",
                                ),
                                html.Div(
                                    [html.H6(id="peak_power_text"), html.P("Peak Load")],
                                    id="gas",
                                    className="mini_container",
                                ),
                                html.Div(
                                    [html.H6(id="add_energy_text"), html.P("Add. Load")],
                                    id="oil",
                                    className="mini_container",
                                ),
                            ],
                            id="info-container",
                            className="row container-display",
                        ),

                        html.Div(
                            [
                                html.B("Energy Profile of Manhattan's Home-Work Commuting Activities"),
                                
                                html.Div(
                                    [
                                        html.Br(),
                                        html.Div([html.Label(['Details: '])],style=dict(width='7%',display='inline-block',verticalAlign='top')),
                                        html.Div([daq.BooleanSwitch(id='Detailed',on=False)],style=dict(width='20%',display='inline-block',height='15px',verticalAlign='top')),
                                        html.Div([html.Label(['Delay Type: '])],style=dict(width='20%',display='inline-block',verticalAlign='top')),
                                        html.Div([dcc.Dropdown(charging_time_method,"Random",id='pev_delay_choice')],style=dict(width='30%',display='inline-block',height='10px',verticalAlign='top')),
                                    ],
                                ),
                                dcc.Graph(id="electric_graphic")
                            ],
                            className="pretty_container",
                        ),
                    ],
                    id="electrical_card",
                    className="six columns"
                ),
            ],
        ),

        # 2nd row
        html.Div(
            id="second_row",
            className="row flex-display",
            children=[
                # traffic flow
                html.Div(
                    id="flow_card",
                    className="pretty_container four columns",
                    children=[
                        html.B("Traffic Flow (+OnRoadFlow)"),
                        dcc.Graph(id="flow_graphic"),
                    ],
                ),
                # eligible vs assign
                html.Div(
                    id="eligible_card",
                    className="pretty_container four columns",
                    children=[
                        html.B("Eligible vs Assigned"),
                        dcc.Graph(id="eligible_graphic"),
                    ],
                ),
                # compare share
                html.Div(
                    id="share_card",
                    className="pretty_container four columns",
                    children=[
                        html.B("Share of Modes"),
                        dcc.Graph(id="share_graphic"),
                    ],
                ),
                # subregion
                html.Div(
                    id="subregion_card",
                    className="pretty_container four columns",
                    children=[
                        html.B("Subregion (+legend)"),
                        dcc.Graph(id="subregion_graphic"),
                    ],
                ),                
            ],
        ),
    ],
)

@app.callback(
    Output('map_graphic', 'figure'),
    Input('commuter_model_of_choice_idx','value'),
    )
def update_map_graph(commuter_model_of_choice_idx):
    fig = px.scatter_mapbox(location_test, 
                            lat="lat", lon="lon", hover_name="TransMode", color="TransMode", 
                            size="PERWT", 
                            size_max=7, 
                            height=420,
                            )
    fig.update_layout(mapbox_style="carto-positron")
    # fig.update_layout(mapbox_style="carto-darkmatter")
    fig.update_layout(margin={"r":0,"t":20,"l":0,"b":0})
    fig.update(layout_showlegend=False)
    return fig


@app.callback(
    [
        Output("total_energy_text", "children"),
        Output("peak_power_text", "children"),
        Output("add_energy_text", "children"),
    ],
    Input("commuter_model_of_choice_idx", "value"),
)
def update_text(commuter_model_of_choice_idx):
    com_df = available_electric_models[commuter_model_of_choice_idx]
    e_tmp_profile = e_profile_hold_space(com_df)
    a = str(int(e_tmp_profile[e_tmp_profile['PEV_DELAY']=='Random']['Energy'].sum()))
    b = str(int(e_tmp_profile['Energy'].max()))
    filter_e = (~com_df['TransMode'].isin(['Subway','CommuterRail']))&(com_df['PEV_DELAY']=='Random')
    c = str(int(com_df[filter_e]['Energy'].sum()/1000))
    return a + " MWh", b + " MW", c + " MWh"
# Earliest
# Random

@app.callback(
    Output('electric_graphic', 'figure'),
    [Input('commuter_model_of_choice_idx','value'),
    Input('Detailed','on'),
    Input('pev_delay_choice', 'value')],
    )
def update_electric_graph(commuter_model_of_choice_idx,Detailed,pev_delay_choice):
    com_df = available_electric_models[commuter_model_of_choice_idx]
    e_tmp_profile = e_profile_hold_space(com_df)
    fig = px.line(e_tmp_profile, x='Charge_Hour', y='Energy', color='PEV_DELAY', height=250, markers=True,
                  labels=dict(Charge_Hour="Time of day (hr)", TransMode="Travel Mode", Energy="Power (MW)", PEV_DELAY="Delay Type"))
    fig.update_xaxes(range = [0,23])
    fig.update_yaxes(range = [0,1000])

    layout_elec = copy.deepcopy(layout)
    layout_elec["height"] = 250
    fig.update_layout(layout_elec)
    fig.update_layout(xaxis_title=None)

    if Detailed:
        df_plot = available_electric_models[commuter_model_of_choice_idx]
        df_plot = df_plot[df_plot["PEV_DELAY"]==pev_delay_choice]
        df_plot['Energy'] = df_plot['Energy']/1000
        df_plot['TransMode'] = df_plot['TransMode'].astype("string")
        gb_plot = df_plot.groupby(by=["Charge_Hour","TransMode"]).agg({"Energy":"sum"}).reset_index()
        fig = px.area(gb_plot,x='Charge_Hour',y='Energy',color='TransMode',height=250, markers=False, 
                      labels=dict(Charge_Hour="Hour of Day", TransMode="Travel Mode", Energy="Power (MW)"))
        fig.update_xaxes(range = [0,23])
        fig.update_yaxes(range = [0,1000])
        # fig.add_hline(y=1e3)
        fig.update_layout(layout_elec)
        fig.update_layout(xaxis_title=None)
        
    return fig


@app.callback(
    Output('flow_graphic', 'figure'),
    Input('commuter_model_of_choice_idx','value'),
    )
def update_flow_graph(commuter_model_of_choice_idx):
    com_df = available_commuter_models[commuter_model_of_choice_idx]
    flow = traffic_flow(com_df)
    in_df = flow[flow['Dir']=='in']
    out_df = flow[flow['Dir']=='out']
    index = in_df.Hour.to_list()
    in_flow = in_df.PERWT.to_list()
    out_flow = out_df.PERWT.to_list()
    layout_flow = copy.deepcopy(layout)
    data = [
        dict(
            type="scatter",
            mode="lines",
            name="In",
            x=index,
            y=in_flow,
            line=dict(shape="spline", smoothing="2", color="#F9ADA0"),
        ),
        dict(
            type="scatter",
            mode="lines",
            name="Out",
            x=index,
            y=out_flow,
            line=dict(shape="spline", smoothing="2", color="#849E68"),
        ),
    ]
    fig = dict(data=data, layout=layout_flow)
    return fig


@app.callback(
    Output('eligible_graphic', 'figure'),
    Input('commuter_model_of_choice_idx','value'),
    )
def update_map_graph(commuter_model_of_choice_idx):
    com_df = available_commuter_models[commuter_model_of_choice_idx]
    flag_df = flag_assign(com_df)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=flag_df.Mode.to_list(),
        x=flag_df.Eligible.to_list(),
        name='Eligible',
        orientation='h',
        marker=dict(
            color='rgba(100, 100, 100, 0.5)')
        )
    )
    fig.add_trace(go.Bar(
        y=flag_df.Mode.to_list(),
        x=flag_df.Reassigned.to_list(),
        name='Assigned',
        orientation='h',
        marker=dict(
            color='#966FD6')
        )
    )
    fig.update_layout(barmode='overlay')
                 
    layout_flag = copy.deepcopy(layout)
    fig.update_layout(layout_flag)
    fig.update_layout(yaxis_title=None,xaxis_title=None)
    fig.update_layout(showlegend=False)
    return fig


@app.callback(
    Output('share_graphic', 'figure'),
    Input('commuter_model_of_choice_idx','value'),
    )
def update_share_graph(commuter_model_of_choice_idx):

    com_df = available_commuter_models[commuter_model_of_choice_idx]
    share_df = com_df.groupby(by=["Reassigned","Reassigned_Parent"]).agg({"PERWT":"sum"}).reset_index()\
                .rename({'Reassigned':'Mode','Reassigned_Parent':'Mode_Parent'},axis=1)
    share_df['ALL'] = 'Share of Modes'
    fig = px.sunburst(share_df, path=['ALL','Mode_Parent','Mode'], values='PERWT', height=350)

    layout_share = copy.deepcopy(layout)
    fig.update_layout(layout_share)
    fig.update_traces(marker_line_color='white',marker_line_width=1)
    return fig


@app.callback(
    Output('subregion_graphic', 'figure'),
    Input('commuter_model_of_choice_idx','value'),
    )
def update_subregion_graph(commuter_model_of_choice_idx):
    
    com_df = available_commuter_models[commuter_model_of_choice_idx]
    gb_plot = subregion(com_df)
    fig = px.bar(gb_plot, x="PERWT", y="Subregion", color='Reassigned', 
                 orientation='h',
                 hover_data=["Reassigned", "PERWT"],
                 height=350)
    layout_subregion = copy.deepcopy(layout)
    fig.update_layout(layout_subregion)
    fig.update_layout(yaxis_title=None,xaxis_title=None)
    fig.update_layout(showlegend=False)
    return fig



# Run the server
if __name__ == "__main__":
    app.run_server(debug=True)
