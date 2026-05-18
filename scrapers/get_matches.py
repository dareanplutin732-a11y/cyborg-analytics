import sqlite3
import requests
import os

def obtener_partidos_nba():
    # Este es un endpoint público no documentado. Devuelve datos limpios en formato JSON.
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
    print("📡 Conectando a la red para obtener la cartelera de la NBA...")
    
    respuesta = requests.get(url)
    
    if respuesta.status_code == 200:
        datos = respuesta.json()
        eventos = datos.get('events', [])
        
        # Encontramos la ruta exacta a tu base de datos
        db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'cyborg_db.sqlite')
        conexion = sqlite3.connect(db_path)
        cursor = conexion.cursor()
        
        partidos_nuevos = 0
        
        for evento in eventos:
            id_partido = evento['id']
            fecha_hora = evento['date']
            estado = evento['status']['type']['description']
            
            # Navegamos el JSON para sacar quién es Local y quién es Visitante
            competidores = evento['competitions'][0]['competitors']
            if competidores[0]['homeAway'] == 'home':
                equipo_local = competidores[0]['team']['name']
                equipo_visitante = competidores[1]['team']['name']
            else:
                equipo_local = competidores[1]['team']['name']
                equipo_visitante = competidores[0]['team']['name']
            
            # INSERT OR IGNORE evita que se dupliquen los partidos si corres el bot varias veces
            cursor.execute('''
                INSERT OR IGNORE INTO partidos 
                (id_partido, deporte, liga, equipo_local, equipo_visitante, fecha_hora, estado)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (id_partido, 'Baloncesto', 'NBA', equipo_local, equipo_visitante, fecha_hora, estado))
            
            # Si se guardó una fila nueva, sumamos al contador
            if cursor.rowcount > 0:
                partidos_nuevos += 1
                print(f"➕ Agregado: {equipo_visitante} @ {equipo_local}")
        
        conexion.commit()
        conexion.close()
        print(f"\n✅ Proceso completado. Se guardaron {partidos_nuevos} partidos nuevos en la base de datos.")
    else:
        print("❌ Error de conexión. El servidor no respondió.")

if __name__ == "__main__":
    obtener_partidos_nba()