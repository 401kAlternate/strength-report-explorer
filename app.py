import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title='Strength Intelligence Lab', page_icon='🏋️', layout='wide', initial_sidebar_state='expanded')

KNOWN = {
    'users': 49139, 'sessions': 368505, 'sets': 5843507,
    'tonnage': 1851118616, 'exercises': 39278,
    'first_session': '2021-03-06', 'last_session': '2026-09-02',
    'bench_users': 6500, 'squat_users': 5931, 'ohp_users': 4582, 'deadlift_users': 5247,
    'bench_share': 0.0979, 'squat_share': 0.0803,
    'session_median': 48.8, 'sets_median': 16, 'exercises_median': 4,
    'tonnage_median': 4330, 'weekly_median': 2,
    'bench_p50': 77.4, 'bench_p90': 115.2, 'bench_p99': 151.5,
    'bench_60_plus': 0.6095,
    'bench_milestone_observed': 2191, 'bench_milestone_reached': 228, 'bench_milestone_share': 0.1041
}

def fmt_int(x): return f'{x:,}'
def fmt_pct(x): return f'{x*100:.1f}%'

@st.cache_data
def load_data(file_bytes):
    return pd.read_csv(BytesIO(file_bytes))

def metric_value(data, dataset, metric, key1=None, key2=None):
    q = data[(data.dataset == dataset) & (data.metric == metric)]
    if key1 is not None: q = q[q.key1.astype(str) == str(key1)]
    if key2 is not None: q = q[q.key2.astype(str) == str(key2)]
    return q.iloc[0].value if len(q) else None

st.title('🏋️ Strength Intelligence Lab')
st.markdown('### The data behind how people train, progress, and get stronger.')
st.caption('A research-style interface built from the supplied 2026 strength report. Upload the source CSV when you want to explore the underlying records.')

with st.sidebar:
    st.header('🧭 Explore')
    page = st.radio('Go to', ['Overview', 'Exercises', 'Progression', 'Milestones', 'Sessions', 'Training Time', 'Strength Percentiles', 'Research Data'], label_visibility='collapsed')
    st.divider()
    st.header('📤 Your Data')
    uploaded = st.file_uploader('Upload the report CSV', type=['csv'])
    if uploaded:
        data = load_data(uploaded.getvalue())
        st.success(f'Loaded {len(data):,} rows')
    else:
        data = None
        st.info('The app can be explored without uploading anything. Upload the CSV for record-level exploration.')

if page == 'Overview':
    st.subheader('What is in this dataset?')
    a,b,c,d = st.columns(4)
    a.metric('People', fmt_int(KNOWN['users']))
    b.metric('Sessions', fmt_int(KNOWN['sessions']))
    c.metric('Finished sets', fmt_int(KNOWN['sets']))
    d.metric('Total tonnage', f"{KNOWN['tonnage']/1e9:.2f}B kg")
    e,f,g,h = st.columns(4)
    e.metric('Exercises logged', fmt_int(KNOWN['exercises']))
    f.metric('Median session', f"{KNOWN['session_median']} min")
    g.metric('Median sets/session', str(KNOWN['sets_median']))
    h.metric('Median sessions/week', str(KNOWN['weekly_median']))

    st.divider()
    st.subheader('Seven questions the report can answer')
    cards = [
        ('🏋️ Exercises', 'What exercises dominate real-world training logs?'),
        ('📈 Progression', 'How much strength changes from month to month?'),
        ('🎯 Milestones', 'How many lifters reach defined strength milestones?'),
        ('⏱️ Sessions', 'What does a typical training session look like?'),
        ('💪 Muscle groups', 'Where does training volume actually go?'),
        ('🕐 Training time', 'When do people train across the day?'),
        ('📊 Percentiles', 'How does a strength level compare with the dataset?')
    ]
    cols = st.columns(3)
    for i,(title,desc) in enumerate(cards):
        with cols[i%3]:
            st.markdown(f'#### {title}')
            st.write(desc)

    st.divider()
    st.subheader('Three things that stand out')
    x,y,z = st.columns(3)
    with x:
        st.metric('Bench press share of sets', fmt_pct(KNOWN['bench_share']))
        st.write('Bench press is the largest single exercise category in the top-exercises section.')
    with y:
        st.metric('Typical session', f"{KNOWN['session_median']} min")
        st.write(f"The median session contains {KNOWN['sets_median']} sets across about {KNOWN['exercises_median']} exercises.")
    with z:
        st.metric('Bench press median e1RM', f"{KNOWN['bench_p50']} kg")
        st.write(f"The 90th percentile is {KNOWN['bench_p90']} kg and the 99th percentile is {KNOWN['bench_p99']} kg.")

    st.caption(f"Report period represented: {KNOWN['first_session']} → {KNOWN['last_session']}")

elif page == 'Exercises':
    st.subheader('🏋️ The Training Landscape')
    st.write('The report tracks 39,278 distinct exercises. The top-exercises section shows which movements generate the largest share of logged sets.')
    if data is not None:
        q = data[data.dataset == 'top-exercises'].copy()
        if not q.empty:
            piv = q.pivot_table(index=['key1','key2'], columns='metric', values='value', aggfunc='first').reset_index()
            for col in ['sets','users','sessions','shareOfSets','medianReps','medianKg']:
                if col in piv: piv[col] = pd.to_numeric(piv[col], errors='coerce')
            st.dataframe(piv.sort_values('sets', ascending=False).head(50), use_container_width=True, hide_index=True)
            if 'sets' in piv:
                chart = piv.sort_values('sets', ascending=False).head(20)
                st.plotly_chart(px.bar(chart, x='sets', y='key1', orientation='h', title='Top 20 exercises by logged sets'), use_container_width=True)
    else:
        ex = pd.DataFrame({'Exercise':['Bench press','Squat','Overhead press','Deadlift'], 'Users':[6500,5931,4582,5247], 'Share of sets':[9.79,8.03,None,None]})
        st.dataframe(ex, use_container_width=True, hide_index=True)
        st.info('Upload the CSV to unlock the full exercise catalogue and interactive ranking.')

