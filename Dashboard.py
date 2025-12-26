import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime
import plotly.graph_objects as go
import numpy as np

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Dashboard Microsip - Inteligencia de Negocios",
    page_icon="📊",
    layout="wide"
)

# --- FUNCIÓN DE CARGA Y LIMPIEZA DE DATOS ---
@st.cache_data
def load_data(file_path):
    try:
        # Detectar si el archivo existe
        if not os.path.exists(file_path):
            return None

        df = pd.read_csv(file_path)
        
        # 1. Normalización de Nombres de Columnas
        df.columns = df.columns.str.strip()
        
        # 2. Manejo de Fechas
        if 'FECHA' in df.columns:
            df['FECHA'] = pd.to_datetime(df['FECHA'], errors='coerce')
        
        # 3. Limpieza de Moneda y Números
        # Agregamos TOTAL_FACTURA, SUBTOTAL_FACTURA, IMPUESTOS_FACTURA a la limpieza
        cols_moneda = [
            'PRECIO_UNITARIO_FINAL', 'TOTAL_TICKET_PAGADO', 
            'DINERO_RECIBIDO', 'CAMBIO_CALCULADO', 
            'MONTO_DESCUENTO', 'PRECIO_RENGLON_IVA', 'TOTAL_TICKET_IVA',
            'TOTAL_FACTURA', 'SUBTOTAL_FACTURA', 'IMPUESTOS_FACTURA',
            'PRECIO_UNITARIO', 'IMPORTE_RENGLON'
        ]
        
        for col in cols_moneda:
            if col in df.columns:
                # Quitamos signos de pesos y comas, convertimos a numérico
                df[col] = df[col].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # 4. Limpieza de Porcentajes
        if '%_DESCUENTO' in df.columns:
            df['%_DESCUENTO'] = df['%_DESCUENTO'].astype(str).str.replace('%', '', regex=False)
            df['%_DESCUENTO'] = pd.to_numeric(df['%_DESCUENTO'], errors='coerce').fillna(0)

        # 5. Lógica de Importe Real para Ventas
        # Solo aplica si es el archivo de Ventas (tiene TIPO_MOV)
        if 'TIPO_MOV' in df.columns:
            # Calculamos importe renglón si no existe explícitamente limpio
            if 'IMPORTE_RENGLON_CALC' not in df.columns:
                # Prioridad: Importe Renglon -> Precio Final * Cantidad
                if 'PRECIO_UNITARIO_FINAL' in df.columns and 'CANTIDAD' in df.columns:
                    df['IMPORTE_RENGLON_CALC'] = df['PRECIO_UNITARIO_FINAL'] * df['CANTIDAD']
                else:
                    df['IMPORTE_RENGLON_CALC'] = 0.0

            df['IMPORTE_REAL'] = df.apply(
                lambda x: -abs(x['IMPORTE_RENGLON_CALC']) if str(x['TIPO_MOV']).upper() == 'DEVOLUCION' else x['IMPORTE_RENGLON_CALC'], axis=1
            )
        
        # 6. Corrección de Hora y Fecha String
        if 'HORA' in df.columns:
            def parse_hour_intelligent(h_str):
                h_str = str(h_str).strip()
                try:
                    return datetime.strptime(h_str, '%I:%M %p').hour # AM/PM
                except:
                    try:
                        return int(h_str.split(':')[0]) # Militar
                    except:
                        return 0
            
            df['HORA_NUM'] = df['HORA'].apply(parse_hour_intelligent)
            
        if 'FECHA' in df.columns:
            df['FECHA_STR'] = df['FECHA'].dt.strftime('%Y-%m-%d')

        return df

    except Exception as e:
        st.error(f"Error al procesar el archivo {file_path}: {e}")
        return None

# --- CARGA DE ARCHIVOS ---
#st.title("📊 Dashboard de Ventas Ferretería")
#st.markdown("---")

ruta_ventas = os.path.join(os.getcwd(), "Reporte_Ventas_Historico.csv")
ruta_facturas = os.path.join(os.getcwd(), "Reporte_Facturas_Detallado.csv")

# ... (código existente de carga de ventas y facturas)
ruta_cortes = os.path.join(os.getcwd(), "Reporte_Cortes_Detallado.csv")
df_cortes = load_data(ruta_cortes)

# Limpieza especifica para Cortes (Asegurar que columnas clave sean numéricas)
if df_cortes is not None:
    cols_corte_num = ['VENTAS_TOT', 'RETIROS', 'SISTEMA_DE_EFECTIVO', 'REAL_CONTADO', 'DIFERENCIA']
    for col in cols_corte_num:
        if col in df_cortes.columns:
            # Limpiar signos de $ y comas si load_data no lo cubrió
            df_cortes[col] = df_cortes[col].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False)
            df_cortes[col] = pd.to_numeric(df_cortes[col], errors='coerce').fillna(0)

df_ventas = load_data(ruta_ventas)
df_facturas = load_data(ruta_facturas)

if df_ventas is None:
    st.warning(f"No se encontró el archivo principal: `Reporte_Ventas_Historico.csv`. Por favor cárgalo o genéralo.")
    uploaded_file = st.file_uploader("Subir Reporte de Ventas", type=["csv"])
    if uploaded_file:
        df_ventas = load_data(uploaded_file)

