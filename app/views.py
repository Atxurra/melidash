from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from .models import Publication, Supply, Sale, ProcessedFile, PublicityCost, UnassignedPublication
from django.core.paginator import Paginator
from django.db.models import Sum, Q
from datetime import timedelta
import pandas as pd
import hashlib
import json
from datetime import datetime
from decimal import Decimal
import math

def normalize_date(date_str):
    if isinstance(date_str, str):
        try:
            if len(date_str.split('-')) == 3:
                year, month, day = date_str.split('-')
                datetime(int(year), int(month), int(day))
                return date_str
            day, month_str, year_time = date_str.split(" de ")
            year = year_time.split(" ")[0]
            month_map = {
                'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
                'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
                'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
            }
            month = month_map.get(month_str.lower(), '01')
            return f"{year}-{month}-{day.zfill(2)}"
        except Exception:
            return None
    return None

#versión legacy
def process_mercadolibre_file(file):
    try:
        df = pd.read_excel(file, header=5, dtype={'# de venta': str})
    except Exception as e:
        return [], f"Failed to read file: {str(e)}"
    column_names = [
        '# de venta', 'Fecha de venta', 'Estado (Venta)', 'Descripción del estado',
        'Paquete de varios productos', 'Pertenece a un kit', 'Unidades',
        'Ingresos por productos (CLP)', 'Cargo por venta e impuestos',
        'Ingresos por envío (CLP)', 'Costos de envío', 'Anulaciones y reembolsos (CLP)',
        'Total (CLP)', 'Mes de facturación de tus cargos', 'Venta por publicidad',
        'SKU', '# de publicación', 'Canal de venta', 'Título de la publicación',
        'Variante', 'Precio unitario de venta de la publicación (CLP)',
        'Tipo de publicación', 'Factura adjunta', 'Datos personales o de empresa',
        'Tipo y número de documento', 'Dirección', 'Tipo de contribuyente',
        'Actividad económica', 'Comprador', 'Cédula', 'Domicilio', 'Comuna',
        'Estado (Región)', 'Código postal', 'País', 'Forma de entrega',
        'Fecha en camino', 'Fecha entregado', 'Transportista', 'Número de seguimiento',
        'URL de seguimiento', 'Unidades (Envíos)', 'Forma de entrega (Devoluciones)',
        'Fecha en camino (Devoluciones)', 'Fecha entregado (Devoluciones)',
        'Transportista (Devoluciones)', 'Número de seguimiento (Devoluciones)',
        'URL de seguimiento (Devoluciones)', 'Revisado por Mercado Libre',
        'Fecha de revisión', 'Dinero a favor', 'Resultado', 'Destino',
        'Motivo del resultado', 'Unidades (Reclamos)', 'Reclamo abierto',
        'Reclamo cerrado', 'Con mediación'
    ]
    if len(df.columns) != len(column_names):
        return [], "Invalid column structure in Excel file."
    df.columns = column_names
    df = df[df['# de venta'].notna() & df['# de venta'].str.startswith('20')]
    df = df.reset_index(drop=True)
    sales_data = []
    for _, row in df.iterrows():
        sale_id = str(int(float(row.get('# de venta', ''))))
        if not sale_id.startswith('20'):
            continue
        def safe_decimal(value):
            try:
                return Decimal(value) if pd.notna(value) and value != '' else Decimal('0.0')
            except (ValueError, TypeError):
                return Decimal('0.0')
        sales_data.append({
            'sale_id': sale_id,
            'publication_name': row.get('Título de la publicación', 'Unknown'),
            'buyer': row.get('Comprador', 'Unknown'),
            'status': row.get('Estado (Venta)', 'Unknown'),
            'date': normalize_date(row.get('Fecha de venta', '')),
            'units': int(row.get('Unidades', 1) or 1) if pd.notna(row.get('Unidades')) else None,
            'income': safe_decimal(row.get('Ingresos por productos (CLP)')),
            'transaction_costs': safe_decimal(row.get('Cargo por venta e impuestos')),
            'shipping_costs': safe_decimal(row.get('Costos de envío')),
            'refunds': safe_decimal(row.get('Anulaciones y reembolsos (CLP)')),
            'total': safe_decimal(row.get('Total (CLP)')),
            'source': 'MercadoLibre',
            'delivery_method': row.get('Forma de entrega', ''),
            'dispatch_date': normalize_date(row.get('Fecha en camino', '')) if row.get('Fecha en camino') else None,
            'arrived': bool(row.get('Fecha entregado'))
        })
    return sales_data, None

