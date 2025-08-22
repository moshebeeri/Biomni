#!/usr/bin/env python3
"""
Protein Connectivity Validator Tool for NIBR Biomni
Validates protein-protein connectivity using network analysis
This is the specific tool mentioned in the biomedical researcher use case
"""

import json
import pandas as pd
from typing import List, Dict, Any, Tuple
import numpy as np

# Try to import networkx, provide fallback if not available
try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    print("Warning: NetworkX not installed. Some features will be limited.")

def validate_protein_connectivity(
    protein_list: List[str], 
    interaction_data: Dict[str, List[Tuple[str, str, float]]], 
    confidence_threshold: float = 0.7
) -> str:
    """
    Validates protein connectivity using network analysis.
    
    Args:
        protein_list: List of protein identifiers to analyze
        interaction_data: Dictionary with 'interactions' key containing 
                         list of (protein_a, protein_b, confidence_score) tuples
        confidence_threshold: Minimum confidence score for interactions (0-1)
    
    Returns:
        JSON string containing validation report with connectivity metrics,
        hub analysis, and pathway coherence scores
    
    Example:
        protein_list = ['BRCA1', 'BRCA2', 'ATM', 'ATR', 'TP53']
        interaction_data = {
            'interactions': [
                ('BRCA1', 'BRCA2', 0.95),
                ('BRCA1', 'ATM', 0.88),
                ('ATM', 'TP53', 0.92),
                ('ATR', 'TP53', 0.75),
                ('BRCA2', 'TP53', 0.81)
            ]
        }
        result = validate_protein_connectivity(protein_list, interaction_data)
    """
    
    if not HAS_NETWORKX:
        return json.dumps({
            'error': 'NetworkX not installed. Please install: pip install networkx',
            'status': 'failed'
        })
    
    try:
        # Create network graph
        G = nx.Graph()
        
        # Add all proteins as nodes first
        G.add_nodes_from(protein_list)
        
        # Parse interaction data
        interactions = interaction_data.get('interactions', [])
        if isinstance(interaction_data, list):
            interactions = interaction_data
        
        # Add edges based on confidence threshold
        high_confidence_edges = []
        medium_confidence_edges = []
        low_confidence_edges = []
        
        for interaction in interactions:
            if len(interaction) >= 3:
                protein_a, protein_b, confidence = interaction
            elif len(interaction) == 2:
                protein_a, protein_b = interaction
                confidence = 0.5  # Default confidence
            else:
                continue
            
            # Only consider interactions between proteins in our list
            if protein_a in protein_list and protein_b in protein_list:
                if confidence >= confidence_threshold:
                    G.add_edge(protein_a, protein_b, weight=confidence)
                    high_confidence_edges.append((protein_a, protein_b, confidence))
                elif confidence >= 0.5:
                    medium_confidence_edges.append((protein_a, protein_b, confidence))
                else:
                    low_confidence_edges.append((protein_a, protein_b, confidence))
        
        # Calculate connectivity metrics for each protein
        connectivity_metrics = {}
        
        for protein in protein_list:
            if protein in G:
                metrics = {
                    'degree': G.degree(protein),
                    'degree_centrality': nx.degree_centrality(G).get(protein, 0),
                    'betweenness_centrality': nx.betweenness_centrality(G).get(protein, 0),
                    'closeness_centrality': nx.closeness_centrality(G).get(protein, 0),
                    'clustering_coefficient': nx.clustering(G, protein),
                    'neighbors': list(G.neighbors(protein))
                }
            else:
                metrics = {
                    'degree': 0,
                    'degree_centrality': 0,
                    'betweenness_centrality': 0,
                    'closeness_centrality': 0,
                    'clustering_coefficient': 0,
                    'neighbors': []
                }
            
            connectivity_metrics[protein] = metrics
        
        # Identify critical hub proteins
        critical_hubs = []
        secondary_hubs = []
        peripheral_proteins = []
        isolated_proteins = []
        
        for protein, metrics in connectivity_metrics.items():
            if metrics['degree'] == 0:
                isolated_proteins.append(protein)
            elif metrics['degree_centrality'] > 0.5 and metrics['betweenness_centrality'] > 0.2:
                critical_hubs.append({
                    'protein': protein,
                    'degree': metrics['degree'],
                    'importance_score': (metrics['degree_centrality'] + 
                                        metrics['betweenness_centrality']) / 2
                })
            elif metrics['degree_centrality'] > 0.3:
                secondary_hubs.append({
                    'protein': protein,
                    'degree': metrics['degree'],
                    'importance_score': metrics['degree_centrality']
                })
            else:
                peripheral_proteins.append(protein)
        
        # Sort hubs by importance
        critical_hubs.sort(key=lambda x: x['importance_score'], reverse=True)
        secondary_hubs.sort(key=lambda x: x['importance_score'], reverse=True)
        
        # Calculate network-level metrics
        network_metrics = {
            'total_proteins': len(protein_list),
            'connected_proteins': len([p for p in protein_list if connectivity_metrics[p]['degree'] > 0]),
            'total_interactions': G.number_of_edges(),
            'network_density': nx.density(G),
            'average_degree': sum(metrics['degree'] for metrics in connectivity_metrics.values()) / len(protein_list),
            'connected_components': nx.number_connected_components(G),
            'largest_component_size': len(max(nx.connected_components(G), key=len)) if G.number_of_nodes() > 0 else 0
        }
        
        # Calculate pathway coherence
        pathway_coherence = calculate_pathway_coherence(G, protein_list)
        
        # Generate validation summary
        validation_summary = {
            'status': 'validated',
            'confidence_threshold': confidence_threshold,
            'network_metrics': network_metrics,
            'pathway_coherence_score': pathway_coherence,
            'critical_hubs': critical_hubs,
            'secondary_hubs': secondary_hubs,
            'isolated_proteins': isolated_proteins,
            'peripheral_proteins': peripheral_proteins,
            'connectivity_metrics': connectivity_metrics,
            'interaction_summary': {
                'high_confidence': len(high_confidence_edges),
                'medium_confidence': len(medium_confidence_edges),
                'low_confidence': len(low_confidence_edges),
                'total_analyzed': len(interactions)
            }
        }
        
        # Add recommendations
        recommendations = generate_recommendations(
            validation_summary, 
            connectivity_metrics,
            critical_hubs,
            isolated_proteins
        )
        validation_summary['recommendations'] = recommendations
        
        return json.dumps(validation_summary, indent=2)
        
    except Exception as e:
        return json.dumps({
            'error': f'Validation failed: {str(e)}',
            'status': 'failed'
        })

