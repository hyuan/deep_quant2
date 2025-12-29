# MCP Server Integration Guide

This guide explains how to use My Quant V2 as an MCP (Model Context Protocol) server, enabling AI assistants like Claude to help you create and validate trading strategies through natural conversation.

## Overview

The MCP server exposes the following capabilities:

### Tools
| Tool | Description |
|------|-------------|
| `list_strategies` | List all available strategy definitions |
| `get_strategy` | Get a strategy's YAML definition |
| `save_strategy` | Create or update a strategy |
| `validate_strategy` | Validate strategy YAML without saving |
| `run_backtest` | Start an async backtest job |
| `get_job_status` | Check backtest job status and results |
| `list_jobs` | List recent backtest jobs |
| `fetch_market_data` | Download historical price data |
| `list_indicators` | List available technical indicators |
| `list_runtime_configs` | List example runtime configurations |
| `get_runtime_config` | Get a specific runtime config |

### Resources
| Resource URI | Description |
|--------------|-------------|
| `strategy://schema` | YAML schema documentation for strategies |
| `strategy://example` | Example strategy definition |
| `indicator://list` | Documentation for available indicators |

## Installation

### Option 1: Install from source (Development)

```bash
cd /path/to/my_quant_v2
pip install -e ".[dev]"
```

### Option 2: Install with pipx (Isolated)

```bash
pipx install /path/to/my_quant_v2
```

## Claude Desktop Configuration

Add the following to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**Linux**: `~/.config/Claude/claude_desktop_config.json`

### If installed with pip/pipx:

```json
{
  "mcpServers": {
    "my-quant-v2": {
      "command": "my-quant-v2-mcp"
    }
  }
}
```

### If running from source:

```json
{
  "mcpServers": {
    "my-quant-v2": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/absolute/path/to/my_quant_v2"
    }
  }
}
```

### Using uv (recommended for development):

```json
{
  "mcpServers": {
    "my-quant-v2": {
      "command": "uv",
      "args": ["run", "--directory", "/absolute/path/to/my_quant_v2", "my-quant-v2-mcp"]
    }
  }
}
```

After editing the config, restart Claude Desktop.

## Usage Examples

Once configured, you can interact with the quant framework through natural language:

### Creating a Strategy

> "Create a new trading strategy that buys when RSI is below 30 and sells when RSI is above 70"

Claude will:
1. Use `list_indicators` to confirm RSI is available
2. Use `strategy://schema` resource to understand the format
3. Create the YAML and use `validate_strategy` to check it
4. Use `save_strategy` to save it

### Running a Backtest

> "Backtest my RSI strategy on Apple stock from January 2023 to December 2024"

Claude will:
1. Use `run_backtest` to start the job
2. Use `get_job_status` to monitor progress
3. Report the results including profit, Sharpe ratio, etc.

### Exploring Strategies

> "What strategies do I have available?"

Claude will use `list_strategies` to show all saved strategies.

> "Show me the VolumeSpike strategy"

Claude will use `get_strategy` to fetch and explain the strategy.

### Comparing Configurations

> "Run the volume spike strategy on both TSLA and NVDA and compare results"

Claude will:
1. Run parallel backtests
2. Compare the metrics
3. Provide analysis

## Workflow: From Idea to Validated Strategy

1. **Describe your idea**: Tell Claude your trading concept in plain language
2. **Review the strategy**: Claude generates YAML and explains the logic
3. **Validate**: Claude validates the syntax and structure
4. **Backtest**: Run against historical data
5. **Iterate**: Adjust parameters based on results
6. **Save**: Store the final strategy for later use

## Rate Limiting

Yahoo Finance data fetching is rate-limited to 1 request per second to avoid API throttling. When running multiple backtests, data is cached locally in the `datas/` folder.

## Job Management

Backtests run asynchronously in background threads:
- Jobs are kept in memory (lost on server restart)
- Maximum 100 jobs retained (oldest pruned automatically)
- Use `list_jobs` to see recent job history

## Troubleshooting

### MCP server not connecting
1. Check Claude Desktop config JSON syntax
2. Ensure the path to my_quant_v2 is absolute
3. Verify Python environment has all dependencies
4. Check Claude Desktop logs for errors

### Backtest fails
1. Check job status for error message
2. Verify strategy name exists
3. Ensure date range has market data available
4. Check ticker symbol is valid

### Strategy validation errors
1. Use `validate_strategy` to see specific issues
2. Reference `strategy://schema` for correct format
3. Ensure all referenced parameters are defined

## Security Notes

- The MCP server runs locally on your machine
- No data is sent to external services (except Yahoo Finance for market data)
- Strategy files are stored in your local `strategies/` folder
- Backtest results are saved to `output/json/`
