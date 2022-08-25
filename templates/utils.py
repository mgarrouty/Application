import dash_bootstrap_components as dbc
from dash import html,dcc
import dash
from dash.exceptions import PreventUpdate
from templates import base, ImportDataFromInflux,styleutils
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from statsmodels.tsa.stattools import acf, pacf, adfuller, kpss
from statsmodels.tsa.arima.model import ARIMA

try :
    faults = pd.read_excel("./data/FaultMatrix.xlsx", sheet_name="Parameter_Fault_List")
except ValueError :
    'pas grave'
centered = {"textAlign": "center", "verticalAlign": "middle"}


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

def emoji_to_status(thing):
    if thing =="◯":
        return 0
        # return "🔵"
    if thing == "🟢":
        return 1
    if thing == "🟡":
        return 2
    if thing == "🟠":
        return 3
    if thing == "🔴":
        return 4
    return 0

def get_faults(param,df=faults) :
    return(list((df.loc[df['ParameterName']==param]["Fault"]))[0])

def content(name) :
    return html.P("No " + name + " selected.", id="" + name + "-content")

def sidebar_list_group_item(type, id, active_button_id, name, runs = [],isrun=True):
    button_id = ''+type+"-button-"+str(id)
    status = (button_id == active_button_id)
    buttons = [dbc.Button(runs, outline=True, disabled=True, size="sm"), dbc.Button(
            name, outline=True, id={'type': ''+type+'-button', 'index': button_id}, active=status)]
    button_group = dbc.ButtonGroup(buttons, size="sm")
    div = html.Div(button_group, style={
                   'margin': 'auto', 'textAlign': 'center'})
    list_groupitem = dbc.ListGroupItem(div, active=status)
    return list_groupitem

def sidebar_card_layout(type, outputdata, text=""):
    """
    Create the html div for the global sidebar.
    """
    input = dbc.Input(id=''+type+'-filter', placeholder=text, type="text")
    button = dbc.Button("Filter", id=''+type+"-filter-button", n_clicks=0)
    input_group = dbc.InputGroup([input, button])
    card_elements = [dbc.CardHeader(input_group), dbc.CardBody(
        outputdata), dbc.CardFooter()]
    card = dbc.Card(card_elements, style=base.SIDEBAR_STYLE,
                    id=''+type+"-sidebar-content")
    return card

def tabs_from_dict(dictabs,type,active_tab,disabled=[]) :
    """
    Create the Tabs options div for a component. The dict must be on format  {label : code}.
    """
    tabsbuttons=[]
    active_tab_id = None
    for key,value in dictabs.items() :
        lab = value
        tab_id= '' + type + '-' + key
        if key in disabled :
            tabsbuttons.append(dbc.Tab(label=lab, tab_id=tab_id,disabled=True))
        else :
            tabsbuttons.append(dbc.Tab(label=lab, tab_id=tab_id))
        if active_tab == lab :
            active_tab_id=tab_id
    id='' + type + '-card-tabs'
    return dbc.Tabs(tabsbuttons, id=id, active_tab=active_tab_id)

def main_sidebar_listgroup(input, active_button_id,name,runs=False):
    """
        Create the html div for the elements appearing in sidebar. Without filter, it takes all the data (all possibles elements).
        Active button display the selected element in dark mode.
        Listgroup item generates html div for each buttons.
        """
    thing = []
    if int(input["length"]) > 0:
        for item in input["elements"]:
            if runs :
                list_groupitem = sidebar_list_group_item(
                    name.rstrip(name[-1]), item["id"], active_button_id, item["name"], runs=item["last status"])
            else :
                list_groupitem = sidebar_list_group_item(
                    name.rstrip(name[-1]), item["id"], active_button_id, item["name"], runs=item["last status"])
            thing.append(list_groupitem)
    else:
        thing.append(dbc.ListGroupItem(html.P("No Data after Filter.")))
    return dbc.ListGroup(thing, id=""+ name + "_selection")

