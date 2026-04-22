import os, time, threading
from flask import Flask, render_template, jsonify
import yfinance as yf
import pandas as pd

app = Flask(__name__)
# التغيير هنا: سنخزن فقط الشركات التي تنطبق عليها الاستراتيجية
data_store = {'signals': [], 'last_update': 0, 'is_loading': False}

def load_tasi_symbols():
    try:
        path = os.path.join(os.path.dirname(__file__), 'tasi.txt')
        with open(path, 'r') as f:
            return [f"{line.strip()}.SR" for line in f if line.strip()]
    except: return ["2222.SR"]

def background_scan():
    global data_store
    while True:
        try:
            data_store['is_loading'] = True
            symbols = load_tasi_symbols()
            # جلب بيانات 100 يوم
            df = yf.download(' '.join(symbols), period="100d", interval="1d", group_by='ticker', threads=True, progress=False)
            
            opportunities = []
            for sym in symbols:
                try:
                    s_data = df[sym].dropna()
                    if len(s_data) < 50: continue

                    # حساب المتوسطات
                    sma20 = s_data['Close'].rolling(window=20).mean()
                    sma50 = s_data['Close'].rolling(window=50).mean()
                    
                    last_p = float(s_data['Close'].iloc[-1])
                    curr_20 = float(sma20.iloc[-1])
                    curr_50 = float(sma50.iloc[-1])
                    
                    # الفلتر الذهبي: تقاطع 20 فوق 50 والسعر فوق 20
                    if curr_20 > curr_50 and last_p > curr_20:
                        prev_close = float(s_data['Close'].iloc[-2])
                        pc = ((last_p - prev_close) / prev_close) * 100
                        
                        opportunities.append({
                            's': sym.replace('.SR', ''),
                            'p': round(last_p, 2),
                            'pc': round(pc, 2),
                            'sma20': round(curr_20, 2),
                            'sma50': round(curr_50, 2)
                        })
                except: continue
            
            # ترتيب النتائج حسب الأعلى صعوداً
            data_store['signals'] = sorted(opportunities, key=lambda x: x['pc'], reverse=True)
            data_store['last_update'] = time.time()
            data_store['is_loading'] = False
        except: data_store['is_loading'] = False
        
        time.sleep(600) # فحص شامل كل 10 دقائق

threading.Thread(target=background_scan, daemon=True).start()

@app.route('/api/data')
def get_signals():
    return jsonify({
        'stocks': data_store['signals'], 
        'count': len(data_store['signals']),
        'updated': bool(data_store['last_update'] > 0)
    })

@app.route('/')
def index(): return render_template('index.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
