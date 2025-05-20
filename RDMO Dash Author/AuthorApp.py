import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import requests

# Define API base URL
BASE_URL = "http://127.0.0.1:5000"

# Fetch data from API
authors = requests.get(f"{BASE_URL}/authors").json()
research_authors = requests.get(f"{BASE_URL}/research_authors").json()
research_data = requests.get(f"{BASE_URL}/researches").json()
campuses = requests.get(f"{BASE_URL}/campuses").json()
colleges = requests.get(f"{BASE_URL}/colleges").json()
programs = requests.get(f"{BASE_URL}/programs").json()

# Convert JSON to DataFrames
df_authors = pd.DataFrame(authors)
df_research_authors = pd.DataFrame(research_authors)
df_research_data = pd.DataFrame(research_data)
df_campuses = pd.DataFrame(campuses)
df_colleges = pd.DataFrame(colleges)
df_programs = pd.DataFrame(programs)

# Merge data
df_authors = df_authors.merge(df_campuses, left_on='campus_id', right_on='camp_id', suffixes=('', '_campus'))
df_research_authors = df_research_authors.merge(df_authors, left_on='author_id', right_on='id', suffixes=('', '_author'))
df_research_authors = df_research_authors.merge(df_research_data, left_on='research_id', right_on='id', suffixes=('', '_research'))
df_research_authors = df_research_authors.merge(df_colleges, left_on='college_id', right_on='id', suffixes=('', '_college'))
df_research_authors = df_research_authors.merge(df_programs, left_on='program_id', right_on='id', suffixes=('', '_program'))

# Drop duplicate ID columns
df_research_authors.drop(columns=['id', 'id_research', 'id_author', 'id_college', 'id_program', 'id_campus'], inplace=True, errors='ignore')
df_final = df_research_authors.dropna(subset=['name', 'college_name', 'program_name', 'date_of_publication', 'title_of_research'])

df_final['name'] = df_final['name'].astype(str).str.split(r'[\n,]')
df_final = df_final.explode('name').reset_index(drop=True)
df_final['name'] = df_final['name'].str.strip()
df_final['year'] = pd.to_datetime(df_final['date_of_publication'], errors='coerce').dt.year.dropna().astype(int)
df_final['school_year'] = df_final['year'].apply(lambda y: f"SY {y}-{y + 1}")

df = df_final.copy()
df['School Year'] = df['school_year']

# Initialize Dash app
app = dash.Dash(__name__)
available_school_years = sorted(df['School Year'].dropna().unique())

app.layout = html.Div([
    # Content
    html.Div([
        html.Div([
            html.Img(src="/assets/TIPLogo.jpg", style={
                'height': '80px',
                'margin-left': '20px',
                'margin-top': '10px'
            }),
            html.Div(style={
                'margin-left': '30px',
                'display': 'flex',
                'flexDirection': 'column',
                'justify-content': 'center'
            }, children=[
                html.Span("Academic Research Unit", style={'font-size': '24px', 'color': 'white'}),
                html.Span("Technological Institute of the Philippines", style={'font-size': '16px', 'color': 'white', 'margin-top': '5px'})
            ])
        ], style={'backgroundColor': '#333333', 'height': '140px', 'display': 'flex', 'align-items': 'center'}),
        
        html.H1("Author Profile Dashboard", style={'color': '#54473F'}),
        
        html.Label("Select Author:"),
        dcc.Dropdown(
            id='author-dropdown',
            options=[{'label': author, 'value': author} for author in sorted(df['name'].dropna().unique())],
            value=None,
            style={'width': '300px'}
        ),

        html.Label("Select School Year Range:"),
        dcc.Dropdown(
            id='start-year-dropdown',
            options=[{'label': sy, 'value': sy} for sy in available_school_years],
            value=available_school_years[0],
            style={'width': '300px'}
        ),
        dcc.Dropdown(
            id='end-year-dropdown',
            options=[{'label': sy, 'value': sy} for sy in available_school_years],
            value=available_school_years[-1],
            style={'width': '300px'}
        ),

        html.Div(id='visualization-container', children=[
            html.Div(id='author-credentials', style={'font-weight': 'bold'}),
            dcc.Graph(id='papers-by-year'),
            dcc.Graph(id='college-distribution'),
            dcc.Graph(id='program-distribution')
        ], style={'display': 'none', 'flex': '1'}) 

    ], style={'flex': '1', 'padding': '20px'}), 

    # Bottom Bar
    html.Div(style={
        'backgroundColor': '#ffcc00',
        'height': '80px',
        'width': '100%',
        'position': 'fixed',
        'bottom': '0',
        'left': '0'
    })
], style={'display': 'flex', 'flexDirection': 'column', 'minHeight': '100vh'})


@app.callback(
    [Output('author-credentials', 'children'),
     Output('papers-by-year', 'figure'),
     Output('college-distribution', 'figure'),
     Output('program-distribution', 'figure'),
     Output('visualization-container', 'style')],
    [Input('author-dropdown', 'value'),
     Input('start-year-dropdown', 'value'),
     Input('end-year-dropdown', 'value')]
)
def update_graphs(selected_author, start_sy, end_sy):
    if not selected_author:
        return "", {}, {}, {}, {'display': 'none'}
    
    filtered_df = df[(df['name'] == selected_author) &
                     (df['School Year'] >= start_sy) &
                     (df['School Year'] <= end_sy)]
    
    author_info = f"Displaying information for: {selected_author}"
    papers_by_year = filtered_df.groupby('School Year')['title_of_research'].count().reset_index()
    fig1 = px.bar(papers_by_year, x='School Year', y='title_of_research', title=f'Number of Papers by {selected_author}', text_auto=True)
    
    college_distribution = filtered_df['college_name'].value_counts().reset_index()
    college_distribution.columns = ['College', 'Count']
    fig2 = px.pie(college_distribution, names='College', values='Count', title='College Distribution')
    
    program_distribution = filtered_df['program_name'].value_counts().reset_index()
    program_distribution.columns = ['Program', 'Count']
    fig3 = px.pie(program_distribution, names='Program', values='Count', title='Program Distribution')
    
    return author_info, fig1, fig2, fig3, {'display': 'block'}

if __name__ == '__main__':
    app.run_server(debug=True)