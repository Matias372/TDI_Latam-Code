import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

class TransactionLogger:
    """Manejo de logging transaccional para habilitar rollback futuro"""
    
    def __init__(self, base_logger):
        self.base_logger = base_logger
        self.transactions_dir = None
        self._setup_transactions_dir()
    
    def _setup_transactions_dir(self):
        """Configurar directorio para transacciones"""
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        
        self.transactions_dir = os.path.join(base_dir, "data", "transactions")
        os.makedirs(self.transactions_dir, exist_ok=True)
    
    def start_transaction(self, process_type: str, description: str, metadata: dict = None) -> str:
        """🎯 INICIAR TRANSACCIÓN: Para tracking de cambios reversibles"""
        transaction_id = f"{process_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        transaction_data = {
            'transaction_id': transaction_id,
            'process_type': process_type,
            'timestamp': datetime.now().isoformat(),
            'description': description,
            'metadata': metadata or {},
            'status': 'STARTED',
            'changes': [],
            'rollback_data': {}  # Datos específicos para rollback
        }
        
        self.base_logger.log_info(f"TRANSACTION_START: {transaction_id} - {description}")
        self._save_transaction(transaction_id, transaction_data)
        
        return transaction_id
    
    def log_transaction_change(self, transaction_id: str, change_data: dict):
        """🎯 REGISTRAR CAMBIO: Cada modificación que pueda necesitar rollback"""
        change_data['change_timestamp'] = datetime.now().isoformat()
        change_data['change_id'] = f"CH_{datetime.now().strftime('%H%M%S%f')}"
        
        # Estructura estándar para cambios
        standardized_change = {
            'system': change_data.get('system', 'UNKNOWN'),
            'operation': change_data.get('operation', 'UNKNOWN'),
            'ticket_id': change_data.get('ticket_id'),
            'field': change_data.get('field'),
            'old_value': change_data.get('old_value'),
            'new_value': change_data.get('new_value'),
            'rollback_data': change_data.get('rollback_data', {}),
            'status': 'PENDING'
        }
        
        self.base_logger.log_debug(f"TRANSACTION_CHANGE: {transaction_id} - {standardized_change}")
        self._update_transaction(transaction_id, 'changes', standardized_change, append=True)
    
    def confirm_transaction_change(self, transaction_id: str, change_id: str, success: bool, error_msg: str = None):
        """🎯 CONFIRMAR CAMBIO: Marcar cambio como exitoso o fallido"""
        update_data = {
            'status': 'SUCCESS' if success else 'FAILED',
            'completion_timestamp': datetime.now().isoformat()
        }
        
        if error_msg:
            update_data['error'] = error_msg
        
        self._update_specific_change(transaction_id, change_id, update_data)
    
    def complete_transaction(self, transaction_id: str, summary: dict):
        """🎯 COMPLETAR TRANSACCIÓN: Con resumen final"""
        complete_data = {
            'completion_timestamp': datetime.now().isoformat(),
            'status': 'COMPLETED',
            'summary': summary
        }
        
        self.base_logger.log_info(f"TRANSACTION_COMPLETE: {transaction_id} - {summary}")
        self._update_transaction(transaction_id, 'completion', complete_data)
    
    def fail_transaction(self, transaction_id: str, error_message: str):
        """🎯 MARCAR TRANSACCIÓN COMO FALLIDA"""
        fail_data = {
            'completion_timestamp': datetime.now().isoformat(),
            'status': 'FAILED',
            'error': error_message
        }
        
        self.base_logger.log_error(f"TRANSACTION_FAILED: {transaction_id} - {error_message}")
        self._update_transaction(transaction_id, 'failure', fail_data)
    
    def _save_transaction(self, transaction_id: str, transaction_data: dict):
        """Guardar transacción en archivo JSON"""
        try:
            # Organizar por tipo de proceso
            process_type = transaction_data.get('process_type', 'GENERAL')
            process_dir = os.path.join(self.transactions_dir, process_type)
            os.makedirs(process_dir, exist_ok=True)
            
            transaction_file = os.path.join(process_dir, f"{transaction_id}.json")
            
            with open(transaction_file, 'w', encoding='utf-8') as f:
                json.dump(transaction_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.base_logger.log_error(f"Error guardando transacción {transaction_id}: {e}")
    
    def _update_transaction(self, transaction_id: str, key: str, value, append: bool = False):
        """Actualizar transacción existente"""
        try:
            transaction_file = self._find_transaction_file(transaction_id)
            if not transaction_file:
                return
            
            with open(transaction_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            
            if append and key in existing_data and isinstance(existing_data[key], list):
                existing_data[key].append(value)
            else:
                existing_data[key] = value
                
            with open(transaction_file, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.base_logger.log_error(f"Error actualizando transacción {transaction_id}: {e}")
    
    def _update_specific_change(self, transaction_id: str, change_id: str, update_data: dict):
        """Actualizar un cambio específico en la transacción"""
        try:
            transaction_file = self._find_transaction_file(transaction_id)
            if not transaction_file:
                return
            
            with open(transaction_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            
            # Buscar y actualizar el cambio específico
            if 'changes' in existing_data:
                for change in existing_data['changes']:
                    if change.get('change_id') == change_id:
                        change.update(update_data)
                        break
                
                with open(transaction_file, 'w', encoding='utf-8') as f:
                    json.dump(existing_data, f, indent=2, ensure_ascii=False)
                    
        except Exception as e:
            self.base_logger.log_error(f"Error actualizando cambio específico: {e}")
    
    def _find_transaction_file(self, transaction_id: str) -> Optional[str]:
        """Encontrar archivo de transacción por ID"""
        for root, dirs, files in os.walk(self.transactions_dir):
            for file in files:
                if file.startswith(transaction_id) and file.endswith('.json'):
                    return os.path.join(root, file)
        return None
    
    # 🎯 MÉTODOS PARA FUTURA IMPLEMENTACIÓN DE ROLLBACK
    def get_transaction(self, transaction_id: str) -> Optional[Dict]:
        """Obtener datos de una transacción para rollback"""
        try:
            transaction_file = self._find_transaction_file(transaction_id)
            if transaction_file and os.path.exists(transaction_file):
                with open(transaction_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.base_logger.log_error(f"Error obteniendo transacción {transaction_id}: {e}")
        return None
    
    def list_transactions(self, process_type: str = None, status: str = None) -> List[Dict]:
        """Listar transacciones para interfaz de rollback"""
        transactions = []
        try:
            search_dir = self.transactions_dir
            if process_type:
                search_dir = os.path.join(self.transactions_dir, process_type)
            
            if os.path.exists(search_dir):
                for root, dirs, files in os.walk(search_dir):
                    for file in files:
                        if file.endswith('.json'):
                            file_path = os.path.join(root, file)
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    transaction_data = json.load(f)
                                
                                if status and transaction_data.get('status') != status:
                                    continue
                                
                                transactions.append(transaction_data)
                            except:
                                continue
        except Exception as e:
            self.base_logger.log_error(f"Error listando transacciones: {e}")
        
        return sorted(transactions, key=lambda x: x.get('timestamp', ''), reverse=True)