"""
Module de visualisation des données OSINT
Génération de graphiques, rapports et tableaux de bord
"""

import json
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import networkx as nx
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from wordcloud import WordCloud
import base64
from io import BytesIO

from utils.logger import Logger
from utils.helpers import human_readable_size, format_timestamp

class DataVisualizer:
    """
    Classe principale pour la visualisation des données OSINT
    """
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.logger = Logger(__name__)
        self.export_dir = self._get_export_directory()
        self._ensure_directories()
        self._setup_styles()
    
    def _get_export_directory(self) -> Path:
        """
        Détermine le répertoire d'exportation des visualisations
        
        Returns:
            Chemin du répertoire d'export
        """
        try:
            settings = self.config.get('settings', {})
            export_path = settings.get('visualization_directory', 'data/visualizations')
            
            export_dir = Path(export_path)
            if not export_dir.is_absolute():
                project_root = Path(__file__).parent.parent
                export_dir = project_root / export_dir
            
            return export_dir
            
        except Exception as e:
            self.logger.error(f"Erreur configuration répertoire visualisation: {str(e)}")
            return Path('data/visualizations')
    
    def _ensure_directories(self):
        """Crée les répertoires d'export s'ils n'existent pas"""
        try:
            self.export_dir.mkdir(parents=True, exist_ok=True)
            
            # Sous-répertoires par type
            formats = ['graphs', 'reports', 'network', 'timeline', 'wordclouds']
            for format_dir in formats:
                (self.export_dir / format_dir).mkdir(exist_ok=True)
                
            self.logger.info(f"Répertoire de visualisation configuré: {self.export_dir}")
            
        except Exception as e:
            self.logger.error(f"Erreur création répertoires visualisation: {str(e)}")
    
    def _setup_styles(self):
        """Configure les styles pour les visualisations"""
        # Style matplotlib
        plt.style.use('seaborn-v0_8')
        self.colors = sns.color_palette("husl", 8)
        
        # Style plotly
        self.plotly_template = "plotly_white"
    
    def create_network_graph(self, nodes: List[Dict], edges: List[Dict], 
                           filename: str = "network_graph") -> Dict[str, Any]:
        """
        Crée un graphique de réseau pour les relations
        
        Args:
            nodes: Liste des nœuds avec propriétés
            edges: Liste des arêtes avec propriétés
            filename: Nom du fichier de sortie
            
        Returns:
            Résultat de la génération
        """
        try:
            self.logger.info(f"Création du graphique de réseau avec {len(nodes)} nœuds et {len(edges)} arêtes")
            
            # Création du graphe
            G = nx.Graph()
            
            # Ajout des nœuds
            for node in nodes:
                G.add_node(
                    node['id'],
                    **{k: v for k, v in node.items() if k != 'id'}
                )
            
            # Ajout des arêtes
            for edge in edges:
                G.add_edge(
                    edge['source'],
                    edge['target'],
                    **{k: v for k, v in edge.items() if k not in ['source', 'target']}
                )
            
            # Calcul des positions
            pos = nx.spring_layout(G, k=1, iterations=50)
            
            # Création de la figure
            fig, ax = plt.subplots(figsize=(16, 12))
            
            # Dessin des nœuds
            node_colors = []
            node_sizes = []
            
            for node_id in G.nodes():
                node_data = G.nodes[node_id]
                node_type = node_data.get('type', 'default')
                
                # Couleur par type
                if node_type == 'person':
                    node_colors.append(self.colors[0])
                    node_sizes.append(800)
                elif node_type == 'organization':
                    node_colors.append(self.colors[1])
                    node_sizes.append(1200)
                elif node_type == 'email':
                    node_colors.append(self.colors[2])
                    node_sizes.append(600)
                elif node_type == 'domain':
                    node_colors.append(self.colors[3])
                    node_sizes.append(1000)
                else:
                    node_colors.append(self.colors[4])
                    node_sizes.append(700)
            
            # Dessin du réseau
            nx.draw_networkx_nodes(G, pos, node_color=node_colors, 
                                 node_size=node_sizes, alpha=0.9, ax=ax)
            nx.draw_networkx_edges(G, pos, alpha=0.5, edge_color='gray', ax=ax)
            
            # Labels des nœuds
            labels = {node: G.nodes[node].get('label', node) for node in G.nodes()}
            nx.draw_networkx_labels(G, pos, labels, font_size=8, ax=ax)
            
            # Métadonnées du graphe
            ax.set_title(f"Réseau OSINT - {len(nodes)} entités, {len(edges)} relations", 
                        fontsize=16, pad=20)
            ax.axis('off')
            
            # Légende
            legend_elements = [
                plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=self.colors[0], 
                          markersize=10, label='Personnes'),
                plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=self.colors[1], 
                          markersize=10, label='Organisations'),
                plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=self.colors[2], 
                          markersize=10, label='Emails'),
                plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=self.colors[3], 
                          markersize=10, label='Domaines')
            ]
            ax.legend(handles=legend_elements, loc='upper left')
            
            # Sauvegarde
            filepath = self.export_dir / 'network' / f"{filename}.png"
            plt.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            
            # Statistiques du réseau
            stats = {
                'nodes_count': len(nodes),
                'edges_count': len(edges),
                'density': nx.density(G),
                'connected_components': nx.number_connected_components(G),
                'average_degree': sum(dict(G.degree()).values()) / len(G.nodes()) if G.nodes() else 0
            }
            
            self.logger.info(f"Graphique de réseau sauvegardé: {filepath}")
            
            return {
                'success': True,
                'filepath': str(filepath),
                'filename': filepath.name,
                'network_stats': stats,
                'format': 'png'
            }
            
        except Exception as e:
            error_msg = f"Erreur création graphique réseau: {str(e)}"
            self.logger.error(error_msg)
            return {'success': False, 'error': error_msg}
    
    def create_timeline_chart(self, events: List[Dict], filename: str = "timeline") -> Dict[str, Any]:
        """
        Crée un graphique de timeline pour les événements temporels
        
        Args:
            events: Liste des événements avec dates
            filename: Nom du fichier de sortie
            
        Returns:
            Résultat de la génération
        """
        try:
            self.logger.info(f"Création de la timeline avec {len(events)} événements")
            
            # Conversion des dates
            for event in events:
                if isinstance(event['date'], str):
                    event['date'] = datetime.fromisoformat(event['date'].replace('Z', '+00:00'))
            
            # Tri par date
            events.sort(key=lambda x: x['date'])
            
            # Création de la figure Plotly
            fig = go.Figure()
            
            # Catégories d'événements
            categories = list(set(event.get('category', 'default') for event in events))
            color_map = {cat: self.colors[i % len(self.colors)] for i, cat in enumerate(categories)}
            
            for event in events:
                category = event.get('category', 'default')
                fig.add_trace(go.Scatter(
                    x=[event['date']],
                    y=[event.get('y_position', 0)],
                    mode='markers+text',
                    marker=dict(
                        size=event.get('importance', 10),
                        color=f'rgb({int(color_map[category][0]*255)},'
                              f'{int(color_map[category][1]*255)},'
                              f'{int(color_map[category][2]*255)})'
                    ),
                    text=event['label'],
                    textposition="middle right",
                    name=category,
                    hovertemplate=(
                        f"<b>{event['label']}</b><br>"
                        f"Date: {event['date'].strftime('%d/%m/%Y')}<br>"
                        f"Catégorie: {category}<br>"
                        f"<extra></extra>"
                    )
                ))
            
            # Configuration de la figure
            fig.update_layout(
                title="Timeline des événements OSINT",
                xaxis_title="Date",
                yaxis=dict(showticklabels=False, showgrid=False),
                showlegend=True,
                template=self.plotly_template,
                height=600
            )
            
            # Sauvegarde
            filepath = self.export_dir / 'timeline' / f"{filename}.html"
            fig.write_html(str(filepath))
            
            self.logger.info(f"Timeline sauvegardée: {filepath}")
            
            return {
                'success': True,
                'filepath': str(filepath),
                'filename': filepath.name,
                'events_count': len(events),
                'format': 'html'
            }
            
        except Exception as e:
            error_msg = f"Erreur création timeline: {str(e)}"
            self.logger.error(error_msg)
            return {'success': False, 'error': error_msg}
    
    def create_risk_dashboard(self, risk_data: Dict[str, Any], filename: str = "risk_dashboard") -> Dict[str, Any]:
        """
        Crée un tableau de bord de risque
        
        Args:
            risk_data: Données de risque
            filename: Nom du fichier de sortie
            
        Returns:
            Résultat de la génération
        """
        try:
            self.logger.info("Création du tableau de bord de risque")
            
            # Création d'une figure avec subplots
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=[
                    'Distribution des niveaux de risque',
                    'Risque par catégorie',
                    'Évolution temporelle du risque',
                    'Top 10 des entités à risque'
                ],
                specs=[
                    [{"type": "pie"}, {"type": "bar"}],
                    [{"type": "scatter"}, {"type": "bar"}]
                ]
            )
            
            # Graphique 1: Distribution des risques (camembert)
            risk_levels = risk_data.get('risk_distribution', {})
            if risk_levels:
                fig.add_trace(
                    go.Pie(
                        labels=list(risk_levels.keys()),
                        values=list(risk_levels.values()),
                        name="Distribution risque"
                    ),
                    row=1, col=1
                )
            
            # Graphique 2: Risque par catégorie (barres)
            risk_by_category = risk_data.get('risk_by_category', {})
            if risk_by_category:
                categories = list(risk_by_category.keys())
                values = list(risk_by_category.values())
                
                fig.add_trace(
                    go.Bar(
                        x=categories,
                        y=values,
                        marker_color='indianred',
                        name="Risque par catégorie"
                    ),
                    row=1, col=2
                )
            
            # Graphique 3: Évolution temporelle
            risk_timeline = risk_data.get('risk_timeline', {})
            if risk_timeline:
                dates = list(risk_timeline.keys())
                risk_scores = list(risk_timeline.values())
                
                fig.add_trace(
                    go.Scatter(
                        x=dates,
                        y=risk_scores,
                        mode='lines+markers',
                        name="Évolution risque",
                        line=dict(color='red', width=3)
                    ),
                    row=2, col=1
                )
            
            # Graphique 4: Top 10 entités à risque
            top_risky = risk_data.get('top_risky_entities', [])
            if top_risky:
                entities = [item['entity'] for item in top_risky[:10]]
                scores = [item['risk_score'] for item in top_risky[:10]]
                
                fig.add_trace(
                    go.Bar(
                        x=scores,
                        y=entities,
                        orientation='h',
                        marker_color='coral',
                        name="Top entités à risque"
                    ),
                    row=2, col=2
                )
            
            # Configuration globale
            fig.update_layout(
                title_text="Tableau de bord d'analyse de risque OSINT",
                height=800,
                showlegend=False,
                template=self.plotly_template
            )
            
            # Sauvegarde
            filepath = self.export_dir / 'reports' / f"{filename}.html"
            fig.write_html(str(filepath))
            
            self.logger.info(f"Tableau de bord de risque sauvegardé: {filepath}")
            
            return {
                'success': True,
                'filepath': str(filepath),
                'filename': filepath.name,
                'format': 'html'
            }
            
        except Exception as e:
            error_msg = f"Erreur création tableau de bord risque: {str(e)}"
            self.logger.error(error_msg)
            return {'success': False, 'error': error_msg}
    
    def create_word_cloud(self, text_data: str, filename: str = "wordcloud") -> Dict[str, Any]:
        """
        Crée un nuage de mots à partir de texte
        
        Args:
            text_data: Texte à analyser
            filename: Nom du fichier de sortie
            
        Returns:
            Résultat de la génération
        """
        try:
            self.logger.info("Création du nuage de mots")
            
            # Génération du wordcloud
            wordcloud = WordCloud(
                width=1200,
                height=800,
                background_color='white',
                colormap='viridis',
                max_words=100,
                contour_width=1,
                contour_color='steelblue'
            ).generate(text_data)
            
            # Création de la figure
            plt.figure(figsize=(12, 8))
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')
            plt.title('Nuage de mots - Analyse de texte OSINT', fontsize=16, pad=20)
            
            # Sauvegarde
            filepath = self.export_dir / 'wordclouds' / f"{filename}.png"
            plt.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            
            self.logger.info(f"Nuage de mots sauvegardé: {filepath}")
            
            return {
                'success': True,
                'filepath': str(filepath),
                'filename': filepath.name,
                'format': 'png',
                'word_count': len(text_data.split())
            }
            
        except Exception as e:
            error_msg = f"Erreur création nuage de mots: {str(e)}"
            self.logger.error(error_msg)
            return {'success': False, 'error': error_msg}
    
    def create_geographic_map(self, locations: List[Dict], filename: str = "geographic_map") -> Dict[str, Any]:
        """
        Crée une carte géographique des localisations
        
        Args:
            locations: Liste des localisations avec coordonnées
            filename: Nom du fichier de sortie
            
        Returns:
            Résultat de la génération
        """
        try:
            self.logger.info(f"Création de la carte géographique avec {len(locations)} localisations")
            
            # Préparation des données
            lats = [loc['latitude'] for loc in locations if 'latitude' in loc]
            lons = [loc['longitude'] for loc in locations if 'longitude' in loc]
            texts = [loc.get('label', 'Unknown') for loc in locations if 'latitude' in loc]
            sizes = [loc.get('importance', 10) for loc in locations if 'latitude' in loc]
            
            # Création de la carte
            fig = go.Figure()
            
            fig.add_trace(go.Scattermapbox(
                lat=lats,
                lon=lons,
                mode='markers',
                marker=dict(
                    size=sizes,
                    color='red',
                    opacity=0.7
                ),
                text=texts,
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "Lat: %{lat}<br>"
                    "Lon: %{lon}<br>"
                    "<extra></extra>"
                )
            ))
            
            # Configuration de la carte
            fig.update_layout(
                title="Carte géographique des localisations OSINT",
                mapbox=dict(
                    style="open-street-map",
                    center=dict(lat=sum(lats)/len(lats) if lats else 0, 
                               lon=sum(lons)/len(lons) if lons else 0),
                    zoom=1
                ),
                height=600,
                template=self.plotly_template
            )
            
            # Sauvegarde
            filepath = self.export_dir / 'reports' / f"{filename}.html"
            fig.write_html(str(filepath))
            
            self.logger.info(f"Carte géographique sauvegardée: {filepath}")
            
            return {
                'success': True,
                'filepath': str(filepath),
                'filename': filepath.name,
                'locations_count': len(locations),
                'format': 'html'
            }
            
        except Exception as e:
            error_msg = f"Erreur création carte géographique: {str(e)}"
            self.logger.error(error_msg)
            return {'success': False, 'error': error_msg}
    
    def create_comprehensive_report(self, analysis_data: Dict[str, Any], 
                                  filename: str = "comprehensive_report") -> Dict[str, Any]:
        """
        Crée un rapport visuel complet
        
        Args:
            analysis_data: Données d'analyse complètes
            filename: Nom du fichier de sortie
            
        Returns:
            Résultat de la génération
        """
        try:
            self.logger.info("Création du rapport visuel complet")
            
            # Création d'un rapport HTML avec multiples visualisations
            html_content = self._generate_html_report(analysis_data)
            
            # Sauvegarde
            filepath = self.export_dir / 'reports' / f"{filename}.html"
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f"Rapport complet sauvegardé: {filepath}")
            
            return {
                'success': True,
                'filepath': str(filepath),
                'filename': filepath.name,
                'format': 'html',
                'sections': list(analysis_data.keys())
            }
            
        except Exception as e:
            error_msg = f"Erreur création rapport complet: {str(e)}"
            self.logger.error(error_msg)
            return {'success': False, 'error': error_msg}
    
    def _generate_html_report(self, analysis_data: Dict[str, Any]) -> str:
        """
        Génère le contenu HTML du rapport
        
        Args:
            analysis_data: Données d'analyse
            
        Returns:
            Contenu HTML
        """
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        
        html = f"""
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Rapport OSINT Complet</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 10px;
                    margin-bottom: 30px;
                    text-align: center;
                }}
                .section {{
                    background: white;
                    padding: 25px;
                    margin-bottom: 25px;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .section-title {{
                    color: #4a5568;
                    border-bottom: 2px solid #e2e8f0;
                    padding-bottom: 10px;
                    margin-bottom: 20px;
                }}
                .metric-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin-bottom: 20px;
                }}
                .metric-card {{
                    background: #f7fafc;
                    padding: 20px;
                    border-radius: 8px;
                    text-align: center;
                    border-left: 4px solid #4299e1;
                }}
                .metric-value {{
                    font-size: 2em;
                    font-weight: bold;
                    color: #2d3748;
                }}
                .metric-label {{
                    color: #718096;
                    font-size: 0.9em;
                }}
                .data-table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 15px;
                }}
                .data-table th,
                .data-table td {{
                    padding: 12px;
                    text-align: left;
                    border-bottom: 1px solid #e2e8f0;
                }}
                .data-table th {{
                    background-color: #f7fafc;
                    font-weight: 600;
                }}
                .risk-high {{ color: #e53e3e; font-weight: bold; }}
                .risk-medium {{ color: #dd6b20; font-weight: bold; }}
                .risk-low {{ color: #38a169; font-weight: bold; }}
                .visualization {{
                    margin: 20px 0;
                    text-align: center;
                }}
                .visualization img {{
                    max-width: 100%;
                    height: auto;
                    border-radius: 8px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }}
                .footer {{
                    text-align: center;
                    margin-top: 40px;
                    color: #718096;
                    font-size: 0.9em;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 Rapport OSINT Complet</h1>
                <p>Généré le {timestamp}</p>
            </div>
        """
        
        # Ajout des sections dynamiques
        for section_name, section_data in analysis_data.items():
            html += f"""
            <div class="section">
                <h2 class="section-title">{section_name.replace('_', ' ').title()}</h2>
            """
            
            # Métriques
            if isinstance(section_data, dict) and any(isinstance(v, (int, float)) for v in section_data.values()):
                html += '<div class="metric-grid">'
                for key, value in section_data.items():
                    if isinstance(value, (int, float)):
                        html += f"""
                        <div class="metric-card">
                            <div class="metric-value">{value}</div>
                            <div class="metric-label">{key.replace('_', ' ').title()}</div>
                        </div>
                        """
                html += '</div>'
            
            # Données structurées
            if isinstance(section_data, list) and section_data:
                html += '<table class="data-table">'
                # En-têtes
                html += '<tr>'
                for key in section_data[0].keys():
                    html += f'<th>{key.replace("_", " ").title()}</th>'
                html += '</tr>'
                
                # Lignes
                for item in section_data[:10]:  # Limite à 10 éléments
                    html += '<tr>'
                    for key, value in item.items():
                        if 'risk' in key.lower():
                            if value == 'HIGH':
                                html += f'<td class="risk-high">{value}</td>'
                            elif value == 'MEDIUM':
                                html += f'<td class="risk-medium">{value}</td>'
                            else:
                                html += f'<td class="risk-low">{value}</td>'
                        else:
                            html += f'<td>{str(value)[:100]}</td>'  # Limite la longueur
                    html += '</tr>'
                html += '</table>'
            
            html += '</div>'
        
        html += """
            <div class="footer">
                <p>Rapport généré par Outils OSINT - https://github.com/AzouC/Outils-Osintt</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def plot_to_base64(self, plt_fig=None) -> str:
        """
        Convertit un plot matplotlib en base64 pour l'intégration HTML
        
        Args:
            plt_fig: Figure matplotlib (optionnelle)
            
        Returns:
            Image en base64
        """
        try:
            if plt_fig is None:
                plt_fig = plt
            
            buffer = BytesIO()
            plt_fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            buffer.close()
            
            return f"data:image/png;base64,{image_base64}"
            
        except Exception as e:
            self.logger.error(f"Erreur conversion plot en base64: {str(e)}")
            return ""

def main():
    """Fonction de démonstration"""
    from core.config_manager import ConfigManager
    
    config = ConfigManager()
    visualizer = DataVisualizer(config)
    
    print("🎨 Visualiseur de Données OSINT")
    print("=" * 40)
    
    # Données de test
    test_nodes = [
        {'id': 'person1', 'type': 'person', 'label': 'John Doe'},
        {'id': 'org1', 'type': 'organization', 'label': 'ACME Corp'},
        {'id': 'email1', 'type': 'email', 'label': 'john@acme.com'},
        {'id': 'domain1', 'type': 'domain', 'label': 'acme.com'}
    ]
    
    test_edges = [
        {'source': 'person1', 'target': 'org1', 'relation': 'works_for'},
        {'source': 'person1', 'target': 'email1', 'relation': 'uses'},
        {'source': 'org1', 'target': 'domain1', 'relation': 'owns'}
    ]
    
    # Test des visualisations
    print("1. Création du graphique de réseau...")
    result = visualizer.create_network_graph(test_nodes, test_edges, "test_network")
    print(f"   ✅ {result['filepath']}")
    
    print("2. Création du nuage de mots...")
    text = "OSINT intelligence investigation security data analysis python kali linux"
    result = visualizer.create_word_cloud(text * 10, "test_wordcloud")
    print(f"   ✅ {result['filepath']}")
    
    print("3. Création du rapport de risque...")
    risk_data = {
        'risk_distribution': {'HIGH': 5, 'MEDIUM': 12, 'LOW': 23},
        'risk_by_category': {'Email': 8, 'Domain': 15, 'IP': 7, 'Person': 12},
        'top_risky_entities': [
            {'entity': 'malicious-domain.com', 'risk_score': 95},
            {'entity': 'suspicious@email.com', 'risk_score': 87},
            {'entity': '192.168.1.100', 'risk_score': 76}
        ]
    }
    result = visualizer.create_risk_dashboard(risk_data, "test_risk")
    print(f"   ✅ {result['filepath']}")
    
    print("\n🎉 Visualisations créées avec succès!")

if __name__ == "__main__":
    main()
