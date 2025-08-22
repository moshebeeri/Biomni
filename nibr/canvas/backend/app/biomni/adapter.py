# Phase 1: Canvas UI Integration with GlobalAgentManager
# Enhanced BiomniCanvasAdapter using persistent agents

from typing import Dict, List, Any, AsyncGenerator, Optional
import asyncio
import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from .persistent_agent import GlobalAgentManager, PersistentA1

# Configure logging
logger = logging.getLogger(__name__)

class BiomniCanvasAdapter:
    """Enhanced adapter to bridge Open Canvas with Persistent Biomni agents for NIBR."""
    
    def __init__(self, database_path: str = "./data/canvas_sessions.db"):
        self.agent_manager = GlobalAgentManager()
        self.active_sessions: Dict[str, Dict] = {}
        self.research_contexts: Dict[str, List[Dict]] = {}  # Track research history
        self.database_path = database_path
        self._init_database()
        
        logger.info("Initialized BiomniCanvasAdapter with persistent agent support")
    
    def _init_database(self):
        """Initialize SQLite database for Canvas sessions."""
        Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Canvas sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS canvas_sessions (
                session_id TEXT PRIMARY KEY,
                researcher_id TEXT NOT NULL,
                username TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                session_metadata JSON,
                research_context JSON
            )
        """)
        
        # Research interactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS research_interactions (
                interaction_id TEXT PRIMARY KEY,
                session_id TEXT,
                researcher_id TEXT,
                prompt TEXT,
                response TEXT,
                tools_used JSON,
                artifacts_generated JSON,
                insights_discovered JSON,
                execution_time_ms INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES canvas_sessions(session_id)
            )
        """)
        
        # Canvas artifacts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS canvas_artifacts (
                artifact_id TEXT PRIMARY KEY,
                session_id TEXT,
                artifact_type TEXT,  -- 'code', 'visualization', 'data', 'report'
                artifact_name TEXT,
                artifact_content TEXT,
                artifact_metadata JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES canvas_sessions(session_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    async def create_research_session(
        self,
        researcher_id: str,
        username: str,
        research_domain: str = "general",
        initial_prompt: Optional[str] = None
    ) -> Dict:
        """Initialize a new research session with persistent agent integration."""
        
        # Create agent ID based on researcher and domain
        agent_id = f"{researcher_id}_{research_domain}"
        
        # Get or create persistent agent
        agent = self.agent_manager.get_agent(
            agent_id=agent_id,
            llm="claude-3-5-sonnet-20241022",
            use_tool_retriever=True,
            timeout_seconds=600
        )
        
        # Create session ID
        session_id = f"{researcher_id}_{research_domain}_{int(datetime.now().timestamp())}"
        
        # Initialize session data
        session_data = {
            'session_id': session_id,
            'researcher_id': researcher_id,
            'username': username,
            'agent_id': agent_id,
            'agent': agent,
            'research_domain': research_domain,
            'start_time': datetime.now(),
            'messages': [],
            'artifacts': [],
            'insights': [],
            'tools_executed': [],
            'research_context': self._build_research_context(agent_id)
        }
        
        self.active_sessions[session_id] = session_data
        self.research_contexts[session_id] = []
        
        # Save session to database
        self._save_session_to_db(session_data)
        
        # Add domain-specific tools based on research area
        await self._configure_domain_tools(agent, research_domain)
        
        logger.info(f"Created research session {session_id} for {username} in {research_domain}")
        
        return {
            'session_id': session_id,
            'agent_id': agent_id,
            'research_domain': research_domain,
            'status': 'initialized',
            'canvas_config': self._get_canvas_config(researcher_id, research_domain),
            'agent_summary': agent.get_state_summary(),
            'available_tools': agent.list_custom_tools(),
            'available_data': agent.list_custom_data()
        }
    
    async def _configure_domain_tools(self, agent: PersistentA1, research_domain: str):
        """Configure domain-specific tools for the research area."""
        
        domain_tools = {
            'genomics': [
                self._create_genomics_tools,
                self._add_genomics_data
            ],
            'drug_discovery': [
                self._create_drug_discovery_tools,
                self._add_drug_discovery_data
            ],
            'protein_analysis': [
                self._create_protein_tools,
                self._add_protein_data
            ],
            'systems_biology': [
                self._create_systems_tools,
                self._add_systems_data
            ]
        }
        
        if research_domain in domain_tools:
            for tool_setup_func in domain_tools[research_domain]:
                await tool_setup_func(agent)
        
        # Add common research tools
        await self._add_common_research_tools(agent)
    
    def _create_genomics_tools(self, agent: PersistentA1):
        """Add genomics-specific research tools."""
        
        def analyze_gene_expression_data(expression_matrix: str, method: str = "deseq2") -> str:
            """Analyze gene expression data using specified method."""
            import pandas as pd
            import numpy as np
            
            # Simulated analysis for demo
            n_genes = 20000
            n_samples = expression_matrix.count('\n') if expression_matrix else 100
            
            # Simulate differential expression analysis
            diff_genes = int(n_genes * 0.05)  # 5% significantly different
            upregulated = diff_genes // 2
            downregulated = diff_genes - upregulated
            
            results = {
                'total_genes_analyzed': n_genes,
                'samples_processed': n_samples,
                'significantly_differential': diff_genes,
                'upregulated': upregulated,
                'downregulated': downregulated,
                'method_used': method,
                'pathways_enriched': ['DNA repair', 'Cell cycle', 'Immune response'],
                'top_genes': ['BRCA1', 'TP53', 'EGFR', 'MYC', 'KRAS']
            }
            
            return f"Gene expression analysis complete:\n{json.dumps(results, indent=2)}"
        
        def identify_variant_effects(variant_list: str, genome_build: str = "hg38") -> str:
            """Identify functional effects of genetic variants."""
            variants = variant_list.strip().split('\n') if variant_list else []
            
            effects = []
            for i, variant in enumerate(variants[:10]):  # Limit for demo
                effect_types = ['missense', 'nonsense', 'synonymous', 'splice_site', 'regulatory']
                clinical_significance = ['benign', 'likely_benign', 'uncertain', 'likely_pathogenic', 'pathogenic']
                
                effects.append({
                    'variant': variant.strip() if variant.strip() else f"chr1:12345{i}:A>G",
                    'effect_type': effect_types[i % len(effect_types)],
                    'clinical_significance': clinical_significance[i % len(clinical_significance)],
                    'affected_gene': f"GENE{i+1}",
                    'conservation_score': round(0.1 + (i * 0.1), 2)
                })
            
            return f"Variant effects analysis:\n{json.dumps(effects, indent=2)}"
        
        def perform_gwas_analysis(phenotype_data: str, genotype_data: str) -> str:
            """Perform genome-wide association study analysis."""
            phenotype_samples = len(phenotype_data.split('\n')) if phenotype_data else 1000
            genotype_markers = 500000  # Typical GWAS marker count
            
            # Simulate GWAS results
            significant_loci = 15
            results = {
                'samples_analyzed': phenotype_samples,
                'markers_tested': genotype_markers,
                'genome_wide_significant': significant_loci,
                'lambda_gc': 1.02,  # Genomic inflation factor
                'top_associations': [
                    {'chr': 1, 'pos': 12345678, 'rsid': 'rs12345', 'p_value': 5e-9, 'beta': 0.15},
                    {'chr': 6, 'pos': 87654321, 'rsid': 'rs67890', 'p_value': 2e-8, 'beta': -0.12},
                    {'chr': 12, 'pos': 55555555, 'rsid': 'rs11111', 'p_value': 8e-8, 'beta': 0.18}
                ]
            }
            
            return f"GWAS analysis complete:\n{json.dumps(results, indent=2)}"
        
        # Add tools to agent
        agent.add_tool(analyze_gene_expression_data)
        agent.add_tool(identify_variant_effects)
        agent.add_tool(perform_gwas_analysis)
        
        logger.info("Added genomics tools to agent")
    
    def _create_drug_discovery_tools(self, agent: PersistentA1):
        """Add drug discovery-specific tools."""
        
        def screen_compound_library(target_protein: str, library_size: int = 100000) -> str:
            """Screen compound library against target protein."""
            # Simulate virtual screening
            hit_rate = 0.01  # 1% hit rate
            hits = int(library_size * hit_rate)
            
            results = {
                'target_protein': target_protein,
                'compounds_screened': library_size,
                'initial_hits': hits,
                'hit_rate_percent': hit_rate * 100,
                'top_compounds': [
                    {'compound_id': f'COMP_{i:06d}', 'score': round(8.5 - i*0.1, 2), 'molecular_weight': 300 + i*10}
                    for i in range(min(10, hits))
                ]
            }
            
            return f"Compound screening results:\n{json.dumps(results, indent=2)}"
        
        def predict_admet_properties(compound_smiles: str) -> str:
            """Predict ADMET properties of compounds."""
            compounds = compound_smiles.strip().split('\n') if compound_smiles else ['CCO']  # Ethanol as default
            
            predictions = []
            for i, smiles in enumerate(compounds[:5]):  # Limit for demo
                predictions.append({
                    'smiles': smiles.strip() if smiles.strip() else f'C{i}CO',
                    'absorption': {'bioavailability': round(0.3 + i*0.1, 2), 'permeability': 'high'},
                    'distribution': {'vd_l_kg': round(1.2 + i*0.2, 2), 'protein_binding': round(0.8 + i*0.05, 2)},
                    'metabolism': {'cyp_inhibition': ['2D6', '3A4'][i % 2], 'stability': 'moderate'},
                    'excretion': {'clearance_ml_min': round(100 + i*20, 1), 'half_life_h': round(2 + i*0.5, 1)},
                    'toxicity': {'ld50_mg_kg': round(500 + i*100, 0), 'mutagenic': i % 3 == 0}
                })
            
            return f"ADMET predictions:\n{json.dumps(predictions, indent=2)}"
        
        def design_drug_combinations(primary_drug: str, target_pathway: str) -> str:
            """Design drug combination strategies."""
            combinations = [
                {'combination': f'{primary_drug} + Compound_A', 'synergy_score': 0.85, 'mechanism': 'pathway_convergence'},
                {'combination': f'{primary_drug} + Compound_B', 'synergy_score': 0.72, 'mechanism': 'resistance_prevention'},
                {'combination': f'{primary_drug} + Compound_C', 'synergy_score': 0.91, 'mechanism': 'enhanced_delivery'}
            ]
            
            return f"Drug combination design for {target_pathway}:\n{json.dumps(combinations, indent=2)}"
        
        # Add tools to agent
        agent.add_tool(screen_compound_library)
        agent.add_tool(predict_admet_properties)
        agent.add_tool(design_drug_combinations)
        
        logger.info("Added drug discovery tools to agent")
    
    def _create_protein_tools(self, agent: PersistentA1):
        """Add protein analysis tools."""
        
        def analyze_protein_structure(pdb_id: str) -> str:
            """Analyze protein structure from PDB."""
            # Simulate structure analysis
            analysis = {
                'pdb_id': pdb_id,
                'resolution_angstrom': 2.1,
                'chain_count': 2,
                'residue_count': 342,
                'secondary_structure': {'alpha_helix': 45, 'beta_sheet': 25, 'loop': 30},
                'binding_sites': [
                    {'site_id': 'ATP_binding', 'residues': ['K72', 'D166', 'N171'], 'volume_cubic_angstrom': 1250},
                    {'site_id': 'allosteric', 'residues': ['F123', 'Y203', 'W245'], 'volume_cubic_angstrom': 890}
                ],
                'druggability_score': 0.78
            }
            
            return f"Protein structure analysis for {pdb_id}:\n{json.dumps(analysis, indent=2)}"
        
        def predict_protein_interactions(protein_sequence: str) -> str:
            """Predict protein-protein interactions."""
            seq_length = len(protein_sequence) if protein_sequence else 300
            
            interactions = [
                {'partner': 'PROT_A', 'confidence': 0.89, 'interaction_type': 'physical', 'binding_region': '45-67'},
                {'partner': 'PROT_B', 'confidence': 0.76, 'interaction_type': 'regulatory', 'binding_region': '123-145'},
                {'partner': 'PROT_C', 'confidence': 0.82, 'interaction_type': 'catalytic', 'binding_region': '200-225'}
            ]
            
            return f"Protein interaction predictions (sequence length: {seq_length}):\n{json.dumps(interactions, indent=2)}"
        
        # Add tools to agent
        agent.add_tool(analyze_protein_structure)
        agent.add_tool(predict_protein_interactions)
        
        logger.info("Added protein analysis tools to agent")
    
    def _create_systems_tools(self, agent: PersistentA1):
        """Add systems biology tools."""
        
        def analyze_pathway_enrichment(gene_list: str, pathway_database: str = "KEGG") -> str:
            """Analyze pathway enrichment for gene list."""
            genes = gene_list.strip().split('\n') if gene_list else []
            gene_count = len([g for g in genes if g.strip()])
            
            pathways = [
                {'pathway': 'DNA repair', 'p_value': 1.2e-5, 'genes_in_pathway': 12, 'enrichment_score': 3.4},
                {'pathway': 'Cell cycle', 'p_value': 3.8e-4, 'genes_in_pathway': 8, 'enrichment_score': 2.1},
                {'pathway': 'Apoptosis', 'p_value': 7.1e-3, 'genes_in_pathway': 6, 'enrichment_score': 1.8}
            ]
            
            return f"Pathway enrichment analysis ({gene_count} genes, {pathway_database}):\n{json.dumps(pathways, indent=2)}"
        
        def model_network_dynamics(network_file: str, perturbation: str = "none") -> str:
            """Model dynamic behavior of biological networks."""
            # Simulate network modeling
            results = {
                'network_nodes': 150,
                'network_edges': 287,
                'perturbation_applied': perturbation,
                'steady_state_reached': True,
                'time_to_steady_state': 45.2,
                'key_oscillators': ['NODE_23', 'NODE_67', 'NODE_101'],
                'robustness_score': 0.73
            }
            
            return f"Network dynamics modeling:\n{json.dumps(results, indent=2)}"
        
        # Add tools to agent
        agent.add_tool(analyze_pathway_enrichment)
        agent.add_tool(model_network_dynamics)
        
        logger.info("Added systems biology tools to agent")
    
    async def _add_common_research_tools(self, agent: PersistentA1):
        """Add common research tools available across all domains."""
        
        def search_literature(query: str, max_results: int = 20) -> str:
            """Search scientific literature for research query."""
            # Simulate literature search
            papers = []
            for i in range(min(max_results, 5)):  # Limit for demo
                papers.append({
                    'title': f'Research paper {i+1} on {query}',
                    'authors': f'Author{i+1}, A. et al.',
                    'journal': ['Nature', 'Science', 'Cell', 'PNAS', 'Nature Medicine'][i % 5],
                    'year': 2024 - i,
                    'pmid': f'PMID{12345000 + i}',
                    'relevance_score': round(0.95 - i*0.1, 2),
                    'abstract': f'This study investigates {query} using novel approaches...'
                })
            
            return f"Literature search results for '{query}':\n{json.dumps(papers, indent=2)}"
        
        def generate_research_hypothesis(background_data: str, research_question: str) -> str:
            """Generate research hypotheses based on background data."""
            hypotheses = [
                {
                    'hypothesis': f'H1: {research_question} is mediated through pathway A',
                    'rationale': 'Based on the background data showing correlation with pathway markers',
                    'testable_predictions': ['Prediction 1', 'Prediction 2'],
                    'required_experiments': ['Experiment A', 'Experiment B'],
                    'feasibility_score': 0.8
                },
                {
                    'hypothesis': f'H2: {research_question} involves epigenetic regulation',
                    'rationale': 'Background data suggests chromatin modifications',
                    'testable_predictions': ['Prediction 3', 'Prediction 4'],
                    'required_experiments': ['ChIP-seq', 'ATAC-seq'],
                    'feasibility_score': 0.6
                }
            ]
            
            return f"Generated research hypotheses:\n{json.dumps(hypotheses, indent=2)}"
        
        def design_experimental_protocol(objective: str, available_resources: str = "standard_lab") -> str:
            """Design experimental protocol for research objective."""
            protocol = {
                'objective': objective,
                'experimental_design': 'randomized_controlled',
                'sample_size_estimation': 'n=30 per group (power=0.8, alpha=0.05)',
                'materials_needed': ['Standard lab equipment', 'Specialized reagent A', 'Instrument B'],
                'timeline_weeks': 12,
                'steps': [
                    '1. Sample preparation and quality control',
                    '2. Primary experimental procedure',
                    '3. Data collection and validation',
                    '4. Statistical analysis',
                    '5. Result interpretation and reporting'
                ],
                'expected_outcomes': ['Outcome A', 'Outcome B'],
                'potential_limitations': ['Limitation 1', 'Limitation 2']
            }
            
            return f"Experimental protocol design:\n{json.dumps(protocol, indent=2)}"
        
        # Add common tools
        agent.add_tool(search_literature)
        agent.add_tool(generate_research_hypothesis)
        agent.add_tool(design_experimental_protocol)
        
        logger.info("Added common research tools to agent")
    
    def _add_genomics_data(self, agent: PersistentA1):
        """Add genomics-specific datasets."""
        genomics_data = {
            "tcga_expression_data.csv": "TCGA gene expression matrices across cancer types",
            "gnomad_variants.vcf": "gnomAD population variant frequencies",
            "gtex_tissue_expression.tsv": "GTEx tissue-specific expression profiles",
            "cosmic_mutations.csv": "COSMIC cancer mutation database",
            "clinvar_variants.xml": "ClinVar clinical variant significance"
        }
        agent.add_data(genomics_data)
    
    def _add_drug_discovery_data(self, agent: PersistentA1):
        """Add drug discovery datasets."""
        drug_data = {
            "chembl_compounds.sdf": "ChEMBL bioactive compound library",
            "drugbank_interactions.xml": "DrugBank drug-target interactions",
            "bindingdb_affinities.csv": "BindingDB binding affinity measurements",
            "admet_training_data.csv": "ADMET property training dataset",
            "clinical_trials_outcomes.json": "Clinical trial efficacy and safety data"
        }
        agent.add_data(drug_data)
    
    def _add_protein_data(self, agent: PersistentA1):
        """Add protein analysis datasets."""
        protein_data = {
            "pdb_structures.mmcif": "Protein Data Bank structure files",
            "uniprot_annotations.xml": "UniProt protein functional annotations",
            "string_interactions.tsv": "STRING protein interaction networks",
            "alphafold_predictions.pdb": "AlphaFold structure predictions",
            "pfam_domains.hmm": "Pfam protein domain models"
        }
        agent.add_data(protein_data)
    
    def _add_systems_data(self, agent: PersistentA1):
        """Add systems biology datasets."""
        systems_data = {
            "kegg_pathways.xml": "KEGG pathway definitions and interactions",
            "reactome_networks.owl": "Reactome biological pathway data",
            "go_annotations.obo": "Gene Ontology functional annotations",
            "omim_phenotypes.txt": "OMIM disease-gene associations",
            "hpo_terms.obo": "Human Phenotype Ontology terms"
        }
        agent.add_data(systems_data)
    
    async def execute_research_task(
        self,
        session_id: str,
        prompt: str,
        stream: bool = True,
        preserve_context: bool = True
    ) -> AsyncGenerator[Dict, None]:
        """Execute research task with enhanced Canvas integration."""
        
        session = self.active_sessions.get(session_id)
        if not session:
            yield {'error': 'Session not found', 'session_id': session_id}
            return
        
        agent = session['agent']
        researcher_id = session['researcher_id']
        
        # Build context from previous interactions if requested
        if preserve_context and session_id in self.research_contexts:
            context_prompt = self._build_context_prompt(session_id, prompt)
        else:
            context_prompt = prompt
        
        # Track execution for Canvas visualization
        execution_tracker = {
            'session_id': session_id,
            'prompt': prompt,
            'start_time': datetime.now(),
            'tools_executed': [],
            'data_accessed': [],
            'key_insights': [],
            'code_generated': [],
            'visualizations_created': [],
            'progress': 0,
            'artifacts': []
        }
        
        interaction_id = f"{session_id}_{int(datetime.now().timestamp())}"
        
        try:
            if stream:
                step_count = 0
                total_output = ""
                
                # Stream execution with enhanced parsing
                async for step in self._stream_agent_execution(agent, context_prompt):
                    step_count += 1
                    
                    # Parse step for Canvas updates
                    canvas_update = self._parse_step_for_canvas(step, execution_tracker)
                    canvas_update.update({
                        'session_id': session_id,
                        'interaction_id': interaction_id,
                        'progress': min(step_count * 3, 95)  # Progress indicator
                    })
                    
                    total_output += step.get('output', '')
                    
                    yield canvas_update
                    
                    # Store important artifacts
                    if canvas_update.get('artifact'):
                        session['artifacts'].append(canvas_update['artifact'])
                        execution_tracker['artifacts'].append(canvas_update['artifact'])
                    
                    if canvas_update.get('insight'):
                        session['insights'].append(canvas_update['insight'])
                        execution_tracker['key_insights'].append(canvas_update['insight'])
                
                # Final result with complete summary
                execution_tracker['end_time'] = datetime.now()
                execution_tracker['total_output'] = total_output
                execution_tracker['execution_time_ms'] = int(
                    (execution_tracker['end_time'] - execution_tracker['start_time']).total_seconds() * 1000
                )
                
                final_result = {
                    'type': 'complete',
                    'session_id': session_id,
                    'interaction_id': interaction_id,
                    'progress': 100,
                    'summary': self._generate_summary(execution_tracker),
                    'artifacts': execution_tracker['artifacts'],
                    'insights': execution_tracker['key_insights'],
                    'tools_used': execution_tracker['tools_executed'],
                    'execution_time_ms': execution_tracker['execution_time_ms'],
                    'agent_state_summary': agent.get_state_summary()
                }
                
                yield final_result
                
                # Update research context
                if preserve_context:
                    self._update_research_context(session_id, prompt, total_output, execution_tracker)
                
                # Save interaction to database
                self._save_interaction_to_db(execution_tracker, total_output)
                
            else:
                # Non-streaming execution
                log, result = agent.go(context_prompt)
                
                execution_tracker.update({
                    'end_time': datetime.now(),
                    'total_output': result,
                    'execution_time_ms': int(
                        (execution_tracker['end_time'] - execution_tracker['start_time']).total_seconds() * 1000
                    )
                })
                
                yield {
                    'type': 'complete',
                    'session_id': session_id,
                    'interaction_id': interaction_id,
                    'result': result,
                    'execution_log': log,
                    'execution_time_ms': execution_tracker['execution_time_ms'],
                    'agent_state_summary': agent.get_state_summary()
                }
                
                # Update context and save
                if preserve_context:
                    self._update_research_context(session_id, prompt, result, execution_tracker)
                
                self._save_interaction_to_db(execution_tracker, result)
        
        except Exception as e:
            logger.error(f"Error executing research task: {e}")
            yield {
                'type': 'error',
                'session_id': session_id,
                'interaction_id': interaction_id,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _build_context_prompt(self, session_id: str, current_prompt: str) -> str:
        """Build context-aware prompt from research history."""
        context_history = self.research_contexts.get(session_id, [])
        
        if not context_history:
            return current_prompt
        
        # Get last 3 interactions for context
        recent_context = context_history[-3:]
        
        context_parts = ["RESEARCH CONTEXT FROM PREVIOUS INTERACTIONS:"]
        for i, ctx in enumerate(recent_context, 1):
            context_parts.append(f"\n{i}. Previous Query: {ctx['prompt']}")
            context_parts.append(f"   Key Findings: {'; '.join(ctx['insights'][:3])}")
            context_parts.append(f"   Tools Used: {', '.join(ctx['tools_used'][:5])}")
        
        context_parts.append(f"\nCURRENT QUERY: {current_prompt}")
        context_parts.append("\nPlease build upon the previous research context while addressing the current query.")
        
        return "\n".join(context_parts)
    
    def _update_research_context(self, session_id: str, prompt: str, output: str, execution_tracker: Dict):
        """Update research context for the session."""
        if session_id not in self.research_contexts:
            self.research_contexts[session_id] = []
        
        context_entry = {
            'timestamp': datetime.now().isoformat(),
            'prompt': prompt,
            'output_summary': output[:500] + "..." if len(output) > 500 else output,
            'insights': execution_tracker['key_insights'],
            'tools_used': execution_tracker['tools_executed'],
            'artifacts_created': len(execution_tracker['artifacts'])
        }
        
        self.research_contexts[session_id].append(context_entry)
        
        # Keep only last 10 interactions to manage memory
        if len(self.research_contexts[session_id]) > 10:
            self.research_contexts[session_id] = self.research_contexts[session_id][-10:]
    
    async def _stream_agent_execution(self, agent: PersistentA1, prompt: str):
        """Stream agent execution steps with error handling."""
        try:
            for step in agent.go_stream(prompt):
                yield step
                await asyncio.sleep(0)  # Allow other async operations
        except Exception as e:
            logger.error(f"Error in agent streaming: {e}")
            yield {
                'type': 'error',
                'output': f"Agent execution error: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }
    
    def _parse_step_for_canvas(self, step: Dict, tracker: Dict) -> Dict:
        """Enhanced step parsing for Canvas visualization."""
        canvas_update = {
            'type': 'step',
            'timestamp': datetime.now().isoformat(),
            'content': step.get('output', ''),
            'step_type': step.get('type', 'unknown')
        }
        
        output = step.get('output', '')
        
        # Enhanced tool detection
        if 'tool' in step or any(keyword in output.lower() for keyword in ['calling', 'executing', 'using tool']):
            tool_name = step.get('tool', self._extract_tool_name(output))
            if tool_name:
                tracker['tools_executed'].append(tool_name)
                canvas_update['tool_execution'] = {
                    'name': tool_name,
                    'category': self._categorize_tool(tool_name),
                    'status': 'executing',
                    'timestamp': canvas_update['timestamp']
                }
        
        # Enhanced code detection
        code_blocks = self._extract_code_blocks(output)
        for code_block in code_blocks:
            tracker['code_generated'].append(code_block)
            canvas_update['artifact'] = {
                'type': 'code',
                'language': code_block.get('language', 'python'),
                'content': code_block['content'],
                'description': 'Generated code',
                'id': f"code_{len(tracker['code_generated'])}"
            }
        
        # Enhanced insight detection
        insights = self._extract_insights(output)
        for insight in insights:
            tracker['key_insights'].append(insight)
            canvas_update['insight'] = {
                'content': insight,
                'type': 'discovery',
                'confidence': self._assess_insight_confidence(insight),
                'timestamp': canvas_update['timestamp']
            }
        
        # Data access detection
        data_refs = self._extract_data_references(output)
        for data_ref in data_refs:
            tracker['data_accessed'].append(data_ref)
            canvas_update['data_access'] = {
                'dataset': data_ref,
                'access_type': 'query',
                'timestamp': canvas_update['timestamp']
            }
        
        # Visualization detection
        if any(viz_keyword in output.lower() for viz_keyword in ['plot', 'chart', 'graph', 'visualization', 'figure']):
            viz_info = self._extract_visualization_info(output)
            if viz_info:
                tracker['visualizations_created'].append(viz_info)
                canvas_update['visualization'] = viz_info
        
        return canvas_update
    
    def _extract_tool_name(self, text: str) -> Optional[str]:
        """Extract tool name from execution text."""
        import re
        
        # Look for tool execution patterns
        patterns = [
            r'calling\s+(\w+)',
            r'executing\s+(\w+)',
            r'using\s+tool\s+(\w+)',
            r'tool:\s*(\w+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_code_blocks(self, text: str) -> List[Dict]:
        """Extract code blocks from text."""
        import re
        
        code_blocks = []
        
        # Match code blocks with language specification
        pattern = r'```(\w+)?\n(.*?)\n```'
        matches = re.findall(pattern, text, re.DOTALL)
        
        for language, content in matches:
            code_blocks.append({
                'language': language or 'text',
                'content': content.strip()
            })
        
        return code_blocks
    
    def _extract_insights(self, text: str) -> List[str]:
        """Extract key insights from text."""
        insights = []
        
        # Look for insight indicators
        insight_patterns = [
            r'(?:found|discovered|identified|revealed|shows?|indicates?|suggests?)\s+(.+?)\.', 
            r'(?:key finding|important|notably|significantly)\s*:?\s*(.+?)\.', 
            r'(?:conclusion|result|outcome)\s*:?\s*(.+?)\.'
        ]
        
        import re
        for pattern in insight_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match.strip()) > 10:  # Filter short matches
                    insights.append(match.strip())
        
        return insights[:3]  # Limit to top 3 insights per step
    
    def _assess_insight_confidence(self, insight: str) -> float:
        """Assess confidence level of an insight."""
        # Simple heuristic based on language
        high_confidence_words = ['confirmed', 'demonstrated', 'proved', 'significant']
        medium_confidence_words = ['suggests', 'indicates', 'appears', 'likely']
        low_confidence_words = ['might', 'could', 'possibly', 'potentially']
        
        insight_lower = insight.lower()
        
        if any(word in insight_lower for word in high_confidence_words):
            return 0.9
        elif any(word in insight_lower for word in medium_confidence_words):
            return 0.7
        elif any(word in insight_lower for word in low_confidence_words):
            return 0.5
        else:
            return 0.6  # Default medium confidence
    
    def _extract_data_references(self, text: str) -> List[str]:
        """Extract data references from text."""
        import re
        
        data_patterns = [
            r'(\w+\.(?:csv|json|xml|tsv|parquet|vcf|sdf|pdb|mmcif))',
            r'(?:dataset|database|data)\s+(\w+)',
            r'(?:from|using|accessing)\s+(\w+(?:_\w+)*)'
        ]
        
        data_refs = []
        for pattern in data_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            data_refs.extend(matches)
        
        return list(set(data_refs))  # Remove duplicates
    
    def _extract_visualization_info(self, text: str) -> Optional[Dict]:
        """Extract visualization information from text."""
        viz_types = ['scatter', 'bar', 'line', 'heatmap', 'histogram', 'boxplot', 'violin']
        
        text_lower = text.lower()
        for viz_type in viz_types:
            if viz_type in text_lower:
                return {
                    'type': viz_type,
                    'description': f'{viz_type.title()} visualization',
                    'timestamp': datetime.now().isoformat()
                }
        
        # Generic visualization
        if any(word in text_lower for word in ['plot', 'chart', 'graph', 'figure']):
            return {
                'type': 'generic',
                'description': 'Data visualization',
                'timestamp': datetime.now().isoformat()
            }
        
        return None
    
    def _categorize_tool(self, tool_name: str) -> str:
        """Enhanced tool categorization."""
        categories = {
            'query_': 'Database Query',
            'analyze_': 'Analysis',
            'predict_': 'Prediction',
            'design_': 'Design',
            'screen_': 'Screening',
            'blast_': 'Sequence Analysis',
            'search_': 'Literature Search',
            'generate_': 'Generation',
            'model_': 'Modeling',
            'identify_': 'Identification',
            'perform_': 'Analysis'
        }
        
        tool_lower = tool_name.lower()
        for prefix, category in categories.items():
            if tool_lower.startswith(prefix):
                return category
        
        # Domain-specific categorization
        if any(word in tool_lower for word in ['gene', 'genomic', 'variant', 'gwas']):
            return 'Genomics'
        elif any(word in tool_lower for word in ['drug', 'compound', 'admet', 'screen']):
            return 'Drug Discovery'
        elif any(word in tool_lower for word in ['protein', 'structure', 'pdb']):
            return 'Protein Analysis'
        elif any(word in tool_lower for word in ['pathway', 'network', 'systems']):
            return 'Systems Biology'
        
        return 'General'
    
    def _generate_summary(self, tracker: Dict) -> Dict:
        """Generate comprehensive execution summary for Canvas."""
        return {
            'execution_time_ms': tracker.get('execution_time_ms', 0),
            'tools_used': len(tracker['tools_executed']),
            'unique_tools': len(set(tracker['tools_executed'])),
            'tool_list': list(set(tracker['tools_executed'])),
            'insights_found': len(tracker['key_insights']),
            'insights_summary': tracker['key_insights'][:5],
            'code_artifacts': len(tracker['code_generated']),
            'visualizations': len(tracker['visualizations_created']),
            'data_sources_accessed': len(set(tracker['data_accessed'])),
            'data_sources': list(set(tracker['data_accessed'])),
            'total_artifacts': len(tracker['artifacts'])
        }
    
    def _save_session_to_db(self, session_data: Dict):
        """Save session data to database."""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO canvas_sessions
                (session_id, researcher_id, username, agent_id, session_metadata, research_context)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                session_data['session_id'],
                session_data['researcher_id'],
                session_data['username'],
                session_data['agent_id'],
                json.dumps({
                    'research_domain': session_data['research_domain'],
                    'start_time': session_data['start_time'].isoformat()
                }),
                json.dumps(session_data.get('research_context', {}))
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving session to database: {e}")
    
    def _save_interaction_to_db(self, execution_tracker: Dict, response: str):
        """Save research interaction to database."""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO research_interactions
                (interaction_id, session_id, researcher_id, prompt, response, 
                 tools_used, artifacts_generated, insights_discovered, execution_time_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                f"{execution_tracker['session_id']}_{int(execution_tracker['start_time'].timestamp())}",
                execution_tracker['session_id'],
                execution_tracker.get('researcher_id', ''),
                execution_tracker['prompt'],
                response,
                json.dumps(execution_tracker['tools_executed']),
                json.dumps(execution_tracker['artifacts']),
                json.dumps(execution_tracker['key_insights']),
                execution_tracker.get('execution_time_ms', 0)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error saving interaction to database: {e}")
    
    def _get_canvas_config(self, researcher_id: str, research_domain: str) -> Dict:
        """Get enhanced Canvas configuration for researcher."""
        base_config = {
            'panels': [
                {'id': 'research_progress', 'enabled': True, 'position': 'right'},
                {'id': 'insights', 'enabled': True, 'position': 'bottom'},
                {'id': 'code_editor', 'enabled': True, 'position': 'center'},
                {'id': 'data_browser', 'enabled': True, 'position': 'left'},
                {'id': 'agent_state', 'enabled': True, 'position': 'right'}
            ],
            'theme': 'light',
            'auto_save': True,
            'stream_updates': True,
            'context_preservation': True
        }
        
        # Domain-specific panel configurations
        domain_configs = {
            'genomics': {
                'additional_panels': [
                    {'id': 'variant_browser', 'enabled': True, 'position': 'left'},
                    {'id': 'pathway_view', 'enabled': True, 'position': 'bottom'}
                ],
                'default_tools': ['analyze_gene_expression_data', 'identify_variant_effects']
            },
            'drug_discovery': {
                'additional_panels': [
                    {'id': 'compound_library', 'enabled': True, 'position': 'left'},
                    {'id': 'admet_dashboard', 'enabled': True, 'position': 'bottom'}
                ],
                'default_tools': ['screen_compound_library', 'predict_admet_properties']
            },
            'protein_analysis': {
                'additional_panels': [
                    {'id': 'structure_viewer', 'enabled': True, 'position': 'center'},
                    {'id': 'interaction_network', 'enabled': True, 'position': 'bottom'}
                ],
                'default_tools': ['analyze_protein_structure', 'predict_protein_interactions']
            }
        }
        
        if research_domain in domain_configs:
            domain_config = domain_configs[research_domain]
            base_config['panels'].extend(domain_config.get('additional_panels', []))
            base_config['default_tools'] = domain_config.get('default_tools', [])
        
        return base_config
    
    # Additional Canvas integration methods
    
    async def get_session_summary(self, session_id: str) -> Optional[Dict]:
        """Get comprehensive session summary."""
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        agent = session['agent']
        
        return {
            'session_id': session_id,
            'researcher_id': session['researcher_id'],
            'username': session['username'],
            'research_domain': session['research_domain'],
            'start_time': session['start_time'].isoformat(),
            'duration_minutes': (datetime.now() - session['start_time']).total_seconds() / 60,
            'interactions_count': len(self.research_contexts.get(session_id, [])),
            'total_artifacts': len(session['artifacts']),
            'total_insights': len(session['insights']),
            'agent_state': agent.get_state_summary(),
            'recent_context': self.research_contexts.get(session_id, [])[-3:]
        }
    
    async def add_custom_tool_to_session(self, session_id: str, tool_code: str, tool_name: str) -> Dict:
        """Add custom tool to session agent."""
        if session_id not in self.active_sessions:
            return {'error': 'Session not found'}
        
        try:
            agent = self.active_sessions[session_id]['agent']
            
            # Execute tool code in controlled environment
            exec_globals = {}
            exec(tool_code, exec_globals)
            
            # Find the function in executed code
            tool_func = None
            for name, obj in exec_globals.items():
                if callable(obj) and (name == tool_name or not tool_name):
                    tool_func = obj
                    tool_name = name
                    break
            
            if tool_func:
                agent.add_tool(tool_func)
                return {
                    'status': 'success',
                    'tool_name': tool_name,
                    'message': f'Added custom tool: {tool_name}'
                }
            else:
                return {'error': 'No callable function found in code'}
        
        except Exception as e:
            logger.error(f"Error adding custom tool: {e}")
            return {'error': str(e)}
    
    async def clone_session_agent(self, source_session_id: str, target_researcher_id: str) -> Dict:
        """Clone agent from one session for use by another researcher."""
        if source_session_id not in self.active_sessions:
            return {'error': 'Source session not found'}
        
        try:
            source_session = self.active_sessions[source_session_id]
            source_agent_id = source_session['agent_id']
            
            # Create target agent ID
            target_agent_id = f"{target_researcher_id}_cloned_from_{source_agent_id}"
            
            # Clone agent
            cloned_agent = self.agent_manager.clone_agent(source_agent_id, target_agent_id)
            
            return {
                'status': 'success',
                'cloned_agent_id': target_agent_id,
                'source_agent_id': source_agent_id,
                'tools_cloned': len(cloned_agent.list_custom_tools()),
                'data_cloned': len(cloned_agent.list_custom_data())
            }
        
        except Exception as e:
            logger.error(f"Error cloning session agent: {e}")
            return {'error': str(e)}
    
    async def export_session_state(self, session_id: str, export_path: str) -> Dict:
        """Export complete session state for sharing."""
        if session_id not in self.active_sessions:
            return {'error': 'Session not found'}
        
        try:
            session = self.active_sessions[session_id]
            agent = session['agent']
            
            # Export agent state
            agent.export_state(export_path)
            
            # Add session metadata
            session_metadata = {
                'session_info': {
                    'session_id': session_id,
                    'researcher_id': session['researcher_id'],
                    'research_domain': session['research_domain'],
                    'export_timestamp': datetime.now().isoformat()
                },
                'research_context': self.research_contexts.get(session_id, []),
                'session_summary': await self.get_session_summary(session_id)
            }
            
            # Save session metadata alongside agent state
            metadata_path = export_path.replace('.json', '_session_metadata.json')
            with open(metadata_path, 'w') as f:
                json.dump(session_metadata, f, indent=2)
            
            return {
                'status': 'success',
                'agent_state_file': export_path,
                'session_metadata_file': metadata_path,
                'export_size_kb': Path(export_path).stat().st_size / 1024
            }
        
        except Exception as e:
            logger.error(f"Error exporting session state: {e}")
            return {'error': str(e)}