# --- INICIO DEL DASHBOARD ---
if df_ventas is not None:
    
    # --- FILTROS SIDEBAR ---
    sidebar = st.sidebar
    #sidebar.header("Filtros Globales")
    
    # 1. Rango de Fechas (Basado en Ventas)
    min_date = df_ventas['FECHA'].min().date()
    max_date = df_ventas['FECHA'].max().date()
    
    # --- INICIO DE LA MODIFICACIÓN (Mes a la Fecha) ---
    hoy = datetime.now().date()
    
    # A. Definimos la Fecha Final:
    # Intentamos usar "hoy", pero si tu archivo de datos es viejo (ej. mes pasado) 
    # y "hoy" se sale del rango, usamos la última fecha disponible en el archivo.
    fecha_fin_default = hoy if (hoy <= max_date) else max_date
    
    # B. Definimos la Fecha Inicial:
    # Calculamos el día 1 del mes correspondiente a la fecha final.
    inicio_mes = fecha_fin_default.replace(day=1)
    
    # Validamos: Si el día 1 del mes es anterior a lo que tienen tus datos (min_date),
    # usamos min_date para no generar error.
    fecha_inicio_default = max(inicio_mes, min_date)
    hoy_real = datetime.now().date()

    # C. Configuramos el widget
    date_range = sidebar.date_input(
        "Rango de Fechas", 
        value=(fecha_inicio_default, fecha_fin_default), # Tupla (Inicio, Fin)
        min_value=min_date, 
        max_value=max(max_date, hoy_real)
    )
    
    # Filtrado de Ventas
    if len(date_range) == 2:
        start_date, end_date = date_range
        mask_ventas = (df_ventas['FECHA'].dt.date >= start_date) & (df_ventas['FECHA'].dt.date <= end_date)
        df_v_filtered = df_ventas[mask_ventas]
        
        # --- CÁLCULO DE PERÍODO ANTERIOR (MISMO RANGO, AÑO PASADO) ---
        dias_diferencia = (end_date - start_date).days
        start_date_ly = start_date.replace(year=start_date.year - 1)
        end_date_ly = end_date.replace(year=end_date.year - 1)
        
        mask_ventas_ly = (df_ventas['FECHA'].dt.date >= start_date_ly) & (df_ventas['FECHA'].dt.date <= end_date_ly)
        df_v_filtered_ly = df_ventas[mask_ventas_ly]
    else:
        df_v_filtered = df_ventas
        df_v_filtered_ly = pd.DataFrame()  # Sin comparación si no hay rango definido

    # Filtrado de Facturas (Si existe el archivo)
    df_f_filtered = pd.DataFrame() # Vacío por defecto
    total_facturado_kpi = 0.0
    
    if df_facturas is not None:
        if len(date_range) == 2:
            mask_facturas = (df_facturas['FECHA'].dt.date >= start_date) & (df_facturas['FECHA'].dt.date <= end_date)
            df_f_filtered = df_facturas[mask_facturas]
        else:
            df_f_filtered = df_facturas
            
        # --- CÁLCULO DE TOTAL FACTURADO ---
        # 1. Filtramos solo vigentes (no canceladas)
        # 2. Eliminamos duplicados por FOLIO_INTERNO para no sumar renglones repetidos
        if not df_f_filtered.empty and 'TOTAL_FACTURA' in df_f_filtered.columns:
            # Normalizamos estatus a mayúsculas
            df_f_filtered['ESTATUS'] = df_f_filtered['ESTATUS'].astype(str).str.upper()
            
            facturas_unicas = df_f_filtered[df_f_filtered['ESTATUS'] != 'CANCELADA'].drop_duplicates(subset=['FOLIO_INTERNO'])
            total_facturado_kpi = facturas_unicas['TOTAL_FACTURA'].sum()

    # Filtros Dinámicos (Solo afectan a ventas visualmente, lógica de negocio)
    if 'SUCURSAL' in df_v_filtered.columns:
        almacenes = ["Todos"] + list(df_v_filtered['SUCURSAL'].unique())
        sel_alm = sidebar.selectbox("Tienda", almacenes)
        if sel_alm != "Todos": 
            df_v_filtered = df_v_filtered[df_v_filtered['SUCURSAL'] == sel_alm]

    if 'LINEA' in df_v_filtered.columns:
        lineas = ["Todas"] + list(df_v_filtered['LINEA'].unique())
        sel_lin = sidebar.selectbox("Línea", lineas)
        if sel_lin != "Todas": 
            df_v_filtered = df_v_filtered[df_v_filtered['LINEA'] == sel_lin]

