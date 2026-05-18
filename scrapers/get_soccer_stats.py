import requests
import sqlite3
import os

def actualizar_estadisticas_futbol():
    LIGAS = {
        'ENG.1': 'Premier League',
        'ESP.1': 'LaLiga',
        'UEFA.CHAMPIONS': 'Champions League'
    }
    
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'cyborg_db.sqlite')
    conexion = sqlite3.connect(db_path)
    cursor = conexion.cursor()
    
    print("⚽ Extrayendo estadísticas de las Grandes Ligas de Fútbol Europeo...")
    equipos_procesados = 0
    
    for liga_id, liga_nombre in LIGAS.items():
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{liga_id}/teams?limit=100"
        try:
            respuesta = requests.get(url)
            if respuesta.status_code == 200:
                datos = respuesta.json()
                equipos = datos.get('sports', [{}])[0].get('leagues', [{}])[0].get('teams', [])
                
                for eq in equipos:
                    info_equipo = eq.get('team', {})
                    nombre = info_equipo.get('displayName')
                    id_equipo = info_equipo.get('id')
                    
                    goles_a_favor = 1.3
                    goles_en_contra = 1.3
                    
                    stats_url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{liga_id}/teams/{id_equipo}"
                    res_stats = requests.get(stats_url).json()
                    record = res_stats.get('team', {}).get('record', {}).get('items', [])
                    
                    if record:
                        stats = record[0].get('stats', [])
                        partidos_jugados = 1.0
                        for s in stats:
                            if s['name'] == 'gamesPlayed':
                                partidos_jugados = float(s['value']) if float(s['value']) > 0 else 1.0
                        for s in stats:
                            if s['name'] == 'pointsFor':
                                goles_a_favor = float(s['value']) / partidos_jugados
                            if s['name'] == 'pointsAgainst':
                                goles_en_contra = float(s['value']) / partidos_jugados
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO estadisticas_equipos (nombre_equipo, puntos_anotados, puntos_recibidos)
                        VALUES (?, ?, ?)
                    ''', (nombre, goles_a_favor, goles_en_contra))
                    equipos_procesados += 1
            else:
                print(f"❌ No se pudo conectar a la liga {liga_nombre}")
        except Exception as e:
            print(f"⚠️ Error procesando liga {liga_nombre}: {e}")
            
    conexion.commit()
    conexion.close()
    print(f"\n✅ Base de datos expandida con éxito. {equipos_procesados} clubes de fútbol europeo listos.")

if __name__ == "__main__":
    actualizar_estadisticas_futbol()
