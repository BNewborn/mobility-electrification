# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from dash import Dash, dcc, html, Input, Output
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from pandas.api.types import CategoricalDtype

app = Dash(__name__)

### read the orginal data
save_dir = "../commuter_model_outputs"
commuter_model_1 = pd.read_pickle(f"{save_dir}/commuter_model_alltransit_dfaggregate.pkl")
commuter_model_2 = pd.read_pickle(f"{save_dir}/commuter_model_allmicro_dfaggregate.pkl")
commuter_model_3 = pd.read_pickle(f"{save_dir}/commuter_model_mix_dfaggregate.pkl")
subregion_reference = pd.read_csv(f"{save_dir}/subregion_reference_table.csv",index_col=0)

save_dir_e = "../electric_model_outputs"
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
    df = df.merge(right=subregion_reference, on=["PUMAKEY_HOME"])
    df['LEAVE_WORK_HOUR'] = (df['ARRIVES_AT_WORK_HOUR'] + np.ceil(df['HRS_WK_DAILY']).astype(int))%24
    df['Current'] = df["MODE_TRANSP_TO_WORK"].replace(mode_dict_1)
    df['Reassigned'] = df["First_Assignment"].replace(mode_dict_2)
    df['Current_Parent'] = df["Current"].replace(mode_dict_3)
    df['Reassigned_Parent'] = df["Reassigned"].replace(mode_dict_3)
    df['MNY_RES'] = df['PUMAKEY_HOME'].apply(lambda x: 1 if x.startswith('36_038') else 0)
    df['distance_row_sum'] = df['DISTANCE_KM']*df['PERWT']
    return df



def share_comparison(df):
    Current = df.groupby(by=["Current"]).agg({"PERWT":"sum"}).reset_index()\
                .rename({'Current':'Mode','PERWT':'Current'},axis=1)
    Reassigned = df.groupby(by=["Reassigned"]).agg({"PERWT":"sum"}).reset_index()\
                   .rename({'Reassigned':'Mode','PERWT':'Reassigned'},axis=1)
    compare = Current.merge(right=Reassigned, on=["Mode"], how='outer').fillna(0)
    compare['Current'] = (compare['Current']/compare['Current'].sum()*100).astype(float).round(1) 
    compare['Reassigned'] = (compare['Reassigned']/compare['Reassigned'].sum()*100).astype(float).round(1) 
    order = CategoricalDtype(['Autos','Subway','CommuterRail',
                              'Bus','Ferry','Escooter','Bicycle','Walk',
                              'WFH','Motorcycle','Taxicab','Other'],ordered=True)
    compare['Mode'] = compare['Mode'].astype(order)
    compare.sort_values('Mode',inplace=True)
    return compare

# def share_comparison(df):
#     Current = df.groupby(by=["Current_Parent"]).agg({"PERWT":"sum"}).reset_index()\
#                 .rename({'Current_Parent':'Mode','PERWT':'Current'},axis=1)
#     Reassigned = df.groupby(by=["Reassigned_Parent"]).agg({"PERWT":"sum"}).reset_index()\
#                    .rename({'Reassigned_Parent':'Mode','PERWT':'Reassigned'},axis=1)
#     compare = Current.merge(right=Reassigned, on=["Mode"], how='outer').fillna(0)
#     compare['Current'] = (compare['Current']/compare['Current'].sum()*100).astype(float).round(1) 
#     compare['Reassigned'] = (compare['Reassigned']/compare['Reassigned'].sum()*100).astype(float).round(1)
#     order = CategoricalDtype(['Transit','Car','Micro','WFH','Other'],ordered=True)
#     compare['Mode'] = compare['Mode'].astype(order)
#     compare.sort_values('Mode',inplace=True)    
#     return compare

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
#     subregion = subregion.pivot_table(values='PERWT',index=['Reassigned'],columns='Subregion')\
#                          .fillna(0).astype(int).reset_index()
#     subregion.columns.name = ''
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
    e_tmp_profile = e_tmp_profile.groupby(by=["Charge_Hour","PEV_DELAY"])\
                                 .agg({"Energy":"sum"}).reset_index()
