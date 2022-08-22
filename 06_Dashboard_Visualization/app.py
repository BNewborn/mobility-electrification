import dash
import copy
from dash import Dash, dcc, html, Input, Output, ClientsideFunction
import plotly.graph_objects as go
import plotly.express as px
import dash_daq as daq
import pandas as pd
import geopandas as gpd
import shapely.geometry
import numpy as np
from pandas.api.types import CategoricalDtype
from textwrap import dedent


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
    margin=dict(l=10, r=10, b=0, t=10),
    hovermode="closest",
    plot_bgcolor="rgba(0, 0, 0, 0)",
    paper_bgcolor="rgba(0, 0, 0, 0)",
    legend=dict(font=dict(size=7), orientation="h", y=-0.1, x=0),
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
               'Walk':'#B6E880',
               'Taxicab':'#FF97FF',
               'Bicycle':'#FECB52',
               'Other':'#7F7F7F',
               'WFH':'#72B7B2',
               'Baseload*':'lightgrey'
               }

color_plant_dict = {'batteries':'#FF6692',
                    'natural gas':'#19D3F3',
                    'biomass':'#B6E880',
                    'solar':'#FFA15A',
                    'pumped storage':'#72B7B2',
                    'hydroelectric':'#EF553B',
                    'wind':'#000',
                    'other':'#7F7F7F',
                    'petroleum':'#636EFA',
                    }

#########################################
#######  read the orginal data  #########
#########################################

save_dir = "./electric_model_outputs_WFHTransitCombos_V3"
commuter_fname = "commuter_model_ipums_df.pkl"
electric_fname = "electric_model_df_aggregate.pkl"

commuter_model_0 = pd.read_pickle(f"{save_dir}/Baseline_2019_Mode/{commuter_fname}")

commuter_model_1 = pd.read_pickle(f"{save_dir}/HighWFH_Mix/{commuter_fname}")
commuter_model_2 = pd.read_pickle(f"{save_dir}/HighWFH_Transit/{commuter_fname}")
commuter_model_3 = pd.read_pickle(f"{save_dir}/HighWFH_Micro/{commuter_fname}")
commuter_model_4 = pd.read_pickle(f"{save_dir}/HighWFH_Car/{commuter_fname}")

commuter_model_5 = pd.read_pickle(f"{save_dir}/MidWFH_Mix/{commuter_fname}")
commuter_model_6 = pd.read_pickle(f"{save_dir}/MidWFH_Transit/{commuter_fname}")
commuter_model_7 = pd.read_pickle(f"{save_dir}/MidWFH_Micro/{commuter_fname}")
commuter_model_8 = pd.read_pickle(f"{save_dir}/MidWFH_Car/{commuter_fname}")

commuter_model_9 = pd.read_pickle(f"{save_dir}/NoWFH_Mix/{commuter_fname}")
commuter_model_10 = pd.read_pickle(f"{save_dir}/NoWFH_Transit/{commuter_fname}")
commuter_model_11 = pd.read_pickle(f"{save_dir}/NoWFH_Micro/{commuter_fname}")
commuter_model_12 = pd.read_pickle(f"{save_dir}/NoWFH_Car/{commuter_fname}")


subregion_reference = pd.read_csv(f"{save_dir}/subregion_reference_table.csv",index_col=0)
location_test = pd.read_csv(f"{save_dir}/location_test.csv",index_col=0)


electric_model_0 = pd.read_pickle(f"{save_dir}/Baseline_2019_Mode/{electric_fname}")
electric_model_1 = pd.read_pickle(f"{save_dir}/HighWFH_Mix/{electric_fname}")
electric_model_2 = pd.read_pickle(f"{save_dir}/HighWFH_Transit/{electric_fname}")
electric_model_3 = pd.read_pickle(f"{save_dir}/HighWFH_Micro/{electric_fname}")
electric_model_4 = pd.read_pickle(f"{save_dir}/HighWFH_Car/{electric_fname}")
electric_model_5 = pd.read_pickle(f"{save_dir}/MidWFH_Mix/{electric_fname}")
electric_model_6 = pd.read_pickle(f"{save_dir}/MidWFH_Transit/{electric_fname}")
electric_model_7 = pd.read_pickle(f"{save_dir}/MidWFH_Micro/{electric_fname}")
electric_model_8 = pd.read_pickle(f"{save_dir}/MidWFH_Car/{electric_fname}")
electric_model_9 = pd.read_pickle(f"{save_dir}/NoWFH_Mix/{electric_fname}")
electric_model_10 = pd.read_pickle(f"{save_dir}/NoWFH_Transit/{electric_fname}")
electric_model_11 = pd.read_pickle(f"{save_dir}/NoWFH_Micro/{electric_fname}")
electric_model_12 = pd.read_pickle(f"{save_dir}/NoWFH_Car/{electric_fname}")


maxload_profiles = pd.read_pickle(f"{save_dir}/maxload_profiles.p")
maxload_profiles = maxload_profiles[maxload_profiles['offshore']=='with']
maxload_profiles['key'] = maxload_profiles['season'] + "_" + maxload_profiles['wind']
maxload_profiles['hour'] = maxload_profiles.apply(lambda row: list(range(0, 24)), axis=1)
maxload_profiles = maxload_profiles.explode(['hour','baseload','maxload'])
maxload_profiles.rename({'hour':'Charge_Hour'},axis=1,inplace=True)


