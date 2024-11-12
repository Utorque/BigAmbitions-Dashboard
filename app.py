import pandas as pd
import plotly.express as px
from dash import Dash, html, dcc, Input, Output, dash, State, callback_context
import dash_bootstrap_components as dbc

# Previous CATEGORIES dictionary remains the same
CATEGORIES = {
    "expenses_categories": {
        "Rent": ["rent"],
        "Marketing": ["marketing"],
        "Training": ["training"],
        "Daily Wage": ["daily wage", "wage"],
        "Vehicle": ["vehicle"],
        "Delivery": ["delivery"],
        "Purchase": ["purchase"],
        "Import": ["import"],
        "Moving": ["moving"],
        "Recruitment": ["recruitment"],
        "Deposit": ["deposit"]
    },
    "companies": {
        "Best Websites Ever": ["best websites ever"],
        "Best Jewelery": ["best jewelery"],
        "Luxury Clothes": ["luxury clothes"],
        "Best Inc": ["best inc"]
    }
}

# Previous load_and_process_data function remains the same
def load_and_process_data(csv_path):
    try:
        df = pd.read_csv(csv_path, 
                        names=['Description', 'Day', 'Type', 'Amount', 'ID'],
                        quotechar='"',
                        encoding='utf-8')
        
        df = df.apply(lambda x: x.str.strip() if isinstance(x, str) else x)
        df['Day'] = pd.to_numeric(df['Day'])
        df['Amount'] = pd.to_numeric(df['Amount'])
        df['is_expense'] = df['Amount'] < 0
        df['abs_amount'] = df['Amount'].abs()
        df['expense_category'] = 'Other'
        df['company'] = 'Other'
        
        df["Description"] = df["Description"].str.replace('(', '')
        
        for category, keywords in CATEGORIES['expenses_categories'].items():
            mask = df['Description'].str.lower().str.contains('|'.join(keywords), case=False)
            df.loc[mask, 'expense_category'] = category
        
        for company, keywords in CATEGORIES['companies'].items():
            mask = df['Description'].str.lower().str.contains('|'.join(keywords), case=False)
            df.loc[mask, 'company'] = company
        
        return df
        
    except Exception as e:
        print(f"Error loading CSV file: {str(e)}")
        return None

