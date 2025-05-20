import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import random

# Load the dataset
data_path = 'C:/Users/akosi/Downloads/Research Database - Quezon City.xlsx'
df = pd.read_excel(data_path)

# Data Cleaning: Remove rows with missing values in relevant columns
df.dropna(subset=['Authors', 'College', 'Program', 'Date of Publication', 'Title of Research'], inplace=True)

# Preprocessing: Split multiple authors into individual entries
df['Authors'] = df['Authors'].astype(str).str.split(r'[\n,]')
df = df.explode('Authors')  # Create a separate row for each author
df['Authors'] = df['Authors'].str.strip()  # Remove any extra whitespace

# Extract the publication year from the 'Date of Publication' column
df['Year'] = pd.to_datetime(df['Date of Publication'], errors='coerce').dt.year
df = df.dropna(subset=['Year'])  # Remove any rows where the 'Year' could not be extracted

# Convert 'Year' column to integer type for proper sorting and display
df['Year'] = df['Year'].astype(int)

# Map publication year to school year
def map_school_year(year):
    return f"SY {year}-{year + 1}"

df['School Year'] = df['Year'].apply(map_school_year)

# Initialize the Dash app
app = dash.Dash(__name__)

# Define the list of available school years
available_school_years = sorted(df['School Year'].unique())

# Define the layout of the app with default colors
app.layout = html.Div([
    html.H1("Author Paper Analysis", style={'text-align': 'center', 'margin-bottom': '20px', 'font-size': '2.5em','color':'#54473F'}),

    # Dropdown for selecting an author
    html.Label("Select Author:", style={'margin-right': '10px', 'font-weight': 'bold','color':'#54473F'}),
    dcc.Dropdown(
        id='author-dropdown',
        options=[{'label': author, 'value': author} for author in sorted(df['Authors'].dropna().unique())],
        value=sorted(df['Authors'].dropna().unique())[0],
        style={'background-color': '#CBD2A4', 'color': '#54473F', 'border': '1px solid black','color':'#54473F'}
    ),

    # Markdown for selecting school year range
    html.Div([
        html.Label("Select School Year Range:", style={'margin-top': '20px', 'margin-right': '10px', 'font-weight': 'bold','color':'#54473F'}),
        dcc.Markdown(id='start-year-markdown', style={'margin-right': '20px'}),
        dcc.Markdown(id='end-year-markdown'),
    ], style={'margin-top': '10px', 'display': 'inline-block'}),

    # Dropdown to select start and end school year
    dcc.Dropdown(
        id='start-year-dropdown',
        options=[{'label': sy, 'value': sy} for sy in available_school_years],
        value=available_school_years[0],
        style={'background-color': '#CBD2A4', 'color': '#54473F', 'border': '1px solid black','color':'#54473F'}
    ),

    dcc.Dropdown(
        id='end-year-dropdown',
        options=[{'label': sy, 'value': sy} for sy in available_school_years],
        value=available_school_years[-1],
        style={'background-color': '#CBD2A4', 'color': '#54473F', 'border': '1px solid black','color':'#54473F'}
    ),

    # Author credentials display
    html.Div(id='author-credentials', style={'margin-top': '20px', 'font-weight': 'bold','color':'#54473F'}),

    # Graphs
    dcc.Graph(id='papers-by-year'),
    dcc.Graph(id='college-distribution'),
    dcc.Graph(id='program-distribution')
], style={'background-color': '#E9EED9', 'padding': '20px','color':'#54473F'})

# Helper function to generate a dictionary of random colors for each unique school year
def generate_year_color_map(school_years):
    unique_years = sorted(school_years.unique())
    colors = ["#"+''.join([random.choice('0123456789ABCDEF') for _ in range(6)]) for _ in unique_years]
    return dict(zip(unique_years, colors))

