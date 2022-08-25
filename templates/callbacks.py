import dash_bootstrap_components as dbc
from dash import html
from dash.dependencies import Input, Output

from templates import (header, home, pumps, sues, rcps, ol3s,
                       sidebar, utils)

#Getting all callbacks from all pages here
def get_callbacks(app):
    """
    this callback uses the current pathname to set the active state of the
    corresponding nav link to true, allowing users to tell see page they are on
    """

    @app.callback(Output("page-content", "children"), Input("url", "pathname"))
    def render_page_content(pathname):
        if pathname in ["/", "/Home"]:
            return home.content()
        elif pathname == "/Pumps":
            return pumps.content
        elif pathname == '/SUES' :
            return sues.content
        elif pathname == '/RCPS':
            return rcps.content
        elif pathname == '/OL3S':
            return ol3s.content
        # If the user tries to reach a different page, return a 404 message
        return html.Div(
            [
                html.H1("404: Not found", className="text-danger"),
                html.Hr(),
                html.P(f"The pathname {pathname} was not recognised..."),
            ]
        )

    header.headerCallback(app)
    home.HomeCallbacks(app)
    pumps.callback(app,"pump",pumps.vardict)
    sidebar.sidebar_callbacks(app)
    sues.callback(app,"sue",sues.vardict)
    ol3s.callback(app,"ol3",ol3s.vardict)
    rcps.callback(app,"rcp",rcps.vardict)

