# FinPilot AI - Visualization System Debugging Guide

## Overview

This guide explains how the visualization system works, common issues, and how to debug them using the enhanced logging.

## Architecture

```
User Query
    ↓
Orchestrator Routes to Agent(s)
    ↓
Agent Returns: {agent, metrics, response, ...}
    ↓
Visualization Node (Optional)
    ├── Checks if request_visualization=true
    ├── Calls visualization_agent.run()
    └── Returns visualization_output
    ↓
Aggregator Node
    ├── Passes through agent results
    └── Includes visualization_output
    ↓
Streamlit Display
    ├── Renders agent analysis
    └── Renders charts (if visualization_output exists)
```

## Visualization Agent Flow

### 1. Data Extraction Phase (extract_chartable_data)

**Purpose:** Extract meaningful metrics from agent results that can be visualized

**Logging Output:**
```
[Visualization Agent] Extract: Processing agent response from 'financial analyst'
[Visualization Agent] Extract: Response keys available: ['agent', 'metrics', 'response', ...]
[Visualization Agent] Extract: Metrics dict has 5 keys
[Visualization Agent] Extract: Metric keys: ['total_revenue', 'cost_breakdown', ...]
[Visualization Agent] Extract: Got 2 items from _extract_from_metrics (total now: 2)
[Visualization Agent] Extract: Financial data provided 0 items
[Visualization Agent] Extract: Trend/breakdown extraction added 0 items
[Visualization Agent] Extract: Final result - returning 2 charts (had 2 candidates)
```

**What it means:**
- "Got X items from _extract_from_metrics" → Found chartable metrics (dict/list data)
- "Got 0 items" → No chartable metrics found in the "metrics" dict
- "Final result - returning X charts" → Successfully extracted X charts

### 2. Chart Creation Phase (create_chart_for_metric)

**Logging Output:**
```
[Visualization Agent] ✓ Created line chart: Revenue Trend
[Visualization Agent] ✓ Created bar chart: Cost Breakdown
[Visualization Agent] ✓ Created 2 charts
```

**What each means:**
- Line chart typically used for time series data (dates as X-axis)
- Bar chart for categorical data or comparisons
- Pie chart for breakdowns/distributions

## Common Issues & Solutions

### Issue 1: "No chartable data found in response"

**Symptoms:**
- Visualization returns empty charts
- Agent analysis works fine, but no visualization

**Root Cause:**
Agent results don't contain dict/list data - only scalar values (count, total, etc.)

**Debug Steps:**
1. Check orchestrator logs for "Extract: Metrics dict has X keys"
2. If X=0: Agent didn't return "metrics" dict
3. If X>0 but "Got 0 items": Metrics contain only scalars

**Solution:**
```python
# Before (only scalars):
metrics = {"total": 1000000, "count": 5}

# After (add dict/list data):
metrics = {
    "total": 1000000,
    "cost_breakdown": {"COGS": 400k, "OpEx": 300k},  # ← Add this
    "monthly_trend": {"2024-01": 100k, "2024-02": 200k}  # ← Add this
}
```

### Issue 2: "Blank graph with date conversion error"

**Symptoms:**
```
Error: could not convert string to float: '2022-01'
```

**Root Cause:**
Chart builder tried to convert date strings to float for cleaning

**Debug Steps:**
1. Check if chart type is "line" (time series)
2. Verify data has "dates" key with string values

**Already Fixed:** 
- Chart builder skips cleaning for time series data
- Dates are preserved as string labels on X-axis

### Issue 3: "Multi-agent query shows blank chart"

**Symptoms:**
- Single agent query: shows chart ✓
- Multi-agent query (finance + sales): no chart ✗

**Root Cause:**
Visualization prioritizes financial data, but finance CSV has no cost_breakdown

**Debug Steps:**
1. Check orchestrator logs for "Financial result has X items in metrics"
2. If financial metrics are empty dict, visualization should fall back to sales

**Already Fixed:**
Smart fallback in orchestrator_agent.py visualization_node:
```python
if financial_result exists and has chartable data:
    use financial_result
else if sales_result exists:
    use sales_result  # ← Fallback
else:
    use investment_result
```

### Issue 4: "Only seeing statistical metrics (count=5, mean=3.2, etc.)"

**Symptoms:**
- Charts show statistical scalars instead of actual data
- Multiple small charts with meaningless values

**Root Cause:**
Agent returned statistical summaries instead of actual data

**Debug Steps:**
1. Check agent's metrics dict for "count", "mean", "median", "std"
2. If present but no breakdowns/trends, fallback to key_metrics chart

**Already Fixed:**
- _extract_from_metrics skips all statistical key names
- If no trends found, creates key_metrics chart as fallback

## Enhanced Logging Reference

### Logging Patterns

**Extract Phase:**
```
[Visualization Agent] Extract: Processing agent response from 'NAME'
[Visualization Agent] Extract: Response keys available: [...]
[Visualization Agent] Extract: Metrics dict has X keys
[Visualization Agent] Extract: Metric keys: [...]
[Visualization Agent] Extract: Got X items from _extract_from_metrics
[Visualization Agent] Extract: Agent-specific extraction added Y items
[Visualization Agent] Extract: Added trend key 'KEY' from response
[Visualization Agent] Extract: Final result - returning Z charts
```

