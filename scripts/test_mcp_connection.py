#!/usr/bin/env python3
"""
Test MCP Connection Script
Attempts to connect to NotebookLM MCP server using local Chrome Profile.
"""

import os
import sys
import asyncio
import json

# Add module path if running directly
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError:
    print("Error: 'mcp' library not installed. Please run 'uv pip install mcp'.")
    sys.exit(1)


async def test_connection():
    print("🚀 Starting MCP Connection Test...")
    print("Target: NotebookLM (via Headless Chrome Profile)")
    
    # Configuration: Rely on credentials saved by 'scripts/run_auth.sh'
    # env = os.environ.copy() 
    # env["GOOGLE_CHROME_PROFILE"] = "Default" <--- REMOVED due to instability
    
    server_params = StdioServerParameters(
        command="uv",
        args=["tool", "run", "notebooklm-mcp", "server"],
        env=os.environ.copy()
    )

    print(f"Executing: {' '.join([server_params.command] + server_params.args)}")
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                print("✅ MCP Client initialized.")
                await session.initialize()
                print("✅ Session initialized.")
                
                # List tools to verify capabilities
                print("🔍 Querying available tools...")
                tools = await session.list_tools()
                
                tool_names = [t.name for t in tools.tools]
                print(f"📦 Found {len(tool_names)} tools: {', '.join(tool_names)}")
                
                if not tool_names:
                    print("⚠️  Warning: No tools returned. Server might be running but not authenticated.")
                    return False
                
                if "notebook_create" in tool_names:
                    print("\n🎉 SUCCESS! Connected to NotebookLM successfully using Chrome Profile.")
                    return True
                else:
                    print("\n⚠️  Tools found, but 'notebook_create' is missing. Strange.")
                    return False

    except Exception as e:
        print(f"\n❌ Connection Failed.")
        print(f"Error details: {e}")
        print("\nDiagnostics:")
        print("1. Ensure Chrome is closed (or ensure standard profile is accessible).")
        print("2. 'notebooklm-mcp-server' might require manual cookie login if Chrome profile is locked.")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(test_connection())
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nTest cancelled.")