# --- 1. CÁLCULOS KPI PRINCIPALES (BASADOS EN CORTES DE CAJA) ---
    venta_neta_kpi = 0.0
    venta_neta_ly = 0.0
    venta_bancos = 0.0
    pct_bancos = 0.0
    total_retiros_kpi = 0.0

    if df_cortes is not None:
        # Filtrado de Cortes (Periodo Actual)
        mask_c = (df_cortes['FECHA'].dt.date >= start_date) & (df_cortes['FECHA'].dt.date <= end_date)
        df_c_filtered_kpi = df_cortes[mask_c].copy()
        
        # Filtrado de Cortes (Año Pasado)
        mask_c_ly = (df_cortes['FECHA'].dt.date >= start_date_ly) & (df_cortes['FECHA'].dt.date <= end_date_ly)
        df_c_ly_kpi = df_cortes[mask_c_ly].copy()

        # Aplicar filtro de Sucursal
        if sel_alm != "Todos":
            df_c_filtered_kpi = df_c_filtered_kpi[df_c_filtered_kpi['SUCURSAL'] == sel_alm]
            if not df_c_ly_kpi.empty:
                df_c_ly_kpi = df_c_ly_kpi[df_c_ly_kpi['SUCURSAL'] == sel_alm]

        # Totales Dinero
        venta_neta_kpi = df_c_filtered_kpi['VENTAS_TOTALES_NETAS'].sum()
        venta_neta_ly = df_c_ly_kpi['VENTAS_TOTALES_NETAS'].sum() if not df_c_ly_kpi.empty else 0.0
        
        venta_bancos = df_c_filtered_kpi['PAGO_DEBITO'].sum() + df_c_filtered_kpi['PAGO_CREDITO'].sum()
        pct_bancos = (venta_bancos / venta_neta_kpi * 100) if venta_neta_kpi > 0 else 0
        total_retiros_kpi = df_c_filtered_kpi['RETIROS'].sum()

    # --- 2. CÁLCULOS DE VOLUMEN (TICKETS Y PROMEDIOS) ---
    # Periodo Actual
    total_tickets = df_v_filtered[df_v_filtered['TIPO_MOV'] == 'VENTA']['FOLIO'].nunique()
    ticket_promedio = venta_neta_kpi / total_tickets if total_tickets > 0 else 0.0

    # Periodo Año Pasado (DEFINICIONES FALTANTES)
    total_tickets_ly = 0
    ticket_promedio_ly = 0.0
    if not df_v_filtered_ly.empty:
        total_tickets_ly = df_v_filtered_ly[df_v_filtered_ly['TIPO_MOV'] == 'VENTA']['FOLIO'].nunique()
        ticket_promedio_ly = venta_neta_ly / total_tickets_ly if total_tickets_ly > 0 else 0.0

    # --- 3. VARIACIONES (%) ---
    var_venta = ((venta_neta_kpi - venta_neta_ly) / venta_neta_ly * 100) if venta_neta_ly > 0 else 0.0
    var_ticket_prom = ((ticket_promedio - ticket_promedio_ly) / ticket_promedio_ly * 100) if ticket_promedio_ly > 0 else 0.0

    # --- 4. DEVOLUCIONES ---
    df_devs = df_v_filtered[df_v_filtered['TIPO_MOV'] == 'DEVOLUCION']
    total_devoluciones = df_devs['IMPORTE_REAL'].sum() if not df_devs.empty else 0.0
    num_devoluciones = df_devs['FOLIO'].nunique()
    
    total_devoluciones_ly = 0.0
    if not df_v_filtered_ly.empty:
        df_devs_ly = df_v_filtered_ly[df_v_filtered_ly['TIPO_MOV'] == 'DEVOLUCION']
        total_devoluciones_ly = abs(df_devs_ly['IMPORTE_REAL'].sum())
    
    var_devs_pct = ((abs(total_devoluciones) - total_devoluciones_ly) / total_devoluciones_ly * 100) if total_devoluciones_ly > 0 else 0.0

    # --- 5. PROMEDIOS DIARIOS ---
    # Actual
    num_dias_seleccionados = df_c_filtered_kpi['FECHA'].nunique()
    dias_p_act = num_dias_seleccionados if num_dias_seleccionados > 0 else 1
    venta_promedio_dia = venta_neta_kpi / dias_p_act
    tickets_promedio_dia = total_tickets / dias_p_act

    # Año Pasado (Para comparar promedios diarios)
    num_dias_ly = df_c_ly_kpi['FECHA'].nunique() if not df_c_ly_kpi.empty else 0
    dias_p_ly = num_dias_ly if num_dias_ly > 0 else 1
    venta_prom_dia_ly = venta_neta_ly / dias_p_ly if venta_neta_ly > 0 else 0.0
    tickets_prom_dia_ly = total_tickets_ly / dias_p_ly if total_tickets_ly > 0 else 0.0

    # Variaciones de promedios diarios
    var_vpd = ((venta_promedio_dia - venta_prom_dia_ly) / venta_prom_dia_ly * 100) if venta_prom_dia_ly > 0 else 0.0
    var_tpd = ((tickets_promedio_dia - tickets_prom_dia_ly) / tickets_prom_dia_ly * 100) if tickets_prom_dia_ly > 0 else 0.0

    # --- PESTAÑAS DEL DASHBOARD ---
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Resumen", "🕒 Tiempo", "👥 Personal", "📦 Productos"])

    # TAB 1: RESUMEN
    with tab1:
            # Fila 1: KPIs Principales desde Cortes
            c1, c2, c3, c4 = st.columns(4)
            
            c1.metric("Venta Neta", f"${venta_neta_kpi:,.2f}", f"{var_venta:+.1f}% vs año ant.")
            c2.metric("Total Facturado", f"${total_facturado_kpi:,.2f}", help="Suma de Facturas Vigentes")
            c3.metric("Ticket Promedio", f"${ticket_promedio:,.2f}", help="Venta Cortes / Núm. Tickets")
            c4.metric("Ingreso Tarjetas", f"${venta_bancos:,.2f}", f"{pct_bancos:.1f}% del total")
            

              # FILA 2: KPIs de Operación (Volumen de Movimientos)
            #st.markdown("### 📑 Volumen de Operaciones")
            o1, o2, o3, o4 = st.columns(4)
            
            o1.metric("Tickets Emitidos", f"{total_tickets:,}")
            delta_texto = f"{var_devs_pct:+.1f}% vs año ant." if total_devoluciones_ly > 0 else None

            o2.metric("Monto Devoluciones", f"${total_devoluciones:,.2f}", delta=delta_texto, delta_color="inverse")
            o3.metric("Núm. Devoluciones", f"{num_devoluciones}")
            
            # Un KPI extra útil: % de clientes que devuelven
            tasa_dev = (num_devoluciones / total_tickets * 100) if total_tickets > 0 else 0
            o4.metric("Tasa de Devolución", f"{tasa_dev:.1f}%", help="Porcentaje de tickets que terminan en devolución")

                    # FILA 3: KPIs Diarios (Promedios)
             
            p1, p2, p3, p4 = st.columns(4)
            p1.metric("Venta Promedio/Día", f"${venta_promedio_dia:,.2f}", f"{var_vpd:+.1f}%")
            p2.metric("Tickets Promedio/Día", f"{tickets_promedio_dia:.1f}", f"{var_tpd:+.1f}%")
            p3.metric("Total Retiros", f"${total_retiros_kpi:,.2f}", help="Suma de los retiros de efectivo registrados en cortes de caja")
            # Un KPI extra sugerido: Dinero retenido en caja (Fondo)
            fondo_total = df_c_filtered_kpi['FONDO_INICIAL'].sum()
            p4.metric("Fondo de Caja Total", f"${fondo_total:,.2f}", help="Suma de fondos iniciales del periodo")


            st.markdown("---")
            
            # Gráficas
            cg1, cg2 = st.columns(2)
            
            with cg1:
                #st.subheader("Ventas por Línea")
                if 'SUCURSAL' in df_v_filtered.columns:
                    v_linea = df_v_filtered.groupby('SUCURSAL')['IMPORTE_REAL'].sum().reset_index()
                    v_linea = v_linea.sort_values('IMPORTE_REAL', ascending=False).head(7)
                    fig = px.bar(v_linea, x='IMPORTE_REAL', y='SUCURSAL', orientation='h', text_auto='.2s', color='IMPORTE_REAL')
                    fig.update_traces(textposition='outside')
                    fig.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig, use_container_width=True)
 
            with cg2:
                #st.subheader("Desglose de Efectivo vs Tarjetas")
                # Creamos el desglose desde los datos de Cortes
                efectivo_total = df_c_filtered_kpi['PAGO_EFECTIVO_CALC'].sum()
                bancos_total = venta_bancos
                
                df_pay_corte = pd.DataFrame({
                    'Método': ['Efectivo', 'Tarjetas (D+C)'],
                    'Monto': [efectivo_total, bancos_total]
                })
                
                fig_pie = px.pie(df_pay_corte, values='Monto', names='Método', hole=0.4, 
                                color_discrete_sequence=['#2ca02c', '#1f77b4'])
                fig_pie.update_layout(showlegend=False)
                fig_pie.update_traces(texttemplate='<b>%{label}</b><br>$%{value:,.0f}<br><b>%{percent}</b>', 
                                    textfont=dict(size=14))
                st.plotly_chart(fig_pie, use_container_width=True)
 
