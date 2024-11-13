import pandas as pd
import plotly.express as px
from dash import Dash, html, dcc, Input, Output, State, callback_context
import dash
import dash_bootstrap_components as dbc

# Simplified category mapping for companies only
COMPANIES = {
    "Best Websites Ever": ["best websites ever"],
    "Best Jewelery": ["best jewelery"],
    "Luxury Clothes": ["luxury clothes"],
    "Best Inc": ["best inc"]
}

def load_and_process_data(csv_path):
    try:
        # Read CSV with specific columns
        df = pd.read_csv(csv_path, 
                        names=['Description', 'Day', 'Type', 'Amount', 'ID'],
                        quotechar='"',
                        encoding='utf-8')
        
        # Basic cleaning
        df = df.apply(lambda x: x.str.strip() if isinstance(x, str) else x)
        df['Day'] = pd.to_numeric(df['Day'])
        df['Amount'] = pd.to_numeric(df['Amount'])
        
        # Add Income/Expense column
        df['IncomeOrExpense'] = df['Amount'].apply(lambda x: 'Income' if x > 0 else 'Expense')
        
        # Make Amount absolute
        df['Amount'] = df['Amount'].abs()
        
        # Add Company column with default 'Other'
        df['Company'] = 'Other'
        
        # Categorize companies
        for company, keywords in COMPANIES.items():
            mask = df['Description'].str.lower().str.contains('|'.join(keywords), case=False)
            df.loc[mask, 'Company'] = company
        
        # Select and reorder final columns
        df = df[['Description', 'Company', 'Day', 'Type', 'Amount', 'IncomeOrExpense']]
        
        return df
        
    except Exception as e:
        print(f"Error loading CSV file: {str(e)}")
        return None

