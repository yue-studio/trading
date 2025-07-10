# 
# A script to try out the APIs from AlphaVantage
# 
import requests
import argparse
from rich.console import Console
from rich.table import Table
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

from config import ALPHAVANTAGE_API_KEY # Get your API key from: https://www.alphavantage.co/

# Install rich: pip install rich

def _make_alpha_vantage_request(function_name, **kwargs):
    """Helper function to make requests to Alpha Vantage API."""
    base_url = "https://www.alphavantage.co/query"
    params = {
        "function": function_name,
        "apikey": ALPHAVANTAGE_API_KEY,
        **kwargs
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        if "Information" in data and "rate limit" in data["Information"].lower():
            print(f"Alpha Vantage API Rate Limit Exceeded: {data["Information"]}")
            return None
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {e}")
        return None

def get_stock_price(symbol: str) -> str | None:
    """Fetches the current stock price for a given symbol."""
    data = _make_alpha_vantage_request("GLOBAL_QUOTE", symbol=symbol)
    if data and "Global Quote" in data and "05. price" in data["Global Quote"]:
        return data["Global Quote"]["05. price"]
    return None

def get_top_gainers_losers() -> dict | None:
    """Fetches top gainers, losers, and most actively traded stocks."""
    return _make_alpha_vantage_request("TOP_GAINERS_LOSERS")

def get_market_news() -> dict | None:
    """Fetches market news and sentiment data."""
    return _make_alpha_vantage_request("NEWS_SENTIMENT")

def get_copper_price() -> dict | None:
    """Fetches global copper price data (monthly interval)."""
    return _make_alpha_vantage_request("COPPER", interval="monthly")

def display_market_news(data):
    console = Console()
    if "feed" in data and data["feed"]:
        news_table = Table(title="Market News & Sentiment", padding=(0, 1, 1, 1))
        news_table.add_column("Title")
        news_table.add_column("Source")
        news_table.add_column("Time Published")
        
        previous_title_words = []
        for article in data["feed"]:
            title = article.get("title", "N/A")
            current_title_words = title.lower().split()[:5]

            if current_title_words == previous_title_words:
                continue # Skip this article if the first 5 words are the same

            previous_title_words = current_title_words

            source = article.get("source", "N/A")
            time_published = article.get("time_published", "N/A")
            url = article.get("url", "N/A")
            
            # Make the title clickable
            clickable_title = f"[link={url}]{title}[/link]"
            news_table.add_row(clickable_title, source, time_published)
        console.print(news_table)
    else:
        console.print("[bold yellow]No market news data available.[/bold yellow]")

def display_gainers_losers_table(data: dict):
    """Displays top gainers, losers, and most actively traded stocks in rich tables."""
    console = Console()

    if data:
        # Top Gainers Table
        if "top_gainers" in data and data["top_gainers"]:
            gainers_table = Table(title="Top Gainers")
            headers = list(data["top_gainers"][0].keys())
            for header in headers:
                gainers_table.add_column(header)
            for gainer in data["top_gainers"]:
                gainers_table.add_row(*[gainer[key] for key in headers])
            console.print(gainers_table)
        else:
            console.print("[bold yellow]No top gainers data available.[/bold yellow]")

        console.print("\n") # Add a newline for separation

        # Top Losers Table
        if "top_losers" in data and data["top_losers"]:
            losers_table = Table(title="Top Losers")
            headers = list(data["top_losers"][0].keys())
            for header in headers:
                losers_table.add_column(header)
            for loser in data["top_losers"]:
                losers_table.add_row(*[loser[key] for key in headers])
            console.print(losers_table)
        else:
            console.print("[bold yellow]No top losers data available.[/bold yellow]")

        # Most Actively Traded Table (Optional, based on API response)
        if "most_actively_traded" in data and data["most_actively_traded"]:
            actively_traded_table = Table(title="Most Actively Traded")
            headers = list(data["most_actively_traded"][0].keys())
            for header in headers:
                actively_traded_table.add_column(header)
            for item in data["most_actively_traded"]:
                actively_traded_table.add_row(*[item[key] for key in headers])
            console.print(actively_traded_table)
        else:
            console.print("[bold yellow]No most actively traded data available.[/bold yellow]")
    else:
        console.print("[bold red]Error: Could not retrieve gainers/losers data.[/bold red]")

def plot_copper_price(data: dict):
    """Plots the global copper price data."""
    if "data" in data:
        dates = [datetime.strptime(item["date"], "%Y-%m-%d") for item in data["data"] if "value" in item and item["value"] != "."]
        prices = [float(item["value"]) for item in data["data"] if "value" in item and item["value"] != "."]

        # Reverse the lists to plot chronologically
        dates.reverse()
        prices.reverse()

        plt.figure(figsize=(12, 6))
        plt.plot(dates, prices, marker='o', linestyle='-', color='b')
        plt.title('Global Copper Price (Monthly)')
        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.grid(True)

        # Format x-axis to show fewer, well-spaced date ticks
        ax = plt.gca()
        ax.xaxis.set_major_locator(mdates.YearLocator(5)) # Show a tick every 5 years
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y')) # Format as Year
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()
    else:
        print("No copper price data to plot.")


def main():
    parser = argparse.ArgumentParser(description="Get stock information, top gainers/losers, or market news.")
    parser.add_argument("-s", "--symbol", type=str, help="Stock ticker symbol (e.g., AAPL)")
    parser.add_argument("-t", "--top", action="store_true", help="Show top gainers and losers")
    parser.add_argument("-n", "--news", action="store_true", help="Show market news and sentiment")
    parser.add_argument("-c", "--copper", action="store_true", help="Get global copper price and plot it")

    args = parser.parse_args()

    executed_action = False

    if args.symbol:
        executed_action = True
        stock_price = get_stock_price(args.symbol)
        if stock_price:
            print(f"Current Stock Price of {args.symbol}: {stock_price}")
        else:
            print(f"Could not retrieve stock price for {args.symbol}. Please check the symbol and your API key.")
    
    if args.top:
        executed_action = True
        data = get_top_gainers_losers()
        display_gainers_losers_table(data)

    if args.news:
        executed_action = True
        news_data = get_market_news()
        display_market_news(news_data)

    if args.copper:
        executed_action = True
        copper_data = get_copper_price()
        if copper_data and "data" in copper_data:
            plot_copper_price(copper_data)
        else:
            print("Could not retrieve copper price data.")

    if not executed_action:
        print("Please provide either a stock symbol (-s), use the --top (-t) option, use the --news (-n) option, or use the --copper (-c) option.")

if __name__ == "__main__":
    main()
