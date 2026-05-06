"""
AGenNext Protocols - AG-UI (Agent-User Interaction Protocol)
====================================================
Standardized SSE streaming for agent-user communication.

Usage:
    from agennext.agui import AGUIStream, TextMessage, ToolCall, RunStarted
    
    async with AGUIStream("http://agent:8000") as stream:
        async for event in stream.events():
            if isinstance(event, TextMessage):
                print(event.content)
            elif isinstance(event, ToolCall):
                print(f"Calling tool: {event.name}")
"""

import asyncio
import json
import sseclient
from typing import AsyncIterator, Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod

__version__ = "0.1.0"

# Try to use ag-ui-protocol if available
try:
    from ag_ui_protocol.core import TextMessageContent, ToolCallStart, ToolCallResult
    AGUI_SDK_AVAILABLE = True
except ImportError:
    AGUI_SDK_AVAILABLE = False


class EventType(Enum):
    """AG-UI event types."""
    RUN_STARTED = "RUN_STARTED"
    RUN_FINISHED = "RUN_FINISHED"
    TOOL_CALL_START = "TOOL_CALL_START"
    TOOL_CALL_END = "TOOL_CALL_END"
    TOOL_CALL_RESULT = "TOOL_CALL_RESULT"
    TEXT_MESSAGE_CONTENT = "TEXT_MESSAGE_CONTENT"
    INPUT_REQUIRED = "INPUT_REQUIRED"
    ERROR = "ERROR"


@dataclass
class AGUIEvent:
    """Base AG-UI event."""
    type: EventType
    data: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return {"type": self.type.value, **self.data}


@dataclass
class TextMessage(AGUIEvent):
    """Text message content."""
    content: str
    
    def __init__(self, content: str):
        super().__init__(EventType.TEXT_MESSAGE_CONTENT, {"content": content})
        self.content = content


@dataclass
class ToolCall(AGUIEvent):
    """Tool call started."""
    tool_name: str
    tool_args: Dict[str, Any]
    
    def __init__(self, name: str, args: Dict[str, Any]):
        super().__init__(EventType.TOOL_CALL_START, {"toolCallName": name, "toolCallArguments": args})
        self.tool_name = name
        self.tool_args = args


@dataclass
class ToolCallResult(AGUIEvent):
    """Tool call result."""
    tool_name: str
    result: str
    
    def __init__(self, name: str, result: str):
        super().__init__(EventType.TOOL_CALL_RESULT, {"toolCallName": name, "content": result})
        self.tool_name = name
        self.result = result


@dataclass
class RunStarted(AGUIEvent):
    """Run started event."""
    def __init__(self):
        super().__init__(EventType.RUN_STARTED, {})


@dataclass
class RunFinished(AGUIEvent):
    """Run finished event."""
    def __init__(self):
        super().__init__(EventType.RUN_FINISHED, {})


@dataclass
class InputRequired(AGUIEvent):
    """Input required from user."""
    prompt: str
    
    def __init__(self, prompt: str):
        super().__init__(EventType.INPUT_REQUIRED, {"prompt": prompt})
        self.prompt = prompt


@dataclass
class Error(AGUIEvent):
    """Error event."""
    message: str
    code: Optional[str] = None
    
    def __init__(self, message: str, code: Optional[str] = None):
        super().__init__(EventType.ERROR, {"message": message, "code": code})
        self.message = message


class AGUIStream:
    """AG-UI SSE Stream Client."""
    
    def __init__(self, url: str, session_id: Optional[str] = None):
        self.url = url.rstrip("/")
        self.session_id = session_id
        self._http = None
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        if self._http:
            await self._http.aclose()
    
    def parse_event(self, data: str) -> Optional[AGUIEvent]:
        """Parse SSE event data into AG-UI event."""
        try:
            event_data = json.loads(data) if data else {}
        except json.JSONDecodeError:
            event_data = {"raw": data}
        
        event_type = event_data.get("type", "")
        
        if event_type == EventType.RUN_STARTED.value:
            return RunStarted()
        elif event_type == EventType.RUN_FINISHED.value:
            return RunFinished()
        elif event_type == EventType.TEXT_MESSAGE_CONTENT.value:
            return TextMessage(event_data.get("content", ""))
        elif event_type == EventType.TOOL_CALL_START.value:
            return ToolCall(
                event_data.get("toolCallName", ""),
                event_data.get("toolCallArguments", {}),
            )
        elif event_type == EventType.TOOL_CALL_RESULT.value:
            return ToolCallResult(
                event_data.get("toolCallName", ""),
                event_data.get("content", ""),
            )
        elif event_type == EventType.INPUT_REQUIRED.value:
            return InputRequired(event_data.get("prompt", ""))
        elif event_type == EventType.ERROR.value:
            return Error(
                event_data.get("message", ""),
                event_data.get("code"),
            )
        return None
    
    async def events(self) -> AsyncIterator[AGUIEvent]:
        """Stream events from agent."""
        self._http = asyncio.AsyncClient()
        
        # Use SSE endpoint
        sse_url = f"{self.url}/run_sse"
        
        async with self._http.stream("POST", sse_url) as resp:
            resp.raise_for_status()
            
            # Parse SSE
            response = resp.encoding = "utf-8"
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]  # Remove "data: " prefix
                    if data.strip():
                        event = self.parse_event(data)
                        if event:
                            yield event


class AGUIServer:
    """Simple AG-UI Server for FastAPI."""
    
    def __init__(self, agent_fn: Callable):
        self.agent_fn = agent_fn
    
    async def stream_events(self, messages) -> AsyncIterator[AGUIEvent]:
        """Stream events from agent function."""
        yield RunStarted()
        
        try:
            async for chunk in self.agent_fn(messages):
                if isinstance(chunk, str):
                    yield TextMessage(chunk)
                elif isinstance(chunk, dict):
                    if "tool" in chunk:
                        yield ToolCall(chunk.get("tool"), chunk.get("args", {}))
                    elif "result" in chunk:
                        yield ToolCallResult(chunk.get("tool"), chunk.get("result"))
        except Exception as e:
            yield Error(str(e))
        finally:
            yield RunFinished()


__all__ = [
    "AGUIEvent",
    "AGUIStream", 
    "AGUIServer",
    "EventType",
    "TextMessage",
    "ToolCall",
    "ToolCallResult",
    "RunStarted",
    "RunFinished",
    "InputRequired",
    "Error",
    "__version__",
]