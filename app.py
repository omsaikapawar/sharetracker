from flask import Flask, render_template, jsonify, request
import yfinance as yf
import pandas as pd

app = Flask(__name__)

# CSV file paths (assumed to be in "data" folder)
stock_categories = {
    "nifty50": "data/ind_nifty50list.csv",
    "nifty500": "data/ind_nifty500list.csv",
    "niftybank": "data/ind_niftybanklist.csv",
    "niftyit": "data/ind_niftyitlist.csv",
    "niftynext50": "data/ind_niftynext50list.csv"
}

def load_stock_symbols(category):
    df = pd.read_csv(stock_categories[category])
    return df["Symbol"].tolist()

def fetch_stock_data(symbol):
    try:
        formatted_symbol = symbol.strip().upper() + ".NS"
        stock = yf.Ticker(formatted_symbol)
        data = stock.history(period="5y")

        if not data.empty:
            ltp = round(data["Close"].iloc[-1], 2)
            all_time_high = round(data["High"].max(), 2)
            all_time_low = round(data["Low"].min(), 2)
            high_date = data["High"].idxmax().strftime("%Y-%m")
            return {
                "symbol": symbol,
                "ltp": ltp,
                "all_time_high": all_time_high,
                "all_time_low": all_time_low,
                "high_date": high_date
            }
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
    return None

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/stocks', methods=['GET'])
def get_stocks():
    category = request.args.get("category", "nifty500")
    user_date = request.args.get("date", "2024-01")

    if category == "all":
        all_symbols = []
        for csv_path in stock_categories.values():
            df = pd.read_csv(csv_path)
            all_symbols.extend(df["Symbol"].tolist())
        stock_list = all_symbols
    elif category in stock_categories:
        stock_list = load_stock_symbols(category)
    else:
        return jsonify({"error": "Invalid category"}), 400

    stock_data = [fetch_stock_data(symbol) for symbol in stock_list if fetch_stock_data(symbol)]
    return jsonify(stock_data)

@app.route('/stock-details/<string:symbol>')
def stock_details(symbol):
    symbol = symbol.strip().upper()
    stock_info = fetch_stock_data(symbol)
    if not stock_info:
        return "Stock not found or no data available", 404

    full_symbol = symbol + ".NS"
    ticker = yf.Ticker(full_symbol)

    info = ticker.info
    open_price = info.get("open", "N/A")
    market_cap = info.get("marketCap", "N/A")
    pe_ratio = info.get("trailingPE", "N/A")
    div_yield = info.get("dividendYield", "N/A")
    wk52_high = info.get("fiftyTwoWeekHigh", "N/A")
    wk52_low = info.get("fiftyTwoWeekLow", "N/A")

    return render_template("stock_details.html",
                           stock=stock_info,
                           open_price=open_price,
                           market_cap=market_cap,
                           pe_ratio=pe_ratio,
                           div_yield=div_yield,
                           wk52_high=wk52_high,
                           wk52_low=wk52_low)

if __name__ == '__main__':
    app.run(debug=True)
