import requests
import sqlite3
import os

def actualizar_lanzadores():
    print("⚾ Escaneando Lanzadores Abridores Confirmados y su Efectividad (ERA)...")
    url = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"
    
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'cyborg_db.sqlite')
    conexion = sqlite3.connect(db_path)
    cursor = conexion.cursor()
    
    # Creamos la tabla rotativa de lanzadores
    cursor.execute("DROP TABLE IF EXISTS lanzadores")
    cursor.execute('''
        CREATE TABLE lanzadores (
            equipo TEXT PRIMARY KEY,
            nombre_pitcher TEXT,
            era REAL
        )
    ''')
    
    try:
        respuesta = requests.get(url)
        datos = respuesta.json()
        eventos = datos.get('events', [])
        
        lanzadores_encontrados = 0
        
        for evento in eventos:
            competidores = evento.get('competitions', [{}])[0].get('competitors', [])
            for comp in competidores:
                equipo = comp.get('team', {}).get('displayName')
                probables = comp.get('probables', [])
                
                # Si hay un lanzador abridor confirmado para hoy
                if probables:
                    atleta = probables[0].get('athlete', {})
                    nombre = atleta.get('displayName', 'Desconocido')
                    
                    # Promedio de la liga por defecto si el lanzador es novato o no tiene datos
                    era = 4.50 
                    stats = probables[0].get('statistics', [])
                    for s in stats:
                        if s.get('name') == 'ERA':
                            try:
                                era = float(s.get('displayValue'))
                            except ValueError:
                                pass # Mantiene el 4.50 si hay un error de formato
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO lanzadores (equipo, nombre_pitcher, era)
                        VALUES (?, ?, ?)
                    ''', (equipo, nombre, era))
                    lanzadores_encontrados += 1
                    print(f"🎯 {equipo}: Lanza {nombre} (ERA: {era})")
                    
        conexion.commit()
        print(f"\n✅ Se registraron las estadísticas de {lanzadores_encontrados} abridores para hoy.")
    except Exception as e:
        print(f"❌ Error al extraer lanzadores: {e}")
    finally:
        conexion.close()

if __name__ == "__main__":
    actualizar_lanzadores()