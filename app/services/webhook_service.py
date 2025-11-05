"""
Webhook Service für OSS goEcommerce
FastAPI-basierter Service zum Empfangen von Daten und SQL-Ausführung
"""

import json
import re
import threading
from typing import Dict, List, Optional, Tuple
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from app.core.logging_config import get_logger
from app.services.database_service import DatabaseService

logger = get_logger(__name__)


# Pydantic Models für Request/Response
class SQLQueryRequest(BaseModel):
    """Request-Model für SQL-Abfrage"""
    sql: str = Field(..., description="SQL-Abfrage die ausgeführt werden soll")
    query_name: Optional[str] = Field(None, description="Optionaler Name für die Abfrage")


class BatchSQLRequest(BaseModel):
    """Request-Model für mehrere SQL-Abfragen"""
    queries: List[SQLQueryRequest] = Field(..., description="Liste von SQL-Abfragen")


class GenericDataRequest(BaseModel):
    """Request-Model für generische Daten"""
    data: Dict = Field(..., description="Empfangene Daten")
    action: Optional[str] = Field(None, description="Aktion die ausgeführt werden soll")
    sql_query: Optional[str] = Field(None, description="Optional: SQL-Abfrage die ausgeführt werden soll")


class SQLResponse(BaseModel):
    """Response-Model für SQL-Abfragen"""
    success: bool
    message: str
    row_count: Optional[int] = None
    results: Optional[List[Dict]] = None
    error: Optional[str] = None


