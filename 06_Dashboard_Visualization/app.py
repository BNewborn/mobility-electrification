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
    height=320,
    # margin=dict(l=35, r=20, b=20, t=20),
    margin=dict(l=10, r=10, b=10, t=10),
    hovermode="closest",
    plot_bgcolor="rgba(0, 0, 0, 0)",
    paper_bgcolor="rgba(0, 0, 0, 0)",
    legend=dict(font=dict(size=10), orientation="h", y=-0.15),
    yaxis = dict(tickfont = dict(size=10)),
    xaxis = dict(tickfont = dict(size=10)),
    legend_title_text = "",
)


color__dict = {'Bus':'#636EFA',
               'Motorcycle':'#EF553B',
               'CommuterRail':'#00CC96',
               'Subway':'#AB63FA',
               'Escooter':'#FFA15A',
               'Ferry':'#19D3F3',
               'Autos':'#FF6692',
               'AutoOccupants':'#FF6692',
               'Walk':'#B6E880',
               'Taxicab':'#FF97FF',
               'Bicycle':'#FECB52',
               'Other':'#7F7F7F',
               'WFH':'#72B7B2',
               }

#########################################
#######  read the orginal data  #########
#########################################

save_dir = "./electric_model_outputs_WFHTransitCombos"
commuter_fname = "commuter_model_ipums_df.pkl"
electric_fname = "electric_model_df_aggregate.pkl"

commuter_model_1 = pd.read_pickle(f"{save_dir}/HighWFH_Mix/{commuter_fname}")
commuter_model_2 = pd.read_pickle(f"{save_dir}/HighWFH_Transit/{commuter_fname}")
commuter_model_3 = pd.read_pickle(f"{save_dir}/HighWFH_Micro/{commuter_fname}")
commuter_model_4 = pd.read_pickle(f"{save_dir}/MidWFH_Mix/{commuter_fname}")
commuter_model_5 = pd.read_pickle(f"{save_dir}/MidWFH_Transit/{commuter_fname}")
commuter_model_6 = pd.read_pickle(f"{save_dir}/MidWFH_Micro/{commuter_fname}")
commuter_model_7 = pd.read_pickle(f"{save_dir}/NoWFH_Mix/{commuter_fname}")
commuter_model_8 = pd.read_pickle(f"{save_dir}/NoWFH_Transit/{commuter_fname}")
commuter_model_9 = pd.read_pickle(f"{save_dir}/NoWFH_Micro/{commuter_fname}")

subregion_reference = pd.read_csv(f"{save_dir}/subregion_reference_table.csv",index_col=0)
location_test = pd.read_csv(f"{save_dir}/location_test.csv",index_col=0)

electric_model_1 = pd.read_pickle(f"{save_dir}/HighWFH_Mix/{electric_fname}")
electric_model_2 = pd.read_pickle(f"{save_dir}/HighWFH_Transit/{electric_fname}")
electric_model_3 = pd.read_pickle(f"{save_dir}/HighWFH_Micro/{electric_fname}")
electric_model_4 = pd.read_pickle(f"{save_dir}/MidWFH_Mix/{electric_fname}")
electric_model_5 = pd.read_pickle(f"{save_dir}/MidWFH_Transit/{electric_fname}")
electric_model_6 = pd.read_pickle(f"{save_dir}/MidWFH_Micro/{electric_fname}")
electric_model_7 = pd.read_pickle(f"{save_dir}/NoWFH_Mix/{electric_fname}")
electric_model_8 = pd.read_pickle(f"{save_dir}/NoWFH_Transit/{electric_fname}")
electric_model_9 = pd.read_pickle(f"{save_dir}/NoWFH_Micro/{electric_fname}")


