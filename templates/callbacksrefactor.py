from dash.dependencies import Input, Output, State
from dash import ALL


def filter(name) :
    """
    This function return the Output, Input and State of filtering callbacks, supposing each div has an id in a good way.
    """
    return ([Output("" + name + "-sidebar-content", "children"),
         Output("" + name + "-filter", "value"),
         Output("" + name + "-content", "children")],
        [Input("" + name + "-filter-button", "n_clicks"),
         Input({'type': "" + name + '-button', 'index': ALL}, 'n_clicks')],
        State("" + name + "-filter", "value"))

def rendercontent(name) :
    """
        This function return the Output, Input and State of rendercontent callbacks, supposing each div has an id in a good way.
        """
    return (Output("" + name + '-tab-content', 'children'),
            Input(name + "-hole", "id"), Input("" + name + 's-card-tabs', "active_tab"),Input(name + "-hole",'children'),
                  [State({'type': "" + name + '-button', 'index': ALL}, 'id'),
                   State({'type': "" + name + '-button', 'index': ALL}, 'active')])

def param_from_channel(name) :
    return(Output(name + "-channel-features-dropdown", "options"), Input(name + 's-ad-value-list', "value"))

def info_for_channel(name) :
    return(Output(name + "main_info", "children"), Input(name +'s-ad-value-list', "value"))

def inf_for_param(name) :
    return(Output(name + "main_info_param", "children"), Input(name +'s-ad-value-list', "value"),Input(name + "-channel-features-dropdown", "value"))

def graph_options(name,compare = False) :
    if compare :
        return(Output(name + "-compare-graph-style", "options"), Output(name + "-compare-graph-style", "value"),
                  Input(name + "-param-compare-dropdown", "value"))
    else :
        return(Output(name + "-graph-style", "options"),Output(name + "-graph-style", "value"),Input(name + "-channel-features-dropdown", "value"),Input(name + "-graph-style", "value"))


def graph(name,compare=False) :
    if compare :
        return(Output(name + "-compare-radial-output", "children"),
                  Input(name + "-param-compare-dropdown", "value"), Input(name + '-compare-graph-style', 'value'),
                  Input(name + "-compare-radios","value"),
                  State({'type': name + '-button', 'index': ALL}, 'id'),
                  State({'type': name + '-button', 'index': ALL}, 'active'), State(name + "s-param-compare-list", "value"))
    else :
        return(Output(name + "-radial-output", "children"),
                  Input(name + "-channel-features-dropdown", "value"), Input(name + '-graph-style','value'),
                  State({'type': name + '-button', 'index': ALL}, 'id'),
                   State({'type': name + '-button', 'index': ALL}, 'active'), State(name + "s-ad-value-list","value"))

def channel_from_param(name) :
    return(Output(name + "-param-compare-dropdown","options"),Input(name + 's-param-compare-list', "value"))


