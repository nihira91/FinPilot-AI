# Quick Start - Visualization Feature

## Installation

```bash
# Install/update dependencies
pip install -r requirements.txt

# Key new dependency:
pip install plotly>=5.14.0
```

---

## How to Use

### **Option 1: Automatic Detection** (Keyword-based)

Just use visualization words in your query:

```
📝 Query: "Show me a bar chart of sales by region"
→ Automatically creates visualization
→ No need to check any boxes
```

**Trigger Words:**
- "chart", "graph", "visualize", "plot", "show me"
- "line chart", "bar chart", "pie chart"
- "trend", "comparison", "distribution"

### **Option 2: Manual Toggle** (UI Checkbox)

```
📝 Query: "Analyze our financial performance"
☑️ Check: 📈 Visualize checkbox
→ Creates charts even without keywords
```

### **Option 3: Combined** (Best)

```
📝 Query: "Visualize quarterly trends"
☑️ Check: 📈 Visualize checkbox
→ Double confirmation for reliable visualization
```

---

## Workflow

### 1. Upload Data (Optional)

Upload Financial/Sales CSV:
- Financial CSV → Financial Agent analyzes
- Sales CSV → Sales Agent analyzes

### 2. Enter Query

```
"Show me revenue trends and cost breakdown"
```

### 3. Enable Visualization (Optional)

- ✅ Check the **📈 Visualize** checkbox, OR
- 🔑 Use keywords in your query

### 4. Click **⚡ RUN ANALYSIS**

### 5. View Results

```
[Analysis Text]
    ↓
[Agent Attribution: Agent/Domain/Source/Confidence]
    ↓
[Interactive Charts] ← NEW!
    ├─ Line Chart: Revenue Trend
    ├─ Bar Chart: Cost Breakdown
    └─ Pie Chart: Budget Allocation
```

---

## Chart Types

### Line Charts
```
📈 When: Trends, Time Series, Forecasts
📊 Example: "Show quarterly revenue trend"
🎯 Auto-triggered: Time series data (3+ months)
```

### Bar Charts
```
📊 When: Comparisons, Breakdowns, Categories
📉 Example: "Sales by region"
🎯 Auto-triggered: Regional/product breakdowns
```

### Pie Charts
```
🥧 When: Distribution, Percentages, Allocation
💰 Example: "Budget allocation"
🎯 Auto-triggered: Cost/revenue splits
```

---

## Examples

### Example 1: Financial Analysis

**Query:**
```
Analyze revenue and show me the trends
```

**Automatically generates:**
- Line chart of revenue over time
- Bar chart of cost breakdown
- Other financial metric visuals

---

### Example 2: Sales Analysis

**Query:**
```
Compare sales performance across regions
```

**Creates:**
- Bar chart: Sales by region (comparison)
- Pie chart: Market share distribution
- Interactive legend toggling

---

### Example 3: Investment Opportunities

**Query (with checkbox):**
```
What are our expansion opportunities?
☑️ [Visualize checkbox]
```

**Shows:**
- Investment metrics as charts
- Strategic opportunity visualizations

---

## Chart Features

### Interactive Controls
- **Hover**: See exact values
- **Zoom**: Click and drag to zoom
- **Pan**: Shift + Drag to move
- **Legend**: Click legend to show/hide series
- **Download**: Camera icon to save as PNG

### Customization
- Auto-sized for Streamlit layout
- Color-coded per chart type
- Professional styling
- Responsive design

---

## Troubleshooting

### Charts not appearing?

**Check:**
1. ✓ Is data available? (CSV uploaded or RAG docs loaded)
2. ✓ Did you use visualization keywords OR check 📈 box?
3. ✓ Is Agent returning metrics data?

**Solution:**
```
# Try explicit keywords:
"Show me a chart of..."
"Visualize the..."
"Plot..."

# Or just check the checkbox
☑️ [Visualize]
```

### No data to visualize?

**Reason:** Agent response doesn't contain metrics

