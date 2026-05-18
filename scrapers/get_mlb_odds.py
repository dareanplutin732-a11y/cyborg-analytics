import requests
import sqlite3
import os

# Tu API Key gratuita (Pon la tuya aquí)
API_KEY = '2f192d53419398fa21bb906dc2f50d5b' 

# Parámetros para las Grandes Ligas
SPORT = 'baseball_mlb' 
REGIONS = 'us'            
MARKETS = 'h2h,totals'     # Buscamos Ganador (Moneyline) y Carreras Totales (Over/Under)
BOOKMAKERS = 'draftkings' 

def obtener_cuotas_mlb():
    url = f'https://api.the-odds-api.com/v4/sports/{SPORT}/odds/?apiKey={API_KEY}&regions={REGIONS}&markets={MARKETS}&bookmakers={BOOKMAKERS}'
    print("⚾ 📡 Conectando a los servidores para extraer cuotas reales de la MLB...")
    
    respuesta = requests.get(url)
    
    if respuesta.status_code == 200:
        datos = respuesta.json()
        
        db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'cyborg_db.sqlite')
        conexion = sqlite3.connect(db_path)
        cursor = conexion.cursor()
        
        cuotas_ml = 0
        cuotas_ou = 0
        
        for evento in datos:
            id_partido = evento['id']
            equipo_local = evento['home_team']
            equipo_visitante = evento['away_team']
            fecha_hora = evento['commence_time']
            
            # Insertamos el partido indicando claramente que es de Béisbol
            cursor.execute('''
                INSERT OR IGNORE INTO partidos 
                (id_partido, deporte, liga, equipo_local, equipo_visitante, fecha_hora, estado)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (id_partido, 'Beisbol', 'MLB', equipo_local, equipo_visitante, fecha_hora, 'Pendiente'))
            
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
                            # Reemplazamos cuotas antiguas si cambian
                            cursor.execute('''
                                INSERT OR REPLACE INTO cuotas (id_partido, mercado, linea, cuota_local, cuota_visitante)
                                VALUES (?, ?, ?, ?, ?)
                            ''', (id_partido, 'Moneyline', 0, cuota_local, cuota_visitante))
                            cuotas_ml += 1

                    elif mkt['key'] == 'totals':
                        linea_carreras = outcomes[0].get('point', 0)
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
                            ''', (id_partido, 'Totals', linea_carreras, cuota_over, cuota_under))
                            cuotas_ou += 1
                            
        conexion.commit()
        conexion.close()
        print(f"\n✅ Extracción exitosa. Registradas {cuotas_ml} líneas de Ganador y {cuotas_ou} líneas de Over/Under para la MLB.")
    else:
        print(f"❌ Error {respuesta.status_code} en la API al buscar béisbol.")

if __name__ == "__main__":
    obtener_cuotas_mlb()