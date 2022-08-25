import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from dash import ALL, dash_table, dcc, html, MATCH
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import dash_mantine_components as dmc
from templates import base, utils, styleutils, ImportDataFromInflux, config
from templates import callbacksrefactor as cbr
import re
import dash_daq as daq

#Loggging info
token = config.token
org = config.org
url = ImportDataFromInflux.url
bucket = "OL3S"
name = "ol3"

class Data:
    data = None
    List= ImportDataFromInflux.get_measurement_list(url,token,org,bucket)

    def Status_to_emoji(column,name=""):
        """
        Convert a column of status in emojis, name will serve later
        """
        if Data.data is not None :
            df = Data.data[column]
            emoji = df.apply(lambda x: Data.status_to_emoji(x))
        return emoji


    def get_numbers_of_issues(name = ""):
        """
        Get number of issues of each kind for pumps.
        """
        df=Data.data
        el="Equipment-Status"
        if df is not None :
            return [df[df[el]==1].count()[0],df[df[el]==2].count()[0],df[df[el]==3].count()[0],df[df[el]==4].count()[0]]

    def status(name):
        """
        Deprecated ?
        :return:
        """
        for item in SIDEBAR_CONFIG["elements"]:
            if name is item["name"]:
                channels = item["channels"]
                df = Data.FeatureStatus[channels]
                series = df.max()
                emoji = Data.status_to_emoji(series.max())
                return emoji
        return "◯"

    def channel_list(name = "",equipment=True):
        '''
        Get the list of channels from a specific pumps, or all of them
        :param equipment:
        :return:
        '''
        liste = list(Data.data.columns)
        liste.remove("Date_Time")
        liste = [x for x in liste if x.endswith("-Status")]
        L = []
        for el in liste:
            L.append(re.split(r'_|-', el)[0])
        if not equipment :
            L.remove("Equipment")
        return list(set(L))

    def parameters_channel(channel, name = ''):
        liste = list(Data.data.columns)
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
        liste=Data.channel_list()
        for el in liste :
            L=L+Data.parameters_channel(el)
        L = list(set(L))
        L.sort()
        return(L)

    def get_channels_parameters(param,name=''):
        L=list(Data.data.columns)
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

    def sidebar_init():
        SIDEBAR_CONFIG = {"elements": [], "length": 0}
        L=Data.List
        for i in range(len(L)):
            lastup, channels, dicochan, param, last_states,last_sev,last_chan=ImportDataFromInflux.get_main_stuff(url,token,org,bucket,L[i])
            SIDEBAR_CONFIG["elements"].append({'name': L[i], "id": i,
                                               "channels": channels,
                                               "last update": lastup,
                                            'last status' : last_states,
                                               'last sev' : last_sev,
                                               "last channel" : last_chan })
        SIDEBAR_CONFIG["length"] = len(L)
        return(SIDEBAR_CONFIG)



classe=Data

tabs={"overview" : "Main Overview", "last" : "History" ,"compo" : "View By Component",'compare' : "Compare Parameters",'faults' : "Faults Analysis"}
SIDEBAR_CONFIG = classe.sidebar_init()
content=utils.overview(SIDEBAR_CONFIG,name)
tab_header = utils.tabs_from_dict(tabs, name + "s", "Main Overview")

def sidebar_listgroup(input=SIDEBAR_CONFIG, active_button_id=""):
    return(utils.main_sidebar_listgroup(input,active_button_id,name + "s",runs=True))

def sidebar_content(input=SIDEBAR_CONFIG,active_button_id=""):
    outputdata = sidebar_listgroup(input, active_button_id)
    card = utils.sidebar_card_layout(name, outputdata, "Filter " + name.capitalize()+ "s")
    return card

def build_overview_table(name=''):
    time="Time"
    if name is not None:
        df = classe.data[[x + "-Status" for x in classe.channel_list()]+[time]]
        liste = df.columns.values.tolist()
        liste = df.columns.values.tolist()
        liste.remove(time)
        liste.remove("Equipment")
        liste.sort()
        liste.insert(0, "Equipment")
        liste.insert(0, time)
        df = df[liste]
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

