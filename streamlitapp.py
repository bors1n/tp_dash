import streamlit as st
import pandas as pd
import plotly.graph_objs as go

st.set_page_config(layout="wide")

# Загрузка данных
tp_wh_coverage = pd.read_csv('МаксАссТП/Дашборд/tp_wh_coverage.csv')
div_coverage = pd.read_csv('МаксАссТП/Дашборд/div_coverage.csv')
dep_coverage = pd.read_csv('МаксАссТП/Дашборд/dep_coverage.csv')
div_static_metrics = pd.read_csv('МаксАссТП/Дашборд/div_static_metrics.csv')


# Заголовок
st.title('Доля по филиалам')

# Список филиалов для выбора
tp_options = sorted(tp_wh_coverage['branch'].unique())
selected_tps = st.multiselect(
    'Выберите филиалы',
    options=tp_options,
    default=['Владивосток Некрасовская ТП']
)

# Функция для графика по филиалам
def plot_tp_line_chart(selected_tps):
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
        hovermode='x unified',
        height=400
    )
    return fig

st.plotly_chart(plot_tp_line_chart(selected_tps), use_container_width=True)

# Блок с двумя графиками — дивизионы и департаменты
col1, col2 = st.columns(2)

with col1:
    st.header('Доля по дивизионам')
    fig_div = go.Figure()
    for div in div_coverage['div'].unique():
        df_div = div_coverage[div_coverage['div'] == div]
        fig_div.add_trace(go.Scatter(
            x=df_div['date_'],
            y=df_div['coverage_rate'],
            mode='lines+markers',
            name=div
        ))
    fig_div.update_layout(
        xaxis_title='Дата',
        yaxis_title='Доля',
        hovermode='x unified',
        height=400
    )
    st.plotly_chart(fig_div, use_container_width=True)

with col2:
    st.header('Доля по департаментам')
    fig_dep = go.Figure()
    for dep in dep_coverage['dep'].unique():
        df_dep = dep_coverage[dep_coverage['dep'] == dep]
        fig_dep.add_trace(go.Scatter(
            x=df_dep['date_'],
            y=df_dep['coverage_rate'],
            mode='lines+markers',
            name=dep
        ))
    fig_dep.update_layout(
        xaxis_title='Дата',
        yaxis_title='Доля',
        hovermode='x unified',
        height=400
    )
    st.plotly_chart(fig_dep, use_container_width=True)

# Статистика за месяц
st.header('Статистика за месяц')

metrics = ['mean', 'median', 'min', 'max']
selected_metric = st.radio(
    'Выберите метрику',
    options=metrics,
    index=0,
    format_func=lambda x: x.capitalize(),
    horizontal=True
)

# Функция для boxplot
def create_coverage_boxplot(div_static_metrics, highlight='mean'):
    fig = go.Figure()

    for i, row in div_static_metrics.iterrows():
        div = row['div_']

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

st.plotly_chart(create_coverage_boxplot(div_static_metrics, highlight=selected_metric), use_container_width=True)
