import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from io import BytesIO

st.set_page_config(page_title='Strength Report Explorer', page_icon='🏋️', layout='wide')
DEFAULT_FILE = Path(__file__).parent / 'strength-report-2026.csv'

@st.cache_data
def load_data(uploaded_bytes=None):
    if uploaded_bytes is None:
        return pd.read_csv(DEFAULT_FILE)
    return pd.read_csv(BytesIO(uploaded_bytes))

def clean_value(series):
    return pd.to_numeric(series, errors='coerce')

st.title('🏋️ Strength Report Explorer')
st.caption('Interactive Streamlit GUI for exploring strength-report-2026.csv')

with st.sidebar:
    st.header('Data')
    uploaded = st.file_uploader('Upload another CSV', type=['csv'])
    data = load_data(uploaded.getvalue() if uploaded else None)
    st.divider()
    st.header('Filters')
    datasets = sorted(data['dataset'].dropna().astype(str).unique())
    selected_datasets = st.multiselect('Dataset sections', datasets, default=datasets)
    filtered = data[data['dataset'].astype(str).isin(selected_datasets)].copy()
    metric_options = sorted(filtered['metric'].dropna().astype(str).unique())
    selected_metrics = st.multiselect('Metrics', metric_options, default=metric_options[:20] if len(metric_options) > 20 else metric_options)
    if selected_metrics:
        filtered = filtered[filtered['metric'].astype(str).isin(selected_metrics)]
    key1_options = sorted(filtered['key1'].dropna().astype(str).unique())
    selected_key1 = st.multiselect('Exercise / category (key1)', key1_options, default=[])
    if selected_key1:
        filtered = filtered[filtered['key1'].astype(str).isin(selected_key1)]
    st.success(f'{len(filtered):,} rows in current view')

filtered['value_num'] = clean_value(filtered['value'])
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
        fig = px.bar(summary, x='value_num', y='metric', color='dataset', orientation='h', title='Top metric totals in the current selection', hover_data=['dataset'])
        fig.update_layout(height=750, yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
        st.subheader('Metric distribution')
        dist = numeric.groupby('metric', as_index=False)['value_num'].agg(['count','min','median','mean','max']).reset_index().sort_values('count', ascending=False)
        st.dataframe(dist, use_container_width=True, hide_index=True)

with tab_explore:
    st.subheader('Build your own chart')
    numeric = filtered.dropna(subset=['value_num']).copy()
    if numeric.empty:
        st.warning('Choose filters that include numeric values.')
    else:
        dimensions = [c for c in ['dataset','key1','key2','metric'] if numeric[c].notna().any()]
        x_dim = st.selectbox('X axis', dimensions, index=min(1, len(dimensions)-1))
        color_dim = st.selectbox('Color / group', ['None'] + dimensions)
        chart_type = st.radio('Chart', ['Bar','Line','Scatter'], horizontal=True)
        chart_df = numeric.copy()
        if chart_df[x_dim].nunique() > 80:
            top_x = chart_df.groupby(x_dim)['value_num'].sum().nlargest(80).index
            chart_df = chart_df[chart_df[x_dim].isin(top_x)]
        kwargs = dict(data_frame=chart_df, x=x_dim, y='value_num', title=f'{chart_type}: value by {x_dim}')
        if color_dim != 'None': kwargs['color'] = color_dim
        if chart_type == 'Bar': fig = px.bar(**kwargs)
        elif chart_type == 'Line': fig = px.line(**kwargs)
        else: fig = px.scatter(**kwargs)
        st.plotly_chart(fig, use_container_width=True)

with tab_data:
    st.subheader('Filtered records')
    display_cols = ['dataset','key1','key2','key3','metric','value']
    st.dataframe(filtered[display_cols], use_container_width=True, height=650, hide_index=True)
    st.download_button('⬇️ Download filtered CSV', data=filtered[display_cols].to_csv(index=False).encode('utf-8'), file_name='strength-report-filtered.csv', mime='text/csv')

with tab_about:
    st.subheader('About this app')
    st.markdown('This app is a public, GitHub-friendly explorer for **strength-report-2026.csv**.\n\n**Dataset columns**\n- `dataset` — report section\n- `key1`, `key2`, `key3` — dimensions/categories\n- `metric` — measured statistic\n- `value` — metric value\n\n**Run locally**\n```bash\npip install -r requirements.txt\nstreamlit run app.py\n```')