import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide")

# Загрузка данных
@st.cache_data
# def load_data():
#     rrc_table = pd.read_csv('https://raw.githubusercontent.com/bors1n/tp_dash/refs/heads/main/rrc_table.csv').dropna()
#     tp_stock = pd.read_csv('https://raw.githubusercontent.com/bors1n/tp_dash/refs/heads/main/tp_stock.csv').dropna()
#     available_tp_stock = pd.read_csv('https://raw.githubusercontent.com/bors1n/tp_dash/refs/heads/main/available_tp_stock.csv').dropna()
#     return rrc_table, tp_stock, available_tp_stock

def load_data():
    rrc_table = pd.read_csv('https://raw.githubusercontent.com/bors1n/tp_dash/main/rrc_table.csv.gz', compression='gzip').dropna()
    tp_stock = pd.read_csv('https://raw.githubusercontent.com/bors1n/tp_dash/main/tp_stock.csv.gz', compression='gzip').dropna()
    available_tp_stock = pd.read_csv('https://raw.githubusercontent.com/bors1n/tp_dash/main/available_tp_stock.csv.gz', compression='gzip').dropna()
    return rrc_table, tp_stock, available_tp_stock

rrc_table, tp_stock, available_tp_stock = load_data()

st.title("Сравнение ассортимента: РРЦ vs ТП - 02.06.2025")

# --- САЙДБАР: ФИЛЬТРЫ ---
st.sidebar.header("Фильтры")

# РРЦ и дивизион
selected_div = st.sidebar.multiselect("Дивизион", sorted(rrc_table['div'].unique()), default="03. див. Западная Сибирь")
selected_rrc = st.sidebar.multiselect("РРЦ", sorted(rrc_table['rrc_name'].unique()))

# Статусы
federal_status_filter = st.sidebar.multiselect(
    "Федеральный статус", sorted(rrc_table['federal_status_name'].unique()))
life_cycle_filter = st.sidebar.multiselect(
    "Статус жизненного цикла", sorted(rrc_table['life_cycle_status_name'].unique()))
purchase_status_filter = st.sidebar.multiselect(
    "Статус закупа", sorted(rrc_table['purchase_status_name'].unique()))
top_category_filter = st.sidebar.multiselect(
    "Топовая категория", options=[True, False], format_func=lambda x: "Топ" if x else "Не топ")

# Категории (drill-down)
category1_filter = st.sidebar.multiselect(
    "Категория 1 уровня", sorted(rrc_table['category_1_name'].unique()))
category4_filter = st.sidebar.multiselect(
    "Категория 4 уровня", sorted(rrc_table['category_4_name'].unique()))

# --- ФИЛЬТРАЦИЯ ДАННЫХ ---
# df_filtered = rrc_table.copy()
available_tp_stock_filtered = available_tp_stock.copy()
tp_stock_filtered = tp_stock.copy()
df_accessible = rrc_table[rrc_table['access'] == True].copy()
df_inaccessible = rrc_table[rrc_table['access'] == False].copy()

if selected_div:
    df_accessible = df_accessible[df_accessible['div'].isin(selected_div)]
    df_inaccessible = df_inaccessible[df_inaccessible['div'].isin(selected_div)]
    available_tp_stock_filtered = available_tp_stock_filtered[available_tp_stock_filtered['div'].isin(selected_div)]

if selected_rrc:
    df_accessible = df_accessible[df_accessible['rrc_name'].isin(selected_rrc)]
    df_inaccessible = df_inaccessible[df_inaccessible['rrc_name'].isin(selected_rrc)]
    available_tp_stock_filtered = available_tp_stock_filtered[available_tp_stock_filtered['rrc_name'].isin(selected_rrc)]

if federal_status_filter:
    df_accessible = df_accessible[df_accessible['federal_status_name'].isin(federal_status_filter)]
    available_tp_stock_filtered = available_tp_stock_filtered[available_tp_stock_filtered['federal_status_name'].isin(federal_status_filter)]

