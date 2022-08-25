# importing libraries
import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import dcc, html
import argparse

# Base defines the style of the differents components of the mainpage
from templates import  base, callbacks, header, sidebar,config,launch_mode

# Creating the app
app = dash.Dash(external_stylesheets=[
                dbc.themes.FLATLY], suppress_callback_exceptions=True)
callbacks.get_callbacks(app)
app.title = "CADIS Offline"

content = html.Div([], id="page-content", style=base.CONTENT_STYLE)



L = [dcc.Loading(children=html.Div(id=name + '-hole')) for name in config.dicobucket.values()]
def mainpage():
    """
    Define the layout of the mainpage (Allows to use Notifications, wrap into MantineProvider allows to set the theme globally)
    The main information is content, which is defined in home
    Header contains the Navigation bar beetwen home and the differents components
    """
    layout = dmc.MantineProvider(
        dmc.NotificationsProvider([
            dcc.Location(id="url"), html.Div(
                id="notifications-container"),  header.content, sidebar.content,content] + L
        ))
    return layout



app.layout = mainpage

parser = argparse.ArgumentParser(description="Arguments go in here")
parser.add_argument('--local',
                    help='runs in local enviroment instead of docker')

args = parser.parse_args()


## TODO
# change the host to be empty in case of running in local enviroment
# https://docs.python.org/3/library/argparse.html
#add
# if RunningInLocal:
#     host = "0.0.0.0"
# else
#     host = "127.0.0.1"



#host = "0.0.0.0"
host = launch_mode.host
# Running the app
if __name__ == "__main__":
    app.run_server(host=host, port=8888, debug=True)
