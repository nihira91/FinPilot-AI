
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
import plotly.graph_objects as go
from datetime import datetime, timedelta


def _detect_time_column(df: pd.DataFrame) -> tuple[str, str]:
   
    time_cols = df.columns.str.lower()
    
    # Priority 0: Month + Year combination 
    month_keywords = ['month', 'mon']
    year_keywords = ['year', 'yr']
    month_col = None
    month_num_col = None
    year_col = None
    
    for col in df.columns:
        col_lower = col.lower().strip()
        if any(kw in col_lower for kw in month_keywords):
            # Prefer numeric month columns 
            if 'number' in col_lower or 'num' in col_lower:
                month_num_col = col
            else:
                month_col = col
        if any(kw in col_lower for kw in year_keywords):
            year_col = col
    
    # Use numeric month if available
    final_month_col = month_num_col if month_num_col else month_col
    
    if final_month_col and year_col:
        print(f"[Forecasting] Found Month+Year columns: '{final_month_col}' + '{year_col}' (PREFERRED)")
        return f"{final_month_col}|{year_col}", 'monthly'
    
    # Priority 1: Month only
    if final_month_col:
        print(f"[Forecasting] Found month column: '{final_month_col}'")
        return final_month_col, 'monthly'
    
    # Priority 2: Explicit Date column
    date_keywords = ['date', 'datetime', 'timestamp', 'day']
    for col in df.columns:
        if col.lower() in date_keywords or any(kw in col.lower() for kw in date_keywords):
            print(f"[Forecasting] Found date column: '{col}' (will aggregate by month if possible)")
            return col, 'daily'
    
    # Priority 3: Week
    week_keywords = ['week', 'wk']
    for col in df.columns:
        if any(kw in col.lower() for kw in week_keywords):
            print(f"[Forecasting] Found week column: '{col}'")
            return col, 'weekly'
    
    # Priority 4: Quarter
    quarter_keywords = ['quarter', 'q1', 'q2', 'q3', 'q4']
    for col in df.columns:
        if any(kw in col.lower() for kw in quarter_keywords):
            print(f"[Forecasting] Found quarter column: '{col}'")
            return col, 'quarterly'
    
    # Priority 5: Year only as fallback
    if year_col:
        print(f"[Forecasting] Found year column (fallback): '{year_col}'")
        return year_col, 'yearly'
    
    print("[Forecasting] No time column detected - will treat data as time-series")
    return None, None
    
    # Priority 4: Week
    week_keywords = ['week', 'wk']
    for col in df.columns:
        if any(kw in col.lower() for kw in week_keywords):
            print(f"[Forecasting] Found week column: '{col}'")
            return col, 'weekly'
    
    # Priority 5: Quarter
    quarter_keywords = ['quarter', 'q1', 'q2', 'q3', 'q4']
    for col in df.columns:
        if any(kw in col.lower() for kw in quarter_keywords):
            print(f"[Forecasting] Found quarter column: '{col}'")
            return col, 'quarterly'
    
    # Priority 6: Year only as fallback
    if year_col:
        print(f"[Forecasting] Found year column (fallback): '{year_col}'")
        return year_col, 'yearly'
    
    print("[Forecasting] No time column detected - will treat data as time-series")
    return None, None


