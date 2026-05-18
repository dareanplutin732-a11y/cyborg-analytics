import requests
import sqlite3
import os

# Tu API Key gratuita de the-odds-api
API_KEY = '2f192d53419398fa21bb906dc2f50d5b' 

SPORT = 'basketball_nba' 
REGIONS = 'us'            
MARKETS = 'h2h,totals'     # <- SOLICITAMOS AMBOS MERCADOS
BOOKMAKERS = 'draftkings' 

def obtener_cuotas_reales():
    url = f'https://api.the-odds-api.com/v4/sports/{SPORT}/odds/?apiKey={API_KEY}&regions={REGIONS}&markets={MARKETS}&bookmakers={BOOKMAKERS}'
    print("实时 📡 Conectando a los servidores para extraer cuotas reales (Moneyline y Over/Under)...")
    
    respuesta = requests.get(url)
    
    if respuesta.status_code == 200:
        datos = respuesta.json()
        
        db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'cyborg_db.sqlite')
        conexion = sqlite3.connect(db_path)
        cursor = conexion.cursor()
        
        # Limpiamos las cuotas anteriores para evitar duplicados obsoletos
        cursor.execute("DELETE FROM cuotas WHERE id_partido IN (SELECT id_partido FROM partidos WHERE liga = 'NBA')")
        
        cuotas_ml = 0
        cuotas_ou = 0
        
        for evento in datos:
            id_partido = evento['id']
            equipo_local = evento['home_team']
            equipo_visitante = evento['away_team']
            fecha_hora = evento['commence_time']
            
            # Aseguramos que el partido base exista en la tabla partidos
            cursor.execute('''
                INSERT OR IGNORE INTO partidos 
                (id_partido, deporte, liga, equipo_local, equipo_visitante, fecha_hora, estado)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (id_partido, 'Baloncesto', 'NBA', equipo_local, equipo_visitante, fecha_hora, 'Pendiente'))
            
            bookmakers = evento.get('bookmakers', [])
            if bookmakers:
                mercados = bookmakers[0].get('markets', [])
                for mkt in mercados:
                    outcomes = mkt.get('outcomes', [])
                    
                    # PROCESAR MERCADO GANADOR (MONEYLINE)
                    if mkt['key'] == 'h2h':
                        cuota_local = 0
                        cuota_visitante = 0
                        for outcome in outcomes:
                            if outcome['name'] == equipo_local:
                                cuota_local = outcome['price']
                            elif outcome['name'] == equipo_visitante:
                                cuota_visitante = outcome['price']
                        
                        if cuota_local > 0 and cuota_visitante > 0:
                            cursor.execute('''
                                INSERT INTO cuotas (id_partido, mercado, linea, cuota_local, cuota_visitante)
                                VALUES (?, ?, ?, ?, ?)
                            ''', (id_partido, 'Moneyline', 0, cuota_local, cuota_visitante))
                            cuotas_ml += 1

                    # PROCESAR MERCADO DE TOTALES (OVER/UNDER)
                    elif mkt['key'] == 'totals':
                        linea_puntos = outcomes[0].get('point', 0)
                        cuota_over = 0
                        cuota_under = 0
                        for outcome in outcomes:
                            if outcome['name'] == 'Over':
                                cuota_over = outcome['price']
                            elif outcome['name'] == 'Under':
                                cuota_under = outcome['price']
                        
                        if cuota_over > 0 and cuota_under > 0:
                            # Guardamos en cuota_local el Over y en cuota_visitante el Under
                            cursor.execute('''
                                INSERT INTO cuotas (id_partido, mercado, linea, cuota_local, cuota_visitante)
                                VALUES (?, ?, ?, ?, ?)
                            ''', (id_partido, 'Totals', linea_puntos, cuota_over, cuota_under))
                            cuotas_ou += 1
                            
        conexion.commit()
        conexion.close()
        print(f"\n✅ Extracción exitosa. Registradas {cuotas_ml} líneas de Moneyline y {cuotas_ou} líneas de Over/Under.")
    else:
        print(f"❌ Error {respuesta.status_code} en la API.")

if __name__ == "__main__":
    obtener_cuotas_reales()