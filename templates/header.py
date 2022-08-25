from email import header

import dash_bootstrap_components as dbc
from dash import html
from dash.dependencies import Input, Output

from templates import base, config


def build_nav():
    """
    Creating the navbar item, based on the list of components at config.page, self-generating ids and links
    """
    navitems = []
    for item in config.pages:
        button_id = "page-" + str(config.pages.index(item)+1) + "-link"
        link = "/"+item
        button = dbc.Button(item, href=link, id=button_id,
                            outline=True, color="primary")
        navitems.append(button)
    nav = dbc.ButtonGroup(navitems)
    logout_button = dbc.Button(
        "Logout", color="link", style={'float': 'right'})
    row = dbc.Row(
        [
            dbc.Col(nav),
            dbc.Col(logout_button),
        ],
        align="end", justify="start"
    )
    return row


# content = html.Div([base.CADIS_Logo, build_nav()], style=base.HEADER_STYLE)
content = html.Div(build_nav(), style=base.HEADER_STYLE)


def headerCallback(app):
    """
    Creating the callback to direct navbar to the right page, page 1 ('/') is treated as the homepage
    """
    @app.callback(
        [Output(f"page-{i}-link", "active")
         for i in range(1, len(config.pages)+1)],
        [Input("url", "pathname")],
    )
    def toggle_active_links(pathname):
        if pathname == "/":
            # Treat page 1 as the homepage / index
            return [True.__eq__(not bool(i)) for i in range(len(config.pages))]
        return [pathname in "/"+item for item in config.pages]
