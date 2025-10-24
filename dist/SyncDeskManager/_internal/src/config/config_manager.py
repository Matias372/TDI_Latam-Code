from utils.logging import logger
# O para funcionalidades específicas:
from utils.logging import logger, TransactionLogger
import json
import os
from getpass import getpass
from .constants import CONFIG_FILE
from utils.display_utils import display

class ConfigManager:
    def __init__(self):
        # 🚀 CONFIGURACIÓN VOLÁTIL - Solo en memoria
        self._config_volatile = {
            'api_key': None,
            'freshdesk_domain': None, 
            'clarity_username': None,
            'clarity_password': None,
            'clarity_domain': None
        }
        
        # 📁 Configuración NO sensible que sí podemos persistir (opcional)
        self._config_non_sensitive = {}
        self._load_non_sensitive_config()
        
        logger.log_info("ConfigManager inicializado - Modo volátil en memoria")

    def _load_non_sensitive_config(self):
        """Cargar solo configuraciones NO sensibles si existen"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    # Solo cargar configuraciones no sensibles
                    self._config_non_sensitive = {
                        'ui_settings': config.get('ui_settings', {}),
                        'last_used_paths': config.get('last_used_paths', []),
                        'preferences': config.get('preferences', {})
                    }
        except Exception as e:
            logger.log_warning(f"No se pudo cargar config no sensible: {e}")

    def _save_non_sensitive_config(self):
        """Guardar solo configuraciones NO sensibles"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self._config_non_sensitive, f, indent=4)
        except Exception as e:
            logger.log_warning(f"No se pudo guardar config no sensible: {e}")

    # 🚀 PROPIEDADES PARA ACCESO SEGURO
    @property
    def api_key(self):
        return self._config_volatile['api_key']
    
    @api_key.setter 
    def api_key(self, value):
        self._config_volatile['api_key'] = value

    @property
    def freshdesk_domain(self):
        return self._config_volatile['freshdesk_domain']
    
    @freshdesk_domain.setter
    def freshdesk_domain(self, value):
        self._config_volatile['freshdesk_domain'] = value

    @property
    def clarity_username(self):
        return self._config_volatile['clarity_username']
    
    @clarity_username.setter
    def clarity_username(self, value):
        self._config_volatile['clarity_username'] = value

    @property
    def clarity_password(self):
        return self._config_volatile['clarity_password']
    
    @clarity_password.setter
    def clarity_password(self, value):
        self._config_volatile['clarity_password'] = value

    @property
    def clarity_domain(self):
        return self._config_volatile['clarity_domain']
    
    @clarity_domain.setter
    def clarity_domain(self, value):
        self._config_volatile['clarity_domain'] = value

    def save_config(self):
        """NO guarda datos sensibles - solo configuración no sensible"""
        self._save_non_sensitive_config()
        logger.log_info("Configuración volátil: datos sensibles NO guardados en disco")

    def load_config(self):
        """NO carga datos sensibles - solo configuración no sensible"""
        self._load_non_sensitive_config()
        logger.log_info("Configuración volátil: datos sensibles NO cargados desde disco")

    def clear_sensitive_data(self):
        """Limpiar todos los datos sensibles de la memoria"""
        sensitive_keys = ['api_key', 'clarity_password']
        for key in sensitive_keys:
            self._config_volatile[key] = None
        logger.log_info("Datos sensibles limpiados de la memoria")

    def get_config_status(self):
        """Obtener estado de configuración sin revelar datos sensibles"""
        return {
            'freshdesk_configured': bool(self.api_key and self.freshdesk_domain),
            'clarity_configured': bool(self.clarity_username and self.clarity_password and self.clarity_domain),
            'has_api_key': bool(self.api_key),
            'has_clarity_password': bool(self.clarity_password)
        }

    def ingresar_datos(self):
        """Interfaz para ingresar datos de conexión - VERSIÓN VOLÁTIL"""
        while True:
            display.clear_screen()
            print("\n╔══════════════════════════════════════════════╗")
            print("║               🔧 CONFIGURACIÓN               ║")
            print("╚══════════════════════════════════════════════╝")
            
            print("   🌐 1. Configurar Freshdesk (API + Dominio)")
            print("   🔐 2. Configurar Clarity (Usuario + Contraseña + Dominio)")
            print("   📁 3. Cargar configuración desde archivo TXT")
            print("   👁️ 4. Ver estado de configuración")
            print("   ↩️  0. Volver al menú principal")
            
            opcion = input("\n👉 Seleccione una opción: ").strip()

            if opcion == "1":
                self.configurar_freshdesk_completo()
            elif opcion == "2":
                self.configurar_clarity_completo()
            elif opcion == "3":
                self.cargar_configuracion_desde_txt()
            elif opcion == "4":
                self.mostrar_configuracion()
            elif opcion == "0":
                break
            else:
                print("❌ Opción inválida.\n")
                display.press_enter_to__continue()

    def configurar_freshdesk_completo(self):
        """Configuración volátil de Freshdesk"""
        display.clear_screen()
        print("\n╔══════════════════════════════════════════════╗")
        print("║               🌐 CONFIGURAR FRESHDESK        ║")
        print("╚══════════════════════════════════════════════╝")
        
        print("\n🔑 INGRESE API KEY DE FRESHDESK:")
        self.api_key = input("👉 API Key: ").strip()
        
        print("\n🌐 CONFIGURACIÓN DE DOMINIO:")
        print("   1. Usar palabra clave (recomendado)")
        print("   2. Ingresar dominio manualmente")
        
        opcion_dominio = input("👉 Seleccione opción (1/2): ").strip()
        
        if opcion_dominio == "1":
            palabra_clave = input("🔑 Palabra clave de la empresa (ej: 'mitienda'): ").strip()
            if palabra_clave:
                self.freshdesk_domain = f"https://{palabra_clave}.freshdesk.com"
                print(f"✅ Dominio generado: {self.freshdesk_domain}")
        elif opcion_dominio == "2":
            dominio_manual = input("🌐 Dominio completo: ").strip()
            if dominio_manual:
                if not dominio_manual.startswith(('http://', 'https://')):
                    dominio_manual = f"https://{dominio_manual}"
                self.freshdesk_domain = dominio_manual
        
        # NO guardamos en disco - solo en memoria
        print(f"\n✅ Configuración de Freshdesk cargada en memoria:")
        print(f"   🔑 API Key: {'✅ Configurada' if self.api_key else '❌ No configurada'}")
        print(f"   🌐 Dominio: {self.freshdesk_domain if self.freshdesk_domain else '❌ No configurado'}")
        print("   💡 Nota: Los datos NO se guardarán en disco")
        display.press_enter_to_continue()

    def configurar_clarity_completo(self):
        """Configuración volátil de Clarity"""
        display.clear_screen()
        print("\n╔══════════════════════════════════════════════╗")
        print("║               🔐 CONFIGURAR CLARITY          ║")
        print("╚══════════════════════════════════════════════╝")
        
        print("\n👤 INGRESE CREDENCIALES DE CLARITY:")
        self.clarity_username = input("👉 Usuario: ").strip()
        self.clarity_password = getpass("🔐 Contraseña: ").strip()
        
        print("\n🌐 CONFIGURACIÓN DE DOMINIO:")
        print("   1. Usar palabra clave y puerto (recomendado)")
        print("   2. Ingresar dominio manualmente")
        
        opcion_dominio = input("👉 Seleccione opción (1/2): ").strip()
        
        if opcion_dominio == "1":
            palabra_clave = input("🔑 Palabra clave de la empresa: ").strip()
            puerto = input("🔢 Número de puerto: ").strip()
            if palabra_clave and puerto:
                self.clarity_domain = f"https://pmservice.{palabra_clave}.com:{puerto}/ppm/rest/v1"
                print(f"✅ Dominio generado: {self.clarity_domain}")
        elif opcion_dominio == "2":
            dominio_manual = input("🌐 Dominio completo: ").strip()
            if dominio_manual:
                if not dominio_manual.startswith(('http://', 'https://')):
                    dominio_manual = f"https://{dominio_manual}"
                self.clarity_domain = dominio_manual
        
        # NO guardamos en disco - solo en memoria
        print(f"\n✅ Configuración de Clarity cargada en memoria:")
        print(f"   👤 Usuario: {self.clarity_username if self.clarity_username else '❌ No configurado'}")
        print(f"   🌐 Dominio: {self.clarity_domain if self.clarity_domain else '❌ No configurado'}")
        print("   💡 Nota: Los datos NO se guardarán en disco")
        display.press_enter_to_continue()

    def cargar_configuracion_desde_txt(self):
        """Cargar configuración desde archivo TXT a memoria volátil"""
        print("\n📁 CARGAR CONFIGURACIÓN DESDE ARCHIVO TXT")
        print("═" * 50)
        
        from utils.file_utils import FileUtils
        self._mostrar_formato_txt()
        
        print("\n📝 Seleccione el archivo de configuración (.txt):")
        ruta_archivo = FileUtils.seleccionar_archivo(
            "Seleccione el archivo de configuración", 
            [("Archivos de texto", "*.txt")]
        )
        
        if not ruta_archivo:
            print("❌ No se seleccionó ningún archivo.")
            return False
        
        try:
            config_data = self._leer_archivo_configuracion(ruta_archivo)
            if config_data:
                self._aplicar_configuracion_desde_txt(config_data)
                return True
            else:
                print("❌ No se pudo cargar la configuración desde el archivo.")
                return False
        except Exception as e:
            print(f"❌ Error al cargar configuración: {str(e)}")
            return False

    def _mostrar_formato_txt(self):
        """Mostrar el formato esperado para el archivo TXT"""
        print("📋 FORMATO ESPERADO DEL ARCHIVO TXT:")
        print("-" * 40)
        print("El archivo debe contener las siguientes líneas:")
        print("")
        print("API_Freshdesk: tu_api_key_aqui")
        print("Freshdesk_domain: https://tudominio.freshdesk.com")
        print("Clarity_user: tu_usuario_clarity")
        print("Clarity_pass: tu_contraseña_clarity")
        print("Clarity_domain: https://pmservice.tudominio.com:##NUMERO##/ppm/rest/v1")
        print("")
        print("💡 NOTAS:")
        print("• Las claves son sensibles a mayúsculas/minúsculas")
        print("• Los valores van después de los dos puntos")
        print("• Se pueden incluir comentarios con # al inicio de la línea")
        print("• Los espacios alrededor de los dos puntos son opcionales")
        print("-" * 40)

    def _leer_archivo_configuracion(self, ruta_archivo):
        """Leer archivo TXT y cargar en memoria volátil"""
        config_data = {}
        
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            lineas = f.readlines()
        
        for num_linea, linea in enumerate(lineas, 1):
            linea = linea.strip()
            if not linea or linea.startswith('#'):
                continue
            
            if ':' not in linea:
                continue
            
            partes = linea.split(':', 1)
            clave = partes[0].strip()
            valor = partes[1].strip() if len(partes) > 1 else ""
            
            mapeo_claves = {
                'API_Freshdesk': 'api_key',
                'Freshdesk_domain': 'freshdesk_domain', 
                'Clarity_user': 'clarity_username',
                'Clarity_pass': 'clarity_password',
                'Clarity_domain': 'clarity_domain'
            }
            
            if clave in mapeo_claves:
                config_data[mapeo_claves[clave]] = valor
                print(f"✅ {clave} → Cargado en memoria")
        
        return config_data

    def _aplicar_configuracion_desde_txt(self, config_data):
        """Aplicar configuración del TXT a memoria volátil"""
        cambios_realizados = []
        
        if 'api_key' in config_data and config_data['api_key']:
            self.api_key = config_data['api_key']
            cambios_realizados.append("API Key Freshdesk")
        
        if 'freshdesk_domain' in config_data and config_data['freshdesk_domain']:
            self.freshdesk_domain = config_data['freshdesk_domain']
            cambios_realizados.append("Dominio Freshdesk")
        
        if 'clarity_username' in config_data and config_data['clarity_username']:
            self.clarity_username = config_data['clarity_username']
            cambios_realizados.append("Usuario Clarity")
        
        if 'clarity_password' in config_data and config_data['clarity_password']:
            self.clarity_password = config_data['clarity_password']
            cambios_realizados.append("Contraseña Clarity")
        
        if 'clarity_domain' in config_data and config_data['clarity_domain']:
            self.clarity_domain = config_data['clarity_domain']
            cambios_realizados.append("Dominio Clarity")
        
        if cambios_realizados:
            print(f"\n✅ CONFIGURACIÓN CARGADA EN MEMORIA")
            print("📋 Datos cargados:")
            for cambio in cambios_realizados:
                print(f"   • {cambio}")
            print("💡 Los datos son volátiles y se perderán al cerrar la aplicación")
        else:
            print("ℹ️  No se cargaron datos (valores vacíos o no reconocidos)")
        display.press_enter_to_continue()

    def mostrar_configuracion(self):
        """Mostrar estado de configuración sin revelar datos sensibles"""
        display.clear_screen()
        print("\n╔══════════════════════════════════════════════╗")
        print("║               👁️ ESTADO DE CONFIGURACIÓN      ║")
        print("╚══════════════════════════════════════════════╝")
        
        status = self.get_config_status()
        
        print("\n🔐 CONEXIONES:")
        print(f"   🌐 Freshdesk: {'✅ Configurado' if status['freshdesk_configured'] else '❌ No configurado'}")
        print(f"      🔑 API Key: {'✅ Presente' if status['has_api_key'] else '❌ No configurada'}")
        print(f"      🌐 Dominio: {self.freshdesk_domain if self.freshdesk_domain else 'No configurado'}")
        
        print(f"\n   🔐 Clarity:")
        print(f"      👤 Usuario: {self.clarity_username if self.clarity_username else 'No configurado'}")
        print(f"      🔐 Contraseña: {'✅ Presente' if status['has_clarity_password'] else '❌ No configurada'}")
        print(f"      🌐 Dominio: {self.clarity_domain if self.clarity_domain else 'No configurado'}")
        
        print(f"\n📊 ESTADO GENERAL:")
        print(f"   {'✅' if status['freshdesk_configured'] and status['clarity_configured'] else '❌'} {'Configuración completa - Sistema operativo' if status['freshdesk_configured'] and status['clarity_configured'] else 'Configuración incompleta'}")
        
        print("\n💡 INFORMACIÓN:")
        print("   • Los datos sensibles NO se guardan en disco")
        print("   • La configuración es volátil (se pierde al cerrar)")
        print("   • Use 'Configurar conexión' para cargar datos")
        
        print("\n──────────────────────────────────────────────────")
        display.press_enter_to_continue()

    def validar_configuracion(self):
        """Validar configuración de Freshdesk en memoria"""
        if not self.api_key or not self.freshdesk_domain:
            print("❌ Configuración de Freshdesk incompleta en memoria.")
            print("💡 Use la opción 'Configurar conexión' para cargar datos")
            return False
        return True

    def validar_configuracion_clarity(self):
        """Validar configuración de Clarity en memoria"""
        if not self.clarity_username or not self.clarity_password or not self.clarity_domain:
            print("❌ Configuración de Clarity incompleta en memoria.")
            print("💡 Use la opción 'Configurar conexión' para cargar datos")
            return False
        return True

    # 🆕 MÉTODOS ADICIONALES PARA COMPATIBILIDAD
    def configurar_dominios_manualmente(self):
        """Método existente para compatibilidad - redirige a los nuevos"""
        self.ingresar_datos()

    def _configurar_dominio_freshdesk_manual(self):
        """Método existente para compatibilidad"""
        self.configurar_freshdesk_completo()

    def _configurar_dominio_clarity_manual(self):
        """Método existente para compatibilidad"""
        self.configurar_clarity_completo()

    def mostrar_dominios_actuales(self):
        """Método existente para compatibilidad"""
        self.mostrar_configuracion()