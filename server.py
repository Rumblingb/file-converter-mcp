#!/usr/bin/env python3
"""File Converter MCP — Convert between CSV, JSON, XML, YAML, Markdown, and HTML."""

import json, csv, io, re, xml.etree.ElementTree as ET
from mcp.server import Server, stdio_server

server = Server("file-converter-mcp")

def _try_json_parse(text):
    try: return json.loads(text)
    except: return None

def _try_yaml_parse(text):
    try:
        import yaml
        return yaml.safe_load(text)
    except ImportError:
        return None

def _to_json(data, indent=2):
    return json.dumps(data, indent=indent, default=str)

def _to_yaml(data):
    try:
        import yaml
        return yaml.dump(data, default_flow_style=False)
    except ImportError:
        return "yaml library not installed. Install with: pip install pyyaml"

def _to_csv(data):
    if isinstance(data, list) and data and isinstance(data[0], dict):
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        return output.getvalue()
    elif isinstance(data, list):
        output = io.StringIO()
        writer = csv.writer(output)
        for row in data:
            writer.writerow(row if isinstance(row, (list, tuple)) else [row])
        return output.getvalue()
    return "CSV conversion requires a list of dicts or lists"

def _to_markdown(data):
    """Convert data to markdown table."""
    if isinstance(data, list) and data and isinstance(data[0], dict):
        headers = list(data[0].keys())
        rows = [[str(r.get(h, "")) for h in headers] for r in data]
        md = "| " + " | ".join(headers) + " |\n"
        md += "| " + " | ".join(["---"] * len(headers)) + " |\n"
        for row in rows:
            md += "| " + " | ".join(row) + " |\n"
        return md
    return _to_json(data)

@server.tool(
    name="convert_to_json",
    description="Convert CSV, YAML, XML, or Markdown table to JSON.",
    input_schema={
        "type": "object",
        "properties": {
            "input_text": {"type": "string", "description": "Input text to convert"},
            "input_format": {"type": "string", "enum": ["csv", "yaml", "xml", "markdown", "auto"], "default": "auto"}
        },
        "required": ["input_text"]
    }
)
async def convert_to_json(input_text: str, input_format: str = "auto") -> str:
    try:
        data = None
        if input_format in ("auto", "json"):
            data = _try_json_parse(input_text)
        if data is None and input_format in ("auto", "yaml"):
            data = _try_yaml_parse(input_text)
        if data is None and input_format in ("auto", "csv"):
            reader = csv.DictReader(io.StringIO(input_text))
            data = list(reader)
        if data is None:
            return json.dumps({"error": "Could not parse input in any supported format", "isError": True}, indent=2)
        
        return json.dumps({"result": data, "format": "json"}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "isError": True}, indent=2)

@server.tool(
    name="convert_to_csv",
    description="Convert JSON or YAML to CSV.",
    input_schema={
        "type": "object",
        "properties": {
            "input_text": {"type": "string", "description": "JSON or YAML input"},
            "input_format": {"type": "string", "enum": ["json", "yaml", "auto"], "default": "auto"}
        },
        "required": ["input_text"]
    }
)
async def convert_to_csv(input_text: str, input_format: str = "auto") -> str:
    try:
        data = _try_json_parse(input_text) if input_format in ("auto", "json") else None
        if data is None:
            data = _try_yaml_parse(input_text)
        if data is None:
            return json.dumps({"error": "Could not parse input", "isError": True}, indent=2)
        
        csv_out = _to_csv(data)
        return json.dumps({"result": csv_out, "format": "csv", "rows": len(data) if isinstance(data, list) else 0}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "isError": True}, indent=2)

@server.tool(
    name="convert_to_yaml",
    description="Convert JSON or CSV to YAML.",
    input_schema={
        "type": "object",
        "properties": {
            "input_text": {"type": "string", "description": "JSON or CSV input"},
            "input_format": {"type": "string", "enum": ["json", "csv", "auto"], "default": "auto"}
        },
        "required": ["input_text"]
    }
)
async def convert_to_yaml(input_text: str, input_format: str = "auto") -> str:
    try:
        data = _try_json_parse(input_text) if input_format in ("auto", "json") else None
        if data is None and input_format in ("auto", "csv"):
            reader = csv.DictReader(io.StringIO(input_text))
            data = list(reader)
        if data is None:
            return json.dumps({"error": "Could not parse input", "isError": True}, indent=2)
        
        yaml_out = _to_yaml(data)
        return json.dumps({"result": yaml_out, "format": "yaml"}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "isError": True}, indent=2)

@server.tool(
    name="convert_to_markdown",
    description="Convert JSON, CSV, or YAML to Markdown table.",
    input_schema={
        "type": "object",
        "properties": {
            "input_text": {"type": "string", "description": "Input data"},
            "input_format": {"type": "string", "enum": ["json", "csv", "yaml", "auto"], "default": "auto"}
        },
        "required": ["input_text"]
    }
)
async def convert_to_markdown(input_text: str, input_format: str = "auto") -> str:
    try:
        data = None
        if input_format in ("auto", "json"):
            data = _try_json_parse(input_text)
        if data is None and input_format in ("auto", "yaml"):
            data = _try_yaml_parse(input_text)
        if data is None and input_format in ("auto", "csv"):
            reader = csv.DictReader(io.StringIO(input_text))
            data = list(reader)
        if data is None:
            return json.dumps({"error": "Could not parse input", "isError": True}, indent=2)
        
        md = _to_markdown(data)
        return json.dumps({"result": md, "format": "markdown"}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "isError": True}, indent=2)

def main():
    import anyio
    async def run():
        async with stdio_server() as streams:
            await server.run(streams[0], streams[1], server.create_initialization_options())
    anyio.run(run)

if __name__ == "__main__":
    main()