station_df = pd.read_csv(f"{save_dir}/substations.csv")
eline_df = gpd.read_file(f"{save_dir}/transmission_lines.geojson")
plant_df = pd.read_csv(f"{save_dir}/powerplants_ny.csv")
plant_df.rename({'PrimSource':'PowerPlants'},axis=1,inplace=True)


lats = []
lons = []
voltages = []

for feature, voltage in zip(eline_df.geometry, eline_df.VOLT_CLASS):
    if isinstance(feature, shapely.geometry.linestring.LineString):
        linestrings = [feature]
    elif isinstance(feature, shapely.geometry.multilinestring.MultiLineString):
        linestrings = feature.geoms
    else:
        continue
    for linestring in linestrings:
        x, y = linestring.xy
        lats = np.append(lats, y)
        lons = np.append(lons, x)
        voltages = np.append(voltages, [voltage]*len(y))
        lats = np.append(lats, None)
        lons = np.append(lons, None)
        voltages = np.append(voltages, None)


##########################################################
#########  pre-processing, helper functions  #############
##########################################################

def build_modal_info_overlay(id, side, content):
    """
    Build div representing the info overlay for a plot panel
    """
    div = html.Div(
        [  # modal div
            html.Div(
                [  # content div
                    html.Div(
                        [
                            html.H4(
                                [
                                    # "Info | Double-click on legend to isolate one trace.",
                                    html.Img(
                                        id=f"close-{id}-modal",
                                        src="assets/times-circle-solid.svg",
                                        n_clicks=0,
                                        className="info-icon",
                                    ),
                                ],
                                className='modal-title'
                            ),
                            dcc.Markdown(content),
                        ]
                    )
                ],
                className=f"modal-content {side}",
            ),
            html.Div(className="modal"),
        ],
        id=f"{id}-modal",
        style={"display": "none"},
    )
    return div


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
    df = df.merge(right=subregion_reference, on=["PUMAKEY_HOME"], how='left')
    df["Subregion"] = df["Subregion"].fillna('Other')
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
    # df['MNY_RES'] = df['PUMAKEY_HOME'].apply(lambda x: 1 if x.startswith('36_038') else 0)
    # df['distance_row_sum'] = df['DISTANCE_KM']*df['PERWT']
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
    df_pro = df[df['FLOW_DIR']!='ALL']
    e_tmp_profile = df_pro.groupby(by=["Charge_Hour","PEV_DELAY"]).agg({"Energy":"sum"}).reset_index()
    e_tmp_profile['Energy'] = e_tmp_profile['Energy']/1000
    return e_tmp_profile

commuter_model_0 = df_processing(commuter_model_0)
commuter_model_1 = df_processing(commuter_model_1)
commuter_model_2 = df_processing(commuter_model_2)
commuter_model_3 = df_processing(commuter_model_3)
commuter_model_4 = df_processing(commuter_model_4)
commuter_model_5 = df_processing(commuter_model_5)
commuter_model_6 = df_processing(commuter_model_6)
commuter_model_7 = df_processing(commuter_model_7)
commuter_model_8 = df_processing(commuter_model_8)
commuter_model_9 = df_processing(commuter_model_9)
commuter_model_10 = df_processing(commuter_model_10)
commuter_model_11 = df_processing(commuter_model_11)
commuter_model_12 = df_processing(commuter_model_12)

### 

pattern_list = [" Mode Choices in 2019 ", " Mix Modes ", " Heavy Transit ", " Heavy Micro-mobility ", " Heavy Car Usage "]
wfh_list = [" High WFH ", " Mid WFH ", " No WFH "]

season_list = ["Summer", "Winter"]
wind_list = ["Low", "High"]

s_1 = pattern_list[1] + "+" + wfh_list[0]
s_2 = pattern_list[2] + "+" + wfh_list[0]
s_3 = pattern_list[3] + "+" + wfh_list[0]
s_4 = pattern_list[4] + "+" + wfh_list[0]

s_5 = pattern_list[1] + "+" + wfh_list[1]
s_6 = pattern_list[2] + "+" + wfh_list[1]
s_7 = pattern_list[3] + "+" + wfh_list[1]
s_8 = pattern_list[4] + "+" + wfh_list[1]

s_9 = pattern_list[1] + "+" + wfh_list[2]
s_10 = pattern_list[2] + "+" + wfh_list[2]
s_11 = pattern_list[3] + "+" + wfh_list[2]
s_12 = pattern_list[4] + "+" + wfh_list[2]

