"""Tests for backend.mcp_server MCP server."""

from __future__ import annotations

import asyncio

from backend.mcp_server import server, handle_tool_call
from backend.storage.run_store import RunStore


def test_server_imports():
    """Server should import successfully."""
    assert server is not None
    assert server.name == "genoma"


def test_server_has_instructions():
    """Server should have proper instructions."""
    assert "ingest_run" in server.instructions
    assert "ingest_trace" in server.instructions
    assert "query_runs" in server.instructions
    assert "get_agent_stats" in server.instructions


def test_ingest_run_minimal():
    """ingest_run should accept minimal required fields."""
    async def run_test():
        result = await handle_tool_call(
            "ingest_run",
            {
                "run_id": "test-001",
                "agent_name": "test-agent",
                "started_at": "2026-05-19T00:00:00Z",
                "task_name": "test-task",
                "outcome": "success",
            },
        )
        assert result.isError is False
        assert "inserted" in result.content[0].text or "updated" in result.content[0].text
        assert "test-001" in result.content[0].text

    asyncio.run(run_test())


def test_ingest_run_with_collector():
    """ingest_run should set collector='mcp-native' by default."""
    async def run_test():
        result = await handle_tool_call(
            "ingest_run",
            {
                "run_id": "test-002",
                "agent_name": "test",
                "started_at": "2026-05-19T00:00:00Z",
                "task_name": "test",
                "outcome": "success",
            },
        )
        assert result.isError is False
        run = RunStore().get_run("test-002")
        assert run.collector == "mcp-native"

    asyncio.run(run_test())


def test_ingest_trace():
    """ingest_trace should accept required fields."""
    async def run_test():
        result = await handle_tool_call(
            "ingest_trace",
            {
                "agent": "test-agent",
                "agent_version": "1.0.0",
                "timestamp": "2026-05-19T00:00:00Z",
                "task": "test-task",
                "outcome": "success",
            },
        )
        assert result.isError is False
        assert "ingested" in result.content[0].text

    asyncio.run(run_test())


def test_query_runs():
    """query_runs should work on populated store."""
    async def run_test():
        result = await handle_tool_call("query_runs", {})
        assert result.isError is False
        content = result.content[0].text
        assert "count" in content

    asyncio.run(run_test())


def test_get_agent_stats():
    """get_agent_stats should return agent list."""
    async def run_test():
        result = await handle_tool_call("get_agent_stats", {})
        assert result.isError is False
        content = result.content[0].text
        assert "agents" in content

    asyncio.run(run_test())


if __name__ == "__main__":
    test_server_imports()
    test_server_has_instructions()
    test_ingest_run_minimal()
    test_ingest_run_with_collector()
    test_ingest_trace()
    test_query_runs()
    test_get_agent_stats()
    print("✓ All tests passed")