#versión que no ajusta stocks de devueltos al repasarlos, atento a bugs
def process_mercadolibre_file(file, previous_sales_data=None):
    try:
        df = pd.read_excel(file, header=5, dtype={'# de venta': str})
    except Exception as e:
        return [], f"Failed to read file: {str(e)}"
    
    column_names = [
        '# de venta', 'Fecha de venta', 'Estado (Venta)', 'Descripción del estado',
        'Paquete de varios productos', 'Pertenece a un kit', 'Unidades',
        'Ingresos por productos (CLP)', 'Cargo por venta e impuestos',
        'Ingresos por envío (CLP)', 'Costos de envío', 'Anulaciones y reembolsos (CLP)',
        'Total (CLP)', 'Mes de facturación de tus cargos', 'Venta por publicidad',
        'SKU', '# de publicación', 'Canal de venta', 'Título de la publicación',
        'Variante', 'Precio unitario de venta de la publicación (CLP)',
        'Tipo de publicación', 'Factura adjunta', 'Datos personales o de empresa',
        'Tipo y número de documento', 'Dirección', 'Tipo de contribuyente',
        'Actividad económica', 'Comprador', 'Cédula', 'Domicilio', 'Comuna',
        'Estado (Región)', 'Código postal', 'País', 'Forma de entrega',
        'Fecha en camino', 'Fecha entregado', 'Transportista', 'Número de seguimiento',
        'URL de seguimiento', 'Unidades (Envíos)', 'Forma de entrega (Devoluciones)',
        'Fecha en camino (Devoluciones)', 'Fecha entregado (Devoluciones)',
        'Transportista (Devoluciones)', 'Número de seguimiento (Devoluciones)',
        'URL de seguimiento (Devoluciones)', 'Revisado por Mercado Libre',
        'Fecha de revisión', 'Dinero a favor', 'Resultado', 'Destino',
        'Motivo del resultado', 'Unidades (Reclamos)', 'Reclamo abierto',
        'Reclamo cerrado', 'Con mediación'
    ]
    
    if len(df.columns) != len(column_names):
        return [], "Invalid column structure in Excel file."
    
    df.columns = column_names
    df = df[df['# de venta'].notna() & df['# de venta'].str.startswith('20')]
    df = df.reset_index(drop=True)
    
    cancellation_statuses = [
        'Cancelada por el comprador',
        'Cancelaste la venta',
        'Devolución finalizada con reembolso al comprador'
    ]
    
    sales_data = []
    messages = []
    
    for _, row in df.iterrows():
        sale_id = str(int(float(row.get('# de venta', ''))))
        if not sale_id.startswith('20'):
            continue
            
        def safe_decimal(value):
            try:
                return Decimal(value) if pd.notna(value) and value != '' else Decimal('0.0')
            except (ValueError, TypeError):
                return Decimal('0.0')
        
        current_status = row.get('Estado (Venta)', 'Unknown')
        is_cancellation = (current_status in cancellation_statuses or 
                         current_status.lower().startswith('devuelto el '))
        
        # Check if this sale exists in previous data
        previous_sale = None
        if previous_sales_data:
            previous_sale = next((sale for sale in previous_sales_data 
                                if sale['sale_id'] == sale_id), None)
        
        # If it's a cancellation status and matches previous cancellation status, skip units update
        if previous_sale and is_cancellation:
            previous_status = previous_sale.get('status', '')
            was_previous_cancellation = (previous_status in cancellation_statuses or 
                                       previous_status.lower().startswith('devuelto el '))
            
            if was_previous_cancellation and previous_status == current_status:
                messages.append(f"El pedido de {row.get('Comprador', 'Unknown')}")
                continue
        
        sale_data = {
            'sale_id': sale_id,
            'publication_name': row.get('Título de la publicación', 'Unknown'),
            'buyer': row.get('Comprador', 'Unknown'),
            'status': current_status,
            'date': normalize_date(row.get('Fecha de venta', '')),
            'units': int(row.get('Unidades', 1) or 1) if pd.notna(row.get('Unidades')) else None,
            'income': safe_decimal(row.get('Ingresos por productos (CLP)')),
            'transaction_costs': safe_decimal(row.get('Cargo por venta e impuestos')),
            'shipping_costs': safe_decimal(row.get('Costos de envío')),
            'refunds': safe_decimal(row.get('Anulaciones y reembolsos (CLP)')),
            'total': safe_decimal(row.get('Total (CLP)')),
            'source': 'MercadoLibre',
            'delivery_method': row.get('Forma de entrega', ''),
            'dispatch_date': normalize_date(row.get('Fecha en camino', '')) if row.get('Fecha en camino') else None,
            'arrived': bool(row.get('Fecha entregado'))
        }
        
        sales_data.append(sale_data)
    
    return sales_data, messages if messages else None