def filter_sidebar(value, active_button_id,sidebar_content,SIDEBAR_CONFIG):
    """
    Allow to filter the values in the sidebar with text search.
    """
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

def get_elements_from_id(id,name,SIDEBAR_CONFIG):
    """
    Get the element from his item. Ex : for the selected valve in the sidebar, element['name'] give access to the runs of this valve.
    """
    element = None
    for item in SIDEBAR_CONFIG["elements"]:
        button_id = "" + name + "-button-"+str(item["id"])
        if button_id == id:
            element = item
    return element

def create_content(button_id,name,SIDEBAR_CONFIG ,tab_header):
    """
    When an element is selected, return the html div of his overview (Global description, and options menu)
    """
    element = get_elements_from_id(button_id,name,SIDEBAR_CONFIG)
    if element is None:
        return  overview(SIDEBAR_CONFIG,name)
    if type(element["last update"]) != str :
        element["last update"]=element["last update"].strftime('%Y-%m-%d %X')
    header =html.Div([html.H3(element["name"],style={"font-weight": "bold"}),html.Div("Last update : " + str(element["last update"]))])
    tab_content = html.Div([], id="" + name + "-tab-content")
    header = dbc.CardHeader(header)
    body = dbc.CardBody([tab_header, tab_content])
    card = dbc.Card([header, body])
    return card


def filter_func(n_clicks, vbut_nclicks, value,vardict,name):
    """
        The function for filtering in the sidebar, common to every components. Value is the string in the search bar, nclicks the Filter button.
        """
    sidebar_content=vardict["sidebar_content"]
    SIDEBAR_CONFIG=vardict["SIDEBAR_CONFIG"]
    tab_header=vardict["tab_header"]
    ctx = dash.callback_context
    button_id = ctx.triggered_id
    if button_id is None:
        raise PreventUpdate
    if type(button_id) is dash._utils.AttributeDict:
        button_id = button_id["index"]
    sidebar = filter_sidebar(value, button_id, sidebar_content, SIDEBAR_CONFIG)
    content = create_content(button_id, name, SIDEBAR_CONFIG, tab_header)
    return sidebar, value, content

def initiate_config(url,token,org,bucket) :
    SIDEBAR_CONFIG = {"elements": [], "length": 0}
    L=ImportDataFromInflux.get_measurement_list(url,token,org,bucket)
    for i in range(len(L)) :
        SIDEBAR_CONFIG["elements"].append({'name' : L[i], "id" : i, "channels" : ImportDataFromInflux.get_channel_list(url,token,org,bucket,L[i]), "last update" : ImportDataFromInflux.get_last_update(url,token,org,bucket,L[i])})
    SIDEBAR_CONFIG["length"]=len(L)
    return(SIDEBAR_CONFIG)