# Callback to update the markdown labels dynamically
@app.callback(
    [Output('start-year-markdown', 'children'),
     Output('end-year-markdown', 'children')],
    [Input('start-year-dropdown', 'value'),
     Input('end-year-dropdown', 'value')]
)
def update_year_markdown(start_sy, end_sy):
    return f"**Start School Year:** {start_sy}", f"**End School Year:** {end_sy}"

# Callback to update the graphs and author credentials based on the selected author and school year range
@app.callback(
    [Output('author-credentials', 'children'),
     Output('papers-by-year', 'figure'),
     Output('college-distribution', 'figure'),
     Output('program-distribution', 'figure')],
    [Input('author-dropdown', 'value'),
     Input('start-year-dropdown', 'value'),
     Input('end-year-dropdown', 'value')]
)
def update_graphs(selected_author, start_sy, end_sy):
    # Filter data for the selected author and school year range
    filtered_df = df[(df['Authors'] == selected_author) &
                     (df['School Year'] >= start_sy) & (df['School Year'] <= end_sy)]

    # Get all school years in the range
    all_years_in_range = pd.DataFrame({'School Year': pd.Series(available_school_years)[(pd.Series(available_school_years) >= start_sy) & (pd.Series(available_school_years) <= end_sy)]})
    
    # Merge with filtered data to ensure all school years are shown (even if no papers exist)
    papers_by_year = all_years_in_range.merge(
        filtered_df.groupby('School Year')['Title of Research'].apply(list).reset_index(),
        on='School Year', how='left'
    ).fillna({'Title of Research': '', 'Number of Papers': 0})

    papers_by_year['Number of Papers'] = papers_by_year['Title of Research'].apply(len)

    # Displaying author credentials (example)
    author_info = f"Displaying information for author: {selected_author} (Papers from {start_sy} to {end_sy})"

    # Generate a color map for each school year
    year_color_map = generate_year_color_map(papers_by_year['School Year'])

    # Bar chart for the number of papers by school year with hover info for research titles
    fig1 = px.bar(
        papers_by_year,
        x='School Year',
        y='Number of Papers',
        title=f'Number of Papers by {selected_author} Per School Year ({start_sy}-{end_sy})',
        hover_data={'Title of Research': True},
        labels={'Title of Research': 'Research Titles'},
        color='School Year',  # Color bars based on the 'School Year'
        color_discrete_map=year_color_map,  # Assign each year a unique color
        text_auto='.1s'
    )
    fig1.update_layout(
        xaxis=dict(
            tickmode='linear',
            color='black'  # Change tick color to black for better visibility
        ),
        yaxis=dict(color='black'),
        title_font=dict(color='black'),
        paper_bgcolor='#E9EED9',  
        plot_bgcolor='#CBD2A4',   
        showlegend=False  
    )
    fig1.update_traces(hovertemplate='<b>School Year:</b> %{x}<br><b>Number of Papers:</b> %{y}<br><b>Research Titles:</b> %{customdata[0]}')

    # Pie chart for college distribution
    college_distribution = filtered_df['College'].value_counts().reset_index()
    college_distribution.columns = ['College', 'Count']
    fig2 = px.pie(
        college_distribution,
        names='College',
        values='Count',
        title=f'College Distribution for {selected_author}'
    )
    fig2.update_layout(
        title_font=dict(color='black'),
        paper_bgcolor='#E9EED9',  
        plot_bgcolor='#CBD2A4', 
        font=dict(color='black')
    )

    # Pie chart for program distribution
    program_distribution = filtered_df['Program'].value_counts().reset_index()
    program_distribution.columns = ['Program', 'Count']
    fig3 = px.pie(
        program_distribution,
        names='Program',
        values='Count',
        title=f'Program Distribution for {selected_author}'
    )
    fig3.update_layout(
        title_font=dict(color='black'),
        paper_bgcolor='#E9EED9',  
        plot_bgcolor='#CBD2A4', 
        font=dict(color='black')
    )

    return author_info, fig1, fig2, fig3

if __name__ == '__main__':
    app.run_server(debug=True)