def calculate_pathway_coherence(graph, protein_list: List[str]) -> float:
    """
    Calculate how well connected the proteins are as a functional unit.
    
    Returns a score from 0 (no connectivity) to 1 (fully connected).
    """
    if not protein_list or not graph:
        return 0.0
    
    # Get subgraph containing only our proteins
    subgraph = graph.subgraph(protein_list)
    
    if subgraph.number_of_nodes() == 0:
        return 0.0
    
    # Calculate various coherence metrics
    n_nodes = subgraph.number_of_nodes()
    n_edges = subgraph.number_of_edges()
    
    # Maximum possible edges
    max_possible_edges = n_nodes * (n_nodes - 1) / 2
    
    if max_possible_edges == 0:
        return 0.0
    
    # Basic connectivity ratio
    connectivity_ratio = n_edges / max_possible_edges
    
    # Component coherence (penalty for disconnected components)
    n_components = nx.number_connected_components(subgraph)
    component_penalty = 1.0 / n_components if n_components > 0 else 0
    
    # Combined coherence score
    coherence_score = (connectivity_ratio * 0.7 + component_penalty * 0.3)
    
    return min(1.0, coherence_score)

def generate_recommendations(
    validation_summary: Dict,
    connectivity_metrics: Dict,
    critical_hubs: List[Dict],
    isolated_proteins: List[str]
) -> List[str]:
    """
    Generate actionable recommendations based on validation results.
    """
    recommendations = []
    
    # Check network connectivity
    if validation_summary['network_metrics']['network_density'] < 0.1:
        recommendations.append(
            "Network density is very low. Consider expanding the protein list or "
            "lowering the confidence threshold to identify more interactions."
        )
    
    # Check for isolated proteins
    if isolated_proteins:
        recommendations.append(
            f"Isolated proteins detected ({', '.join(isolated_proteins)}). "
            "These proteins show no interactions with others in the network. "
            "Consider: (1) Verifying if these proteins belong to this pathway, "
            "(2) Checking for indirect interactions, or (3) Using additional databases."
        )
    
    # Identify critical hubs for experimental validation
    if critical_hubs:
        top_hubs = [hub['protein'] for hub in critical_hubs[:3]]
        recommendations.append(
            f"Critical hub proteins identified ({', '.join(top_hubs)}). "
            "These are high-priority targets for experimental validation and "
            "potential drug targeting due to their central role in the network."
        )
    
    # Check pathway coherence
    coherence = validation_summary['pathway_coherence_score']
    if coherence < 0.3:
        recommendations.append(
            "Low pathway coherence detected. The proteins may not form a "
            "functionally cohesive unit. Consider reviewing pathway membership "
            "or investigating sub-modules within the network."
        )
    elif coherence > 0.7:
        recommendations.append(
            "High pathway coherence confirmed. The proteins form a well-connected "
            "functional unit, supporting their role as a coordinated pathway."
        )
    
    # Check for potential bottlenecks
    bottlenecks = []
    for protein, metrics in connectivity_metrics.items():
        if metrics['betweenness_centrality'] > 0.3 and metrics['degree'] > 2:
            bottlenecks.append(protein)
    
    if bottlenecks:
        recommendations.append(
            f"Potential bottleneck proteins identified ({', '.join(bottlenecks[:3])}). "
            "These proteins control information flow in the network and may be "
            "critical control points for pathway regulation."
        )
    
    # Suggest next steps
    if validation_summary['network_metrics']['connected_components'] > 1:
        recommendations.append(
            "Multiple disconnected components detected. Consider investigating "
            "bridging proteins or indirect interactions that might connect these "
            "sub-networks."
        )
    
    return recommendations

