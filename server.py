from mcp.server.fastmcp import FastMCP

# Create the MCP Server
mcp = FastMCP("Math Specialist")

# Define tools
@mcp.tool()
def add_numbers(a: int, b: int) -> int:
    """Add two numbers together. Returns the sum."""
    return a + b

@mcp.tool()
def multiply_numbers(a: int, b: int) -> int:
    """Multiply two numbers. Returns the product."""
    return a * b

# 3. Run the server
if __name__ == "__main__":
    mcp.run()