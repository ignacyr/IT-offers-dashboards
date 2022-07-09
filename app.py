from collections import Counter
from datetime import date

from dash import dcc, html, Dash
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
import sqlalchemy
import pandasql as ps

# from wordcloud import WordCloud

app = Dash(__name__)
server = app.server

# Connect to postgres and import, clean data
password_reporting_user = "plzanalyzeme69"
conn = sqlalchemy.create_engine(
    f"postgresql://reporting_user:{password_reporting_user}@it-offers.c9umk0ew1r8h.us-east-1.rds.amazonaws.com:5432/dwh")

max_date_int = pd.read_sql_query(sql="SELECT date FROM offers", con=conn)["date"].max()
max_date_s = str(max_date_int)
max_date_in_db = date(year=int(max_date_s[0:4]), month=int(max_date_s[4:6]), day=int(max_date_s[6:8]))
min_date_in_db = date(2022, 6, 20)

app.title = "IT offers"
# Layout
app.layout = html.Div([
    html.H1("Polish IT offers", style={'text-align': 'center'}),

    dcc.DatePickerSingle(
        id='date-picker-single',
        min_date_allowed=min_date_in_db,
        max_date_allowed=max_date_in_db,
        initial_visible_month=max_date_in_db,
        date=max_date_in_db,
        display_format='D-M-Y'
    ),

    dcc.Graph(id="it-offers-salary", figure={}),
    dcc.Graph(id="skills-salary", figure={}),
    dcc.Graph(id="levels-salary", figure={}),
    dcc.Graph(id="skills-pop", figure={}),
    dcc.Graph(id="categories-pop", figure={}),

    html.H1("Polish IT salaries inflation", style={'text-align': 'center'}),

    dcc.Graph(id="average-salary", figure={}),

    # html.Img(src='assets/skills.png'),
    # html.Img(src='assets/categories.png')
])


# Update graph
@app.callback(
    [Output(component_id="it-offers-salary", component_property="figure"),
     Output(component_id="skills-salary", component_property="figure"),
     Output(component_id="levels-salary", component_property="figure"),
     Output(component_id="skills-pop", component_property="figure"),
     Output(component_id="categories-pop", component_property="figure"),
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
    salary_fig = px.histogram(dff[dff["salary"] < 75000], x="salary", nbins=100)  # throw away offers higher than 75k
    salary_fig.update_layout(bargap=0.1, xaxis_title_text='Salary', yaxis_title_text='Count',
                             title_text='Offered salary for IT specialists')

    # skills extraction from 'skills' column
    skill_sets = dff.skills.apply(lambda x: x[1:-1].split(','))
    skills = [skill.replace("'", '').replace(' ', '') for skill_set in skill_sets for skill in skill_set]
    skills = [skill for skill in skills if skill]
    # count skills
    skills_count = dict(Counter(skills))
    new_skill_count = {}
    other_skills_count = 0
    for k, v in skills_count.items():
        if v >= 100:
            new_skill_count[k] = v
        else:
            other_skills_count += v
    if "other" in new_skill_count:
        new_skill_count["other"] += other_skills_count
    else:
        new_skill_count["other"] = other_skills_count
    # pie chart skills popularity
    skills_pop_fig = px.pie(values=new_skill_count.values(), names=new_skill_count.keys(),
                            title='Popularity of different skills', height=800)
    skills_pop_fig.update_traces(textposition='inside', textinfo='percent+label')

    # categories extraction from 'category' column
    cat_sets = dff.category.apply(lambda x: x[1:-1].split(','))
    categories = [cat.replace("'", '').replace(' ', '') for cat_set in cat_sets for cat in cat_set]
    categories = [cat for cat in categories if cat]
    # count categories
    categories_count = dict(Counter(categories))
    new_cat_count = {}
    other_cat_count = 0
    for k, v in categories_count.items():
        if v >= 100:
            new_cat_count[k] = v
        else:
            other_cat_count += v
    if "other" in new_cat_count:
        new_cat_count["other"] += other_cat_count
    else:
        new_cat_count["other"] = other_cat_count
    # pie chart categories popularity
    categories_pop_fig = px.pie(values=new_cat_count.values(), names=new_cat_count.keys(),
                                title='Popularity of different categories', height=800)
    categories_pop_fig.update_traces(textposition='inside', textinfo='percent+label')

    # avg salary
    avg_salary_df = df.groupby("date")[["min_salary", "salary", "max_salary"]].median()
    avg_salary_df["date"] = pd.to_datetime(avg_salary_df.index, format='%Y%m%d')
    avg_salary_fig = px.scatter(avg_salary_df, x="date", y="salary", trendline="lowess")
    avg_salary_fig.update_layout(xaxis_title_text="Day", yaxis_title_text="Salary")
    avg_salary_fig.update_xaxes(dtick="D1")
    max_date_str = str(max_date)
    max_date_dt = date(year=int(max_date_str[0:4]), month=int(max_date_str[4:6]), day=int(max_date_str[6:8]))

    # word clouds
    # skills_cloud = WordCloud(width=1000, height=500, background_color="white").generate(" ".join(skills))
    # skills_cloud.to_file("assets/skills.png")
    # categories_cloud = WordCloud(width=800, height=500, background_color="white").generate(" ".join(categories))
    # categories_cloud.to_file("assets/categories.png")

    skill_level_salary_df = pd.DataFrame(columns=['skill', 'level', 'salary'])
    for skill in set(skills):
        for level in ('trainee', 'junior', 'mid', 'senior', 'expert'):
            if avg := ps.sqldf(f"select avg(salary) from dff where skills like '%{skill}%' and level like '%{level}%'")['avg(salary)'][0]:
                skill_level_salary_df.loc[len(skill_level_salary_df)] = {'skill': skill, 'level': level, 'salary': avg}
            else:
                skill_level_salary_df.loc[len(skill_level_salary_df)] = {'skill': skill, 'level': level, 'salary': 100}

    skill_sal_fig = px.histogram(skill_level_salary_df, x="skill", y="salary", barmode="group", color="level",
                                 title='Average salary based on different skills, level')
    skill_sal_fig.update_layout(xaxis_title_text='Skill, level', yaxis_title_text='Average salary')
    skill_sal_fig.update_xaxes(categoryorder="total descending")

    level_sal_fig = px.histogram(skill_level_salary_df, x="level", y="salary", barmode="group", color="skill",
                                 title='Average salary based on different levels, skills')
    level_sal_fig.update_layout(xaxis_title_text='Level, skill', yaxis_title_text='Average salary')
    level_sal_fig.update_xaxes(categoryorder="total descending")

    return salary_fig, skill_sal_fig, level_sal_fig, skills_pop_fig, categories_pop_fig, avg_salary_fig, max_date_dt


if __name__ == "__main__":
    app.run_server(debug=True)