def build_monitor_table(name='',channel=None,isparam=False,param = None,issues=[1,2,3,4]):
    time = "Time"
    dico={0 :"◯", 1: "🟢" ,2: "🟡",3 :"🟠", 4 : "🔴"}
    issues=[dico[x] for x in issues]
    if isparam :
        if param == 'Overview' :
            df = classe.data[[channel +'_' + x + "-Status" for x in classe.parameters_channel(channel)]+[time] + [channel + '-Status']]
            liste = df.columns.values.tolist()
            liste.remove(time)
            for col in liste:
                df = df.assign(**{col: classe.Status_to_emoji(col)})
                df = df.rename(columns={col: col[:len(col) - 7]})
                col = col[:len(col) - 7]
            liste = df.columns.values.tolist()
            liste.remove(time)
            liste.sort()
            liste.insert(0, time)
            df = df[liste]
            df = df[df[channel].isin(issues)]
            if len(df[time]) == 0:
                texte = html.Div('None of the issues selected has  been recently detected on ' + channel + ".")
            else:
                L = []
                liste=list(df.columns)
                liste.remove(channel)
                for a in liste:
                    if set(['🔴','🟠',"🟡"]) & set(df[a].values) :
                        L.append(a[(len(channel) + 1):len(a)])
                if len(L)==0 :
                    texte= html.Div('None of the issues selected has  been recently detected on ' + channel + ".")
                else :
                    U=[]
                    for el in L :
                        U+=utils.get_faults('_' + el).split(', ')
                    U=list(set(U))
                    texte = html.Div([html.Div(" Recent issues on " + channel + " were due to parameter" + (len(L)>1)*'s' + " " + ', '.join(L) + "."),
                                      html.Div("Possibles faults : " + ', '.join(U) + '.')])
            df.columns=[utils.renaming(channel,col) for col in df.columns]
        else :
            df = classe.data[[channel + '-Status'] + [channel + '_' + param + "-Status"] + [time]]
            liste = df.columns.values.tolist()
            liste.remove(time)
            for col in liste:
                df = df.assign(**{col: classe.Status_to_emoji(col)})
                df = df.rename(columns={col: col[:len(col) - 7]})
                col = col[:len(col) - 7]
            liste = df.columns.values.tolist()
            liste.remove(time)
            liste.sort()
            liste.insert(0, time)
            df = df[liste]
            df = df[df[channel + '_' + param].isin(issues)]
            if len(df[time]) == 0 :
                texte = html.Div('None of the issues selected has been recently detected on ' + channel + '_' + param + ".")
            else:
                L = []
                liste = list(df.columns)
                liste.remove(channel)
                for a in liste:
                    if set(['🔴','🟠',"🟡"]) & set(df[a].values) :
                    #if '🔴' in df[a].values or '🟠' in df[a].values or "🟡" in df[a].values:
                        L.append(a[(len(channel) + 1):len(a)])
                if len(L) == 0:
                    texte = html.Div('None of the issues selected has  been recently detected on ' + channel + '_' + param + ".")
                else:
                    texte = html.Div([html.Div(" Recent issues detected on " +  channel + '_' + param + "."),
                                      html.Div("Possibles faults : " + utils.get_faults('_' + param) + '.')])
            df.rename(columns={channel + '_' + param : param}, inplace=True)
    else :

        df = classe.data[[x + "-Status" for x in classe.channel_list()]+[time]]
        liste = df.columns.values.tolist()
        liste.remove(time)
        for col in liste:
            df=df.assign(**{col:classe.Status_to_emoji(col)})
            df = df.rename(columns={col: col[:len(col) - 7]})
            col = col[:len(col) - 7]
        liste = df.columns.values.tolist()
        liste.remove(time)
        liste.remove("Equipment")
        liste.sort()
        liste.insert(0, "Equipment")
        liste.insert(0, time)
        df = df[liste]
        df=df[df[channel].isin(issues)]
        if len(df[time]) == 0 :
            texte = html.Div('None of the issues selected has been recently detected on ' + channel + ".")
        else :
            L = []
            for a in list(df.columns):
                if set(['🔴','🟠',"🟡"]) & set(df[a].values) :
                    L.append(a)
            if "Equipment" in L :
                L.remove("Equipment")
            texte=html.Div(" Recent issues were due to parameters " + ', '.join(L) + "." )
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
                                page_size=5,)
    table = html.Div([data, html.Div(id='datatable-interactivity-container')])
    header = styleutils.head_of_overview('pumps')
    loading = dcc.Loading(id='loading', children=[table], type="circle")
    return dbc.Col([texte,loading])

