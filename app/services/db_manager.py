import pyodbc
from datetime import date, datetime
from typing import Dict, Any, Optional
import json
import base64

from app.config.settings import *

class DBManager:
    def __init__(self):
        """Inicializa el DBManager para SQL Server."""
        self.conn_str = (
            f'DRIVER={MSSQL_DRIVER};'
            f'SERVER={MSSQL_HOST};'
            f'DATABASE={MSSQL_DB};'
            f'UID={MSSQL_USER};'
            f'PWD={MSSQL_PASSWORD};'
            f'TrustServerCertificate=yes;'
        )
        self.conn = None

    def initialize_pool(self):
        """Inicializa la conexión a SQL Server."""
        if self.conn:
            return
        try:
            print("💡 Initializing SQL Server database connection...")
            self.conn = pyodbc.connect(self.conn_str, autocommit=False)
        except pyodbc.Error as e:
            print(f"FATAL: Error initializing connection: {e}")
            raise ConnectionError(f"Could not initialize SQL Server connection: {e}")

    def close_pool(self):
        """Cierra la conexión a SQL Server."""
        if self.conn:
            print("... Closing SQL Server database connection.")
            self.conn.close()

    def save_document(self, nombre_archivo: str, fecha_documento: date, fuente: str, hash_documento: str) -> Optional[int]:
        """Guarda un nuevo documento si no existe y devuelve su ID."""
        check_sql = "SELECT id FROM documentos WHERE hash_documento = ?"
        insert_sql = """
            INSERT INTO documentos (nombre_archivo, fecha_documento, fuente, hash_documento)
            OUTPUT INSERTED.id
            VALUES (?, ?, ?, ?);
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute(check_sql, hash_documento)
            existing = cursor.fetchone()
            if existing:
                return existing.id

            row = cursor.execute(insert_sql, nombre_archivo, fecha_documento, fuente, hash_documento).fetchone()
            self.conn.commit()
            return row.id if row else None
        except pyodbc.Error as e:
            print(f"Error al guardar el documento: {e}")
            self.conn.rollback()
            return None
        finally:
            cursor.close()

    def save_results_to_db(self, document_id: int, source: str, document_date: date, results: Dict[str, Any]):
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

    def _insert_many(self, sql: str, data_generator):
        """Helper para insertar múltiples registros. Ignora errores de llaves duplicadas."""
        try:
            with self.conn.cursor() as cursor:
                for params in data_generator:
                    try:
                        cursor.execute(sql, params)
                    except pyodbc.IntegrityError:
                        # Ignorar si el registro ya existe (basado en un UNIQUE constraint)
                        print(f"  -> Registro duplicado ignorado: {params[:3]}...")
                        continue
                self.conn.commit()
        except pyodbc.Error as e:
            print(f"Error en inserción masiva: {e}")
            self.conn.rollback()

    def save_inventories(self, document_id: int, source: str, document_date: date, data: Dict[str, Any]):
        sql = """
            INSERT INTO inventarios (documento_id, fuente, tipo_inventario, valor, fecha_dato)
            VALUES (?, ?, ?, ?, ?);
        """
        def data_gen():
            for tipo_inventario, values in data.items():
                if values and isinstance(values, dict) and 'valor' in values:
                    yield (document_id, source, tipo_inventario, values.get('valor'), values.get('fecha') or document_date)
        
        self._insert_many(sql, data_gen())
        print(f"  -> Procesados registros de inventario.")

    def save_news(self, document_id: int, source: str, document_date: date, data: Dict[str, Any]):
        sql = """
            INSERT INTO noticias (documento_id, fuente, titulo, resumen, sentimiento, fecha_noticia, categoria, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """
        def data_gen():
            for noticia in data.get("noticias", []):
                yield (document_id, source, noticia.get("titulo"), noticia.get("resumen"), noticia.get("sentimiento"), noticia.get("fecha_noticia") or document_date, noticia.get("categoria"), json.dumps(noticia.get("tags")))
        
        self._insert_many(sql, data_gen())
        print(f"  -> Procesadas {len(data.get('noticias', []))} noticias.")

    def save_prices(self, document_id: int, source: str, document_date: date, data: Dict[str, Any]):
        sql = """
            INSERT INTO precios (documento_id, fuente, tipo_precio, valor, fecha_precio, moneda, unidad)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """
        def data_gen():
            for tipo_precio, values in data.items():
                if values and isinstance(values, dict) and 'valor' in values:
                    yield (document_id, source, tipo_precio, values.get('valor'), values.get('fecha') or document_date, values.get('moneda', 'USD'), values.get('unidad', 'ton'))

        self._insert_many(sql, data_gen())
        print(f"  -> Procesados registros de precios.")

    def save_graphs(self, document_id: int, source: str, document_date: date, data: Dict[str, Any]):
        sql = """
            INSERT INTO graficos (documento_id, fuente, titulo, pagina, contenido, descripcion_ia, fecha_grafico)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """
        def data_gen():
            for grafico in data.get("graficos", []):
                contenido_bytes = grafico.get("contenido")
                if isinstance(contenido_bytes, str):
                    contenido_bytes = base64.b64decode(contenido_bytes)
                # Para SQL Server, los datos binarios se deben envolver en pyodbc.Binary
                yield (document_id, source, grafico.get("titulo"), grafico.get("pagina"), pyodbc.Binary(contenido_bytes) if contenido_bytes else None, grafico.get("descripcion_ia"), grafico.get("fecha_grafico") or document_date)

        self._insert_many(sql, data_gen())
        print(f"  -> Procesados {len(data.get('graficos', []))} gráficos.")

    def log_procesamiento_evento(self, documento_id: int, etapa: str, estado: str, duracion_ms: Optional[int] = None, detalles: Optional[Dict] = None, error_mensaje: Optional[str] = None):
        sql = """
            INSERT INTO logs_procesamiento (documento_id, etapa, estado, duracion_ms, detalles, error_mensaje)
            VALUES (?, ?, ?, ?, ?, ?);
        """
        try:
            with self.conn.cursor() as cur:
                detalles_json = json.dumps(detalles) if detalles else None
                cur.execute(sql, (documento_id, etapa, estado, duracion_ms, detalles_json, error_mensaje))
                self.conn.commit()
        except pyodbc.Error as e:
            print(f"Error al registrar log de procesamiento: {e}")
            self.conn.rollback()

    def log_tarea(self, documento_id: int, nombre_tarea: str, estado: str, inicio: datetime, fin: datetime, resultados_encontrados: Optional[int] = None, error_mensaje: Optional[str] = None):
        sql = """
            INSERT INTO logs_tareas (documento_id, nombre_tarea, timestamp_inicio, timestamp_fin, estado, resultados_encontrados, error_mensaje)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql, (documento_id, nombre_tarea, inicio, fin, estado, resultados_encontrados, error_mensaje))
                self.conn.commit()
        except pyodbc.Error as e:
            print(f"Error al registrar log de tarea: {e}")
            self.conn.rollback()

db_manager = DBManager() 