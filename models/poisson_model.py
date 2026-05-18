import sqlite3
import os
from scipy.stats import poisson

def calcular_probabilidad_ganador(lambda_local, lambda_visitante, max_puntos):
    prob_local_gana = 0.0
    for puntos_local in range(max_puntos):
        for puntos_visitante in range(max_puntos):
            prob_marcador = poisson.pmf(puntos_local, lambda_local) * poisson.pmf(puntos_visitante, lambda_visitante)
            if puntos_local > puntos_visitante:
                prob_local_gana += prob_marcador
    return prob_local_gana

def ejecutar_modelo_completo():
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'cyborg_db.sqlite')
    conexion = sqlite3.connect(db_path)
    cursor = conexion.cursor()

    cursor.execute("DROP TABLE IF EXISTS predicciones")
    cursor.execute('''
        CREATE TABLE predicciones (
            id_partido TEXT PRIMARY KEY,
            prob_cyborg_local REAL,
            linea_total_proyectada REAL,
            prob_cyborg_over REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute("""
        SELECT AVG(e.puntos_anotados) FROM estadisticas_equipos e
        JOIN partidos p ON e.nombre_equipo = p.equipo_local
        WHERE p.liga = 'NBA'
    """)
    promedio_nba = cursor.fetchone()[0] or 114.0

    cursor.execute("""
        SELECT AVG(e.puntos_anotados) FROM estadisticas_equipos e
        JOIN partidos p ON e.nombre_equipo = p.equipo_local
        WHERE p.liga = 'MLB'
    """)
    promedio_mlb = cursor.fetchone()[0] or 4.5

    cursor.execute("SELECT id_partido, equipo_local, equipo_visitante, liga FROM partidos")
    partidos = cursor.fetchall()

    print(f"🧠 Ejecutando simulaciones Poisson (NBA y MLB Avanzada)...")

    for partido in partidos:
        id_partido, local, visitante, liga = partido
        
        cursor.execute("SELECT puntos_anotados, puntos_recibidos FROM estadisticas_equipos WHERE nombre_equipo = ?", (local,))
        res_local = cursor.fetchone()
        
        cursor.execute("SELECT puntos_anotados, puntos_recibidos FROM estadisticas_equipos WHERE nombre_equipo = ?", (visitante,))
        res_visitante = cursor.fetchone()
        
        if res_local and res_visitante:
            off_local, def_local = res_local
            off_visitante, def_visitante = res_visitante
            
            # ==========================================
            # 🏀 LÓGICA NBA
            # ==========================================
            if liga == 'NBA':
                promedio_liga = promedio_nba
                max_puntos = 150
                ventaja_localia = 3.0
                
                try:
                    cursor.execute("SELECT SUM(impacto_lambda) FROM lesiones WHERE equipo = ? AND estado = 'OUT'", (local,))
                    bajas_local = cursor.fetchone()[0] or 0.0
                    cursor.execute("SELECT SUM(impacto_lambda) FROM lesiones WHERE equipo = ? AND estado = 'OUT'", (visitante,))
                    bajas_visitante = cursor.fetchone()[0] or 0.0
                except sqlite3.OperationalError:
                    bajas_local = bajas_visitante = 0.0
                    
                lambda_local = ((off_local * def_visitante) / promedio_liga) + ventaja_localia - bajas_local
                lambda_visitante = (off_visitante * def_local) / promedio_liga - bajas_visitante
                
                lambda_local = max(lambda_local, 60.0)
                lambda_visitante = max(lambda_visitante, 60.0)

            # ==========================================
            # ⚾ LÓGICA MLB AVANZADA (FACTOR PITCHER)
            # ==========================================
            elif liga == 'MLB':
                promedio_liga = promedio_mlb
                max_puntos = 25
                ventaja_localia = 0.25 
                
                # Buscamos el ERA del lanzador local
                try:
                    cursor.execute("SELECT era FROM lanzadores WHERE equipo = ?", (local,))
                    res_pitcher_local = cursor.fetchone()
                    era_local = res_pitcher_local[0] if res_pitcher_local else def_local
                except sqlite3.OperationalError:
                    era_local = def_local

                # Buscamos el ERA del lanzador visitante
                try:
                    cursor.execute("SELECT era FROM lanzadores WHERE equipo = ?", (visitante,))
                    res_pitcher_visitante = cursor.fetchone()
                    era_visitante = res_pitcher_visitante[0] if res_pitcher_visitante else def_visitante
                except sqlite3.OperationalError:
                    era_visitante = def_visitante

                # FÓRMULA DE DEFENSA AJUSTADA: (Defensa del Equipo + ERA del Pitcher) / 2
                def_local_ajustada = (def_local + era_local) / 2
                def_visitante_ajustada = (def_visitante + era_visitante) / 2

                lambda_local = ((off_local * def_visitante_ajustada) / promedio_liga) + ventaja_localia
                lambda_visitante = (off_visitante * def_local_ajustada) / promedio_liga
                
                lambda_local = max(lambda_local, 1.0)
                lambda_visitante = max(lambda_visitante, 1.0)
            
            else:
                continue

            # --- EJECUCIÓN MATEMÁTICA COMÚN ---
            prob_victoria_local = calcular_probabilidad_ganador(lambda_local, lambda_visitante, max_puntos)
            lambda_total = lambda_local + lambda_visitante
            
            cursor.execute("SELECT linea FROM cuotas WHERE id_partido = ? AND mercado = 'Totals'", (id_partido,))
            res_linea = cursor.fetchone()
            linea_casa = res_linea[0] if res_linea else lambda_total
            
            prob_under = poisson.cdf(linea_casa, lambda_total)
            prob_over = 1 - prob_under
            
            cursor.execute('''
                INSERT INTO predicciones (id_partido, prob_cyborg_local, linea_total_proyectada, prob_cyborg_over)
                VALUES (?, ?, ?, ?)
            ''', (id_partido, prob_victoria_local, lambda_total, prob_over))
            
            print(f"📈 [{liga}] {local} vs {visitante} | Proy. Total: {lambda_total:.1f} | Prob Over {linea_casa}: {prob_over*100:.1f}%")
        else:
            print(f"⚠️ Datos insuficientes en DB para {local} vs {visitante} ({liga}).")

    conexion.commit()
    conexion.close()
    print("\n🚀 Predicciones Multideporte guardadas con éxito.")

if __name__ == "__main__":
    ejecutar_modelo_completo()