import streamlit as st
import sqlite3
import pandas as pd
import os

# Configuración inicial adaptada para móviles y escritorio
st.set_page_config(page_title="Cyborg Mando", layout="wide")

# Estilos CSS inyectados para forzar texto legible y ajustar márgenes en celulares
st.markdown("""
    <style>
    .reportview-container .main .block-container{ padding-top: 1rem; padding-bottom: 1rem; }
    h1 { font-size: 24px !important; text-align: center; }
    h3 { font-size: 18px !important; }
    .stDataFrame { width: 100% !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🤖 CYBORG ANALYTICS V4")

# Ruta de la base de datos relacional
db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'cyborg_db.sqlite')

def cargar_datos():
    conexion = sqlite3.connect(db_path)
    consulta = """
        SELECT 
            p.liga AS Liga,
            p.equipo_local AS Local,
            p.equipo_visitante AS Visitante,
            c_ml.cuota_local AS Cuota_ML_Local,
            c_ml.cuota_visitante AS Cuota_ML_Visitante,
            c_tot.linea AS Linea_Casa,
            c_tot.cuota_local AS Cuota_Over,
            c_tot.cuota_visitante AS Cuota_Under,
            pred.prob_cyborg_local AS Prob_Cyborg_Local,
            pred.linea_total_proyectada AS Proy_Total_Cyborg,
            pred.prob_cyborg_over AS Prob_Cyborg_Over
        FROM partidos p
        LEFT JOIN cuotas c_ml ON p.id_partido = c_ml.id_partido AND c_ml.mercado = 'Moneyline'
        LEFT JOIN cuotas c_tot ON p.id_partido = c_tot.id_partido AND c_tot.mercado = 'Totals'
        LEFT JOIN predicciones pred ON p.id_partido = pred.id_partido
    """
    df = pd.read_sql_query(consulta, conexion)
    conexion.close()
    return df

try:
    df_completo = cargar_datos()

    # Selector de liga simplificado para fácil toque en pantallas táctiles
    liga_filtro = st.sidebar.selectbox("🎯 Filtrar Liga", ["NBA", "MLB", "FUTBOL"])

    if not df_completo.empty:
        df = df_completo[df_completo['Liga'] == liga_filtro].copy()
        
        # Filtro destructor de clones
        df = df.drop_duplicates(subset=['Local', 'Visitante'])
        df = df.dropna(subset=['Prob_Cyborg_Local', 'Cuota_ML_Local', 'Cuota_Over'])

        if not df.empty:
            # Cálculos de ventajas matemáticas
            df['Prob_Casa_Local'] = 1 / df['Cuota_ML_Local']
            df['Prob_Casa_Over'] = 1 / df['Cuota_Over']
            df['Edge_Ganador'] = (df['Prob_Cyborg_Local'] - df['Prob_Casa_Local']) * 100
            df['Edge_Over'] = (df['Prob_Cyborg_Over'] - df['Prob_Casa_Over']) * 100

            # Creamos una columna compacta de enfrentamiento para ahorrar espacio horizontal en móviles
            df['Partido'] = df['Local'] + " vs " + df['Visitante']

            # Interruptor en la barra lateral para alternar vistas si estás en PC o Celular
            vista_movil = st.sidebar.checkbox("📱 Optimizar para Celular", value=True)

            if vista_movil:
                # --- VISTA ULTRA LIMPIA PARA MÓVILES ---
                # Agrupamos la información crítica en pocas columnas
                columnas_visibles = ['Partido', 'Cuota_ML_Local', 'Edge_Ganador', 'Linea_Casa', 'Proy_Total_Cyborg', 'Edge_Over']
                df_display = df[columnas_visibles].copy()
                
                formatos = {
                    'Cuota_ML_Local': '{:.2f}',
                    'Edge_Ganador': '{:+.1f}%',
                    'Linea_Casa': '{:.1f}',
                    'Proy_Total_Cyborg': '{:.1f}',
                    'Edge_Over': '{:+.1f}%'
                }
                subset_color = ['Edge_Ganador', 'Edge_Over']
            else:
                # --- VISTA COMPLETA PARA ESCRITORIO ---
                columnas_visibles = [
                    'Local', 'Visitante', 'Cuota_ML_Local', 'Prob_Cyborg_Local', 'Edge_Ganador',
                    'Linea_Casa', 'Cuota_Over', 'Proy_Total_Cyborg', 'Prob_Cyborg_Over', 'Edge_Over'
                ]
                df_display = df[columnas_visibles].copy()
                
                formatos = {
                    'Cuota_ML_Local': '{:.2f}',
                    'Prob_Cyborg_Local': '{:.1%}',
                    'Edge_Ganador': '{:+.1f}%',
                    'Linea_Casa': '{:.1f}',
                    'Cuota_Over': '{:.2f}',
                    'Proy_Total_Cyborg': '{:.2f}',
                    'Prob_Cyborg_Over': '{:.1%}',
                    'Edge_Over': '{:+.1f}%'
                }
                subset_color = ['Edge_Ganador', 'Edge_Over']

            # Estilos de color para cazar ventajas al instante
            def color_edge(val):
                try:
                    num = float(val.replace('%', ''))
                    if num > 10.0:
                        return 'background-color: #2ecc71; color: black; font-weight: bold;'
                    elif num > 0.0:
                        return 'background-color: #a2f2b7; color: black;'
                    elif num < -5.0:
                        return 'background-color: #f7a1a1; color: black;'
                except:
                    pass
                return ''

            st.write(f"### 📊 Cuotas y Ventajas ({liga_filtro})")
            
            # Mostramos la tabla adaptativa
            st.dataframe(
                df_display.style.format(formatos).map(color_edge, subset=subset_color),
                use_container_width=True,
                height=400
            )

            # Tarjetas de picks recomendados en formato vertical (perfecto para celular)
            st.markdown("---")
            st.write("### 🔥 Picks Sugeridos")
            
            max_edge_ml = df['Edge_Ganador'].max()
            if max_edge_ml > 0:
                partido_ml = df[df['Edge_Ganador'] == max_edge_ml].iloc[0]
                st.success(f"🎯 **Moneyline:** {partido_ml['Partido']} | Ventaja: {max_edge_ml:+.1f}%")
                
            max_edge_tot = df['Edge_Over'].max()
            if max_edge_tot > 0:
                partido_tot = df[df['Edge_Over'] == max_edge_tot].iloc[0]
                st.info(f"⚽ **Línea de Goles/Puntos:** {partido_tot['Partido']} | Ventaja Over: {max_edge_tot:+.1f}%")

        else:
            st.info(f"📅 No hay partidos activos hoy para {liga_filtro}.")
    else:
        st.warning("⚠️ La base de datos central está vacía.")

except Exception as e:
    st.error(f"❌ Error crítico: {e}")