**Solution:**
- With CSV: Upload financial/sales CSV first
- With RAG: Add PDF documents to knowledge base
- Ensure query is specific enough for analysis

### Wrong chart type?

**Solution:** Use specific chart keywords
```
"Show me a LINE chart" → Line chart
"Create a BAR chart" → Bar chart  
"Make a PIE chart" → Pie chart
```

---

## Data Requirements

### For Financial Agent

**CSV must include:**
- Revenue/Income column
- Expense/Cost columns
- Date/Period column (for trends)

**Example Financial Data:**
```
Period,Revenue,Expenses,Profit
Q1,100000,60000,40000
Q2,120000,70000,50000
Q3,150000,85000,65000
```

### For Sales Agent

**CSV must include:**
- Sales column
- Region/Product column
- Date/Period column

**Example Sales Data:**
```
Month,Region,Sales,Units
Jan,North,50000,500
Jan,South,40000,400
Feb,North,55000,550
Feb,South,45000,450
```

---

## Tips & Tricks

### 💡 Get Better Charts

**Do:**
- ✅ Upload complete CSV with dates
- ✅ Use specific metric names in query
- ✅ Enable visualization for comparison queries
- ✅ Check 📈 box for complex queries

**Avoid:**
- ❌ Empty/incomplete CSV data
- ❌ Very short queries
- ❌ Requesting non-numerical analysis only

### 🎯 Best Queries for Charts

```
✅ "Show revenue trends quarterly"
✅ "Compare sales by region"
✅ "Visualize cost breakdown"
✅ "Chart our growth trajectory"

❌ "Give me thoughts"
❌ "What do you think?"
❌ "Provide recommendations" (without data)
```

### ⚡ Performance Tips

- Charts auto-limit to ~10 per analysis
- Large datasets use sampling
- PNG export usually instant
- Zoom/pan are client-side (fast)

---

## Feature Details

### Agent Support

- **Financial Agent**: Full charts from metrics ✅
- **Sales Agent**: Full charts from metrics ✅
- **Investment Agent**: Supports visualization ✅
- **Cloud Agent**: Coming soon 🚧

### Chart Types Available

| Chart | Financial | Sales | Investment |
|-------|-----------|-------|-----------|
| Line  | ✅ Trends | ✅ Trends | ✅ Performance |
| Bar   | ✅ Breakdown | ✅ Comparison | ✅ Breakdown |
| Pie   | ✅ Allocation | ✅ Mix | ✅ Distribution |

---

## FAQ

**Q: Do I have to visualize every query?**
> No! Visualization is optional. Only charts appear when you request it (via keywords or checkbox).

**Q: Can I get text analysis WITHOUT charts?**
> Yes! Just uncheck 📈 Visualize and don't use visualization keywords.

**Q: How many charts can I get?**
> Typically 3-5 per analysis (depends on data available). Maximum is ~10.

**Q: Can I customize chart colors?**
> Currently no - they use professional default styling. Future enhancement planned.

**Q: Do charts work on mobile?**
> Yes! Plotly charts are fully responsive and mobile-compatible.

**Q: Can I export charts?**
> Yes! Click the camera icon in chart to download PNG. PDF export coming soon.

---

## Next Steps

1. **Install** dependencies: `pip install -r requirements.txt`
2. **Upload** CSV data (optional but recommended)
3. **Query** with visualization keywords
4. **Enable** 📈 Visualize if needed
5. **Enjoy** interactive charts! 🎉

---

## Keyboard Shortcuts (in charts)

| Action | Shortcut |
|--------|----------|
| Zoom | Click & drag |
| Pan | Shift + Click & drag |
| Reset | Double-click |
| Screenshot | Camera icon in toolbar |
| Legend | Click legend items |

---

## Support

For issues with visualization:
1. Check VISUALIZATION_FEATURE.md for detailed docs
2. Review VISUALIZATION_IMPLEMENTATION.md for architecture
3. Check error messages in Streamlit terminal
4. Verify chart data in agent output
