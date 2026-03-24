# Visualization Feature - Implementation Guide

## Overview

FinPilot AI now includes **interactive Plotly-based chart generation** triggered conditionally when users request visualization. The feature provides:

- ✨ **Interactive Charts** - Line, Bar, and Pie charts
- 🎯 **Smart Detection** - Keyword-based + UI toggle for visualization requests  
- 📊 **Multi-source Data** - Financial metrics, Sales data, Investment analysis
- 🔄 **Conditional Execution** - Only creates charts when user asks
- ⚡ **Automatic Reranking** - Suggests optimal chart types per metric

---

## Architecture

### Component Stack

```
┌─────────────────────────────────────────────────────┐
│   STREAMLIT UI                                      │
│  [Query Input] [📈 Visualize Checkbox]             │
│     ↓              ↓                                │
│  [Keyword Detection + Toggle]                      │
└──────────────────┬──────────────────────────────────┘
                   │ request_visualization = True/False
                   ↓
┌─────────────────────────────────────────────────────┐
│   LANGGRAPH ORCHESTRATOR                            │
│  Financial/Sales/Investment Agents Execute          │
│  Store full result dicts (metrics, data, etc)      │
│     ↓                                               │
│  Aggregator Node (aggregates text results)         │
│     ↓                                               │
│  [Conditional Check] request_visualization?        │
│     ├→ YES: Visualization Node ↓                   │
│     └→ NO: END                                      │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────↓──────────────────────────────────┐
│   VISUALIZATION AGENT                               │
│  Extract metrics from full agent response           │
│  Detect optimal chart types per metric              │
│  Create Plotly figures                              │
│  Return chart JSONs                                 │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────↓──────────────────────────────────┐
│   STREAMLIT DISPLAY                                 │
│  Render Plotly charts section                       │
│  Interactive hover, zoom, download PNG              │
└─────────────────────────────────────────────────────┘
```

### Key Files

**Core Visualization Modules:**
- `utils/chart_builder.py` - Plotly chart creation functions
- `utils/visualization_helpers.py` - Keyword detection & metric formatting
- `agents/visualization_agent.py` - Chart generation orchestration

**Integration Points:**
- `streamlit_app.py` - UI detection & display
- `orchestrator/orchestrator_agent.py` - Conditional routing & state management

---

## How It Works

### 1. **Visualization Detection** (Streamlit)

The app detects visualization requests via dual mechanism:

```python
# streamlit_app.py
visualize_toggled = st.checkbox("📈 Visualize", value=False)

from utils.visualization_helpers import detect_visualization_request
wants_viz_auto, suggested_chart_type = detect_visualization_request(query)
request_visualization = visualize_toggled or wants_viz_auto
```

**Triggering Keywords:**
- Chart types: `"line chart"`, `"bar chart"`, `"pie chart"`
- General: `"visualize"`, `"chart"`, `"graph"`, `"plot"`, `"show me"`
- Actions: `"show"`, `"display"`, `"draw"`, `"illustrate"`

**Example Queries:**
- ✅ "Show me a bar chart of sales by region"
- ✅ "Visualize the revenue trend"
- ✅ "Plot quarterly profit data"
- ✅ "Can you graph our expenses?" + 📈 checkbox

### 2. **Data Flow Through Orchestrator**

```python
# orchestrator/orchestrator_agent.py
input_data = {
    "query": query,
    "request_visualization": True/False,
    "chart_type": "auto|line|bar|pie"
}

# Agent nodes return full result dicts
financial_result = {
    "agent": "Financial Analyst",
    "metrics": {...},           # ← Contains chartable data
    "response": "Analysis...",
    "forecast_data": {...}
}
state["financial_result"] = financial_result  # Store for visualization
```

### 3. **Conditional Visualization Node**

