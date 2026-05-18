import streamlit as st
import pandas as pd
import sqlite3
import os

st.set_page_config(page_title="Cyborg Analytics", page_icon="🤖", layout="wide")

# =========================================================================
# 🎛️ MENÚ LATERAL (SIDEBAR)
# =========================================================================
st.sidebar.title("⚙️ Panel de Control")
st.sidebar.markdown("---")
deporte_seleccionado = st.sidebar.radio(
    "Selecciona la Liga a analizar:",
    ["🏀 NBA (Baloncesto)", "⚾ MLB (Béisbol)"]
)

# Variable lógica para filtrar la base de datos
liga_filtro = "NBA" if "NBA" in deporte_seleccionado else "MLB"

st.title(f"🤖 Cyborg Analytics - {liga_filtro}")
st.markdown("---")

db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'cyborg_db.sqlite')

try:
    conexion = sqlite3.connect(db_path)
    
    # Alerta de Lesiones (Por ahora solo la mostraremos si estamos en modo NBA)
    if liga_filtro == "NBA":
        try:
            cursor_lesiones = conexion.cursor()
            cursor_lesiones.execute("SELECT equipo, jugador, impacto_lambda FROM lesiones")
            lesionados = cursor_lesiones.fetchall()
            if lesionados:
                for l in lesionados:
                    st.error(f"🚨 **IMPACTO DE ÚLTIMA HORA DETECTADO:** {l[1]} ({l[0]}) es BAJA. El modelo ha penalizado su ofensiva con -{l[2]} puntos.")
        except Exception:
            pass 

    # Añadimos 'p.liga' a la consulta para poder separar los deportes
    query = """
    SELECT 
        p.liga AS Liga,
        p.equipo_local AS Local,
        p.equipo_visitante AS Visitante,
        c_ml.cuota_local AS Cuota_ML_Local,
        c_ml.cuota_visitante AS Cuota_ML_Visitante,
        c_to.linea AS Linea_Casa,
        c_to.cuota_local AS Cuota_Over,
        c_to.cuota_visitante AS Cuota_Under,
        pr.prob_cyborg_local AS Prob_Cyborg_Local,
        pr.linea_total_proyectada AS Linea_Proyectada,
        pr.prob_cyborg_over AS Prob_Cyborg_Over
    FROM partidos p
    LEFT JOIN cuotas c_ml ON p.id_partido = c_ml.id_partido AND c_ml.mercado = 'Moneyline'
    LEFT JOIN cuotas c_to ON p.id_partido = c_to.id_partido AND c_to.mercado = 'Totals'
    LEFT JOIN predicciones pr ON p.id_partido = pr.id_partido
    """
    
    df_completo = pd.read_sql_query(query, conexion)
    conexion.close()

    if not df_completo.empty:
        # 1. Filtramos solo los partidos del deporte que seleccionaste en el menú
        df = df_completo[df_completo['Liga'] == liga_filtro].copy()
        
        # 2. Escondemos los partidos que aún no han pasado por el cerebro matemático
        df = df.dropna(subset=['Prob_Cyborg_Local', 'Cuota_ML_Local', 'Cuota_Over'])