# Additional helper function for creating example interaction data
def create_example_interaction_data() -> Dict:
    """
    Create example interaction data for testing.
    This represents typical protein-protein interaction data from databases.
    """
    return {
        'interactions': [
            # DNA Damage Response pathway interactions
            ('BRCA1', 'BRCA2', 0.95),
            ('BRCA1', 'ATM', 0.88),
            ('BRCA1', 'PALB2', 0.92),
            ('BRCA1', 'RAD51', 0.85),
            ('BRCA2', 'PALB2', 0.94),
            ('BRCA2', 'RAD51', 0.91),
            ('ATM', 'TP53', 0.93),
            ('ATM', 'CHK2', 0.89),
            ('ATR', 'CHK1', 0.87),
            ('ATR', 'TP53', 0.75),
            ('TP53', 'MDM2', 0.96),
            ('CHK1', 'CHK2', 0.65),
            ('RAD51', 'RAD52', 0.78),
            ('PALB2', 'RAD51', 0.83),
            ('MDM2', 'MDM4', 0.88)
        ]
    }

# Example usage
if __name__ == "__main__":
    # Example protein list from DNA damage response pathway
    proteins = ['BRCA1', 'BRCA2', 'ATM', 'ATR', 'TP53', 'CHK1', 'CHK2', 
                'PALB2', 'RAD51', 'RAD52', 'MDM2', 'MDM4']
    
    # Get example interaction data
    interactions = create_example_interaction_data()
    
    # Validate connectivity
    result = validate_protein_connectivity(
        protein_list=proteins,
        interaction_data=interactions,
        confidence_threshold=0.7
    )
    
    # Print results
    print("Protein Connectivity Validation Results:")
    print("=" * 50)
    print(result)