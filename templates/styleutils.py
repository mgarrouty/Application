import dash_bootstrap_components as dbc
from dash import html, dcc
import dash
from dash.exceptions import PreventUpdate
from templates import base
import pandas as pd
import plotly.graph_objects as go
import dash_daq as daq
import numpy as np
import seaborn as sns
import io
import matplotlib.pyplot as plt
import base64
import matplotlib
from statsmodels.tsa.stattools import adfuller, kpss,acf,pacf
from statsmodels.graphics.tsaplots import plot_pacf, plot_acf
from statsmodels.tsa.stattools import acf, pacf
from statsmodels.tsa.arima.model import ARIMA
from tslearn.utils import to_time_series_dataset
import matplotlib.pyplot as plt
from tslearn.clustering import TimeSeriesKMeans
from sklearn.cluster import KMeans, DBSCAN, OPTICS
from sklearn.ensemble import IsolationForest
from mpl_toolkits import mplot3d
from yellowbrick.cluster import KElbowVisualizer
import sklearn
from plotly.subplots import make_subplots
from sklearn.neighbors import LocalOutlierFactor
import plotly.express as px
from colordict import *
matplotlib.use('Agg')
colors = ColorDict()

centered = {"textAlign": "center", "verticalAlign": "middle"}

def head_of_overview(name) :
    """
    A dictionnary-like function which returns the header of the overview of the element.
    """
    if name == "valves" :
        span_style = {"textDecoration": "underline", "cursor": "pointer"}
        elem1 = html.Span("🟢", id="tooltip-success", style=span_style)
        elem2 = html.Span("🔴", id="tooltip-failure", style=span_style)
        elem3 = html.Span("🟡", id="tooltip-warning", style=span_style)
        elem4 = html.Span("◯", id="tooltip-missing", style=span_style)
        legend = html.Div(
            html.P([elem1, elem2, elem3, elem4], style={'text-align': 'right'}))
        tt1 = dbc.Tooltip("Successful run.", target="tooltip-success")
        tt2 = dbc.Tooltip(
            "Run where at least one boundary was hit.", target="tooltip-failure")
        tt3 = dbc.Tooltip(
            "Partial movement. To be evaluated.", target="tooltip-warning")
        tt4 = dbc.Tooltip(
            "Boundary condition not configured.", target="tooltip-missing")
        tt = html.Div([tt1, tt2, tt3, tt4])
        col = dbc.Row(
            [dbc.Col(html.Div("Valve Runs")), dbc.Col([legend, tt])])
        return dbc.CardHeader(col)

    if name == "pumps" or name == 'pompes' or name == "sues":
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
        return dbc.CardHeader(col)

def overview(table,name) :
    """
    Return the overview of a table, and the header associated with the name (like valve).
    """
    header = head_of_overview(name)
    runs = dbc.ListGroup(table, flush=True,id="" + name + "_selection")
    body = dbc.CardBody(runs)
    internal_card = dbc.Card([header, body])
    return internal_card

#return styleutils.overview(build_runs_table(element["name"]),"pumps")





