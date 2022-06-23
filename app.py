from collections import Counter
from datetime import date, datetime

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

# Layout
app.layout = html.Div([
    html.H1("IT offers dashboards at specific date", style={'text-align': 'center'}),

    dcc.Dropdown(id="select-day",
                 options=[
                     {"label": "20-06-2022", "value": 20220620},
                     {"label": "21-06-2022", "value": 20220621},
                     {"label": "22-06-2022", "value": 20220622},
                     {"label": "23-06-2022", "value": 20220623}],
                 multi=False,
                 value=20220623,
                 style={"width": "40%"}),

    dcc.Graph(id="it-offers-salary", figure={}),
    dcc.Graph(id="skills-pop", figure={}),


    html.H2("IT offers inflation", style={'text-align': 'center'}),

    dcc.Graph(id="average-salary", figure={}),
])


# Update graph
@app.callback(
    [Output(component_id="it-offers-salary", component_property="figure"),
     Output(component_id="skills-pop", component_property="figure"),
     Output(component_id="average-salary", component_property="figure")],
    [Input(component_id="select-day", component_property="value")]
)
def update_graph(option_selected):
    df = pd.read_sql_query(
        sql="SELECT title, skills, category, level, company, date, min_salary, max_salary FROM offers",
        con=conn)

    # additional column of mean salary
    df["salary"] = df[["min_salary", "max_salary"]].mean(axis=1)

    dff = df.copy()
    dff = dff[dff["date"] == option_selected]

    # plotly express
    salary_fig = px.histogram(dff, x="salary", nbins=100)
    salary_fig.update_layout(bargap=0.1, xaxis_title_text='Salary', yaxis_title_text='Count',
                             title_text='Offered salary for IT specialists')
    
    # skills extraction from 'skills' column
    skill_sets = dff.skills.apply(lambda x: x[1:-1].split(','))
    skills = [skill.replace("'", '').replace(' ', '') for skill_set in skill_sets for skill in skill_set]
    skills = [skill for skill in skills if skill]

    # count skills
    skills_count = dict(Counter(skills))

    # pie chart
    skills_pop_fig = px.pie(values=skills_count.values(), names=skills_count.keys(),
                            title='Popularity of different skills',
                            width=1600, height=1000)

    # avg salary
    avg_salary_df = df.groupby("date")[["min_salary", "salary", "max_salary"]].mean()
    avg_salary_df["date"] = pd.to_datetime(avg_salary_df.index, format='%Y%m%d')
    avg_salary_fig = px.scatter(avg_salary_df, x="date", y="salary", trendline="ols")
    avg_salary_fig.update_layout(xaxis_title_text="Day", yaxis_title_text="Salary")
    avg_salary_fig.update_xaxes(dtick="D1")

    return salary_fig, skills_pop_fig, avg_salary_fig


if __name__ == "__main__":
    app.run_server(debug=True)