available_commuter_models = {s_1: commuter_model_1,
                             s_2: commuter_model_2, 
                             s_3: commuter_model_3,
                             s_4: commuter_model_4,
                             s_5: commuter_model_5, 
                             s_6: commuter_model_6,
                             s_7: commuter_model_7,
                             s_8: commuter_model_8, 
                             s_9: commuter_model_9,
                             s_10: commuter_model_10,
                             s_11: commuter_model_11, 
                             s_12: commuter_model_12,                             
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
                             s_10: electric_model_10,
                             s_11: electric_model_11, 
                             s_12: electric_model_12,                             
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
            html.H2("Load Profile"),
            html.P("1. Select Season"),
            dcc.RadioItems(
                id='season',
                className="dcc_control",
                options=[
                    {'label': " Summer", 'value': "Summer"},
                    {'label': " Winter", 'value': "Winter"},
                ],
                value="Summer",
                labelStyle={'display': 'inline', 'margin-right': 10}
            ),
            html.P("2. Select Wind Level"),
            dcc.RadioItems(
                id='wind_level',
                className="dcc_control",
                options=[
                    {'label': " Low", 'value': "Low"},
                    {'label': " High", 'value': "High"},
                ],
                value="Low",
                labelStyle={'display': 'inline', 'margin-right': 10}
            ),
            html.P("3. With offshore wind projects (current & planned)"),
            html.H2("Commuting Scenario"),
            html.P("1. Select Transit Patterns"),
            dcc.RadioItems(
                id='transit_pattern',
                className="dcc_control",
                options=[
                    {'label': pattern_list[0], 'value': pattern_list[0]},
                    {'label': pattern_list[1], 'value': pattern_list[1]},
                    {'label': pattern_list[2], 'value': pattern_list[2]},
                    {'label': pattern_list[3], 'value': pattern_list[3]},
                    {'label': pattern_list[4], 'value': pattern_list[4]}
                ],
                value=pattern_list[1],
                labelStyle={'display': 'block'}
            ),
            html.P("2. Select Work-from-home Level"),
            dcc.RadioItems(
                id='wfh_level',
                className="dcc_control",
                options=[
                    {'label': wfh_list[0], 'value': wfh_list[0]},
                    {'label': wfh_list[1], 'value': wfh_list[1]},
                    {'label': wfh_list[2], 'value': wfh_list[2]},
                ],
                value=wfh_list[0],
                labelStyle={'display': 'inline', 'margin-right': 10}
            ),
        ],
    )

side_bar = html.Div(
            className="side_bar",
            children=[
                html.Img(src=app.get_asset_url("NYU_Short_RGB_Color.png")),
                description_card(), 
                generate_control_card(),
                html.Br(),
                # html.Img(src=app.get_asset_url("GitHub-Mark-64px.png")),
                html.A([html.Img(src=app.get_asset_url("GitHub-Mark-64px.png"))], href='https://github.com/BNewborn/mobility-electrification',target="_blank")
                ]
        )

map_card = html.Div(
            id="mapping-div",
            className="map card_container",
            children=[
                html.H4(
                    [
                        "Manhattan Workers’ Place of Residence",
                        html.Img(
                            id="show-mapping-modal",
                            src="assets/question-circle-solid.svg",
                            n_clicks=0,
                            className="info-icon",
                        ),
                    ],
                    className="container_title",
                ),
                dcc.Graph(id="map_graphic_s"),
            ],
        )

map_card_full = html.Div(
                    id="mapping-div",
                    className="map_full card_container",
                    children=[
                        html.H4(
                            [
                                "Manhattan Workers’ Place of Residence & Power System",
                                html.Img(
                                    id="show-mapping-modal",
                                    src="assets/question-circle-solid.svg",
                                    n_clicks=0,
                                    className="info-icon",
                                ),
                            ],
                            className="container_title",
                        ),
                        dcc.RadioItems(
                            [" Commuting", " Power System"],
                            " Commuting",
                            className="dcc_control",
                            id='layer'
                        ),
                        dcc.Graph(id="map_graphic"),
                    ],
                )

e_card = html.Div(
                    # id="radio-div",
                    className="e_card",
                    children=[
                        html.Div(
                            [
                                html.H3(id="total_energy_text"), html.P("Total Energy")
                            ],
                            className="mini_container",
                        ),
                        html.Div(
                            [
                                html.H3(id="trans_energy_text"), html.P("Total Trans. Energy")
                            ],
                            className="mini_container",
                        ),
                        html.Div(
                            [
                                html.H3(id="peak_power_text"), html.P(["Peak Trans. Load"]),
                            ],
                            className="mini_container",
                        ),
                    ],
                )

energy_profile = html.Div(
                    className="energy_profile card_container",
                    children=[
                        html.H4(
                            [
                                "Energy Profile of Manhattan's Home-Work Commuting Activities",
                                html.Img(
                                    id="show-energy-modal",
                                    src="assets/question-circle-solid.svg",
                                    n_clicks=0,
                                    className="info-icon",
                                ),
                            ],
                            className="container_title",
                        ),
                        html.Div(
                            className="e_choice", 
                            children=[
                                html.Div(className="e_choice_1", children=[html.Label(['Details:'])]),
                                html.Div(className="e_choice_11", children=[daq.BooleanSwitch(id='Detailed',on=False)]),
                                html.Div(className="e_choice_2", children=[html.Label(['Start time for EV charge:'])]),
                                # html.Div(className="e_choice_22", children=[dcc.Dropdown(charging_time_method,"Random",id='pev_delay_choice')]),
                                html.Div(
                                    className="e_choice_22", 
                                    children=[
                                        dcc.RadioItems(
                                            id='pev_delay_choice',
                                            options=[
                                                {'label': 'Random', 'value': 'Random'},
                                                {'label': 'Earliest', 'value': 'Earliest'},
                                                {'label': 'Latest', 'value': 'Latest'},
                                                {'label': 'Custom - 3 hr.', 'value': 'Custom'}
                                            ],
                                            value="Random",
                                            labelStyle={'display':'inline','margin-right':10,'font-style':'italic'}
                                        )
                                    ]
                                ),
                            ],
                        ),
                        dcc.Graph(id="electric_graphic", config={"displayModeBar": False, "scrollZoom": False})
                    ],
                )

energy = html.Div(
            id="energy-div",
            className="energy",
            children=[
                e_card,
                energy_profile,
            ],
        )

pce_flow = html.Div(
            id="pce-div",
            className="flow card_container",
            children=[
                html.H4(
                    [
                        "Traffic Flow",
                        html.Img(
                            id="show-pce-modal",
                            src="assets/question-circle-solid.svg",
                            n_clicks=0,
                            className="info-icon",
                        ),
                    ],
                    className="container_title",
                ),
                dcc.Graph(id="flow_graphic", config={"displayModeBar": False, "scrollZoom": False}),
            ],
        )