```python
# orchestrator/orchestrator_agent.py
def should_visualize(state) -> str:
    if state.get("request_visualization"):
        return "visualization"
    return "end"

graph.add_conditional_edges(
    "aggregator",
    should_visualize,
    {
        "visualization": "visualization",
        "end": END
    }
)
```

Only the visualization node runs if `request_visualization = True`.

### 4. **Chart Generation**

```python
# agents/visualization_agent.py
def run(agent_response: dict, chart_type: str = "auto", query: str = ""):
    # Extract metrics from financial/sales/investment agent response
    chartable_metrics = extract_chartable_data(agent_response, chart_type)
    
    # Create charts for each metric
    for metric in chartable_metrics:
        fig = create_chart_for_metric(metric, chart_type)
        chart_json = fig.to_json()
        charts.append({"title": ..., "plotly_json": chart_json})
    
    return {"charts": charts, ...}
```

**Extracted Chartable Data:**
- From `metrics` dict: total_revenue, total_expenses, gross_profit, etc.
- Time series: "time_series_revenue", "monthly_sales", etc.
- Breakdowns: "cost_breakdown", "sales_by_region", etc.

### 5. **Streamlit Display**

```python
# streamlit_app.py
viz_result = result["visualization_output"]
charts = viz_result.get("charts", [])

for chart in charts:
    st.subheader(chart.get("title"))
    
    # Render Plotly chart
    fig = go.Figure(json.loads(chart["plotly_json"]))
    st.plotly_chart(fig, use_container_width=True)
```

Charts are interactive:
- Hover for data values
- Zoom/pan with mouse
- Download PNG
- Toggle legend items

---

## Chart Types

### 1. **Line Chart** (Time Series)

**Best for:** Trends, forecasts, growth patterns

```python
create_time_series_chart(data, title)
# Input: dict with dates/values or multiple series
# Output: Interactive line chart with markers
```

**Triggered by:**
- Query keywords: "trend", "forecast", "timeline"
- Data type: Dict with 3+ entries
- Agent: Financial (revenue trends), Sales (seasonal patterns)

### 2. **Bar Chart** (Comparisons)

**Best for:** Categories, breakdowns, comparisons

```python  
create_bar_chart(data, title)
# Input: dict with {category: value}
# Output: Horizontal/vertical bar chart with values on top
```

**Triggered by:**
- Query keywords: "comparison", "breakdown", "versus"
- Data type: Dict with 2+ entries or List
- Agent: Sales (by region/product), Financial (cost breakdown)

### 3. **Pie Chart** (Distribution)

**Best for:** Allocation, market share, percentages

```python
create_pie_chart(data, title)
# Input: dict with {category: value}
# Output: Interactive pie with percentage labels
```

**Triggered by:**
- Query keywords: "distribution", "percentage", "share", "split"
- Data type: Dict with ≤5 entries
- Agent: Financial (budget allocation), Sales (product mix)

---

## Usage Examples

### Example 1: Financial Analysis with Charts

**User Query:**
```
"Analyze our financial performance and show me the revenue trends"
```

**Flow:**
1. ✅ Keyword detected: "show me" + financial analysis
2. ✅ `request_visualization = True`
3. ✅ Financial Agent runs → extracts metrics
4. ✅ Visualization Agent creates charts:
   - Line chart: "Revenue Trend" (from time_series_revenue)
   - Bar chart: "Cost Breakdown" (from cost_breakdown)
   - Bar chart: "Budget vs Actual" (from budget_vs_actual)
5. ✅ Charts displayed below analysis

### Example 2: Sales Data with Manual Toggle

**User Query:** "What are our top performing regions?"
**Manually checks:** 📈 Visualize checkbox

**Flow:**
1. ✅ `visualize_toggled = True` (from checkbox)
2. ✅ Sales Agent runs → extracts regional sales
3. ✅ Visualization Agent creates:
   - Bar chart: "Sales by Region"
   - Pie chart: "Sales Region Distribution"
4. ✅ Charts shown alongside text analysis