# 1. Filtramos solo los partidos del deporte que seleccionaste en el menú
        df = df_completo[df_completo['Liga'] == liga_filtro].copy()
        
        # --- NUEVO FILTRO ANTI-CLONES ---
        df = df.drop_duplicates(subset=['Local', 'Visitante'])
        
        # 2. Escondemos los partidos que aún no han pasado por el cerebro matemático
        df = df.dropna(subset=['Prob_Cyborg_Local', 'Cuota_ML_Local', 'Cuota_Over'])
        if not df.empty:
            tab1, tab2 = st.tabs(["🎯 Ganador del Partido (Moneyline)", "📊 Totales de Puntos (Over/Under)"])
            
            # --- PESTAÑA 1: GANADOR ---
            with tab1:
                st.subheader(f"Análisis de Ventaja (Ganador) - {liga_filtro}")
                df['Prob_Casa_Local'] = 1 / df['Cuota_ML_Local']
                df['Edge_Local'] = df['Prob_Cyborg_Local'] - df['Prob_Casa_Local']
                
                df_ml = pd.DataFrame({
                    'Partido': df['Local'] + " vs " + df['Visitante'],
                    'Cuota Local': df['Cuota_ML_Local'],
                    'Prob. Casa': (df['Prob_Casa_Local'] * 100).round(1).astype(str) + '%',
                    'Prob. Cyborg': (df['Prob_Cyborg_Local'] * 100).round(1).astype(str) + '%',
                    'Edge Ventaja (%)': (df['Edge_Local'] * 100).round(2)
                })
                
                st.dataframe(df_ml.style.map(lambda v: f"color: {'#00FF00' if v > 0 else '#FF4B4B'}; font-weight: bold", subset=['Edge Ventaja (%)']), use_container_width=True, hide_index=True)
                
                mejor_ml = df_ml.loc[df_ml['Edge Ventaja (%)'].idxmax()]
                if mejor_ml['Edge Ventaja (%)'] > 0:
                    st.success(f"🔥 **PICK RECOMENDADO GANADOR:** **{mejor_ml['Partido'].split(' vs ')[0]}** | Cuota: **{mejor_ml['Cuota Local']}** (Edge: +{mejor_ml['Edge Ventaja (%)']}%)")

            # --- PESTAÑA 2: OVER/UNDER ---
            with tab2:
                st.subheader(f"Análisis de Probabilidad Acumulada (Totales) - {liga_filtro}")
                
                df['Prob_Casa_Over'] = 1 / df['Cuota_Over']
                df['Prob_Casa_Under'] = 1 / df['Cuota_Under']
                df['Prob_Cyborg_Under'] = 1 - df['Prob_Cyborg_Over']
                df['Edge_Over'] = df['Prob_Cyborg_Over'] - df['Prob_Casa_Over']
                df['Edge_Under'] = df['Prob_Cyborg_Under'] - df['Prob_Casa_Under']
                
                df_ou = pd.DataFrame({
                    'Partido': df['Local'] + " vs " + df['Visitante'],
                    'Línea Casa': df['Linea_Casa'],
                    'Proyección Cyborg': df['Linea_Proyectada'].round(1),
                    'Cuota Over': df['Cuota_Over'],
                    'Prob. Over (Cyborg)': (df['Prob_Cyborg_Over'] * 100).round(1).astype(str) + '%',
                    'Edge Over (%)': (df['Edge_Over'] * 100).round(2),
                    'Cuota Under': df['Cuota_Under'],
                    'Prob. Under (Cyborg)': (df['Prob_Cyborg_Under'] * 100).round(1).astype(str) + '%',
                    'Edge Under (%)': (df['Edge_Under'] * 100).round(2)
                })
                
                st.dataframe(df_ou.style.map(lambda v: f"color: {'#00FF00' if v > 0 else '#FF4B4B'}; font-weight: bold", subset=['Edge Over (%)', 'Edge Under (%)']), use_container_width=True, hide_index=True)
                
                max_edge_over = df_ou['Edge Over (%)'].max()
                max_edge_under = df_ou['Edge Under (%)'].max()
                
                if max_edge_over > max_edge_under and max_edge_over > 0:
                    pick = df_ou.loc[df_ou['Edge Over (%)'].idxmax()]
                    st.success(f"🔥 **PICK RECOMENDADO TOTALES:** **Over {pick['Línea Casa']}** en el partido {pick['Partido']} | Cuota: **{pick['Cuota Over']}** (Edge: +{pick['Edge Over (%)']}%)")
                elif max_edge_under > max_edge_over and max_edge_under > 0:
                    pick = df_ou.loc[df_ou['Edge Under (%)'].idxmax()]
                    st.success(f"🔥 **PICK RECOMENDADO TOTALES:** **Under {pick['Línea Casa']}** en el partido {pick['Partido']} | Cuota: **{pick['Cuota Under']}** (Edge: +{pick['Edge Under (%)']}%)")
                else:
                    st.warning("⚠️ Sin valor matemático detectado en las líneas de Over/Under actuales.")
        else:
             st.info(f"⚾ Los partidos de la {liga_filtro} ya están en la base de datos, pero el Motor Matemático aún no ha calculado sus predicciones.")
    else:
        st.info("Por favor, ejecuta los scrapers para inicializar las tablas.")

except Exception as e:
    st.error(f"Error en la carga del Dashboard: {e}")