##########################################################
#########  pre-processing, helper functions  #############
##########################################################

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
    df["Subregion"] = df["Subregion"].replace({"Non-MNY Boroughs":"Non-MNY Boros",
                                               "Inner NJ":"NJ",
                                               "Outer NJ":"NJ",
                                               "Low Hud":"Hud",
                                               "Mid Hud":"Hud",
                                               })
    df['LEAVE_WORK_HOUR'] = (df['ARRIVES_AT_WORK_HOUR'] + np.ceil(df['HRS_WK_DAILY']).astype(int))%24
    df['Current'] = df["MODE_TRANSP_TO_WORK"].replace(mode_dict_1)
    # df['Reassigned'] = df["First_Assignment"].replace(mode_dict_2)
    df['Reassigned'] = df["TransMode"].replace(mode_dict_2)
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
    # order = CategoricalDtype(['CT','Hud','LI','NJ','Non-MNY Boros','Manhattan'],ordered=True)
    order = CategoricalDtype(['Manhattan','Non-MNY Boros','NJ','LI','Hud','CT'],ordered=True)
    subregion['Subregion'] = subregion['Subregion'].astype(order)
    subregion.sort_values('Subregion',inplace=True)
    return subregion


def PCE(row):
    # https://en.wikipedia.org/wiki/Passenger_car_equivalent
    # private car (including taxis or pick-up) 1
    # motorcycle 0.75
    # bicycle 0.5
    # horse-drawn vehicle 4
    # bus, tractor, truck 3
    if row['TransMode'] in ['Autos','Taxicab','Other']:
        return row['PERWT']
    elif row['TransMode']=='Bus':
        return (row['PERWT']*3)/20
    elif row['TransMode'] in ['Bicycle','Escooter']:
        return row['PERWT']*0.5
    elif row['TransMode']=='Motorcycle':
        return row['PERWT']*0.75
    elif row['TransMode'] in ['WFH','CommuterRail','Subway','Walk','Ferry']:
        return 0 

def traffic_flow(df):
    df['PCE'] = df.apply(lambda row: PCE(row), axis=1)
    in_agg = df.rename({'ARRIVES_AT_WORK_HOUR':'Hour'},axis=1).groupby(by=["Hour"]).agg({"PCE":"sum"}).reset_index().astype(int)
    in_agg['Dir'] = 'in'
    out_agg = df.rename({'LEAVE_WORK_HOUR':'Hour'},axis=1).groupby(by=["Hour"]).agg({"PCE":"sum"}).reset_index().astype(int)
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
commuter_model_4 = df_processing(commuter_model_4)
commuter_model_5 = df_processing(commuter_model_5)
commuter_model_6 = df_processing(commuter_model_6)
commuter_model_7 = df_processing(commuter_model_7)
commuter_model_8 = df_processing(commuter_model_8)
commuter_model_9 = df_processing(commuter_model_9)


### 

s_1 = " 1: High WFH + Mix Modes"
s_2 = " 2: High WFH + Max Transit"
s_3 = " 3: High WFH + Max Micro-mobility"
s_4 = " 4: Mid WFH + Mix Modes"
s_5 = " 5: Mid WFH + Max Transit"
s_6 = " 6: Mid WFH + Max Micro-mobility"
s_7 = " 7: No WFH + Mix Modes"
s_8 = " 8: No WFH + Max Transit"
s_9 = " 9: No WFH + Max Micro-mobility"

available_commuter_models = {s_1: commuter_model_1,
                             s_2: commuter_model_2, 
                             s_3: commuter_model_3,
                             s_4: commuter_model_4,
                             s_5: commuter_model_5, 
                             s_6: commuter_model_6,
                             s_7: commuter_model_7,
                             s_8: commuter_model_8, 
                             s_9: commuter_model_9,
                             }
available_electric_models = {s_1: electric_model_1,
                             s_2: electric_model_2, 
                             s_3: electric_model_3,
                             s_4: electric_model_4,
                             s_5: electric_model_5, 
                             s_6: electric_model_6,
                             s_7: electric_model_7,
                             s_8: electric_model_8, 
                             s_9: electric_model_9,
                             }

charging_time_method = sorted(electric_model_1.PEV_DELAY.dropna().unique())


#################################################
#########  generate dashboard card  #############
#################################################

def description_card():
    """
    :return: A Div containing dashboard title & descriptions.
    """
    return html.Div(
        id="description_card",
        className = "description_card",
        children=[
            html.H2("The Electric Commute"),
            html.H1("Envisioning 100% Electrified Mobility in New York City"),
            html.P("Select any of the load profile and preset scenarios of home-work commuting activities in Manhattan."),
            html.Br()
        ],
    )