def summary_view(request):
    publication_filter = request.GET.get('publication', '')
    
    # Fetch data
    publications = Publication.objects.all()
    if publication_filter:
        publications = publications.filter(publication_name=publication_filter)
    
    supplies = Supply.objects.all()
    sales = Sale.objects.all()
    publicity_costs = PublicityCost.objects.all()
    
    # Identify unassigned items
    unassigned_sales = Sale.objects.filter(publication__isnull=True)
    unassigned_supplies = Supply.objects.filter(publication__isnull=True)
    unallocated_publicity_costs = PublicityCost.objects.filter(publication__isnull=True)
    
    # Calculate implied stock and unallocated goods
    supply_units = supplies.aggregate(total_units=Sum('units', filter=Q(publication__in=publications)))['total_units'] or 0
    sale_units = sales.aggregate(total_units=Sum('units', filter=Q(publication__in=publications)))['total_units'] or 0
    implied_stock = supply_units - sale_units
    unallocated_supply_units = supplies.filter(publication__isnull=True).aggregate(total_units=Sum('units'))['total_units'] or 0
    
    # Stock graph data
    stock_data = []
    for supply in supplies.filter(publication__in=publications, arrival_date__isnull=False):
        stock_data.append({
            'date': supply.arrival_date,
            'units': int(supply.units or 0),
            'publication_name': supply.publication.publication_name if supply.publication else 'Unassigned',
            'type': 'supply'
        })
        if supply.purchase_date:
            stock_data.append({
                'date': supply.purchase_date,
                'units': 0,
                'publication_name': supply.publication.publication_name if supply.publication else 'Unassigned',
                'type': 'purchase_marker'
            })
    for sale in sales.filter(publication__in=publications, sale_date__isnull=False):
        stock_data.append({
            'date': sale.sale_date,
            'units': -int(sale.units or 0),
            'publication_name': sale.publication.publication_name if sale.publication else 'Unassigned',
            'type': 'sale'
        })
    
    stock_df = pd.DataFrame(stock_data)
    stock_traces = []
    purchase_markers = []
    projection_traces = []
    colors = ['#FF6666', '#FFB266', '#66CC99', '#6699CC', '#99CC66']
    
    if not stock_df.empty:
        stock_df['date'] = pd.to_datetime(stock_df['date'], errors='coerce')
        stock_df = stock_df.sort_values('date')
        latest_date = stock_df['date'].max()
        week_ago = latest_date - timedelta(days=2)
        
        # Calculate current stock per publication
        stock_summary = stock_df[stock_df['type'] != 'purchase_marker'].groupby('publication_name').agg({'units': 'sum'}).reset_index()
        stock_summary['units'] = stock_summary['units'].astype(int)
        
        # Filter for publications with at least one sale in the last 2 days
        recent_sales = stock_df[(stock_df['type'] == 'sale') & (stock_df['date'] >= week_ago)]
        pubs_with_recent_sales = recent_sales['publication_name'].unique()
        stock_summary = stock_summary[
            (stock_summary['units'] > 5) & (stock_summary['publication_name'].isin(pubs_with_recent_sales))
        ]
        
        # Calculate average purchase-to-arrival delay
        supply_delays = []
        for supply in supplies.filter(publication__in=publications, purchase_date__isnull=False, arrival_date__isnull=False):
            delay = (supply.arrival_date - supply.purchase_date).days
            if delay >= 0:
                supply_delays.append({'publication_name': supply.publication.publication_name, 'delay': delay})
        delay_df = pd.DataFrame(supply_delays)
        avg_delays = delay_df.groupby('publication_name')['delay'].mean().to_dict()
        avg_delays = {k: float(v) for k, v in avg_delays.items()}
        
        # Collect pending supplies
        pending_supplies = []
        for supply in supplies.filter(publication__in=publications, purchase_date__isnull=False, arrival_date__isnull=True):
            pending_supplies.append({
                'publication_name': supply.publication.publication_name,
                'purchase_date': supply.purchase_date,
                'units': int(supply.units or 0)
            })
        
        grouped = stock_df.groupby('publication_name')
        for i, (pub_name, group) in enumerate(grouped):
            stock_pivot = group[group['type'] != 'purchase_marker'][['date', 'units']].set_index('date').resample('D').sum().fillna(0)
            stock_pivot['units'] = stock_pivot['units'].astype(int)
            stock_pivot['cumulative'] = stock_pivot['units'].cumsum()
            stock_traces.append({
                'x': stock_pivot.index.strftime('%Y-%m-%d').tolist(),
                'y': stock_pivot['cumulative'].astype(int).tolist(),
                'type': 'scatter',
                'mode': 'lines',
                'name': f'{pub_name} Stock',
                'line': {'color': colors[i % len(colors)]}
            })
            purchase_points = group[group['type'] == 'purchase_marker']
            if not purchase_points.empty:
                purchase_markers.append({
                    'x': purchase_points['date'].dt.strftime('%Y-%m-%d').tolist(),
                    'y': [0] * len(purchase_points),
                    'type': 'scatter',
                    'mode': 'markers',
                    'name': f'{pub_name} Indicator',
                    'marker': {'color': colors[i % len(colors)], 'size': 10, 'symbol': 'circle'}
                })
            
            # Single-curve projection for publications with stock > 5 and recent sales
            if pub_name in stock_summary['publication_name'].values:
                current_stock = int(stock_summary[stock_summary['publication_name'] == pub_name]['units'].iloc[0])
                sales_data = group[(group['type'] == 'sale') & (group['units'] < 0)][['date', 'units']]
                avg_daily_sales = 0
                if not sales_data.empty:
                    sales_data['units'] = sales_data['units'].abs().astype(int)
                    # Group by date to sum units sold per day and count days with sales
                    daily_sales = sales_data.groupby(sales_data['date'].dt.date)['units'].sum().reset_index()
                    if not daily_sales.empty:
                        total_units_sold = daily_sales['units'].sum()
                        days_with_sales = len(daily_sales)
                        avg_daily_sales = float(total_units_sold / days_with_sales) if days_with_sales > 0 else 0
                
                # Get pending supplies for this publication
                pub_pending_supplies = [s for s in pending_supplies if s['publication_name'] == pub_name]
                avg_delay = avg_delays.get(pub_name, 0)
                
                if avg_daily_sales > 0 or pub_pending_supplies:
                    # Create projection timeline
                    last_date = stock_pivot.index.max()
                    max_projection_days = 365  # Limit to 1 year
                    projection_dates = pd.date_range(start=last_date + timedelta(days=1), periods=max_projection_days, freq='D')
                    projection_stock = [float(current_stock)]
                    current_stock_value = current_stock
                    supply_events = [
                        {'date': s['purchase_date'] + timedelta(days=avg_delay), 'units': s['units']}
                        for s in pub_pending_supplies if avg_delay > 0
                    ]
                    supply_events.sort(key=lambda x: x['date'])
                    
                    for i, date in enumerate(projection_dates):
                        # Apply daily decrease
                        if current_stock_value > 0 and avg_daily_sales > 0:
                            current_stock_value = max(0, current_stock_value - avg_daily_sales)
                        
                        # Apply pending supply arrivals
                        for event in supply_events:
                            if event['date'] == date.date():
                                current_stock_value += event['units']
                        
                        projection_stock.append(float(current_stock_value))
                        
                        # Stop projection if stock is 0 and no more pending supplies
                        if current_stock_value <= 0 and not any(e['date'] > date.date() for e in supply_events):
                            projection_dates = projection_dates[:i + 1]
                            projection_stock = projection_stock[:i + 2]
                            break
                    
                    if len(projection_dates) > 0:
                        projection_traces.append({
                            'x': projection_dates.strftime('%Y-%m-%d').tolist(),
                            'y': projection_stock[1:],
                            'type': 'scatter',
                            'mode': 'lines',
                            'name': f'{pub_name} Stock Projection',
                            'line': {'color': colors[i % len(colors)], 'dash': 'dash'}
                        })
    
    # Net Investment Curve
    investment_data = []
    for supply in supplies.filter(publication__in=publications):
        if supply.purchase_date:
            investment_data.append({
                'date': supply.purchase_date,
                'amount': -float(supply.total_cost or 0),
                'publication_name': supply.publication.publication_name if supply.publication else 'Unassigned'
            })
    for pc in publicity_costs.filter(publication__in=publications):
        if pc.date:
            investment_data.append({
                'date': pc.date,
                'amount': -float(pc.cost or 0),
                'publication_name': pc.publication.publication_name if pc.publication else 'Unassigned'
            })
    for sale in sales.filter(publication__in=publications, sale_date__isnull=False):
        investment_data.append({
            'date': sale.sale_date,
            'amount': float(sale.total or 0),
            'publication_name': sale.publication.publication_name if sale.publication else 'Unassigned'
        })
    
    investment_df = pd.DataFrame(investment_data)
    investment_traces = []
    if not investment_df.empty:
        investment_df['date'] = pd.to_datetime(investment_df['date'], errors='coerce')
        investment_df = investment_df.sort_values('date')
        grouped_investment = investment_df.groupby('publication_name')
        for i, (pub_name, group) in enumerate(grouped_investment):
            investment_pivot = group[['date', 'amount']].set_index('date').resample('D').sum().fillna(0)
            investment_pivot['amount'] = investment_pivot['amount'].astype(float)
            investment_pivot['cumulative'] = investment_pivot['amount'].cumsum()
            investment_traces.append({
                'x': investment_pivot.index.strftime('%Y-%m-%d').tolist(),
                'y': investment_pivot['cumulative'].astype(float).tolist(),
                'type': 'scatter',
                'mode': 'lines',
                'name': f'{pub_name} Net Investment',
                'line': {'color': colors[i % len(colors)]}
            })
    
    # Sales Summary
    sales_data = [
        {
            'date': s.sale_date,
            'amount': float(s.total or 0),
            'publication_name': s.publication.publication_name if s.publication else s.publication_name or 'Unassigned',
            'units': int(s.units or 0),
            'income': float(s.income or 0)
        }
        for s in sales if s.sale_date
    ]
    sales_df = pd.DataFrame(sales_data)
    
    sales_traces = []
    sales_count_traces = []
    if not sales_df.empty:
        sales_df['date'] = pd.to_datetime(sales_df['date'], errors='coerce')
        sales_pivot = sales_df.pivot_table(
            index='date', columns='publication_name', values='amount', aggfunc='sum', fill_value=0
        ).resample('D').sum().fillna(0)
        sales_pivot = sales_pivot.astype(float)
        sales_traces = [
            {
                'x': sales_pivot.index.strftime('%Y-%m-%d').tolist(),
                'y': sales_pivot[pub].tolist(),
                'type': 'scatter',
                'mode': 'lines',
                'name': pub,
                'line': {'color': colors[i % len(colors)]}
            } for i, pub in enumerate(sales_pivot.columns)
        ]
        
        sales_count_pivot = sales_df.pivot_table(
            index='date', columns='publication_name', values='units', aggfunc='count', fill_value=0
        ).resample('D').sum().fillna(0)
        sales_count_pivot = sales_count_pivot.astype(int)
        sales_count_traces = [
            {
                'x': sales_count_pivot.index.strftime('%Y-%m-%d').tolist(),
                'y': sales_count_pivot[pub].tolist(),
                'type': 'bar',
                'name': pub,
                'marker': {'color': colors[i % len(colors)]}
            } for i, pub in enumerate(sales_count_pivot.columns)
        ]
    
    # Publication Summary Table
    supply_costs_df = pd.DataFrame([
        {'publication_name': s.publication.publication_name, 'units': int(s.units or 0), 'cost': float(s.total_cost or 0)}
        for s in supplies if s.publication and s.total_cost
    ])
    publicity_costs_df = pd.DataFrame([
        {'publication_name': pc.publication.publication_name, 'cost': float(pc.cost or 0)}
        for pc in publicity_costs if pc.publication and pc.cost
    ])
    sales_summary_df = pd.DataFrame([
        {'publication_name': s.publication.publication_name, 'units': int(s.units or 0), 'income': float(s.income or 0)}
        for s in sales if s.publication and s.sale_date
    ])
    
    total_costs = pd.concat([
        supply_costs_df.groupby('publication_name')[['cost']].sum(),
        publicity_costs_df.groupby('publication_name')[['cost']].sum()
    ]).groupby('publication_name').sum().reset_index()
    total_costs['cost'] = total_costs['cost'].astype(float)
    total_sales = sales_summary_df.groupby('publication_name').agg({
        'units': 'sum',
        'income': 'sum'
    }).reset_index()
    total_sales['units'] = total_sales['units'].astype(int)
    total_sales['income'] = total_sales['income'].astype(float)
    
    supply_counts = supply_costs_df.groupby('publication_name').size().reset_index(name='supply_count')
    supply_counts['supply_count'] = supply_counts['supply_count'].astype(int)
    sales_counts = sales_summary_df.groupby('publication_name').size().reset_index(name='sales_count')
    sales_counts['sales_count'] = sales_counts['sales_count'].astype(int)
    publicity_counts = publicity_costs_df.groupby('publication_name').size().reset_index(name='publicity_count')
    publicity_counts['publicity_count'] = publicity_counts['publicity_count'].astype(int)
    
    summary_table = total_costs.merge(total_sales, on='publication_name', how='outer').fillna(0)
    summary_table = summary_table.merge(supply_counts, on='publication_name', how='left').fillna(0)
    summary_table = summary_table.merge(sales_counts, on='publication_name', how='left').fillna(0)
    summary_table = summary_table.merge(publicity_counts, on='publication_name', how='left').fillna(0)
    
    summary_table['sold_vs_invested_roi'] = summary_table.apply(
        lambda row: ((row['income'] - row['cost']) / row['cost'] * 100) if row['cost'] > 0 else 0, axis=1
    ).astype(float)
    
    total_invested = float(summary_table['cost'].sum())
    total_income = float(summary_table['income'].sum())
    total_roi = float((total_income - total_invested) / total_invested * 100) if total_invested > 0 else 0
    
    summary_table = summary_table[[
        'publication_name', 'sold_vs_invested_roi', 'units', 'income', 'cost', 
        'supply_count', 'sales_count', 'publicity_count'
    ]].to_dict('records')
    
    # Paginate sales
    sales_paginator = Paginator(sales, 10)
    page_number = request.GET.get('page', 1)
    page_obj = sales_paginator.get_page(page_number)
    
    plots = {
        'sales_plot': sales_traces,
        'sales_count_plot': sales_count_traces,
        'stock_plot': stock_traces + purchase_markers + projection_traces,
        'investment_plot': investment_traces
    }
    layout = {
        'sales_plot': {
            'title': {'text': 'Sales Income Over Time', 'x': 0.5, 'xanchor': 'center'},
            'xaxis': {'tickangle': 45, 'tickformat': '%Y-%m-%d'},
            'yaxis': {'title': 'Income ($)', 'tickformat': ',.0f'},
            'showlegend': True
        },
        'sales_count_plot': {
            'title': {'text': 'Sales Count Over Time', 'x': 0.5, 'xanchor': 'center'},
            'xaxis': {'tickangle': 45, 'tickformat': '%Y-%m-%d'},
            'yaxis': {'title': 'Number of Sales'},
            'showlegend': True
        },
        'stock_plot': {
            'title': {'text': 'Stock Levels Over Time (with Projections)', 'x': 0.5, 'xanchor': 'center'},
            'xaxis': {'tickangle': 45, 'tickformat': '%Y-%m-%d'},
            'yaxis': {'title': 'Stock Units'},
            'showlegend': True
        },
        'investment_plot': {
            'title': {'text': 'Net Investment Over Time', 'x': 0.5, 'xanchor': 'center'},
            'xaxis': {'tickangle': 45, 'tickformat': '%Y-%m-%d'},
            'yaxis': {'title': 'Net Investment ($)', 'tickformat': ',.0f'},
            'showlegend': True
        }
    }
    
    return render(request, 'summary.html', {
        'plots': json.dumps(plots, allow_nan=False),
        'layout': json.dumps(layout, allow_nan=False),
        'publications': publications,
        'selected_publication': publication_filter,
        'page_obj': page_obj,
        'unassigned_sales': unassigned_sales,
        'unassigned_supplies': unassigned_supplies,
        'unallocated_publicity_costs': unallocated_publicity_costs,
        'implied_stock': int(implied_stock),
        'unallocated_supply_units': int(unallocated_supply_units),
        'summary_table': summary_table,
        'total_roi': float(total_roi)
    })

