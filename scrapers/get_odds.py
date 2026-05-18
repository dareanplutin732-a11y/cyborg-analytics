import sqlite3
import random
import os

def actualizar_cuotas():
    # Conectamos a la base de datos
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'cyborg_db.sqlite')
    conexion = sqlite3.connect(db_path)
    cursor = conexion.cursor()

    # Buscamos qué partidos tenemos guardados
    cursor.execute("SELECT id_partido, equipo_local, equipo_visitante FROM partidos")
    partidos = cursor.fetchall()

    cuotas_agregadas = 0

    for partido in partidos:
        id_partido, local, visitante = partido
        
        # Generamos cuotas realistas de Moneyline (formato decimal europeo)
        # Ejemplo: 1.90 a 1.90 (partido igualado) o 1.30 a 3.50 (favorito claro)
        probabilidad_local = random.uniform(0.3, 0.8)
        cuota_local = round(1 / probabilidad_local, 2)
        cuota_visit = round(1 / (1 - probabilidad_local + 0.05), 2) # +0.05 simula la comisión de la casa (Vig/Juice)

        # Insertamos la cuota en la tabla
        cursor.execute('''
            INSERT INTO cuotas (id_partido, mercado, linea, cuota_local, cuota_visitante)
            VALUES (?, ?, ?, ?, ?)
        ''', (id_partido, 'Moneyline', 0, cuota_local, cuota_visit))
        
        cuotas_agregadas += 1
        print(f"💰 Cuotas añadidas para {local} ({cuota_local}) vs {visitante} ({cuota_visit})")

    conexion.commit()
    conexion.close()
    print(f"\n✅ Se actualizaron las cuotas de {cuotas_agregadas} partidos.")

if __name__ == "__main__":
    actualizar_cuotas()