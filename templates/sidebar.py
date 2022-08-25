from dash import Input, Output, html

from templates import base, sidebar, pumps,sues,rcps,ol3s

content = html.Div([],
                   style=base.SIDEBAR_STYLE, id="sidebar-content"
                   )

# Sidebar is only visible when a class of component is choosen. Otherwise, it is an empty div (for homepage for instance)


def sidebar_callbacks(app):
    @app.callback(Output("sidebar-content", "children"), Input("url", "pathname"))
    def render_sidebar_content(pathname):
        if pathname in ["/", "/Home"]:
            return sidebar.content
        elif pathname == "/Pumps" :
            return pumps.sidebar_content()
        elif pathname == "/SUES" :
            return sues.sidebar_content()
        elif pathname == '/RCPS':
            return rcps.sidebar_content()
        elif pathname == '/OL3S':
            return ol3s.sidebar_content()
