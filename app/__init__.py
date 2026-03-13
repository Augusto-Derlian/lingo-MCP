from fastmcp import FastMCP

mcp = FastMCP("LingoRate")

# Ensure database is initialized and tools are registered when importing the package
from .database import init_db
from . import tools  # noqa: F401 (register MCP tools via import)

init_db()