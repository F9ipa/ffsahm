import yfinance as yf
import pandas as pd
from flask import Flask, render_template, request
import os

app = Flask(__name__)

def calculate_wavetrend(df):
    if len(df) < 40: return pd.Series(), pd.Series()
    
    # حساب hlc3
    ap = (df['High'] + df['Low'] + df['Close']) / 3
    
    # حساب ESA (EMA n1=10)
    esa = ap.ewm(span=10, adjust=False).mean()
    
    # حساب D (EMA n1=10 لفرق السعر عن ESA)
    d = abs(ap - esa).ewm(span=10, adjust=False).mean()
    
    # حساب CI
    ci = (ap - esa) / (0.015 * d)
    
    # حساب WT1 (EMA n2=21 لـ CI)
    wt1 = ci.ewm(span=21, adjust=False).mean()
    
    # حساب WT2 (SMA 4 لـ WT1)
    wt2 = wt1.rolling(window=4).mean()
    
    return wt1, wt2

def get_signals(interval):
    try:
        with open('stocks.txt', 'r') as f:
            tickers = [line.strip() for line in f if line.strip()]
    except:
        tickers = ["2222.SR", "1120.SR"]

    pos_signals, neg_signals = [], []
    
    for t in tickers:
        try:
            # التحميل مع تقليل البيانات لتسريع العمل
            data = yf.download(t, period="1y", interval=interval, progress=False)
            if len(data) < 10: continue
            
            wt1, wt2 = calculate_wavetrend(data)
            
            # التأكد من وجود قيم كافية
            if pd.isna(wt1.iloc[-1]) or pd.isna(wt2.iloc[-1]): continue
            
            w1_now, w2_now = wt1.iloc[-1], wt2.iloc[-1]
            w1_prev, w2_prev = wt1.iloc[-2], wt2.iloc[-2]
            
            if w1_prev <= w2_prev and w1_now > w2_now:
                pos_signals.append(t.split('.')[0])
            elif w1_prev >= w2_prev and w1_now < w2_now:
                neg_signals.append(t.split('.')[0])
        except:
            continue
    return pos_signals, neg_signals

@app.route('/')
def index():
    interval = request.args.get('interval', '1d')
    pos, neg = get_signals(interval)
    return render_template('index.html', pos=pos, neg=neg, interval=interval)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
