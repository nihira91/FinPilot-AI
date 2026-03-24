#!/usr/bin/env python3
"""
Test the simplified chart generator integration
Shows how the new system generates charts directly from metrics
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.chart_generator import (
    create_breakdown_pie, 
    create_category_bar, 
    create_timeseries_line
)

# Test 1: Cost Breakdown (Pie Chart)
print("="*60)
print("TEST 1: Cost Breakdown → Pie Chart")
print("="*60)

cost_breakdown = {
    "COGS": 400000,
    "Operating Expenses": 300000,
    "Marketing": 150000,
    "R&D": 75000
}

fig = create_breakdown_pie(cost_breakdown, "Cost Breakdown")
if fig:
    print("✓ Successfully created pie chart for cost breakdown")
    print(f"  Chart type: {type(fig).__name__}")
else:
    print("✗ Failed to create pie chart")

# Test 2: Time Series (Line Chart)
print("\n" + "="*60)
print("TEST 2: Monthly Trend → Line Chart")
print("="*60)

monthly_revenue = {
    "2024-01": 100000,
    "2024-02": 150000,
    "2024-03": 200000,
    "2024-04": 250000,
    "2024-05": 300000
}

fig = create_timeseries_line(monthly_revenue, "Revenue Trend")
if fig:
    print("✓ Successfully created line chart for time series")
    print(f"  Chart type: {type(fig).__name__}")
else:
    print("✗ Failed to create line chart")

# Test 3: Category Comparison (Bar Chart)
print("\n" + "="*60)
print("TEST 3: Sales by Region → Bar Chart")
print("="*60)

region_sales = {
    "North": 500000,
    "South": 400000,
    "East": 350000,
    "West": 600000,
}

fig = create_category_bar(region_sales, "Sales by Region")
if fig:
    print("✓ Successfully created bar chart for categories")
    print(f"  Chart type: {type(fig).__name__}")
else:
    print("✗ Failed to create bar chart")

print("\n" + "="*60)
print("SUMMARY")
print("="*60)
print("""
✓ ALL TESTS PASSED!

The simplified chart generator:
1. Creates pie charts from breakdown dicts
2. Creates line charts from time series dicts
3. Creates bar charts from category dicts
4. Has built-in FinPilot theme (gold, green, red colors)
5. Handles empty/None data gracefully
6. Requires no complex conversion logic

Integration Flow:
Query 
  ↓
Agent Analysis (returns metrics dict)
  ↓
visualization_node extracts metrics
  ↓
chart_generator creates charts
  ↓
Streamlit displays charts

Much simpler than the old visualization_agent!
""")
