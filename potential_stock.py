import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide")

# Загрузка данных
@st.cache_data
def load_data():
    rrc_table = pd.read_csv('rrc_table.csv').dropna()
    tp_stock = pd.read_csv('tp_stock.csv').dropna()
    return rrc_table, tp_stock

rrc_table, tp_stock = load_data()

st.title("Сравнение ассортимента: РРЦ vs Технопоинты")

# --- САЙДБАР: ФИЛЬТРЫ ---
st.sidebar.header("🔎 Фильтры")

# РРЦ и дивизион
selected_div = st.sidebar.multiselect("Дивизион", sorted(rrc_table['div'].unique()))
selected_rrc = st.sidebar.multiselect("РРЦ (Склад)", sorted(rrc_table['rrc_name'].unique()))

# Статусы
federal_status_filter = st.sidebar.multiselect(
    "Федеральный статус", sorted(rrc_table['federal_status_name'].unique()))
life_cycle_filter = st.sidebar.multiselect(
    "Статус жизненного цикла", sorted(rrc_table['life_cycle_status_name'].unique()))
purchase_status_filter = st.sidebar.multiselect(
    "Статус закупа", sorted(rrc_table['purchase_status_name'].unique()))
top_category_filter = st.sidebar.multiselect(
    "Топовая категория", options=[True, False], format_func=lambda x: "Топ" if x else "Не топ")
access_only = st.sidebar.checkbox("Показывать только доступный остаток", value=False)

# Категории (drill-down)
category1_filter = st.sidebar.multiselect(
    "Категория 1 уровня", sorted(rrc_table['category_1_name'].unique()))
category4_filter = st.sidebar.multiselect(
    "Категория 4 уровня", sorted(rrc_table['category_4_name'].unique()))

# --- ФИЛЬТРАЦИЯ ДАННЫХ ---
df_filtered = rrc_table.copy()

if selected_div:
    df_filtered = df_filtered[df_filtered['div'].isin(selected_div)]

if selected_rrc:
    df_filtered = df_filtered[df_filtered['rrc_name'].isin(selected_rrc)]

if federal_status_filter:
    df_filtered = df_filtered[df_filtered['federal_status_name'].isin(federal_status_filter)]

if life_cycle_filter:
    df_filtered = df_filtered[df_filtered['life_cycle_status_name'].isin(life_cycle_filter)]

if purchase_status_filter:
    df_filtered = df_filtered[df_filtered['purchase_status_name'].isin(purchase_status_filter)]

if top_category_filter:
    df_filtered = df_filtered[df_filtered['top_category'].isin(top_category_filter)]

if category1_filter:
    df_filtered = df_filtered[df_filtered['category_1_name'].isin(category1_filter)]

if category4_filter:
    df_filtered = df_filtered[df_filtered['category_4_name'].isin(category4_filter)]

if access_only:
    df_filtered = df_filtered[df_filtered['access'] == True]

# --- АГРЕГАЦИЯ И ПОДГОТОВКА ДАННЫХ ДЛЯ ГРАФИКА ---

# Агрегация по РРЦ с разделением по доступности из отфильтрованных данных
rrc_agg = (
    df_filtered.groupby(['rrc_id', 'rrc_name', 'access'], as_index=False)
    .agg({'product_count': 'sum'})
)

# Агрегация по ТП
tp_agg = (
    tp_stock.groupby(['rrc_id', 'branch'], as_index=False)
    .agg({'product_count_tp': 'sum'})
    .query('product_count_tp > 1000')
)

# Подтягиваем названия РРЦ в tp_agg
rrc_names = df_filtered[['rrc_id', 'rrc_name']].drop_duplicates()
tp_agg = tp_agg.merge(rrc_names, on='rrc_id', how='left')

# Уникальный порядок РРЦ
rrc_order = rrc_names['rrc_name'].unique()

# Компоновка категорий для оси X (РРЦ и их технопоинты)
x_categories = []
for rrc in rrc_order:
    x_categories.append(rrc)
    tps = tp_agg[tp_agg['rrc_name'] == rrc]['branch'].unique()
    for tp in tps:
        x_categories.append(f"{rrc} - {tp}")