def excel_processing_view(request):
    if request.method == 'POST':
        files = request.FILES.getlist('file')
        if not files:
            messages.error(request, "No files uploaded.")
            return redirect('excel_upload')
        
        total_new_sales = 0
        total_updated_sales = 0
        unassigned_names = set()
        errors = []
        
        with transaction.atomic():
            for file in files:
                if not file.name.endswith('.xlsx'):
                    errors.append(f"{file.name}: Only .xlsx files are supported.")
                    continue
                
                file_hash = hashlib.md5(file.read()).hexdigest()
                file.seek(0)
                processed_file, created = ProcessedFile.objects.get_or_create(
                    file_path=file.name,
                    defaults={'file_hash': file_hash, 'last_processed': timezone.now()}
                )
                if not created and processed_file.file_hash == file_hash:
                    errors.append(f"{file.name}: File already processed.")
                    continue
                
                sales_data, error = process_mercadolibre_file(file)
                if error:
                    errors.append(f"{file.name}: {error}")
                    continue
                if not sales_data:
                    errors.append(f"{file.name}: No valid sales data found.")
                    continue
                
                new_sales = 0
                updated_sales = 0
                
                for sale_data in sales_data:
                    publication_name = sale_data['publication_name']
                    publication = Publication.objects.filter(publication_name=publication_name).first()
                    if not publication:
                        UnassignedPublication.objects.get_or_create(publication_name=publication_name)
                        unassigned_names.add(publication_name)
                    
                    existing_sale = Sale.objects.filter(sale_id=sale_data['sale_id']).first()
                    if existing_sale:
                        old_units = existing_sale.units
                        old_status = existing_sale.status.lower()
                        old_total = existing_sale.total
                        if (sale_data['status'].lower() == old_status and
                                sale_data['units'] == old_units and
                                sale_data['total'] == old_total):
                            continue
                        existing_sale.previous_units = old_units
                        existing_sale.previous_status = existing_sale.status
                        existing_sale.previous_total = old_total
                        existing_sale.publication = publication
                        existing_sale.publication_name = publication_name
                        existing_sale.buyer = sale_data['buyer']
                        existing_sale.status = sale_data['status']
                        existing_sale.sale_date = sale_data['date']
                        existing_sale.units = sale_data['units']
                        existing_sale.income = sale_data['income']
                        existing_sale.transaction_costs = sale_data['transaction_costs']
                        existing_sale.shipping_costs = sale_data['shipping_costs']
                        existing_sale.refunds = sale_data['refunds']
                        existing_sale.total = sale_data['total']
                        existing_sale.source = sale_data['source']
                        existing_sale.dispatch_date = sale_data['dispatch_date']
                        existing_sale.delivery_method = sale_data['delivery_method']
                        existing_sale.arrived = sale_data['arrived']
                        existing_sale.save()
                        updated_sales += 1
                    else:
                        Sale.objects.create(
                            sale_id=sale_data['sale_id'],
                            publication=publication,
                            publication_name=publication_name,
                            buyer=sale_data['buyer'],
                            status=sale_data['status'],
                            sale_date=sale_data['date'],
                            dispatch_date=sale_data['dispatch_date'],
                            delivery_method=sale_data['delivery_method'],
                            units=sale_data['units'],
                            income=sale_data['income'],
                            transaction_costs=sale_data['transaction_costs'],
                            shipping_costs=sale_data['shipping_costs'],
                            refunds=sale_data['refunds'],
                            total=sale_data['total'],
                            source=sale_data['source'],
                            arrived=sale_data['arrived']
                        )
                        new_sales += 1
                
                total_new_sales += new_sales
                total_updated_sales += updated_sales
                processed_file.file_hash = file_hash
                processed_file.last_processed = timezone.now()
                processed_file.save()
        
        if total_new_sales + total_updated_sales > 0:
            messages.success(request, f"Processed {total_new_sales + total_updated_sales} sales across all files: {total_new_sales} new, {total_updated_sales} updated.")
        for error in errors:
            messages.error(request, error)
        
        if unassigned_names:
            return redirect('assign_publications')
        return redirect('summary')
    
    return render(request, 'excel_upload.html')

