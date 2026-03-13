from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
import uvicorn

from app import mcp

if __name__ == "__main__":
    # 1. Create the MCP app with CORS middleware included
    # This is the built-in way FastMCP handles web integrations
    mcp_app = mcp.http_app(
        transport="sse",
        middleware=[
            Middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_methods=["*"],
                allow_headers=["*"],
            )
        ]
    )

    # 2. Start the server using the mcp_app we just created
    print("🚀 LingoRate Server starting on http://127.0.0.1:3006")
    uvicorn.run(mcp_app, host="127.0.0.1", port=3006)

# if __name__ == "__main__":
#     # Change from http_app/uvicorn to the standard stdio run command
#     mcp.run(transport="stdio")