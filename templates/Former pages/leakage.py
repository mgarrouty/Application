import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
import pandas as pd
import plotly.graph_objects as go
from dash import ALL, dash_table, dcc, html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from numpy import NaN, empty

from templates import base, utils



def leakage_content():
    return html.Div(html.P("No line selected."), id="leak-content")


tab_header = dbc.Tabs(
    [dbc.Tab(label="Monitoring Overview",   tab_id="leak-overview"),
     dbc.Tab(label="Line Measurements",  tab_id="leak-diag", disabled=True),
     dbc.Tab(label="Line Configuraiton",   tab_id="leak-options", disabled=True)],
    id="leak-card-tabs",
    active_tab="leak-overview",)


def get_elements_from_id(id):
    element = None
    for item in SIDEBAR_CONFIG["elements"]:
        button_id = "leak-button-"+str(item["id"])
        if button_id == id:
            element = item
    return element


SIDEBAR_CONFIG = {"elements": [
    {
        "name": "Line 1",
        "meta": {
                "ECS": "ECS code: x1234",
                "POS": "Position: Line monitors the main containment.",
                "DES": "Description: Generic description for leakage line 1"
        },
        "id": 0,
        "channels": ["Section1", "Monitoring1", "Monitoring2"],
    }
],
    "length": 1}



class LeakData:
    Header = pd.read_csv("./data/leakage/Header.CSV", sep=";")
    Section1 = pd.read_csv("./data/leakage/Section1.CSV", sep=";", decimal=".")
    Polygon = pd.read_csv("./data/leakage/Polygon.CSV", sep=";", decimal=".")
    Monitoring1 = pd.read_csv("./data/leakage/Monitoring1.CSV", sep=";").drop(0)
    Monitoring2 = pd.read_csv("./data/leakage/Monitoring2.CSV", sep=";").drop(0)


def sidebar_listgroup(input=SIDEBAR_CONFIG, active_button_id=""):
    thing = []
    if int(input["length"]) > 0:
        for item in input["elements"]:
            runs = "🟢"
            list_groupitem = utils.sidebar_list_group_item(
                "leak", item["id"], active_button_id, item["name"], runs)
            thing.append(list_groupitem)
    else:
        thing.append(dbc.ListGroupItem(html.P("No Data after Filter.")))
    return dbc.ListGroup(thing, id="pumps_selection")


def filter_sidebar(value, active_button_id):
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

empty_page= html.P("No leak selected")
def create_content(button_id):
    element = get_elements_from_id(button_id)
    if element is None:
        return empty_page

    alert = dbc.Alert(
        "Only a single run exists in the history.",
        color="warning",
        dismissable=True,
        fade=False,
        is_open=True,
    )

    header = [alert, html.H2(element["name"]),
              html.Hr(),
              html.P(element["meta"]["ECS"]),
              html.P(element["meta"]["POS"]),
              html.P(element["meta"]["DES"])]
    tab_content = html.Div([], id="leak-tab-content")
    header = dbc.CardHeader(header)
    body = dbc.CardBody([tab_header, tab_content])
    card = dbc.Card([header, body])
    return card


def sidebar_content(input=SIDEBAR_CONFIG, active_button_id=""):
    outputdata = sidebar_listgroup(input, active_button_id)
    card = utils.sidebar_card_layout("leak", outputdata, "Filter Lines")
    return card


def build_monitoring_tab(element):
    table = build_runs_table(element["name"])
    runs = dbc.ListGroup(table, flush=True, id="valved_selection")
    span_style = {"textDecoration": "underline", "cursor": "pointer"}
    col = dbc.Row(
        [dbc.Col(html.Div("Last run results:")), dbc.Col()])
    header = dbc.CardHeader(col)
    body = dbc.CardBody(runs)
    internal_card = dbc.Card([header, body])
    return internal_card


def create_table(df):
    columns, values = df.columns, df.values
    header = [html.Tr([html.Th(col) for col in columns])]
    rows = [html.Tr([html.Td(cell) for cell in row]) for row in values]
    table = [html.Thead(header), html.Tbody(rows)]
    return table


def build_runs_table(name):
    if name is not None:
        df = LeakData.Header
        df = df.drop(df.columns[2:], axis=1)
        data = create_table(df)
        table = html.Div(data, id='datatable-interactivity-container')
        loading = dcc.Loading(id='loading', children=[table], type="circle")
        return loading


def leaks_callback(app):
    @app.callback(
        [Output("leak-sidebar-content", "children"),
         Output("leak-filter", "value"),
         Output("leak-content", "children")],
        [Input("leak-filter-button", "n_clicks"),
         Input({'type': 'leak-button', 'index': ALL}, 'n_clicks')],
        State("leak-filter", "value"), prevent_initial_call=True)
    def filter_func(n_clicks, vbut_nclicks, value):
        ctx = dash.callback_context
        button_id = ctx.triggered_id
        if button_id is None:
            raise PreventUpdate
        if type(button_id) is dash._utils.AttributeDict:
            button_id = button_id["index"]
        sidebar = filter_sidebar(value, button_id)
        content = create_content(button_id)
        return sidebar, value, content

    @app.callback(Output('leak-tab-content', 'children'),
                  Input('leak-card-tabs', "active_tab"),
                  [State({'type': 'leak-button', 'index': ALL}, 'id'),
                   State({'type': 'leak-button', 'index': ALL}, 'active')])
    def render_content(tab, button_id, active):
        if type(button_id) is dash._utils.AttributeDict or list:
            button_id = button_id[active.index(True)]["index"]
        element = get_elements_from_id(button_id)
        if element is None:
            PreventUpdate
        if tab == "leak-overview":
            internal_card = build_monitoring_tab(element)
            return internal_card
        if tab == "leak-diag":
            header = dbc.CardHeader()
            body = dbc.CardBody([html.Div(id="leak-radial-output")])
            card = dbc.Card([header, body])
            return card
        return empty_page

    @app.callback(Output("leak-radial-output", "children"),
                  [Input("leak-ad-value-list", "value")],
                  [State({'type': 'leak-button', 'index': ALL}, 'id'),
                   State({'type': 'leak-button', 'index': ALL}, 'active')])
    def display_value(value, button_id, active):
        if type(button_id) is dash._utils.AttributeDict or list:
            button_id = button_id[active.index(True)]["index"]
        element = get_elements_from_id(button_id)
        if element is None:
            PreventUpdate
        if value is None:
            return html.P("No value selection")
        if len(value) == 0:
            return html.P("No value selection")
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=LeakData.Polygon["Location"], y=LeakData.Polygon["X Effective"], name=value, mode='lines+markers'))
        fig.update_yaxes(showticklabels=False)

        fig['layout']['showlegend'] = False

        return dcc.Graph(id="graph", figure=fig)
