import requests
import sqlite3
import os

API_KEY = '2f192d53419398fa21bb906dc2f50d5b' 
SPORT = 'soccer_epl' 
REGIONS = 'us'
MARKETS = 'h2h,totals'
BOOKMAKERS = 'draftkings'

def obtener_cuotas_futbol():
    url = f'https://api.the-odds-api.com/v4/sports/{SPORT}/odds/?apiKey={API_KEY}&regions={REGIONS}&markets={MARKETS}&bookmakers={BOOKMAKERS}'
    print("⚽ 📡 Descargando cuotas del mercado europeo 1X2 y Totales...")
    
    respuesta = requests.get(url)
    if respuesta.status_code == 200:
        datos = respuesta.json()
        db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'cyborg_db.sqlite')
        conexion = sqlite3.connect(db_path)
        cursor = conexion.cursor()
        partidos_registrados = 0
        
        for evento in datos:
            id_partido = evento['id']
            equipo_local = evento['home_team']
            equipo_visitante = evento['away_team']
            fecha_hora = evento['commence_time']
            
            cursor.execute('''
                INSERT OR IGNORE INTO partidos (id_partido, deporte, liga, equipo_local, equipo_visitante, fecha_hora, estado)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (id_partido, 'Futbol', 'FUTBOL', equipo_local, equipo_visitante, fecha_hora, 'Pendiente'))
            
            bookmakers = evento.get('bookmakers', [])
            if bookmakers:
                mercados = bookmakers[0].get('markets', [])
                for mkt in mercados:
                    outcomes = mkt.get('outcomes', [])
                    if mkt['key'] == 'h2h':
                        cuota_local = cuota_visitante = 0
                        for outcome in outcomes:
                            if outcome['name'] == equipo_local:
                                cuota_local = outcome['price']
                            elif outcome['name'] == equipo_visitante:
                                cuota_visitante = outcome['price']
                        if cuota_local > 0 and cuota_visitante > 0:
                            cursor.execute('''
                                INSERT OR REPLACE INTO cuotas (id_partido, mercado, linea, cuota_local, cuota_visitante)
                                VALUES (?, ?, ?, ?, ?)
                            ''', (id_partido, 'Moneyline', 0, cuota_local, cuota_visitante))
                            partidos_registrados += 1
                    elif mkt['key'] == 'totals':
                        linea_goles = outcomes[0].get('point', 2.5)
                        cuota_over = cuota_under = 0
                        for outcome in outcomes:
                            if outcome['name'] == 'Over':
                                cuota_over = outcome['price']
                            elif outcome['name'] == 'Under':
                                cuota_under = outcome['price']
                        if cuota_over > 0 and cuota_under > 0:
                            cursor.execute('''
                                INSERT OR REPLACE INTO cuotas (id_partido, mercado, linea, cuota_local, cuota_visitante)
                                VALUES (?, ?, ?, ?, ?)
                            ''', (id_partido, 'Totals', linea_goles, cuota_over, cuota_under))
                            
        conexion.commit()
        conexion.close()
        print(f"✅ Extracción de fútbol completada. {partidos_registrados} partidos listos.")
    else:
        print(f"❌ Error {respuesta.status_code} al consultar las cuotas.")

if __name__ == "__main__":
    obtener_cuotas_futbol()