# TAB 2: TIEMPO
# TAB 2: TIEMPO
    with tab2:
        # --- 0. SELECTOR DE AGRUPACIÓN ---
        col_t1, _ = st.columns([1, 3])
        with col_t1:
            tg = st.selectbox("Agrupar datos por:", ["Día", "Semana", "Mes"], key="agrupar_tiempo_v3")
        
        freq_map = {"Día": "D", "Semana": "W", "Mes": "MS"}
        frecuencia = freq_map[tg]

        # Diccionario de traducción para días
        dias_es = {
            "Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miércoles",
            "Thursday": "Jueves", "Friday": "Viernes", "Saturday": "Sábado", "Sunday": "Domingo"
        }

        if not df_c_filtered_kpi.empty:
            # 1. Procesar Datos Actuales
            df_plot_act = df_c_filtered_kpi.set_index('FECHA').resample(frecuencia)['VENTAS_TOTALES_NETAS'].sum().reset_index()
            df_plot_act.columns = ['FECHA', 'VENTAS_ACT']
            
            # --- NUEVA SECCIÓN: CÁLCULOS ESTADÍSTICOS ROBUSTOS ---
            ventas_serie = df_plot_act['VENTAS_ACT'].values
            n_puntos = len(ventas_serie)
            
            # A. Venta Mínima y Máxima
            v_min = df_plot_act['VENTAS_ACT'].min()
            v_max = df_plot_act['VENTAS_ACT'].max()
            v_avg = df_plot_act['VENTAS_ACT'].mean()

            # B. Estabilidad (Coeficiente de Variación)
            # CV = Desviación Estándar / Media. 
            # < 15%: Estable | 15-30%: Moderada | > 30%: Volátil
            v_std = df_plot_act['VENTAS_ACT'].std()
            cv = (v_std / v_avg) if v_avg > 0 else 0
            
            if cv < 0.15:
                estabilidad_txt = "✅ Estable"
                color_est = "normal"
            elif cv < 0.35:
                estabilidad_txt = "⚠️ Moderada"
                color_est = "normal"
            else:
                estabilidad_txt = "🚨 Volátil"
                color_est = "inverse"

            # C. Tendencia (Regresión Lineal Simple)
            # Calculamos la pendiente (slope) de la línea de mejor ajuste
            if n_puntos > 1:
                x = np.arange(n_puntos)
                y = ventas_serie
                slope, _ = np.polyfit(x, y, 1)
                
                # Definimos un umbral para considerar "Plana" (ej. 2% del promedio)
                umbral = v_avg * 0.02 
                if slope > umbral:
                    tendencia_txt = "📈 Alcista"
                elif slope < -umbral:
                    tendencia_txt = "📉 Bajista"
                else:
                    tendencia_txt = "➡️ Plana"
            else:
                tendencia_txt = "Insuficiente"

            # --- RENDERIZADO DE MÉTRICAS ---
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Venta Mínima", f"${v_min:,.0f}", help=f"Venta más baja registrada por {tg}")
            m2.metric("Venta Máxima", f"${v_max:,.0f}", help=f"Venta más alta registrada por {tg}")
            m3.metric("Estabilidad", estabilidad_txt, f"{cv:.1%}", delta_color=color_est, help="Basado en el Coeficiente de Variación. Entre menor sea el %, más predecible es tu venta.")
            m4.metric("Tendencia", tendencia_txt, help=f"Calculada mediante regresión lineal sobre los datos de {tg}")

            st.markdown("---")

            if not df_c_ly_kpi.empty:
                # 2. Procesar Datos Año Pasado
                df_plot_ly = df_c_ly_kpi.copy()
                df_plot_ly = df_plot_ly.set_index('FECHA').resample(frecuencia)['VENTAS_TOTALES_NETAS'].sum().reset_index()
                df_plot_ly['FECHA'] = df_plot_ly['FECHA'] + pd.DateOffset(years=1)
                df_plot_ly.columns = ['FECHA', 'VENTAS_LY']
                
                df_comp = pd.merge(df_plot_act, df_plot_ly, on='FECHA', how='outer').sort_values('FECHA')
            else:
                df_comp = df_plot_act.copy()
                df_comp['VENTAS_LY'] = None

            # Etiqueta de día para la gráfica de líneas
            df_comp['DIA_SEMANA'] = df_comp['FECHA'].dt.day_name().map(dias_es)

            fig = go.Figure()
            
            # --- LÍNEA AÑO PASADO ---
            fig.add_trace(go.Scatter(
                x=df_comp['FECHA'], y=df_comp['VENTAS_LY'],
                name='Año Pasado',
                customdata=df_comp['DIA_SEMANA'],
                line=dict(color='#BDC3C7', width=2, dash='dot'),
                connectgaps=True,
                mode='lines+text',
                text=[f"${y/1e3:.1f}k" if (not pd.isna(y) and y > 0) else "" for y in df_comp['VENTAS_LY']],
                textposition="top center",
                hovertemplate='<b>%{customdata}</b> %{x|%d-%b}<br>Pasado: $%{y:,.2f}<extra></extra>'
            ))
            
            # --- LÍNEA AÑO ACTUAL ---
            fig.add_trace(go.Scatter(
                x=df_comp['FECHA'], y=df_comp['VENTAS_ACT'],
                name='Actual',
                customdata=df_comp['DIA_SEMANA'],
                line=dict(color='#2ECC71', width=4),
                connectgaps=True,
                mode='lines+markers+text',
                text=[f"${y/1e3:.1f}k" if (not pd.isna(y) and y > 0) else "" for y in df_comp['VENTAS_ACT']],
                textposition="top center",
                textfont=dict(size=11, color='#2ECC71'),
                hovertemplate='<b>%{customdata}</b> %{x|%d-%b}<br>Actual: $%{y:,.2f}<extra></extra>'
            ))
            
            fig.update_layout(
                height=380, margin=dict(t=30, b=20, l=0, r=0), 
                hovermode='x unified', plot_bgcolor='rgba(0,0,0,0)', 
                showlegend=False,
                yaxis=dict(showticklabels=True, showgrid=True, gridcolor='#333', zeroline=False)
            )
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        
        # --- 2. DESGLOSE POR PERIODO (BARRAS) ---
        if not df_plot_act.empty:
            v_tmp = df_plot_act.copy()
            v_tmp.columns = ['FECHA', 'VENTAS_TOTALES_NETAS']
            
            # Agregamos el día de la semana para el hover de las barras
            v_tmp['DIA_SEMANA'] = v_tmp['FECHA'].dt.day_name().map(dias_es)
            
            if tg == "Día":
                label_x = 'FECHA'
                window = 7
                hover_fmt = '<b>%{customdata}</b> %{x|%d-%b}'
            elif tg == "Semana":
                label_x = 'FECHA'
                window = 4
                hover_fmt = '<b>Semana del %{x|%d-%b}</b>'
            else:
                v_tmp['Mes'] = v_tmp['FECHA'].dt.strftime('%b %Y')
                label_x = 'Mes'
                window = 3
                hover_fmt = '<b>%{x}</b>'

            v_tmp['TENDENCIA'] = v_tmp['VENTAS_TOTALES_NETAS'].rolling(window=window, center=True).mean()

            fig_bot = go.Figure()
            
            # BARRAS
            fig_bot.add_trace(go.Bar(
                x=v_tmp[label_x],
                y=v_tmp['VENTAS_TOTALES_NETAS'],
                name='Venta Real',
                customdata=v_tmp['DIA_SEMANA'],
                marker_color='#273746',
                opacity=0.8,
                text=v_tmp['VENTAS_TOTALES_NETAS'],
                texttemplate='%{text:$.2s}', 
                textposition='outside',
                hovertemplate=hover_fmt + '<br>Venta: $%{y:,.2f}<extra></extra>'
            ))
            
            # LÍNEA DE TENDENCIA
            fig_bot.add_trace(go.Scatter(
                x=v_tmp[label_x], y=v_tmp['TENDENCIA'],
                name='Tendencia',
                line=dict(color='#E74C3C', width=3, shape='spline'),
                mode='lines',
                hoverinfo='skip' # Para que no ensucie el hover de las barras
            ))
            
            fig_bot.update_layout(
                height=400, margin=dict(t=50, b=20, l=0, r=0), 
                plot_bgcolor='rgba(0,0,0,0)', hovermode='x unified',
                showlegend=False, 
                yaxis=dict(showticklabels=True, showgrid=True, gridcolor='#333')
            )
            st.plotly_chart(fig_bot, use_container_width=True)


