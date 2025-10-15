import requests
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import yfinance as yf
from art import text2art

load_dotenv()

mcp = FastMCP(name="hai_mcp_server")

# Stock Quote - accepts plain symbol string
@mcp.tool()
async def get_stock(symbol: str = "AAPL"):
    """Get real-time stock quotes for a given symbol"""
    try:
        stock = yf.Ticker(symbol.upper())
        info = stock.info
        return {
            "symbol": symbol,
            "price": info.get("currentPrice", "N/A"),
            "change": info.get("regularMarketChange", "N/A"),
            "volume": info.get("volume", "N/A"),
            "company": info.get("longName", "N/A")
        }
    except Exception as e:
        return {"error": f"Failed to fetch {symbol}: {str(e)}"}


# ASCII Art - accepts plain text string
@mcp.tool()
async def generate_art(text: str, font: str = "block"):
    """Generate ASCII art from text"""
    try:
        art = text2art(text, font=font)
        return {"art": art}
    except Exception as e:
        return {"error": f"Failed to generate art: {str(e)}"}


# Web Search
@mcp.tool()
async def web_search(query: str):
    """Search the web using DuckDuckGo"""
    try:
        url = f"https://duckduckgo.com/html/?q={query}"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        results = []
        for result in soup.find_all("a", class_="result__a", limit=3):
            results.append({"title": result.text, "url": result["href"]})
        return results if results else {"error": "No results found"}
    except Exception as e:
        return {"error": f"Search failed: {str(e)}"}


# Math Calculator
@mcp.tool()
async def calculate(expression: str):
    """Evaluate mathematical expressions"""
    try:
        import sympy
        result = sympy.sympify(expression).evalf()
        return {"result": float(result), "expression": expression}
    except Exception as e:
        return {"error": f"Calculation failed: {str(e)}"}


if __name__ == "__main__":
    print("[INFO] Starting HAI MCP Server")
    print("[INFO] Tools: get_stock, generate_art, web_search, calculate")
    mcp.run(transport="stdio")