import pandas as pd
import numpy as np
import yfinance as yf
from flask import Flask, render_template
import os

app = Flask(__name__)

# تحويل الشموع إلى Heikin-Ashi
def get_heikin_ashi(df):
    try:
        ha_df = df.copy()
        ha_df['Close'] = (df['Open'] + df['High'] + df['Low'] + df['Close']) / 4
        ha_open = np.zeros(len(df))
        ha_open[0] = (df['Open'].iloc[0] + df['Close'].iloc[0]) / 2
        for i in range(1, len(df)):
            ha_open[i] = (ha_open[i-1] + ha_df['Close'].iloc[i-1]) / 2
        ha_df['Open'] = ha_open
        ha_df['High'] = ha_df[['High', 'Open', 'Close']].max(axis=1)
        ha_df['Low'] = ha_df[['Low', 'Open', 'Close']].min(axis=1)
        return ha_df
    except: return df

# حساب WaveTrend
def calculate_wavetrend(df, n1=10, n2=21):
    ap = (df['High'] + df['Low'] + df['Close']) / 3
    esa = ap.ewm(span=n1, adjust=False).mean()
    d = (ap - esa).abs().ewm(span=n1, adjust=False).mean()
    ci = (ap - esa) / (0.015 * d)
    wt1 = ci.ewm(span=n2, adjust=False).mean()
    wt2 = wt1.rolling(window=4).mean()
    return wt1, wt2

def get_signals():
    # الرموز من ملفك أو الافتراضية
    symbols = ["^TASI", "6040.SR"] # رموز تجريبية
    if os.path.exists('symbols.txt'):
        with open('symbols.txt', 'r') as f:
            extra = [l.strip() for l in f.readlines() if l.strip()]
            if extra: symbols = extra

    results = []
    for symbol in symbols:
        try:
            # التعديل هنا: فاصل أسبوعي interval="1wk"
            # فترة 5 سنوات كافية جداً للأسبوعي
            data = yf.download(symbol, period="5y", interval="1wk", progress=False, timeout=15)
            
            if data.empty or len(data) < 25:
                continue

            ha_data = get_heikin_ashi(data)
            wt1, wt2 = calculate_wavetrend(ha_data)
            
            c_wt1, c_wt2 = float(wt1.iloc[-1]), float(wt2.iloc[-1])
            p_wt1, p_wt2 = float(wt1.iloc[-2]), float(wt2.iloc[-2])

            signal, color = "انتظار", "#95a5a6"
            
            # تقاطع إيجابي أسبوعي (قيد التشكل أو مؤكد)
            if p_wt1 <= p_wt2 and c_wt1 > c_wt2:
                signal, color = "إيجابي أسبوعي", "#2ecc71"
            elif p_wt1 >= p_wt2 and c_wt1 < c_wt2:
                signal, color = "سلبي أسبوعي", "#e74c3c"

            results.append({
                'symbol': symbol, 
                'wt1': round(c_wt1, 2), 
                'wt2': round(c_wt2, 2), 
                'signal': signal, 
                'color': color
            })
        except: continue
            
    return results

@app.route('/')
def index():
    stocks = get_signals()
    return render_template('index.html', stocks=stocks)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