def run_graph(element,run,xaxe,value,df) :
    """
    Returns a div of a graph displaying the components of dfname which are in options, according to xaxe.
    If df is None
    If value is None or empty, ask for selection.
    If run is None, ask for run.
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
        fig.add_trace(go.Scatter(
            x=df[xaxe], y=df[selection], name=selection))
    fig.update_layout(title="Run from: " + run)
    return dcc.Graph(id="graph", figure=fig)

def graph(element,xaxe,value,df,title="",style= None,multiple=False) :
    """
    Returns a div of a graph displaying the components of dfname which are in options, according to xaxe.
    If df is None
    If value is None or empty, ask for selection.
    If run is None, ask for run.
    value[i]
    """
    if element is None:
        PreventUpdate
    if value is None:
        return html.P("No value selection")
    if len(value) == 0:
        return html.P("No value selection")
    if style == "Density" :
        if type(value) == list :
            sns.set_style('whitegrid')
            for i in range(len(value)):
                fig=sns.kdeplot(np.array(df[value[i]]))
            fig.set(title=title)
            s = io.BytesIO()
            plt.legend(labels=value)
            plt.savefig(s, format='png')
            s = base64.b64encode(s.getvalue()).decode("utf-8").replace("\n", "")
            plt.clf()
            return html.Img(id="graph", src='data:image/png;base64,{}'.format(s))
        else :
            sns.set_style('whitegrid')
            sns.kdeplot(np.array(df[value])).set(title=title)
            s = io.BytesIO()
            plt.legend(labels=[value])
            plt.savefig(s, format='png')
            s = base64.b64encode(s.getvalue()).decode("utf-8").replace("\n", "")
            plt.clf()
            return html.Img(src='data:image/png;base64,{}'.format(s))
    elif style == "Evolution" :
        if multiple :
            if type(value) == list:
                fig = make_subplots(rows=len(value), cols=1,
                                    specs=[[{"secondary_y": True}] for x in range(len(value))])
                for i in range(len(value)) :
                    fig.add_trace(
                    go.Scatter(x=df[xaxe], y=df[value[i]], name=value[i]),
                    row=i+1, col=1, secondary_y=False)
                fig.update_layout(hovermode="x unified")
                fig.update_layout(title=title)
            return dcc.Graph(figure=fig)
        else :
            fig = go.Figure()
            if type(value) == list :
                for selection in value:
                    fig.add_trace(go.Scatter(
                        x=df[xaxe], y=df[selection], name=selection))
            else :
                fig.add_trace(go.Scatter(
                    x=df[xaxe], y=df[value], name=value))
            fig.update_layout(hovermode="x unified")
            fig.update_layout(title=title)
            return dcc.Graph(figure=fig)
    elif style == "Evolution with status" :
        if type(value) == list :
            if len(value) > 1 :
                return dcc.Div("Can't display multiple status evolution.")
            else :
                value=value[0]
        fig=nice_graph(df,"Date_Time",value)
        return dcc.Graph(figure=fig)
    elif style == 'Quick Overview' :
        specs = [[{'type': 'xy'}, {'type': 'xy'}], [{'type': 'xy'}, {'type': 'xy'}]]
        colordic = {1: "green", 2: 'Yellow', 3: 'Orange', 4: 'Red', 0: 'grey'}
        colorstat = {1: "Ok", 2: 'Potential Warning', 3: 'Warning', 4: 'Alert', 0: 'No Data'}
        fig = make_subplots(rows=2, cols=2, specs=specs)
        df0 = df[[xaxe, value, value + '-Sev', value + '-Status']].copy()
        df = df0.copy()
        df2 = df.groupby([value + "-Status"]).count()
        df2 = df2.reset_index()
        df2['State'] = df2.apply(lambda row: colorstat[int(row[value + '-Status'])], axis=1)

        df = df2.reset_index()
        df = df.reset_index()
        df = df.sort_values(value + "-Status")
        df["colors"] = df.apply(lambda row: colordic[int(row[value + '-Status'])], axis=1)
        df["label"] = df.apply(lambda row: colorstat[int(row[value + '-Status'])], axis=1)

        fig.add_trace(go.Scatter(
            x=df0[xaxe], y=df0[value], name=value, marker={'color': "blue"}), row=1, col=1)
        fig.add_annotation(xref="x domain", yref="y domain", x=0.5, y=1.2, showarrow=False,
                           text="<b>" + value + "</b>", row=1, col=1)

        if df0[value].var() > 0:
            fig.add_trace(go.Histogram(x=df0[value], marker={'color': "blue"}, name="Density"), row=1, col=2)
            fig.add_annotation(xref="x domain", yref="y domain", x=0.5, y=1.2, showarrow=False,
                               text="<b>" + value + ' Density' "</b>", row=1, col=2)
        else:
            fig.add_trace(go.Histogram(x=df0[value + '-Sev'], marker={'color': "blue"}, visible=False), row=1, col=2)
            fig.add_annotation(xref="x domain", yref="y domain", x=0.5, y=1.2, showarrow=False,
                               text="<b>" + 'No variance' + "</b>", row=1, col=2)

        fig.add_trace(go.Scatter(
            x=df0[xaxe], y=df0[value + '-Sev'], name="Severity", marker={'color': "red"}), row=2, col=1)
        fig.add_annotation(xref="x domain", yref="y domain", x=0.5, y=1.2, showarrow=False,
                           text="<b>" + value + ' Severity' + "</b>", row=2, col=1)

        if df0[value + '-Sev'].var() > 0:
            fig.add_trace(go.Histogram(x=df0[value + '-Sev'], marker={'color': "red"},name="Severity density"), row=2, col=2)
            fig.add_annotation(xref="x domain", yref="y domain", x=0.5, y=1.2, showarrow=False,
                               text="<b>" + value + ' Severity density' "</b>", row=2, col=2)
        else:
            fig.add_trace(go.Histogram(x=df0[value + '-Sev'], marker={'color': "red"}, visible=False), row=2, col=2)
            fig.add_annotation(xref="x domain", yref="y domain", x=0.5, y=1.2, showarrow=False,
                               text="<b>" + 'No variance in severity' + "</b>", row=2, col=2)
        return dcc.Graph(figure=fig)
    else :
        return dcc.Graph(figure=outliers_graph(df,value,type=style))

def head_diagnosis_multiples_runs(df,name,date,features) :
    """
    This function return the head card of diagnosis, for a component with multiple runs, like a valve.
    df is the dataframe of data for only one component (like one valve)
    Name is the class of component for ids (singular !)
    The head proposes to choose the run (date column) to display, and which components of the run to display.
    Date is the column of df containing the names of runs.
    features are the parameters of a run to display.
    df is ValvesData.get_only_for_name(element["name"])
    """
    dropdown = dcc.Dropdown(
        df[date], placeholder="Select a run", id="" + name + "s-ad-run")
    checklist = dbc.Checklist(
        id="" + name + "-ad-value-list", options=features, inline=True,)
    button_group = html.Div([checklist], className="radio-group",)
    header = dbc.CardHeader([dropdown, button_group])
    body = dbc.CardBody([html.Div(id="" + name + "-radial-output")])
    card = dbc.Card([header, body])
    return card

def severity(val) :
    theme = {
        'dark': True,
        'detail': '#007439',
        'primary': '#00EA64',
        'secondary': '#6E6E6E',
    }
    return(html.Div(daq.DarkThemeProvider(
        theme=theme,
        children=daq.GraduatedBar(
            min=0,
            max=400,
            step=20,
            value=val,
            size=100,
            id='darktheme-daq-tank',
            className='dark-theme-control',
            color={"gradient":True,"ranges":{"green":[0,150],"yellow":[150,300],"red":[300,400]}},
        )),style={'verticalAlign' : "middle","height" : '5px !important'}))

dicostatus={1 : ["OK","#008000"], 2 : ["Potential Warning","#FFD801"], 3 : ["Warning","#FFA500"], 4 : ["Alarm","#FF0000"], 0 : ["No Information,""#FFFFFF"]}
def status_sev(data,va,sensor= None) :
    if sensor is not None :
        va = sensor + '_' + va
    el=dicostatus[int(data[va + "-Status"][0])]
    equip = html.Div(el[0], style={'color' : el[1],"font-size" : "20px", "verticalAlign": "middle"})
    """
    sev = daq.Gauge(
        color={"gradient": True, "ranges": {"green": [0, 150], "yellow": [150, 300], "red": [300, 400]}},
        value=data[va + "-Sev"][0],
        max=400,
        min=0,
        showCurrentValue=True,
        size = 100
    )
    """
    sev=severity(data[va + "-Sev"][0])
    tab_header=[html.Thead(html.Tr([html.Th("Status",style=centered), html.Th("Severity",style=centered)]))]
    content=html.Tbody([html.Tr([html.Td(html.Div(equip,style=centered)),html.Td(html.Div(sev,style = centered))])])
    table=dbc.Table(tab_header+[content],bordered=True,style={"table-layout" : "fixed"})
    top_card = dbc.Card(
        [
            dbc.CardHeader(html.Div(va +" Status", style={ "textAlign": "center"})),
            dbc.CardBody(equip,style={ "textAlign": "center"})
        ],
    )

    bottom_card = dbc.Card(
        [
            dbc.CardHeader(html.Div(va +" Severity",style={ "textAlign": "center"})),
            dbc.CardBody(sev,style={ "textAlign": "center"}),
        ],
    )

    cards = dbc.CardGroup(
        [
            top_card,
            bottom_card,
        ]
    )

    return (table)

def gaps(df) :
    gap=[]
    alone=[]
    for i in range(1,len(df.index)) :
        if df.index[i]-df.index[i-1] >1 :
            a=0
            if i < len(df.index)-1 :
                if df.index[i+1]-df.index[i] > 1 :
                    a=1
                    alone.append(df.index[i])
            if a == 0 :
                gap.append(df.index[i-1]+1)
    return gap,alone

def insert_Nan(df,index) :
    line = pd.DataFrame(data=[None], index=[index])
    dico={}
    for x in df.columns :
        dico[x]=None
    line = pd.DataFrame(dico, index=[index])
    df = df.append(line, ignore_index=False)
    df = df.sort_index().reset_index(drop=True)
    return(df.copy())

def nice_graph(data,xaxe,val,lab="auto",label="") :
    if lab == "auto" :
        df=data[[xaxe,val,val + '-Status']].copy()
    else :
        df=data[[xaxe,val,label]].copy()
    df1=df.copy()
    df=df.groupby(val+ '-Status')
    dfs = []
    colordic={1:"green",2:'yellow', 3:'orange',4 : 'red'}
    colorstat={1:"Ok",2:'Potential Warning', 3:'Warning',4 : 'Alert'}
    for name, dat in df:
        dfs.append(dat)

    # one line to connect them all
    fig=go.Figure((go.Scatter(x=df1[xaxe], y=df1[val],
                              name = 'All data',
                              line=dict(color='rgba(200,200,200,0.7)'))))
    def modes(df):
        if len(df) > 1: return 'lines'
        else: return  'markers'


    for frame in dfs:
        gap,alone=gaps(frame)
        frame.drop(frame[frame.index.isin(alone)].index, inplace=True)
        for i in gap :
            frame=insert_Nan(frame,i)

        fig.add_trace(go.Scatter(x=frame[xaxe], y = frame[val],
                                 mode = modes(frame),
                                 marker_color =colordic[int(frame[val+ '-Status'].iloc[0])],
                                 legendgroup=frame[val+ '-Status'].iloc[0],
                                 name=colorstat[int(frame[val+ '-Status'].iloc[0])],
                                connectgaps=False),
                                 )
    fig.update_layout(template='plotly_dark')
    fig.update_layout(hovermode="x unified")
    fig.update_xaxes(showgrid=False)
    fig.update_layout(uirevision='constant')
    return fig


def piechartstatus(data,value) :
    df=data[[value+ "-Status"]].copy()
    colordic={1:"green",2:'yellow', 3:'orange',4 : 'red'}
    colorstat={1:"Ok",2:'Potential Warning', 3:'Warning',4 : 'Alert'}
    df2=df.groupby([value+ "-Status"]).count()
    df2=df2.reset_index()
    df2['name']=df2.apply(lambda row : colorstat[int(row[value+ "-Status"])], axis = 1)
    fig = px.pie(df2, values=value+ "-Status",names="name", color=value+ "-Status", color_discrete_map=colordic)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(title_text=value + ": Percentage of time in each status", title_x=0.5)
    return dcc.Graph(figure=fig)

def diff(serie,order=1) :
    for i in range(order) :
        serie=serie.diff()
        serie.drop(serie.index[0],inplace=True)
    return(serie)

def pacf_graph(data,value,order=1) :
    serie=diff(data[value],order)
    plot_pacf(serie,method='ywm')
    s = io.BytesIO()
    plt.savefig(s, format='png')
    s = base64.b64encode(s.getvalue()).decode("utf-8").replace("\n", "")
    plt.clf()
    return html.Img(src='data:image/png;base64,{}'.format(s),style={'width':'100%'})

def acf_graph(data,value,order=1) :
    serie=diff(data[value],order)
    plot_acf(serie)
    s = io.BytesIO()
    plt.savefig(s, format='png')
    s = base64.b64encode(s.getvalue()).decode("utf-8").replace("\n", "")
    plt.clf()
    return html.Img(src='data:image/png;base64,{}'.format(s),style={'width':'100%'})

def insampleforecast(data,value,model,rate=0.2) :
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=data[value].index,y=data[value],name=value))
    lag=int((1-rate)*len(data[value]))
    xaxe=[i + lag for i in range(len(data[value])-lag)]
    fig.add_trace(go.Scatter(x=xaxe,y=model.predict(start=lag),name= value + ' in-sample prediction'))
    return dcc.Graph(figure=fig)

def diagnosis(model) :
    model.plot_diagnostics()
    s = io.BytesIO()
    plt.savefig(s, format='png')
    s = base64.b64encode(s.getvalue()).decode("utf-8").replace("\n", "")
    plt.clf()
    return html.Img(src='data:image/png;base64,{}'.format(s), style={'width': '100%'})

def Kelbowgraph(data,val) :
    model = KElbowVisualizer(KMeans(), k=(1, 10))
    work = data[val].reset_index().copy()
    work = (work - work.mean()) / work.std()
    work = work.to_numpy()
    model.fit(work)
    model.show()
    s = io.BytesIO()
    plt.legend(labels=[val])
    plt.savefig(s, format='png')
    s = base64.b64encode(s.getvalue()).decode("utf-8").replace("\n", "")
    plt.clf()
    return html.Img(src='data:image/png;base64,{}'.format(s),style={'height':'50%',"textAlign": "center", "verticalAlign": "middle"})

def Kelbowgraph3D(data,val1,val2) :
    model = KElbowVisualizer(KMeans(), k=(1, 10))
    work = data[[val1,val2]].reset_index().copy()
    work = (work - work.mean()) / work.std()
    work = work.to_numpy()
    model.fit(work)
    model.show()
    s = io.BytesIO()
    plt.savefig(s, format='png')
    s = base64.b64encode(s.getvalue()).decode("utf-8").replace("\n", "")
    plt.clf()
    return html.Img(src='data:image/png;base64,{}'.format(s),style={'height':'50%',"textAlign": "center", "verticalAlign": "middle"})

def cluster_graph(data, val, n,method):
    work = data[val].reset_index().copy()
    work = (work - work.mean()) / work.std()
    work = work.to_numpy()
    if method == "Kmeans" :
        banane = pd.DataFrame(KMeans(n_clusters=n).fit_predict(work))
    elif method == "DBSCAN" :
        banane = pd.DataFrame(DBSCAN(eps=0.2).fit_predict(work))
    else :
        banane = pd.DataFrame(OPTICS(min_samples=50).fit_predict(work))
    banane.columns = ['result']
    disp = pd.concat([data[val], banane], axis=1).reset_index()

    fig = px.scatter(x=disp['index'], y=disp[val], color=disp["result"], labels=dict(x="Time", y=val))
    fig.update(layout_coloraxis_showscale=False)

    return dcc.Graph(figure=fig)

def cluster_graph3D(data, val1, val2, n,method):
    work = data[[val1,val2]].reset_index().copy()
    work = (work - work.mean()) / work.std()
    work = work.to_numpy()
    if method == "Kmeans" :
        banane = pd.DataFrame(KMeans(n_clusters=n).fit_predict(work))
    elif method == "DBSCAN" :
        banane = pd.DataFrame(DBSCAN(eps=0.2).fit_predict(work))
    else :
        banane = pd.DataFrame(OPTICS(min_samples=50).fit_predict(work))
    banane.columns = ['result']
    disp = pd.concat([data[[val1,val2]], banane], axis=1).reset_index()

    disp["size"] = 1
    fig = px.scatter_3d(disp, x=val1, y=val2, z="index",
                        color='result', size="size", size_max=10)
    fig.update(layout_coloraxis_showscale=False)
    fig.update_layout(
        title_text="Operating conditions of " + val1 + " and " + val2 + ' clusterized over time (' + method + ' algorithm)',
        title_x=0.5)
    return dcc.Graph(figure=fig)

def outliers_graph(data,val,type="Outliers Detection (Isolation Forest)") :
    work=data[val].reset_index().copy()
    work=(work-work.mean())/work.std()
    work=work.to_numpy()
    if type == "Outliers Detection (Isolation Forest)" :
        banane=pd.DataFrame(IsolationForest(n_estimators=10).fit_predict(work))
        title ="Outliers of " + val + " (Isolation Forest method)"
    elif type == "Outliers Detection (Local Outlier Factor)" :
        banane = pd.DataFrame(LocalOutlierFactor().fit_predict(work))
        title = "Outliers of " + val + " (Local Outlier Factor)"
    banane.columns=['result']
    disp=pd.concat([data[val],banane], axis=1).reset_index()
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=disp['index'], y=disp[val],line=dict(color='blue'),name=val))
    fig.add_trace(go.Scatter(x=disp[disp['result']==-1]['index'], y=disp[disp['result']==-1][val],mode="markers",marker_color ="red",name='Outliers'))
    fig.update(layout_coloraxis_showscale=False)
    fig.update_layout(title_text=title, title_x=0.5)
    return fig
