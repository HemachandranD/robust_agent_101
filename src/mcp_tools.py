# src/mcp_tools.py
import asyncio
from langchain_core.tools import Tool
from agent_mcp.client import MCPClient
from pydantic import BaseModel, Field

mcp_client = MCPClient()
_event_loop = None

def get_or_create_event_loop():
    """Get or create a persistent event loop"""
    global _event_loop
    if _event_loop is None or _event_loop.is_closed():
        _event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_event_loop)
    return _event_loop

def sync_mcp_call(tool_name: str, args: dict, timeout: int = 10):
    """Synchronous wrapper for async MCP tool calls with timeout and persistent event loop"""
    async def _call():
        try:
            if not mcp_client.session:
                await mcp_client.connect()
                await mcp_client.list_tools()
            result = await mcp_client.call_tool(tool_name, args)
            if hasattr(result, 'content') and result.content:
                return result.content[0].text if hasattr(result.content[0], 'text') else str(result.content)
            return str(result)
        except asyncio.TimeoutError:
            return f"⚠️ Error: {tool_name} timed out after {timeout} seconds"
        except Exception as e:
            return f"⚠️ Error calling {tool_name}: {str(e)}"
    
    try:
        # Use persistent event loop instead of asyncio.run()
        loop = get_or_create_event_loop()
        return loop.run_until_complete(asyncio.wait_for(_call(), timeout=timeout))
    except asyncio.TimeoutError:
        return f"⚠️ Error: {tool_name} timed out after {timeout} seconds"
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

# Define input schemas for tools
class StockInput(BaseModel):
    symbol: str = Field(description="Stock ticker symbol, e.g., 'AAPL', 'TSLA', 'GOOGL'")

class WebSearchInput(BaseModel):
    query: str = Field(description="Search query string")

class ArtInput(BaseModel):
    text: str = Field(description="Text to convert to ASCII art")


# Tool wrapper functions that accept the schema objects
def get_stock_tool(symbol: str) -> str:
    """Get real-time stock quotes for a given ticker symbol"""
    return sync_mcp_call("get_stock", {"symbol": symbol}, timeout=15)

def web_search_tool(query: str) -> str:
    """Search the web using DuckDuckGo"""
    return sync_mcp_call("web_search", {"query": query}, timeout=20)

def generate_art_tool(text: str) -> str:
    """Generate ASCII art from text"""
    return sync_mcp_call("generate_art", {"text": text, "font": "block"}, timeout=10)


# MCP-based tools with explicit schemas
from langchain_core.tools import StructuredTool

mcp_tools = [
    StructuredTool(
        name="StockQuote",
        func=get_stock_tool,
        description="Get real-time stock quotes. Provide a stock ticker symbol like 'AAPL' or 'TSLA'.",
        args_schema=StockInput
    ),
    StructuredTool(
        name="WebSearch",
        func=web_search_tool,
        description="Search the web using DuckDuckGo. Provide a search query.",
        args_schema=WebSearchInput
    ),
    StructuredTool(
        name="ASCIIArt",
        func=generate_art_tool,
        description="Generate ASCII art from text. Provide the text to convert.",
        args_schema=ArtInput
    )
]