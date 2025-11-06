#!/usr/bin/env python3
# core/main.py
import argparse
import sys
import asyncio
from datetime import datetime
from typing import Dict, List, Any
import json

from core.config_manager import ConfigManager
from core.plugin_system import PluginSystem
from core.security import SecurityManager
from modules.phone_intel import PhoneIntel
from modules.email_intel import EmailIntel
from modules.social.instagram import InstagramIntel
from modules.social.twitter import TwitterIntel
from modules.social.telegram import TelegramIntel
from modules.web.shodan_intel import ShodanIntel
from modules.web.darkweb import DarkWebSearch
from modules.blockchain.bitcoin import BitcoinAnalyzer
from modules.ai.analyzer import AIAnalyzer
from utils.visualizer import GraphVisualizer
from utils.exporter import ReportExporter
from utils.logger import Logger

class OSINTFramework:
    def __init__(self):
        self.config = ConfigManager()
        self.plugins = PluginSystem()
        self.security = SecurityManager()
        self.logger = Logger()
        
        # Chargement des modules
        self.modules = self._load_modules()
        self.ai_analyzer = AIAnalyzer()
        self.visualizer = GraphVisualizer()
        self.exporter = ReportExporter()
        
        # Résultats de l'investigation
        self.investigation_data = {}
        
    def _load_modules(self) -> Dict[str, Any]:
        """Charge tous les modules disponibles"""
        return {
            'phone': PhoneIntel(),
            'email': EmailIntel(),
            'instagram': InstagramIntel(),
            'twitter': TwitterIntel(),
            'telegram': TelegramIntel(),
            'shodan': ShodanIntel(),
            'darkweb': DarkWebSearch(),
            'bitcoin': BitcoinAnalyzer(),
        }
    
    async def investigate(self, target_type: str, target_value: str, 
                         depth: int = 2, options: Dict = None) -> Dict:
        """Lance une investigation complète"""
        
        investigation_id = f"inv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.logger.info(f"Starting investigation {investigation_id} for {target_type}: {target_value}")
        
        results = {
            'investigation_id': investigation_id,
            'target': {'type': target_type, 'value': target_value},
            'timestamp': datetime.now().isoformat(),
            'modules': {},
            'correlations': {},
            'risk_assessment': {},
            'timeline': []
        }
        
        # Investigation principale
        if target_type in self.modules:
            module_results = await self.modules[target_type].investigate(target_value, depth)
            results['modules'][target_type] = module_results
        
        # Recherche cross-platform
        if depth >= 2:
            await self._cross_platform_search(target_type, target_value, results)
        
        # Analyse IA
        if depth >= 3:
            results['ai_analysis'] = await self.ai_analyzer.analyze_investigation(results)
            results['risk_assessment'] = await self.ai_analyzer.risk_assessment(results)
        
        # Génération de rapports
        results['visualization'] = await self.visualizer.create_comprehensive_graph(results)
        
        self.investigation_data[investigation_id] = results
        return results
    
    async def _cross_platform_search(self, target_type: str, target_value: str, results: Dict):
        """Recherche cross-platform avancée"""
        cross_results = {}
        
        # Extraction des identifiants pour recherche cross-platform
        identifiers = self._extract_identifiers(results)
        
        for identifier_type, values in identifiers.items():
            for value in values[:5]:  # Limiter pour éviter la surcharge
                for module_name, module in self.modules.items():
                    if module_name != target_type:
                        try:
                            cross_result = await module.investigate(value, depth=1)
                            cross_results[f"{module_name}_{value}"] = cross_result
                        except Exception as e:
                            self.logger.warning(f"Cross-platform search failed for {module_name}: {e}")
        
        results['cross_platform'] = cross_results
        results['correlations'] = self._find_correlations(cross_results)
    
    def _extract_identifiers(self, results: Dict) -> Dict[str, List]:
        """Extrait les identifiants pour la recherche cross-platform"""
        identifiers = {
            'usernames': [],
            'emails': [],
            'phones': [],
            'domains': []
        }
        
        # Implémentation de l'extraction d'identifiants
        # ... code d'extraction ...
        
        return identifiers
    
    def _find_correlations(self, data: Dict) -> Dict:
        """Trouve des corrélations entre les données"""
        correlations = {}
        # Implémentation des algorithmes de corrélation
        return correlations