mode_assign = html.Div(
            id="flagvs-div",
            className="flag card_container",
            children=[
                html.H4(
                    [
                        "Eligible vs Assigned",
                        html.Img(
                            id="show-flagvs-modal",
                            src="assets/question-circle-solid.svg",
                            n_clicks=0,
                            className="info-icon",
                        ),
                    ],
                    className="container_title",
                ),
                dcc.Graph(id="eligible_graphic", config={"displayModeBar": False, "scrollZoom": False}),
            ],
        )

mode_share = html.Div(
                    id="share-div",
                    className="share card_container",
                    children=[
                        html.H4(
                            [
                                "Travel Mode Share",
                                html.Img(
                                    id="show-share-modal",
                                    src="assets/question-circle-solid.svg",
                                    n_clicks=0,
                                    className="info-icon",
                                ),
                            ],
                            className="container_title",
                        ),
                        dcc.Graph(id="share_graphic", config={"displayModeBar": False, "scrollZoom": False}),
                    ],
                )

mode_share_subregion = html.Div(
                            id="subregion-div",
                            className="region card_container",
                            children=[
                                # html.H4("Mode Choices by Subregion"),
                                html.H4(
                                    [
                                        "Mode Choices by Subregion",
                                        html.Img(
                                            id="show-subregion-modal",
                                            src="assets/question-circle-solid.svg",
                                            n_clicks=0,
                                            className="info-icon",
                                        ),
                                    ],
                                    className="container_title",
                                ),
                                dcc.Graph(id="subregion_graphic", config={"displayModeBar": False, "scrollZoom": False}),
                            ],
                        )



modal_1 = build_modal_info_overlay(
                    "mapping",
                    "bottom",
                    dedent(
                        """
            The selected _**Map**_ panel displays 
            
            1) _**Manhattan Workers’ Place of Residence by Travel Mode**_

            Each dot represents a group of commuters. The location of the dot is randomly generated within its residential area. _Data Source: ACS, IPUMS_

            2) _**Power System**_

            This map shows the operable electric generating plants, transmission lines, and substations in the New York Metropolitan Area. _Source: EIA, HIFLD_
            """
                    ),
                )

modal_3 = build_modal_info_overlay(
                    "energy",
                    "bottom",
                    dedent(
                        """
            The selected _**Energy Profile**_ panel displays 
            
            1) _**Three energy indicators**_

            The three energy indicators are total daily energy consumption (base electrical load plus energy calculated for transportation), energy consumption by transportation, and peak transportation load.

            2) _**Average hourly energy consumption - General**_

            Our electricity model simulates the hourly energy consumption in Manhattan for four different charging start times of passenger electric vehicles: earliest, latest, random, and 3-hour delay, all relative to the time commuters arrive at work. In the general view, we can explore the impact of the four charging habits on the overall energy consumption, whether the existing peak load is exacerbated or alleviated based on the current baseload, and whether the energy will exceed the maximum load. 

            3) _**Average hourly energy consumption - Details**_

            The detailed view on the right demonstrates the stacking power needs of this scenario.
        """
                    ),
                )

modal_4 = build_modal_info_overlay(
                    "share",
                    "top",
                    dedent(
                        """
            The selected _**Mode Share**_ panel shows the proportion of four transit patterns (inner ring), as well as the proportion of detailed transportation modes (outer ring). 
        """
                    ),
                )

modal_5 = build_modal_info_overlay(
                    "subregion",
                    "top",
                    dedent(
                        """
            The selected _**Subregion**_ panel displays the aggregated number of commuters by region. In it, we can explore the dominant commuting mode in each region for this scenario.
        """
                    ),
                )

modal_6 = build_modal_info_overlay(
                    "pce",
                    "top",
                    dedent(
                        """
            The selected _**Traffic Flow**_ panel displays the number of vehicles measured by Passenger Car Equivalent (PCE).

            -- private car (including taxis or pick-up) 1

            -- motorcycle 0.75

            -- bicycle 0.5

            -- bus, tractor, truck 3
        """
                    ),
                )

modal_7 = build_modal_info_overlay(
                    "flagvs",
                    "top",
                    dedent(
                        """
            The selected _**Eligible vs Assigned**_ panel displays the number of eligible (grey) and final assigned commuters (purple) for each mode.
        """
                    ),
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
                label='Main',
                value='tab-1',
                className='custom-tab',
                selected_className='custom-tab--selected'
            ),
            dcc.Tab(
                label='Detail',
                value='tab-2',
                className='custom-tab',
                selected_className='custom-tab--selected'
            ),
            dcc.Tab(
                label='Framework',
                value='tab-3', className='custom-tab',
                selected_className='custom-tab--selected'
            ),
            dcc.Tab(
                label='About',
                value='tab-4', className='custom-tab',
                selected_className='custom-tab--selected'
            ),
        ]),
        html.Div(id='tabs-content-classes', className="tab_contents")], className="right")
        ], 
        className="app_container"
    )


#################################################
################    callback   ##################
#################################################

