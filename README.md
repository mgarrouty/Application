# CadisMockup

This is a MockUp Dash App used to examplify the future desing goal of CADIS as a Asset Management Dashboard.

## Requires:
`Python>3.10`

## Install:

Execute the `make_venv.bat` this will generate a enviroment install the necessary packages from pip and run the app.

## Running:

To view the page open the `Cadis.html` shortcut.

## Running in Docker:

To run in docker build the `dockerfile` and then run with -p 8888:8888 
Also the `clean.bat` file can be used to speed up the process to make sure that no venv of normal runs remains.

To run in Docker use the commands 'docker build --tag python-docker .' to build the container and then run with the ports options set to 8888 for the TCP port of the container 8888