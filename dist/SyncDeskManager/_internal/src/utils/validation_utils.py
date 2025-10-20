class ValidationUtils:
    @staticmethod
    def validar_emails(emails):
        """Validar y corregir emails"""
        emails_corregidos = []
        for mail in emails:
            if "@" not in mail:
                print(f"❌ Email inválido detectado: {mail}")
                nuevo_mail = input(f"Ingrese un correo válido para reemplazar '{mail}': ").strip()
                emails_corregidos.append(nuevo_mail)
            else:
                emails_corregidos.append(mail)
        return emails_corregidos

    @staticmethod
    def confirmar_accion(mensaje):
        """Pedir confirmación al usuario"""
        respuesta = input(f"{mensaje} (S/N): ").strip().upper()
        return respuesta == "S"

    @staticmethod
    def seleccionar_modo_ejecucion():
        """Seleccionar modo manual o automático"""
        print("\n=== MODO DE EJECUCIÓN ===")
        print("1. Manual (confirmar cada envío)")
        print("2. Automático (enviar directo)")
        
        try:
            modo = input("Seleccione el modo (1/2): ").strip()
            return modo == "2"  # True para automático, False para manual
        except:
            print("❌ Opción inválida. Se usará modo manual.")
            return False