import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import requests
import pandas as pd
import plotly.express as px

# Initialize Dash app
app = dash.Dash(__name__)

app.layout = html.Div([
    # Top bar
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

    # Main content container
    html.Div([
        # Header
        html.H1("Department Profile", style={'text-align': 'left', 'margin-left': '20px', 'margin-bottom': '20px', 'font-size': '2.5em', 'color': '#54473F'}),

        # Dropdowns
        html.Div([
            html.Div([
                html.Label("Campus:", style={'margin-right': '10px', 'font-weight': 'bold', 'color': '#54473F'}),
                dcc.Dropdown(id='campus-dropdown', options=[], placeholder="Select a campus", style={'width': '300px'})
            ], style={'margin-bottom': '20px'}),

            html.Div([
                html.Label("College:", style={'margin-right': '10px', 'font-weight': 'bold', 'color': '#54473F'}),
                dcc.Dropdown(id='college-dropdown', options=[], placeholder="Select a college", style={'width': '300px'})
            ], style={'margin-bottom': '20px'}),

            html.Div([
                html.Label("Program:", style={'margin-right': '10px', 'font-weight': 'bold', 'color': '#54473F'}),
                dcc.Dropdown(id='program-dropdown', options=[], placeholder="Select a program", style={'width': '300px'})
            ])
        ], style={'margin-left': '20px'}),

        # Visualizations (initially hidden)
        html.Div(id='visualizations', style={'display': 'none'}, children=[
            html.Div([
                dcc.Graph(id='bar-chart'),
            ], style={'margin-bottom': '30px'}),

            html.Div([
                html.Div([
                    dcc.Graph(id='college-piechart'),
                ], style={'flex': 1, 'margin': '20px'}),

                html.Div([
                    dcc.Graph(id='program-piechart'),
                ], style={'flex': 1, 'margin': '20px'})
            ], style={'display': 'flex', 'flex-wrap': 'wrap', 'margin': '20px'}),
        ]),
    ], style={'flex': 1, 'display': 'flex', 'flexDirection': 'column'}),  # This makes sure the main content area expands to fill available space

    # Yellow bottom bar
    html.Div(style={'backgroundColor': '#ffcc00', 'height': '80px', 'width': '100%'})
], style={'display': 'flex', 'flexDirection': 'column', 'minHeight': '100vh'})


# Callbacks to load dropdown options
@app.callback(
    Output('campus-dropdown', 'options'),
    Input('campus-dropdown', 'value')
)
def load_campuses(selected_value):
    response = requests.get("http://127.0.0.1:5000/campuses")
    campuses = response.json()
    return [{'label': campus['camp_name'], 'value': campus['camp_id']} for campus in campuses]

@app.callback(
    Output('college-dropdown', 'options'),
    Input('campus-dropdown', 'value')
)
def load_colleges(selected_campus):
    if not selected_campus:
        return []
    response = requests.get(f"http://127.0.0.1:5000/colleges?campus_id={selected_campus}")
    colleges = response.json()
    return [{'label': college['college_name'], 'value': college['id']} for college in colleges]

@app.callback(
    Output('program-dropdown', 'options'),
    Input('college-dropdown', 'value')
)
def load_programs(selected_college):
    if not selected_college:
        return []
    response = requests.get(f"http://127.0.0.1:5000/programs?college_id={selected_college}")
    programs = response.json()
    return [{'label': program['program_name'], 'value': program['id']} for program in programs]

# Callback to update charts
@app.callback(
    [Output('bar-chart', 'figure'),
     Output('college-piechart', 'figure'),
     Output('program-piechart', 'figure'),
     Output('visualizations', 'style')],
    [Input('campus-dropdown', 'value'),
     Input('college-dropdown', 'value'),
     Input('program-dropdown', 'value')]
)
def update_charts(selected_campus, selected_college, selected_program):
    if not selected_campus:
        return {}, {}, {}, {'display': 'none'}  # Hide charts if no campus is selected

    filters = {'campus_id': selected_campus}
    if selected_college:
        filters['college_id'] = selected_college
    if selected_program:
        filters['program_id'] = selected_program

    try:
        response = requests.get("http://127.0.0.1:5000/researches", params=filters)
        response.raise_for_status()
        researches = response.json()

        if not researches:
            return {}, {}, {}, {'display': 'none'}  # Hide charts if no data is fetched

        df = pd.DataFrame(researches)

        if df.empty or not {'date_of_publication', 'college_name', 'program_name'}.issubset(df.columns):
            return {}, {}, {}, {'display': 'none'}  # Hide charts if data is incomplete

        # Ensure the 'year' column is in the correct format
        df['year'] = pd.to_datetime(df['date_of_publication'], errors='coerce').dt.year

        # Filter data to include only years >= 2007
        df_filtered = df[df['year'] >= 2007]

        # Group by year and count papers for each year
        papers_by_year = df_filtered.groupby('year').size().reset_index(name='Number of Papers')

        # Remove years with no papers
        papers_by_year = papers_by_year[papers_by_year['Number of Papers'] > 0]

        # Create bar chart grouped by year
        bar_chart = px.bar(
            papers_by_year,
            x='year',
            y='Number of Papers',
            title="Number of Papers by Year",
            template='plotly_white'
        ).update_layout(title_x=0.5, title_font_size=20)

        # Pie chart: College distribution
        college_distribution = df['college_name'].value_counts().reset_index()
        college_distribution.columns = ['College Name', 'Number of Papers']
        college_piechart = px.pie(
            college_distribution,
            names='College Name',
            values='Number of Papers',
            title="College Distribution",
            template='plotly_white'
        ).update_layout(title_x=0.5, title_font_size=20).update_traces(textinfo='none', showlegend=True)

        # Pie chart: Program distribution
        program_distribution = df['program_name'].value_counts().reset_index()
        program_distribution.columns = ['Program Name', 'Number of Papers']
        program_piechart = px.pie(
            program_distribution,
            names='Program Name',
            values='Number of Papers',
            title="Program Distribution",
            template='plotly_white'
        ).update_layout(title_x=0.5, title_font_size=20).update_traces(textinfo='none', showlegend=True)

        return bar_chart, college_piechart, program_piechart, {'display': 'block'}  # Show charts after data is fetched
    except requests.exceptions.RequestException as e:
        return {}, {}, {}, {'display': 'none'}  # Hide charts in case of error

if __name__ == '__main__':
    app.run_server(debug=True)