**Format Phase:**
```
[Visualization Agent] _format_metric_for_chart(KEY): type=dict, len=5
[Visualization Agent]   → Sample data: {...}
```

**Key Metrics Phase:**
```
[Visualization Agent] KeyMetrics: Found 'total_revenue' = 1000000 in metrics dict
[Visualization Agent] KeyMetrics: Extracted 3 metrics: [...]
```

**Chart Creation Phase:**
```
[Visualization Agent] ✓ Created line chart: Revenue Trend
[Visualization Agent] ✓ Created 2 charts
```

## Testing Visualization

### Test 1: CSV with Financial Metrics

**Query:** "Analyze my financial data"

**Expected Flow:**
```
1. extract_chartable_data finds "metrics" dict
2. _extract_from_metrics identifies cost_breakdown, monthly_trend
3. Creates 2 charts: line (trend) + pie (breakdown)
4. Streamlit renders both charts
```

**Check Logs For:**
```
[Visualization Agent] Extract: Metrics dict has X keys
[Visualization Agent] _format_metric_for_chart(monthly_trend): type=dict, len=12
[Visualization Agent] ✓ Created line chart
```

### Test 2: CSV with Only Scalars

**Query:** "What's the total revenue?"

**Expected Flow:**
```
1. extract_chartable_data finds only scalars in metrics
2. No trends/breakdowns found → fallback to key_metrics
3. KeyMetrics chart created from total_revenue, net_income, etc.
4. Streamlit renders key metrics bar chart
```

**Check Logs For:**
```
[Visualization Agent] Extract: Got 0 items from _extract_from_metrics
[Visualization Agent] KeyMetrics: Found 'total_revenue' = ...
[Visualization Agent] ✓ Created 1 charts
```

### Test 3: Multi-Agent Query

**Query:** "Analyze both sales and finance"

**Expected Flow:**
```
1. Financial data has no cost_breakdown
2. Visualization checks: financial metrics empty → fall back
3. Uses sales data instead (has period_breakdown with totals)
4. Creates line chart from sales trends
```

**Check Logs For (Orchestrator):**
```
[Orchestrator] Financial focused - metrics: COUNT=X
[Orchestrator] Checking if financial has chartable data...
[Orchestrator] Financial empty → Using sales data for visualization
[Visualization Agent] Extract: Processing agent response from 'sales analyst'
```

## Performance Optimization

### When to Add Aggregation

If visualization is slow with large datasets:

1. Identify slow line in logs: `_format_metric_for_chart(huge_metric): type=dict, len=10000`
2. Add aggregation in extract_chartable_data:
   ```python
   if len(value) > 500:
       # Aggregate data (e.g., weekly for daily data)
       aggregated = aggregate_time_series(value, "weekly")
       data = aggregated
   ```

### When to Skip Visualization

If visualization is unnecessary overhead:

1. In streamlit_app.py, uncheck "Enable Visualization" by default
2. Or modify orchestrator to skip visualization for small datasets:
   ```python
   if sum(len(m) for m in metrics.values()) < 5:
       skip_visualization = True
   ```

## Adding New Chart Types

To add new chart types (heatmaps, scatter plots, etc.):

1. Add to utils/chart_builder.py:
   ```python
   def create_heatmap(data, title):
       return go.Figure(...)
   ```

2. Update _format_metric_for_chart:
   ```python
   elif "matrix" in key.lower():
       chart_suggestion = "heatmap"
   ```

3. Update create_chart_for_metric:
   ```python
   elif chart_type == "heatmap":
       return create_heatmap(data, title)
   ```

## FAQ

**Q: Why is my data not visualizing?**
A: Check logs for "Extract: Metrics dict has 0 keys". If 0, your agent needs to return a "metrics" dict.

**Q: Why do I only see key metrics instead of trends?**
A: Your data contains only scalar values. Add dict/list data (e.g., monthly_trend, cost_breakdown) to agent output.

**Q: Why does multi-agent query show different chart than single agent?**
A: Visualization intelligently picks the agent with better data. Check orchestrator logs for "Using X data for visualization".

**Q: My dates are showing as numbers in charts?**
A: Ensure chart type is "line" and data format is `{"dates": [...], "values": [...]}`.

**Q: How do I disable visualization?**
A: In orchestrator routing, set `state["request_visualization"] = False`.

## Debug Checklist

When visualization isn't working:

- [ ] Check if "request_visualization" is True in agent state
- [ ] Verify agent returned "metrics" dict (not empty)
- [ ] Look for "Extract: Metrics dict has X keys" in logs
- [ ] Check if _extract_from_metrics found chartable data
- [ ] Verify chart creation succeeded (look for "✓ Created" message)
- [ ] Check streamlit UI is actually calling visualization
- [ ] Verify visualization_output is populated in aggregator_node
- [ ] Test with sample data of known structure

## Recent Code Changes

### Enhanced Logging (This Session)
- Added detailed extraction phase logging
- Enhanced key metrics discovery
- Added sample data preview in logs
- Added chart selection transparency

### Smart Fallback (Previous Session)
- Multi-agent fallback: finance → sales → investment
- Key metrics fallback when no trends found
- Nested period data extraction from {period: {total: X}}
- Date string preservation in time series

### Data Type Handling (Previous Session)
- Skip statistical metrics (count, mean, median, std)
- Preserve date strings in charts
- Extract nested structures properly
- Smart numeric conversion in formatters
