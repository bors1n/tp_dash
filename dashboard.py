import pandas as pd
import dash
from dash import dcc, html, Input, Output
import plotly.graph_objs as go
from flib import Db

tp_wh_coverage = pd.read_csv('tp_wh_coverage.csv')
div_coverage = pd.read_csv('div_coverage.csv')
dep_coverage = pd.read_csv('dep_coverage.csv')
div_static_metrics = pd.read_csv('div_static_metrics.csv')

app = dash.Dash(__name__)

tp_options = [{'label': tp, 'value': tp} for tp in sorted(tp_wh_coverage['branch'].unique())]

metrics = ['mean', 'median', 'min', 'max']

app.layout = html.Div([
    html.H2('Доля по филиалам'),

    dcc.Dropdown(
        id='tp-dropdown',
        options=tp_options,
        value=['Владивосток Некрасовская ТП'],
        multi=True,
        clearable=False
    ),

    dcc.Graph(id='tp-line-chart', style={'width': '100%', 'height': '400px'}),

    html.Div([
        html.Div([
            html.H3('Доля по дивизионам'),
            dcc.Graph(id='div-line-chart')
        ], style={'width': '49%', 'display': 'inline-block', 'verticalAlign': 'top'}),

        html.Div([
            html.H3('Доля по департаментам'),
            dcc.Graph(id='dep-line-chart')
        ], style={'width': '49%', 'display': 'inline-block', 'verticalAlign': 'top'}),
    ]),

    html.H3('Статистика за месяц'),

    dcc.RadioItems(
        id='metric-radio',
        options=[{'label': m.capitalize(), 'value': m} for m in metrics],
        value='mean',
        labelStyle={'display': 'inline-block', 'marginRight': '15px'}
    ),

    dcc.Graph(id='boxplot-chart')
])


@app.callback(
    Output('tp-line-chart', 'figure'),
    Input('tp-dropdown', 'value')
)
def update_tp_chart(selected_tps):
    filtered = tp_wh_coverage[tp_wh_coverage['branch'].isin(selected_tps)]
    fig = go.Figure()
    for tp in selected_tps:
        df_tp = filtered[filtered['branch'] == tp]
        fig.add_trace(go.Scatter(
            x=df_tp['date_'],
            y=df_tp['coverage_rate'],
            mode='lines+markers',
            name=tp
        ))
    fig.update_layout(
        xaxis_title='Дата',
        yaxis_title='Доля',
        hovermode='x unified'
    )
    return fig


@app.callback(
    Output('div-line-chart', 'figure'),
    Input('tp-dropdown', 'value')
)
def update_div_chart(_):
    fig = go.Figure()
    for div in div_coverage['div'].unique():
        df_div = div_coverage[div_coverage['div'] == div]
        fig.add_trace(go.Scatter(
            x=df_div['date_'],
            y=df_div['coverage_rate'],
            mode='lines+markers',
            name=div
        ))
    fig.update_layout(
        xaxis_title='Дата',
        yaxis_title='Доля',
        hovermode='x unified'
    )
    return fig


@app.callback(
    Output('dep-line-chart', 'figure'),
    Input('tp-dropdown', 'value')
)
def update_dep_chart(_):
    fig = go.Figure()
    for dep in dep_coverage['dep'].unique():
        df_dep = dep_coverage[dep_coverage['dep'] == dep]
        fig.add_trace(go.Scatter(
            x=df_dep['date_'],
            y=df_dep['coverage_rate'],
            mode='lines+markers',
            name=dep
        ))
    fig.update_layout(
        xaxis_title='Дата',
        yaxis_title='Доля',
        hovermode='x unified'
    )
    return fig


def create_coverage_boxplot(div_static_metrics, highlight='mean'):
    fig = go.Figure()

    for i, row in div_static_metrics.iterrows():
        div = row['div_']

        # Собираем значения для boxplot
        values = [
            row.get('sku_tp_min', 0),
            row.get('sku_tp_median', 0),
            row.get('sku_tp_max', 0),
            row.get('sku_tp_mean', 0)
        ]

        fig.add_trace(go.Box(
            y=values,
            name=div,
            boxpoints=False,
            marker=dict(color='lightblue'),
            line=dict(width=1),
            showlegend=False
        ))

        # Добавляем красную точку для выделенной метрики
        highlight_value = row.get(f'sku_tp_{highlight}', None)
        if highlight_value is not None:
            fig.add_trace(go.Scatter(
                x=[div],
                y=[highlight_value],
                mode='markers+text',
                marker=dict(color='red', size=10),
                text=[f"{int(row.get('branch_nunique', 0))} ТП"],
                textposition='top center',
                showlegend=False
            ))

    fig.update_layout(
        yaxis_title='Количество SKU',
        height=500
    )

    return fig


@app.callback(
    Output('boxplot-chart', 'figure'),
    Input('metric-radio', 'value')
)
def update_boxplot(selected_metric):
    return create_coverage_boxplot(div_static_metrics, highlight=selected_metric)


if __name__ == '__main__':
    app.run_server(debug=True)