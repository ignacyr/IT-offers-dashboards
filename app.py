from collections import Counter
from datetime import date

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

max_date_int = pd.read_sql_query(sql="SELECT date FROM offers", con=conn)["date"].max()
max_date_s = str(max_date_int)
max_date_in_db = date(year=int(max_date_s[0:4]), month=int(max_date_s[4:6]), day=int(max_date_s[6:8]))

# Layout
app.layout = html.Div([
    html.H1("IT offers dashboards at specific date", style={'text-align': 'center'}),

    dcc.DatePickerSingle(
        id='date-picker-single',
        min_date_allowed=date(2022, 6, 20),
        max_date_allowed=max_date_in_db,
        initial_visible_month=max_date_in_db,
        date=max_date_in_db,
        display_format='D-M-Y'
    ),

    dcc.Graph(id="it-offers-salary", figure={}),
    dcc.Graph(id="skills-pop", figure={}),

    html.H1("IT offers inflation", style={'text-align': 'center'}),

    dcc.Graph(id="average-salary", figure={}),
])


# Update graph
@app.callback(
    [Output(component_id="it-offers-salary", component_property="figure"),
     Output(component_id="skills-pop", component_property="figure"),
     Output(component_id="average-salary", component_property="figure"),
     Output(component_id="date-picker-single", component_property="max_date_allowed")],
    [Input(component_id="date-picker-single", component_property="date")]
)
def update_graph(date_dt):
    date_int = int(date_dt.replace('-', ''))

    df = pd.read_sql_query(
        sql="SELECT title, skills, category, level, company, date, min_salary, max_salary FROM offers",
        con=conn)

    max_date = df["date"].max()

    # additional column of mean salary
    df["salary"] = df[["min_salary", "max_salary"]].mean(axis=1)

    dff = df.copy()
    dff = dff[dff["date"] == date_int]

    # plotly express
    salary_fig = px.histogram(dff[dff["max_salary"] < 100000], x="salary", nbins=100)  # throw away offers higher than 100k
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
                            width=1200, height=800)

    # avg salary
    avg_salary_df = df.groupby("date")[["min_salary", "salary", "max_salary"]].mean()
    avg_salary_df["date"] = pd.to_datetime(avg_salary_df.index, format='%Y%m%d')
    avg_salary_fig = px.scatter(avg_salary_df, x="date", y="salary", trendline="lowess")
    avg_salary_fig.update_layout(xaxis_title_text="Day", yaxis_title_text="Salary")
    avg_salary_fig.update_xaxes(dtick="D1")

    max_date_str = str(max_date)
    max_date_dt = date(year=int(max_date_str[0:4]), month=int(max_date_str[4:6]), day=int(max_date_str[6:8]))

    return salary_fig, skills_pop_fig, avg_salary_fig, max_date_dt


if __name__ == "__main__":
    app.run_server(debug=True)
