#!/usr/bin/env python3
"""PlusPlus MCP Server - Exposes PlusPlus training catalog as MCP resources"""

import os
import json
import httpx
from typing import Any
from mcp.server import Server
from mcp.types import (
    Resource,
    ResourceTemplate,
    TextContent,
    Tool,
    TextBlock,
    ToolResult,
)
import mcp.types as types

# Configuration
BASE_URL = os.environ.get("PLUSPLUS_BASE_URL", "https://sfdc-bt.plusplus.app")
API_KEY = os.environ.get("PLUSPLUS_API_KEY", "")

if not API_KEY:
    raise ValueError("PLUSPLUS_API_KEY environment variable is required")

server = Server("plusplus")

# HTTP client with auth
def _client():
    return httpx.Client(
        base_url=BASE_URL,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        timeout=10
    )

@server.list_resources()
async def list_resources() -> list[Resource]:
    """List available PlusPlus resources"""
    resources = [
        Resource(
            uri="plusplus://courses",
            name="PlusPlus Courses",
            description="Available training courses from PlusPlus",
            mimeType="application/json",
        ),
        Resource(
            uri="plusplus://events",
            name="PlusPlus Events",
            description="Upcoming training events from PlusPlus",
            mimeType="application/json",
        ),
    ]
    return resources

@server.read_resource()
async def read_resource(uri: str) -> str:
    """Read a PlusPlus resource"""
    if uri == "plusplus://courses":
        return _get_courses()
    elif uri == "plusplus://events":
        return _get_events()
    else:
        raise ValueError(f"Unknown resource: {uri}")

def _get_courses() -> str:
    """Fetch courses from PlusPlus API"""
    try:
        with _client() as client:
            resp = client.get("/api/v2/courses", params={"limit": 100})
            resp.raise_for_status()
            data = resp.json()
            courses = data.get("data", [])
            formatted = []
            for course in courses[:50]:
                formatted.append({
                    "id": course.get("id"),
                    "name": course.get("name"),
                    "description": course.get("description"),
                    "duration": course.get("duration"),
                    "level": course.get("level"),
                    "topics": course.get("topics", []),
                    "url": course.get("url"),
                })
            return json.dumps({"courses": formatted}, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch courses: {str(e)}"})

def _get_events() -> str:
    """Fetch events from PlusPlus API"""
    try:
        with _client() as client:
            resp = client.get("/api/v2/events", params={"limit": 100})
            resp.raise_for_status()
            data = resp.json()
            events = data.get("data", [])
            formatted = []
            for event in events[:50]:
                formatted.append({
                    "id": event.get("id"),
                    "name": event.get("name"),
                    "description": event.get("description"),
                    "date": event.get("date"),
                    "time": event.get("time"),
                    "location": event.get("location"),
                    "capacity": event.get("capacity"),
                    "url": event.get("url"),
                })
            return json.dumps({"events": formatted}, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch events: {str(e)}"})

@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools"""
    return [
        Tool(
            name="search_courses",
            description="Search for training courses by keyword",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (keyword, topic, etc.)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max results to return (default 10)",
                        "default": 10,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="search_events",
            description="Search for upcoming training events",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (topic, location, etc.)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max results to return (default 10)",
                        "default": 10,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_course_details",
            description="Get detailed information about a specific course",
            inputSchema={
                "type": "object",
                "properties": {
                    "course_id": {
                        "type": "string",
                        "description": "The course ID"
                    },
                },
                "required": ["course_id"],
            },
        ),
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> ToolResult:
    """Handle tool calls"""
    if name == "search_courses":
        return _search_courses(arguments.get("query"), arguments.get("limit", 10))
    elif name == "search_events":
        return _search_events(arguments.get("query"), arguments.get("limit", 10))
    elif name == "get_course_details":
        return _get_course_details(arguments.get("course_id"))
    else:
        return ToolResult(
            content=[TextBlock(type="text", text=f"Unknown tool: {name}")],
            isError=True,
        )

def _search_courses(query: str, limit: int) -> ToolResult:
    """Search for courses"""
    try:
        with _client() as client:
            resp = client.get("/api/v2/courses", params={"limit": limit * 2})
            resp.raise_for_status()
            data = resp.json()
            courses = data.get("data", [])

            # Filter by query
            q_lower = query.lower()
            matching = []
            for course in courses:
                name = (course.get("name", "") or "").lower()
                desc = (course.get("description", "") or "").lower()
                if q_lower in name or q_lower in desc:
                    matching.append({
                        "id": course.get("id"),
                        "name": course.get("name"),
                        "description": course.get("description"),
                        "duration": course.get("duration"),
                        "level": course.get("level"),
                        "url": course.get("url"),
                    })

            results = matching[:limit]
            content = json.dumps({"results": results, "count": len(results)}, indent=2)
            return ToolResult(content=[TextBlock(type="text", text=content)])
    except Exception as e:
        return ToolResult(
            content=[TextBlock(type="text", text=f"Error searching courses: {str(e)}")],
            isError=True,
        )

def _search_events(query: str, limit: int) -> ToolResult:
    """Search for events"""
    try:
        with _client() as client:
            resp = client.get("/api/v2/events", params={"limit": limit * 2})
            resp.raise_for_status()
            data = resp.json()
            events = data.get("data", [])

            # Filter by query
            q_lower = query.lower()
            matching = []
            for event in events:
                name = (event.get("name", "") or "").lower()
                desc = (event.get("description", "") or "").lower()
                if q_lower in name or q_lower in desc:
                    matching.append({
                        "id": event.get("id"),
                        "name": event.get("name"),
                        "description": event.get("description"),
                        "date": event.get("date"),
                        "location": event.get("location"),
                        "url": event.get("url"),
                    })

            results = matching[:limit]
            content = json.dumps({"results": results, "count": len(results)}, indent=2)
            return ToolResult(content=[TextBlock(type="text", text=content)])
    except Exception as e:
        return ToolResult(
            content=[TextBlock(type="text", text=f"Error searching events: {str(e)}")],
            isError=True,
        )

def _get_course_details(course_id: str) -> ToolResult:
    """Get course details"""
    try:
        with _client() as client:
            resp = client.get(f"/api/v2/courses/{course_id}")
            resp.raise_for_status()
            course = resp.json()
            content = json.dumps(course, indent=2)
            return ToolResult(content=[TextBlock(type="text", text=content)])
    except Exception as e:
        return ToolResult(
            content=[TextBlock(type="text", text=f"Error fetching course details: {str(e)}")],
            isError=True,
        )

if __name__ == "__main__":
    import asyncio

    async def main():
        async with server:
            print("PlusPlus MCP Server running...")
            await server.run_forever()

    asyncio.run(main())
