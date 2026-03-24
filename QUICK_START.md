# 🚀 Quick Start - New Simplified Chart System

## ✅ What Was Fixed

**Problem:** Cost breakdown showing as blank line chart with indices (0, 1, 2, 3, 4, 5)

**Root Cause:** Complex visualization agent auto-detection logic misclassified breakdowns as time series

**Solution:** Simple chart generator with keyword-based chart selection

---

## 🎯 How to Use

### 1. Restart Streamlit
```bash
streamlit run streamlit_app.py
```

### 2. Upload Financial CSV
- Click "📁 Upload Financial Data"
- Select your CSV with cost data (COGS, OpEx, Revenue, etc.)

### 3. Ask Query
- Text input: "Analyze my financial data"
- Or: "Show cost breakdown"

### 4. Enable Visualization
- Check "📈 Visualize" checkbox

### 5. See Results
- **Cost Breakdown** → **Pie chart** ✓
- Chart shows category names (COGS, OpEx, etc.) on labels
- Chart shows actual values not indices

---

## 📊 Chart Types Generated

| Metric Name | Chart Type | Example Keywords |
|---|---|---|
| `cost_breakdown` | **Pie** 🥧 | breakdown, distribution, split |
| `monthly_revenue` | **Line** 📈 | trend, monthly, period, time, over |
| `sales_by_region` | **Bar** 📊 | region, category, *other* |

---

## 🔧 How It Works

1. **Agent analyzes data** → Returns `metrics` dict
   ```python
   {
       "cost_breakdown": {"COGS": 400K, "OpEx": 300K, ...},
       "monthly_trend": {"2024-01": 100K, "2024-02": 150K, ...}
   }
   ```

2. **visualization_node loops through metrics**
   ```python
   for key, value in metrics.items():
       if "breakdown" in key:  # Pie chart
       elif "trend" in key:    # Line chart
       else:                   # Bar chart
   ```

3. **chart_generator creates chart**
   ```python
   fig = create_breakdown_pie(value, title)
   ```

4. **Streamlit displays chart**
   ```python
   st.plotly_chart(fig)
   ```

---

## ⚡ Why It's Better

| Aspect | Old System | New System |
|---|---|---|
| **Lines of Code** | ~300 | ~50 |
| **Complexity** | ⬆️ High | ⬇️ Low |
| **Performance** | Slower | Faster |
| **Reliability** | 🔴 Buggy | 🟢 Solid |
| **Cost Breakdown** | ❌ Blank | ✅ Proper Pie |
| **Debuggability** | 😫 Hard | 😊 Easy |

---

## 📝 Common Scenarios

### Scenario 1: Cost Analysis
```
Input:  "Analyze cost breakdown"
Agent Returns:
  cost_breakdown: {COGS: 400K, Salaries: 300K, Marketing: 150K}
Visualization:
  ✓ Pie chart with 3 slices (COGS, Salaries, Marketing)
  ✓ Each slice labeled with amount
```

### Scenario 2: Revenue Trends
```
Input:  "Show revenue trend by month"
Agent Returns:
  monthly_revenue: {2024-01: 100K, 2024-02: 150K, 2024-03: 200K}
Visualization:
  ✓ Line chart with months on X-axis
  ✓ Revenue values shown as line
  ✓ Green trend going up
```

### Scenario 3: Sales by Region
```
Input:  "Compare sales by region"
Agent Returns:
  sales_region: {North: 500K, South: 400K, East: 350K}
Visualization:
  ✓ Bar chart with 3 bars
  ✓ Categories on X-axis (North, South, East)
  ✓ Values as bar heights
```

---

## 🎨 Chart Styling

All charts use **FinPilot theme**:
- **Gold:** #C9A84C (primary)
- **Green:** #2ECC71 (positive)
- **Red:** #E74C3C (negative)
- **Navy:** #0D1117 (background)
- **Font:** DM Sans

---

## 🆘 Troubleshooting

### Issue: Still seeing blank charts
- **Solution:** Restart Streamlit completely
  ```bash
  taskkill /F /IM streamlit.exe
  streamlit run streamlit_app.py
  ```

### Issue: Chart not appearing
- **Check:** Is "📈 Visualize" checkbox enabled?
- **Check:** Does your CSV have cost columns?
- **Check:** Browser console for errors (F12)

### Issue: Wrong chart type
- **Problem:** Bar chart appearing instead of pie
- **Reason:** Metric name doesn't contain "breakdown"
- **Solution:** Agent needs to use standard metric names

---

## 📋 Files Changed

✅ Created:
- `utils/chart_generator.py` - Simple chart functions

✅ Modified:
- `orchestrator/orchestrator_agent.py` - Removed complex visualization, added simple chart generation

✅ No longer used:
- ~~`agents/visualization_agent.py`~~ (kept for reference, not called)
- ~~`utils/visualization_helpers.py`~~ (kept for reference, not called)

---

## ✨ Next Steps

1. ✅ Restart Streamlit
2. ✅ Upload financial CSV with cost data
3. ✅ Ask query with "breakdown," "trend," or metric name
4. ✅ Enable visualization
5. ✅ See proper charts with your data!

---

## 🎓 For Developers

To add custom chart types to `chart_generator.py`:

```python
def create_custom_chart(data_dict: dict, title: str = "Custom"):
    """Your description here"""
    # Create Plotly figure
    fig = go.Figure(...)
    fig.update_layout(**LAYOUT)  # Use theme
    return fig
```

Then in `orchestrator/orchestrator_agent.py` `visualization_node()`:

```python
elif "custom_keyword" in key_lower:
    fig = create_custom_chart(value)
```

Done! No complex agent logic needed.

---

**Happy charting! 📊✨**