def monittable(equipement,liste,data,name,typ,clickable=True,value=[1,2,3,4]) :
    thing = []
    last_row = data[data["Time"] ==data["Time"].max()].copy()
    table_header = [
        html.Thead(html.Tr([html.Th("Component", style=centered), html.Th("Status", style=centered),
                            html.Th("Severity", style=centered),html.Th("", style=centered)]))
    ]
    for i in range(len(liste)):
        channel = liste[i]
        if int(last_row[channel + "-Status"]) in value :
            stat = styleutils.dicostatus[int(last_row[channel + "-Status"])]
            status = html.Div(stat[0], style={'color': stat[1], "font-size": "16px", "textAlign": "center",
                                              "verticalAlign": "middle", "max-width" : "70px","font-weight": "bold"})
            sev = html.Div(html.Div(styleutils.severity(last_row[channel + '-Sev']), style={'display': 'inline-block',"verticalAlign": "middle","max-height" : "10px !important"}))
            sevalue=html.Div(str(int(last_row[channel + '-Sev'])),style={"font-size": "20px", "textAlign": "center", "verticalAlign": "middle"})
            if clickable :
                if typ=="param" :
                    comp_name = dbc.Button(channel.split('_')[1], id={"type": name + '-' + typ + '-ov-button', 'index': channel},
                                          size="sm",outline=True)
                elif typ=="chan" :
                    comp_name = dbc.Button(channel,
                                           id={"type": name + '-' + typ + '-ov-button', 'index': channel},
                                           size="sm",outline=True)
            else :
                comp_name = html.Div(channel)
            if channel == "Equipment":
                comp_name=dbc.Button(equipement, id={"type": name + '-' + typ + '-ov-button', 'index': channel},size="sm",outline=True)
            thing.append(html.Tr([html.Td(
            html.Div(comp_name, style=centered)),
                              html.Td(html.Div(status, style=centered)), html.Td(sev),html.Td(sevalue)]))
    return html.Div(dbc.Row([dbc.Table(table_header + [html.Tbody(thing)], bordered=True, style={"width": "fit-content"},size="sm")]))

