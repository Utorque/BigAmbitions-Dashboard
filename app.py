import pandas as pd
import plotly.express as px
from dash import Dash, html, dcc, Input, Output, State, no_update, callback_context
import dash
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import base64
import io
import re

# Sidebar styling
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "300px",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
    "overflow-y": "auto",
}

CONTENT_STYLE = {
    "margin-left": "320px",
    "padding": "2rem 1rem",
}

def get_companies(df):
    """
    Extract company names and return a dictionary mapping company names to their lowercase variants.
    """
    # Get revenue-generating companies first
    revenue_companies = set()
    revenue_entries = df[
        (df['Amount'] > 0) &
        (df['Description'].str.contains('Revenue'))
    ]
    for description in revenue_entries['Description']:
        company_name = description.split(' Revenue')[0].strip()
        if company_name:
            revenue_companies.add(company_name)
    
    # Find headquarters from wage descriptions
    headquarters = set()
    wage_entries = df[df['Description'].str.contains('Daily Wage')]
    
    for description in wage_entries['Description']:
        match = re.search(r'\((.*?) Daily Wage\)', description)
        if match:
            company = match.group(1).strip()
            if company == 'Best Inc':
                headquarters.add(company)
    
    # Combine all companies
    all_companies = revenue_companies.union(headquarters)
    
    # Create the new dictionary format
    return {
        company: [company.lower()]
        for company in all_companies
    }