def generate_control_card():
    """
    :return: A Div containing controls for graphs.
    """
    return html.Div(
        id="control_card",
        className = "control_card",
        children=[

            html.P("Load Profile"),
            dcc.Dropdown(
                ["Summer Peak","Winter"],
                "Summer Peak",
                id="load_profile",
                className="dropdown"
            ), 
            html.P("Select One Scenario"),
            dcc.RadioItems(
                list(available_commuter_models.keys()),
                list(available_commuter_models.keys())[0],
                id='commuter_model_of_choice_idx',
                className="dcc_control",
                labelStyle={'display': 'block'}
            ),
        ],
    )

side_bar = html.Div(
            className="side_bar",
            children=[
                html.Img(src=app.get_asset_url("NYU_Short_RGB_Color.png")),
                description_card(), 
                generate_control_card(),
                html.Img(src=app.get_asset_url("matrix.png")),
                ]
        )

map_card = html.Div(
            id="map_card",
            className="map card_container",
            children=[
                html.Div(
                className="title_flex",
                children=[
                        html.H4("MAP TITLE | MAP TITLE | MAP TITLE"),
                        html.Button('?')
                    ]
                ),
                dcc.Graph(id="map_graphic"),
            ],
        )

map_card_full = html.Div(
                    id="map_card",
                    className="map_full card_container",
                    children=[
                        html.Div(
                            className="title_flex",
                            children=[
                                    html.H4("MAP TITLE | MAP TITLE | MAP TITLE"),
                                    html.Button('?')
                                ]
                            ),
                        html.H5("One sentence intro of the map layers: Manhattan Workers’ Place of Residence by Travel Mode. placeholder=Type something here! placeholder=Type something here!"),
                        dcc.Graph(id="map_graphic"),
                    ],
                )

e_card = html.Div(className="e_card",
                    children=[
                        html.Div(
                            [html.H3(id="total_energy_text"), html.P("Daily Energy")],
                            id="wells",
                            className="mini_container",
                        ),
                            html.Div(
                            [html.H3(id="add_energy_text"), html.P("Add. Energy")],
                            id="oil",
                            className="mini_container",
                        ),
                        html.Div(
                            [html.H3(id="peak_power_text"), html.P("Peak Load")],
                            id="gas",
                            className="mini_container",
                        ),
                    ],
                )

energy_profile = html.Div(className="energy_profile card_container",
                    children=[
                            html.Div(
                            className="title_flex",
                            children=[                       
                                html.H4("Energy Profile of Manhattan's Home-Work Commuting Activities"),
                                html.Button('?')
                            ]
                        ),

                        html.Div(
                            className="e_choice", 
                            children=[
                                html.Div(className="e_choice_1", children=[html.Label(['Details: '])]),
                                html.Div(className="e_choice_11", children=[daq.BooleanSwitch(id='Detailed',on=False)]),
                                html.Div(className="e_choice_2", children=[html.Label(['Delay Type: '])]),
                                html.Div(className="e_choice_22", children=[dcc.Dropdown(charging_time_method,"Random",id='pev_delay_choice')]),
                            ],
                        ),
                        dcc.Graph(id="electric_graphic")
                    ],
                )


energy = html.Div(
            id="energy_card",
            className="energy",
            children=[
                e_card,
                energy_profile,
            ],
        )


pce_flow = html.Div(
            id="pce_flow",
            className="flow card_container",
            children=[
                html.H4("Passenger Car Equivalent"),
                dcc.Graph(id="flow_graphic"),
            ],
        )

mode_assign = html.Div(
            id="mode_assign",
            className="flag card_container",
            children=[
                html.H4("Eligible vs Assigned (rename title)"),
                dcc.Graph(id="eligible_graphic"),
            ],
        )

mode_share = html.Div(
                    id="mode_share",
                    className="share card_container",
                    children=[
                        html.H4("Travel Modes Share"),
                        dcc.Graph(id="share_graphic"),
                    ],
                )


mode_share_subregion = html.Div(
                            id="mode_share_subregion",
                            className="region card_container",
                            children=[
                                html.H4("Mode Choices by Subregion"),
                                dcc.Graph(id="subregion_graphic"),
                            ],
                        )