# Create show/hide callbacks for each info modal
for id in ["mapping", "energy", "share", "subregion", "pce", "flagvs"]:
    @app.callback(
        [Output(f"{id}-modal", "style"), Output(f"{id}-div", "style")],
        [Input(f"show-{id}-modal", "n_clicks"), Input(f"close-{id}-modal", "n_clicks")],
    )
    def toggle_modal(n_show, n_close):
        ctx = dash.callback_context
        if ctx.triggered and ctx.triggered[0]["prop_id"].startswith("show-"):
            return {"display": "block"}, {"zIndex": 1003}
        else:
            return {"display": "none"}, {"zIndex": 0}


@app.callback(Output('tabs-content-classes', 'children'),
              Input('tabs-with-classes', 'value'))
def render_content(tab):
    if tab == 'tab-1':
        return html.Div([
            modal_1,
            # modal_2,
            modal_3,
            modal_4,
            modal_5,
            map_card_full,
            energy,
            mode_share,
            mode_share_subregion,
        ],className="tab1_content")
    elif tab == 'tab-2':
        return html.Div([
            modal_1,
            # modal_2,
            modal_3,
            modal_4,
            modal_5,
            modal_6,
            modal_7,
            map_card,
            energy,
            pce_flow,
            mode_assign,
            mode_share,
            mode_share_subregion,
        ],className="tab2_content")
    ### https://dash.plotly.com/dash-core-components/markdown
    elif tab == 'tab-3':
        return html.Div([
            html.Div(
                        [
                            dcc.Markdown(dedent(
                        """
            ## Framework
            The framework is composed of three parts: 

            (1) Data cleaning and aggregation/disaggregation; \n
            (2) Reusable pipeline composed of commuting model and electricity model built by Python Class, and power system model in New York State; \n
            (3) Information visualization and development of dashboard. 
            """
                    )),
                            html.Img(src=app.get_asset_url("framework.png"))
                        ], 
                        className="commuter_model_1 card_container"
                    ),
            html.Div(
                        [
                            dcc.Markdown(dedent(
                        """
            ## Commuting Model
            Our commuting model was built as a Python class, which enabled concurrent, repeatable runs. Through internal methods, it assigns each commuter the possible commuting modes they are eligible for taking, and, depending on input parameters, a final commuting mode that they are assigned. 

            ```python
            ### sample codes of Commuting Model - Eligibility Model
            from commuter_model.commuter_model import CommuterModel
            commuter_model_1 = CommuterModel(ipums_df=ipums_df_19.copy()) 
            commuter_model_1.ipums_df['FLAG_ESCOOTER'] = commuter_model_1.escooter_flag_binary(
                                             max_age=60
                                            ,max_distance=4
                                            ,scooter_friendly_origins=commuter_model_1.bike_friendly_origins
                                            ,male_pct=10
                                            ,female_pct=10
                                            )
            ```
            """
                    )),
                    html.Br(),
                            dcc.Markdown(dedent(
                        """
            ## Electricity Model
            Then we pass the commuting model outputs to the electricity model, another reusable Python class, that summed up the distance traveled by each transportation mode, per hour, and multiplied this by variables in our EV dataset to get aggregate energy demand by hour and transit mode. 

            ```python
            ### sample codes of Electricity Model
            from electrical_model.electrical_model import ElectricModel
            electric_model_1 = ElectricModel(electric_model_1.ipums_df
                                                ,ev_reference_table_loc="EV_reference_table.csv"
                                                ,PEV_delay_hr=3
                                                ,bus_ferry_cab_delay=6
                                                ,model_name = 'electric_model_1')
            ```
            """
                    )),
                    html.Br(),
                            dcc.Markdown(dedent(
                        """
            ## Power System Model
            The NYISO power system is modeled with 1,814 buses and 2,202 high voltage transmission lines. This model has been tuned to synthesize the properties of the real NYISO power system and can be used to quantify congestion patterns, optimize generator schedules, and propose market prices. 
            """
                    )),
                        ], 
                        className="electrical_model_1 card_container"
                    ),            
        ],className="tab3_content")    
    elif tab == 'tab-4':
        return html.Div([
            html.Div(
                        [
                    dcc.Markdown(dedent(
                        """
            ## Center for Urban Science + Progress (CUSP)

            [CUSP](https://cusp.nyu.edu/), a unique research center at the NYU Tandon School of Engineering dedicated to the interdisciplinary application of science, technology, engineering, and mathematics in the service of urban communities across the globe.

            TEC-NYC is one of the [2022 Capstone Projects](https://cusp.nyu.edu/2022-capstone-projects/) - Modern Civil and Communications Infrastructure Category.
            """
                    ),link_target="_blank"),
                    html.Br(),
                    html.Br(),
                    dcc.Markdown(dedent(
                        """
            ## Project Sponsors

            Dr. [Robert Mieth](https://scholar.google.com/citations?user=xF6QXAUAAAAJ&hl=en), *Postdoctoral Researcher, Project Director*

            Dr. [Yury Dvorkin](https://scholar.google.com/citations?user=lI2PTkAAAAAJ&hl=en), *Assistant Professor, Faculty Mentor*
            """
                    ),link_target="_blank"),
                    html.Br(),
                    html.Br(),
                    dcc.Markdown(dedent(
                        """
            ## Research Team

            [Amber Jiang](https://www.linkedin.com/in/amber-ming-jiang/), *Subject Matter Expert*

            Sara Kou, *Project Manager*

            [Brian Newborn](https://www.linkedin.com/in/brian-newborn/), *Data Analysis Lead*

            [Jingrong Zhang](https://zhangjingrong.com/), *Visualization Lead*      

            """
                    ),link_target="_blank"),
                    html.Br(),
                    html.Br(),
                    dcc.Markdown(dedent(
                        """
            ## Sources
            
            [IPUMS USA](https://www.ipums.org/), University of Minnesota, [www.ipums.org](https://www.ipums.org/)

            [2019 Hub Bound Travel](https://www.nymtc.org/Portals/0/Pdf/Hub%20Bound/2019%20Hub%20Bound/DM_TDS_Hub_Bound_Travel_2019.pdf?ver=GS5smEoyHSsHsyX_t_Zriw%3d%3d), New York Metropolitan Transportation Council (NYMTC), [www.nymtc.org](https://www.nymtc.org/)

            [Load Data](https://www.nyiso.com/load-data), New York Independent System Operator (NYISO), [www.nyiso.com](https://www.nyiso.com/)
            """
                    ),link_target="_blank"),                    
                        ], 
                        className="commuter_model card_container"
                    ),   
        ],className="tab4_content")    