async def main():
    parser = argparse.ArgumentParser(description='OSINT Framework Pro - Investigation Tool')
    
    # Arguments principaux
    parser.add_argument('-t', '--type', required=True,
                       choices=['phone', 'email', 'instagram', 'twitter', 
                               'telegram', 'bitcoin', 'domain', 'ip'],
                       help='Type of target')
    parser.add_argument('-v', '--value', required=True, help='Target value')
    parser.add_argument('-d', '--depth', type=int, default=2, choices=[1, 2, 3],
                       help='Investigation depth (1: Basic, 2: Advanced, 3: Full)')
    
    # Options avancées
    parser.add_argument('--ai-analysis', action='store_true', help='Enable AI analysis')
    parser.add_argument('--dark-web', action='store_true', help='Include dark web search')
    parser.add_argument('--real-time', action='store_true', help='Real-time monitoring')
    parser.add_argument('--anonymize', action='store_true', help='Use Tor and proxies')
    
    # Export
    parser.add_argument('--export', nargs='+', choices=['json', 'pdf', 'html', 'csv'],
                       help='Export formats')
    parser.add_argument('--visualize', action='store_true', help='Generate visualization')
    parser.add_argument('--report', action='store_true', help='Generate comprehensive report')
    
    # Mode
    parser.add_argument('--interactive', action='store_true', help='Interactive mode')
    parser.add_argument('--web-ui', action='store_true', help='Start web interface')
    parser.add_argument('--api', action='store_true', help='Start REST API')
    
    args = parser.parse_args()
    
    # Initialisation du framework
    framework = OSINTFramework()
    
    if args.web_ui:
        # Lancer l'interface web
        from web.app import create_app
        app = create_app(framework)
        app.run(host='0.0.0.0', port=5000, debug=False)
    
    elif args.api:
        # Lancer l'API REST
        from web.api import create_api
        api = create_api(framework)
        api.run(host='0.0.0.0', port=8080, debug=False)
    
    elif args.interactive:
        # Mode interactif
        await interactive_mode(framework)
    
    else:
        # Mode ligne de commande
        options = {
            'ai_analysis': args.ai_analysis,
            'dark_web': args.dark_web,
            'real_time': args.real_time,
            'anonymize': args.anonymize
        }
        
        results = await framework.investigate(args.type, args.value, args.depth, options)
        
        if args.export:
            for format in args.export:
                framework.exporter.export(results, format)
        
        if args.visualize:
            framework.visualizer.show_interactive_graph(results)
        
        if args.report:
            framework.exporter.generate_comprehensive_report(results)

async def interactive_mode(framework):
    """Mode interactif avancé"""
    print("🕵️ OSINT Framework Pro - Mode Interactif")
    print("=" * 50)
    
    while True:
        print("\nOptions disponibles:")
        print("1. Investigation rapide")
        print("2. Investigation approfondie")
        print("3. Monitoring temps réel")
        print("4. Génération de rapports")
        print("5. Visualisation des données")
        print("6. Quitter")
        
        choice = input("\nChoisissez une option (1-6): ").strip()
        
        if choice == '1':
            await quick_investigation(framework)
        elif choice == '2':
            await deep_investigation(framework)
        elif choice == '3':
            await real_time_monitoring(framework)
        elif choice == '4':
            await report_generation(framework)
        elif choice == '5':
            await data_visualization(framework)
        elif choice == '6':
            break
        else:
            print("Option invalide!")

if __name__ == "__main__":
    asyncio.run(main())
