import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from dash import ALL, dash_table, dcc, html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from templates import base, utils, styleutils
from templates import callbacksrefactor as cbr

SIDEBAR_CONFIG = {"elements": [
    {
        "name": "Pump 1",
        "meta": {
                "ECS": "ECS code: l1234",
                "POS": "Position: Main Pump Housing 1",
                "DES": "Description: Generic description for Pump 1"
        },
        "id": 0,
        "channels": ["S106", "S107", "K1"],
    },
    {
        "name": "Pump 2",
        "meta":
            {
                "ECS": "ECS code: m1234",
                "POS": "Position: Main Pump Housing 2",
                "DES": "Description: Generic description for Pump 2"
            },
        "id": 1,
            "channels": ["S206", "S207", "K2"],
    },
    {
        "name": "Pump 3",
        "meta":
            {
                "ECS": "ECS code: n1234",
                "POS": "Position: Main Pump Housing 3",
                "DES": "Description: Generic description for Pump 3"
            },
        "id": 2,
            "channels": ["S306", "S307", "K2"],
    },
],
    "length": 3}


class PumpsData:
    ChannelStatus = pd.read_csv(
        "./data/KIR/Features/ChannelStatusTable.csv", sep=";", decimal=",")
    FeatureStatus = pd.read_csv(
        "./data/KIR/Features/ChannelFeatureStatusTable.csv", sep=";", decimal=",")

    def List_of_Pumps():
        return ["Pump1, Pump2, Pump3"]

    def get_table_of_pump(name):
        for item in SIDEBAR_CONFIG["elements"]:
            if name is item["name"]:
                channels = []
                channels.append("Parameters")
                for thing in item["channels"]:
                    channels.append(thing)
                df = PumpsData.FeatureStatus[channels]
                return df
        pass

    def status_of_Pumps(name):
        for item in SIDEBAR_CONFIG["elements"]:
            if name is item["name"]:
                channels = item["channels"]
                df = PumpsData.FeatureStatus[channels]
                series = df.max()
                emoji = PumpsData.status_to_emoji(series.max())
                return emoji
        return "◯"

    def status_to_emoji(input):
        thing = int(input)
        if thing == 0:
            return "◯"
            # return "🔵"
        if thing == 1:
            return "🟢"
        if thing == 2:
            return "🟡"
        if thing == 3:
            return "🟠"
        if thing == 4:
            return "🔴"
        return "◯"

    def trend_of_pump(name):
        return [""]


pumpstabs={ "overview" : "Monitoring Overview", "diag" : "Longtime Trend View",  "options" : "Pump Configuration"}
tab_header = utils.tabs_from_dict(pumpstabs, "pumps", "Monitoring Overview")

def sidebar_listgroup(input=SIDEBAR_CONFIG, active_button_id=""):
    return(utils.main_sidebar_listgroup(input,active_button_id,"pumps",PumpsData.status_of_Pumps))

def sidebar_content(input=SIDEBAR_CONFIG, active_button_id=""):
    outputdata = sidebar_listgroup(input, active_button_id)
    card = utils.sidebar_card_layout("pump", outputdata, "Filter Pumps")
    return card


def build_monitoring_tab(element):
    table = build_runs_table(element["name"])
    runs = dbc.ListGroup(table, flush=True, id="valve_selection")
    span_style = {"textDecoration": "underline", "cursor": "pointer"}
    elem1 = html.Span("🟢", id="tooltip-success", style=span_style)
    elem3 = html.Span("🟡", id="tooltip-pre-warning", style=span_style)
    elem4 = html.Span("🟠", id="tooltip-warning", style=span_style)
    elem2 = html.Span("🔴", id="tooltip-failure", style=span_style)
    elem5 = html.Span("◯", id="tooltip-missing", style=span_style)
    legend = html.Div(
        html.P([elem1, elem3, elem4, elem2, elem5], style={'text-align': 'right'}))
    tt1 = dbc.Tooltip("Successful run.", target="tooltip-success")
    tt2 = dbc.Tooltip("Alarm.", target="tooltip-failure")
    tt3 = dbc.Tooltip("Potential warning. To be evaluated.",
                      target="tooltip-pre-warning")
    tt4 = dbc.Tooltip("Warning.", target="tooltip-warning")
    tt5 = dbc.Tooltip("Not configured.", target="tooltip-missing")
    tt = html.Div([tt1, tt2, tt3, tt4, tt5])
    col = dbc.Row(
        [dbc.Col(html.Div("Current Feature Status")), dbc.Col([legend, tt])])
    header = dbc.CardHeader(col)
    body = dbc.CardBody(runs)
    internal_card = dbc.Card([header, body])
    return internal_card


