import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from scipy.optimize import curve_fit

st.set_page_config(page_title='Fashion Trend Lifecycle', layout='wide')

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;600;700&family=Jost:wght@300;400&display=swap');
    
    * {
        font-family: 'Jost', sans-serif !important;
        font-weight: 300 !important;
        letter-spacing: 0.03em !important;
    }
    
    h1, h2, h3 {
        font-family: 'Cormorant Garamond', serif !important;
        font-weight: 600 !important;
        letter-spacing: 0.05em !important;
    }
    </style>
""", unsafe_allow_html=True)

df = pd.read_csv('trends_raw.csv', index_col=0, parse_dates=True)

def dates_to_numeric(series):
    return np.array((series.index - series.index[0]).days, dtype=float)

def lognormal_curve(x, amplitude, mean, sigma):
    return amplitude * np.exp(-((np.log(x + 1) - mean) ** 2) / (2 * sigma ** 2))

def fit_trend(series):
    x = dates_to_numeric(series)
    y = series.values.astype(float)
    for sigma_guess in [0.1, 0.3, 0.5, 1.0, 2.0]:
        try:
            p0 = [y.max(), np.log(x[y.argmax()] + 1), sigma_guess]
            params, _ = curve_fit(lognormal_curve, x, y, p0=p0, maxfev=10000)
            amplitude, mean, sigma = params
            y_pred = lognormal_curve(x, *params)
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1 - (ss_res / ss_tot)
            return params, r_squared, x
        except RuntimeError:
            continue
    return None, None, None

st.title('Fashion Micro-Trend Lifecycle Modeler')
st.write('Analyzing how fast fashion trends rise and fall using Google Trends data.')

st.subheader('Search Interest Over Time')
st.line_chart(df)

st.subheader('Explore a Trend')
selected_trend = st.selectbox('Select a trend', df.columns)

series = df[selected_trend].dropna()
params, r_squared, x = fit_trend(series)

fig = go.Figure()
fig.add_trace(go.Scatter(x=series.index, y=series.values, name='Actual', opacity=0.6))

if params is not None:
    y_fitted = lognormal_curve(x, *params)
    fig.add_trace(go.Scatter(x=series.index, y=y_fitted, name='Fitted curve', line=dict(color='red', width=2)))
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric('Peak Value', f"{series.max()}/100")
    col2.metric('Peak Date', series.idxmax().strftime('%b %Y'))
    col3.metric('R² Score', round(r_squared, 3))
    col4.metric('Sigma', round(params[2], 2))
else:
    st.info('This trend could not be fitted — it may still be growing or have insufficient data.')
    col1, col2 = st.columns(2)
    col1.metric('Peak Value', f"{series.max()}/100")
    col2.metric('Peak Date', series.idxmax().strftime('%b %Y'))

fig.update_layout(title=f'{selected_trend} — Lifecycle Curve', xaxis_title='Date', yaxis_title='Search Interest (0-100)')
st.plotly_chart(fig, use_container_width=True)

st.subheader('All Trends Summary')
metrics = []
for trend in df.columns:
    series = df[trend]
    peak_value = series.max()
    peak_date = series.idxmax()
    post_peak = series[peak_date:]
    half_life_rows = post_peak[post_peak <= peak_value * 0.5]
    weeks_to_halflife = (half_life_rows.index[0] - peak_date).days // 7 if not half_life_rows.empty else None
    _, r_squared, _ = fit_trend(series.dropna())
    metrics.append({
        'Trend': trend,
        'Peak Value': peak_value,
        'Peak Date': peak_date.strftime('%b %Y'),
        'Weeks to Half-Life': weeks_to_halflife,
        'R²': round(r_squared, 3) if r_squared else 'no fit'
    })

st.dataframe(pd.DataFrame(metrics).set_index('Trend'))