@app.callback(
    Output('wfh_level', 'options'),
    Input('transit_pattern', 'value')
    )
def disable_options(transit_pattern):
    if transit_pattern==pattern_list[0]:
        return [
                    {'label': wfh_list[0], 'value': wfh_list[0], 'disabled': True},
                    {'label': wfh_list[1], 'value': wfh_list[1], 'disabled': True},
                    {'label': wfh_list[2], 'value': wfh_list[2], 'disabled': True},
                ]
    else:
        return [
                    {'label': wfh_list[0], 'value': wfh_list[0], 'disabled': False},
                    {'label': wfh_list[1], 'value': wfh_list[1], 'disabled': False},
                    {'label': wfh_list[2], 'value': wfh_list[2], 'disabled': False},
                ]


@app.callback(
    Output('map_graphic', 'figure'),
    [
        Input("transit_pattern", "value"),  
        Input("wfh_level", "value"),
        Input('tabs-with-classes', 'value'),
        Input('layer', 'value'),
     ],
    )
def update_map_graph(transit_pattern,wfh_level,tab,layer):
    if transit_pattern==pattern_list[0]:
        comm_df = commuter_model_0.copy()
    else:
        commuter_model_of_choice_idx = transit_pattern + "+" + wfh_level
        comm_df = available_commuter_models[commuter_model_of_choice_idx].copy()

    comm_df['sequence']=comm_df.groupby(['PUMAKEY_HOME']).cumcount()
    location_test['sequence']=location_test.groupby(['PUMAKEY_HOME']).cumcount()
    comm_df = comm_df.merge(right=location_test[['PUMAKEY_HOME','sequence','lat','lon']], on=["sequence","PUMAKEY_HOME"], how='left')

    mode_order = CategoricalDtype(['Walk','Escooter','Bicycle','Ferry','WFH','Autos','Bus','Motorcycle','Taxicab','CommuterRail','Subway','Other'],ordered=True)
    comm_df['Reassigned'] = comm_df['Reassigned'].astype(mode_order)
    comm_df.sort_values(by=['Reassigned'],ascending=False,inplace=True)

    comm_df.rename({'PERWT':'Commuters', 'Reassigned':'Travel_Mode'},axis=1,inplace=True)
    comm_df['size'] = 1

    if layer==' Commuting':
        fig = px.scatter_mapbox(comm_df, 
                                lat="lat", lon="lon", hover_name="Travel_Mode", color="Travel_Mode", 
                                size="size", 
                                size_max=2, 
                                zoom=8,
                                color_discrete_map=color__dict,
                                hover_data=dict(lat=False, lon=False, size=False, Travel_Mode=False, Commuters=True),
                                )
    else:
        # https://plotly.com/python/lines-on-mapbox/
        plant_df['size'] = 1
        fig = px.scatter_mapbox(plant_df, lat="Y", lon="X", hover_name="PowerPlants", color="PowerPlants", 
                                color_discrete_map=color_plant_dict,
                                hover_data=dict(Y=False, X=False), size="size", size_max=7,
                                zoom=8
                                )

        fig.add_trace(go.Scattermapbox(
                        name = 'Transmission Lines',
                        mode = "lines",
                        lon = lons,
                        lat = lats,
                        marker = {'color':'lightgrey'}
                        ))              

        fig.add_trace(go.Scattermapbox(
            name = 'Substations',
            lon = station_df.lon,
            lat = station_df.lat,
            showlegend=False,
            marker = {'size':3, 'color':'grey'}
            ))

    fig.update_layout(mapbox_style="carto-positron")
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    fig.update_layout(legend = dict(bgcolor='rgba(255,255,255,0.7)'))
    fig.update_layout(legend=dict(x=0.03, y=0.97, traceorder="reversed", font=dict(size=11)))
    if tab=='tab-1':
        fig.update_layout(height=730)
    else:
        fig.update_layout(height=390)
    return fig


@app.callback(
    Output('map_graphic_s', 'figure'),
    [
        Input("transit_pattern", "value"),  
        Input("wfh_level", "value"),
        Input('tabs-with-classes', 'value'),
     ],
    )
