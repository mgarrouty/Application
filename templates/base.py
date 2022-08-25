import base64
import os

from dash import html

# icons used are from https://icon-sets.iconify.design/

header_height, footer_height = "5rem", "0rem"
#header_height, footer_height = "10rem", "5rem"
sidebar_width, adbar_width = "18rem", "12rem"

HEADER_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "right": 0,
    "height": header_height,
    "padding": "0.5rem 1rem 1rem 1rem",
    "background-color": "white",
    "zIndex" : 999,
}

SIDEBAR_STYLE = {
    "position": "fixed",
    "top": header_height,
    "left": 0,
    "bottom": footer_height,
    "width": sidebar_width,
    "padding": "1rem 1rem",
    "background-color": "white",
}

ADBAR_STYLE = {
    "position": "fixed",
    "top": header_height,
    "right": 0,
    "bottom": footer_height,
    "width": adbar_width,
    "padding": "1rem 1rem",
    "background-color": "white",
}

FOOTER_STYLE = {
    "bottom": "0%",
    "position": "fixed",
    "padding": "1rem 1rem",
    "background-color": "white",
}

CONTENT_STYLE = {
    "margin-top": header_height,
    "margin-left": sidebar_width,
    "margin-right": adbar_width,
    "margin-bottom": footer_height,
    "padding": "1rem 1rem",
}

CADIS_logo_style = {'display': 'inline-block',
                    'margin': '10px', 'font-weight': 'bold'}

CADIS_Logo = html.Div([html.H2("I ", style={'color': 'Orange'} | CADIS_logo_style, className="display-2"),
                       html.H2("CADIS", style={'color': 'Blue'} | CADIS_logo_style, className="display-2")])


#Get framatome's logo
def get_framatome_logo():
    cwd = os.getcwd()
    image_file = 'RVB_FRAMATOME_HD.png'  # replace with your own image
    image_filename = os.path.join(cwd, "images", image_file)
    encoded_image = base64.b64encode(open(image_filename, 'rb').read())
    return html.Img(src='data:image/png;base64,{}'.format(encoded_image.decode()), style={"float": "right", 'width': '10%'})
