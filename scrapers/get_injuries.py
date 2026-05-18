import sqlite3
import os

# Diccionario de Impacto Ofensivo (Cuántos puntos pierde el equipo si este jugador no juega)
# En un sistema nivel Dios, esto se actualiza raspando el "Usage Rate" del jugador.
IMPACTO_JUGADORES = {
    'Jalen Brunson': 8.5,     # Si Brunson no juega, los Knicks anotan ~8.5 puntos menos
    'Donovan Mitchell': 7.0,  # Cleveland pierde ~7 puntos de ofensiva
    'Shai Gilgeous-Alexander': 8.0,
    'Victor Wembanyama': 6.5, # Impacto masivo también en defensa, pero lo pondremos en ataque por ahora
    'DEFAULT': 2.0            # Jugador de rol promedio
}

def escanear_lesiones_nlp():
    print("🏥 Iniciando Escáner NLP de Reportes de Lesiones (Injury Report)...")
    
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'cyborg_db.sqlite')
    conexion = sqlite3.connect(db_path)
    cursor = conexion.cursor()
    
    # Creamos la tabla del Hospital
    cursor.execute("DROP TABLE IF EXISTS lesiones")
    cursor.execute('''
        CREATE TABLE lesiones (
            equipo TEXT,
            jugador TEXT,
            estado TEXT,
            impacto_lambda REAL
        )
    ''')

    # --- SIMULACIÓN DEL MOTOR NLP (Web Scraping) ---
    # Aquí el bot leería el HTML de CBS Sports o ESPN buscando etiquetas de lesionados.
    # Para nuestra demostración en vivo, simularemos que el bot acaba de leer un Tweet o reporte 
    # de última hora indicando que Jalen Brunson está "Out" (Fuera) por lesión de rodilla.
    
    noticias_ultima_hora = [
        {'equipo': 'New York Knicks', 'jugador': 'Jalen Brunson', 'texto_noticia': 'Jalen Brunson is OUT for tonight game with a knee contusion.'},
    ]
    
    lesiones_detectadas = 0

    for noticia in noticias_ultima_hora:
        # Motor NLP Básico: Buscamos palabras clave de gravedad
        texto = noticia['texto_noticia'].upper()
        
        if "OUT" in texto or "IR" in texto:
            estado = "OUT"
            impacto = IMPACTO_JUGADORES.get(noticia['jugador'], IMPACTO_JUGADORES['DEFAULT'])
            
            cursor.execute('''
                INSERT INTO lesiones (equipo, jugador, estado, impacto_lambda)
                VALUES (?, ?, ?, ?)
            ''', (noticia['equipo'], noticia['jugador'], estado, impacto))
            lesiones_detectadas += 1
            
            print(f"🚨 ¡ALERTA NLP! Se detectó baja crítica: {noticia['jugador']} ({noticia['equipo']}) está {estado}. Impacto en el modelo: -{impacto} puntos.")

    conexion.commit()
    conexion.close()
    print(f"\n✅ Escáner médico completado. {lesiones_detectadas} bajas importantes registradas en la base de datos.")

if __name__ == "__main__":
    escanear_lesiones_nlp()