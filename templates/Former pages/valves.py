import dash
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import ALL, dash_table, dcc, html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from numpy import NaN, empty
import functools

from templates import base, utils,styleutils
from templates import callbacksrefactor as cbr

#We define the differents Valves that appears (refactor it ?)
SIDEBAR_CONFIG = {
    "elements": [
        {
            "name": "Valve 1",
            "meta": {
                "ECS": "ECS code: a1234",
                "POS": "Position: Compartment 1",
                "DES": "Description: Generic description for Valve 1"
            },
            "id": 0,
        },
        {
            "name": "Valve 2",
            "meta":
            {
                "ECS": "ECS code: b1234",
                "POS": "Position: Compartment 2",
                "DES": "Description: Generic description for Valve 2"
            },
            "id": 1,
        },
        {
            "name": "Valve 3",
            "meta":
            {
                "ECS": "ECS code: c1234",
                "POS": "Position: Compartment 3",
                "DES": "Description: Generic description for Valve 3"
            },
            "id": 2,
        },
        {
            "name": "Valve 4",
            "meta":
            {
                "ECS": "ECS code: d1234",
                "POS": "Position: Compartment 4",
                "DES": "Description: Generic description for Valve 4"},
            "id": 3,
        },
        {
            "name": "Valve 5",
            "meta":
            {"ECS": "ECS code: e1234",
             "POS": "Position: Compartment 5",
             "DES": "Description: Generic description for Valve 5"
             },
            "id": 4,
        }],
    "length": 5
}

#We define class Valves
class ValvesData:
    #This should be attributes defined for each valves
    Messungen = pd.read_excel(
        "./data/Valves/Messungen.xlsx", sheet_name="ForMockup")
    Example_1 = pd.read_csv("./data/Valves/Example_1.CSV", sep=";", decimal=",").drop(
        ["Sample", "Time.1", "Unnamed: 13"], axis=1)

    #List of parameters of a run (for display), to be directly used in displaying options
    def runsfeatures() :
        thing = []
        for data in ValvesData.Example_1.columns:
            if data != "Time":
                thing.append({"label": data, "value": data})
        return(thing)

    def get_only_for_name(name):
        """
        Return the data only for the valve called name.
        """
        return ValvesData.Messungen[ValvesData.Messungen["KKS"] == name]

    def Bew_To_Emoji(int):
        """
        Return an emoji according to the value of int for Bew (legend in description)
        """
        if int == 0:
            return "🟢"
        if int > 0:
            return "🔴"
        if int < 0:
            return "🟡"

    def Result_To_Emoji(int):
        """
        Return an emoji according to the value of int for Results (legend in description)
        """
        if int == 1:
            return "🟢"
        if int == 3 or int == 4:
            return "🔴"
        if int == 2:
            return "🟡"
        if int != int:
            return ""
        return "◯"

    def Stats(df):
        """
        Return a list of Bew summed by values (negative, null and positive).
        """
        rest = []
        rest.append((df["Bew"] > 0).sum())
        rest.append((df["Bew"] == 0).sum())
        rest.append((df["Bew"] < 0).sum())
        return rest

    def Last_Runs_History(df, length):
        """
        Return the length last values of Bew to emoji from df, but we need to give df
        """
        results = df["Bew"].values
        runs = []
        for i in range(length):
            res = ValvesData.Bew_To_Emoji(results[i])
            runs.append(res)
        return runs



"""
tab_header = dbc.Tabs(
    [dbc.Tab(label="Monitoring Overview",   tab_id="valves-overview"),
     dbc.Tab(label="Advanced Diagnostics",  tab_id="valves-diag"),
     dbc.Tab(label="Valve Configuration",   tab_id="valves-options", disabled=True)],
    id="valve-card-tabs",
    active_tab="valves-overview",)
def get_elements_from_id(id):
    element = None
    for item in SIDEBAR_CONFIG["elements"]:
        button_id = "valve-button-"+str(item["id"])
        if button_id == id:
            element = item
    return element

def filter_sidebar(value, active_button_id):

    Allow to filter the values in the sidebar with text search.

    if value is None:
        return sidebar_content(SIDEBAR_CONFIG, active_button_id)
    if type(value) != str:
        return sidebar_content(SIDEBAR_CONFIG, active_button_id)
    if value == "":
        return sidebar_content(SIDEBAR_CONFIG, active_button_id)
    filtered_data = {}
    filtered_data["elements"] = []
    filtered_data["length"] = 0
    for item in SIDEBAR_CONFIG["elements"]:
        if value in item["name"]:
            filtered_data["elements"].append(item)
            filtered_data["length"] += 1
    return sidebar_content(filtered_data, active_button_id)

def create_content(button_id):
    element = utils.get_elements_from_id(button_id,"valve")
    if element is None:
        return empty_page
    header = [html.H2(element["name"]),
              html.Hr(),
              html.P(element["meta"]["ECS"]),
              html.P(element["meta"]["POS"]),
              html.P(element["meta"]["DES"])]
    tab_content = html.Div([], id="valve-tab-content")
    header = dbc.CardHeader(header)
    body = dbc.CardBody([tab_header, tab_content])
    card = dbc.Card([header, body])
    return card

    thing = []
    if int(input["length"]) > 0:
        for item in input["elements"]:
            runs = ValvesData.Last_Runs_History(
                ValvesData.get_only_for_name(item["name"]), 4)
            list_groupitem = utils.sidebar_list_group_item(
                "valve", item["id"], active_button_id, item["name"], runs)
            thing.append(list_groupitem)
    else:
        thing.append(dbc.ListGroupItem(html.P("No Data after Filter.")))
    return dbc.ListGroup(thing, id="valve_selection")
"""
#Defining html div of an element overview, with the feature options
valvestabs={'overview' : 'Monitoring Overview', 'diag' : 'Advanced Diagonostics', 'options':'Valve Configuration'}
tab_header = utils.tabs_from_dict(valvestabs, "valves", "Monitoring Overview")