### Example 3: No Visualization Request

**User Query:** "Provide investment strategy recommendations"
**Checkbox:** Not checked

**Flow:**
1. ❌ No keywords detected
2. ❌ Checkbox not checked
3. → Visualization node skipped
4. → Only text analysis returned

---

## Adding Chartable Metrics to Agents

For an agent to support visualization, return structured metrics:

```python
# In financial_agent.py or sales_agent.py
def run(query: str, ...):
    # ... analysis code ...
    
    return {
        "agent": "Financial Analyst",
        "metrics": {  # ← Add this!
            "total_revenue": 150000,
            "total_expenses": 95000,
            "cost_breakdown": {
                "salaries": 50000,
                "operations": 30000,
                "marketing:": 15000
            },
            "time_series_revenue": {
                "Q1": 40000,
                "Q2": 50000,
                "Q3": 60000
            }
        },
        "response": "...",  # Text analysis
        ...
    }
```

**Visualization Agent automatically extracts and charts:**
- Scalar values → Bar charts
- Dicts with 2+ entries → Bar or Pie
- Time series (3+ entries) → Line charts

---

## Configuration

### Chart Detection Keywords

Edit `utils/visualization_helpers.py`:

```python
VISUALIZATION_KEYWORDS = {
    "chart": ["chart", "diagram", "graph", "visual", ...],
    "specific_type": {
        "line": ["line chart", "trend", "timeline", ...],
        "bar": ["bar chart", "comparison", "breakdown", ...],
        "pie": ["pie chart", "distribution", "share", ...],
        "all": ["visualize", "plot", "graph", ...]
    }
}
```

### default Chart Types

Edit `utils/visualization_helpers.py`:

```python
def get_chart_type_suggestion(query: str, agent_domain: str) -> str:
    # Financial domain defaults to line (trends)
    # Sales domain defaults to bar (comparisons)
    # Custom logic per domain
```

---

## Dependencies

**New Requirement:**
```
plotly>=5.14.0  # Already added to requirements.txt
```

**Plotly Features:**
- Interactive hover tooltips
- Zoom/pan controls
- Legend toggling
- Download PNG
- Responsive sizing

---

## Testing

### Test Visualization Request Detection

```python
from utils.visualization_helpers import detect_visualization_request

# Should True
detect_visualization_request("show me a line chart of trends")
# → (True, "line")

detect_visualization_request("visualize the data")
# → (True, "auto")

# Should be False
detect_visualization_request("provide analysis")
# → (False, None)
```

### Test Chart Generation

```python
from agents.visualization_agent import run

result = run(
    agent_response={
        "agent": "Financial Analyst",
        "metrics": {
            "revenue": {"Q1": 100, "Q2": 120, "Q3": 150}
        }
    },
    chart_type="auto",
    query="Show trends"
)

print(f"Generated {len(result['charts'])} charts")
# → Generated 1 charts
#     Charts[0]: "Revenue" (line chart)
```

---

## Troubleshooting

**Charts not appearing?**
- ✓ Check "📈 Visualize" checkbox is enabled
- ✓ Verify agent response contains `metrics` dict
- ✓ Check browser console for Plotly errors
- ✓ Ensure plotly installed: `pip install plotly>=5.14.0`

**No data to visualize error?**
→ Agent response missing metrics dict or contains only text

**Wrong chart type?**
→ Override with specific keywords: "bar chart", "line chart", "pie chart"

**Performance slow?**
→ Limit chart count: Edit visualization_agent.py max_charts parameter

---

## Future Enhancements

- [ ] Heatmaps for matrix data (sales by region × time)
- [ ] Waterfall charts for profit/loss breakdown
- [ ] Sankey diagrams for process flows
- [ ] Scatter plots with trend lines
- [ ] Multi-series comparison charts
- [ ] Export to PDF with charts
- [ ] Chart customization (colors, labels, etc)
- [ ] Caching chart generation
