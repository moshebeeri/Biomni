#!/usr/bin/env python3
"""
Pre-Phase 0: State Management Foundation - Usage Examples
Demonstrates PersistentA1 and GlobalAgentManager functionality
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from biomni.persistent_agent import PersistentA1, GlobalAgentManager


def demo_persistent_a1():
    """Demonstrate PersistentA1 agent with state persistence."""
    print("🔬 PersistentA1 Demo")
    print("=" * 50)
    
    # Create temporary directory for demo
    temp_dir = tempfile.mkdtemp()
    print(f"Using temporary directory: {temp_dir}")
    
    try:
        # Create a persistent agent
        print("\n1. Creating PersistentA1 agent...")
        agent = PersistentA1(
            agent_id="demo_researcher",
            state_dir=temp_dir,
            path="./data",
            llm="claude-3-5-sonnet-20241022",
            use_tool_retriever=True,
            auto_save=True
        )
        print(f"✅ Created agent: {agent.agent_id}")
        
        # Add custom tools
        print("\n2. Adding custom research tools...")
        
        def analyze_protein_sequence(sequence: str, analysis_type: str = "basic") -> str:
            """Analyze protein sequence using various methods."""
            # Simulated analysis
            results = {
                "sequence_length": len(sequence),
                "analysis_type": analysis_type,
                "hydrophobic_residues": sequence.count('A') + sequence.count('V') + sequence.count('L'),
                "charged_residues": sequence.count('K') + sequence.count('R') + sequence.count('D') + sequence.count('E')
            }
            return f"Protein analysis results: {results}"
        
        def scrape_pubmed_abstracts(query: str, max_results: int = 10) -> str:
            """Scrape PubMed abstracts for research query."""
            # Simulated scraping
            abstracts = []
            for i in range(min(max_results, 3)):  # Simulate 3 results
                abstracts.append({
                    "title": f"Research paper {i+1} on {query}",
                    "abstract": f"Abstract {i+1} discussing {query} in biomedical context...",
                    "pmid": f"PMID{12345678 + i}"
                })
            return f"Found {len(abstracts)} abstracts for '{query}': {abstracts}"
        
        # Add tools to agent
        agent.add_tool(analyze_protein_sequence)
        agent.add_tool(scrape_pubmed_abstracts)
        print("✅ Added custom tools: analyze_protein_sequence, scrape_pubmed_abstracts")
        
        # Add custom data
        print("\n3. Adding custom research data...")
        research_data = {
            "lab_protocols.json": "Standard lab protocols for protein analysis",
            "patient_cohort_2024.csv": "Patient cohort data with genomic annotations", 
            "literature_cache.parquet": "Cached literature search results"
        }
        agent.add_data(research_data)
        print(f"✅ Added {len(research_data)} data sources")
        
        # Add custom software
        print("\n4. Adding custom software packages...")
        software_packages = {
            "biopython": "Bioinformatics library for Python",
            "pip:networkx": "Network analysis library",
            "pip:matplotlib": "Plotting library",
            "rdkit-pypi": "Chemical informatics toolkit"
        }
        # Add without installation for demo
        agent.add_software(software_packages, install=False)
        print(f"✅ Added {len(software_packages)} software packages")
        
        # Show current state
        print("\n5. Current agent state:")
        state_summary = agent.get_state_summary()
        for key, value in state_summary.items():
            print(f"   {key}: {value}")
        
        # Test tool functionality
        print("\n6. Testing custom tools...")
        tools = agent.list_custom_tools()
        print(f"Available tools: {tools}")
        
        # Export state
        print("\n7. Exporting agent state...")
        export_path = os.path.join(temp_dir, "demo_agent_export.json")
        agent.export_state(export_path)
        print(f"✅ Exported state to: {export_path}")
        
        # Create second agent and import state
        print("\n8. Creating second agent and importing state...")
        agent2 = PersistentA1(
            agent_id="demo_researcher_clone",
            state_dir=temp_dir,
            auto_save=False
        )
        agent2.import_state(export_path, merge=False)
        print(f"✅ Imported state to agent: {agent2.agent_id}")
        print(f"   Tools imported: {agent2.list_custom_tools()}")
        print(f"   Data imported: {agent2.list_custom_data()}")
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)
        print(f"\n🧹 Cleaned up temporary directory: {temp_dir}")


def demo_global_agent_manager():
    """Demonstrate GlobalAgentManager for multi-agent workflows."""
    print("\n\n🌐 GlobalAgentManager Demo")
    print("=" * 50)
    
    # Create temporary directory for demo
    temp_dir = tempfile.mkdtemp()
    print(f"Using temporary directory: {temp_dir}")
    
    try:
        # Initialize manager
        print("\n1. Initializing GlobalAgentManager...")
        manager = GlobalAgentManager(base_state_dir=temp_dir)
        print("✅ Manager initialized")
        
        # Create multiple research agents
        print("\n2. Creating multiple research agents...")
        
        # Genomics researcher
        genomics_agent = manager.create_agent(
            "genomics_researcher_001",
            llm="claude-3-5-sonnet-20241022",
            use_tool_retriever=True
        )
        
        # Add genomics-specific tools
        def analyze_gene_expression(expression_data: str, method: str = "deseq2") -> str:
            """Analyze gene expression data."""
            return f"Gene expression analysis using {method}: {len(expression_data)} samples processed"
        
        def find_variant_effects(variant_list: str) -> str:
            """Find effects of genetic variants."""
            variants = variant_list.split(',')
            return f"Analyzed {len(variants)} variants for functional effects"
        
        genomics_agent.add_tool(analyze_gene_expression)
        genomics_agent.add_tool(find_variant_effects)
        
        # Drug discovery researcher
        drug_agent = manager.create_agent(
            "drug_discovery_researcher_001",
            llm="claude-3-5-sonnet-20241022",
            use_tool_retriever=True
        )
        
        # Add drug discovery tools
        def screen_compound_library(target_protein: str, library_size: int = 1000) -> str:
            """Screen compound library against target."""
            hits = library_size // 100  # Simulate 1% hit rate
            return f"Screened {library_size} compounds against {target_protein}, found {hits} hits"
        
        def predict_admet_properties(compound_smiles: str) -> str:
            """Predict ADMET properties of compound."""
            return f"ADMET prediction for {compound_smiles}: Good oral bioavailability, Low toxicity"
        
        drug_agent.add_tool(screen_compound_library)
        drug_agent.add_tool(predict_admet_properties)
        
        print("✅ Created specialized agents:")
        print(f"   - Genomics agent: {genomics_agent.agent_id}")
        print(f"   - Drug discovery agent: {drug_agent.agent_id}")
        
        # Show all agents
        print("\n3. Listing all agents...")
        all_agents = manager.list_agents()
        print(f"Active agents: {all_agents}")
        
        # Get agent summaries
        print("\n4. Agent summaries:")
        for agent_id in all_agents:
            summary = manager.get_agent_summary(agent_id)
            if summary:
                print(f"   {agent_id}:")
                print(f"     Tools: {summary.get('custom_tools_count', 0)}")
                print(f"     Data: {summary.get('custom_data_count', 0)}")
                print(f"     In memory: {summary.get('in_memory', True)}")
        
        # Clone an agent
        print("\n5. Cloning genomics agent...")
        cloned_agent = manager.clone_agent(
            "genomics_researcher_001",
            "genomics_researcher_002"
        )
        print(f"✅ Cloned agent: {cloned_agent.agent_id}")
        print(f"   Cloned tools: {cloned_agent.list_custom_tools()}")
        
        # Demonstrate agent retrieval
        print("\n6. Retrieving existing agents...")
        retrieved_agent = manager.get_agent("genomics_researcher_001")
        print(f"✅ Retrieved agent: {retrieved_agent.agent_id}")
        print(f"   Same instance: {retrieved_agent is genomics_agent}")
        
        # Show collaboration scenario
        print("\n7. Collaboration scenario:")
        print("   Genomics researcher shares data with drug discovery team...")
        
        # Add shared data to genomics agent
        shared_data = {
            "target_genes.csv": "List of target genes for drug discovery",
            "variant_effects.json": "Functional effects of variants",
            "pathway_analysis.xlsx": "Pathway enrichment results"
        }
        genomics_agent.add_data(shared_data)
        
        # Export genomics state for sharing
        export_path = os.path.join(temp_dir, "genomics_shared_state.json")
        genomics_agent.export_state(export_path)
        
        # Import shared data to drug discovery agent
        drug_agent.import_state(export_path, merge=True)
        print(f"✅ Shared data imported to drug discovery agent")
        print(f"   Drug agent now has: {drug_agent.list_custom_data()}")
        
        # Cleanup demonstration
        print("\n8. Cleanup operations...")
        print(f"   Agents before cleanup: {len(manager.list_agents())}")
        
        manager.delete_agent("genomics_researcher_002", remove_files=True)
        print(f"   Agents after deleting clone: {len(manager.list_agents())}")
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)
        print(f"\n🧹 Cleaned up temporary directory: {temp_dir}")


def demo_real_world_scenario():
    """Demonstrate real-world research workflow."""
    print("\n\n🧬 Real-World Research Scenario")
    print("=" * 50)
    print("Scenario: Cancer biomarker discovery workflow")
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        manager = GlobalAgentManager(base_state_dir=temp_dir)
        
        # Phase 1: Data analyst sets up initial analysis
        print("\n📊 Phase 1: Data Analyst - Initial Analysis Setup")
        analyst_agent = manager.create_agent("cancer_data_analyst_001")
        
        def preprocess_omics_data(data_type: str, sample_count: int) -> str:
            """Preprocess multi-omics data."""
            return f"Preprocessed {data_type} data for {sample_count} samples"
        
        def identify_differential_genes(control_count: int, treatment_count: int) -> str:
            """Identify differentially expressed genes."""
            total_genes = 20000
            diff_genes = int(total_genes * 0.05)  # 5% differentially expressed
            return f"Found {diff_genes} differentially expressed genes ({control_count} vs {treatment_count} samples)"
        
        analyst_agent.add_tool(preprocess_omics_data)
        analyst_agent.add_tool(identify_differential_genes)
        
        # Add initial datasets
        analyst_data = {
            "tcga_brca_expression.csv": "TCGA breast cancer expression data",
            "clinical_metadata.json": "Patient clinical information",
            "mutation_data.vcf": "Somatic mutation data"
        }
        analyst_agent.add_data(analyst_data)
        print("✅ Data analyst setup complete")
        
        # Phase 2: Bioinformatician extends analysis
        print("\n🧬 Phase 2: Bioinformatician - Pathway Analysis")
        bioinfo_agent = manager.clone_agent("cancer_data_analyst_001", "bioinformatician_001")
        
        def pathway_enrichment_analysis(gene_list: str) -> str:
            """Perform pathway enrichment analysis."""
            genes = gene_list.split(',')
            enriched_pathways = ["DNA repair", "Cell cycle", "Apoptosis", "Immune response"]
            return f"Analyzed {len(genes)} genes, found enrichment in: {enriched_pathways}"
        
        def protein_interaction_network(proteins: str) -> str:
            """Build protein interaction network."""
            protein_list = proteins.split(',')
            interactions = len(protein_list) * 3  # Average 3 interactions per protein
            return f"Built network with {len(protein_list)} proteins and {interactions} interactions"
        
        bioinfo_agent.add_tool(pathway_enrichment_analysis)
        bioinfo_agent.add_tool(protein_interaction_network)
        print("✅ Bioinformatician analysis ready")
        
        # Phase 3: Computational biologist adds ML models
        print("\n🤖 Phase 3: Computational Biologist - ML Models")
        ml_agent = manager.clone_agent("bioinformatician_001", "comp_bio_ml_001")
        
        def train_biomarker_classifier(features: str, labels: str) -> str:
            """Train machine learning classifier for biomarkers."""
            feature_count = len(features.split(','))
            return f"Trained classifier with {feature_count} features, AUC: 0.87"
        
        def validate_biomarker_panel(validation_data: str) -> str:
            """Validate biomarker panel on independent dataset."""
            return "Biomarker panel validation: Sensitivity 85%, Specificity 92%"
        
        ml_agent.add_tool(train_biomarker_classifier)
        ml_agent.add_tool(validate_biomarker_panel)
        
        # Add ML-specific data
        ml_data = {
            "validation_cohort.csv": "Independent validation dataset",
            "feature_matrix.npy": "Processed feature matrix for ML",
            "trained_models.pkl": "Saved ML models"
        }
        ml_agent.add_data(ml_data)
        print("✅ ML pipeline setup complete")
        
        # Phase 4: Research collaboration summary
        print("\n🤝 Phase 4: Research Collaboration Summary")
        agents = manager.list_agents()
        print(f"Active research agents: {len(agents)}")
        
        for agent_id in agents:
            summary = manager.get_agent_summary(agent_id)
            if summary:
                print(f"\n{agent_id}:")
                print(f"  Tools: {summary['custom_tools_count']}")
                print(f"  Datasets: {summary['custom_data_count']}")
                print(f"  Software: {summary['custom_software_count']}")
        
        # Export final workflow
        print("\n📦 Exporting complete workflow...")
        workflow_dir = os.path.join(temp_dir, "cancer_biomarker_workflow")
        os.makedirs(workflow_dir, exist_ok=True)
        
        for agent_id in agents:
            agent = manager.get_agent(agent_id)
            export_file = os.path.join(workflow_dir, f"{agent_id}_state.json")
            agent.export_state(export_file)
        
        print(f"✅ Workflow exported to: {workflow_dir}")
        print("   This workflow can now be shared with collaborators")
        print("   or deployed in production environments")
        
    finally:
        shutil.rmtree(temp_dir)
        print(f"\n🧹 Cleaned up temporary directory")


if __name__ == "__main__":
    print("🚀 Pre-Phase 0: State Management Foundation Demo")
    print("=" * 60)
    
    # Run all demos
    demo_persistent_a1()
    demo_global_agent_manager()
    demo_real_world_scenario()
    
    print("\n✨ All demos completed successfully!")
    print("\nKey takeaways:")
    print("1. PersistentA1 provides automatic state persistence for biomni agents")
    print("2. Custom tools, data, and software are preserved across sessions")
    print("3. GlobalAgentManager enables multi-agent collaboration workflows")
    print("4. Agents can be cloned, shared, and exported for team collaboration")
    print("5. The foundation supports real-world research scenarios with state continuity")