if life_cycle_filter:
    df_accessible = df_accessible[df_accessible['life_cycle_status_name'].isin(life_cycle_filter)]
    available_tp_stock_filtered = available_tp_stock_filtered[available_tp_stock_filtered['life_cycle_status_name'].isin(life_cycle_filter)]

if purchase_status_filter:
    df_accessible = df_accessible[df_accessible['purchase_status_name'].isin(purchase_status_filter)]
    available_tp_stock_filtered = available_tp_stock_filtered[available_tp_stock_filtered['purchase_status_name'].isin(purchase_status_filter)]

if top_category_filter:
    df_accessible = df_accessible[df_accessible['top_category'].isin(top_category_filter)]
    df_inaccessible = df_inaccessible[df_inaccessible['top_category'].isin(top_category_filter)]
    available_tp_stock_filtered = available_tp_stock_filtered[available_tp_stock_filtered['top_category'].isin(top_category_filter)]
    tp_stock_filtered = tp_stock_filtered[tp_stock_filtered['top_category'].isin(top_category_filter)]

if category1_filter:
    df_accessible = df_accessible[df_accessible['category_1_name'].isin(category1_filter)]
    df_inaccessible = df_inaccessible[df_inaccessible['category_1_name'].isin(category1_filter)]
    available_tp_stock_filtered = available_tp_stock_filtered[available_tp_stock_filtered['category_1_name'].isin(category1_filter)]
    tp_stock_filtered = tp_stock_filtered[tp_stock_filtered['category_1_name'].isin(category1_filter)]

if category4_filter:
    df_accessible = df_accessible[df_accessible['category_4_name'].isin(category4_filter)]
    df_inaccessible = df_inaccessible[df_inaccessible['category_4_name'].isin(category4_filter)]
    available_tp_stock_filtered = available_tp_stock_filtered[available_tp_stock_filtered['category_4_name'].isin(category4_filter)]
    tp_stock_filtered = tp_stock_filtered[tp_stock_filtered['category_4_name'].isin(category4_filter)]

df_filtered = pd.concat([df_accessible, df_inaccessible], ignore_index=True)
# --- АГРЕГАЦИЯ И ПОДГОТОВКА ДАННЫХ ДЛЯ ГРАФИКА ---

# Агрегация по РРЦ с разделением по доступности из отфильтрованных данных
rrc_agg = (
    df_filtered.groupby(['rrc_id', 'rrc_name', 'access'], as_index=False)
    .agg({'product_count': 'sum'})
)

# Агрегация по ТП
tp_agg = (
    tp_stock_filtered.groupby(['rrc_id', 'branch'], as_index=False)
    .agg({'product_count_tp': 'sum'})
      # .query('product_count_tp > 1000')
)

