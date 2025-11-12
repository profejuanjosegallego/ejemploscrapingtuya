#IMPORTACIONES
import sqlite3
from pydantic import BaseModel
from typing import List


#conexion hacia una bd
NOMBRE_BASEDATOS="ranking.db"
FUENTE_DATOS="fifa_ranking.json"

#modelo de datos (tabla)
#USAR CLASES que configuren la tabla
class Ranking(BaseModel):
    rango:int
    pais:str
    puntos:str

class CuerpoRanking(BaseModel):
    items:List[Ranking]


#operaciones o servicios que voy a entregarle al front
 
#abrir conexion a bd

def crear_conexion():
    return sqlite3.connect(NOMBRE_BASEDATOS)

#crear la tabla que almcena el ranking si no existe
def crear_tabla():
    conexion=crear_conexion() 
    cursor=conexion.cursor() #ubicate en la bd despues de conectarte
    cursor.execute("""

            CREATE TABLE IF NOT EXISTS ranking_fifa(
                   rango INTEGER PRIMARY KEY,
                   pais TEXT NOT NULL,
                   puntos TEXT NOT NULL
            )

    """)
    conexion.commit() #Ejecuta la consulta en la bd
    conexion.close()

#modificar el ranking
def modificar_ranking(lista:List[Ranking]):
    conexion=crear_conexion() 
    cursor=conexion.cursor() #ubicate en la bd despues de conectarte
    cursor.execute("DELETE FROM ranking_fifa")
    cursor.executemany(
        "INSERT INTO ranking_fifa(rango, pais, puntos) VALUES (?,?,?)",
        [(elementoDeLaLista.rango, elementoDeLaLista.pais, elementoDeLaLista.puntos)for elementoDeLaLista in lista]
    )
    conexion.commit() #Ejecuta la consulta en la bd
    conexion.close()    

#leer el ranking
def leer_ranking():
    conexion=crear_conexion() 
    cursor=conexion.cursor() #ubicate en la bd despues de conectarte
    cursor.execute("SELECT rango, pais, puntos FROM ranking_fifa ORDER BY rango ASC")
    filas=cursor.fetchall()
    conexion.close()
    return [ {"rango":rango,"pais":pais,"puntos":puntos} for (rango, pais, puntos) in filas]



#construir los endpoints