# TAB 3: PERSONAL (INCLUYE AUDITORÍA Y GRÁFICAS)
    with tab3:
        if df_cortes is not None:
            # --- 1. DATOS DE AUDITORÍA (Métricas solicitadas) ---
            df_mod_audit = df_v_filtered[df_v_filtered['MODIF_PRECIO'].astype(str).str.contains('SI', na=False)] if 'MODIF_PRECIO' in df_v_filtered.columns else pd.DataFrame()
            df_hi_audit = df_v_filtered[df_v_filtered['%_DESCUENTO'] > 15] if '%_DESCUENTO' in df_v_filtered.columns else pd.DataFrame()
            df_z_audit = df_v_filtered[(df_v_filtered['IMPORTE_REAL'] == 0) & (df_v_filtered['TIPO_MOV'] == 'VENTA')]
            num_devs_docs = df_v_filtered[df_v_filtered['TIPO_MOV'] == 'DEVOLUCION']['FOLIO'].nunique()

            # --- A. BLOQUE DE AUDITORÍA AL PRINCIPIO ---
            #st.markdown("##### 🚨 Control de Auditoría de Ventas")
            am1, am2, am3, am4 = st.columns(4)
            am1.metric("Precios Manipulados", len(df_mod_audit), delta_color="inverse")
            am2.metric("Descuentos > 15%", len(df_hi_audit), delta_color="inverse")
            am3.metric("Devoluciones (Docs)", num_devs_docs, delta_color="inverse")
            am4.metric("Precio $0.00", len(df_z_audit), delta_color="inverse")
            
            #st.markdown("---")

            # 2. Preparación de datos de Cortes
            mask_c = (df_cortes['FECHA'].dt.date >= start_date) & (df_cortes['FECHA'].dt.date <= end_date)
            df_c_personal = df_cortes[mask_c].copy()
            
            if sel_alm != "Todos":
                df_c_personal = df_c_personal[df_c_personal['SUCURSAL'] == sel_alm]

            # ELIMINACIÓN DE OUTLIERS (> $30,000)
            df_c_personal = df_c_personal[df_c_personal['DIFERENCIA'].abs() <= 30000]

            if not df_c_personal.empty:
                # --- B. KPIs DE CAJA ---
                #st.markdown("##### 💰 Gestión de Caja")
                kc1, kc2, kc3, kc4 = st.columns(4)
                
                total_dif = df_c_personal['DIFERENCIA'].sum()
                total_cortes = df_c_personal['FOLIO_CORTE'].nunique()
                cortes_modificados = df_c_personal[df_c_personal['FUE_MODIFICADO'].astype(str).str.upper() == 'SI'].shape[0]
                total_retiros = df_c_personal['RETIROS'].sum()

                kc1.metric("Balance Total", f"${total_dif:,.2f}", help="Suma de diferencias de caja")
                kc2.metric("Cortes Realizados", total_cortes)
                kc3.metric("Cortes Modificados", cortes_modificados, delta_color="inverse")
                kc4.metric("Total Retiros", f"${total_retiros:,.2f}")

                # --- C. TABLA DE CAJEROS Y GRÁFICA DE FALTANTES ---
                perf_cajero = df_c_personal.groupby(['SUCURSAL', 'CAJERO']).agg({
                    'FOLIO_CORTE': 'count',
                    'VENTAS_TOTALES_NETAS': 'sum',
                    'DIFERENCIA': 'sum'
                }).reset_index()
                perf_cajero.columns = ['SUCURSAL','CAJERO', 'Cortes (#)', 'Ventas Totales ($)', 'Diferencia Neta ($)']

                col_tabla, col_graf = st.columns([2, 1])
                
                with col_tabla:
                   # st.markdown("##### 📋 Resumen por Cajero")
                    df_styled = perf_cajero.style.format({
                        'Ventas Totales ($)': "${:,.2f}",
                        'Diferencia Neta ($)': "${:,.2f}"
                    })
                    st.dataframe(df_styled, use_container_width=True)

                with col_graf:
                    perf_cajero['Color'] = perf_cajero['Diferencia Neta ($)'].apply(lambda x: 'Sobrante' if x >= 0 else 'Faltante')
                    fig_dif = px.bar(
                        perf_cajero, x='Diferencia Neta ($)', y='CAJERO', orientation='h', 
                        color='Color', color_discrete_map={'Sobrante': '#2ca02c', 'Faltante': '#d62728'},
                        text_auto='.2s', title="📉 Faltantes/Sobrantes",hover_data=['SUCURSAL'] 
                    )
                    fig_dif.update_layout(showlegend=False, height=300)
                    st.plotly_chart(fig_dif, use_container_width=True)

                st.markdown("---")

                # --- D. GRÁFICAS DE VENTAS Y MEJORES CLIENTES (RESTAURADAS) ---
               # st.markdown("##### 🏆 Desempeño Comercial")
                cg1, cg2 = st.columns(2)
                if 'CAJERO' in df_v_filtered.columns:
                     with cg1:
                        # 1. Cambiamos el groupby para incluir SUCURSAL
                        v_cajero_sales = df_v_filtered.groupby(['SUCURSAL', 'CAJERO'])['IMPORTE_REAL'].sum().reset_index().sort_values('IMPORTE_REAL', ascending=False)
                        
                        # 2. Agregamos hover_data al px.bar
                        fig_caj_sales = px.bar(
                            v_cajero_sales, 
                            x='CAJERO', 
                            y='IMPORTE_REAL', 
                            color='IMPORTE_REAL', 
                            text_auto='.2s', 
                            title="Ventas Totales por Cajero",
                            color_continuous_scale='Greens',
                            hover_data=['SUCURSAL']  # <--- AGREGA ESTA LÍNEA
                        )
                        fig_caj_sales.update_traces(textposition='outside')
                        st.plotly_chart(fig_caj_sales, use_container_width=True)

                                    
                if 'CLIENTE' in df_v_filtered.columns:
                    with cg2:
                        v_cliente = df_v_filtered.groupby('CLIENTE')['IMPORTE_REAL'].sum().reset_index().sort_values('IMPORTE_REAL', ascending=False).head(10)
                        fig_cli = px.bar(
                            v_cliente, x='IMPORTE_REAL', y='CLIENTE', orientation='h', 
                            color='IMPORTE_REAL', text_auto='.2s', title="Top 10 Mejores Clientes",
                            color_continuous_scale='Blues'
                        )
                        fig_cli.update_traces(textposition='outside')
                        fig_cli.update_layout(yaxis={'categoryorder':'total ascending'})
                        st.plotly_chart(fig_cli, use_container_width=True)

                st.markdown("---")
                if not df_v_filtered.empty:
                    # 1. Crear timestamp completo para calcular diferencias
                    # Asumimos que HORA ya viene en formato string legible o ya fue procesada
                    try:
                        df_time = df_v_filtered.copy()
                        # Intentamos reconstruir la fecha y hora exacta de cada ticket
                        df_time['FECHA_HORA'] = pd.to_datetime(df_time['FECHA_STR'] + ' ' + df_time['HORA'], errors='coerce')
                        df_time = df_time.dropna(subset=['FECHA_HORA']).sort_values('FECHA_HORA')

                        # 2. Calcular la diferencia de tiempo entre un ticket y el anterior (por sucursal/día)
                        df_time['GAP_MINUTOS'] = df_time.groupby(['SUCURSAL', 'FECHA'])['FECHA_HORA'].diff().dt.total_seconds() / 60
                        
                        # Filtramos Gaps extremos (ej. más de 4 horas) porque pueden ser cierres de comida o errores
                        # Solo contamos gaps entre 1 minuto y 120 minutos como "tiempo muerto operativo"
                        df_gaps = df_time[(df_time['GAP_MINUTOS'] > 0) & (df_time['GAP_MINUTOS'] <= 180)]

                        # 3. Cálculos de métricas
                        tiempo_entre_ventas = df_gaps['GAP_MINUTOS'].mean()
                        gap_maximo = df_gaps['GAP_MINUTOS'].max()
                        
                        # Identificar la hora con menos tickets (Tiempos muertos por horario)
                        df_time['HORA_SOLO'] = df_time['FECHA_HORA'].dt.hour
                        peor_hora = df_time.groupby('HORA_SOLO')['FOLIO'].nunique().idxmin()
                        mejor_hora = df_time.groupby('HORA_SOLO')['FOLIO'].nunique().idxmax()

                        # --- Visualización de Métricas de Tiempo ---
                        tm1, tm2, tm3, tm4 = st.columns(4)
                        
                        tm1.metric("Tiempo entre Ventas", f"{tiempo_entre_ventas:.1f} min", help="Promedio de minutos que pasan entre un ticket y otro.")
                        tm2.metric("Brecha Máxima", f"{gap_maximo:.0f} min", help="El periodo más largo de inactividad registrado entre tickets hoy.")
                        tm3.metric("Hora de Baja Venta", f"{int(peor_hora)}:00 hrs", help="La hora del día con menor volumen de tickets procesados.")
                        tm4.metric("Hora Pico", f"{int(mejor_hora)}:00 hrs", help="La hora con mayor flujo de clientes.")

                        # --- Gráfica de Calor (Heatmap) de Actividad por Hora ---
                        #st.markdown("##### 📅 Densidad de Ventas por Hora y Día")
                        
                        # Preparamos datos para el heatmap
                        df_time['DiaSemana'] = df_time['FECHA_HORA'].dt.day_name().map(dias_es)
                        heatmap_data = df_time.groupby(['DiaSemana', 'HORA_SOLO'])['FOLIO'].nunique().reset_index()
                        
                        # Ordenar días de la semana
                        orden_dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
                        
                        fig_heat = px.density_heatmap(
                            heatmap_data, 
                            x="HORA_SOLO", 
                            y="DiaSemana", 
                            z="FOLIO",
                            category_orders={"DiaSemana": orden_dias},
                            labels={'HORA_SOLO': 'Hora del Día', 'DiaSemana': 'Día', 'FOLIO': 'Tickets'},
                            color_continuous_scale="Viridis",
                            text_auto=True
                        )
                        fig_heat.update_layout(height=400)
                        st.plotly_chart(fig_heat, use_container_width=True)

                    except Exception as e:
                        st.info(f"Para calcular tiempos muertos, asegúrate de que la columna HORA esté en formato correcto. Error: {e}")


                # --- E. EXPANDERS DE AUDITORÍA DETALLADA (AL FINAL) ---
                exp1, exp2 = st.columns(2) # Opcional: ponerlos uno al lado del otro o uno abajo de otro
                
                with st.expander("⚠️ Ver Cortes con Alertas (Modificados o Diferencia > $50)"):
                    alertas = df_c_personal[
                        (df_c_personal['FUE_MODIFICADO'].astype(str).str.upper() == 'SI') | 
                        (abs(df_c_personal['DIFERENCIA']) > 50)
                    ][['FECHA', 'HORA', 'SUCURSAL', 'CAJA', 'CAJERO', 'VENTAS_TOTALES_NETAS', 'DIFERENCIA', 'FUE_MODIFICADO', 'USUARIO_MODIF']]
                    
                    if not alertas.empty:
                        st.dataframe(alertas.sort_values('FECHA', ascending=False), use_container_width=True)
                    else:
                        st.success("No hay cortes con alertas de descuadre.")

                with st.expander("🔍 Ver Detalle de Devoluciones del Periodo"):
                    if not df_devs.empty:
                        cols_mostrar = ['FECHA', 'HORA', 'CAJERO', 'FOLIO', 'ARTICULO', 'CANTIDAD', 'IMPORTE_REAL']
                        cols_existentes = [c for c in cols_mostrar if c in df_devs.columns]
                        st.dataframe(df_devs[cols_existentes].sort_values('FECHA', ascending=False), use_container_width=True)
                    else:
                        st.info("No se registraron devoluciones en este periodo.")

            else:
                st.info("No hay datos de cortes para los filtros seleccionados.")
        else:
            st.warning("Archivo de cortes no disponible.")
        st.markdown("---")
        
      