def create_app(df) -> Dash:
    app = Dash(__name__, 
               external_stylesheets=[dbc.themes.BOOTSTRAP],
               title='Financial Analysis')
    
    max_day = df['Day'].max()
    min_day = df['Day'].min()
    all_companies = sorted(df['Company'].unique())
    all_types = sorted(df['Type'].unique())

    # Create filter section
    filter_section = dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.H6("Companies"),
                    dbc.ButtonGroup([
                        dbc.Button("Select All", id="select-all-companies", color="primary", size="sm", className="me-2"),
                        dbc.Button("Unselect All", id="unselect-all-companies", color="primary", size="sm"),
                    ], className="mb-2"),
                    dcc.Checklist(
                        id='company-filter',
                        options=[{'label': " " + comp, 'value': comp} for comp in all_companies],
                        value=all_companies,
                        inline=False,
                        className="ms-2"
                    )
                ], width=6),
                dbc.Col([
                    html.H6("Types"),
                    dbc.ButtonGroup([
                        dbc.Button("Select All", id="select-all-types", color="primary", size="sm", className="me-2"),
                        dbc.Button("Unselect All", id="unselect-all-types", color="primary", size="sm"),
                    ], className="mb-2"),
                    dcc.Checklist(
                        id='type-filter',
                        options=[{'label': " " + type_, 'value': type_} for type_ in all_types],
                        value=all_types,
                        inline=False,
                        className="ms-2"
                    )
                ], width=6)
            ])
        ])
    ], className="mb-4")

    app.layout = dbc.Container([
        dbc.Row([
            dbc.Col(html.H1("Financial Dashboard", className="text-center my-4"))
        ]),
        
        dbc.Row([
            dbc.Col([
                dbc.ButtonGroup([
                    dbc.Button("Last Day", id="last-day-button", color="primary", className="me-2"),
                    dbc.Button("Last Week", id="last-week-button", color="primary", className="me-2"),
                    dbc.Button("All Time", id="all-time-button", color="primary"),
                ], className="mb-3")
            ])
        ]),
        
        dbc.Row([
            dbc.Col(filter_section)
        ]),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dcc.RangeSlider(
                            id='day-range-slider',
                            min=min_day,
                            max=max_day,
                            value=[min_day, max_day],
                            marks={i: str(i) for i in range(min_day, max_day + 1, 5)},
                            step=1
                        )
                    ])
                ], className="mb-4")
            ])
        ]),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(id='overall-graph')
                    ])
                ])
            ])
        ], className="mb-4"),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(id='company-graph')
                    ])
                ])
            ])
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(id='company-pie')
                    ])
                ])
            ], width=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(id='type-pie')
                    ])
                ])
            ], width=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(id='income-company-pie')
                    ])
                ])
            ], width=4)
        ])
    ], fluid=True)
    
    @app.callback(
        Output('company-filter', 'value'),
        [Input('select-all-companies', 'n_clicks'),
         Input('unselect-all-companies', 'n_clicks')],
        [State('company-filter', 'options')],
        prevent_initial_call=True
    )
    def update_company_selection(select_clicks, unselect_clicks, options):
        ctx = callback_context
        if not ctx.triggered:
            raise dash.exceptions.PreventUpdate
            
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if button_id == "select-all-companies":
            return [option['value'] for option in options]
        else:
            return []

    @app.callback(
        Output('type-filter', 'value'),
        [Input('select-all-types', 'n_clicks'),
         Input('unselect-all-types', 'n_clicks')],
        [State('type-filter', 'options')],
        prevent_initial_call=True
    )
    def update_type_selection(select_clicks, unselect_clicks, options):
        ctx = callback_context
        if not ctx.triggered:
            raise dash.exceptions.PreventUpdate
            
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if button_id == "select-all-types":
            return [option['value'] for option in options]
        else:
            return []

    @app.callback(
        Output('day-range-slider', 'value'),
        [Input('last-day-button', 'n_clicks'),
         Input('last-week-button', 'n_clicks'),
         Input('all-time-button', 'n_clicks')],
        prevent_initial_call=True
    )
    def update_range_slider(*args):
        ctx = callback_context
        if not ctx.triggered:
            return [min_day, max_day]
        
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        if button_id == 'last-day-button':
            return [max_day - 1, max_day - 1]
        elif button_id == 'last-week-button':
            return [max(min_day, max_day - 7), max_day]
        else:  # all-time-button
            return [min_day, max_day]
    
    @app.callback(
        [Output('overall-graph', 'figure'),
         Output('company-graph', 'figure'),
         Output('company-pie', 'figure'),
         Output('type-pie', 'figure'),
         Output('income-company-pie', 'figure')],
        [Input('day-range-slider', 'value'),
         Input('company-filter', 'value'),
         Input('type-filter', 'value')]
    )
    def update_graphs(day_range, selected_companies, selected_types):
        # Apply filters
        filtered_df = df[
            (df['Day'] >= day_range[0]) & 
            (df['Day'] <= day_range[1]) & 
            (df['Company'].isin(selected_companies)) &
            (df['Type'].isin(selected_types))
        ]
        
        # Overall stacked bar chart by Type
        type_fig = px.bar(
            filtered_df.groupby(['IncomeOrExpense', 'Type'])['Amount'].sum().reset_index(),
            x="IncomeOrExpense",
            y="Amount",
            color="Type",
            barmode="stack",
            title="Income and Expenses by Type"
        )
        type_fig.update_layout(
            margin=dict(t=30, b=0, l=0, r=0),
            height=400
        )

        # Stacked bar chart by Company
        company_fig = px.bar(
            filtered_df.groupby(['IncomeOrExpense', 'Company'])['Amount'].sum().reset_index(),
            x="IncomeOrExpense",
            y="Amount",
            color="Company",
            barmode="stack",
            title="Income and Expenses by Company"
        )
        company_fig.update_layout(
            margin=dict(t=30, b=0, l=0, r=0),
            height=400
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
            height=400
        )
        
        expenses_by_type = filtered_df[filtered_df['IncomeOrExpense'] == 'Expense'].groupby('Type')['Amount'].sum()
        type_pie = px.pie(
            values=expenses_by_type.values,
            names=expenses_by_type.index,
            title='Expenses by Type'
        )
        type_pie.update_layout(
            margin=dict(t=30, b=0, l=0, r=0),
            height=400
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
            height=400
        )
        
        return type_fig, company_fig, company_pie, type_pie, income_company_pie

    return app

if __name__ == '__main__':
    df = load_and_process_data(r"./Transactions.csv")
    app = create_app(df)
    app.run_server(debug=False, port=80, host='0.0.0.0')