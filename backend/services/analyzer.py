import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import warnings
warnings.filterwarnings('ignore')


def load_dataset(filepath):
    """Load and validate dataset from CSV or JSON."""
    if filepath.endswith('.csv'):
        df = pd.read_csv(filepath)
    elif filepath.endswith('.json'):
        df = pd.read_json(filepath)
    else:
        raise ValueError("Unsupported file format. Use CSV or JSON.")
    
    # Normalize column names
    df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]
    
    # Detect and parse date column
    date_cols = [c for c in df.columns if 'date' in c or 'time' in c]
    if date_cols:
        df[date_cols[0]] = pd.to_datetime(df[date_cols[0]], errors='coerce')
        df.rename(columns={date_cols[0]: 'date'}, inplace=True)
    
    # Detect quantity column
    qty_cols = [c for c in df.columns if any(k in c for k in ['qty', 'quantity', 'units', 'sold', 'count'])]
    if qty_cols:
        df.rename(columns={qty_cols[0]: 'quantity'}, inplace=True)
    elif 'quantity' not in df.columns:
        df['quantity'] = 1

    # Detect product column
    prod_cols = [c for c in df.columns if any(k in c for k in ['product', 'item', 'name', 'sku'])]
    if prod_cols and prod_cols[0] != 'product':
        df.rename(columns={prod_cols[0]: 'product'}, inplace=True)

    # Detect category column
    cat_cols = [c for c in df.columns if any(k in c for k in ['category', 'type', 'dept', 'department'])]
    if cat_cols and cat_cols[0] != 'category':
        df.rename(columns={cat_cols[0]: 'category'}, inplace=True)

    df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').fillna(1)
    df.dropna(subset=['date'], inplace=True)
    df.sort_values('date', inplace=True)
    
    return df


def run_full_analysis(filepath):
    """Run complete trend analysis on a dataset."""
    df = load_dataset(filepath)
    result = {}

    # ── 1. Top Products ──────────────────────────────────────────────
    if 'product' in df.columns:
        top_products = (
            df.groupby('product')['quantity']
            .sum()
            .sort_values(ascending=False)
            .head(10)
        )
        result['top_products'] = {
            'labels': top_products.index.tolist(),
            'values': top_products.values.tolist()
        }

    # ── 2. Category Demand ───────────────────────────────────────────
    if 'category' in df.columns:
        cat_demand = (
            df.groupby('category')['quantity']
            .sum()
            .sort_values(ascending=False)
        )
        result['category_demand'] = {
            'labels': cat_demand.index.tolist(),
            'values': cat_demand.values.tolist()
        }

    # ── 3. Monthly Time-Series ───────────────────────────────────────
    df['month'] = df['date'].dt.to_period('M')
    monthly = df.groupby('month')['quantity'].sum().reset_index()
    monthly['month_str'] = monthly['month'].astype(str)
    result['time_series'] = {
        'labels': monthly['month_str'].tolist(),
        'values': monthly['quantity'].tolist()
    }

    # ── 4. Seasonal Patterns ─────────────────────────────────────────
    df['season'] = df['date'].dt.month.map({
        12: 'Winter', 1: 'Winter', 2: 'Winter',
        3: 'Spring', 4: 'Spring', 5: 'Spring',
        6: 'Summer', 7: 'Summer', 8: 'Summer',
        9: 'Autumn', 10: 'Autumn', 11: 'Autumn'
    })
    seasonal = df.groupby('season')['quantity'].sum()
    result['seasonal'] = {
        'labels': seasonal.index.tolist(),
        'values': seasonal.values.tolist()
    }

    # ── 5. Growth / Decline Analysis ─────────────────────────────────
    if 'product' in df.columns and 'date' in df.columns:
        df['period'] = (df['date'].dt.year * 100 + df['date'].dt.month)
        periods = sorted(df['period'].unique())
        growth_data = []

        if len(periods) >= 2:
            mid = len(periods) // 2
            first_half = periods[:mid]
            second_half = periods[mid:]

            first_qty = df[df['period'].isin(first_half)].groupby('product')['quantity'].sum()
            second_qty = df[df['period'].isin(second_half)].groupby('product')['quantity'].sum()

            common = first_qty.index.intersection(second_qty.index)
            for prod in common:
                old = first_qty[prod]
                new = second_qty[prod]
                if old > 0:
                    pct = round(((new - old) / old) * 100, 1)
                    growth_data.append({'product': prod, 'growth_pct': pct, 'current_qty': int(new)})

            growth_data.sort(key=lambda x: x['growth_pct'], reverse=True)

        result['growth_analysis'] = growth_data

    # ── 6. Trend Predictions ──────────────────────────────────────────
    predictions = _generate_predictions(df, result)
    result['predictions'] = predictions

    # ── 7. Trend Scores ───────────────────────────────────────────────
    if 'product' in df.columns:
        result['trend_scores'] = _compute_trend_scores(df)

    # ── 8. Regional Demand (if region column exists) ──────────────────
    if 'region' in df.columns:
        regional = df.groupby('region')['quantity'].sum().sort_values(ascending=False)
        result['regional'] = {
            'labels': regional.index.tolist(),
            'values': regional.values.tolist()
        }

    # ── 9. Summary Stats ─────────────────────────────────────────────
    result['summary'] = {
        'total_records': len(df),
        'date_range': f"{df['date'].min().strftime('%b %Y')} – {df['date'].max().strftime('%b %Y')}",
        'total_units_sold': int(df['quantity'].sum()),
        'unique_products': int(df['product'].nunique()) if 'product' in df.columns else 0,
        'unique_categories': int(df['category'].nunique()) if 'category' in df.columns else 0,
        'top_region': df.groupby('region')['quantity'].sum().idxmax() if 'region' in df.columns else 'N/A'
    }

    return result