class WebhookServer:
    """
    FastAPI-Server für Webhook-Endpunkte.
    Läuft in einem separaten Thread.
    """
    
    def __init__(self, host: str = 'localhost', port: int = 8000, api_token: Optional[str] = None):
        """
        Initialisiert den Webhook-Server.
        
        Args:
            host: Server-Hostname
            port: Server-Port
            api_token: Optional API-Token für Authentifizierung
        """
        self.host = host
        self.port = port
        self.api_token = api_token or "default_token_change_me"
        self.app = FastAPI(
            title="OSS goEcommerce Webhook API",
            description="API für Empfang von Daten und SQL-Ausführung",
            version="1.0.0"
        )
        self.server_thread = None
        self.server_config = None
        self.database_service = DatabaseService()
        self._setup_routes()
        logger.info(f"WebhookServer initialisiert - {host}:{port}")
    
    def _setup_routes(self):
        """Richtet FastAPI-Routes ein"""
        
        async def verify_token(authorization: Optional[str] = Header(None, alias="Authorization")):
            """
            Dependency zur Token-Verifizierung.
            
            Erwartet Header: Authorization: Bearer <token>
            """
            if not self.api_token:
                # Kein Token erforderlich wenn api_token nicht gesetzt
                return True
            
            if not authorization:
                raise HTTPException(
                    status_code=401,
                    detail="Authorization header fehlt. Erwartet: Authorization: Bearer <token>",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Prüfe Bearer Token
            if not authorization.startswith("Bearer "):
                raise HTTPException(
                    status_code=401,
                    detail="Ungültiges Authorization Format. Erwartet: Bearer <token>",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            token = authorization.replace("Bearer ", "").strip()
            
            if token != self.api_token:
                logger.warning(f"Ungültiger API-Token verwendet (Token-Start: {token[:5]}...)")
                raise HTTPException(
                    status_code=403,
                    detail="Ungültiger API-Token",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            logger.debug("Token erfolgreich verifiziert")
            return True
        
        @self.app.post("/api/receive_data", response_model=Dict)
        async def receive_data(
            request: GenericDataRequest,
            authorized: bool = Depends(verify_token)
        ):
            """
            Hauptendpunkt zum Empfangen von Daten.
            
            Empfängt JSON-Daten und kann optional SQL ausführen.
            """
            try:
                logger.info(f"Empfange Daten über /api/receive_data: {request.action}")
                
                # Prüfe ob SQL-Abfrage enthalten ist
                if request.sql_query:
                    # Validiere SQL-Abfrage
                    if not self._validate_sql_query(request.sql_query):
                        logger.warning(f"Blockierte gefährliche SQL-Abfrage: {request.sql_query[:100]}...")
                        return JSONResponse(
                            status_code=403,
                            content={
                                "success": False,
                                "error": "SQL-Abfrage enthält nicht erlaubte Operationen"
                            }
                        )
                    
                    # Führe SQL-Abfrage aus
                    logger.info(f"Führe SQL-Abfrage aus: {request.sql_query[:100]}...")
                    success, message, results = self.database_service.execute_query(request.sql_query)
                    
                    if success:
                        formatted_results = []
                        if results:
                            for row in results:
                                if hasattr(row, 'keys'):
                                    formatted_results.append(dict(row))
                                else:
                                    formatted_results.append({
                                        f'column_{i}': value 
                                        for i, value in enumerate(row)
                                    })
                        
                        return {
                            "success": True,
                            "message": "Daten empfangen und SQL ausgeführt",
                            "action": request.action,
                            "data_received": request.data,
                            "sql_result": {
                                "row_count": len(formatted_results),
                                "results": formatted_results
                            }
                        }
                    else:
                        return JSONResponse(
                            status_code=500,
                            content={
                                "success": False,
                                "error": f"SQL-Fehler: {message}",
                                "data_received": request.data
                            }
                        )
                else:
                    # Keine SQL-Abfrage - nur Daten empfangen
                    return {
                        "success": True,
                        "message": "Daten erfolgreich empfangen",
                        "action": request.action,
                        "data_received": request.data
                    }
                    
            except Exception as e:
                logger.error(f"Fehler beim Verarbeiten von /api/receive_data: {e}")
                return JSONResponse(
                    status_code=500,
                    content={
                        "success": False,
                        "error": f"Server-Fehler: {str(e)}"
                    }
                )
        
        @self.app.post("/api/sql", response_model=SQLResponse)
        async def execute_sql(
            request: SQLQueryRequest,
            authorized: bool = Depends(verify_token)
        ):
            """
            Endpunkt für direkte SQL-Ausführung.
            
            Führt eine SQL-Abfrage aus.
            """
            try:
                # Validierung
                if not self._validate_sql_query(request.sql):
                    logger.warning(f"Blockierte gefährliche SQL-Abfrage: {request.sql[:100]}...")
                    return JSONResponse(
                        status_code=403,
                        content={
                            "success": False,
                            "error": "SQL-Abfrage enthält nicht erlaubte Operationen"
                        }
                    )
                
                # SQL-Abfrage ausführen
                logger.info(f"Führe SQL-Abfrage aus: {request.sql[:100]}...")
                success, message, results = self.database_service.execute_query(request.sql)
                
                if success:
                    formatted_results = []
                    if results:
                        for row in results:
                            if hasattr(row, 'keys'):
                                formatted_results.append(dict(row))
                            else:
                                formatted_results.append({
                                    f'column_{i}': value 
                                    for i, value in enumerate(row)
                                })
                    
                    return {
                        "success": True,
                        "message": message,
                        "row_count": len(formatted_results),
                        "results": formatted_results
                    }
                else:
                    return JSONResponse(
                        status_code=500,
                        content={
                            "success": False,
                            "error": message
                        }
                    )
                    
            except Exception as e:
                logger.error(f"Fehler beim Ausführen der SQL-Abfrage: {e}")
                return JSONResponse(
                    status_code=500,
                    content={
                        "success": False,
                        "error": f"Server-Fehler: {str(e)}"
                    }
                )
        
        @self.app.post("/api/batch_sql", response_model=Dict)
        async def execute_batch_sql(
            request: BatchSQLRequest,
            authorized: bool = Depends(verify_token)
        ):
            """
            Endpunkt für mehrere SQL-Abfragen.
            
            Führt mehrere SQL-Abfragen in einer Anfrage aus.
            """
            try:
                results = []
                for idx, query_obj in enumerate(request.queries):
                    sql_query = query_obj.sql
                    
                    # Validierung
                    if not self._validate_sql_query(sql_query):
                        logger.warning(f"Blockierte gefährliche SQL-Abfrage #{idx}: {sql_query[:100]}...")
                        results.append({
                            "index": idx,
                            "success": False,
                            "error": "SQL-Abfrage enthält nicht erlaubte Operationen"
                        })
                        continue
                    
                    # SQL-Abfrage ausführen
                    success, message, query_results = self.database_service.execute_query(sql_query)
                    
                    formatted_results = []
                    if query_results:
                        for row in query_results:
                            if hasattr(row, 'keys'):
                                formatted_results.append(dict(row))
                            else:
                                formatted_results.append({
                                    f'column_{i}': value 
                                    for i, value in enumerate(row)
                                })
                    
                    results.append({
                        "index": idx,
                        "success": success,
                        "message": message,
                        "row_count": len(formatted_results),
                        "results": formatted_results if success else None
                    })
                
                return {
                    "success": True,
                    "total_queries": len(request.queries),
                    "results": results
                }
                    
            except Exception as e:
                logger.error(f"Fehler beim Verarbeiten von Batch-SQL: {e}")
                return JSONResponse(
                    status_code=500,
                    content={
                        "success": False,
                        "error": f"Server-Fehler: {str(e)}"
                    }
                )
        
        @self.app.get("/api/health")
        async def health_check():
            """Health-Check-Endpunkt"""
            return {
                "status": "healthy",
                "service": "OSS goEcommerce Webhook API",
                "database_connected": self.database_service.has_saved_credentials(),
                "version": "1.0.0"
            }
        
        @self.app.get("/")
        async def root():
            """Root-Endpunkt mit API-Informationen"""
            return {
                "service": "OSS goEcommerce Webhook API",
                "version": "1.0.0",
                "endpoints": {
                    "/api/receive_data": "POST - Empfängt Daten und kann SQL ausführen",
                    "/api/sql": "POST - Führt eine SQL-Abfrage aus",
                    "/api/batch_sql": "POST - Führt mehrere SQL-Abfragen aus",
                    "/api/health": "GET - Health-Check"
                },
                "authentication": "Bearer Token im Authorization Header erforderlich" if self.api_token else "Keine Authentifizierung erforderlich"
            }
    
    def _validate_sql_query(self, sql_query: str) -> bool:
        """
        Validiert SQL-Abfrage für Sicherheit.
        
        Blockiert gefährliche Operationen wie:
        - DROP, TRUNCATE, DELETE ohne WHERE
        - ALTER, CREATE, EXEC, EXECUTE
        - System-Prozeduren
        
        Args:
            sql_query: Zu validierende SQL-Abfrage
            
        Returns:
            True wenn sicher, False wenn gefährlich
        """
        sql_upper = sql_query.upper().strip()
        
        # Gefährliche Operationen
        dangerous_patterns = [
            r'\bDROP\b',
            r'\bTRUNCATE\b',
            r'\bALTER\b',
            r'\bCREATE\b',
            r'\bEXEC\b',
            r'\bEXECUTE\b',
            r'\bSP_\w+',  # System-Prozeduren
            r'\bXP_\w+',  # Extended Prozeduren
            r'\bBACKUP\b',
            r'\bRESTORE\b',
            r'\bSHUTDOWN\b',
            r'\bKILL\b',
            r'--',  # SQL-Kommentare (können Injection sein)
            r'/\*',  # Mehrzeilige Kommentare
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, sql_upper):
                logger.warning(f"Gefährliches SQL-Pattern erkannt: {pattern}")
                return False
        
        # DELETE ohne WHERE ist gefährlich
        if re.search(r'\bDELETE\s+FROM\b', sql_upper):
            if 'WHERE' not in sql_upper:
                logger.warning("DELETE ohne WHERE-Klausel blockiert")
                return False
        
        # UPDATE ohne WHERE ist gefährlich
        if re.search(r'\bUPDATE\s+\w+\s+SET\b', sql_upper):
            if 'WHERE' not in sql_upper:
                logger.warning("UPDATE ohne WHERE-Klausel blockiert")
                return False
        
        return True
    
    def start(self):
        """Startet den Webhook-Server in einem separaten Thread"""
        if self.server_thread and self.server_thread.is_alive():
            logger.warning("Server läuft bereits")
            return
        
        def run_server():
            config = uvicorn.Config(
                self.app,
                host=self.host,
                port=self.port,
                log_level="info"
            )
            self.server_config = uvicorn.Server(config)
            logger.info(f"Webhook-Server gestartet auf http://{self.host}:{self.port}")
            self.server_config.run()
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        logger.info("Webhook-Server Thread gestartet")
    
    def stop(self):
        """Stoppt den Webhook-Server"""
        if self.server_config:
            logger.info("Stoppe Webhook-Server...")
            self.server_config.should_exit = True
            if self.server_thread:
                self.server_thread.join(timeout=5)
            self.server_config = None
            self.server_thread = None
            logger.info("Webhook-Server gestoppt")
        else:
            logger.warning("Server läuft nicht")
    
    def is_running(self) -> bool:
        """Prüft ob der Server läuft"""
        return (self.server_thread is not None and 
                self.server_thread.is_alive() and 
                self.server_config is not None)
    
    def get_url(self) -> str:
        """Gibt die Server-URL zurück"""
        return f"http://{self.host}:{self.port}"


class WebhookService:
    """
    Service-Klasse für Webhook-Funktionalität.
    Wrapper um WebhookServer für einfache Integration.
    """
    
    def __init__(self, host: str = 'localhost', port: int = 8000, api_token: Optional[str] = None):
        """
        Initialisiert den Webhook-Service.
        
        Args:
            host: Server-Hostname
            port: Server-Port
            api_token: Optional API-Token für Authentifizierung
        """
        self.host = host
        self.port = port
        self.api_token = api_token
        self.server = None
        logger.info(f"WebhookService initialisiert - {host}:{port}")
    
    def start_server(self) -> Tuple[bool, str]:
        """
        Startet den Webhook-Server.
        
        Returns:
            Tuple (success: bool, message: str)
        """
        try:
            if self.server and self.server.is_running():
                return True, "Server läuft bereits"
            
            self.server = WebhookServer(self.host, self.port, self.api_token)
            self.server.start()
            
            # Kurz warten, ob Server startet
            import time
            time.sleep(0.5)
            
            if self.server.is_running():
                url = self.server.get_url()
                logger.info(f"Webhook-Server erfolgreich gestartet: {url}")
                return True, f"Server gestartet: {url}"
            else:
                return False, "Server konnte nicht gestartet werden"
                
        except Exception as e:
            logger.error(f"Fehler beim Starten des Webhook-Servers: {e}")
            return False, f"Fehler: {str(e)}"
    
    def stop_server(self) -> Tuple[bool, str]:
        """
        Stoppt den Webhook-Server.
        
        Returns:
            Tuple (success: bool, message: str)
        """
        try:
            if not self.server:
                return True, "Server läuft nicht"
            
            if self.server.is_running():
                self.server.stop()
                logger.info("Webhook-Server gestoppt")
                return True, "Server gestoppt"
            else:
                return True, "Server läuft nicht"
                
        except Exception as e:
            logger.error(f"Fehler beim Stoppen des Webhook-Servers: {e}")
            return False, f"Fehler: {str(e)}"
    
    def is_server_running(self) -> bool:
        """Prüft ob der Server läuft"""
        return self.server is not None and self.server.is_running()
    
    def get_server_url(self) -> Optional[str]:
        """Gibt die Server-URL zurück"""
        if self.server and self.server.is_running():
            return self.server.get_url()
        return None
    
    def set_api_token(self, token: str):
        """Setzt den API-Token"""
        self.api_token = token
        if self.server:
            self.server.api_token = token
        logger.info("API-Token aktualisiert")