# TAB 4: PRODUCTOS (DISEÑO PROFESIONAL)
    with tab4:
        # --- 1. HEADER: MÉTRICAS CLAVE DEL CATÁLOGO ---
        # Calculamos métricas
        total_skus = df_v_filtered['CLAVE'].nunique()
        articulos_por_ticket = df_v_filtered.groupby('FOLIO')['CANTIDAD'].sum().mean()
        linea_top = df_v_filtered.groupby('LINEA')['IMPORTE_REAL'].sum().idxmax()
        
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Variedad de SKUs", f"{total_skus:,}", help="Total de productos distintos vendidos")
        with m2:
            st.metric("Artículos por Ticket", f"{articulos_por_ticket:.1f}", help="Promedio de productos en cada venta")
        with m3:
            st.metric("Línea Líder", linea_top)

        st.markdown("---")

        # --- 2. ÁREA DE CONTROL Y FILTROS ---
        # Usamos un expander para los controles para no saturar la vista
        with st.expander("🛠️ Configuración del Análisis de Productos", expanded=True):
            c_col1, c_col2, c_col3 = st.columns([2, 1, 1])
            with c_col1:
                crit = st.radio("Métrica de éxito:", ["Importe ($)", "Unidades (#)", "Frecuencia (Tickets)"], horizontal=True)
            with c_col2:
                top_n = st.select_slider("Cantidad de productos:", options=[5, 10, 15, 20, 30, 50], value=15)
            with c_col3:
                orden = st.toggle("Ver productos de baja rotación", value=False)

        # --- 3. PROCESAMIENTO DE DATOS ---
        g_cols = ['CLAVE', 'ARTICULO', 'LINEA']
        df_prod = df_v_filtered.groupby(g_cols).agg({
            'IMPORTE_REAL': 'sum',
            'CANTIDAD': 'sum',
            'FOLIO': 'nunique'
        }).reset_index()

        df_prod.columns = ['CLAVE', 'ARTICULO', 'LINEA', 'Ventas ($)', 'Unidades', 'Tickets']
        total_tickets_periodo = df_v_filtered['FOLIO'].nunique()
        df_prod['Penetración (%)'] = (df_prod['Tickets'] / total_tickets_periodo) * 100

        # Lógica de Ordenamiento
        sort_col = 'Ventas ($)' if crit == "Importe ($)" else ('Unidades' if crit == "Unidades (#)" else 'Tickets')
        df_prod = df_prod.sort_values(sort_col, ascending=orden)
        top_data = df_prod.head(top_n)

        # --- 4. VISUALIZACIÓN PRINCIPAL (TOP PRODUCTOS) ---
        #st.subheader(f"📊 {'Peores' if orden else 'Mejores'} {top_n} Productos por {crit}")
        
        fig_prod = px.bar(
            top_data, 
            x=sort_col, 
            y='ARTICULO', 
            orientation='h', 
            color=sort_col, # Gradiente basado en el valor
            color_continuous_scale='Blugrn',
            text_auto='.2s',
            labels={sort_col: crit, 'ARTICULO': 'Producto'}
        )
        
        fig_prod.update_traces(
            textposition='outside', 
            textfont=dict(size=12, color='white' if not orden else 'black'), # Texto claro
            cliponaxis=False
        )
        
        fig_prod.update_layout(
            yaxis={'categoryorder':'total ascending'}, 
            height=500,
            margin=dict(l=0, r=50, t=30, b=0),
            plot_bgcolor='rgba(0,0,0,0)',
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_prod, use_container_width=True)

        st.markdown("---")

        # --- 5. ANÁLISIS ESTRATÉGICO (PARETO Y DISTRIBUCIÓN) ---
        col_st1, col_st2 = st.columns([1, 2])
        
        with col_st1:
            st.subheader("🎯 Análisis de Pareto (80/20)")
            df_pareto = df_prod.sort_values('Ventas ($)', ascending=False).copy()
            df_pareto['Acumulado (%)'] = df_pareto['Ventas ($)'].cumsum() / df_pareto['Ventas ($)'].sum() * 100
            
            prod_80 = df_pareto[df_pareto['Acumulado (%)'] <= 80]
            conteo_80 = len(prod_80)
            pct_skus_80 = (conteo_80 / total_skus * 100) if total_skus > 0 else 0
            
            # Un diseño más visual para Pareto
            st.info(f"""
            **Resumen Estratégico:**
            - El **80% de tus ingresos** proviene de **{conteo_80}** productos.
            - Esto representa el **{pct_skus_80:.1f}%** de tu catálogo actual.
            """)
            
            # Tabla de eficiencia rápida
            st.markdown("##### 📋 Eficiencia de SKUs Top")
            st.dataframe(
                top_data[['ARTICULO', 'Penetración (%)']].head(10),
                column_config={
                    "Penetración (%)": st.column_config.ProgressColumn(
                        format="%.1f%%", min_value=0, max_value=100
                    )
                },
                use_container_width=True,
                hide_index=True
            )
        with col_st2:
            st.subheader("📦 Ventas por Línea")
            
            if 'LINEA' in df_v_filtered.columns:
                # 1. Agrupamos los datos por Línea
                v_linea = df_v_filtered.groupby('LINEA')['IMPORTE_REAL'].sum().reset_index()
                # 2. Tomamos las mejores (opcional, por ejemplo las top 10 para que no sea infinita)
                v_linea = v_linea.sort_values('IMPORTE_REAL', ascending=False).head(10)

                # 3. Creamos la gráfica con tu estilo
                fig_linea = px.bar(
                    v_linea, 
                    x='IMPORTE_REAL', 
                    y='LINEA', 
                    orientation='h', 
                    text_auto='.2s', 
                    color='IMPORTE_REAL',
                    color_continuous_scale='Blugrn' # Azul a Verde para mantener consistencia
                )
                
                fig_linea.update_layout(
                    yaxis={'categoryorder':'total ascending'},
                    font=dict(color="#2c3e50"), # Texto profesional
                    margin=dict(t=20, b=20, l=0, r=60), # Margen derecho para que no se corte el texto
                    plot_bgcolor='rgba(0,0,0,0)',
                    coloraxis_showscale=False, # Quitar barra lateral de color
                    height=450
                )
                
                # 4. Forzar etiquetas afuera, en negrita y legibles
                fig_linea.update_traces(
                    textfont=dict(size=12, color="white"), # Cambia a "black" si tu fondo es blanco
                    textposition="outside", 
                    cliponaxis=False,
                    texttemplate='%{x:$.2s}' # Negrita y formato moneda
                )
                
                st.plotly_chart(fig_linea, use_container_width=True)
            else:
                st.info("No se encontró la columna 'LINEA' en los datos.")
        # --- 6. TABLA DE EXPLORACIÓN DETALLADA (AL FINAL) ---
        st.markdown("---")
        with st.expander("🔍 Explorador de Inventario Vendido (Detalle Completo)"):
            st.dataframe(
                df_prod.sort_values('Ventas ($)', ascending=False),
                column_config={
                    "Ventas ($)": st.column_config.NumberColumn(format="$%.2f"),
                    "Penetración (%)": st.column_config.NumberColumn(format="%.2f%%"),
                    "Unidades": st.column_config.NumberColumn(format="%d u."),
                    "Tickets": st.column_config.NumberColumn(format="%d tkt.")
                },
                use_container_width=True,
                hide_index=True
            )