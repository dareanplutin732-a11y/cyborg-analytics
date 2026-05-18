import streamlit as st
import sqlite3
import pandas as pd
import os

# Configuración inicial de la página
st.set_page_config(page_title="Cyborg Analytics - Centro de Mando", layout="wide")

st.title("🤖 CYBORG ANALYTICS - MULTIDEPORTE V4")
st.subheader("Sistema de Simulación Cuantitativa basado en Distribución de Poisson")

# Ruta de la base de datos relacional
db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'cyborg_db.sqlite')

# Conexión y extracción de datos con un JOIN limpio
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

    # Menú lateral expansivo para seleccionar el deporte
    liga_filtro = st.sidebar.selectbox("🎯 Selecciona la Liga a Monitorear", ["NBA", "MLB", "FUTBOL"])

    if not df_completo.empty:
        # 1. Filtramos solo los partidos del deporte que seleccionaste
        df = df_completo[df_completo['Liga'] == liga_filtro].copy()
        
        # --- FILTRO ANTI-CLONES ---
        df = df.drop_duplicates(subset=['Local', 'Visitante'])
        
        # 2. Escondemos los partidos que aún no han sido procesados por el motor matemático
        df = df.dropna(subset=['Prob_Cyborg_Local', 'Cuota_ML_Local', 'Cuota_Over'])

        if not df.empty:
            # --- CÁLCULOS ESTADÍSTICOS DE VALOR (EDGES) ---
            # Implicación matemática de las cuotas de la casa (1 / Cuota)
            df['Prob_Casa_Local'] = 1 / df['Cuota_ML_Local']
            df['Prob_Casa_Over'] = 1 / df['Cuota_Over']

            # Cálculo minucioso del Edge (Nuestra Probabilidad - Probabilidad de la Casa)
            df['Edge_Ganador_Local'] = (df['Prob_Cyborg_Local'] - df['Prob_Casa_Local']) * 100
            df['Edge_Over'] = (df['Prob_Cyborg_Over'] - df['Prob_Casa_Over']) * 100

            # --- DISEÑO Y PRESENTACIÓN DE LA TABLA COMPLETA ---
            columnas_visibles = [
                'Local', 'Visitante', 
                'Cuota_ML_Local', 'Prob_Cyborg_Local', 'Edge_Ganador_Local',
                'Linea_Casa', 'Cuota_Over', 'Proy_Total_Cyborg', 'Prob_Cyborg_Over', 'Edge_Over'
            ]
            
            df_display = df[columnas_visibles].copy()

            # Formateo visual estricto para que los porcentajes y cuotas se lean perfectos
            formatos = {
                'Cuota_ML_Local': '{:.2f}',
                'Prob_Cyborg_Local': '{:.1%}',
                'Edge_Ganador_Local': '{:+.1f}%',
                'Linea_Casa': '{:.1f}',
                'Cuota_Over': '{:.2f}',
                'Proy_Total_Cyborg': '{:.2f}',
                'Prob_Cyborg_Over': '{:.1%}',
                'Edge_Over': '{:+.1f}%'
            }

            # Aplicamos estilos de colores llamativos para cazar los Edges positivos de un vistazo
            def color_edge(val):
                try:
                    num = float(val.replace('%', ''))
                    if num > 10.0: # Resaltado verde fuerte para ventajas brutales mayores al 10%
                        return 'background-color: #2ecc71; color: black; font-weight: bold;'
                    elif num > 0.0: # Verde claro para ventajas estándar
                        return 'background-color: #a2f2b7; color: black;'
                    elif num < -5.0: # Rojo suave si la casa tiene la ventaja completa
                        return 'background-color: #f7a1a1; color: black;'
                except:
                    pass
                return ''

            st.write(f"### 📊 Panel de Cuotas y Ventajas Matemáticas Encontradas para: **{liga_filtro}**")
            
            # Renderizamos la tabla estilizada en la interfaz web
            st.dataframe(
                df_display.style.format(formatos).map(color_edge, subset=['Edge_Ganador_Local', 'Edge_Over']),
                use_container_width=True,
                height=500
            )

            # Métricas rápidas de control de mando en la parte inferior
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                max_edge_ml = df['Edge_Ganador_Local'].max()
                if max_edge_ml > 0:
                    partido_ml = df[df['Edge_Ganador_Local'] == max_edge_ml].iloc[0]
                    st.metric("🔥 Mayor Ventaja en Ganador Directo", f"{partido_ml['Local']} ({max_edge_ml:+.1f}%)")
            with col2:
                max_edge_tot = df['Edge_Over'].max()
                if max_edge_tot > 0:
                    partido_tot = df[df['Edge_Over'] == max_edge_tot].iloc[0]
                    st.metric("⚽ Mayor Ventaja en Línea de Goles (Over)", f"{partido_tot['Local']} vs {partido_tot['Visitante']} ({max_edge_tot:+.1f}%)")

        else:
            st.info(f"📅 No hay partidos con cuotas activas procesados para {liga_filtro} en las próximas horas.")
    else:
        st.warning("⚠️ La base de datos central está vacía. Verifica que los robots extractores estén corriendo.")

except Exception as e:
    st.error(f"❌ Error crítico en la carga del Dashboard: {e}")