vardict = {"sidebar_content" : sidebar_content, "SIDEBAR_CONFIG" : SIDEBAR_CONFIG, "tab_header" : tab_header}


def callback(app, name, var):
    @app.callback(*cbr.filter(name), prevent_initial_call=True)
    def filter_func(n_clicks, vbut_nclicks, value):
        return utils.filter_func(n_clicks, vbut_nclicks, value, var, name)

    @app.callback(Output(name + "-hole", "children"), Input({'type': "" + name + '-button', 'index': ALL}, 'id'),
                  State({'type': "" + name + '-button', 'index': ALL}, 'active'))
    def database(button_id, active):
        if type(button_id) is dash._utils.AttributeDict or list:
            if True in active:
                button_id = button_id[active.index(True)]["index"]
            else:
                raise PreventUpdate
        element = utils.get_elements_from_id(button_id, name, var["SIDEBAR_CONFIG"])
        if element is None:
            raise PreventUpdate
        else:
            data, _, _ = ImportDataFromInflux.query_bucket_measurement(bucket, element["name"], from_date=None,
                                                                       to_date=None)
            data = data.reset_index()
            data["Time"] = data["Date_Time"]
            data["Date_Time"] = data["index"]
            data.drop("index", inplace=True, axis=1)
            classe.data = data
            return (dmc.Notification(
                id="my-notification",
                title="Database",
                message=["Data fully charged !"],
                loading=False,
                color="green",
                action="show",
                autoClose=True,
                disallowClose=False,
            ))

    @app.callback(*cbr.rendercontent(name), prevent_initial_call=True)
    def render_content(f, tab, z, button_id, active):
        centered = {"textAlign": "center", "verticalAlign": "middle"}
        if type(button_id) is dash._utils.AttributeDict or list:
            if True in active:
                button_id = button_id[active.index(True)]["index"]
            else:
                return html.Div("No " + name + " selected")
        element = utils.get_elements_from_id(button_id, name, var["SIDEBAR_CONFIG"])
        if element is None:
            return (utils.overview(var["SIDEBAR_CONFIG"]))
        if classe.data is None:
            raise PreventUpdate
        tab = tab[(len(name) + 2):len(tab)]
        if tab == "overview":
            checklist0 = html.Div([html.Div('Show channels with status :'),
                                   dbc.Checklist(
                                       options=[
                                           # {"label": "◯", "value": 0, 'disabled': True},
                                           {"label": "🟢", "value": 1},
                                           {"label": "🟡", "value": 2},
                                           {"label": "🟠", "value": 3},
                                           {"label": "🔴", "value": 4},
                                       ],
                                       value=[1, 2, 3, 4],
                                       id=name + "-state-overview-checklist", inline=True)])
            return html.Div(dbc.Row([
                dbc.Col([dbc.Row([dbc.Col(html.Div(
                    [checklist0, dcc.Store(name + '-element', data=element), html.Div(id=name + "-channel-overview")])),
                                  dbc.Col(html.Div(id=name + "-param-overview")),
                                  ], style={"width": "fit-content"})]),
                dbc.Col(html.Div(id=name + "-quick-graph"))]))

        if tab == "compo":
            thing = []
            for channel in classe.channel_list(equipment=False):
                thing.append({"label": channel, "value": channel})

            channel_choice = dcc.Dropdown(options=thing, placeholder="Select a channel", id=name + "s-ad-value-list")
            chan_info = html.Div(id=name + "main_info")
            feature_choice = dcc.Dropdown([], placeholder="Select a parameter", id=name + '-channel-features-dropdown')
            feature_info = html.Div(id=name + "main_info_param")
            table_header = [
                html.Thead(html.Tr([html.Th(channel_choice, style=centered), html.Th(feature_choice, style=centered)]))]
            content = html.Tbody([html.Tr([html.Td(chan_info, style=centered), html.Td(feature_info)])])
            table = dbc.Table(table_header + [content], bordered=True, style={"table-layout": "fixed"})
            final = dbc.Col([table, dcc.Dropdown(id=name + "-graph-style"), html.Div(id=name + "-radial-output")])
            return (final)
        if tab == "compare":
            thing = []
            for param in classe.get_parameters():
                thing.append({"label": param, "value": param})
            param_choice = dcc.Dropdown(options=thing, id=name + "s-param-compare-list")
            channels_choice = dcc.Dropdown(options=[], id=name + '-param-compare-dropdown', multi=True)
            graph_choice = dcc.Dropdown(id=name + "-compare-graph-style")
            multiple_graph = html.Div(
                [
                    dbc.RadioItems(
                        id=name + "-compare-radios",
                        className="btn-group",
                        inputClassName="btn-check",
                        labelClassName="btn btn-outline-primary",
                        labelCheckedClassName="active",
                        options=[
                            {"label": "Same graph", "value": False},
                            {"label": "Multiple graphs", "value": True},
                        ],
                        value=False,
                    ),
                    html.Div(id="output"),
                ],
                className="radio-group",
            )
            table_header = [html.Thead(html.Tr(
                [html.Th(param_choice, style=centered), html.Th(channels_choice, style=centered),
                 html.Th(graph_choice, style=centered), html.Th(multiple_graph, style=centered)]))]
            table = dbc.Table(table_header, bordered=True, style={"table-layout": "fixed"})
            final = dbc.Col([table, html.Div(id=name + "-compare-radial-output")])
            return final
        if tab == 'last':
            thing = []
            for channel in classe.channel_list(equipment=False):
                thing.append({"label": channel, "value": channel})
            thing.append({"label": "Global Overview", "value": "Equipment"})
            checklist0 = html.Div([html.Div('Issues displayed :'),
                                   dbc.Checklist(
                                       options=[
                                           # {"label": "◯", "value": 0, 'disabled': True},
                                           {"label": "🟢", "value": 1},
                                           {"label": "🟡", "value": 2},
                                           {"label": "🟠", "value": 3},
                                           {"label": "🔴", "value": 4},
                                       ],
                                       value=[1, 2, 3, 4],
                                       id=name + "-state-checklist", inline=True)])

            checklist1 = dcc.Dropdown(options=thing, value="Equipment", id=name + "last-channel")
            checklist2 = dcc.Dropdown(options=[], id=name + "last-channel-param", style={'display': 'none'})
            checklist = dbc.Col([checklist0, checklist1, checklist2])
            button_group = html.Div([checklist], className="radio-group")
            final = dbc.Col([dbc.CardHeader(button_group),
                             html.Div([], style={'display': 'none'}, id=name + "-last-table")])
            return (final)
        if tab == "faults":
            thing = []
            for channel in classe.channel_list(equipment=False):
                thing.append({"label": channel, "value": channel})
            thing.append({"label": "Global Overview", "value": "Equipment"})
            checklist0 = html.Div([html.Div('Issues displayed :'),
                                   dbc.Checklist(
                                       options=[
                                           {"label": "🟡", "value": 2},
                                           {"label": "🟠", "value": 3},
                                           {"label": "🔴", "value": 4},
                                       ],
                                       value=[2, 3, 4],
                                       id=name + "faults-state-checklist", inline=True)])
            checklist1 = dcc.Dropdown(options=thing, value="Equipment", id=name + "faults-channel")
            checklist2 = dcc.Dropdown(options=[], id=name + "faults-channel-param", style={'display': 'none'})
            checklist = dbc.Col([checklist1, checklist2])
            button_group = html.Div([checklist], className="radio-group")
            final = dbc.Col([dbc.CardHeader(button_group),
                             html.Div([], style={'display': 'none'}, id=name + "-faults-table")])
            return (final)
        return html.P('Wait for it')

    @app.callback(Output(name + "-channel-overview", 'children'), Input(name + "-state-overview-checklist", "value"),
                  Input(name + "-element", 'data'))
    def channel_status(val, element):
        liste = element["channels"]
        liste.remove("Equipment")
        liste.sort()
        liste.insert(0, 'Equipment')
        return utils.monittable(element["name"], liste, classe.data, name, typ='chan', value=val)

    @app.callback(Output(name + "-param-overview", "children"),
                  Input({'type': name + '-chan-ov-button', 'index': ALL}, 'n_clicks'))
    def param_status(nclick):
        """
        Define the parameters status overview.
        """
        if len(list(dash.callback_context.triggered_prop_ids.values())) > 0:
            a = False
            for i in dash.callback_context.args_grouping:
                if i["value"] is not None:
                    a = True
            if a:
                channel = list(dash.callback_context.triggered_prop_ids.values())[0]['index']
                if channel == "Equipment":
                    return []
                liste = classe.parameters_channel(channel)
                liste = [channel + '_' + x for x in liste]
                liste.sort()
                checklist1 = html.Div([html.Div('Show parameters with status :'),
                                       dbc.Checklist(
                                           options=[
                                               # {"label": "◯", "value": 0, 'disabled': True},
                                               {"label": "🟢", "value": 1},
                                               {"label": "🟡", "value": 2},
                                               {"label": "🟠", "value": 3},
                                               {"label": "🔴", "value": 4},
                                           ],
                                           value=[1, 2, 3, 4],
                                           id=name + "-state-overview-checklist-param", inline=True)])
                return [checklist1,
                        html.Div(utils.monittable("", liste, classe.data, name, typ="param"), id=name + 'param-list'),
                        dcc.Store(id=name + '-channel', data=channel)]
            else:
                return []

    @app.callback(Output(name + 'param-list', 'children'), Input(name + "-state-overview-checklist-param", 'value'),
                  Input(name + '-channel', 'data'))
    def update_param_list(val, channel):
        liste = classe.parameters_channel(channel)
        liste = [channel + '_' + x for x in liste]
        liste.sort()
        return utils.monittable("", liste, classe.data, name, typ="param", value=val)

    @app.callback(Output(name + "-quick-graph", 'children'),
                  Input({'type': name + '-param-ov-button', 'index': ALL}, 'n_clicks'))
    def display_quick_graph(nclick):
        """
        Create div for graph and graph choice
        """
        if len(list(dash.callback_context.triggered_prop_ids.values())) > 0:
            a = False
            for i in dash.callback_context.args_grouping:
                if i["value"] is not None:
                    a = True
            if a:
                val = list(dash.callback_context.triggered_prop_ids.values())[0]['index']
                graph = "Evolution"
                return html.Div([dcc.Dropdown(options=["Evolution", "Evolution with status", "Density"],
                                              value="Evolution", id=name + "-quick-graph-choice"),
                                 html.Div(id=name + '-real-quick-graph'),
                                 dcc.Store(id=name + '-chan-parameter', data=val)])

    @app.callback(Output(name + '-real-quick-graph', 'children'), Input(name + "-quick-graph-choice", 'value'),
                  Input(name + '-chan-parameter', "data"))
    def display_graph(graph, val):
        return styleutils.graph(True, 'Date_Time', val, classe.data, style=graph, title=graph + " of " + val)

    @app.callback(Output(name + "faults-channel-param", 'options'), Output(name + "faults-channel-param", 'value'),
                  Output(name + "faults-channel-param", 'style'), Input(name + "faults-channel", "value"))
    def get_param0(va):
        if va is None or va == "Equipment":
            return [" "], " ", {'display': 'none'}
        else:
            return classe.parameters_channel(va) + ["Overview"], "Overview", {}

    @app.callback(Output(name + "last-channel-param", 'options'), Output(name + "last-channel-param", 'value'),
                  Output(name + "last-channel-param", 'style'), Input(name + "last-channel", "value"))
    def get_param(va):
        if va is None or va == "Equipment":
            return [" "], " ", {'display': 'none'}
        else:
            return classe.parameters_channel(va) + ["Overview"], "Overview", {}

    @app.callback(Output(name + "-last-table", 'children'), Output(name + "-last-table", 'style'),
                  Input(name + "last-channel-param", "value"), Input(name + "last-channel", "value"),
                  Input(name + "-state-checklist", "value"))
    def table_issues(param, channel, issues):
        if channel is None:
            return [], {'display': 'none'}
        if param is None or param == " ":
            return build_monitor_table(channel=channel, isparam=False, issues=issues), {}
        elif param == "Overview":
            return build_monitor_table(channel=channel, isparam=True, param=param, issues=issues), {}
        else:
            return dbc.Row([dbc.Col(build_monitor_table(channel=channel, isparam=True, param=param, issues=issues)),
                            dbc.Col([dcc.Dropdown(options=["Evolution", "Evolution with status", "Density"],
                                                  value="Evolution with status",
                                                  id=name + "-last-graph-choice"),
                                     html.Div([], id=name + "-last-graph")])]), {}

    @app.callback(Output(name + "-last-graph", 'children'), Input(name + "last-channel-param", "value"),
                  Input(name + "last-channel", "value"), Input(name + "-last-graph-choice", "value"))
    def display(param, chan, graph):
        if chan is None or graph is None:
            raise PreventUpdate
        elif param != "Overview" and chan != "Equipment":
            val = chan + '_' + param
            return styleutils.graph(True, 'Date_Time', val, classe.data, style=graph, title=graph + " of " + val)
        else:
            raise PreventUpdate

    @app.callback(*cbr.param_from_channel(name))
    def get_parameters(va):
        if va is None:
            raise PreventUpdate
        else:
            return classe.parameters_channel(va)

    @app.callback(*cbr.info_for_channel(name))
    def get_stuff(va):
        if va is None:
            raise PreventUpdate
        else:
            return styleutils.status_sev(classe.data, va)

    @app.callback(*cbr.inf_for_param(name))
    def get_stuff(param, va):
        if va is None:
            return html.Div()
        elif param + '_' + va not in list(classe.data.columns):
            return html.Div()
        else:
            return styleutils.status_sev(classe.data, va, sensor=param)

    @app.callback(*cbr.graph_options(name))
    def get_choice(val, val2):
        if val is None:
            raise PreventUpdate
        else:
            if val2 is None:
                return (["Evolution", "Evolution with status", "Density"], "Evolution")
            else:
                return (["Evolution", "Evolution with status", "Density"], val2)

    @app.callback(*cbr.graph(name))
    def display_value(value, graph, button_id, active, channel):
        if type(button_id) is dash._utils.AttributeDict or list:
            button_id = button_id[active.index(True)]["index"]
        element = utils.get_elements_from_id(button_id, name, var["SIDEBAR_CONFIG"])
        if channel is not None and value is not None:
            return html.Div([
                styleutils.graph(element, 'Date_Time', channel + '_' + value, classe.data, style=graph,
                                 title=graph + " of " + channel + '_' + value)])
        else:
            return html.Div("Select a channel and/or a feature")

    @app.callback(*cbr.channel_from_param(name))
    def get_channels(param):
        if param is None:
            raise PreventUpdate
        else:
            return classe.get_channels_parameters(param)

    @app.callback(*cbr.graph_options(name, compare=True))
    def get_choices(val):
        if val is None:
            raise PreventUpdate
        else:
            return (["Evolution", "Density"], "Evolution")

    @app.callback(*cbr.graph(name, compare=True))
    def display_value(channel, graph, multi, button_id, active, value):
        if type(button_id) is dash._utils.AttributeDict or list:
            button_id = button_id[active.index(True)]["index"]
        element = utils.get_elements_from_id(button_id, name, var["SIDEBAR_CONFIG"])
        if channel is not None and value is not None:
            return html.Div([
                styleutils.graph(element, 'Date_Time', [c + '_' + value for c in channel], classe.data, style=graph,
                                 title=graph + " of " + value, multiple=multi)])
        else:
            return html.Div("Select a channel and/or a feature")