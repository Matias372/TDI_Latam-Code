# 📁 src/features/classification/pattern_manager.py (NUEVO - mismo código anterior)

import re
from collections import Counter
import pandas as pd
from utils.display_utils import display

class PatternManager:
    def __init__(self, config_manager):
        self.config_manager = config_manager

        self.config = {
            'variable_patterns': {
                'enabled': True,
                'server_patterns': [
                    r'pwcauimapp\d+',
                    r'appserver\d+',
                    r'dbserver\d+',
                    r'webapp\d+',
                    r'srv\d+'
                ],
                'normalized_to': {
                    'pwcauimapp': 'servidor aplicacion uim',
                    'appserver': 'servidor aplicaciones',
                    'dbserver': 'servidor base datos',
                    'webapp': 'aplicacion web',
                    'srv': 'servidor'
                },
                'custom_patterns': {}
            }
        }
        
        # 🆕 INTENTAR CARGAR CONFIGURACIÓN PERSONALIZADA SI EXISTE
        self._cargar_configuracion_personalizada()

    def mostrar_menu_gestion_patrones(self):
        """Menú principal de gestión de patrones variables"""
        while True:
            display.clear_screen()
            print("\n╔══════════════════════════════════════════════╗")
            print("║           🔄 GESTIÓN DE PATRONES            ║")
            print("╚══════════════════════════════════════════════╝")
            
            print("   🔧 1. Ver patrones actuales")
            print("   ➕ 2. Agregar patrón personalizado")
            print("   ✏️  3. Modificar patrón existente")
            print("   🗑️  4. Eliminar patrón")
            print("   🧪 5. Probar normalización con texto")
            print("   ⚡ 6. Activar/Desactivar normalización")
            print("   🤖 7. Detección automática de patrones")
            print("   ↩️  0. Volver al menú anterior")
            
            opcion = input("\n👉 Seleccione una opción: ").strip()

            if opcion == "1":
                self.mostrar_patrones_actuales()
            elif opcion == "2":
                self.agregar_patron_personalizado()
            elif opcion == "3":
                self.modificar_patron_existente()
            elif opcion == "4":
                self.eliminar_patron()
            elif opcion == "5":
                self.probar_normalizacion_texto()
            elif opcion == "6":
                self.toggle_normalizacion()
            elif opcion == "7":
                self.deteccion_automatica_patrones()
            elif opcion == "0":
                break
            else:
                print("❌ Opción inválida.")
                display.press_enter_to_continue()

    def mostrar_patrones_actuales(self):
        """Muestra todos los patrones configurados"""
        print("\n📋 PATRONES CONFIGURADOS ACTUALMENTE")
        print("=" * 50)
        
        variable_config = self.config.get('variable_patterns', {})
        
        print(f"🔄 Normalización: {'✅ ACTIVADA' if variable_config.get('enabled', True) else '❌ DESACTIVADA'}")
        
        print("\n🏷️  PATRONES PREDEFINIDOS:")
        server_patterns = variable_config.get('server_patterns', [])
        normalized_to = variable_config.get('normalized_to', {})
        
        for i, pattern in enumerate(server_patterns, 1):
            base = re.sub(r'\\d\+', '', pattern)  # Extraer base sin \d+
            meaning = normalized_to.get(base, "No definido")
            print(f"   {i}. {pattern} -> '{meaning}'")
        
        custom_patterns = variable_config.get('custom_patterns', {})
        print(f"\n🎯 PATRONES PERSONALIZADOS ({len(custom_patterns)}):")
        if custom_patterns:
            for i, (pattern, meaning) in enumerate(custom_patterns.items(), 1):
                print(f"   {i}. {pattern} -> '{meaning}'")
        else:
            print("   🤷 No hay patrones personalizados")
        
        display.press_enter_to_continue()

    def agregar_patron_personalizado(self):
        """Agrega un nuevo patrón personalizado"""
        print("\n➕ AGREGAR PATRÓN PERSONALIZADO")
        print("=" * 50)
        
        print("Ejemplos de patrones:")
        print("  • pwcauimapp\\d+  (detecta: PWCAUIMAPP12, PWCAUIMAPP5)")
        print("  • miempresa\\d+   (detecta: MIEMPRESA01, MIEMPRESA99)")
        print("  • cluster\\d+     (detecta: CLUSTER01, CLUSTER15)")
        
        patron = input("\n🔍 Patrón (regex): ").strip()
        if not patron:
            print("❌ El patrón no puede estar vacío")
            display.press_enter_to_continue()
            return
        
        # Validar que sea regex válido
        try:
            re.compile(patron)
        except re.error as e:
            print(f"❌ Error en el patrón regex: {e}")
            display.press_enter_to_continue()
            return
        
        significado = input("🎯 Significado normalizado: ").strip()
        if not significado:
            print("❌ El significado no puede estar vacío")
            display.press_enter_to_continue()
            return
        
        # Agregar a configuración usando el nuevo método set
        current_patterns = self.get('variable_patterns.custom_patterns', {})
        current_patterns[patron] = significado
        self.set('variable_patterns.custom_patterns', current_patterns)
        
        print(f"✅ Patrón agregado: '{patron}' -> '{significado}'")
        display.press_enter_to_continue()

    def probar_normalizacion_texto(self):
        """Prueba la normalización con texto de ejemplo"""
        print("\n🧪 PROBAR NORMALIZACIÓN")
        print("=" * 50)
        
        texto_ejemplo = input("Ingrese texto para probar normalización: ").strip()
        if not texto_ejemplo:
            texto_ejemplo = "El servidor PWCAUIMAPP12 tiene problemas con PWCAUIMAPP5 y APPSERVER01"
            print(f"📝 Usando ejemplo: {texto_ejemplo}")
        
        # Usar el motor de clasificación para probar
        from .classification_engine import ClassificationEngine
        engine = ClassificationEngine()
        
        print(f"\n📝 Texto original: {texto_ejemplo}")
        texto_normalizado = engine.preprocess_text(texto_ejemplo)
        print(f"🔄 Texto normalizado: {texto_normalizado}")
        
        display.press_enter_to_continue()

    def toggle_normalizacion(self):
        """Activa/desactiva la normalización de patrones"""
        estado_actual = self.get('variable_patterns.enabled', True)
        nuevo_estado = not estado_actual
        
        self.set('variable_patterns.enabled', nuevo_estado)
        
        print(f"✅ Normalización de patrones: {'✅ ACTIVADA' if nuevo_estado else '❌ DESACTIVADA'}")
        display.press_enter_to_continue()


    def deteccion_automatica_patrones(self):
        """Detecta automáticamente patrones en archivos Excel"""
        print("\n🤖 DETECCIÓN AUTOMÁTICA DE PATRONES")
        print("=" * 50)
        
        excel_path = input("Ruta del archivo Excel para analizar (Enter para predeterminado): ").strip()
        if not excel_path:
            excel_path = "data/input/tickets_para_analizar.xlsx"
        
        try:
            import pandas as pd
            df = pd.read_excel(excel_path)
            
            # Combinar asuntos y descripciones
            textos = ' '.join(
                df['Asunto'].fillna('').astype(str) + ' ' + 
                df.get('Descripción', pd.Series('')).fillna('').astype(str)
            ).lower()
            
            # Buscar patrones (palabra + número)
            patrones_encontrados = re.findall(r'\b[a-z]{4,}[a-z]*\d{2,}\b', textos)
            
            # Contar frecuencia
            from collections import Counter
            contador = Counter(patrones_encontrados)
            
            print(f"\n🔍 Patrones encontrados (archivo: {excel_path}):")
            print("-" * 40)
            
            patrones_sugeridos = []
            for patron, frecuencia in contador.most_common(15):
                if frecuencia >= 3:  # Mínimo 3 apariciones
                    base_patron = re.sub(r'\d+', '\\\\d+', patron)
                    print(f"   • {patron} (aparece {frecuencia} veces)")
                    print(f"     🎯 Patrón sugerido: {base_patron}")
                    print(f"     📝 Significado sugerido: servidor {patron.rstrip('0123456789')}")
                    patrones_sugeridos.append((base_patron, f"servidor {patron.rstrip('0123456789')}"))
                    print()
            
            if patrones_sugeridos:
                agregar = input("¿Agregar estos patrones automáticamente? (s/n): ").strip().lower()
                if agregar == 's':
                    for patron, significado in patrones_sugeridos:
                        current_patterns = self.get('variable_patterns.custom_patterns', {})
                        current_patterns[patron] = significado
                        self.set('variable_patterns.custom_patterns', current_patterns)
                    
                    print(f"✅ {len(patrones_sugeridos)} patrones agregados automáticamente")
            else:
                print("🤷 No se encontraron patrones significativos")
                
        except Exception as e:
            print(f"❌ Error en detección automática: {e}")
        
        display.press_enter_to_continue()
    
    def _cargar_configuracion_personalizada(self):
        """Carga configuración personalizada si existe"""
        try:
            # Intentar cargar desde classification_config.json
            import os
            import json
            config_path = "data/classification/classification_config.json"
            
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                
                # Actualizar con configuración personalizada
                if 'variable_patterns' in user_config:
                    self.config['variable_patterns'].update(user_config['variable_patterns'])
                    
        except Exception as e:
            display.show_message(f"⚠️  No se pudo cargar configuración personalizada: {e}", "warning")
    
    # 🆕 MÉTODO PARA OBTENER CONFIGURACIÓN (COMPATIBLE)
    def get(self, key, default=None):
        """Obtener valor de configuración usando dot notation (compatible con ClassificationConfigManager)"""
        keys = key.split('.')
        current = self.config
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        return current

    # 🆕 MÉTODO PARA GUARDAR CONFIGURACIÓN (COMPATIBLE)
    def set(self, key, value):
        """Establecer valor de configuración usando dot notation"""
        keys = key.split('.')
        current = self.config
        
        # Navegar hasta el penúltimo nivel
        for k in keys[:-1]:
            if k not in current or not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]
        
        # Establecer el valor final
        current[keys[-1]] = value
        self._guardar_configuracion_personalizada()

    def _guardar_configuracion_personalizada(self):
        """Guarda la configuración personalizada"""
        try:
            import os
            import json
            config_path = "data/classification/classification_config.json"
            
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            # Guardar solo la parte de variable_patterns para no sobreescribir otra configuración
            existing_config = {}
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    existing_config = json.load(f)
            
            # Actualizar solo variable_patterns
            existing_config['variable_patterns'] = self.config['variable_patterns']
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(existing_config, f, indent=4, ensure_ascii=False)
                
        except Exception as e:
            display.show_message(f"❌ Error guardando configuración: {e}", "error")
    
    def modificar_patron_existente(self):
        """Modifica un patrón personalizado existente"""
        print("\n✏️  MODIFICAR PATRÓN EXISTENTE")
        print("=" * 50)
        
        custom_patterns = self.get('variable_patterns.custom_patterns', {})
        if not custom_patterns:
            print("🤷 No hay patrones personalizados para modificar")
            display.press_enter_to_continue()
            return
        
        # Mostrar patrones existentes
        print("Patrones personalizados actuales:")
        for i, (patron, significado) in enumerate(custom_patterns.items(), 1):
            print(f"   {i}. {patron} -> '{significado}'")
        
        try:
            seleccion = int(input("\n🔢 Número del patrón a modificar: ").strip())
            if seleccion < 1 or seleccion > len(custom_patterns):
                print("❌ Número inválido")
                return
            
            patron_actual = list(custom_patterns.keys())[seleccion-1]
            significado_actual = custom_patterns[patron_actual]
            
            print(f"\n📝 Patrón actual: {patron_actual}")
            print(f"🎯 Significado actual: {significado_actual}")
            
            nuevo_patron = input(f"\n🔍 Nuevo patrón (Enter para mantener actual): ").strip()
            nuevo_significado = input(f"🎯 Nuevo significado (Enter para mantener actual): ").strip()
            
            # Si no se ingresa nada, mantener el valor actual
            if not nuevo_patron:
                nuevo_patron = patron_actual
            if not nuevo_significado:
                nuevo_significado = significado_actual
            
            # Validar el nuevo patrón
            try:
                re.compile(nuevo_patron)
            except re.error as e:
                print(f"❌ Error en el patrón regex: {e}")
                display.press_enter_to_continue()
                return
            
            # Si el patrón cambió, eliminar el antiguo y agregar el nuevo
            if nuevo_patron != patron_actual:
                del custom_patterns[patron_actual]
            
            custom_patterns[nuevo_patron] = nuevo_significado
            self.set('variable_patterns.custom_patterns', custom_patterns)
            
            print("✅ Patrón modificado exitosamente")
            
        except ValueError:
            print("❌ Debe ingresar un número válido")
        except Exception as e:
            print(f"❌ Error modificando patrón: {e}")
        
        display.press_enter_to_continue()

    def eliminar_patron(self):
        """Elimina un patrón personalizado"""
        print("\n🗑️  ELIMINAR PATRÓN PERSONALIZADO")
        print("=" * 50)
        
        custom_patterns = self.get('variable_patterns.custom_patterns', {})
        if not custom_patterns:
            print("🤷 No hay patrones personalizados para eliminar")
            display.press_enter_to_continue()
            return
        
        # Mostrar patrones existentes
        print("Patrones personalizados actuales:")
        for i, (patron, significado) in enumerate(custom_patterns.items(), 1):
            print(f"   {i}. {patron} -> '{significado}'")
        
        try:
            seleccion = int(input("\n🔢 Número del patrón a eliminar: ").strip())
            if seleccion < 1 or seleccion > len(custom_patterns):
                print("❌ Número inválido")
                return
            
            patron_a_eliminar = list(custom_patterns.keys())[seleccion-1]
            
            confirmar = input(f"¿Está seguro de eliminar el patrón '{patron_a_eliminar}'? (s/n): ").strip().lower()
            if confirmar == 's':
                del custom_patterns[patron_a_eliminar]
                self.set('variable_patterns.custom_patterns', custom_patterns)
                print("✅ Patrón eliminado exitosamente")
            else:
                print("❌ Eliminación cancelada")
                
        except ValueError:
            print("❌ Debe ingresar un número válido")
        except Exception as e:
            print(f"❌ Error eliminando patrón: {e}")
        
        display.press_enter_to_continue()