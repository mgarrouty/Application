from dash import html
import dash_bootstrap_components as dbc
from dash import dcc
from templates import pumps, utils, config, sues,ol3s, rcps
import pandas as pd
warning_badge_style = alert_badge_style = {"marginLeft": 10}
import plotly.express as px
centered = {"textAlign": "center", "verticalAlign": "middle"}

def span(liste):
    """
    From the list of status, returns the list of badges for displaying.
    :param list:
    :return:
    """
    U = []
    if liste[3] != 0 :
        U.append(dbc.Badge(liste[3], color="danger"))
    if liste[2] != 0:
        U.append(dbc.Badge(liste[2], color="warning"))
    if liste[1] != 0:
        U.append(dbc.Badge(liste[1], color="yellow"))
    if liste[0] != 0:
        U.append(dbc.Badge(liste[0], color="success"))
    return (U)

def miniature(name) :
    if name == "pump" :
        sidebar=pumps.SIDEBAR_CONFIG
    elif name == 'sue' :
        sidebar=sues.SIDEBAR_CONFIG
    elif name == "ol3" :
        sidebar=ol3s.SIDEBAR_CONFIG
    elif name == "rcp" :
        sidebar=rcps.SIDEBAR_CONFIG
    else :
        return html.Div()
    lastup = 0
    a = 0
    L = [0, 0, 0, 0]
    V = [0, 0, 0, 0]
    df = pd.DataFrame(columns=["Count", "Status", "Severity"])
    for elem in sidebar['elements'] :
        df.loc[len(df)] = [elem["name"], utils.emoji_to_status(elem["last status"][0]), int(elem['last sev'])]
        """
        if a == 0 :
            lastup=elem["last update"]
            a=1
        else :
            #lastup=min(lastup,elem["last update"])
            """
        if elem["last sev"] < 100 :
            V[0]+=1
        elif elem["last sev"] < 200 :
            V[1] += 1
        elif elem["last sev"] < 300 :
            V[2] += 1
        elif elem["last sev"] <= 400 :
            V[3] += 1
        L[utils.emoji_to_status(elem['last status'][0]) - 1] += 1
    colordic = {1: "green", 2: 'yellow', 3: 'orange', 4: 'red'}
    colorstat = {1: "Ok", 2: 'Potential Warning', 3: 'Warning', 4: 'Alert'}
    df2 = df.groupby(["Status"]).count()
    df2 = df2.reset_index()
    df2['State'] = df2.apply(lambda row: colorstat[int(row["Status"])], axis=1)
    table_header = [
        html.Thead(html.Tr([html.Th("Severity", style=centered), html.Th("Count", style=centered)]))]
    content = html.Tbody([
        html.Tr([html.Td("0 to 100", style=centered), html.Td(V[0], style=centered)]),
        html.Tr([html.Td("100 to 200", style=centered), html.Td(V[1], style=centered)]),
    html.Tr([html.Td("200 to 300", style=centered), html.Td(V[2],style=centered)]),
    html.Tr([html.Td("300 to 400", style=centered), html.Td(V[3], style=centered)])]
    )
    table = dbc.Table(table_header + [content], bordered=True, style={"width": "fit-content"})
    fig=px.pie(df2, values="Count", names="State", color="Status", color_discrete_map=colordic)
    fig.update_layout(title=name.capitalize() + 's' + ' status',title_x=0.5)
    bigtable_header=html.Thead(html.Tr([html.Th([html.Div(name.capitalize() + 's'), html.P(span(L)) ])]))
    bigtable=dbc.Table(bigtable_header)
    return html.Div([
                html.H5(name.capitalize() + 's', className="card-title"),

                html.P(
                    span(L),
                    className="card-text"),
                html.Div(table, className='text-center'),
             dcc.Graph(figure=fig,style={'width': '30vh', 'height': '30vh'},className='text-center'),
                ], className="card align-items-center", style= {"width" : 'fit-content '})

#Creating the content for the homepage
def content():
    text = html.P("This is the content of Home page Yay!")
#Connection issues (has to be linked to a real issue)
    alert = dbc.Alert(
        "Database connection has been successful.",
        color="green",
        dismissable=True,
        fade=True,
        is_open=True,
    )

    L=[miniature(name) for name in config.dicobucket.values()]
    cards = dbc.CardGroup(L)


#Creating the final page with all smaller divs
    body = html.Div([alert, cards], id="Home-Body-Content")
    return body

#Possibilities of other features

"""
def sidebar():
    return html.P("This is sidebar of Home page")


def addbar():
    return

"""
def HomeCallbacks(app):
   pass