def assign_publications(request):
    if request.method == 'POST':
        with transaction.atomic():
            for key, value in request.POST.items():
                if key.startswith('publication_'):
                    unassigned_id = key.split('_')[1]
                    unassigned = UnassignedPublication.objects.filter(id=unassigned_id).first()
                    if not unassigned:
                        continue
                    publication_name = unassigned.publication_name
                    if value == 'new':
                        publication, _ = Publication.objects.get_or_create(
                            publication_name=publication_name,
                            defaults={'created_at': timezone.now().date()}
                        )
                    else:
                        publication = Publication.objects.filter(id=value).first()
                        if not publication:
                            continue
                    Sale.objects.filter(
                        publication_name=publication_name,
                        publication__isnull=True
                    ).update(publication=publication)
                    unassigned.delete()
            messages.success(request, "Publications assigned successfully.")
        return redirect('summary')
    
    unassigned = UnassignedPublication.objects.all()
    publications = Publication.objects.all()
    unassigned_with_sales = []
    for item in unassigned:
        sample_sales = Sale.objects.filter(
            publication_name=item.publication_name,
            publication__isnull=True
        )[:5]
        unassigned_with_sales.append({
            'id': item.id,
            'publication_name': item.publication_name,
            'sample_sales': sample_sales
        })
    return render(request, 'assign_publications.html', {
        'unassigned': unassigned_with_sales,
        'publications': publications
    })