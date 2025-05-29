import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

# file_id = '1i9eeimraY6oceYxVqOiCBeT0GcUBnxH3'
# url = f'https://drive.google.com/uc?id={file_id}&export=download'

@st.cache_data
def load_data():
    df = pd.read_csv('df_28_05.csv')
    return df

def main():
    # Уровень 1: Заголовок
    st.title("Доля уникальных товаров по технопоинтам")

    df = load_data()

    # Уровень 2: 3 мультиселекта - в одной строке
    col1, col2, col3 = st.columns(3)
    with col1:
        federal_status_filter = st.multiselect(
            "Федеральный статус",
            options=df['federal_status_name'].dropna().unique(),
            default=list(df['federal_status_name'].dropna().unique())
        )
    with col2:
        life_cycle_filter = st.multiselect(
            "Статус жизненного цикла",
            options=df['life_cycle_status_name'].dropna().unique(),
            default=list(df['life_cycle_status_name'].dropna().unique())
        )
    with col3:
        purchase_status_filter = st.multiselect(
            "Статус закупа",
            options=df['purchase_status_name'].dropna().unique(),
            default=list(df['purchase_status_name'].dropna().unique())
        )

    # Уровень 3: фильтр топ категорий
    col_left, col_right = st.columns(2)
    with col_left:
        top_category_filter = st.multiselect(
            "В топ категориях",
            options=[True, False],
            default=[True, False]
        )
    with col_right:
        st.empty()  # можно убрать или добавить ещё элементы

    # Фильтрация данных по первичным фильтрам (кроме РРЦ)
    df_filtered = df[
        (df['federal_status_name'].isin(federal_status_filter)) &
        (df['life_cycle_status_name'].isin(life_cycle_filter)) &
        (df['purchase_status_name'].isin(purchase_status_filter)) &
        (df['top_category'].isin(top_category_filter))
    ]

    # Подготовка данных для таблицы и мини-графика (без фильтрации по РРЦ)
    tp_ass = df_filtered.groupby(['div', 'rrc_name', 'branch'], as_index=False)['product'] \
                .nunique() \
                .query('product >= 1000') \
                .rename(columns={'product': 'tp_ass'})

    rrc_ass = df_filtered.groupby(['div', 'rrc_name'], as_index=False)['product'] \
                .nunique() \
                .rename(columns={'product': 'rrc_ass'})

    main_df = rrc_ass.merge(tp_ass, on=['div', 'rrc_name'])[['div', 'rrc_name', 'branch', 'rrc_ass', 'tp_ass']]
    main_df['cover_rate'] = (main_df['tp_ass'] / main_df['rrc_ass']).mul(100).round(2)

    # Уровень 4: таблица + график на одной линии, таблица 2/3 ширины
    st.write("Таблица с абсолютными значениями")
    absolute_df = main_df[['div', 'rrc_name', 'branch', 'rrc_ass', 'tp_ass']].rename(columns={
        'div': 'Дивизион',
        'rrc_name': 'РРЦ',
        'branch': 'ТП',
        'rrc_ass': 'Ассортимент на РРЦ',
        'tp_ass': 'Ассортимент на ТП'
    })

    col4, col5 = st.columns([2, 1])  # 2/3 и 1/3 ширины

    with col4:
        st.dataframe(absolute_df)

    net_diff = round((main_df['tp_ass'] / main_df['rrc_ass']).mean() * 100, 2)
    one_number = pd.DataFrame({
        "Net": ["ДНС"],
        "CovarageRate": [net_diff]
    })

    fig_n = px.bar(one_number, x="Net",
                   y="CovarageRate",
                   labels={"Net": "Сеть", "CovarageRate": "Доля ассортимента (%)"},
                   text='CovarageRate')
    fig_n.update_yaxes(range=[0, 100])
    fig_n.update_traces(texttemplate='%{text:.1f}%', textposition='outside')

    with col5:
        st.plotly_chart(fig_n)

    # --- НОВЫЙ БЛОК: Фильтр по РРЦ для большего графика ---
    all_rrc = main_df['rrc_name'].dropna().unique().tolist()
    default_rrc = all_rrc[:3]  # по умолчанию 3 РРЦ

    col_rrc_filter, _ = st.columns([1,1])  # Левая половина для фильтра, правая пустая

    with col_rrc_filter:
        rrc_selection = st.multiselect(
            "Выберите РРЦ для отображения большого графика",
            options=all_rrc,
            default=default_rrc
        )

    # Фильтруем данные для большого графика только по выбранным РРЦ
    main_df_filtered_for_chart = main_df[main_df['rrc_name'].isin(rrc_selection)].copy()

    # Сортируем по РРЦ и технопоинтам для правильного порядка на оси X
    main_df_filtered_for_chart = main_df_filtered_for_chart.sort_values(by=['rrc_name', 'branch'])
    ordered_branches = main_df_filtered_for_chart['branch'].unique().tolist()

    # Уровень 5: большой график с долями для каждого филиала (на всю ширину)
    fig = px.bar(
        main_df_filtered_for_chart,
        x='branch',
        y='cover_rate',
        color='rrc_name',
        text='cover_rate',
        labels={
            'branch': 'Технопоинт',
            'cover_rate': 'Доля ассортимента (%)',
            'rrc_name': 'РРЦ'
        },
        barmode='group'
    )
    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig.update_yaxes(range=[0, 100])
    fig.update_layout(
        bargap=0.02,           # уменьшенный зазор между группами баров
        bargroupgap=0.01,      # уменьшенный зазор между барами внутри группы
        xaxis=dict(
            type='category',
            categoryorder='array',
            categoryarray=ordered_branches,
            automargin=True
        )
    )

    st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()