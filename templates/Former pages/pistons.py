import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from dash import ALL, dash_table, dcc, html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from templates import base, utils, styleutils, ImportDataFromInflux
from templates import callbacksrefactor as cbr
import re
import dash_daq as daq

"""
How to add a new class of components:
    - Change the class name, the two call to class functions inside the class definition
    - Change name, bucket, and the name of SIDEBAR_CONFIG
    - callbacks page : add name of the page in the import, add the path link, import callbacks
    - Config page : add the name of the Component in the list
    - Sidebar : import the new page, add the path link
"""
#Logging info
token = "CMX91SGDttyhzJ9QwVU3TK55tE4TD9BidRSBJ7NG2q07Y6pHxxDm5IzHeLr81xIe5aSqfTNZfi5JXuUWk-o5Ww=="
org = "cadis_framatome"
url = ImportDataFromInflux.url

class PistonsData:
    data,_,_=ImportDataFromInflux.query_bucket_measurement('Pistons',"piston 1", from_date=None,to_date=None)
    #This part is to pretend we have continuous data
    data = data.reset_index()
    data["Date_Time"] = data["index"]
    data.drop("index", inplace=True, axis=1)
    def List():
        return ImportDataFromInflux.get_measurement_list(url,token,org,bucket)

    def Status_to_emoji(column,name=""):
        """
        Convert a column of status in emojis, name will serve later
        """
        df = PistonsData.data[column]
        emoji = df.apply(lambda x: PistonsData.status_to_emoji(x))
        return emoji

    def get_last_status(name=""):
        df=PistonsData.Status_to_emoji("Equipment-Status")
        return(df[0],df[1],df[2])

    def status(name):
        for item in SIDEBAR_CONFIG["elements"]:
            if name is item["name"]:
                channels = item["channels"]
                df = PistonsData.FeatureStatus[channels]
                series = df.max()
                emoji = PistonsData.status_to_emoji(series.max())
                return emoji
        return "◯"

    def channel_list(name = "",equipment=True):
        liste = list(PistonsData.data.columns)
        liste.remove("Date_Time")
        liste = [x for x in liste if x.endswith("-Status")]
        L = []
        for el in liste:
            L.append(re.split(r'_|-', el)[0])
        if not equipment :
            L.remove("Equipment")
        return list(set(L))

    def parameters_channel(channel, name = ''):
        liste = list(PistonsData.data.columns)
        if channel is not None:
            liste = [x for x in liste if x.startswith(channel + '_')]
            U=[]
        for el in liste:
            l = re.split(r'_|-', el)
            if len(l) == 2:
                U.append(l[1])
        U=list(set(U))
        U.sort()
        return U

    def get_parameters(name = '') :
        L=[]
        liste=PistonsData.channel_list()
        for el in liste :
            L=L+PistonsData.parameters_channel(el)
        L = list(set(L))
        L.sort()
        return(L)

    def get_channels_parameters(param,name=''):
        L=list(PistonsData.data.columns)
        U=[]
        for el in L :
            l = re.split(r'_|-', el)
            if param in l :
                U.append(l[0])
        U=list(set(U))
        U.sort()
        return U

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


bucket = "Pistons"
classe=PistonsData
name = "piston"
tabs={"overview" : "Main Overview", "compo" : "View By Component",'compare' : "Compare Parameters"}
SIDEBAR_CONFIG = utils.initiate_config(url,token,org,bucket)

tab_header = utils.tabs_from_dict(tabs, name + "s", "Main Overview")

def sidebar_listgroup(input=SIDEBAR_CONFIG, active_button_id=""):
    return(utils.main_sidebar_listgroup(input,active_button_id,name + "s",classe.status,runs=classe.get_last_status("")))

def sidebar_content(input=SIDEBAR_CONFIG,active_button_id=""):
    outputdata = sidebar_listgroup(input, active_button_id)
    card = utils.sidebar_card_layout(name, outputdata, "Filter " + name.capitalize()+ "s")
    return card

def build_overview_table(name=''):
    if name is not None:
        df = classe.data[[x + "-Status" for x in classe.channel_list()]+["Date_Time"]]
        liste = df.columns.values.tolist()
        liste.remove("Date_Time")
        for col in liste:
            df=df.assign(**{col:classe.Status_to_emoji(col)})
            df = df.rename(columns={col: col[:len(col) - 7]})
            col = col[:len(col) - 7]
        liste = df.columns.values.tolist()
        liste.remove("Date_Time")
        liste.remove("Equipment")
        liste.sort()
        liste.insert(0, "Equipment")
        liste.insert(0, "Date_Time")
        df = df[liste]
        df.columns
        data = dash_table.DataTable(id='datatable-interactivity',
                                    columns=[
                                        {"name": i, "id": i} for i in df.columns
                                    ],
                                    data=df.to_dict('records'),
                                    style_cell={"textAlign": "center"},
                                    sort_action="native",
                                    sort_mode="multi",
                                    page_action="native",
                                    page_current=0,
                                    page_size=25,)
    table = html.Div([data, html.Div(id='datatable-interactivity-container')])
    header = styleutils.head_of_overview('pumps')
    loading = dcc.Loading(id='loading', children=[table], type="circle")
    return loading