#     e_tmp_profile = e_tmp_profile.pivot_table(values='Energy',
#                                               index=['Charge_Hour'],
#                                               columns='PEV_DELAY').reset_index()
#     e_tmp_profile.columns.name = ''
    return e_tmp_profile

commuter_model_1 = df_processing(commuter_model_1)
commuter_model_2 = df_processing(commuter_model_2)
commuter_model_3 = df_processing(commuter_model_3)


### 
available_commuter_models = {"Max Transit":commuter_model_1
                             ,"Max Micro-mobility":commuter_model_2
                             ,"Mix of Everything":commuter_model_3}
available_electric_models = {"Max Transit":electric_model_1
                             ,"Max Micro-mobility":electric_model_2
                             ,"Mix of Everything":electric_model_3}

app.layout = html.Div(children=[   
    html.Div([
            dcc.RadioItems(
                list(available_commuter_models.keys()),
                list(available_commuter_models.keys())[0],
                id='commuter_model_of_choice_idx'),
        ], style={'display': 'inline-block'}),
    html.Div(dcc.Graph(id='comparison-graphic')),
    html.Div(dcc.Graph(id='flag-graphic')),
    html.Div(dcc.Graph(id='subregion-graphic')),
    html.Div(dcc.Graph(id='flow-graphic')),
    html.Div(dcc.Graph(id='electric-graphic')),
    ])


### 
@app.callback(
    Output('comparison-graphic', 'figure'),
    Input('commuter_model_of_choice_idx','value'),
    )
def update_comparison_graph(commuter_model_of_choice_idx):
    com_df = available_commuter_models[commuter_model_of_choice_idx]
    compare = share_comparison(com_df)
    
    top_labels = compare.Mode.to_list()

    colors = ['rgba(38, 24, 74, 0.8)', 'rgba(71, 58, 131, 0.8)',
              'rgba(122, 120, 168, 0.8)', 'rgba(164, 163, 204, 0.85)',
              'rgba(190, 192, 213, 1)', 'rgba(38, 24, 74, 0.8)', 'rgba(71, 58, 131, 0.8)',
              'rgba(122, 120, 168, 0.8)', 'rgba(164, 163, 204, 0.85)',
              'rgba(190, 192, 213, 1)', 'rgba(38, 24, 74, 0.8)', 'rgba(71, 58, 131, 0.8)',
              'rgba(122, 120, 168, 0.8)', 'rgba(164, 163, 204, 0.85)',
              'rgba(190, 192, 213, 1)']

    x_data = [compare.Reassigned.to_list(), compare.Current.to_list()]

    y_data = ['Reassigned', 'Current']

    fig = go.Figure()

    for i in range(0, len(x_data[0])):
        for xd, yd in zip(x_data, y_data):
            fig.add_trace(go.Bar(
                x=[xd[i]], y=[yd],
                orientation='h',
                marker=dict(
                    color=colors[i],
                    line=dict(color='white', width=2)
                           )
            ))

    fig.update_layout(
        xaxis=dict(
            showgrid=False,
            showline=False,
            showticklabels=False,
            zeroline=False,
            domain=[0.15, 1]
        ),
        yaxis=dict(
            showgrid=False,
            showline=False,
            showticklabels=False,
            zeroline=False,
        ),
        barmode='stack',
        paper_bgcolor='rgb(255, 255, 255)',
        plot_bgcolor='rgb(255, 255, 255)',
        margin=dict(l=10, r=10, t=140, b=80),
        showlegend=False,
    )

    annotations = []

    for yd, xd in zip(y_data, x_data):
        # labeling the y-axis
        annotations.append(dict(xref='paper', yref='y',
                                x=0.14, y=yd,
                                xanchor='right',
                                text=str(yd),
                                font=dict(family='Arial', size=14, color='rgb(67, 67, 67)'),
                                showarrow=False, align='right'))
        # labeling the first percentage of each bar (x_axis)
        annotations.append(dict(xref='x', yref='y',
                                x=xd[0] / 2, y=yd,
                                text=str(int(xd[0])) + '%',
                                font=dict(family='Arial', size=14, color='rgb(248, 248, 255)'),
                                showarrow=False))
        # labeling the first Likert scale (on the top)
        if yd == y_data[-1]:
            annotations.append(dict(xref='x', yref='paper',
                                    x=xd[0] / 2, y=1.1,
                                    text=top_labels[0],
                                    font=dict(family='Arial', size=14, color='rgb(67, 67, 67)'),
                                    showarrow=False))
        space = xd[0]
        for i in range(1, len(xd)):
            # labeling the rest of percentages for each bar (x_axis)
            annotations.append(dict(xref='x', yref='y',
                                    x=space + (xd[i]/2), y=yd,
                                    text=str(int(xd[i])) + '%',
                                    font=dict(family='Arial', size=14, color='rgb(248, 248, 255)'),
                                    showarrow=False))
            # labeling the Likert scale
            if yd == y_data[-1]:
                annotations.append(dict(xref='x', yref='paper',
                                        x=space + (xd[i]/2), y=1.1,
                                        text=top_labels[i],
                                        font=dict(family='Arial', size=14, color='rgb(67, 67, 67)'),
                                        showarrow=False))
            space += xd[i]

    fig.update_layout(title = "Share of Modes <i>Current</i> vs <i>Reassigned</i>",
        annotations=annotations)
    
    return fig


