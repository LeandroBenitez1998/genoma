"""
Genoma MCP Server — 4 telemetry ingestion tools for AI agents.

Supports stdio transport.
Run:
    python3 -m backend.mcp_server
"""

from __future__ import annotations

import asyncio
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    TextContent,
    Tool,
    CallToolResult,
    ListToolsResult,
)

from backend.promethean.models import CanonicalRun, TraceRecord
from backend.promethean.trace_ingestion import get_ingestor
from backend.storage.run_store import RunStore

server = Server(
    name="genoma",
    instructions=(
        "Push telemetry from your running session to Genoma. "
        "Use ingest_run for full canonical run events, ingest_trace for lightweight "
        "trace records, query_runs to retrieve past runs, and get_agent_stats for "
        "per-agent performance statistics."
    ),
)


@server.list_tools()
async def list_tools() -> ListToolsResult:
    """Advertise all 4 MCP tools."""
    return ListToolsResult(
        tools=[
            Tool(
                name="ingest_run",
                description="Push a canonical run event to Genoma's telemetry store.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "run_id": {"type": "string"},
                        "agent_name": {"type": "string"},
                        "started_at": {"type": "string"},
                        "task_name": {"type": "string"},
                        "outcome": {"type": "string"},
                        "collector": {"type": "string", "default": "mcp-native"},
                        "agent_version": {"type": "string"},
                        "provider": {"type": "string"},
                        "model": {"type": "string"},
                        "repo": {"type": "string"},
                        "session_id": {"type": "string"},
                        "ended_at": {"type": "string"},
                        "tool_calls": {"type": "array"},
                        "files_touched": {"type": "array"},
                        "metrics": {"type": "object"},
                        "errors": {"type": "array"},
                        "context": {"type": "object"},
                        "resolution": {"type": "string"},
                    },
                    "required": ["run_id", "agent_name", "started_at", "task_name", "outcome"],
                },
            ),
            Tool(
                name="ingest_trace",
                description="Push a lightweight TraceRecord to Genoma.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "agent": {"type": "string"},
                        "agent_version": {"type": "string"},
                        "timestamp": {"type": "string"},
                        "task": {"type": "string"},
                        "outcome": {"type": "string"},
                        "error_signature": {"type": "string"},
                        "context": {"type": "object"},
                        "resolution": {"type": "string"},
                    },
                    "required": ["agent", "agent_version", "timestamp", "task", "outcome"],
                },
            ),
            Tool(
                name="query_runs",
                description="Query past runs from Genoma's telemetry store.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "agent_name": {"type": "string"},
                        "outcome": {"type": "string"},
                        "repo": {"type": "string"},
                        "since": {"type": "string"},
                        "until": {"type": "string"},
                        "limit": {"type": "integer", "default": 20},
                    },
                },
            ),
            Tool(
                name="get_agent_stats",
                description="Get performance statistics for one or all agents.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "agent_name": {"type": "string"},
                    },
                },
            ),
        ]
    )


@server.call_tool()
async def handle_tool_call(tool_name: str, arguments: dict[str, Any]) -> CallToolResult:
    """Route tool calls to handlers."""
    if tool_name == "ingest_run":
        return await ingest_run(arguments)
    elif tool_name == "ingest_trace":
        return await ingest_trace(arguments)
    elif tool_name == "query_runs":
        return await query_runs(arguments)
    elif tool_name == "get_agent_stats":
        return await get_agent_stats(arguments)
    else:
        raise ValueError(f"Unknown tool: {tool_name}")


async def ingest_run(args: dict[str, Any]) -> CallToolResult:
    """Push a canonical run event to Genoma's telemetry store."""
    data = {
        "run_id": args["run_id"],
        "agent_name": args["agent_name"],
        "collector": args.get("collector", "mcp-native"),
        "started_at": args["started_at"],
        "task_name": args["task_name"],
        "outcome": args["outcome"],
        "agent_version": args.get("agent_version"),
        "provider": args.get("provider"),
        "model": args.get("model"),
        "repo": args.get("repo"),
        "session_id": args.get("session_id"),
        "ended_at": args.get("ended_at"),
        "tool_calls": args.get("tool_calls", []),
        "files_touched": args.get("files_touched", []),
        "metrics": args.get("metrics"),
        "errors": args.get("errors", []),
        "context": args.get("context", {}),
        "resolution": args.get("resolution"),
    }
    run = CanonicalRun.from_dict(data)
    is_new = RunStore().upsert_run(run)
    result = {
        "status": "inserted" if is_new else "updated",
        "run_id": run.run_id,
    }
    return CallToolResult(
        content=[TextContent(type="text", text=str(result))],
        isError=False,
    )


async def ingest_trace(args: dict[str, Any]) -> CallToolResult:
    """Push a lightweight TraceRecord to Genoma."""
    trace = TraceRecord(
        agent=args["agent"],
        agent_version=args["agent_version"],
        timestamp=args["timestamp"],
        task=args["task"],
        outcome=args["outcome"],
        error_signature=args.get("error_signature"),
        context=args.get("context", {}),
        resolution=args.get("resolution"),
    )
    get_ingestor().ingest(trace)
    canonical = trace.to_canonical()
    RunStore().upsert_run(canonical)
    result = {
        "status": "ingested",
        "trace_id": trace.trace_id,
        "run_id": canonical.run_id,
    }
    return CallToolResult(
        content=[TextContent(type="text", text=str(result))],
        isError=False,
    )


async def query_runs(args: dict[str, Any]) -> CallToolResult:
    """Query past runs from Genoma's telemetry store."""
    limit = min(args.get("limit", 20), 100)
    runs = RunStore().list_runs(
        agent_name=args.get("agent_name"),
        outcome=args.get("outcome"),
        repo=args.get("repo"),
        since=args.get("since"),
        until=args.get("until"),
        limit=limit,
        offset=0,
    )
    lightweight = [
        {
            "run_id": r.run_id,
            "agent_name": r.agent_name,
            "agent_version": r.agent_version,
            "collector": r.collector,
            "started_at": r.started_at,
            "ended_at": r.ended_at,
            "task_name": r.task_name,
            "outcome": r.outcome,
            "provider": r.provider,
            "model": r.model,
            "repo": r.repo,
            "session_id": r.session_id,
            "resolution": r.resolution,
        }
        for r in runs
    ]
    result = {"runs": lightweight, "count": len(lightweight)}
    return CallToolResult(
        content=[TextContent(type="text", text=str(result))],
        isError=False,
    )


async def get_agent_stats(args: dict[str, Any]) -> CallToolResult:
    """Get performance statistics for one or all agents."""
    summary = RunStore().get_agent_summary()
    agent_name = args.get("agent_name")
    if agent_name:
        summary = [s for s in summary if s.get("agent_name") == agent_name]
    result = {"agents": summary}
    return CallToolResult(
        content=[TextContent(type="text", text=str(result))],
        isError=False,
    )


async def main() -> None:
    """Start MCP server with stdio transport."""
    async with stdio_server(server) as (read_stream, write_stream):
        await read_stream.read()


if __name__ == "__main__":
    asyncio.run(main())