def update_map_graph_small(transit_pattern,wfh_level,tab):
    if transit_pattern==pattern_list[0]:
        comm_df = commuter_model_0.copy()
    else:
        commuter_model_of_choice_idx = transit_pattern + "+" + wfh_level
        comm_df = available_commuter_models[commuter_model_of_choice_idx].copy()
    comm_df['sequence']=comm_df.groupby(['PUMAKEY_HOME']).cumcount()
    location_test['sequence']=location_test.groupby(['PUMAKEY_HOME']).cumcount()
    comm_df = comm_df.merge(right=location_test[['PUMAKEY_HOME','sequence','lat','lon']], on=["sequence","PUMAKEY_HOME"], how='left')

    mode_order = CategoricalDtype(['Walk','Escooter','Bicycle','Ferry','WFH','Autos','Bus','Motorcycle','Taxicab','CommuterRail','Subway','Other'],ordered=True)
    comm_df['Reassigned'] = comm_df['Reassigned'].astype(mode_order)
    comm_df.sort_values(by=['Reassigned'],ascending=False,inplace=True)

    comm_df.rename({'PERWT':'Number_of_Commuters', 'Reassigned':'Travel Mode'},axis=1,inplace=True)
    comm_df['size'] = 1

    fig = px.scatter_mapbox(comm_df, 
                            lat="lat", lon="lon", hover_name="Travel Mode", color="Travel Mode", 
                            size="size", 
                            size_max=2, 
                            zoom=7.5,
                            color_discrete_map=color__dict,
                            hover_data=dict(lat=False, lon=False, size=False, Number_of_Commuters=True),
                            )

    fig.update_layout(mapbox_style="carto-positron")
    # fig.update_layout(mapbox_style="carto-darkmatter")
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    fig.update_layout(legend = dict(bgcolor='rgba(0,0,0,0)'))
    fig.update_layout(legend=dict(x=0.03, y=0.97, traceorder="reversed", font=dict(size=11)))
    if tab=='tab-1':
        fig.update_layout(height=730)
    else:
        fig.update_layout(height=390)
    return fig


@app.callback(
    Output('pev_delay_choice', 'options'),
    Input('Detailed', 'on')
    )
def disable_options(Detailed):
    if Detailed:
        return [
                {'label': 'Random', 'value': 'Random', 'disabled': False},
                {'label': 'Earliest', 'value': 'Earliest', 'disabled': False},
                {'label': 'Latest', 'value': 'Latest', 'disabled': False},
                {'label': 'Custom - 3 hr.', 'value': 'Custom', 'disabled': False}
            ]
    else:
        return [
                {'label': 'Random', 'value': 'Random', 'disabled': True},
                {'label': 'Earliest', 'value': 'Earliest', 'disabled': True},
                {'label': 'Latest', 'value': 'Latest', 'disabled': True},
                {'label': 'Custom - 3 hr.', 'value': 'Custom', 'disabled': True}
            ]


@app.callback(
    [
        Output('electric_graphic', 'figure'),
        Output("total_energy_text", "children"),
        Output("trans_energy_text", "children"),
        Output("peak_power_text", "children"),
    ],
    [
        Input("transit_pattern", "value"),   
        Input("wfh_level", "value"),
        Input('Detailed','on'),
        Input('pev_delay_choice', 'value'),
        Input('season', 'value'),
        Input('wind_level', 'value'),
    ],
    )
def update_electric_graph(transit_pattern,wfh_level,Detailed,pev_delay_choice,season,wind_level):
    if transit_pattern==pattern_list[0]:
        com_df = electric_model_0.copy()
    else:
        commuter_model_of_choice_idx = transit_pattern + "+" + wfh_level
        com_df = available_electric_models[commuter_model_of_choice_idx].copy() 

    condition = (season + "_" + wind_level).lower()
    load_df = maxload_profiles[maxload_profiles['key']==condition]
    
    e_tmp_profile = e_profile_hold_space(com_df)
    
    c = str(int(e_tmp_profile['Energy'].max()))
    b = str(int(e_tmp_profile[e_tmp_profile['PEV_DELAY']=='Random']['Energy'].sum()))

    e_tmp_profile = e_tmp_profile.merge(right=load_df, on=["Charge_Hour"])
    e_tmp_profile['Energy'] = e_tmp_profile['Energy'] + e_tmp_profile['baseload']

    a = str(int(e_tmp_profile[e_tmp_profile['PEV_DELAY']=='Random']['Energy'].sum()))

    fig = px.line(e_tmp_profile, x='Charge_Hour', y='Energy', color='PEV_DELAY', markers=False,
                  labels=dict(Charge_Hour="Time of day (hr)", TransMode="Travel Mode", Energy="Power (MW)", PEV_DELAY="Delay Type"))
    fig.add_trace(go.Scatter(x=load_df.Charge_Hour.to_list(), y=load_df.maxload.to_list(), name='Maxload*', line=dict(color='gold', width=3)))
    fig.add_trace(go.Scatter(x=load_df.Charge_Hour.to_list(), y=load_df.baseload.to_list(), name='Baseload*', line=dict(color='orange', width=3, dash='dot')))
    layout_elec = copy.deepcopy(layout)
    layout_elec["height"] = 240
    fig.update_layout(layout_elec)
    fig.update_layout(xaxis_title=None)
    fig.update_layout(legend=dict(orientation="v", y=1, x=1))
    fig.update_xaxes(range = [0,23], showline=True, linewidth=1, linecolor='grey')
    fig.update_yaxes(range = [0,3500], showline=True, linewidth=1, linecolor='grey')

    if Detailed:
        df_plot = com_df.copy()
        df_plot = df_plot[df_plot["PEV_DELAY"]==pev_delay_choice].copy()
        df_plot['Energy'] = df_plot['Energy']/1000
        df_plot['TransMode'] = df_plot['TransMode'].astype("string")
        df_plot['TransMode'] = df_plot["TransMode"].replace(mode_dict_2)
        gb_plot = df_plot.groupby(by=["Charge_Hour","TransMode"]).agg({"Energy":"sum"}).reset_index()
        
        load_df_mode = load_df[['Charge_Hour','baseload']].rename({'baseload':'Energy'},axis=1)
        load_df_mode['TransMode'] = 'Baseload*'
        gb_plot = pd.concat([gb_plot, load_df_mode])  

        sum_energy_by_mode = gb_plot.groupby(by=["TransMode"]).agg({"Energy":"sum"}).rename({'Energy':'sum'},axis=1).reset_index()
        gb_plot = gb_plot.merge(right=sum_energy_by_mode, on=["TransMode"])

        gb_plot.sort_values(by=['sum'],ascending=False,inplace=True)
        fig = px.area(gb_plot,x='Charge_Hour',y='Energy',color='TransMode',markers=False, 
                      color_discrete_map=color__dict,
                      labels=dict(Charge_Hour="Hour of Day", TransMode="Travel Mode", Energy="Power (MW)"))
        fig.add_trace(go.Scatter(x=load_df.Charge_Hour.to_list(), y=load_df.maxload.to_list(), name='Maxload*', line=dict(color='gold', width=3)))
        fig.update_xaxes(range = [0,23], showline=True, linewidth=1, linecolor='grey')
        fig.update_yaxes(range = [0,3500], showline=True, linewidth=1, linecolor='grey')
        fig.update_layout(layout_elec)
        fig.update_layout(legend=dict(orientation="v", y=1, x=1))
        fig.update_layout(xaxis_title=None)
        
    return fig, a + " MWh", b + " MWh", c + " MW"


