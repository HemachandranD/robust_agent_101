import requests, sympy
from fastapi import HTTPException
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import yfinance as yf
from art import text2art

load_dotenv()

mcp = FastMCP(name="hai_mcp_server")

# Model for stock request
class StockRequest(BaseModel):
    symbol: str = "AAPL"

# Model for ASCII art request
class ArtRequest(BaseModel):
    text: str
    font: str = "block"  # Default font; options from pyfiglet/art libs


# Stock Quote
@mcp.tool()
async def get_stock(request: StockRequest):
    try:
        stock = yf.Ticker(request.symbol.upper())
        info = stock.info
        return {
            "symbol": request.symbol,
            "price": info.get("currentPrice", "N/A"),
            "change": info.get("regularMarketChange", "N/A"),
            "volume": info.get("volume", "N/A")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch {request.symbol}: {str(e)}")


# ASCII Art
@mcp.tool()
async def generate_art(request: ArtRequest):
    try:
        art = text2art(request.text, font=request.font)
        return {"art": art}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate art: {str(e)}")


# Web Search
@mcp.tool()
def web_search(query: str):
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


# Math
@mcp.tool()
def calculate(expression: str):
    try:
        result = sympy.sympify(expression).evalf()
        return {"result": float(result)}
    except Exception as e:
        return {"error": f"Calculation failed: {str(e)}"}


if __name__ == "__main__":
    print("[INFO] Starting HAI MCP Servers")
    print("[INFO] Tools: get_stock, generate_art, web_search, calculate")
    mcp.run(transport="stdio")