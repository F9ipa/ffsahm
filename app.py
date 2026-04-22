import os
import time
from flask import Flask, render_template, jsonify
import yfinance as yf

app = Flask(__name__)

# تخزين مؤقت للبيانات
data_cache = {'stocks': [], 'last_update': 0}

def load_symbols():
    file_path = os.path.join(os.path.dirname(__file__), 'tasi.txt')
    with open(file_path, 'r') as f:
        return [f"{line.strip()}.SR" for line in f if line.strip()]

@app.route('/api/data')
def get_data():
    global data_cache
    # تحديث كل 5 دقائق
    if time.time() - data_cache['last_update'] < 300 and data_cache['stocks']:
        return jsonify(data_cache['stocks'])

    symbols = load_symbols()
    try:
        # جلب جماعي سريع
        raw_data = yf.download(' '.join(symbols), period="1d", interval="1m", group_by='ticker', threads=True, progress=False)
        stocks_list = []
        for symbol in symbols:
            try:
                s_data = raw_data[symbol]
                if not s_data.empty:
                    close = s_data['Close'].iloc[-1]
                    open_p = s_data['Open'].iloc[0]
                    change = close - open_p
                    stocks_list.append({
                        's': symbol.replace('.SR', ''),
                        'p': round(float(close), 2),
                        'c': round(float(change), 2),
                        'pc': round(float((change/open_p)*100), 2)
                    })
            except: continue
        
        data_cache['stocks'] = sorted(stocks_list, key=lambda x: x['pc'], reverse=True)
        data_cache['last_update'] = time.time()
        return jsonify(data_cache['stocks'])
    except:
        return jsonify(data_cache['stocks'])

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
