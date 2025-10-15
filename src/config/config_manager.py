from utils.logger import logger
import json
import os
from getpass import getpass
from .constants import CONFIG_FILE
from utils.display_utils import display

class ConfigManager:
    def __init__(self):
        self.api_key = None
        self.freshdesk_domain = None
        self.clarity_username = None
        self.clarity_password = None
        self.clarity_domain = None
        self.load_config()
    
    def load_config(self):
        """Cargar configuración desde archivo"""
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                self.api_key = config.get('api_key')
                self.freshdesk_domain = config.get('freshdesk_domain')
                self.clarity_username = config.get('clarity_username')
                self.clarity_password = config.get('clarity_password')
                self.clarity_domain = config.get('clarity_domain')
                
            logger.log_info(f"Configuración cargada desde: {CONFIG_FILE}")
            
        except FileNotFoundError:
            logger.log_warning("Archivo de configuración no encontrado. Se usarán valores por defecto.")
        except Exception as e:
            logger.log_error(f"Error al cargar configuración: {e}")

    def save_config(self):
        """Guardar configuración en archivo"""
        config = {
            'api_key': self.api_key,
            'freshdesk_domain': self.freshdesk_domain,
            'clarity_username': self.clarity_username,
            'clarity_password': self.clarity_password,
            'clarity_domain': self.clarity_domain
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)

    def ingresar_datos(self):
        """Interfaz para ingresar datos de conexión"""
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
                display.press_enter_to_continue()

    def configurar_freshdesk_completo(self):
        """Configuración completa de Freshdesk en un solo flujo"""
        display.clear_screen()
        print("\n╔══════════════════════════════════════════════╗")
        print("║               🌐 CONFIGURAR FRESHDESK        ║")
        print("╚══════════════════════════════════════════════╝")
        
        # 1. API Key
        print("\n🔑 INGRESE API KEY DE FRESHDESK:")
        self.api_key = input("👉 API Key: ").strip()
        
        # 2. Dominio
        print("\n🌐 CONFIGURACIÓN DE DOMINIO:")
        print("   1. Usar palabra clave (recomendado)")
        print("   2. Ingresar dominio manualmente")
        
        opcion_dominio = input("👉 Seleccione opción (1/2): ").strip()
        
        if opcion_dominio == "1":
            print("\n📝 CONFIGURACIÓN AUTOMÁTICA DE DOMINIO")
            print("💡 Ejemplo: Si ingresa 'mitienda'")
            print("   → Se generará: https://mitienda.freshdesk.com")
            print()
            
            palabra_clave = input("🔑 Palabra clave de la empresa (ej: 'mitienda'): ").strip()
            if palabra_clave:
                self.freshdesk_domain = f"https://{palabra_clave}.freshdesk.com"
                print(f"✅ Dominio generado: {self.freshdesk_domain}")
                
        elif opcion_dominio == "2":
            print("\n🌐 CONFIGURACIÓN MANUAL DE DOMINIO")
            print("💡 Ingrese el dominio completo de Freshdesk")
            print("   Ejemplo: https://mitienda.freshdesk.com")
            print()
            
            dominio_manual = input("🌐 Dominio completo: ").strip()
            if dominio_manual:
                if not dominio_manual.startswith(('http://', 'https://')):
                    dominio_manual = f"https://{dominio_manual}"
                self.freshdesk_domain = dominio_manual
        
        # Guardar
        self.save_config()
        print(f"\n✅ Configuración de Freshdesk guardada:")
        print(f"   🔑 API Key: {'✅ Configurada' if self.api_key else '❌ No configurada'}")
        print(f"   🌐 Dominio: {self.freshdesk_domain if self.freshdesk_domain else '❌ No configurado'}")

    def configurar_clarity_completo(self):
        """Configuración completa de Clarity en un solo flujo"""
        display.clear_screen()
        print("\n╔══════════════════════════════════════════════╗")
        print("║               🔐 CONFIGURAR CLARITY          ║")
        print("╚══════════════════════════════════════════════╝")
        
        # 1. Usuario y Contraseña
        print("\n👤 INGRESE CREDENCIALES DE CLARITY:")
        self.clarity_username = input("👉 Usuario: ").strip()
        self.clarity_password = input("🔐 Contraseña: ").strip()
        
        # 2. Dominio
        print("\n🌐 CONFIGURACIÓN DE DOMINIO:")
        print("   1. Usar palabra clave y puerto (recomendado)")
        print("   2. Ingresar dominio manualmente")
        
        opcion_dominio = input("👉 Seleccione opción (1/2): ").strip()
        
        if opcion_dominio == "1":
            print("\n📝 CONFIGURACIÓN AUTOMÁTICA DE DOMINIO")
            print("💡 Ejemplo: Si ingresa 'mitienda' y '1234'")
            print("   → Se generará: https://pmservice.mitienda.com:1234/ppm/rest/v1")
            print()
            
            palabra_clave = input("🔑 Palabra clave de la empresa (ej: 'mitienda'): ").strip()
            puerto = input("🔢 Número de puerto (ej: 1234): ").strip()
            
            if palabra_clave and puerto:
                self.clarity_domain = f"https://pmservice.{palabra_clave}.com:{puerto}/ppm/rest/v1"
                print(f"✅ Dominio generado: {self.clarity_domain}")
                
        elif opcion_dominio == "2":
            print("\n🌐 CONFIGURACIÓN MANUAL DE DOMINIO")
            print("💡 Ingrese el dominio completo de Clarity")
            print("   Ejemplo: https://pmservice.ejemplo.com:1234/ppm/rest/v1")
            print()
            
            dominio_manual = input("🌐 Dominio completo: ").strip()
            if dominio_manual:
                if not dominio_manual.startswith(('http://', 'https://')):
                    dominio_manual = f"https://{dominio_manual}"
                self.clarity_domain = dominio_manual
        
        # Guardar
        self.save_config()
        print(f"\n✅ Configuración de Clarity guardada:")
        print(f"   👤 Usuario: {self.clarity_username if self.clarity_username else '❌ No configurado'}")
        print(f"   🌐 Dominio: {self.clarity_domain if self.clarity_domain else '❌ No configurado'}")

    def cargar_configuracion_desde_txt(self):
        """Cargar configuración desde archivo de texto"""
        print("\n📁 CARGAR CONFIGURACIÓN DESDE ARCHIVO TXT")
        print("═" * 50)
        from utils.file_utils import FileUtils
        # Mostrar formato esperado
        self._mostrar_formato_txt()
        
        print("\n📝 Seleccione el archivo de configuración (.txt):")
        ruta_archivo = FileUtils.seleccionar_archivo(
            "Seleccione el archivo de configuración", 
            [("Archivos de texto", "*.txt")]
        )
        
        if not ruta_archivo:
            print("❌ No se seleccionó ningún archivo.")
            return False
        
        if not os.path.exists(ruta_archivo):
            print("❌ El archivo no existe.")
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
        """Leer y parsear archivo de configuración TXT"""
        config_data = {}
        
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            lineas = f.readlines()
        
        for num_linea, linea in enumerate(lineas, 1):
            linea = linea.strip()
            
            # Saltar líneas vacías o comentarios
            if not linea or linea.startswith('#'):
                continue
            
            # Buscar separador de dos puntos
            if ':' not in linea:
                print(f"⚠️  Línea {num_linea} ignorada (formato incorrecto): {linea}")
                continue
            
            # Separar clave y valor
            partes = linea.split(':', 1)  # Dividir solo en el primer dos puntos
            clave = partes[0].strip()
            valor = partes[1].strip() if len(partes) > 1 else ""
            
            # Mapear claves del TXT a atributos internos
            mapeo_claves = {
                'API_Freshdesk': 'api_key',
                'Freshdesk_domain': 'freshdesk_domain', 
                'Clarity_user': 'clarity_username',
                'Clarity_pass': 'clarity_password',
                'Clarity_domain': 'clarity_domain'
            }
            
            if clave in mapeo_claves:
                config_data[mapeo_claves[clave]] = valor
                print(f"✅ {clave} → {valor}")
            else:
                print(f"⚠️  Clave desconocida en línea {num_linea}: {clave}")
        
        return config_data

    def _aplicar_configuracion_desde_txt(self, config_data):
        """Aplicar la configuración leída desde el archivo TXT"""
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
            self.save_config()
            print(f"\n✅ CONFIGURACIÓN ACTUALIZADA EXITOSAMENTE")
            print("📋 Cambios aplicados:")
            for cambio in cambios_realizados:
                print(f"   • {cambio}")
            print(f"\n💾 Configuración guardada en: {CONFIG_FILE}")
        else:
            print("ℹ️  No se realizaron cambios (valores vacíos o no reconocidos)")

    # Los demás métodos permanecen igual...
    def configurar_dominios_manualmente(self):
        """Configurar dominios manualmente con URLs completas"""
        while True:
            print("\n=== CONFIGURACIÓN MANUAL DE DOMINIOS ===")
            print("1. Configurar Dominio Freshdesk Manualmente")
            print("2. Configurar Dominio Clarity Manualmente")
            print("3. Ver dominios actuales")
            print("0. Volver")
            
            opcion = input("Seleccione una opción: ").strip()

            if opcion == "1":
                self._configurar_dominio_freshdesk_manual()

            elif opcion == "2":
                self._configurar_dominio_clarity_manual()

            elif opcion == "3":
                self.mostrar_dominios_actuales()

            elif opcion == "0":
                break
            else:
                print("❌ Opción inválida.\n")

    def _configurar_dominio_freshdesk_manual(self):
        """Configurar dominio Freshdesk manualmente"""
        print("\n🌐 CONFIGURACIÓN MANUAL DOMINIO FRESHDESK")
        print("💡 Ejemplo: https://mitienda.freshdesk.com")
        
        # Mostrar dominio actual si existe
        if self.freshdesk_domain:
            print(f"📌 Dominio actual: {self.freshdesk_domain}")
        
        dominio_manual = input("👉 Ingrese el dominio completo de Freshdesk: ").strip()
        
        if dominio_manual:
            # Validar formato básico
            if not dominio_manual.startswith(('http://', 'https://')):
                dominio_manual = f"https://{dominio_manual}"
            
            # Advertencia si no contiene el dominio estándar
            if '.freshdesk.com' not in dominio_manual:
                print("⚠️  El dominio no contiene '.freshdesk.com'")
                confirmar = input("¿Desea guardarlo de todas formas? (S/N): ").strip().upper()
                if confirmar != 'S':
                    return
            
            self.freshdesk_domain = dominio_manual
            self.save_config()
            print(f"✅ Dominio Freshdesk configurado manualmente: {self.freshdesk_domain}\n")
        else:
            print("❌ Dominio inválido.\n")

    def _configurar_dominio_clarity_manual(self):
        """Configurar dominio Clarity manualmente"""
        print("\n🌐 CONFIGURACIÓN MANUAL DOMINIO CLARITY")
        print("💡 Ejemplo: https://pmservice.ejemplo.com:8043/ppm/rest/v1")
        
        # Mostrar dominio actual si exists
        if self.clarity_domain:
            print(f"📌 Dominio actual: {self.clarity_domain}")
        
        dominio_manual = input("👉 Ingrese el dominio completo de Clarity: ").strip()
        
        if dominio_manual:
            # Validar formato básico
            if not dominio_manual.startswith(('http://', 'https://')):
                dominio_manual = f"https://{dominio_manual}"
            
            self.clarity_domain = dominio_manual
            self.save_config()
            print(f"✅ Dominio Clarity configurado manualmente: {self.clarity_domain}\n")
        else:
            print("❌ Dominio inválido.\n")

    def mostrar_dominios_actuales(self):
        """Mostrar solo la configuración de dominios"""
        print("\n--- DOMINIOS ACTUALES ---")
        print(f"🌐 Freshdesk: {self.freshdesk_domain if self.freshdesk_domain else '❌ No configurado'}")
        print(f"🌐 Clarity: {self.clarity_domain if self.clarity_domain else '❌ No configurado'}")
        print("--------------------------")

    def mostrar_configuracion(self):
        """Mostrar configuración actual con nuevo formato"""
        display.clear_screen()
        print("\n╔══════════════════════════════════════════════╗")
        print("║               👁️ ESTADO DE CONFIGURACIÓN      ║")
        print("╚══════════════════════════════════════════════╝")
        
        print("\n🔐 CONEXIONES:")
        print(f"   🌐 Freshdesk:")
        print(f"      {'✅' if self.api_key else '❌'} API Key: {'Configurada' if self.api_key else 'No configurada'}")
        print(f"      {'✅' if self.freshdesk_domain else '❌'} Dominio: {self.freshdesk_domain if self.freshdesk_domain else 'No configurado'}")
        
        print(f"\n   🔐 Clarity:")
        print(f"      {'✅' if self.clarity_username else '❌'} Usuario: {self.clarity_username if self.clarity_username else 'No configurado'}")
        print(f"      {'✅' if self.clarity_domain else '❌'} Dominio: {self.clarity_domain if self.clarity_domain else 'No configurado'}")
        
        # Verificar estado general
        config_completa = (self.api_key and self.freshdesk_domain and 
                        self.clarity_username and self.clarity_password and self.clarity_domain)
        
        print(f"\n📊 ESTADO GENERAL:")
        print(f"   {'✅' if config_completa else '❌'} {'Configuración completa - Sistema operativo' if config_completa else 'Configuración incompleta'}")
        
        # Verificar archivos disponibles
        try:
            from utils.file_utils import FileUtils
            archivos = FileUtils.listar_archivos_input()
            print(f"   📂 Archivos disponibles: {len(archivos)} archivos en data/input")
            if archivos:
                for archivo in archivos[:3]:  # Mostrar solo los primeros 3
                    print(f"      • {archivo}")
                if len(archivos) > 3:
                    print(f"      ... y {len(archivos) - 3} más")
        except:
            print("   📂 No se pudo verificar archivos disponibles")
        
        print("\n──────────────────────────────────────────────────")
        input("↩️  Presione Enter para volver...")

    def validar_configuracion(self):
        """Validar que la configuración de Freshdesk esté completa"""
        if not self.api_key or not self.freshdesk_domain:
            print("❌ Configuración de Freshdesk incompleta.")
            print("💡 Use la opción 1 del menú principal para configurar")
            return False
        return True

    def validar_configuracion_clarity(self):
        """Validar que la configuración de Clarity esté completa"""
        if not self.clarity_username or not self.clarity_password or not self.clarity_domain:
            print("❌ Configuración de Clarity incompleta.")
            print("💡 Use la opción 1 del menú principal para configurar")
            return False
        return True