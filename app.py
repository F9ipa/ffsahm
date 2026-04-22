import pandas as pd
import numpy as np
import yfinance as yf
from flask import Flask, render_template
import os

app = Flask(__name__)

# 1. دالة تحويل الشموع العادية إلى Heikin-Ashi
def get_heikin_ashi(df):
    ha_df = df.copy()
    # إغلاق هايكن آشي: (Open+High+Low+Close) / 4
    ha_df['Close'] = (df['Open'] + df['High'] + df['Low'] + df['Close']) / 4
    
    # افتتاح هايكن آشي: متوسط (افتتاح السابقة + إغلاق السابقة)
    # نحتاج لحلقة بسيطة لحسابها لأن كل شمعة تعتمد على ما قبلها
    ha_open = [(df['Open'].iloc[0] + df['Close'].iloc[0]) / 2]
    for i in range(1, len(df)):
        ha_open.append((ha_open[i-1] + ha_df['Close'].iloc[i-1]) / 2)
    ha_df['Open'] = ha_open
    
    # أعلى وأدنى هايكن آشي
    ha_df['High'] = ha_df[['High', 'Open', 'Close']].max(axis=1)
    ha_df['Low'] = ha_df[['Low', 'Open', 'Close']].min(axis=1)
    
    return ha_df

# 2. حساب WaveTrend باستخدام قيم Heikin-Ashi
def calculate_wavetrend(df, n1=10, n2=21):
    # استخدام hlc3 من قيم هايكن آشي المحسوبة
    ap = (df['High'] + df['Low'] + df['Close']) / 3
    esa = ap.ewm(span=n1, adjust=False).mean()
    d = (ap - esa).abs().ewm(span=n1, adjust=False).mean()
    ci = (ap - esa) / (0.015 * d)
    wt1 = ci.ewm(span=n2, adjust=False).mean()
    wt2 = wt1.rolling(window=4).mean()
    return wt1, wt2

def get_signals():
    default_symbols = ["^TASI", "6040.SR", "1120.SR", "2222.SR"]
    
    symbols = []
    if os.path.exists('symbols.txt'):
        with open('symbols.txt', 'r') as f:
            symbols = [line.strip() for line in f.readlines() if line.strip()]
    
    if not symbols:
        symbols = default_symbols
    
    results = []
    for symbol in symbols:
        try:
            data = yf.download(symbol, period="5y", interval="1mo", progress=False)
            if data.empty or len(data) < 30: continue

            # --- التحويل إلى هايكن آشي أولاً ---
            ha_data = get_heikin_ashi(data)
            # --- حساب المؤشر بناءً على هايكن آشي ---
            wt1, wt2 = calculate_wavetrend(ha_data)
            
            curr_wt1 = float(wt1.iloc[-1])
            curr_wt2 = float(wt2.iloc[-1])
            prev_wt1 = float(wt1.iloc[-2])
            prev_wt2 = float(wt2.iloc[-2])
            p_prev_wt1 = float(wt1.iloc[-3])
            p_prev_wt2 = float(wt2.iloc[-3])

            signal = "انتظار"
            color = "gray"
            
            if prev_wt1 <= prev_wt2 and curr_wt1 > curr_wt2:
                signal = "إيجابي (HA لحظي)"
                color = "#2ecc71"
            elif p_prev_wt1 <= p_prev_wt2 and prev_wt1 > prev_wt2:
                signal = "إيجابي مؤكد (HA)"
                color = "#27ae60"
            elif prev_wt1 >= prev_wt2 and curr_wt1 < curr_wt2:
                signal = "سلبي (HA لحظي)"
                color = "#e74c3c"

            results.append({
                'symbol': symbol,
                'wt1': round(curr_wt1, 2),
                'wt2': round(curr_wt2, 2),
                'signal': signal,
                'color': color
            })
        except Exception as e:
            print(f"Error with {symbol}: {e}")
            
    return results

@app.route('/')
def index():
    stocks_data = get_signals()
    return render_template('index.html', stocks=stocks_data)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
