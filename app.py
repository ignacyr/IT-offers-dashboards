from dash import dcc, html, Dash
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
import sqlalchemy

app = Dash(__name__)
server = app.server

# Connect to postgres and import, clean data
password_reporting_user = "plzanalyzeme69"
conn = sqlalchemy.create_engine(
    f"postgresql://reporting_user:{password_reporting_user}@it-offers.c9umk0ew1r8h.us-east-1.rds.amazonaws.com:5432/dwh")
df = pd.read_sql_query(
    sql="SELECT title, skills, category, level, company, date, min_salary, max_salary FROM offers",
    con=conn)

# Layout
app.layout = html.Div([
    html.H1("IT offers dashboards", style={'text-align': 'center'}),

    dcc.Dropdown(id="select-day",
                 options=[
                     {"label": "20-06-2022", "value": 20220620},
                     {"label": "21-06-2022", "value": 20220621}],
                 multi=False,
                 value=20220620,
                 style={"width": "40%"}),

    html.Br(),

    dcc.Graph(id="it-offers-min-salary", figure={}),
    dcc.Graph(id="it-offers-max-salary", figure={})
])


@app.callback(
    [Output(component_id="it-offers-min-salary", component_property="figure"),
     Output(component_id="it-offers-max-salary", component_property="figure")],
    [Input(component_id="select-day", component_property="value")]
)
def update_graph(option_selected):
    dff = df.copy()
    dff = dff[dff["date"] == option_selected]

    # plotly express
    min_salary_fig = px.histogram(dff, x="min_salary", nbins=100)
    max_salary_fig = px.histogram(dff, x="max_salary", nbins=100)

    return min_salary_fig, max_salary_fig


if __name__ == "__main__":
    app.run_server(debug=True)