def _aggregate_by_period(df: pd.DataFrame, selected_col: str, time_col: str) -> tuple[list, list, str]:
    
    try:
        # Handle Date columns - extract Month+Year for aggregation
        if time_col.lower() in ['date', 'datetime', 'timestamp']:
            print(f"[Forecasting] Date column detected - extracting Month+Year...")
            try:
                # Parse dates
                df_agg = df[[selected_col, time_col]].copy()
                df_agg['_parsed_date'] = pd.to_datetime(df_agg[time_col], errors='coerce')
                df_agg['_year_month'] = df_agg['_parsed_date'].dt.to_period('M')
                df_agg[selected_col] = pd.to_numeric(df_agg[selected_col], errors='coerce')
                
                print(f"[Forecasting] After date parsing: {df_agg['_year_month'].notna().sum()} valid dates found")
                
                # Aggregate by year-month
                grouped = df_agg.groupby('_year_month', as_index=False, sort=False)[selected_col].sum()
                grouped = grouped.sort_values('_year_month')
                grouped = grouped.dropna(subset=[selected_col])
                
                # Generate labels
                labels = [str(ym) for ym in grouped['_year_month']]
                values = grouped[selected_col].values.tolist()
                periods_found = len(grouped)
                
                print(f"[Forecasting] ✓ Aggregated by date to {periods_found} month(s): {labels[:3]}...")
                return values, labels, f"{periods_found} months from dates"
                
            except Exception as e:
                print(f"[Forecasting] Date parsing failed: {str(e)}")
                # Fall back to raw data
                values = pd.to_numeric(df[selected_col], errors='coerce').dropna().values.tolist()
                labels = [f"P{i+1}" for i in range(len(values))]
                return values, labels, f"{len(values)} rows (date parsing failed)"
        
        # Handle Month+Year combination
        if "|" in time_col:
            month_col, year_col = time_col.split("|")
            print(f"[Forecasting] Grouping by {month_col} + {year_col}...")
            
            df_agg = df[[selected_col, month_col, year_col]].copy()
            df_agg[selected_col] = pd.to_numeric(df_agg[selected_col], errors='coerce')
            
            print(f"[Aggregation Debug] Raw data shape: {df_agg.shape}")
            print(f"[Aggregation Debug] Non-null values in {selected_col}: {df_agg[selected_col].notna().sum()}")
            
            # Group by year and month
            grouped = df_agg.groupby([year_col, month_col], as_index=False, sort=False)[selected_col].sum()
            grouped = grouped.sort_values([year_col, month_col])
            grouped = grouped.dropna(subset=[selected_col])
            
            print(f"[Aggregation Debug] After groupby: {len(grouped)} unique periods")
            print(f"[Aggregation Debug] Grouped data:\n{grouped}")
            
            # Create meaningful labels
            labels = []
            for _, row in grouped.iterrows():
                year_val = int(row[year_col])
                month_val = row[month_col]
                
                # Try to convert month to name
                if isinstance(month_val, (int, float)) and 1 <= month_val <= 12:
                    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                    month_name = month_names[int(month_val) - 1]
                    labels.append(f"{month_name}'{str(year_val)[-2:]}")
                else:
                    labels.append(f"{str(month_val)[:3]} '{str(year_val)[-2:]}")
            
            values = grouped[selected_col].values
            periods_found = len(grouped)
            print(f"[Forecasting] ✓ Aggregated to {periods_found} month(s): {labels}")
            return values.tolist(), labels, f"{periods_found} months"
        
        else:
            # Single time column
            print(f"[Forecasting] Grouping by {time_col}...")
            
            df_agg = df[[selected_col, time_col]].copy()
            df_agg[selected_col] = pd.to_numeric(df_agg[selected_col], errors='coerce')
            
            grouped = df_agg.groupby(time_col, as_index=False, sort=False)[selected_col].sum()
            grouped = grouped.sort_values(time_col)
            grouped = grouped.dropna(subset=[selected_col])
            
            labels = grouped[time_col].astype(str).tolist()
            values = grouped[selected_col].values
            periods_found = len(grouped)
            print(f"[Forecasting] ✓ Aggregated to {periods_found} period(s)")
            return values.tolist(), labels, f"{periods_found} periods"
            
    except Exception as e:
        print(f"[Forecasting] ✗ Error during aggregation: {str(e)}")
        return None, None, str(e)




def _train_polynomial_model(X: np.ndarray, y: np.ndarray, periods: int = 4) -> tuple:
    """Polynomial Regression (Degree 2) - Current model"""
    poly = PolynomialFeatures(degree=2)
    X_poly = poly.fit_transform(X)
    model = LinearRegression()
    model.fit(X_poly, y)
    
    # Predictions
    y_pred = model.predict(X_poly)
    future_X = np.arange(len(y), len(y) + periods).reshape(-1, 1)
    future_X_poly = poly.transform(future_X)
    future_predictions = model.predict(future_X_poly)
    
    # Accuracy
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
    accuracy = max(0, min(100, int(r_squared * 100)))
    
    return np.maximum(future_predictions, 0), accuracy, "Polynomial Regression (Degree 2)"




