import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
import requests
import datetime
import threading
import time
import logging

# Global data storage
rc1_data = {"player_count": [], "seeders": []}
rc2_data = {"player_count": [], "seeders": []}
rc3_data = {"player_count": [], "seeders": []}
active_accounts = []
idle_accounts = []
log_output_lines = []

# Set up logging and custom handler
class DashLogHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)
        log_output_lines.append(log_entry)
        # Keep log_output_lines from growing indefinitely.
        if len(log_output_lines) > 100:
            del log_output_lines[0]

# Configure logging (and attach our custom handler)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()
logger.addHandler(DashLogHandler())

# Function to fetch data in the background
def fetch_data():
    global rc1_data, rc2_data, rc3_data, active_accounts, idle_accounts
    while True:
        try:
            # Fetch server stats
            RC1_response = requests.get("https://battlelog.battlefield.com/bf4/servers/show/pc/cfa68ec0-a030-4247-90e1-9b643a71edcd/?json=1&join=true")
            RC2_response = requests.get("https://battlelog.battlefield.com/bf4/servers/show/pc/8529e349-cd4a-4fa1-965a-afb4e8d7431e/?json=1&join=true")
            RC3_response = requests.get("https://battlelog.battlefield.com/bf4/servers/show/pc/de2e60c6-159a-4a5b-b30d-a1ee51998a8d/?json=1&join=true")
            
            RC1_gameID = RC1_response.json()["data"]["gameId"]
            RC2_gameID = RC2_response.json()["data"]["gameId"]
            RC3_gameID = RC3_response.json()["data"]["gameId"]
            
            RC1_playercount = RC1_response.json()["data"]["slots"]["2"].get("current", 0)
            RC2_playercount = RC2_response.json()["data"]["slots"]["2"].get("current", 0)
            RC3_playercount = RC3_response.json()["data"]["slots"]["2"].get("current", 0)
            
            # Fetch account data
            response = requests.get("https://accounting.rtx3080sc.workers.dev/")
            accounts = response.json()
            actives = []
            idles = []
            for Account in accounts:
                if Account["inServer"]:
                    actives.append(f"{Account['Account']} - active")
                else:
                    idles.append(f"{Account['Account']} - idle")
            
            active_accounts = actives
            idle_accounts = idles
            
            # Update graph data with current timestamp
            timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            rc1_data["player_count"].append({"timestamp": timestamp, "count": RC1_playercount})
            rc1_data["seeders"].append({"timestamp": timestamp, "count": sum(1 for Account in accounts if Account["gameID"] == RC1_gameID)})
            
            rc2_data["player_count"].append({"timestamp": timestamp, "count": RC2_playercount})
            rc2_data["seeders"].append({"timestamp": timestamp, "count": sum(1 for Account in accounts if Account["gameID"] == RC2_gameID)})
            
            rc3_data["player_count"].append({"timestamp": timestamp, "count": RC3_playercount})
            rc3_data["seeders"].append({"timestamp": timestamp, "count": sum(1 for Account in accounts if Account["gameID"] == RC3_gameID)})
            
            logging.debug(f"{timestamp} - Fetched: RC1={RC1_playercount}, RC2={RC2_playercount}, RC3={RC3_playercount}")
        except Exception as e:
            logging.error(f"Error fetching data: {e}")
        time.sleep(30)

# Start the background data fetching thread
threading.Thread(target=fetch_data, daemon=True).start()

# Create the Dash app
app = dash.Dash(__name__)

# Define the layout with top graphs, bottom left accounts, bottom right logs
app.layout = html.Div(children=[
    # Top row: Graphs for RC1, RC2, RC3
    html.Div([
        html.Div([
            html.H3("RC1 - Player Count & Seeders", style={'color': '#ffffff'}),
            dcc.Graph(id='rc1-graph')
        ], style={'width': '33%', 'display': 'inline-block'}),
        html.Div([
            html.H3("RC2 - Player Count & Seeders", style={'color': '#ffffff'}),
            dcc.Graph(id='rc2-graph')
        ], style={'width': '33%', 'display': 'inline-block'}),
        html.Div([
            html.H3("RC3 - Player Count & Seeders", style={'color': '#ffffff'}),
            dcc.Graph(id='rc3-graph')
        ], style={'width': '33%', 'display': 'inline-block'})
    ], style={'width': '100%', 'display': 'block'}),
    
    # Bottom row: Active/Idle Accounts and Log Output
    html.Div([
        html.Div([
            html.H3("Active & Idle Accounts", style={'color': '#ffffff'}),
            html.Div(id='account-list', style={'color': '#ffffff'})
        ], style={'width': '50%', 'display': 'inline-block', 'verticalAlign': 'top'}),
        html.Div([
            html.H3("Log Output", style={'color': '#ffffff'}),
            html.Pre(id='log-output', style={'overflowY': 'scroll', 'height': '300px', 'backgroundColor': '#333333', 'color': '#ffffff'})
        ], style={'width': '50%', 'display': 'inline-block', 'verticalAlign': 'top'})
    ], style={'width': '100%', 'display': 'block', 'marginTop': '20px'}),

    # Add Interval component for auto-refresh every 30 seconds
    dcc.Interval(
        id='interval-component',
        interval=30*1000,  # 30 seconds in milliseconds
        n_intervals=0
    )
], style={'backgroundColor': '#121212', 'color': '#ffffff', 'minHeight': '100vh'})

# Callback to update all sections periodically (triggered by Interval)
@app.callback(
    Output('rc1-graph', 'figure'),
    Output('rc2-graph', 'figure'),
    Output('rc3-graph', 'figure'),
    Output('account-list', 'children'),
    Output('log-output', 'children'),
    Input('interval-component', 'n_intervals')  # Trigger update every interval
)
def update_dashboard(n_intervals):
    def create_figure(data, title):
        timestamps = [entry['timestamp'] for entry in data["player_count"]]
        player_counts = [entry['count'] for entry in data["player_count"]]
        seeders = [entry['count'] for entry in data["seeders"]]
        return {
            'data': [
                go.Scatter(x=timestamps, y=player_counts, mode='lines+markers', name='Player Count'),
                go.Scatter(x=timestamps, y=seeders, mode='lines+markers', name='Seeders')
            ],
            'layout': go.Layout(
                title=title,
                xaxis={'title': 'Time', 'color': '#ffffff'},
                yaxis={'title': 'Count', 'color': '#ffffff'},
                plot_bgcolor='#121212',
                paper_bgcolor='#121212',
                font={'color': '#ffffff'}
            )
        }
    
    rc1_fig = create_figure(rc1_data, "RC1 - Player Count & Seeders")
    rc2_fig = create_figure(rc2_data, "RC2 - Player Count & Seeders")
    rc3_fig = create_figure(rc3_data, "RC3 - Player Count & Seeders")
    
    accounts_list_component = html.Ul([html.Li(acc) for acc in (active_accounts + idle_accounts)])
    log_text = "\n".join(log_output_lines)
    
    return rc1_fig, rc2_fig, rc3_fig, accounts_list_component, log_text

if __name__ == '__main__':
    app.run(debug=True)