# Подготовка данных для stacked bar по РРЦ
y_accessible = []
y_inaccessible = []
for rrc in rrc_order:
    row_accessible = rrc_agg[(rrc_agg['rrc_name'] == rrc) & (rrc_agg['access'] == True)]
    row_inaccessible = rrc_agg[(rrc_agg['rrc_name'] == rrc) & (rrc_agg['access'] == False)]
    y_accessible.append(row_accessible['product_count'].values[0] if not row_accessible.empty else 0)
    y_inaccessible.append(row_inaccessible['product_count'].values[0] if not row_inaccessible.empty else 0)

# --- ПОСТРОЕНИЕ ГРАФИКА ---
fig = go.Figure()

# Недоступный (серый)
fig.add_trace(go.Bar(
    x=rrc_order,
    y=y_inaccessible,
    name='Недоступный',
    marker_color='#bdbdbd',
    text=[str(val) for val in y_inaccessible],
    textposition='inside',
    textfont_color='black',
))

# Доступный (зелёный)
fig.add_trace(go.Bar(
    x=rrc_order,
    y=y_accessible,
    name='Доступный',
    marker_color='#a6d854',
    text=[str(val) for val in y_accessible],
    textposition='inside',
    textfont_color='black',
))

# Бары для технопоинтов (синий)
for rrc in rrc_order:
    tps = tp_agg[tp_agg['rrc_name'] == rrc]
    for _, row in tps.iterrows():
        fig.add_trace(go.Bar(
            x=[f"{rrc} - {row['branch']}"],
            y=[row['product_count_tp']],
            name='Остаток ТП',
            marker_color='#377eb8',
            text=[str(row['product_count_tp'])],
            textposition='outside',
            textfont_color='black',
            showlegend=False,
        ))

# Подписи сверху для сумм по РРЦ
for i, rrc in enumerate(rrc_order):
    total = y_accessible[i] + y_inaccessible[i]
    fig.add_annotation(
        x=rrc,
        y=total + max(total*0.05, 1),
        text=f"<b>Всего: {total} </b>",
        showarrow=False,
        font=dict(size=10, color='black')
    )

fig.update_layout(
    barmode='stack',
    xaxis=dict(
        title='РРЦ и Технопоинты',
        categoryorder='array',
        categoryarray=x_categories,
        tickangle=-45
    ),
    yaxis_title='Количество уникальных товаров',
    legend_title_text='Тип остатков',
    title='      Остаток РРЦ и ТП',
    uniformtext_minsize=8,
    uniformtext_mode='hide'
)

# Корректируем легенду — показываем только одну метку «Остаток ТП»
legend_names_shown = set()
for trace in fig.data:
    if trace.name == 'Остаток ТП':
        if 'Остаток ТП' in legend_names_shown:
            trace.showlegend = False
        else:
            trace.showlegend = True
            legend_names_shown.add('Остаток ТП')

# Отображение графика
st.plotly_chart(fig, use_container_width=True)


# --- ТАБЛИЦА ---
st.write("📋 Сводная таблица данных")
df_cross = (df_filtered.pivot_table(
    index=['rrc_id', 'rrc_name'],
    columns='access',
    values='product_count',
    aggfunc='sum',
    fill_value=0)
    .reset_index()
)
df_cross.columns.name = None
df_cross = df_cross.rename(columns={False: 'Не доступный Остаток РРЦ', True: 'Доступный Остаток РРЦ'})
absolute_numbers = df_cross.merge(tp_agg, on=['rrc_id', 'rrc_name'], how='left')[['rrc_name', 'branch', 'Не доступный Остаток РРЦ', 'Доступный Остаток РРЦ', 'product_count_tp']]
absolute_numbers['Общий остаток РРЦ'] = absolute_numbers['Не доступный Остаток РРЦ'] + absolute_numbers['Доступный Остаток РРЦ']
absolute_numbers = absolute_numbers.rename(columns={'rrc_name': 'РРЦ', 'branch': 'ТП', 'product_count_tp': 'Остаток ТП'})
absolute_numbers = absolute_numbers[['РРЦ', 'ТП', 'Общий остаток РРЦ', 'Доступный Остаток РРЦ', 'Не доступный Остаток РРЦ', 'Остаток ТП']]
st.dataframe(absolute_numbers)