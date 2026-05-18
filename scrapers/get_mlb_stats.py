import requests
import sqlite3
import os

def actualizar_estadisticas_mlb():
    url = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/teams?limit=30"
    print("⚾ Extrayendo estadísticas sabermétricas (Carreras) de la MLB...")
    
    respuesta = requests.get(url)
    if respuesta.status_code == 200:
        datos = respuesta.json()
        equipos = datos.get('sports', [{}])[0].get('leagues', [{}])[0].get('teams', [])
        
        db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'cyborg_db.sqlite')
        conexion = sqlite3.connect(db_path)
        cursor = conexion.cursor()
        
        equipos_procesados = 0
        
        for eq in equipos:
            info_equipo = eq.get('team', {})
            nombre = info_equipo.get('displayName')
            id_equipo = info_equipo.get('id')
            
            # Promedio base de la MLB (4.5 carreras) por si hay un error en la API
            carreras_a_favor = 4.5
            carreras_en_contra = 4.5
            
            # Extraemos las carreras reales de la temporada actual
            try:
                stats_url = f"https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/teams/{id_equipo}"
                res_stats = requests.get(stats_url).json()
                record = res_stats.get('team', {}).get('record', {}).get('items', [])
                
                if record:
                    stats = record[0].get('stats', [])
                    juegos_jugados = 1.0
                    
                    # Primero buscamos cuántos juegos han jugado para sacar el promedio exacto
                    for s in stats:
                        if s['name'] == 'gamesPlayed':
                            juegos_jugados = float(s['value'])
                    
                    # Luego buscamos las carreras totales y las dividimos por los juegos
                    for s in stats:
                        if s['name'] == 'runs':
                            carreras_a_favor = float(s['value']) / juegos_jugados
                        if s['name'] == 'runsAllowed':
                            carreras_en_contra = float(s['value']) / juegos_jugados
            except Exception:
                pass
            
            # Reutilizamos la misma tabla que usamos para la NBA, el sistema es agnóstico
            cursor.execute('''
                INSERT OR REPLACE INTO estadisticas_equipos (nombre_equipo, puntos_anotados, puntos_recibidos)
                VALUES (?, ?, ?)
            ''', (nombre, carreras_a_favor, carreras_en_contra))
            
            equipos_procesados += 1
            print(f"📊 {nombre} -> Ofensiva (RF): {carreras_a_favor:.2f} | Defensiva (RA): {carreras_en_contra:.2f}")
            
        conexion.commit()
        conexion.close()
        print(f"\n✅ Base de datos actualizada con las estadísticas de {equipos_procesados} equipos de MLB.")
    else:
        print("❌ Error de conexión al buscar las estadísticas de la MLB.")

if __name__ == "__main__":
    actualizar_estadisticas_mlb()