#################################################
#################    layout   ###################
#################################################

app.layout = html.Div([
    side_bar,
    html.Div([dcc.Tabs(
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
            dcc.Tab(
                label='OTHERS',
                value='tab-4', className='custom-tab',
                selected_className='custom-tab--selected'
            ),
        ]),
    html.Div(id='tabs-content-classes', className="tab_contents")], className="right")
], className="app_container")



#################################################
################    callback   ##################
#################################################

@app.callback(Output('tabs-content-classes', 'children'),
              Input('tabs-with-classes', 'value'))
def render_content(tab):
    if tab == 'tab-1':
        return html.Div([
            map_card_full,
            energy,
            mode_share,
            mode_share_subregion,
        ],className="tab1_content")
    elif tab == 'tab-2':
        return html.Div([
            map_card,
            energy,
            pce_flow,
            mode_assign,
            mode_share,
            mode_share_subregion,
        ],className="tab2_content")
    elif tab == 'tab-3':
        return html.Div([
            html.Div(
                        [
                            html.H3('COMMUTER MODEL'),
                            html.P('One sentence intro of the model. placeholder=Type something here! placeholder=Type something here! placeholder=Type something here! placeholder=Type something here!'),
                            html.Img(src=app.get_asset_url("commuter_model.png"))
                        ], 
                        className="commuter_model card_container"
                    ),
            html.Div(
                        [
                            html.H3('ELECTRICAL MODEL'),
                            html.P('One sentence intro of the model. placeholder=Type something here! placeholder=Type something here! placeholder=Type something here! placeholder=Type something here!'),                            
                            # html.Img(src=app.get_asset_url("NYU_Short_RGB_Color.png"))
                        ], 
                        className="electrical_model card_container"
                    ),            
        ],className="tab3_content")    


@app.callback(
    Output('map_graphic', 'figure'),
    [Input('commuter_model_of_choice_idx','value'),
     Input('tabs-with-classes', 'value')],
    )
def update_map_graph(commuter_model_of_choice_idx,tab):
    comm_df = available_commuter_models[commuter_model_of_choice_idx]
    comm_df['sequence']=comm_df.groupby(['PUMAKEY_HOME']).cumcount()
    location_test['sequence']=location_test.groupby(['PUMAKEY_HOME']).cumcount()
    comm_df = comm_df.merge(right=location_test[['PUMAKEY_HOME','sequence','lat','lon']], on=["sequence","PUMAKEY_HOME"])
    comm_df.rename({'PERWT':'Number_of_Commuters', 'TransMode':'Travel Mode'},axis=1,inplace=True)
    comm_df['size'] = 1
    fig = px.scatter_mapbox(comm_df, 
                            lat="lat", lon="lon", hover_name="Travel Mode", color="Travel Mode", 
                            size="size", 
                            size_max=2.5, 
                            zoom=7.5,
                            color_discrete_map=color__dict,
                            hover_data=dict(lat=False, lon=False, size=False, Number_of_Commuters=True),
                            )
    fig.update_layout(mapbox_style="carto-positron")
    # fig.update_layout(mapbox_style="carto-darkmatter")
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    fig.update(layout_showlegend=False)
    if tab=='tab-1':
        fig.update_layout(height=700)
    else:
        fig.update_layout(height=380)
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


@app.callback(
    Output('electric_graphic', 'figure'),
    [Input('commuter_model_of_choice_idx','value'),
    Input('Detailed','on'),
    Input('pev_delay_choice', 'value'),
    Input('load_profile', 'value')],
    )