def _generate_predictions(df, analysis):
    """Generate forward-looking predictions using linear extrapolation."""
    predictions = []

    if 'product' not in df.columns:
        return predictions

    df['month_num'] = (df['date'].dt.year - df['date'].dt.year.min()) * 12 + df['date'].dt.month

    for product in df['product'].unique():
        pdata = df[df['product'] == product].groupby('month_num')['quantity'].sum().reset_index()
        if len(pdata) < 3:
            continue

        x = pdata['month_num'].values
        y = pdata['quantity'].values

        # Simple linear regression
        coeffs = np.polyfit(x, y, 1)
        slope = coeffs[0]
        
        # Predict next quarter (3 months ahead)
        next_x = x[-1] + 3
        pred_qty = max(0, np.polyval(coeffs, next_x))
        current_qty = y[-1]
        
        if current_qty > 0:
            change_pct = ((pred_qty - current_qty) / current_qty) * 100
        else:
            change_pct = 0

        if abs(change_pct) >= 5:  # Only notable predictions
            direction = "rise" if change_pct > 0 else "decline"
            predictions.append({
                'product': product,
                'direction': direction,
                'change_pct': round(abs(change_pct), 1),
                'predicted_qty': int(round(pred_qty)),
                'confidence': _confidence(len(pdata))
            })

    predictions.sort(key=lambda x: x['change_pct'], reverse=True)
    return predictions[:10]


def _confidence(n_points):
    if n_points >= 12:
        return 'High'
    elif n_points >= 6:
        return 'Medium'
    return 'Low'


def _compute_trend_scores(df):
    """Compute a 0-100 trend score per product based on recency and growth."""
    scores = []
    if 'product' not in df.columns:
        return scores

    now = df['date'].max()
    df['month_num'] = (df['date'].dt.year - df['date'].dt.year.min()) * 12 + df['date'].dt.month
    max_month = df['month_num'].max()

    for product in df['product'].unique():
        pdata = df[df['product'] == product]
        total = pdata['quantity'].sum()
        recency_months = pdata.groupby('month_num')['quantity'].sum()

        if len(recency_months) < 2:
            continue

        x = recency_months.index.values
        y = recency_months.values
        coeffs = np.polyfit(x, y, 1)
        slope = coeffs[0]

        # Normalize slope to 0-100
        max_slope = 50  
        trend_component = min(100, max(0, (slope / max_slope + 1) * 50))
        
        # Volume component
        all_totals = df.groupby('product')['quantity'].sum()
        vol_rank = (all_totals.rank(pct=True)[product]) * 100

        score = round(0.6 * trend_component + 0.4 * vol_rank, 1)
        scores.append({'product': product, 'score': score})

    scores.sort(key=lambda x: x['score'], reverse=True)
    return scores[:15]


def get_analysis_summary_text(analysis):
    """Convert analysis to a text summary for chatbot context."""
    parts = []

    if 'summary' in analysis:
        s = analysis['summary']
        parts.append(f"Dataset: {s['total_records']} records from {s['date_range']}, "
                     f"{s['total_units_sold']} total units sold across "
                     f"{s['unique_products']} products in {s['unique_categories']} categories.")

    if 'top_products' in analysis:
        top = list(zip(analysis['top_products']['labels'][:5], analysis['top_products']['values'][:5]))
        parts.append("Top 5 products by volume: " + ", ".join(f"{p} ({v} units)" for p, v in top))

    if 'category_demand' in analysis:
        cats = list(zip(analysis['category_demand']['labels'][:4], analysis['category_demand']['values'][:4]))
        parts.append("Top categories: " + ", ".join(f"{c} ({v} units)" for c, v in cats))

    if 'predictions' in analysis and analysis['predictions']:
        preds = analysis['predictions'][:4]
        pred_str = "; ".join(
            f"{p['product']} expected to {p['direction']} ~{p['change_pct']}% next quarter"
            for p in preds
        )
        parts.append(f"Trend predictions: {pred_str}.")

    if 'seasonal' in analysis:
        season_data = dict(zip(analysis['seasonal']['labels'], analysis['seasonal']['values']))
        top_season = max(season_data, key=season_data.get)
        parts.append(f"Peak selling season: {top_season}.")

    return " | ".join(parts)