vardict = {"sidebar_content" : sidebar_content, "SIDEBAR_CONFIG" : SIDEBAR_CONFIG, "tab_header" : tab_header}
def callbacks(app,name,var):
    @app.callback(*cbr.filter(name), prevent_initial_call=True)
    def filter_func(n_clicks, vbut_nclicks, value):
        return utils.filter_func(n_clicks, vbut_nclicks, value, var,name)

    @app.callback(*cbr.rendercontent(name))
    def render_content(tab, button_id, active):
        if type(button_id) is dash._utils.AttributeDict or list:
            button_id = button_id[active.index(True)]["index"]
        element = utils.get_elements_from_id(button_id,name,var["SIDEBAR_CONFIG"])
        if element is None:
            PreventUpdate
        if tab == name + "s-overview":
            return styleutils.overview(build_overview_table(),name + "s")
        if tab == name + "s-compo":
            thing=[]
            for channel in classe.channel_list(equipment=False):
                thing.append({"label": channel, "value":   channel})
            checklist = dbc.RadioItems(options=thing, id=name + "s-ad-value-list",  inline=True)
            button_group = html.Div([checklist], className="radio-group")
            firstitem = dbc.Col([dbc.CardHeader(button_group),html.Div(id=name + "main_info")])
            seconditem=dbc.Col([dcc.Dropdown([], id=name + '-channel-features-dropdown'),html.Div(id=name +  "main_info_param")])
            header = dbc.CardHeader([button_group])
            card=dbc.CardGroup([dbc.Card(firstitem),dbc.Card(seconditem)])
            final=dbc.Col([card,dcc.Dropdown(id=name +"-graph-style"),html.Div(id=name + "-radial-output")])
            return styleutils.overview(final,name+'s')
        if tab == name + "s-compare":
            thing=[]
            for channel in classe.get_parameters():
                thing.append({"label": channel, "value":   channel})
            checklist = dcc.Dropdown(options=thing, id=name + "s-param-compare-list",  inline=True)
            button_group = html.Div([checklist], className="radio-group")
            final=dbc.Col([dbc.CardHeader(button_group),
                           dcc.Checklist(options=[],id=name +'-param-compare-dropdown',inline=True),
                           dcc.Dropdown(id=name +"-compare-graph-style"),html.Div(id=name +"-compare-radial-output")])
            return styleutils.overview(final,name +'')
        return html.P('Wait for it')


    @app.callback(*cbr.param_from_channel(name))
    def get_parameters(va):
        if va is None :
            raise PreventUpdate
        else :
            return classe.parameters_channel(va)

    @app.callback(*cbr.info_for_channel(name))
    def get_stuff(va):
        if va is None:
            raise PreventUpdate
        else:
            return styleutils.status_sev(classe.data,va)

    @app.callback(*cbr.inf_for_param(name))
    def get_stuff(param,va):
        if va is None:
            return html.Div()
        elif param + '_' + va not in list(classe.data.columns) :
            return html.Div()
        else:
            return styleutils.status_sev(classe.data, va,sensor=param)

    @app.callback(*cbr.graph_options(name))
    def get_choice(val) :
        if val is None :
            raise PreventUpdate
        else :
            return (["Evolution", "Density"],"Evolution")


    @app.callback(*cbr.graph(name))
    def display_value(value, graph,button_id, active,  channel):
        if type(button_id) is dash._utils.AttributeDict or list:
            button_id = button_id[active.index(True)]["index"]
        element = utils.get_elements_from_id(button_id, name, var["SIDEBAR_CONFIG"])
        if channel is not None and value is not None:
            return html.Div([
                styleutils.graph(element,'Date_Time',channel + '_' + value, classe.data,style = graph,title = graph + " of " + channel + '_' + value)])
        else :
            return html.Div("Select a channel and/or a feature")

    @app.callback(*cbr.channel_from_param(name))
    def get_channels(param):
        if param is None :
            raise PreventUpdate
        else :
            return classe.get_channels_parameters(param)

    @app.callback(*cbr.graph_options(name,compare=True))
    def get_choices(val):
        if val is None:
            raise PreventUpdate
        else:
            return (["Evolution", "Density"], "Evolution")

    @app.callback(*cbr.graph(name,compare=True))
    def display_value(channel, graph, button_id, active, value):
        if type(button_id) is dash._utils.AttributeDict or list:
            button_id = button_id[active.index(True)]["index"]
        element = utils.get_elements_from_id(button_id, name, var["SIDEBAR_CONFIG"])
        if channel is not None and value is not None:
            return html.Div([
                styleutils.graph(element, 'Date_Time', [c + '_' + value for c in channel], classe.data, style=graph,
                                 title=graph + " of " + value)])
        else:
            return html.Div("Select a channel and/or a feature")