def build_runs_table(name):
    data = []
    if name is not None:
        df = PumpsData.get_table_of_pump(name)
        list = df.columns.values.tolist()
        list.remove("Parameters")
        for col in list:
            df[col] = df[col].apply(lambda x: PumpsData.status_to_emoji(x))
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
def pumps_callback(app):
    @app.callback(*cbr.filter('pump'), prevent_initial_call=True)
    def filter_func(n_clicks, vbut_nclicks, value):
        return utils.filter_func(n_clicks, vbut_nclicks, value, vardict,'pump')

    @app.callback(*cbr.rendercontent('pump'))
    def render_content(tab, button_id, active):
        if type(button_id) is dash._utils.AttributeDict or list:
            button_id = button_id[active.index(True)]["index"]
        element = utils.get_elements_from_id(button_id,'pump',SIDEBAR_CONFIG)
        if element is None:
            PreventUpdate
        if tab == "pumps-overview":
            return styleutils.overview(build_runs_table(element["name"]),"pumps")
        if tab == "pumps-diag":
            thing = []
            for channel in element["channels"]:
                thing.append({"label": channel, "value":   channel})
            checklist = dbc.RadioItems(options=thing,
                                       id="pumps-ad-value-list",  inline=True,)
            button_group = html.Div([checklist], className="radio-group",)
            header = dbc.CardHeader([button_group])
            body = dbc.CardBody([html.Div(id="pump-radial-output")])
            card = dbc.Card([header, body])
            return card
        return html.P('No pump selected')

    @app.callback(Output("pump-radial-output", "children"),
                  [Input("pumps-ad-value-list", "value")],
                  [State({'type': 'pump-button', 'index': ALL}, 'id'),
                   State({'type': 'pump-button', 'index': ALL}, 'active')])
    def display_value(value, button_id, active):
        if type(button_id) is dash._utils.AttributeDict or list:
            button_id = button_id[active.index(True)]["index"]
        element = utils.get_elements_from_id(button_id,'pump',SIDEBAR_CONFIG)
        if element is None:
            PreventUpdate
        if value is None:
            return html.P("No value selection")
        if len(value) == 0:
            return html.P("No value selection")
        #fig = go.Figure()
        #fig.add_trace(go.Scatter(
        #    x=PumpsData.ChannelStatus["Date_Time"], y=PumpsData.ChannelStatus[""+value+"-Status"].astype('int64'), name=value, mode='lines+markers'))

        #This way, we can display colored markers, but we have to remove coloraxes after
        fig=px.scatter(x=PumpsData.ChannelStatus["Date_Time"], y=PumpsData.ChannelStatus[""+value+"-Status"].astype('int64'), color=PumpsData.ChannelStatus[""+value+"-Status"].astype('int64'))
        fig.data[0].update(mode="markers+lines")
        fig.update_yaxes(showticklabels=False)

        colorbar_trace = go.Scatter(x=[None],
                                    y=[None],
                                    mode='markers',
                                    marker=dict(
            showscale=True,
            cmin=0,
            cmax=4,
            colorbar=dict(thickness=5, tickvals=[0, 1, 2, 3, 4], ticktext=[
                'No-Data', 'Ok', 'Pre-Warning', 'Warning', 'Alarm'], outlinewidth=0)
        ),
            hoverinfo='none'
        )
        fig.update_coloraxes(showscale=False)
        fig.update_traces(marker_showscale=False)
        fig.add_trace(colorbar_trace)
        fig['layout']['showlegend'] = False
        fig.update_yaxes(range=[-0.25, 4.25])
        return dcc.Graph(id="graph", figure=fig)