def create_app(df):
    app = Dash(__name__, 
               external_stylesheets=[dbc.themes.BOOTSTRAP],
               title='BC Analysis')
    
    max_day = df['Day'].max()
    min_day = df['Day'].min()

    # Get all unique categories and companies
    all_categories = sorted(list(CATEGORIES['expenses_categories'].keys()) + ['Other'])
    all_companies = sorted(list(CATEGORIES['companies'].keys()) + ['Other'])

    # Create filter section
    filter_section = dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.H6("Expense Categories"),
                    dbc.ButtonGroup([
                        dbc.Button("Select All", id="select-all-categories", color="primary", size="sm", className="me-2"),
                        dbc.Button("Unselect All", id="unselect-all-categories", color="primary", size="sm"),
                    ], className="mb-2"),
                    dcc.Checklist(
                        id='category-filter',
                        options=[{'label': " " + cat, 'value': cat} for cat in all_categories],
                        value=all_categories,
                        inline=False,
                        className="ms-2"
                    )
                ], md=6),
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
                ], md=6),
            ])
        ])
    ], className="mb-4")

    app.layout = dbc.Container([
        dbc.Row([
            dbc.Col(html.H1("Financial Dashboard", className="text-center my-4"))
        ]),
        
        dbc.Row([
            dbc.Col(filter_section)
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
                        dcc.Graph(id='overall-graph-by-company')
                    ])
                ])
            ])
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(id='expenses-category-pie')
                    ])
                ])
            ], md=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(id='expenses-company-pie')
                    ])
                ])
            ], md=6)
        ])
    ], fluid=True)
    
    @app.callback(
        Output('category-filter', 'value'),
        [Input('select-all-categories', 'n_clicks'),
        Input('unselect-all-categories', 'n_clicks')],
        [State('category-filter', 'options')],
        prevent_initial_call=True
    )
    def update_category_selection(select_clicks, unselect_clicks, options):
        if not callback_context.triggered:
            raise dash.exceptions.PreventUpdate
                
        button_id = callback_context.triggered[0]['prop_id'].split('.')[0]
        if button_id == "select-all-categories":
            return [option['value'] for option in options]
        else:
            return []

    @app.callback(
        Output('company-filter', 'value'),
        [Input('select-all-companies', 'n_clicks'),
        Input('unselect-all-companies', 'n_clicks')],
        [State('company-filter', 'options')],
        prevent_initial_call=True
    )
    def update_company_selection(select_clicks, unselect_clicks, options):
        if not callback_context.triggered:
            raise dash.exceptions.PreventUpdate
                
        button_id = callback_context.triggered[0]['prop_id'].split('.')[0]
        if button_id == "select-all-companies":
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
        if not callback_context.triggered:
            return [min_day, max_day]
        
        button_id = callback_context.triggered[0]['prop_id'].split('.')[0]
        
        if button_id == 'last-day-button':
            return [max_day - 1, max_day - 1]
        elif button_id == 'last-week-button':
            return [max(min_day, max_day - 8), max_day - 1]
        else:  # all-time-button
            return [min_day, max_day]
    
    @app.callback(
        [Output('overall-graph', 'figure'),
         Output('overall-graph-by-company', 'figure'),
         Output('expenses-category-pie', 'figure'),
         Output('expenses-company-pie', 'figure')],
        [Input('day-range-slider', 'value'),
         Input('category-filter', 'value'),
         Input('company-filter', 'value')]
    )
    def update_graphs(day_range, selected_categories, selected_companies):
        # Apply date filter
        filtered_df = df[(df['Day'] >= day_range[0]) & (df['Day'] <= day_range[1])]
        
        # Apply category and company filters
        category_mask = filtered_df['expense_category'].isin(selected_categories)
        company_mask = filtered_df['company'].isin(selected_companies)
        filtered_df = filtered_df[category_mask & company_mask]
        
        # Overall stacked bar chart by Type
        income_expense_df = filtered_df.loc[:,["Type","Amount"]].groupby(["Type"]).sum().reset_index()
        income_expense_df["IncomeOrExpense"] = income_expense_df["Amount"].apply(lambda x: "Income" if x > 0 else "Expense")
        income_expense_df["Amount"] = income_expense_df["Amount"].abs()
        
        overall_fig = px.bar(
            income_expense_df, 
            x="IncomeOrExpense", 
            y="Amount", 
            color="Type", 
            barmode="stack",
            title="Income and Expenses by Type"
        )
        overall_fig.update_layout(
            margin=dict(t=30, b=0, l=0, r=0),
            height=400
        )

        # Overall stacked bar chart by Company
        company_df = filtered_df.loc[:,["company","Amount"]].groupby(["company"]).sum().reset_index()
        company_df["IncomeOrExpense"] = company_df["Amount"].apply(lambda x: "Income" if x > 0 else "Expense")
        company_df["Amount"] = company_df["Amount"].abs()
        
        company_fig = px.bar(
            company_df, 
            x="IncomeOrExpense", 
            y="Amount", 
            color="company", 
            barmode="stack",
            title="Income and Expenses by Company"
        )
        company_fig.update_layout(
            margin=dict(t=30, b=0, l=0, r=0),
            height=400
        )
        
        # Expenses by category pie chart
        expenses_by_category = filtered_df[filtered_df['Amount'] < 0].groupby('expense_category')['abs_amount'].sum()
        category_pie = px.pie(
            values=expenses_by_category.values,
            names=expenses_by_category.index,
            title='Expenses by Category'
        )
        category_pie.update_layout(
            margin=dict(t=30, b=0, l=0, r=0),
            height=400
        )
        
        # Expenses by company pie chart
        expenses_by_company = filtered_df[filtered_df['Amount'] < 0].groupby('company')['abs_amount'].sum()
        company_pie = px.pie(
            values=expenses_by_company.values,
            names=expenses_by_company.index,
            title='Expenses by Company'
        )
        company_pie.update_layout(
            margin=dict(t=30, b=0, l=0, r=0),
            height=400
        )
        
        return overall_fig, company_fig, category_pie, company_pie

    return app

if __name__ == '__main__':
    df = load_and_process_data(r"C:\Users\Thibault\AppData\LocalLow\Hovgaard Games\Big Ambitions\SaveGames\EA 0.6\7BT1vEwZVEGXpXoAL250wQ==\Transactions.csv")
    app = create_app(df)
    app.run_server(debug=True)