def update_electric_graph(commuter_model_of_choice_idx,Detailed,pev_delay_choice,load_profile):
    com_df = available_electric_models[commuter_model_of_choice_idx]
    e_tmp_profile = e_profile_hold_space(com_df)
    fig = px.line(e_tmp_profile, x='Charge_Hour', y='Energy', color='PEV_DELAY', markers=True,
                  labels=dict(Charge_Hour="Time of day (hr)", TransMode="Travel Mode", Energy="Power (MW)", PEV_DELAY="Delay Type"))

    layout_elec = copy.deepcopy(layout)
    layout_elec["height"] = 240
    fig.update_layout(layout_elec)
    fig.update_layout(xaxis_title=None)
    fig.update_xaxes(range = [0,23])
    fig.update_yaxes(range = [0,1000])

    if load_profile == "Winter":
        fig.add_hline(800)

    if Detailed:
        df_plot = available_electric_models[commuter_model_of_choice_idx]
        df_plot = df_plot[df_plot["PEV_DELAY"]==pev_delay_choice]
        df_plot['Energy'] = df_plot['Energy']/1000
        df_plot['TransMode'] = df_plot['TransMode'].astype("string")
        gb_plot = df_plot.groupby(by=["Charge_Hour","TransMode"]).agg({"Energy":"sum"}).reset_index()
        ### order: most or stable on bottom, now use most
        sum_energy_by_mode = df_plot.groupby(by=["TransMode"]).agg({"Energy":"sum"}).rename({'Energy':'sum'},axis=1).reset_index()
        gb_plot = gb_plot.merge(right=sum_energy_by_mode, on=["TransMode"])
        gb_plot.sort_values(by=['sum'],ascending=False,inplace=True)
        fig = px.area(gb_plot,x='Charge_Hour',y='Energy',color='TransMode',markers=False, 
                      color_discrete_map=color__dict,
                      labels=dict(Charge_Hour="Hour of Day", TransMode="Travel Mode", Energy="Power (MW)"))
        fig.update_xaxes(range = [0,23])
        fig.update_yaxes(range = [0,1000])
        fig.update_layout(layout_elec)
        fig.update_layout(xaxis_title=None)

        if load_profile == "Winter":
                fig.add_hline(800)
        
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
    in_flow = in_df.PCE.to_list()
    out_flow = out_df.PCE.to_list()
    layout_flow = copy.deepcopy(layout)
    layout_flow["yaxis"] = dict(range=[0,3e5])
    layout_flow['height'] = 280
    layout_flow['margin'] = dict(l=35, r=10, b=10, t=10)
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
    layout_flag["height"] = 280
    fig.update_layout(layout_flag)
    fig.update_layout(yaxis_title=None,xaxis_title=None)
    fig.update_layout(showlegend=True)
    return fig


@app.callback(
    Output('share_graphic', 'figure'),
    Input('commuter_model_of_choice_idx','value'),
    )
def update_share_graph(commuter_model_of_choice_idx):

    com_df = available_commuter_models[commuter_model_of_choice_idx]
    share_df = com_df.groupby(by=["Reassigned","Reassigned_Parent"]).agg({"PERWT":"sum"}).reset_index()\
                .rename({'Reassigned':'Mode','Reassigned_Parent':'Mode_Parent'},axis=1)
    share_df['ALL'] = 'Travel Modes'
    fig = px.sunburst(share_df, path=['ALL','Mode_Parent','Mode'], values='PERWT')

    layout_share = copy.deepcopy(layout)
    layout_share["height"] = 280
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

    ### order: most or stable on bottom, now use most
    sum_subregion = gb_plot.groupby(by=["Reassigned"]).agg({"PERWT":"sum"}).rename({'PERWT':'sum'},axis=1).reset_index()
    gb_plot = gb_plot.merge(right=sum_subregion, on=["Reassigned"])
    gb_plot.sort_values(by=["Subregion",'sum'],ascending=False,inplace=True)
    gb_plot.rename({'PERWT':'Number of Commuters', 'Reassigned':'Travel Mode'},axis=1,inplace=True)



    fig = px.bar(gb_plot, x="Number of Commuters", y="Subregion", 
                 color='Travel Mode', 
                 orientation='h',
                 hover_data=["Travel Mode", "Number of Commuters"],
                 color_discrete_map=color__dict,
                 height=350)
    layout_subregion = copy.deepcopy(layout)
    layout_subregion["height"] = 280
    fig.update_layout(layout_subregion)
    fig.update_layout(yaxis_title=None,xaxis_title=None)
    fig.update_layout(showlegend=True)
    return fig


# Run the server
if __name__ == "__main__":
    app.run_server(debug=True)