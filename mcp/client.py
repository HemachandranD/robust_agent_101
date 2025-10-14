import asyncio
import json
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPClient:
    def __init__(self):
        self.session = None
        self.exit_stack = None
        self.available_tools = []
        
    async def connect(self):
        """Connect to the MCP server and initialize session"""
        # Server parameters from config
        server_params = StdioServerParameters(
            command="python",
            args=["mcp/server.py"],
            env=None
        )
        
        # Create context managers
        self.exit_stack = AsyncExitStack()
        
        # Connect to server via stdio
        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        read, write = stdio_transport
        
        # Create session
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(read, write)
        )
        
        # Initialize the connection
        await self.session.initialize()
        
        print("[INFO] Connected to MCP Server")
        
    async def list_tools(self):
        """List all available tools from the server"""
        if not self.session:
            raise RuntimeError("Not connected. Call connect() first.")
        
        response = await self.session.list_tools()
        self.available_tools = response.tools
        
        print(f"\n[INFO] Available Tools ({len(self.available_tools)}):")
        for tool in self.available_tools:
            print(f"  - {tool.name}: {tool.description}")
        
        return self.available_tools
    
    async def call_tool(self, tool_name: str, arguments: dict = None):
        """Call a specific tool with given arguments"""
        if not self.session:
            raise RuntimeError("Not connected. Call connect() first.")
        
        if arguments is None:
            arguments = {}
        
        print(f"\n[INFO] Calling tool: {tool_name}")
        print(f"[INFO] Arguments: {json.dumps(arguments, indent=2)}")
        
        result = await self.session.call_tool(tool_name, arguments=arguments)
        
        print(f"[INFO] Result:")
        print(json.dumps(result.content, indent=2))
        
        return result
    
    async def close(self):
        """Close the connection"""
        if self.exit_stack:
            await self.exit_stack.aclose()
            print("\n[INFO] Disconnected from MCP Server")


async def demo():
    """Demo usage of the MCP client"""
    client = MCPClient()
    
    try:
        # Connect to server
        await client.connect()
        
        # List available tools
        await client.list_tools()
        
        # Example 1: Calculate
        await client.call_tool("calculate", {"expression": "2 + 2 * 3"})
        
        # Example 2: Get stock quote
        await client.call_tool("get_stock", {"symbol": "AAPL"})
        
        # Example 3: Generate ASCII art
        await client.call_tool("generate_art", {"text": "MCP", "font": "block"})
        
        # Example 4: Web search
        await client.call_tool("web_search", {"query": "Python MCP protocol"})
        
    finally:
        await client.close()


if __name__ == "__main__":
    print("=" * 60)
    print("MCP Client Demo")
    print("=" * 60)
    asyncio.run(demo())