def get_run_from_element(element,date) :
    """
    In its final form, this function is supposed to return the dataframe of the run at date of valve element (valve from the button id) (with InfluxDB). Here, it is once again just the example.
    """
    return pd.read_csv("data\Valves\Example_1.csv", sep=";", decimal=",").drop(
        ["Sample", "Time.1", "Unnamed: 13"], axis=1)

def valvesmainrun(item_name):
    return  ValvesData.Last_Runs_History(ValvesData.get_only_for_name(item_name), 4)

def sidebar_listgroup(input=SIDEBAR_CONFIG, active_button_id=""):
    return (utils.main_sidebar_listgroup(input, active_button_id, "valves",valvesmainrun))


def sidebar_content(input=SIDEBAR_CONFIG, active_button_id=""):
    outputdata = sidebar_listgroup(input, active_button_id)
    card = utils.sidebar_card_layout("valve", outputdata, "Filter Valves")
    return card



def build_runs_table(name):
    """
    Define the html datatable overview of the element "named". Useless information have been removed, and partial information have been merged (like opening and closing)
    """
    data = []
    if name is not None:
        df = ValvesData.get_only_for_name(name)
        df = df.drop("KKS", axis=1).drop("KKSNR", axis=1)
        df["Bew"] = df["Bew"].apply(lambda x: ValvesData.Bew_To_Emoji(x))
        list = df.columns.values.tolist()
        list = list[list.index("Bew")+1:]
        for col in list:
            df[col] = df[col].apply(lambda x: ValvesData.Result_To_Emoji(x))
        for i in range(int(len(list)/2)):
            i = 2 * i
            newname = list[i][2:-1]
            df[newname] = df[[list[i], list[i+1]]
                             ].astype(str).apply(lambda x: "".join(x), axis=1)
            df = df.drop(list[i], axis=1).drop(list[i+1], axis=1)
        data = dash_table.DataTable(id='datatable-interactivity',
                                    columns=[
                                        {"name": i, "id": i} for i in df.columns
                                    ],
                                    data=df.to_dict('records'),
                                    sort_action="native",
                                    sort_mode="multi",
                                    page_action="native",
                                    page_current=0,
                                    page_size=25,)
    table = html.Div([data, html.Div(id='datatable-interactivity-container')])
    loading = dcc.Loading(id='loading', children=[table], type="circle")
    return loading

vardict = {"sidebar_content" : sidebar_content, "SIDEBAR_CONFIG" : SIDEBAR_CONFIG, "tab_header" : tab_header}


def valves_callback(app):

    #Callback for filtering valves in the sidebar
    @app.callback(*cbr.filter('valve'), prevent_initial_call=True)
    def filter_func(n_clicks, vbut_nclicks, value):
        return utils.filter_func(n_clicks, vbut_nclicks, value, vardict,'valve')

    #Define the visualization options for a selected component.
    @app.callback(*cbr.rendercontent('valve'))
    def render_content(tab, button_id, active):
        if type(button_id) is dash._utils.AttributeDict or list:
            button_id = button_id[active.index(True)]["index"]
        element = utils.get_elements_from_id(button_id,"valve",SIDEBAR_CONFIG)
        if element is None:
            PreventUpdate
        if tab == "valves-overview":
            return styleutils.overview(build_runs_table(element["name"]),"valves")
        if tab == "valves-diag":
            return styleutils.head_diagnosis_multiples_runs(ValvesData.get_only_for_name(element["name"]),"valve","ErfDat",ValvesData.runsfeatures())
            """
            thing = []
            #Thing takes all label of Valves data but time, it is used to create the checklist of graph displaying.
            for data in ValvesData.Example_1.columns:
                if data != "Time":
                    thing.append({"label": data, "value":   data})

            df = ValvesData.get_only_for_name(element["name"])
            dropdown = dcc.Dropdown(
                df["ErfDat"], placeholder="Select a run", id="valves-ad-run")
            checklist = dbc.Checklist(
                id="valve-ad-value-list", options=thing, inline=True,)
            button_group = html.Div([checklist], className="radio-group",)
            header = dbc.CardHeader([dropdown, button_group])
            body = dbc.CardBody([html.Div(id="valve-radial-output")])
            card = dbc.Card([header, body])
            return card
            """
        else :
            return html.P("a thing")


#Display graph for the tab advanced diagnosis
    @app.callback(Output("valve-radial-output", "children"),
                  [Input("valve-ad-value-list", "value"),Input("valves-ad-run", "value")],
                  [State({'type': 'valve-button', 'index': ALL}, 'id'),
                   State({'type': 'valve-button', 'index': ALL}, 'active'),
                   ])
    def display_value(value, run, button_id, active):
        if type(button_id) is dash._utils.AttributeDict or list:
            button_id = button_id[active.index(True)]["index"]
        element = utils.get_elements_from_id(button_id,"valve",SIDEBAR_CONFIG)

        return styleutils.run_graph(element,run,'Time',value,get_run_from_element(element,run))
        """
        if element is None:
            PreventUpdate
        if run is None or "":
            return html.P("No run selected.")
        if value is None:
            return html.P("No value selection")
        if len(value) == 0:
            return html.P("No value selection")
        fig = go.Figure()
        for selection in value:
            # TODO: make sure different plots can get selected
            fig.add_trace(go.Scatter(
                x=ValvesData.Example_1["Time"], y=ValvesData.Example_1[selection], name=selection))
        fig.update_layout(title="Run from: " + run)
        return dcc.Graph(id="graph", figure=fig)
"""