def _train_exponential_smoothing(X: np.ndarray, y: np.ndarray, periods: int = 4, alpha: float = 0.3) -> tuple:
    """Exponential Smoothing - Gives more weight to recent data"""
    # Calculate smoothed values
    smoothed = [y[0]]
    for i in range(1, len(y)):
        smoothed.append(alpha * y[i] + (1 - alpha) * smoothed[i - 1])
    
    smoothed = np.array(smoothed)
    
    # Fit linear trend on smoothed data
    model = LinearRegression()
    model.fit(X, smoothed)
    
    # Last smoothed value as base
    last_smoothed = smoothed[-1]
    trend = model.coef_[0]
    
    # Future predictions using trend
    future_predictions = np.array([last_smoothed + trend * (i + 1) for i in range(periods)])
    
    # Accuracy on smoothed data
    y_pred = model.predict(X)
    ss_res = np.sum((smoothed - y_pred) ** 2)
    ss_tot = np.sum((smoothed - np.mean(smoothed)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
    accuracy = max(0, min(100, int(r_squared * 100)))
    
    return np.maximum(future_predictions, 0), accuracy, "Exponential Smoothing (α=0.3)"




def _get_model_function(model_type: str):
    """Get model function by name"""
    models = {
        "polynomial": _train_polynomial_model,
        "exponential": _train_exponential_smoothing,
    }
    return models.get(model_type, _train_exponential_smoothing)  # Default to exponential smoothing


def forecast_revenue(df: pd.DataFrame, periods: int = 4, column_to_forecast: str = None, model_type: str = "polynomial") -> dict:
   
    try:
        print(f"\n[Forecasting] Starting forecast. DataFrame shape: {df.shape}")
        print(f"[Forecasting] Columns available: {list(df.columns)}")
        
        
        print(f"[Forecasting] Cleaning currency symbols...")
        for col in df.columns:
            if df[col].dtype == 'object':  # String columns
               
                sample = str(df[col].iloc[0]) if len(df) > 0 else ""
                if any(curr in sample for curr in ['$', '₹', '€', '£']):
                    # Remove currency symbols and convert to numeric
                    df[col] = df[col].astype(str).str.replace(r'[$₹€£,\s]', '', regex=True)
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    print(f"[Forecasting] Cleaned currency column: '{col}'")
        
        # User-specified column 
        if column_to_forecast and column_to_forecast in df.columns:
            selected_col = column_to_forecast
            print(f"[Forecasting] Using user-selected column: '{selected_col}'")
        else:
            # Auto-detect revenue/sales columns 
            selected_col = None
            revenue_keywords = ['revenue', 'sales', 'income', 'total_sales', 'net_sales', 'profit', 'margin']
            
            for col in df.columns:
                if col.lower() in revenue_keywords or any(
                    kw in col.lower() for kw in revenue_keywords
                ):
                    selected_col = col
                    print(f"[Forecasting] Auto-detected column: '{selected_col}'")
                    break
            
            #  Pick largest numeric column 
            if selected_col is None:
                numeric_cols = []
                for col in df.columns:
                    if df[col].dtype in ['float64', 'int64']:
                        # Skip obvious metadata columns
                        if not any(
                            skip_kw in col.lower() 
                            for skip_kw in ['date', 'month', 'year', 'week', 'quarter', 'period', 'id', 'count', 'number']
                        ):
                            numeric_cols.append(col)
                
                # Find column with largest mean value
                if numeric_cols:
                    largest_col = max(
                        numeric_cols,
                        key=lambda col: pd.to_numeric(df[col], errors='coerce').mean()
                    )
                    selected_col = largest_col
                    print(f"[Forecasting] Using largest numeric column: '{selected_col}'")
        
        if selected_col is None:
            return {"error": "No suitable numeric column found for forecasting"}
        
        #Detect time column and aggregate if needed 
        time_col, frequency = _detect_time_column(df)
        
        if time_col:
            # Data needs aggregation
            values, labels, period_info = _aggregate_by_period(df, selected_col, time_col)
            
            if values is None:
                return {"error": f"Aggregation failed: {period_info}"}
            
            historical_labels = labels
        else:
            # No time column - treat as time-series as-is
            print(f"[Forecasting] No time column found, treating as time-series...")
            values = pd.to_numeric(df[selected_col], errors='coerce').dropna().values.tolist()
            historical_labels = [f"P{i+1}" for i in range(len(values))]
            period_info = f"{len(values)} rows"
        
        #Validate minimum data points
        if len(values) < 2:
            return {
                "error": f"Insufficient historical data: only {len(values)} period(s) found ({period_info}). "
                        f"Need at least 2 data points for forecasting. "
                        f"Your dataset may contain data from only 1 time period."
            }
        
        # Prepare data for ML 
        X = np.arange(len(values)).reshape(-1, 1)
        y = np.array(values)
        
        # Select and train chosen model
        print(f"[Forecasting] Using model: {model_type}")
        model_func = _get_model_function(model_type)
        future_predictions, accuracy, model_name = model_func(X, y, periods)
        
        print(f"[Forecasting] Model: {model_name} | Accuracy: {accuracy}%")
        
        # Calculate growth rate 
        last_actual = float(values[-1])
        next_predicted = float(future_predictions[0])
        growth_rate = ((next_predicted - last_actual) / last_actual * 100) if last_actual > 0 else 0
        
        # Generate future labels 
        future_labels = []
        if 'Month' in df.columns:
            # Try to parse month from existing data
            try:
                last_month_str = str(df['Month'].iloc[-1])
                # Parse month like "January", "Jan-23", etc.
                months = ['January', 'February', 'March', 'April', 'May', 'June', 
                         'July', 'August', 'September', 'October', 'November', 'December',
                         'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                
                # Find which month it is
                current_month_idx = None
                for i, m in enumerate(months):
                    if m.lower() in last_month_str.lower():
                        current_month_idx = i % 12
                        break
                
                if current_month_idx is not None:
                    months_short = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                    
                    year = df.get('Year', pd.Series([2014])).iloc[-1] if 'Year' in df.columns else 2014
                    
                    for i in range(periods):
                        next_month_idx = (current_month_idx + i + 1) % 12
                        next_year = year + ((current_month_idx + i + 1) // 12)
                        future_labels.append(f"{months_short[next_month_idx]} {next_year}")
                else:
                    future_labels = [f"Period {i+1}" for i in range(periods)]
            except:
                future_labels = [f"Period {i+1}" for i in range(periods)]
        else:
            future_labels = [f"Period {i+1}" for i in range(periods)]
        
        return {
            "accuracy": accuracy,
            "last_actual": last_actual,
            "next_predicted": next_predicted,
            "growth_rate": growth_rate,
            "predictions": [float(p) for p in future_predictions],
            "future_labels": future_labels,
            "historical_values": [float(v) for v in values],
            "historical_labels": historical_labels,
            "column_name": selected_col,
            "model_name": model_name
        }
    
    except Exception as e:
        print(f"[Forecasting Error] {str(e)}")
        return {"error": str(e)}


def forecast_summary_text(forecast_data: dict) -> str:
   
    if "error" in forecast_data:
        return f"⚠️ Forecast Error: {forecast_data['error']}"
    
    if not forecast_data or len(forecast_data) == 0:
        return "No forecast data available"
    
    try:
        accuracy = forecast_data.get("accuracy", 0)
        last_actual = forecast_data.get("last_actual", 0)
        next_predicted = forecast_data.get("next_predicted", 0)
        growth_rate = forecast_data.get("growth_rate", 0)
        predictions = forecast_data.get("predictions", [])
        
        if not predictions:
            return "⚠️ No forecast predictions generated"
        
        avg_forecast = np.mean(predictions) if predictions else 0
        
        trend = "📈 **Upward Trend**" if growth_rate > 0 else "📉 **Downward Trend**"
        
        return f"""
**ML Model Accuracy:** {accuracy}%

**Current Value:** ₹{last_actual:,.0f}
**Next Period Forecast:** ₹{next_predicted:,.0f} ({growth_rate:+.1f}%)

**Forecast Summary:** {trend}
- Average forecast (4 periods): ₹{avg_forecast:,.0f}
- Growth trajectory: {growth_rate:+.1f}% next period
- Model confidence: {accuracy}% (R² score)

Model Type: Polynomial Regression (Degree 2)
"""
    except Exception as e:
        return f"Error generating summary: {str(e)}"


def forecast_chart(df: pd.DataFrame, forecast_data: dict) -> object:
    
    try:
        if "error" in forecast_data:
            return None
        
        # ── Extract data ──
        historical_labels = forecast_data["historical_labels"]
        historical_values = forecast_data["historical_values"]
        future_labels = forecast_data["future_labels"]
        future_predictions = forecast_data["predictions"]
        
        # ── Create figure ──
        fig = go.Figure()
        
        # Historical data
        fig.add_trace(go.Scatter(
            x=historical_labels,
            y=historical_values,
            mode='lines+markers',
            name='Historical Revenue',
            line=dict(color='#C9A84C', width=3),
            marker=dict(size=8, color='#C9A84C'),
            hovertemplate='<b>%{x}</b><br>Revenue: ₹%{y:,.0f}<extra></extra>'
        ))
        
        # Forecast data
        fig.add_trace(go.Scatter(
            x=future_labels,
            y=future_predictions,
            mode='lines+markers',
            name='Forecast',
            line=dict(color='#2ECC71', width=3, dash='dash'),
            marker=dict(size=8, color='#2ECC71', symbol='diamond'),
            hovertemplate='<b>%{x}</b><br>Forecast: ₹%{y:,.0f}<extra></extra>'
        ))
        
        # ── Layout ──
        fig.update_layout(
            title={
                'text': '<b>Revenue Forecast Analysis</b>',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18, 'color': '#C9A84C'}
            },
            xaxis_title='Period',
            yaxis_title='Revenue (₹)',
            hovermode='x unified',
            template='plotly_dark',
            plot_bgcolor='#111820',
            paper_bgcolor='#0D1117',
            font=dict(family='DM Mono', color='#F0EAD6'),
            xaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(201,168,76,0.1)'
            ),
            yaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(201,168,76,0.1)',
                tickformat=',.0f'
            ),
            height=400,
            margin=dict(l=60, r=60, t=80, b=60)
        )
        
        return fig
    
    except Exception as e:
        print(f"Error creating forecast chart: {str(e)}")
        return None
