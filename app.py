import os
from flask import Flask, render_template
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

# دالة قراءة الرموز من الملف
def load_symbols():
    try:
        with open('tasi.txt', 'r') as f:
            # تنظيف الرموز وإضافة .SR ليتعرف عليها ياهو فايننس
            return [f"{line.strip()}.SR" for line in f if line.strip()]
    except FileNotFoundError:
        # رموز احتياطية في حال فقدان الملف
        return ["2222.SR", "1120.SR", "1180.SR"]

def get_stock_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        # استخدام fast_info لسرعة الاستجابة
        info = ticker.fast_info
        
        current_price = info['last_price']
        prev_close = info['previous_close']
        change = current_price - prev_close
        pct_change = (change / prev_close) * 100
        
        return {
            'symbol': symbol.replace('.SR', ''),
            'lNameAr': f"شركة {symbol.replace('.SR', '')}", # اسم افتراضي بالرمز
            'lastTradePrice': round(current_price, 2),
            'change': round(change, 2),
            'pctChange': round(pct_change, 2)
        }
    except:
        return None

@app.route('/')
def index():
    symbols = load_symbols()
    stocks_list = []
    
    # استخدام التوازي (Multi-threading) لجلب 269 شركة بسرعة فائقة
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(get_stock_data, symbols)
        
    for res in results:
        if res:
            stocks_list.append(res)
            
    # ترتيب الشركات: الأكبر صعوداً في الأعلى
    stocks_list = sorted(stocks_list, key=lambda x: x['pctChange'], reverse=True)
    
    return render_template('index.html', stocks=stocks_list)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
