#IMPORTACIONES
import sqlite3
import os 
import json
from pydantic import BaseModel
from typing import List
from fastapi import FastAPI  # Crea la API web
from fastapi.middleware.cors import CORSMiddleware  # Habilita CORS para frontends
from contextlib import asynccontextmanager


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


def autocargar_json_si_existe():  # Carga JSON a SQLite si el archivo existe
    if not os.path.exists(FUENTE_DATOS):  # Si no existe JSON, no hace nada
        print(f"[INFO] No se encontró {FUENTE_DATOS}; arranco sin datos iniciales.")
        return
    try:  # Lee y valida contra el modelo
        with open(FUENTE_DATOS, "r", encoding="utf-8") as fifaranking:
            data = json.load(fifaranking)  # Espera lista de dicts
        modelos = [Ranking(**item) for item in data]  # Valida con Pydantic
        modificar_ranking(modelos)  # Inserta en BD
        print(f"[OK] Cargados {len(modelos)} registros desde {FUENTE_DATOS} a SQLite.")
    except Exception as error:  # Manejo básico de error
        print(f"[WARN] No se pudo cargar {FUENTE_DATOS}: {error}")



@asynccontextmanager  
async def lifespan(app: FastAPI):  # Se ejecuta al iniciar y al cerrar la app
    crear_tabla()  #
    autocargar_json_si_existe()  # Startup: intenta precargar datos del JSON
    yield  # La app queda corriendo entre este yield y el cierre
      

# Instancia de FastAPI con lifespan moderno
app = FastAPI(title="API Ranking FIFA con SQLite", lifespan=lifespan)

# CORS para demos/Front local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


#construir los endpoints

@app.get("/ranking")  # Devuelve todo el ranking
def get_ranking():
    return {"items": leer_ranking()}

@app.post("/ranking")  # Reemplaza con lo recibido
def post_ranking(cuerpo: CuerpoRanking):
    leer_ranking(cuerpo.items)
    return {"mensaje": "Ranking guardado en SQLite", "cantidad": len(cuerpo.items)}


#Levanto el servidor
if __name__ == "__main__": 
    import uvicorn  # Importa uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)  # Levanta servidor