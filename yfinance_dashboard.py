import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import datetime
import requests
import re
from streamlit_autorefresh import st_autorefresh  # 🔄 Import auto-refresh
import pytz


# Set up the Streamlit page
st.set_page_config(page_title='Stock Dashboard', layout='wide')
st.title('📈 Stock Market Dashboard')

# Function to check if the stock market is open
def is_market_open():
    tz = pytz.timezone("America/New_York")
    now = datetime.datetime.now(tz)
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
    return market_open <= now <= market_close and now.weekday() < 5  # Mon-Fri

# Auto-refresh only if market is open
if is_market_open():
    st_autorefresh(interval=30 * 1000, key="stock_refresh")  # 🔄 Refresh every 30 sec
    st.info("📡 Live updates enabled (Market is open)")
else:
    st.warning("⚠️ Market is closed. Live updates paused.")

# Create Tabs
markets_tab, stock_tab, news_tab = st.tabs(["Market Indices", "Stock Data", "Market News"])

def get_stock_data(ticker, start, end, interval="1d"):
    stock = yf.Ticker(ticker)
    df = stock.history(start=start, end=end, interval=interval)
    return df

# Function to get index data for a given period and interval
def get_index_data(symbol, interval='1d', period='1mo'):
    index = yf.Ticker(symbol)
    df = index.history(period=period, interval=interval)
    return df

with markets_tab:
    st.header("📊 Global Market Indices")

    # Dropdown to select trend interval
    interval_map = {
        "Minute": ("1m", "1d"),  # 🔄 Last 60 minutes
        "Hourly": ("1h", "1d"),  # 🔄 Last 24 hours
        "Daily": ("1d", "5d"),
        "Weekly": ("1wk", "3mo"),
        "Monthly": ("1mo", "1y")
    }
    trend_option = st.selectbox("View Trend Interval", list(interval_map.keys()), key="market_interval")
    interval, period = interval_map[trend_option]

    # Market indices to show
    indices = {
        "S&P 500": "^GSPC",
        "NASDAQ": "^IXIC",
        "Dow Jones": "^DJI",
        "FTSE 100": "^FTSE"
    }

    for name, symbol in indices.items():
        try:
            df_idx = get_index_data(symbol, interval=interval, period=period)
            df_idx = df_idx.dropna()

            if not df_idx.empty:
                change_percent = ((df_idx['Close'].iloc[-1] - df_idx['Close'].iloc[0]) / df_idx['Close'].iloc[0]) * 100
                current_price = df_idx['Close'].iloc[-1]

                st.subheader(f"{name} ({symbol})")
                st.metric(label=f"{trend_option} Change", value=f"{current_price:.2f}", delta=f"{change_percent:.2f}%")

                # Plot chart with labels
                fig, ax = plt.subplots(figsize=(8, 3))
                ax.plot(df_idx.index, df_idx['Close'], color='blue', linewidth=2)
                ax.set_title(f"{name} - {trend_option} Trend")
                ax.set_xlabel("Date")
                ax.set_ylabel("Closing Price")
                ax.grid(True)
                st.pyplot(fig)
            else:
                st.warning(f"No data available for {name}.")

        except Exception as e:
            st.warning(f"{name} data unavailable: {e}")

with stock_tab:
    st.header("📉 Stock Analysis")
    
    # Stock input and date selection inside the tab
    symbol = st.text_input('Enter Stock Symbol (e.g., AAPL, TSLA, GOOG)', 'AAPL')
    today = datetime.date.today()
    start_date = st.date_input("Start Date", today - datetime.timedelta(days=365))
    end_date = st.date_input("End Date", today)

    # Fetch stock data
    df = get_stock_data(symbol, start_date, end_date)

    if not df.empty:
        st.subheader(f'Stock Data for {symbol}')
        st.write(df.tail())
        
        # Plot closing price
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(df.index, df['Close'], label='Closing Price', color='blue')
        ax.set_title(f'{symbol} Closing Price')
        ax.set_xlabel('Date')
        ax.set_ylabel('Price')
        ax.legend()
        st.pyplot(fig)
        
        # Plot volume
        fig, ax = plt.subplots(figsize=(10, 3))
        ax.bar(df.index, df['Volume'], label='Volume', color='gray')
        ax.set_title(f'{symbol} Trading Volume')
        ax.set_xlabel('Date')
        ax.set_ylabel('Volume')
        ax.legend()
        st.pyplot(fig)
    else:
        st.warning('No data found. Please check the stock symbol and date range.')

with news_tab:
    st.header("📰 Market News")
    
    # Function to fetch general market news from NewsAPI
    def get_market_news(category):
        API_KEY = "5592f6b9e9a3444da5a0df080a6e60cd"  # Replace with your NewsAPI key
        url = f"https://newsapi.org/v2/top-headlines?category={category}&language=en&apiKey={API_KEY}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json().get('articles', [])
        return []
    
    # Dropdown menu for news categories (capitalized)
    category = st.selectbox("Select News Category", ["Business", "Technology", "General", "Science", "Health"], key="news_category")
    category_lower = category.lower()
    
    news = get_market_news(category_lower)
    if news:
        for article in news:
            st.markdown(f"**[{article['title']}]({article['url']})**")
            st.write(f"Published: {article['publishedAt']}")
            st.write(f"Source: {article['source']['name']}")
            st.write(article['description'])
            st.write("---")
    else:
        st.warning("No recent news found. Make sure the API key is valid.")

st.sidebar.markdown('---')
st.sidebar.write('🔹 Built with Streamlit, yfinance & NewsAPI')