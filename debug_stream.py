
import os
import asyncio
from langchain_core.messages import HumanMessage, AIMessageChunk, ToolMessage
from src.agent.react_agent import graph

# Mock env if needed, but it should be in .env or system env
if not os.environ.get("DEEPSEEK_API_KEY"):
    print("Warning: DEEPSEEK_API_KEY not set")

def test_stream():
    print("Starting stream test...")
    # Ask for time to trigger tool
    user_input = "What time is it?"
    inputs = {"messages": [HumanMessage(content=user_input)]}
    
    try:
        for chunk, metadata in graph.stream(inputs, stream_mode="messages"):
            # print(f"Chunk Type: {type(chunk)}")
            if isinstance(chunk, AIMessageChunk):
                content = chunk.content
                if content:
                    print(f"AI Content: {content!r}")
                if chunk.tool_call_chunks:
                    print(f"AI Tool Call: {chunk.tool_call_chunks}")
            elif isinstance(chunk, ToolMessage):
                print(f"Tool Output: {chunk.content[:50]!r}...")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_stream()
