import streamlit as st
import pandas as pd
import plotly.graph_objs as go

st.set_page_config(layout="wide")

# Загрузка данных
tp_wh_coverage = pd.read_csv('https://raw.githubusercontent.com/bors1n/tp_dash/refs/heads/main/tp_wh_coverage.csv')
div_coverage = pd.read_csv('https://raw.githubusercontent.com/bors1n/tp_dash/refs/heads/main/div_coverage.csv')
dep_coverage = pd.read_csv('https://raw.githubusercontent.com/bors1n/tp_dash/refs/heads/main/dep_coverage.csv')
div_static_metrics = pd.read_csv('https://raw.githubusercontent.com/bors1n/tp_dash/refs/heads/main/div_static_metrics.csv')

# Заголовок
st.title('Макс Ассортимент')

# Список филиалов для выбора
tp_options = sorted(tp_wh_coverage['branch'].unique())

# Функция для графика общей доли по всей сети
def plot_network_coverage():
    df_network = tp_wh_coverage.groupby('date_').agg({'coverage_rate': 'mean'}).reset_index()
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_network['date_'],
        y=df_network['coverage_rate'],
        mode='lines+markers',
        name='Общая доля по сети',
        line=dict(color='green')
    ))
    fig.update_layout(
        xaxis_title='Дата',
        yaxis_title='Доля',
        hovermode='x unified',
        height=400
    )
    return fig

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

col_left, col_right = st.columns([1,1])  # две колонки равной ширины

with col_right:
    selected_tps = st.multiselect(
        'Выберите филиалы',
        options=tp_options,
        default=['Владивосток Некрасовская ТП']
    )

with col_left:
    st.empty()  # пустое место или другой контент

# Верхний ряд с двумя графиками — по выбранным филиалам и по всей сети
col2, col1 = st.columns(2)

with col1:
    st.header('Доля по филиалам')
    st.plotly_chart(plot_tp_line_chart(selected_tps), use_container_width=True)

with col2:
    st.header('Доля по всей сети')
    st.plotly_chart(plot_network_coverage(), use_container_width=True)

# Второй ряд с графиками дивизионов и департаментов
col3, col4 = st.columns(2)

with col3:
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

with col4:
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

