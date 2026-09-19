import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title='Strength Report Explorer', page_icon='🏋️', layout='wide')

st.title('🏋️ Strength Report Explorer')
st.caption('Upload a strength-report CSV and explore it interactively — no local Python installation required.')

with st.sidebar:
    st.header('📤 Upload Data')
    uploaded = st.file_uploader(
        'Upload your CSV',
        type=['csv'],
        help='CSV should contain dataset, key1, key2, key3, metric, and value columns.'
    )

if uploaded is None:
    st.info('👋 Upload a CSV in the sidebar to start exploring your data.')
    st.markdown('''
    ### Expected columns
    - `dataset` — report section
    - `key1`, `key2`, `key3` — dimensions/categories
    - `metric` — measured statistic
    - `value` — metric value

    Your file is processed by this Streamlit session. It does not need to be stored in GitHub.
    ''')
    st.stop()

@st.cache_data
def load_data(file_bytes):
    return pd.read_csv(BytesIO(file_bytes))

data = load_data(uploaded.getvalue())
required = {'dataset', 'key1', 'key2', 'key3', 'metric', 'value'}
missing = required - set(data.columns)

if missing:
    st.error(f'Missing required columns: {", ".join(sorted(missing))}')
    st.write('Your file contains:', ', '.join(data.columns))
    st.stop()

with st.sidebar:
    st.divider()
    st.header('🔎 Filters')
    datasets = sorted(data['dataset'].dropna().astype(str).unique())
    selected_datasets = st.multiselect('Dataset sections', datasets, default=datasets)
    filtered = data[data['dataset'].astype(str).isin(selected_datasets)].copy()

    metric_options = sorted(filtered['metric'].dropna().astype(str).unique())
    selected_metrics = st.multiselect(
        'Metrics', metric_options,
        default=metric_options[:20] if len(metric_options) > 20 else metric_options
    )
    if selected_metrics:
        filtered = filtered[filtered['metric'].astype(str).isin(selected_metrics)]

    key1_options = sorted(filtered['key1'].dropna().astype(str).unique())
    selected_key1 = st.multiselect('Exercise / category', key1_options, default=[])
    if selected_key1:
        filtered = filtered[filtered['key1'].astype(str).isin(selected_key1)]

    st.success(f'{len(filtered):,} rows')

filtered['value_num'] = pd.to_numeric(filtered['value'], errors='coerce')

c1, c2, c3, c4 = st.columns(4)
c1.metric('Rows', f'{len(filtered):,}')
c2.metric('Datasets', filtered['dataset'].nunique())
c3.metric('Metrics', filtered['metric'].nunique())
c4.metric('Numeric values', f"{filtered['value_num'].notna().sum():,}")

tab_dashboard, tab_explore, tab_data, tab_about = st.tabs(['📊 Dashboard', '📈 Explore', '🔎 Data', 'ℹ️ About'])

with tab_dashboard:
    st.subheader('Dataset overview')
    numeric = filtered.dropna(subset=['value_num']).copy()
    if numeric.empty:
        st.info('No numeric values match the current filters.')
    else:
        summary = numeric.groupby(['dataset', 'metric'], as_index=False)['value_num'].sum().sort_values('value_num', ascending=False).head(30)
        fig = px.bar(summary, x='value_num', y='metric', color='dataset', orientation='h', title='Top metric totals')
        fig.update_layout(height=750, yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
        dist = numeric.groupby('metric', as_index=False)['value_num'].agg(['count','min','median','mean','max']).reset_index().sort_values('count', ascending=False)
        st.subheader('Metric distribution')
        st.dataframe(dist, use_container_width=True, hide_index=True)

with tab_explore:
    st.subheader('Build your own chart')
    numeric = filtered.dropna(subset=['value_num']).copy()
    if numeric.empty:
        st.warning('Choose filters that include numeric values.')
    else:
        dimensions = [c for c in ['dataset','key1','key2','metric'] if numeric[c].notna().any()]
        x_dim = st.selectbox('X axis', dimensions)
        color_dim = st.selectbox('Color / group', ['None'] + dimensions)
        chart_type = st.radio('Chart', ['Bar','Line','Scatter'], horizontal=True)
        chart_df = numeric.copy()
        if chart_df[x_dim].nunique() > 80:
            top_x = chart_df.groupby(x_dim)['value_num'].sum().nlargest(80).index
            chart_df = chart_df[chart_df[x_dim].isin(top_x)]
        kwargs = dict(data_frame=chart_df, x=x_dim, y='value_num', title=f'{chart_type}: value by {x_dim}')
        if color_dim != 'None': kwargs['color'] = color_dim
        fig = px.bar(**kwargs) if chart_type == 'Bar' else (px.line(**kwargs) if chart_type == 'Line' else px.scatter(**kwargs))
        st.plotly_chart(fig, use_container_width=True)

with tab_data:
    st.subheader('Filtered records')
    display_cols = ['dataset','key1','key2','key3','metric','value']
    st.dataframe(filtered[display_cols], use_container_width=True, height=650, hide_index=True)
    st.download_button('⬇️ Download filtered CSV', data=filtered[display_cols].to_csv(index=False).encode('utf-8'), file_name='strength-report-filtered.csv', mime='text/csv')

with tab_about:
    st.subheader('About')
    st.markdown('This is a browser-based Strength Report Explorer. Upload a compatible CSV in the sidebar; no dataset file is required in GitHub.')