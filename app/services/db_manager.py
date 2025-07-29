import psycopg2
from datetime import date, datetime
from typing import Dict, Any, Optional
import json
import base64

from app.config.settings import *

class DBManager:
    def get_db_connection(self):
        """Establece una conexión con la base de datos PostgreSQL."""
        try:
            conn = psycopg2.connect(
                dbname=POSTGRES_DB,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                host="postgres",
                port="5432"
            )
            return conn
        except psycopg2.OperationalError as e:
            print(f"FATAL: Error al conectar con PostgreSQL: {e}")
            return None

    def save_document(self, nombre_archivo: str, fecha_documento: date, fuente: str, hash_documento: str) -> Optional[int]:
        """Guarda un nuevo documento y devuelve su ID. Si ya existe por hash, devuelve None."""
        sql = """
            INSERT INTO documentos (nombre_archivo, fecha_documento, fuente, hash_documento)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (hash_documento) DO NOTHING
            RETURNING id;
        """
        conn = self.get_db_connection()
        if not conn: return None
        
        document_id = None
        try:
            with conn.cursor() as cur:
                cur.execute(sql, (nombre_archivo, fecha_documento, fuente, hash_documento))
                result = cur.fetchone()
                if result:
                    document_id = result[0]
                conn.commit()
        except psycopg2.Error as e:
            print(f"Error al guardar el documento: {e}")
            conn.rollback()
        finally:
            conn.close()
        
        return document_id

    def save_results_to_db(self, document_id: int, source: str, document_date: date, results: Dict[str, Any]):
        """Orquesta el guardado de todos los resultados extraídos en las tablas correspondientes."""
        if not document_id:
            print("No se proporcionó un ID de documento válido para guardar resultados.")
            return

        task_savers = {
            "get_mysteel_inventory": self.save_inventories,
            "get_mysteel_news": self.save_news,
            "get_platts_prices": self.save_prices,
            "get_fastmarkets_prices": self.save_prices,
            "get_baltic_prices": self.save_prices,
            "get_mysteel_graphs": self.save_graphs,
        }

        for task_name, data in results.items():
            if task_name in task_savers and data and not data.get("error"):
                task_savers[task_name](document_id, source, document_date, data)

    def save_inventories(self, document_id: int, source: str, document_date: date, data: Dict[str, Any]):
        sql = """
            INSERT INTO inventarios (documento_id, fuente, tipo_inventario, valor, fecha_dato)
            VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING;
        """
        
        conn = self.get_db_connection()
        if not conn: return
        
        items_guardados = 0
        try:
            with conn.cursor() as cur:
                for tipo_inventario, values in data.items():
                    if values and isinstance(values, dict) and 'valor' in values:
                        cur.execute(sql, (
                            document_id,
                            source,
                            tipo_inventario,
                            values.get('valor'),
                            values.get('fecha') or document_date
                        ))
                        items_guardados += 1
                conn.commit()
                if items_guardados > 0:
                    print(f"  -> Guardados {items_guardados} registros de inventario.")
        except psycopg2.Error as e:
            print(f"Error al guardar inventarios: {e}")
            conn.rollback()
        finally:
            conn.close()

    def save_news(self, document_id: int, source: str, document_date: date, data: Dict[str, Any]):
        sql = """
            INSERT INTO noticias (documento_id, fuente, titulo, resumen, sentimiento, fecha_noticia, categoria, tags)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING;
        """
        items = data.get("noticias", [])
        if not items: return

        conn = self.get_db_connection()
        if not conn: return
            
        try:
            with conn.cursor() as cur:
                for noticia in items:
                    cur.execute(sql, (
                        document_id, source, noticia.get("titulo"), noticia.get("resumen"),
                        noticia.get("sentimiento"), noticia.get("fecha_noticia") or document_date,
                        noticia.get("categoria"), noticia.get("tags")
                    ))
                conn.commit()
                print(f"  -> Guardadas {len(items)} noticias.")
        except psycopg2.Error as e:
            print(f"Error al guardar noticias: {e}")
            conn.rollback()
        finally:
            conn.close()

    def save_prices(self, document_id: int, source: str, document_date: date, data: Dict[str, Any]):
        sql = """
            INSERT INTO precios (documento_id, fuente, tipo_precio, valor, fecha_precio, moneda, unidad)
            VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING;
        """
        
        conn = self.get_db_connection()
        if not conn: return
            
        items_guardados = 0
        try:
            with conn.cursor() as cur:
                for tipo_precio, values in data.items():
                    if values and isinstance(values, dict) and 'valor' in values:
                        cur.execute(sql, (
                            document_id,
                            source,
                            tipo_precio,
                            values.get('valor'),
                            values.get('fecha') or document_date,
                            values.get('moneda', 'USD'),
                            values.get('unidad', 'ton')
                        ))
                        items_guardados += 1
                conn.commit()
                if items_guardados > 0:
                    print(f"  -> Guardados {items_guardados} registros de precios.")
        except psycopg2.Error as e:
            print(f"Error al guardar precios: {e}")
            conn.rollback()
        finally:
            conn.close()

    def save_graphs(self, document_id: int, source: str, document_date: date, data: Dict[str, Any]):
        sql = """
            INSERT INTO graficos (documento_id, fuente, titulo, pagina, contenido, descripcion_ia, fecha_grafico)
            VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING;
        """
        items = data.get("graficos", [])
        if not items: return

        conn = self.get_db_connection()
        if not conn: return
            
        try:
            with conn.cursor() as cur:
                for grafico in items:
                    contenido_bytes = grafico.get("contenido")
                    if isinstance(contenido_bytes, str):
                        contenido_bytes = base64.b64decode(contenido_bytes)

                    cur.execute(sql, (
                        document_id,
                        source,
                        grafico.get("titulo"),
                        grafico.get("pagina"),
                        contenido_bytes,
                        grafico.get("descripcion_ia"),
                        grafico.get("fecha_grafico") or document_date
                    ))
                conn.commit()
                print(f"  -> Guardados {len(items)} gráficos.")
        except psycopg2.Error as e:
            print(f"Error al guardar gráficos: {e}")
            conn.rollback()
        finally:
            conn.close()

    def log_procesamiento_evento(self, documento_id: int, etapa: str, estado: str, duracion_ms: Optional[int] = None, detalles: Optional[Dict] = None, error_mensaje: Optional[str] = None):
        """Registra un evento en la tabla 'logs_procesamiento'."""
        sql = """
            INSERT INTO logs_procesamiento (documento_id, etapa, estado, duracion_ms, detalles, error_mensaje)
            VALUES (%s, %s, %s, %s, %s, %s);
        """
        conn = self.get_db_connection()
        if not conn: return

        try:
            with conn.cursor() as cur:
                detalles_json = json.dumps(detalles) if detalles else None
                cur.execute(sql, (documento_id, etapa, estado, duracion_ms, detalles_json, error_mensaje))
                conn.commit()
        except psycopg2.Error as e:
            print(f"Error al registrar log de procesamiento: {e}")
            conn.rollback()
        finally:
            conn.close()

    def log_tarea(self, documento_id: int, nombre_tarea: str, estado: str, inicio: datetime, fin: datetime, resultados_encontrados: Optional[int] = None, error_mensaje: Optional[str] = None):
        """Registra el resultado de una tarea específica en 'logs_tareas'."""
        sql = """
            INSERT INTO logs_tareas (documento_id, nombre_tarea, timestamp_inicio, timestamp_fin, estado, resultados_encontrados, error_mensaje)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """
        conn = self.get_db_connection()
        if not conn: return

        try:
            with conn.cursor() as cur:
                cur.execute(sql, (documento_id, nombre_tarea, inicio, fin, estado, resultados_encontrados, error_mensaje))
                conn.commit()
        except psycopg2.Error as e:
            print(f"Error al registrar log de tarea: {e}")
            conn.rollback()
        finally:
            conn.close()

db_manager = DBManager() 