def create_app() -> Dash:
    app = Dash(__name__, 
               external_stylesheets=[dbc.themes.BOOTSTRAP],
               title='Big Ambitions Dashboard')
    
    app._favicon = "favicon.ico"
    
    # File upload component styling
    upload_style = {
        'width': '100%',
        'height': '60px',
        'lineHeight': '20px',
        'borderWidth': '1px',
        'borderStyle': 'dashed',
        'borderRadius': '5px',
        'textAlign': 'center',
        'padding-top': '7px',
        'backgroundColor': '#fafafa'
    }

    # Create sidebar
    sidebar = html.Div([
        html.H2("Big Ambitions Dashboard", className="display-6 mb-4"),
        
        # Add upload component
        dcc.Upload(
            id='upload-data',
            children=html.Div([
                'Drag and Drop or Select Transactions.csv',
                html.A('')
            ]),
            style=upload_style,
            multiple=False
        ),
        html.Div([
            html.P(id='upload-status', className="mb-3", style={'margin': '0', 'padding': '0'}),
            html.Hr(),
            html.P("Made with ❤️ by Utorque", className="text-secondary"),
            html.A(
                html.Div([
                    html.I(className="fab fa-github me-2"),  # GitHub icon
                    "View on GitHub"
                ], className="d-flex align-items-center"),
                href="https://github.com/Utorque/BigAmbitions-Dashboard/",
                target="_blank",
                className="btn btn-outline-dark mb-2 w-100"
            ),
            # html.A(
            #     html.Div([
            #         html.I(className="fab fa-paypal me-2"),  # PayPal icon
            #         "Support me on PayPal :)"
            #     ], className="d-flex align-items-center"),
            #     href="https://www.paypal.com/paypalme/ThibBart",
            #     target="_blank",
            #     className="btn btn-outline-primary w-100"
            # ),
            html.Hr()
        ], className="mt-auto p-3"),  # mt-auto will push it to bottom if in a flex container
        
        
        # Controls section - initially hidden
        html.Div(id='sidebar-controls', style={'display': 'none'}, children=[
            html.H6("Time Range", className="mt-4"),
            dbc.ButtonGroup([
                dbc.Button("Last Day", id="last-day-button", color="primary", size="sm", className="me-1"),
                dbc.Button("Last Week", id="last-week-button", color="primary", size="sm", className="me-1"),
                dbc.Button("All Time", id="all-time-button", color="primary", size="sm"),
            ], className="mb-3 d-flex"),
            
            dbc.Card([
                dbc.CardBody([
                    dcc.RangeSlider(
                        id='day-range-slider',
                        min=0,
                        max=1,
                        value=[0, 1],
                        marks={},
                        step=1
                    )
                ])
            ], className="mb-4"),
            
            html.H6("Companies"),
            dbc.ButtonGroup([
                dbc.Button("Select All", id="select-all-companies", color="primary", size="sm", className="me-1"),
                dbc.Button("Unselect All", id="unselect-all-companies", color="primary", size="sm"),
            ], className="mb-2 d-flex"),
            dcc.Checklist(
                id='company-filter',
                options=[],
                value=[],
                className="mb-4",
                labelStyle={'display': 'block', 'margin-bottom': '0.1rem'}
            ),
            
            html.H6("Types"),
            dbc.ButtonGroup([
                dbc.Button("Select All", id="select-all-types", color="primary", size="sm", className="me-1"),
                dbc.Button("Unselect All", id="unselect-all-types", color="primary", size="sm"),
            ], className="mb-2 d-flex"),
            dcc.Checklist(
                id='type-filter',
                options=[],
                value=[],
                className="mb-4",
                labelStyle={'display': 'block', 'margin-bottom': '0.1rem'}
            ),
        ]),
            html.A("Ambition icons created by Karyative - Flaticon", href="https://www.flaticon.com/free-icons/ambition", target="_blank", className="text-secondary"),
    ], style=SIDEBAR_STYLE)

    # Create main content
    content = html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(id='overall-graph', config={"displayModeBar": False})
                    ])
                ])
            ]),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(id='company-graph', config={"displayModeBar": False})
                    ])
                ])
            ])
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(id='company-pie', config={"displayModeBar": False})
                    ])
                ])
            ], width=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(id='type-pie', config={"displayModeBar": False})
                    ])
                ])
            ], width=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(id='income-company-pie', config={"displayModeBar": False})
                    ])
                ])
            ], width=4)
        ])
    ], style=CONTENT_STYLE)

    app.layout = html.Div([
        dcc.Store(id='stored-data'),  # Store for the processed DataFrame
        sidebar,
        content
    ])

    @app.callback(
        [Output('overall-graph', 'figure'),
         Output('company-graph', 'figure'),
         Output('company-pie', 'figure'),
         Output('type-pie', 'figure'),
         Output('income-company-pie', 'figure')],
        [Input('stored-data', 'data'),
         Input('day-range-slider', 'value'),
         Input('company-filter', 'value'),
         Input('type-filter', 'value')]
    )
    def update_graphs(json_data, day_range, selected_companies, selected_types):
        if not json_data:
            raise PreventUpdate
            
        df = pd.read_json(io.StringIO(json_data), orient='split')
        
        filtered_df = df[
            (df['Day'] >= day_range[0]) & 
            (df['Day'] <= day_range[1]) & 
            (df['Company'].isin(selected_companies)) &
            (df['Type'].isin(selected_types))
        ]
        
        type_grouped = filtered_df.groupby(['IncomeOrExpense', 'Type'])['Amount'].sum().reset_index()
        # Create a sorting index for each IncomeOrExpense group
        type_grouped['SortOrder'] = type_grouped.groupby('IncomeOrExpense')['Amount'].rank(ascending=False)
        type_grouped = type_grouped.sort_values(['IncomeOrExpense', 'SortOrder'])
        
        type_fig = px.bar(
            type_grouped,
            x="IncomeOrExpense",
            y="Amount",
            color="Type",
            barmode="stack",
            title="Income and Expenses by Type",
            category_orders={"Type": type_grouped['Type'].unique()}
        )
        type_fig.update_layout(
            margin=dict(t=30, b=0, l=0, r=0),
            height=375
        )

        # For Company stacked bar - sort by Amount within each IncomeOrExpense category
        company_grouped = filtered_df.groupby(['IncomeOrExpense', 'Company'])['Amount'].sum().reset_index()
        # Create a sorting index for each IncomeOrExpense group
        company_grouped['SortOrder'] = company_grouped.groupby('IncomeOrExpense')['Amount'].rank(ascending=False)
        company_grouped = company_grouped.sort_values(['IncomeOrExpense', 'SortOrder'])
        
        company_fig = px.bar(
            company_grouped,
            x="IncomeOrExpense",
            y="Amount",
            color="Company",
            barmode="stack",
            title="Income and Expenses by Company",
            category_orders={"Company": company_grouped['Company'].unique()}
        )
        company_fig.update_layout(
            margin=dict(t=30, b=0, l=0, r=0),
            height=375
        )
        
        # Company pie chart (expenses only)
        expenses_by_company = filtered_df[filtered_df['IncomeOrExpense'] == 'Expense'].groupby('Company')['Amount'].sum()
        company_pie = px.pie(
            values=expenses_by_company.values,
            names=expenses_by_company.index,
            title='Expenses by Company'
        )
        company_pie.update_layout(
            margin=dict(t=30, b=0, l=0, r=0),
            height=375
        )
        
        # Type pie chart
        expenses_by_type = filtered_df[filtered_df['IncomeOrExpense'] == 'Expense'].groupby('Type')['Amount'].sum()
        type_pie = px.pie(
            values=expenses_by_type.values,
            names=expenses_by_type.index,
            title='Expenses by Type'
        )
        type_pie.update_layout(
            margin=dict(t=30, b=0, l=0, r=0),
            height=375
        )
        
        # Income by Company pie chart
        income_by_company = filtered_df[filtered_df['IncomeOrExpense'] == 'Income'].groupby('Company')['Amount'].sum()
        income_company_pie = px.pie(
            values=income_by_company.values,
            names=income_by_company.index,
            title='Income by Company'
        )
        income_company_pie.update_layout(
            margin=dict(t=30, b=0, l=0, r=0),
            height=375
        )
        
        return type_fig, company_fig, company_pie, type_pie, income_company_pie

    @app.callback(
        [Output('company-filter', 'value', allow_duplicate=True),
         Output('type-filter', 'value', allow_duplicate=True)],
        [Input('select-all-companies', 'n_clicks'),
         Input('unselect-all-companies', 'n_clicks'),
         Input('select-all-types', 'n_clicks'),
         Input('unselect-all-types', 'n_clicks')],
        [State('company-filter', 'options'),
         State('type-filter', 'options')],
        prevent_initial_call=True
    )
    def update_all_filters(comp_select_clicks, comp_unselect_clicks, 
                         type_select_clicks, type_unselect_clicks,
                         company_options, type_options):
        if not company_options or not type_options:
            raise PreventUpdate
            
        ctx = callback_context
        if not ctx.triggered:
            raise PreventUpdate
            
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        if button_id == "select-all-companies":
            return [option['value'] for option in company_options], dash.no_update
        elif button_id == "unselect-all-companies":
            return [], dash.no_update
        elif button_id == "select-all-types":
            return dash.no_update, [option['value'] for option in type_options]
        else:  # unselect-all-types
            return dash.no_update, []

    @app.callback(
        Output('day-range-slider', 'value', allow_duplicate=True),
        [Input('last-day-button', 'n_clicks'),
         Input('last-week-button', 'n_clicks'),
         Input('all-time-button', 'n_clicks'),
         Input('stored-data', 'data')],
        prevent_initial_call=True
    )
    def update_range_slider(*args):
        if not args[-1]:  # Check if data is loaded (stored-data is not None)
            raise PreventUpdate
            
        ctx = callback_context
        if not ctx.triggered:
            raise PreventUpdate
        
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        df = pd.read_json(io.StringIO(args[-1]), orient='split')
        min_day = df['Day'].min()
        max_day = df['Day'].max()
        
        if button_id == 'last-day-button':
            return [max_day - 1, max_day - 1]
        elif button_id == 'last-week-button':
            return [max(min_day, max_day - 8), max_day - 1]
        else:  # all-time-button
            return [min_day, max_day]

    # The main update_data callback (for file upload) stays the same
    @app.callback(
        [Output('stored-data', 'data'),
         Output('upload-status', 'children'),
         Output('sidebar-controls', 'style'),
         Output('day-range-slider', 'min'),
         Output('day-range-slider', 'max'),
         Output('day-range-slider', 'value'),
         Output('day-range-slider', 'marks'),
         Output('company-filter', 'options'),
         Output('company-filter', 'value'),
         Output('type-filter', 'options'),
         Output('type-filter', 'value')],
        Input('upload-data', 'contents'),
        State('upload-data', 'filename')
    )
    def update_data(contents, filename):
        if contents is None:
            raise PreventUpdate

        if not filename.endswith('.csv'):
            return [None, html.Div('Please upload a CSV file', style={'color': 'red'}),
                   {'display': 'none'}, 0, 1, [0, 1], {}, [], [], [], []]

        try:
            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')),
                           names=['Description', 'Day', 'Type', 'Amount', 'ID'],
                           quotechar='"',
                           encoding='utf-8')
            
            # Process the DataFrame
            df = df.apply(lambda x: x.str.strip() if isinstance(x, str) else x)
            df['Day'] = pd.to_numeric(df['Day'])
            df['Amount'] = pd.to_numeric(df['Amount'])
            df['IncomeOrExpense'] = df['Amount'].apply(lambda x: 'Income' if x > 0 else 'Expense')
            df['Amount'] = df['Amount'].abs()
            df['Company'] = 'Other'
            
            companies_dict = get_companies(df)
            
            for company, keywords in companies_dict.items():
                mask = df['Description'].str.lower().str.contains('|'.join(keywords), case=False)
                df.loc[mask, 'Company'] = company
            
            df = df[['Description', 'Company', 'Day', 'Type', 'Amount', 'IncomeOrExpense']]
            
            # Prepare filter options
            min_day = df['Day'].min()
            max_day = df['Day'].max()
            all_companies = sorted(df['Company'].unique())
            all_types = sorted(df['Type'].unique())
            
            company_options = [{'label': " " + comp, 'value': comp} for comp in all_companies]
            type_options = [{'label': " " + type_, 'value': type_} for type_ in all_types]
            
            marks = {i: str(i) for i in range(min_day, max_day + 1, 5)}
            
            return [
                df.to_json(date_format='iso', orient='split'),
                html.Div('File uploaded successfully!', style={'color': 'green'}),
                {'display': 'block'},
                min_day,
                max_day,
                [min_day, max_day],
                marks,
                company_options,
                all_companies,
                type_options,
                all_types
            ]
            
        except Exception as e:
            return [None, html.Div(f'Error processing file: {str(e)}', style={'color': 'red'}),
                   {'display': 'none'}, 0, 1, [0, 1], {}, [], [], [], []]
    return app

if __name__ == '__main__':
    app = create_app()
    app.run_server(debug=True, port=80, host='0.0.0.0')