def overview(SIDEBAR_CONFIG,name) :
    thing = []
    table_header = [
        html.Thead(html.Tr([html.Th("Component", style=centered), html.Th("Status", style=centered),
                            html.Th("Severity", style=centered),html.Th("", style=centered)]))
    ]
    df=pd.DataFrame(columns = ["Count","Status","Severity"])
    for item in SIDEBAR_CONFIG["elements"] :
        df.loc[len(df)] = [item["name"],emoji_to_status(item["last status"][0]),int(item['last sev'])]
        channel = item["name"]
        stat = styleutils.dicostatus[emoji_to_status(item["last status"][0])]
        status = html.Div(stat[0], style={'color': stat[1], "font-size": "20px", "textAlign": "center",
                                          "verticalAlign": "middle","font-weight": "bold"})
        sev =html.Div(styleutils.severity(item['last sev']), style={'display': 'inline-block',"max-height" : "10px !important"})
        sevalue=html.Div(str(int(item['last sev'])),style={"font-size": "20px", "textAlign": "center", "verticalAlign": "middle"})
        comp_name = html.Div(channel)
        thing.append(html.Tr([html.Td(
        html.Div(comp_name, style=centered)),
                          html.Td(html.Div(status, style=centered)), html.Td(sev),html.Td(sevalue)]))
    colordic = {1: "green", 2: 'Yellow', 3: 'Orange', 4: 'Red',0 : 'grey'}
    colorstat = {1: "Ok", 2: 'Potential Warning', 3: 'Warning', 4: 'Alert', 0 : 'No Data'}
    df2 = df.groupby(["Status"]).count()
    df2 = df2.reset_index()
    df2['State']=df2.apply(lambda row : colorstat[int(row["Status"])], axis = 1)
    fig1 = px.pie(df2, values="Count", names="State", color="Status", color_discrete_map=colordic)
    fig1.update_traces(textposition='inside', textinfo='percent+label')
    fig1.update_layout(title_text="Status of " + name + 's', title_x=0.5)
    l=SIDEBAR_CONFIG["length"]

    i=0
    fig = go.Figure()
    specs = [[{'type': 'domain'} for i in range(int(l / 3 + 1 * (l / 3 != int(l / 3))) * 3)]]
    fig = make_subplots(rows=int(l / 3 + 1 * (l / 3 != int(l / 3))), cols=3, specs=specs)
    for item in SIDEBAR_CONFIG["elements"] :
        df = pd.DataFrame(columns=["Count", "Status"])
        for param in item["last channel"] :
            df.loc[len(df)]=["banane",item["last channel"][param][0]]
        df2 = df.groupby(["Status"]).count()
        df = df2.reset_index()
        df = df.reset_index()
        df = df.sort_values("Status")
        df["colors"] = df.apply(lambda row: colordic[int(row["Status"])], axis=1)
        df["label"] = df.apply(lambda row: colorstat[int(row["Status"])], axis=1)
        fig.add_trace(go.Pie(labels=df["label"], values=df["Count"], title=item["name"]), row = 1+ i//3, col = 1 + i%3
                             )
        fig.update_traces(hoverinfo='label+percent',
                          textfont_size=20,
                          marker=dict(colors=df["colors"], line=dict(color='#000000')),row = 1+ i//3, col = 1 + i%3)
        i=i+1
    fig.update_layout(
        title_text="Channel status for each " + name, title_x=0.5 )
    """

    fig = px.pie(df2, values=value+ "-Status",names="name", color=value+ "-Status", color_discrete_map=colordic)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(title_text=value + ": Percentage of time in each status", title_x=0.5)
    """
    return html.Div(dbc.CardGroup([
        dbc.Col(dbc.Card(dbc.Table(table_header + [html.Tbody(thing)], bordered=True, style={"width": "fit-content"})),width='fit-content'),
        dbc.Card(dcc.Graph(figure=fig1)),
        dbc.Card(dcc.Graph(figure=fig)),
    ]),id="" + name + "-content")



def renaming(chan,name) :
    if name.startswith(chan) :
        if name != chan :
            return name[(len(chan) + 1):len(name)]
    return(name)


def diff(serie,order=1) :
    for i in range(order) :
        serie=serie.diff()
        serie.drop(serie.index[0],inplace=True)
    return(serie)

def statio_test(data,value,maxorder=4) :
    table_header =[ html.Thead(html.Tr([html.Th("Differentation order", style=centered), html.Th("ADF P-value", style=centered),
                            html.Th("KPSS P-value", style=centered), html.Th("", style=centered)]))]
    thing= []
    for i in range(maxorder) :
        serie=diff(data[value],i)
        pvalkpss=round(kpss(serie)[1],3)
        if pvalkpss==0.01 :
            kpssdiv=html.Div("<0.01",style={'color' : 'green',"textAlign": "center", "verticalAlign": "middle"})
        elif pvalkpss==0.1 :
            kpssdiv = html.Div(">0.1", style={'color': 'red',"textAlign": "center", "verticalAlign": "middle"})
        else :
            kpssdiv= html.Div(pvalkpss,style = centered)

        if round(adfuller(serie)[1],3)<=0.01 :
            styleadf={'color' : 'green',"textAlign": "center", "verticalAlign": "middle"}
        elif round(adfuller(serie)[1],3)>=0.1 :
            styleadf={'color' : 'red',"textAlign": "center", "verticalAlign": "middle"}
        else :
            styleadf= centered
        thing.append(html.Tr([html.Td(html.Div(i,style=centered)),html.Td(html.Div(round(adfuller(serie)[1],3),style=styleadf)),
            html.Td(kpssdiv)]))
    return html.Div(dbc.Row([dbc.Table(table_header + [html.Tbody(thing)], bordered=True, style={"width": "fit-content"},size="sm")]))

def model_choice(serie,armax,mamax,criteria) :
    if criteria == 'BIC' :
        a=ARIMA(serie,order=(0,0,0)).fit().bic
    elif criteria == "AIC" :
        a=ARIMA(serie,order=(0,0,0)).fit().aic
    i,j=0,0
    for p in range(armax + 1) :
        for q in range (mamax + 1) :
            if criteria == 'BIC' :
                if ARIMA(serie,order=(p,0,q)).fit().bic < a :
                    a=ARIMA(serie,order=(p,0,q)).fit().bic
                    i,j=p,q
            if criteria == 'AIC' :
                if ARIMA(serie,order=(p,0,q)).fit().aic < a :
                    a=ARIMA(serie,order=(p,0,q)).fit().aic
                    i,j=p,q
    return(i,j,ARIMA(serie,order=(i,0,j)).fit())