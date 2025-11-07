
"""
Module d'exportation des données
Gère l'export des résultats d'analyse dans différents formats
"""

import json
import csv
import yaml
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
from datetime import datetime
import os
import pandas as pd
from pathlib import Path

from utils.logger import Logger
from core.security import sanitize_filename

class DataExporter:
    """
    Classe principale pour l'exportation des données OSINT
    """
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.logger = Logger(__name__)
        self.export_dir = self._get_export_directory()
        self._ensure_export_directories()
    
    def _get_export_directory(self) -> Path:
        """
        Détermine le répertoire d'exportation
        
        Returns:
            Chemin du répertoire d'export
        """
        try:
            settings = self.config.get('settings', {})
            export_path = settings.get('export_directory', 'data/exports')
            
            # Création du chemin absolu
            export_dir = Path(export_path)
            if not export_dir.is_absolute():
                # Relatif au répertoire du projet
                project_root = Path(__file__).parent.parent
                export_dir = project_root / export_dir
            
            return export_dir
            
        except Exception as e:
            self.logger.error(f"Erreur configuration répertoire export: {str(e)}")
            # Fallback vers le répertoire par défaut
            return Path('data/exports')
    
    def _ensure_export_directories(self):
        """Crée les répertoires d'export s'ils n'existent pas"""
        try:
            self.export_dir.mkdir(parents=True, exist_ok=True)
            
            # Sous-répertoires par format
            formats = ['json', 'csv', 'xml', 'yaml', 'pdf', 'xlsx']
            for format_dir in formats:
                (self.export_dir / format_dir).mkdir(exist_ok=True)
                
            self.logger.info(f"Répertoire d'export configuré: {self.export_dir}")
            
        except Exception as e:
            self.logger.error(f"Erreur création répertoires export: {str(e)}")
    
    def export_json(self, data: Any, filename: str, 
                   timestamp: bool = True, pretty: bool = True) -> Dict[str, Any]:
        """
        Exporte les données au format JSON
        
        Args:
            data: Données à exporter
            filename: Nom du fichier
            timestamp: Ajouter un timestamp au nom
            pretty: Formatage lisible
            
        Returns:
            Dict avec le résultat de l'export
        """
        try:
            filename = sanitize_filename(filename)
            if timestamp:
                timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{filename}_{timestamp_str}"
            
            filepath = self.export_dir / 'json' / f"{filename}.json"
            
            with open(filepath, 'w', encoding='utf-8') as f:
                if pretty:
                    json.dump(data, f, indent=2, ensure_ascii=False, default=str)
                else:
                    json.dump(data, f, ensure_ascii=False, default=str)
            
            self.logger.info(f"Export JSON réussi: {filepath}")
            
            return {
                'success': True,
                'format': 'json',
                'filepath': str(filepath),
                'filename': filepath.name,
                'size': filepath.stat().st_size,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Erreur export JSON: {str(e)}"
            self.logger.error(error_msg)
            return {'success': False, 'error': error_msg}
    
    def export_csv(self, data: Any, filename: str, 
                  timestamp: bool = True, delimiter: str = ',') -> Dict[str, Any]:
        """
        Exporte les données au format CSV
        
        Args:
            data: Données à exporter
            filename: Nom du fichier
            timestamp: Ajouter un timestamp au nom
            delimiter: Séparateur de champs
            
        Returns:
            Dict avec le résultat de l'export
        """
        try:
            filename = sanitize_filename(filename)
            if timestamp:
                timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{filename}_{timestamp_str}"
            
            filepath = self.export_dir / 'csv' / f"{filename}.csv"
            
            # Conversion des données en format tabulaire
            flattened_data = self._flatten_data_for_csv(data)
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                if flattened_data:
                    writer = csv.DictWriter(f, fieldnames=flattened_data[0].keys(), delimiter=delimiter)
                    writer.writeheader()
                    writer.writerows(flattened_data)
                else:
                    # Cas où les données sont simples
                    writer = csv.writer(f, delimiter=delimiter)
                    if isinstance(data, list):
                        for item in data:
                            writer.writerow([item] if not isinstance(item, list) else item)
                    else:
                        writer.writerow([str(data)])
            
            self.logger.info(f"Export CSV réussi: {filepath}")
            
            return {
                'success': True,
                'format': 'csv',
                'filepath': str(filepath),
                'filename': filepath.name,
                'size': filepath.stat().st_size,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Erreur export CSV: {str(e)}"
            self.logger.error(error_msg)
            return {'success': False, 'error': error_msg}
    
    def _flatten_data_for_csv(self, data: Any, parent_key: str = '', sep: str = '_') -> List[Dict[str, Any]]:
        """
        Aplatit les données complexes pour le format CSV
        
        Args:
            data: Données à aplatir
            parent_key: Clé parente pour les champs imbriqués
            sep: Séparateur pour les clés imbriquées
            
        Returns:
            Liste de dictionnaires aplatis
        """
        items = []
        
        if isinstance(data, list):
            for i, item in enumerate(data):
                items.extend(self._flatten_data_for_csv(item, f"{parent_key}{sep}{i}" if parent_key else str(i), sep))
        elif isinstance(data, dict):
            flattened = {}
            for k, v in data.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                if isinstance(v, (dict, list)):
                    flattened.update(self._flatten_data_for_csv(v, new_key, sep))
                else:
                    flattened[new_key] = v
            items.append(flattened)
        else:
            items.append({parent_key: data} if parent_key else {'value': data})
        
        return items
    
    def export_xml(self, data: Any, filename: str, 
                  timestamp: bool = True, root_name: str = 'osint_data') -> Dict[str, Any]:
        """
        Exporte les données au format XML
        
        Args:
            data: Données à exporter
            filename: Nom du fichier
            timestamp: Ajouter un timestamp au nom
            root_name: Nom de l'élément racine
            
        Returns:
            Dict avec le résultat de l'export
        """
        try:
            filename = sanitize_filename(filename)
            if timestamp:
                timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{filename}_{timestamp_str}"
            
            filepath = self.export_dir / 'xml' / f"{filename}.xml"
            
            # Création de l'élément racine
            root = ET.Element(root_name)
            root.set('export_timestamp', datetime.now().isoformat())
            root.set('version', '1.0')
            
            # Conversion des données en XML
            self._dict_to_xml(data, root)
            
            # Création de l'arbre XML
            tree = ET.ElementTree(root)
            
            # Écriture avec indentation
            self._pretty_xml(root)
            tree.write(filepath, encoding='utf-8', xml_declaration=True)
            
            self.logger.info(f"Export XML réussi: {filepath}")
            
            return {
                'success': True,
                'format': 'xml',
                'filepath': str(filepath),
                'filename': filepath.name,
                'size': filepath.stat().st_size,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Erreur export XML: {str(e)}"
            self.logger.error(error_msg)
            return {'success': False, 'error': error_msg}
    
    def _dict_to_xml(self, data: Any, parent_element: ET.Element):
        """
        Convertit un dictionnaire en structure XML
        
        Args:
            data: Données à convertir
            parent_element: Élément parent XML
        """
        if isinstance(data, dict):
            for key, value in data.items():
                # Nettoyage du nom de la clé pour XML
                clean_key = self._clean_xml_key(key)
                child = ET.SubElement(parent_element, clean_key)
                self._dict_to_xml(value, child)
        elif isinstance(data, list):
            for item in data:
                child = ET.SubElement(parent_element, 'item')
                self._dict_to_xml(item, child)
        else:
            parent_element.text = str(data)
    
    def _clean_xml_key(self, key: str) -> str:
        """
        Nettoie une clé pour être valide en XML
        
        Args:
            key: Clé à nettoyer
            
        Returns:
            Clé nettoyée
        """
        # Remplace les caractères invalides
        clean_key = re.sub(r'[^a-zA-Z0-9_]', '_', str(key))
        # S'assure que ça ne commence pas par un chiffre
        if clean_key and clean_key[0].isdigit():
            clean_key = 'key_' + clean_key
        return clean_key
    
    def _pretty_xml(self, elem: ET.Element, level: int = 0):
        """
        Formate l'XML avec une indentation lisible
        
        Args:
            elem: Élément XML à formater
            level: Niveau d'indentation
        """
        i = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self._pretty_xml(elem, level + 1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i
    
    def export_yaml(self, data: Any, filename: str, 
                   timestamp: bool = True) -> Dict[str, Any]:
        """
        Exporte les données au format YAML
        
        Args:
            data: Données à exporter
            filename: Nom du fichier
            timestamp: Ajouter un timestamp au nom
            
        Returns:
            Dict avec le résultat de l'export
        """
        try:
            filename = sanitize_filename(filename)
            if timestamp:
                timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{filename}_{timestamp_str}"
            
            filepath = self.export_dir / 'yaml' / f"{filename}.yaml"
            
            with open(filepath, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            
            self.logger.info(f"Export YAML réussi: {filepath}")
            
            return {
                'success': True,
                'format': 'yaml',
                'filepath': str(filepath),
                'filename': filepath.name,
                'size': filepath.stat().st_size,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Erreur export YAML: {str(e)}"
            self.logger.error(error_msg)
            return {'success': False, 'error': error_msg}
    
    def export_excel(self, data: Any, filename: str, 
                    timestamp: bool = True, sheet_name: str = 'OSINT_Data') -> Dict[str, Any]:
        """
        Exporte les données au format Excel
        
        Args:
            data: Données à exporter
            filename: Nom du fichier
            timestamp: Ajouter un timestamp au nom
            sheet_name: Nom de la feuille Excel
            
        Returns:
            Dict avec le résultat de l'export
        """
        try:
            filename = sanitize_filename(filename)
            if timestamp:
                timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{filename}_{timestamp_str}"
            
            filepath = self.export_dir / 'xlsx' / f"{filename}.xlsx"
            
            # Conversion des données pour Excel
            if isinstance(data, list):
                # Données déjà tabulaires
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                # Données dictionnaire simple
                df = pd.DataFrame([data])
            else:
                # Autres types
                df = pd.DataFrame({'value': [data]})
            
            # Écriture Excel
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # Ajustement automatique des colonnes
                worksheet = writer.sheets[sheet_name]
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            
            self.logger.info(f"Export Excel réussi: {filepath}")
            
            return {
                'success': True,
                'format': 'excel',
                'filepath': str(filepath),
                'filename': filepath.name,
                'size': filepath.stat().st_size,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Erreur export Excel: {str(e)}"
            self.logger.error(error_msg)
            return {'success': False, 'error': error_msg}
    
    def export_report(self, data: Any, filename: str, 
                     formats: List[str] = None) -> Dict[str, Any]:
        """
        Exporte les données dans multiples formats
        
        Args:
            data: Données à exporter
            filename: Nom de base du fichier
            formats: Liste des formats d'export
            
        Returns:
            Dict avec les résultats de tous les exports
        """
        if formats is None:
            formats = ['json', 'csv', 'xml', 'yaml', 'excel']
        
        results = {}
        
        for format_type in formats:
            if format_type == 'json':
                results['json'] = self.export_json(data, filename)
            elif format_type == 'csv':
                results['csv'] = self.export_csv(data, filename)
            elif format_type == 'xml':
                results['xml'] = self.export_xml(data, filename)
            elif format_type == 'yaml':
                results['yaml'] = self.export_yaml(data, filename)
            elif format_type == 'excel':
                results['excel'] = self.export_excel(data, filename)
        
        # Résumé de l'export
        successful = [fmt for fmt, result in results.items() if result.get('success')]
        failed = [fmt for fmt, result in results.items() if not result.get('success')]
        
        summary = {
            'total_formats': len(formats),
            'successful_exports': successful,
            'failed_exports': failed,
            'results': results
        }
        
        self.logger.info(f"Export multi-format: {len(successful)}/{len(formats)} réussis")
        
        return summary
    
    def list_exports(self, format_type: str = None, days: int = None) -> List[Dict[str, Any]]:
        """
        Liste les fichiers d'export disponibles
        
        Args:
            format_type: Filtre par format
            days: Filtre par âge (derniers jours)
            
        Returns:
            Liste des fichiers d'export
        """
        try:
            exports = []
            
            if format_type:
                search_dir = self.export_dir / format_type
                if search_dir.exists():
                    directories = [search_dir]
                else:
                    directories = []
            else:
                directories = [self.export_dir / fmt for fmt in ['json', 'csv', 'xml', 'yaml', 'xlsx']]
            
            for directory in directories:
                if directory.exists():
                    for file_path in directory.glob('*.*'):
                        file_info = {
                            'filename': file_path.name,
                            'filepath': str(file_path),
                            'format': directory.name,
                            'size': file_path.stat().st_size,
                            'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                            'age_days': (datetime.now() - datetime.fromtimestamp(file_path.stat().st_mtime)).days
                        }
                        
                        # Filtre par âge si spécifié
                        if days is None or file_info['age_days'] <= days:
                            exports.append(file_info)
            
            # Tri par date de modification (plus récent en premier)
            exports.sort(key=lambda x: x['modified'], reverse=True)
            
            return exports
            
        except Exception as e:
            self.logger.error(f"Erreur liste exports: {str(e)}")
            return []
    
    def cleanup_exports(self, older_than_days: int = 30, format_type: str = None) -> Dict[str, Any]:
        """
        Nettoie les anciens fichiers d'export
        
        Args:
            older_than_days: Supprime les fichiers plus vieux que X jours
            format_type: Filtre par format
            
        Returns:
            Résultat du nettoyage
        """
        try:
            exports = self.list_exports(format_type=format_type)
            deleted = []
            errors = []
            
            for export in exports:
                if export['age_days'] > older_than_days:
                    try:
                        file_path = Path(export['filepath'])
                        file_path.unlink()
                        deleted.append(export['filename'])
                    except Exception as e:
                        errors.append(f"{export['filename']}: {str(e)}")
            
            result = {
                'deleted_count': len(deleted),
                'deleted_files': deleted,
                'error_count': len(errors),
                'errors': errors
            }
            
            self.logger.info(f"Nettoyage exports: {len(deleted)} fichiers supprimés")
            
            return result
            
        except Exception as e:
            error_msg = f"Erreur nettoyage exports: {str(e)}"
            self.logger.error(error_msg)
            return {'error': error_msg}

# Fonctions utilitaires pour un usage simplifié
def export_data(data: Any, filename: str, format_type: str = 'json', 
               config_manager = None) -> Dict[str, Any]:
    """
    Fonction simplifiée pour l'export de données
    
    Args:
        data: Données à exporter
        filename: Nom du fichier
        format_type: Format d'export
        config_manager: Gestionnaire de configuration
        
    Returns:
        Résultat de l'export
    """
    if config_manager is None:
        from core.config_manager import ConfigManager
        config_manager = ConfigManager()
    
    exporter = DataExporter(config_manager)
    
    if format_type == 'json':
        return exporter.export_json(data, filename)
    elif format_type == 'csv':
        return exporter.export_csv(data, filename)
    elif format_type == 'xml':
        return exporter.export_xml(data, filename)
    elif format_type == 'yaml':
        return exporter.export_yaml(data, filename)
    elif format_type == 'excel':
        return exporter.export_excel(data, filename)
    else:
        return {'success': False, 'error': f"Format non supporté: {format_type}"}

def main():
    """Fonction principale pour test du module"""
    from core.config_manager import ConfigManager
    
    config = ConfigManager()
    exporter = DataExporter(config)
    
    print("📤 Module d'Exportation de Données")
    print("=" * 40)
    
    # Données de test
    test_data = {
        'email_analysis': {
            'email': 'test@example.com',
            'valid': True,
            'breaches': 2,
            'domain': 'example.com'
        },
        'timestamp': datetime.now().isoformat()
    }
    
    while True:
        print("\nOptions:")
        print("1. Exporter JSON")
        print("2. Exporter CSV")
        print("3. Exporter XML")
        print("4. Exporter YAML")
        print("5. Exporter Excel")
        print("6. Exporter multi-format")
        print("7. Lister les exports")
        print("8. Nettoyer les anciens exports")
        print("9. Quitter")
        
        choice = input("\nChoisissez une option (1-9): ").strip()
        
        if choice == '1':
            result = exporter.export_json(test_data, 'test_export')
            print(f"\nExport JSON: {result}")
            
        elif choice == '2':
            result = exporter.export_csv(test_data, 'test_export')
            print(f"\nExport CSV: {result}")
            
        elif choice == '3':
            result = exporter.export_xml(test_data, 'test_export')
            print(f"\nExport XML: {result}")
            
        elif choice == '4':
            result = exporter.export_yaml(test_data, 'test_export')
            print(f"\nExport YAML: {result}")
            
        elif choice == '5':
            result = exporter.export_excel(test_data, 'test_export')
            print(f"\nExport Excel: {result}")
            
        elif choice == '6':
            result = exporter.export_report(test_data, 'test_comprehensive', ['json', 'csv', 'xml'])
            print(f"\nExport multi-format: {result}")
            
        elif choice == '7':
            exports = exporter.list_exports()
            print(f"\nExports disponibles ({len(exports)}):")
            for export in exports[:5]:  # Affiche les 5 premiers
                print(f"  - {export['filename']} ({export['format']}, {export['size']} bytes)")
            
        elif choice == '8':
            result = exporter.cleanup_exports(older_than_days=1)  # Supprime les fichiers de plus d'1 jour (pour le test)
            print(f"\nNettoyage: {result}")
            
        elif choice == '9':
            break
        else:
            print("Option invalide")

if __name__ == "__main__":
    main()
