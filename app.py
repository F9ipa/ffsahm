import os
import time
import threading
from flask import Flask, render_template, jsonify
import yfinance as yf

app = Flask(__name__)

# مخزن البيانات في ذاكرة السيرفر
data_store = {
    'stocks': [],
    'last_update': 0,
    'is_loading': False
}

def load_tasi_symbols():
    try:
        path = os.path.join(os.path.dirname(__file__), 'tasi.txt')
        with open(path, 'r') as f:
            return [f"{line.strip()}.SR" for line in f if line.strip()]
    except:
        return ["2222.SR"] # رمز احتياطي في حال فقدان الملف

def background_fetch():
    """وظيفة تعمل في الخلفية لتحديث البيانات كل 5 دقائق"""
    global data_store
    while True:
        try:
            data_store['is_loading'] = True
            symbols = load_tasi_symbols()
            
            # جلب البيانات لـ 269 شركة دفعة واحدة
            df = yf.download(' '.join(symbols), period="1d", interval="1m", group_by='ticker', threads=True, progress=False)
            
            temp_list = []
            for sym in symbols:
                try:
                    if sym in df and not df[sym].empty:
                        last = float(df[sym]['Close'].iloc[-1])
                        prev = float(df[sym]['Open'].iloc[0])
                        change = last - prev
                        temp_list.append({
                            's': sym.replace('.SR', ''),
                            'p': round(last, 2),
                            'c': round(change, 2),
                            'pc': round((change/prev)*100, 2)
                        })
                except: continue
            
            if temp_list:
                # ترتيب حسب الأكثر صعوداً وتخزينها
                data_store['stocks'] = sorted(temp_list, key=lambda x: x['pc'], reverse=True)
                data_store['last_update'] = time.time()
            
            data_store['is_loading'] = False
        except Exception as e:
            print(f"Fetch Error: {e}")
            data_store['is_loading'] = False
        
        # الانتظار لمدة 5 دقائق قبل التحديث القادم
        time.sleep(300)

# تشغيل عملية الجلب في الخلفية فور تشغيل التطبيق
threading.Thread(target=background_fetch, daemon=True).start()

@app.route('/api/data')
def get_stock_data():
    # الرد الفوري بما هو موجود في الذاكرة
    return jsonify({
        'stocks': data_store['stocks'],
        'loading': data_store['is_loading'],
        'updated': bool(data_store['stocks'])
    })

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == "__main__":
    # تشغيل السيرفر على بورت Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
