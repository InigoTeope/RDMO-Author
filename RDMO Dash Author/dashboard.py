import dash
from dash import dcc, html, Input, Output
import requests
import pandas as pd
import plotly.express as px

# Define the Flask API base URL
API_BASE_URL = "http://127.0.0.1:5000"  # Update if hosted elsewhere

# Initialize Dash app
app = dash.Dash(__name__)

# Fetch data from Flask API
def fetch_authors():
    response = requests.get(f"{API_BASE_URL}/authors")
    return response.json() if response.status_code == 200 else []

def fetch_research():
    response = requests.get(f"{API_BASE_URL}/researches")
    return response.json() if response.status_code == 200 else []

# Load initial data
authors = fetch_authors()
research_data = fetch_research()

# Convert research data to DataFrame
df_author = pd.DataFrame(research_data)
if not df_author.empty:
    df_author.rename(columns={
        'title': 'Research Title',
        'year': 'School Year',
        'journal_publisher': 'Journal Publisher',
        'indexing': 'Indexing',
        'doi': 'DOI',
        'keywords': 'Keywords'
    }, inplace=True)
    df_author.fillna("Unlabeled", inplace=True)  # Replace NaN values with 'Unlabeled'

else:
    df = pd.DataFrame(columns=['Research Title', 'Faculty Name', 'Program', 'School Year', 'Indexing', 'Journal Publisher', 'DOI', 'Keywords'])

# App layout
app.layout = html.Div([
    # Top bar
    html.Div([
        html.Img(src="/assets/TIPLogo.jpg", style={'height': '80px', 'margin-left': '20px', 'margin-top': '10px'}),
        html.Div(style={'margin-left': '30px', 'display': 'flex', 'flexDirection': 'column', 'justify-content': 'center'}, children=[
            html.Span("Academic Research Unit", style={'font-size': '24px', 'color': 'white'}),
            html.Span("Technological Institute of the Philippines", style={'font-size': '16px', 'color': 'white', 'margin-top': '5px'})
        ])
    ], style={'backgroundColor': '#333333', 'height': '140px', 'display': 'flex', 'align-items': 'center'}),
    
    html.H1("Author Research Visualization", style={'text-align': 'left', 'margin-left': '20px', 'margin-bottom': '20px', 'font-size': '2.5em', 'color': '#54473F'}),
    
    dcc.Dropdown(
        id="author-dropdown",
        options=[{"label": author["name"], "value": author["id"]} for author in authors],
        placeholder="Select an Author",
        style={'width': '50%', 'margin': 'auto'}
    ),
    
    dcc.Graph(id='research-year-chart'),
    dcc.Graph(id='journal-bar-chart'),
    dcc.Graph(id='indexing-piechart'),
    dcc.Graph(id='doi-table'),
    dcc.Graph(id='keyword-bar-chart'),
    
    # Yellow bottom bar
    html.Div(style={'backgroundColor': '#ffcc00', 'height': '80px', 'width': '100%'})
])

# Callbacks
@app.callback(
    [
        Output('research-year-chart', 'figure'),
        Output('journal-bar-chart', 'figure'),
        Output('indexing-piechart', 'figure'),
        Output('doi-table', 'figure'),
        Output('keyword-bar-chart', 'figure')
    ],
    [Input('author-dropdown', 'value')]
)
def update_visuals(author_id):
    if not author_id:
        return px.bar(), px.bar(), px.pie(), px.bar(), px.bar()
    
    author_research = requests.get(f"{API_BASE_URL}/author_research/{author_id}").json()
    df_author = pd.DataFrame(author_research)
    
    if df_author.empty:
        return px.bar(), px.bar(), px.pie(), px.bar(), px.bar()

    df_author.fillna("Unlabeled", inplace=True)  # Replace NaN values with 'Unlabeled'
    
    # Research count per publication year
    fig1 = px.bar(df_author, x='year', title="Research Count by Year of Publication")

    # Research per journal publisher
    fig2 = px.bar(df_author, x='journal_publisher', title="Research Published per Journal")

    # Scopus indexing pie chart
    fig3 = px.pie(df_author, names='indexing', title="Research Indexing Distribution")

    # DOI table
    fig4 = px.bar(df_author, x='doi', y='title', title="DOI per Research")

    # Keywords bar chart
    df_author['keywords'] = df_author['keywords'].apply(lambda x: x.split(',') if isinstance(x, str) else ["Unlabeled"])
    fig5 = px.bar(df_author.explode('keywords'), x='keywords', title="Keywords per Research")

    return fig1, fig2, fig3, fig4, fig5







if __name__ == "__main__":
    app.run_server(debug=True)