elif page == 'Progression':
    st.subheader('📈 How Strength Changes')
    st.write('Monthly-gain records describe observed changes in strength by starting level and month. This section is intended to distinguish typical progression from individual anecdotes.')
    if data is not None:
        q = data[data.dataset == 'monthly-gain'].copy()
        q['value_num'] = pd.to_numeric(q.value, errors='coerce')
        metric = st.selectbox('Measure', sorted(q.metric.dropna().unique()))
        qq = q[q.metric == metric]
        st.dataframe(qq, use_container_width=True, hide_index=True)
    else:
        st.info('Upload the CSV to inspect monthly progression cohorts, gains, percent gains, and no-gain shares.')

elif page == 'Milestones':
    st.subheader('🎯 Strength Milestones')
    st.write('Milestones are framed as observed users, users who reached the milestone, and the share reaching it. This makes the report useful for studying progression pathways rather than only maximum lifts.')
    st.metric('Bench press — 1 plate reached share', fmt_pct(KNOWN['bench_milestone_share']))
    st.write(f"In the supplied report, {fmt_int(KNOWN['bench_milestone_observed'])} users were observed for this milestone and {fmt_int(KNOWN['bench_milestone_reached'])} reached it.")
    if data is not None:
        q = data[data.dataset == 'milestones'].copy()
        q['value_num'] = pd.to_numeric(q.value, errors='coerce')
        lift = st.selectbox('Lift', sorted(q.key1.dropna().unique()))
        qq = q[q.key1 == lift]
        st.dataframe(qq, use_container_width=True, hide_index=True)
    else:
        st.info('Upload the CSV to explore all milestone levels and lifts.')

elif page == 'Sessions':
    st.subheader('⏱️ What Does a Typical Workout Look Like?')
    a,b,c,d = st.columns(4)
    a.metric('Median duration', f"{KNOWN['session_median']} min")
    b.metric('Median sets', str(KNOWN['sets_median']))
    c.metric('Median exercises', str(KNOWN['exercises_median']))
    d.metric('Median tonnage', f"{KNOWN['tonnage_median']:,} kg")
    st.write('The report describes the distribution of session duration, sets, exercises, tonnage, and active-week frequency.')
    if data is not None:
        q = data[data.dataset == 'session-stats'].copy()
        q['value_num'] = pd.to_numeric(q.value, errors='coerce')
        st.dataframe(q[['metric','value']], use_container_width=True, hide_index=True)
    else:
        st.info('Upload the CSV for the complete session-stat distribution.')

elif page == 'Training Time':
    st.subheader('🕐 When Do People Train?')
    st.write('The `when` section breaks sessions down by hour. Use it to see the daily rhythm of recorded training.')
    if data is not None:
        q = data[data.dataset == 'when'].copy()
        q['value_num'] = pd.to_numeric(q.value, errors='coerce')
        sessions = q[q.metric == 'sessions'].copy()
        if not sessions.empty:
            sessions['hour'] = pd.to_numeric(sessions.key2, errors='coerce')
            st.plotly_chart(px.line(sessions.sort_values('hour'), x='hour', y='value_num', markers=True, title='Recorded sessions by hour'), use_container_width=True)
        st.dataframe(q, use_container_width=True, hide_index=True)
    else:
        st.info('Upload the CSV to render the full hourly training curve.')

elif page == 'Strength Percentiles':
    st.subheader('📊 Where Does a Strength Level Sit?')
    st.write('Percentiles let the report answer a different question: not just “how much?”, but “how does this level compare with the observed population?”')
    if data is not None:
        q = data[data.dataset == 'percentiles'].copy()
        lifts = sorted(q.key1.dropna().unique())
        lift = st.selectbox('Lift', lifts)
        qq = q[q.key1 == lift].copy()
        qq['value_num'] = pd.to_numeric(qq.value, errors='coerce')
        st.dataframe(qq[['metric','value']], use_container_width=True, hide_index=True)
        p = qq[qq.metric.str.startswith('e1rmP', na=False)]
        if not p.empty:
            st.plotly_chart(px.bar(p, x='metric', y='value_num', title=f'{lift}: estimated 1RM percentiles'), use_container_width=True)
    else:
        st.metric('Bench press P50 e1RM', f"{KNOWN['bench_p50']} kg")
        st.metric('Bench press P90 e1RM', f"{KNOWN['bench_p90']} kg")
        st.metric('Bench press P99 e1RM', f"{KNOWN['bench_p99']} kg")
        st.info('Upload the CSV to compare all lifts and percentile bands.')

elif page == 'Research Data':
    st.subheader('🔬 Research Data')
    st.write('This is the raw-data view for people who want to inspect the evidence behind the narratives.')
    if data is None:
        st.warning('Upload the CSV from the sidebar to activate the research table.')
    else:
        st.dataframe(data, use_container_width=True, height=650, hide_index=True)
        st.download_button('⬇️ Download the loaded CSV', data=data.to_csv(index=False).encode('utf-8'), file_name='strength-report-copy.csv', mime='text/csv')

st.divider()
st.caption('Interpretation note: these are descriptive statistics from the supplied report, not a representative sample of all people who train. Use them as an observational dataset.')