@app.callback(
    Output('flow_graphic', 'figure'),
    [
        Input("transit_pattern", "value"),   
        Input("wfh_level", "value"),
    ],
    )
def update_flow_graph(transit_pattern,wfh_level):
    if transit_pattern==pattern_list[0]:
        com_df = commuter_model_0.copy()
    else:
        commuter_model_of_choice_idx = transit_pattern + "+" + wfh_level
        com_df = available_commuter_models[commuter_model_of_choice_idx].copy()

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
    [
        Input("transit_pattern", "value"),    
        Input("wfh_level", "value"),    
    ],
    )
def update_map_graph(transit_pattern,wfh_level):
    if transit_pattern==pattern_list[0]:
        com_df = commuter_model_0.copy()
    else:
        commuter_model_of_choice_idx = transit_pattern + "+" + wfh_level
        com_df = available_commuter_models[commuter_model_of_choice_idx].copy()

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
    [
        Input("transit_pattern", "value"),  
        Input("wfh_level", "value"),
    ],
    )
def update_share_graph(transit_pattern,wfh_level):
    if transit_pattern==pattern_list[0]:
        com_df = commuter_model_0.copy()
    else:
        commuter_model_of_choice_idx = transit_pattern + "+" + wfh_level
        com_df = available_commuter_models[commuter_model_of_choice_idx].copy()

    share_df = com_df.groupby(by=["Reassigned","Reassigned_Parent"]).agg({"PERWT":"sum"}).reset_index()\
                .rename({'Reassigned':'Mode','Reassigned_Parent':'Mode_Parent'},axis=1)
    share_df['ALL'] = '~2.7M Workers'
    share_df['pct_mode'] = round(100*share_df['PERWT']/share_df['PERWT'].sum(),2)
    share_df.rename({'PERWT':'Number_of_Commuters'},axis=1,inplace=True)
    fig = px.sunburst(
                        share_df, 
                        path=['ALL','Mode_Parent','Mode'], 
                        values='Number_of_Commuters',
                        color='Mode_Parent',
                        color_discrete_map={
                            'Transit':'#636EFA', 
                            'Micro':'#FECB52', 
                            'WFH':'#72B7B2', 
                            'Car':'#FF6692',
                            '(?)':'white'
                            }
                    )
    layout_share = copy.deepcopy(layout)
    layout_share["height"] = 280
    fig.update_layout(layout_share)
    fig.update_traces(marker_line_color='white',marker_line_width=1)
    fig.update_traces(hovertemplate='<b>%{value} Commuters</b>')  # parent, or label, or id, or value

    return fig


@app.callback(
    Output('subregion_graphic', 'figure'),
    [
        Input("transit_pattern", "value"), 
        Input("wfh_level", "value"),
    ],
    )
def update_subregion_graph(transit_pattern,wfh_level):
    if transit_pattern==pattern_list[0]:
        com_df = commuter_model_0.copy()
    else:
        commuter_model_of_choice_idx = transit_pattern + "+" + wfh_level
        com_df = available_commuter_models[commuter_model_of_choice_idx].copy()
    
    gb_plot = com_df.groupby(by=["Subregion","Reassigned"]).agg({"PERWT":"sum"}).reset_index()

    ### order: most or stable on bottom, now use most
    sum_subregion = gb_plot.groupby(by=["Reassigned"]).agg({"PERWT":"sum"}).rename({'PERWT':'sum'},axis=1).reset_index()
    gb_plot = gb_plot.merge(right=sum_subregion, on=["Reassigned"])
    gb_plot.sort_values(by=['sum'],ascending=False,inplace=True)
    
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
    fig.update_layout(barmode='stack', yaxis={'categoryorder':'array', 'categoryarray':['Other','CT','Hud','LI','NJ','Non-MNY Boros','Manhattan']})
    fig.update_layout(yaxis_title=None,xaxis_title=None)
    fig.update_layout(showlegend=True)
    fig.update_layout(legend=dict(orientation="v", y=1, x=1))
    return fig


# Run the server
if __name__ == "__main__":
    app.run_server(debug=True)