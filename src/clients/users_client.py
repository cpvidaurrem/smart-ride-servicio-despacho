import httpx
import traceback
from typing import List, Optional, Dict, Any
from src.config import settings


class UsersClient:
    """Cliente HTTP para el servicio de usuarios"""
    
    def __init__(self):
        self.base_url = settings.users_service_url
        self.timeout = 10.0
    
    async def get_conductor(self, id_conductor: int, token: str = None) -> Optional[Dict[str, Any]]:
        """Obtener conductor por ID"""
        try:
            headers = {}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/users/conductores/{id_conductor}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    return None
                else:
                    print(f" Error obteniendo conductor {id_conductor}: {response.status_code}")
                    return None
        except Exception as e:
            print(f" Error en get_conductor: {e}")
            return None
    
    async def get_conductores_disponibles(self, token: str = None) -> List[Dict[str, Any]]:
        """Obtener conductores disponibles"""
        try:
            headers = {}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/users/conductores/all",
                    params={"estado": "disponible"},
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    print(f"📦 [USERS_CLIENT] Respuesta completa:")
                    print(f"   Tipo: {type(data)}")
                    print(f"   Claves: {data.keys() if isinstance(data, dict) else 'No es dict'}")
                    
                    #  Manejar estructura anidada
                    if not isinstance(data, dict):
                        print(" Respuesta no es un diccionario")
                        return []
                    
                    # Nivel 1: {"success": true, "data": {...}}
                    if "data" not in data:
                        print(" No se encontró clave 'data' en nivel 1")
                        return []
                    
                    nested_data = data["data"]
                    
                    if not isinstance(nested_data, dict):
                        print(" data.data no es un diccionario")
                        return []
                    
                    # Nivel 2: {"success": true, "data": [...], "total": 1}
                    if "data" not in nested_data:
                        print(" No se encontró clave 'data' en nivel 2")
                        return []
                    
                    conductores_raw = nested_data["data"]
                    
                    if not isinstance(conductores_raw, list):
                        print(f" data.data.data no es una lista: {type(conductores_raw)}")
                        return []
                    
                    print(f"✅ [USERS_CLIENT] Encontrados {len(conductores_raw)} conductores raw")
                    
                    #  Convertir cada conductor a diccionario plano
                    conductores = []
                    for c in conductores_raw:
                        if not isinstance(c, dict):
                            print(f"⚠️ Conductor no es dict: {type(c)}")
                            continue
                        
                        # Extraer datos del conductor
                        conductor_data = {
                            "id_conductor": c.get("id_conductor"),
                            "id_usuario": c.get("id_usuario"),
                            "numero_licencia": c.get("numero_licencia"),
                            "estado_conductor": c.get("estado_conductor"),
                            "calificacion_promedio": float(c.get("calificacion_promedio", 5.0)),
                            "total_viajes": int(c.get("total_viajes", 0)),
                            "marca_auto": c.get("marca_auto"),
                            "modelo_auto": c.get("modelo_auto"),
                            "placa_auto": c.get("placa_auto")
                        }
                        
                        # Validar campos obligatorios
                        if not conductor_data["id_conductor"]:
                            print(f"⚠️ Conductor sin id_conductor: {c}")
                            continue
                        
                        conductores.append(conductor_data)
                    
                    print(f"✅ [USERS_CLIENT] Conductores parseados correctamente: {len(conductores)}")
                    if conductores:
                        print(f"   Ejemplo: ID={conductores[0]['id_conductor']}, Estado={conductores[0]['estado_conductor']}, Calificación={conductores[0]['calificacion_promedio']}")
                    
                    return conductores
                else:
                    print(f" Error obteniendo conductores: {response.status_code}")
                    print(f"   Respuesta: {response.text}")
                    return []
        except Exception as e:
            print(f" Error en get_conductores_disponibles: {e}")
            traceback.print_exc()
            return []
    
    async def actualizar_estado_conductor(
        self,
        id_conductor: int,
        estado: str,
        token: str = None
    ) -> bool:
        """Actualizar estado del conductor"""
        try:
            headers = {"Content-Type": "application/json"}
            #  NO enviar token - endpoint es público
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.patch(
                    f"{self.base_url}/api/v1/users/{id_conductor}/estado",  
                    json={"estado_conductor": estado},
                    headers=headers
                )
                
                if response.status_code == 200:
                    print(f"✅ [USERS_CLIENT] Conductor {id_conductor} actualizado a estado '{estado}'")
                    return True
                else:
                    print(f" [USERS_CLIENT] Error actualizando conductor {id_conductor}: {response.status_code}")
                    print(f"   Respuesta: {response.text}")
                    return False
        except Exception as e:
            print(f" Error actualizando estado conductor: {e}")
            traceback.print_exc()
            return False


# Instancia global
users_client = UsersClient()