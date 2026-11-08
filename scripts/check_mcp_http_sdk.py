"""Independent official SDK over real MCP HTTP, against fixture data only."""
import argparse,asyncio,json,os
from importlib.metadata import version
import httpx2
from mcp import Client
from mcp.client.streamable_http import streamable_http_client

async def check(url):
    headers={"X-API-Key":os.environ["KONTEXT_HTTP_TEST_KEY"]} if os.environ.get("KONTEXT_HTTP_TEST_KEY") else {}
    async with httpx2.AsyncClient(headers=headers,timeout=30) as http:
        async with Client(streamable_http_client(url,http_client=http)) as client:
            tools=await client.list_tools()
            result=await client.call_tool("query_ai_system_compliance",{"system_id":"SYS-CHAT-004"})
            assert not result.is_error
            assert json.loads(result.content[0].text)["system_id"]=="SYS-CHAT-004"
            return {"status":"PASS","sdk_version":version("mcp"),"protocol":client.protocol_version,"transport":"Streamable HTTP (stateless JSON)","tools":len(tools.tools),"public_read":True}

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--url",required=True);args=parser.parse_args()
    print(json.dumps(asyncio.run(asyncio.wait_for(check(args.url),timeout=45))))