### 
@app.callback(
    Output('flag-graphic', 'figure'),
    Input('commuter_model_of_choice_idx','value'),
    )
def update_flag_graph(commuter_model_of_choice_idx):
    com_df = available_commuter_models[commuter_model_of_choice_idx]
    flag_df = flag_assign(com_df)

    fig = go.Figure()

    fig.add_trace(go.Barpolar(
        r=flag_df.Reassigned.to_list(),
        name='Reassigned',
        marker_color='rgb(106,81,163)',
        theta=flag_df.Mode.to_list(),
    ))

    fig.add_trace(go.Barpolar(
        ### just for right length
        r=[x - y for x, y in zip(flag_df.Eligible.to_list(),flag_df.Reassigned.to_list())],
        name='Eligible',
        marker_color='rgb(203,201,226)',
        theta=flag_df.Mode.to_list(),   
    ))

    fig.update_traces(text=flag_df.Mode.to_list())
    fig.update_layout(
        title='Number of Commuters <i>Eligible</i> vs <i>Reassigned</i>',
        font_size=12,
        legend_font_size=14,
        polar_radialaxis_ticksuffix=' ',
        polar_angularaxis_rotation=180,
    )    
    
    return fig

### 
@app.callback(
    Output('subregion-graphic', 'figure'),
    Input('commuter_model_of_choice_idx','value'),
    )
def update_subregion_graph(commuter_model_of_choice_idx):
    com_df = available_commuter_models[commuter_model_of_choice_idx]
    gb_plot = subregion(com_df)
    fig = px.bar(gb_plot, x="PERWT", y="Subregion", color='Reassigned', 
                 orientation='h',
                 hover_data=["Reassigned", "PERWT"],
                 height=450,
                 title='Number of Commuters by Subregion')
    return fig


### 
@app.callback(
    Output('flow-graphic', 'figure'),
    Input('commuter_model_of_choice_idx','value'),
    )
def update_flow_graph(commuter_model_of_choice_idx):
    com_df = available_commuter_models[commuter_model_of_choice_idx]
    flow = traffic_flow(com_df)
    fig = px.line(flow, x='Hour', y='PERWT', color='Dir', 
                  height=400, markers=True, 
                  title='Manhattan Commuting Flows')
    return fig

### 
@app.callback(
    Output('electric-graphic', 'figure'),
    Input('commuter_model_of_choice_idx','value'),
    )
def update_electric_graph(commuter_model_of_choice_idx):
    com_df = available_electric_models[commuter_model_of_choice_idx]
    e_tmp_profile = e_profile_hold_space(com_df)
    fig = px.line(e_tmp_profile, x='Charge_Hour', y='Energy', color='PEV_DELAY', 
                  height=400, markers=True, 
                  title="Energy Profile of Manhattan's Home-Work Commuting Activities")
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