# Агрегация доступного асс по ТП
tp_agg_available = (
    available_tp_stock_filtered.groupby(['rrc_id', 'rrc_name', 'branch'], as_index=False)
    .agg({'product_count': 'sum'})
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

    tps_a = tp_agg_available[tp_agg_available['rrc_name'] == rrc]
    for _, row in tps_a.iterrows():
        fig.add_trace(go.Bar(
            x=[f"{rrc} - {row['branch']}"],
            y=[row['product_count']],
            name='Потенциал Наполнения',
            marker_color='#a6d854',
            text=[str(row['product_count'])],
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
    height=600,
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
st.write("Ассортимент")
df_cross = (df_filtered.pivot_table(
    index=['rrc_id', 'rrc_name'],
    columns='access',
    values='product_count',
    aggfunc='sum',
    fill_value=0)
    .reset_index()
            )

# таблица с абсолютными значениями
df_cross.columns.name = None
df_cross = df_cross.rename(columns={False: 'Не доступный Остаток РРЦ', True: 'Доступный Остаток РРЦ'})
absolute_numbers = df_cross.merge(tp_agg, on=['rrc_id', 'rrc_name'], how='left')[['rrc_name', 'rrc_id', 'branch', 'Не доступный Остаток РРЦ', 'Доступный Остаток РРЦ', 'product_count_tp']]
absolute_numbers = absolute_numbers.merge(tp_agg_available, on=['rrc_id', 'rrc_name', 'branch'], how='left')
absolute_numbers['Общий остаток РРЦ'] = absolute_numbers['Не доступный Остаток РРЦ'] + absolute_numbers['Доступный Остаток РРЦ']
absolute_numbers = absolute_numbers.rename(columns={'rrc_name': 'РРЦ', 'branch': 'ТП', 'product_count_tp': 'Остаток ТП', 'product_count': 'Потенциал Наполнения'})
absolute_numbers = absolute_numbers[['РРЦ', 'ТП', 'Общий остаток РРЦ', 'Доступный Остаток РРЦ', 'Не доступный Остаток РРЦ', 'Остаток ТП', 'Потенциал Наполнения']]
absolute_numbers = absolute_numbers[absolute_numbers['ТП'].isnull() == False]

if absolute_numbers.empty:
    st.write('Нет данных')
else:
    st.dataframe(absolute_numbers)


rrc_stock_2_columns = df_filtered.pivot_table(
                                            index=['div', 'rrc_id', 'rrc_name', 'category_1_name', 'category_4_name', 'category_4_id'],
                                            columns=['access'],
                                            values=['product_count'],
                                            aggfunc='sum',
                                            fill_value=0
                                        )\
                                .reset_index()
rrc_stock_2_columns.columns.name = None
rrc_stock_2_columns = rrc_stock_2_columns.rename(columns={False: 'access_false', True: 'asccess_true'})
rrc_stock_2_columns.columns = ['_'.join(filter(None, col)).strip() for col in rrc_stock_2_columns.columns.values]
rrc_stock_2_columns['full_stock'] = rrc_stock_2_columns['product_count_access_false'] + rrc_stock_2_columns[
    'product_count_access_false']

# собираем остаток РРЦ + Остаток ТП
t_tp_stock = tp_stock_filtered[['rrc_id', 'branch', 'branch_id', 'category_4_id', 'product_count_tp']].copy()
rrc_stock_tp_stock = rrc_stock_2_columns.merge(t_tp_stock, on=['rrc_id', 'category_4_id'], how='left')\
                                        .fillna({"branch": 'Отсуствует', 'branch_id': '00000000-0000-0000-0000-000000000000', 'product_count_tp': 0})

#суммируем потенциальный остаток
tp_agg_available = (
    available_tp_stock_filtered.groupby(['rrc_id', 'rrc_name', 'branch', 'branch_id', 'category_4_id'], as_index=False)
    .agg({'product_count': 'sum'})[['rrc_id', 'branch_id', 'category_4_id', 'product_count']]
)

# добавляем потенциальный остаток ТП
df_full_table = rrc_stock_tp_stock.merge(tp_agg_available, on=['rrc_id', 'branch_id', 'category_4_id'], how='left').fillna(0)
df_full_table = df_full_table.rename(columns={'div': 'Дивизион', 'rrc_name': 'РРЦ', 'category_1_name': 'Департамент', 'category_4_name': 'Категория',
                              'product_count_access_false': 'Не доступный остаток РРЦ', 'product_count_asccess_true': 'Доступный остаток РРЦ',
                              'full_stock': 'Остаток РРЦ', 'branch': 'ТП', 'product_count_tp': 'Остаток ТП', 'product_count': 'Потенциал наполения ТП'})

st.write("Полная таблица")

if df_full_table.empty:
    st.write('Нет данных')
else:
    st.dataframe(df_full_table[['Дивизион', 'РРЦ', 'Департамент', 'Категория', 'Не доступный остаток РРЦ', 'Доступный остаток РРЦ', 'Остаток РРЦ', 'ТП', 'Остаток ТП', 'Потенциал наполения ТП']])