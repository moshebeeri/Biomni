#!/bin/bash

# Biomni Data Lake Download Script
# Downloads the 11GB data lake from Biomni S3 to local Mac filesystem
# Supports resume on interruption

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
S3_BASE_URL="https://biomni-release.s3.amazonaws.com"
LOCAL_DATA_DIR="../../data/data_lake"
BENCHMARK_DIR="../../data/benchmark"
TOTAL_SIZE="11GB"

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_progress() {
    echo -e "${BLUE}[PROGRESS]${NC} $1"
}

# Function to download a file with curl (supports resume)
download_file() {
    local url=$1
    local output_file=$2
    local description=$3
    
    if [ -f "$output_file" ]; then
        # File exists, check if complete
        local remote_size=$(curl -sI "$url" | grep -i Content-Length | awk '{print $2}' | tr -d '\r')
        local local_size=$(stat -f%z "$output_file" 2>/dev/null || stat --format=%s "$output_file" 2>/dev/null || echo "0")
        
        if [ "$remote_size" = "$local_size" ]; then
            print_info "✓ $description already downloaded"
            return 0
        else
            print_warning "Resuming partial download of $description"
        fi
    else
        print_progress "Downloading $description"
    fi
    
    # Download with resume support
    curl -L -C - --progress-bar -o "$output_file" "$url" || {
        print_error "Failed to download $description"
        return 1
    }
    
    print_info "✓ Downloaded $description"
}

# Create directories
print_info "Creating data directories..."
mkdir -p "$LOCAL_DATA_DIR"
mkdir -p "$BENCHMARK_DIR"

# List of all 79 data files from env_desc.py
declare -a DATA_FILES=(
    "affinity_capture-ms.parquet"
    "affinity_capture-rna.parquet"
    "BindingDB_All_202409.tsv"
    "broad_repurposing_hub_molecule_with_smiles.parquet"
    "broad_repurposing_hub_phase_moa_target_info.parquet"
    "co-fractionation.parquet"
    "czi_census_datasets_v4.parquet"
    "DepMap_CRISPRGeneDependency.csv"
    "DepMap_CRISPRGeneEffect.csv"
    "DepMap_Model.csv"
    "DepMap_OmicsExpressionProteinCodingGenesTPMLogp1.csv"
    "ddinter_alimentary_tract_metabolism.csv"
    "ddinter_antineoplastic.csv"
    "ddinter_antiparasitic.csv"
    "ddinter_blood_organs.csv"
    "ddinter_dermatological.csv"
    "ddinter_hormonal.csv"
    "ddinter_respiratory.csv"
    "ddinter_various.csv"
    "DisGeNET.parquet"
    "dosage_growth_defect.parquet"
    "enamine_cloud_library_smiles.pkl"
    "evebio_assay_table.csv"
    "evebio_bundle_table.csv"
    "evebio_compound_table.csv"
    "evebio_control_table.csv"
    "evebio_detailed_result_table.csv"
    "evebio_observed_points_table.csv"
    "evebio_summary_result_table.csv"
    "evebio_target_table.csv"
    "genebass_missense_LC_filtered.pkl"
    "genebass_pLoF_filtered.pkl"
    "genebass_synonymous_filtered.pkl"
    "gene_info.parquet"
    "genetic_interaction.parquet"
    "go-plus.json"
    "gtex_tissue_gene_tpm.parquet"
    "gwas_catalog.pkl"
    "hp.obo"
    "kg.csv"
    "marker_celltype.parquet"
    "McPAS-TCR.parquet"
    "miRDB_v6.0_results.parquet"
    "miRTarBase_microRNA_target_interaction.parquet"
    "miRTarBase_microRNA_target_interaction_pubmed_abtract.txt"
    "miRTarBase_MicroRNA_Target_Sites.parquet"
    "mousemine_m1_positional_geneset.parquet"
    "mousemine_m2_curated_geneset.parquet"
    "mousemine_m3_regulatory_target_geneset.parquet"
    "mousemine_m5_ontology_geneset.parquet"
    "mousemine_m8_celltype_signature_geneset.parquet"
    "mousemine_mh_hallmark_geneset.parquet"
    "msigdb_human_c1_positional_geneset.parquet"
    "msigdb_human_c2_curated_geneset.parquet"
    "msigdb_human_c3_regulatory_target_geneset.parquet"
    "msigdb_human_c3_subset_transcription_factor_targets_from_GTRD.parquet"
    "msigdb_human_c4_computational_geneset.parquet"
    "msigdb_human_c5_ontology_geneset.parquet"
    "msigdb_human_c6_oncogenic_signature_geneset.parquet"
    "msigdb_human_c7_immunologic_signature_geneset.parquet"
    "msigdb_human_c8_celltype_signature_geneset.parquet"
    "msigdb_human_h_hallmark_geneset.parquet"
    "omim.parquet"
    "proteinatlas.tsv"
    "proximity_label-ms.parquet"
    "reconstituted_complex.parquet"
    "sgRNA_KO_SP_mouse.txt"
    "sgRNA_KO_SP_human.txt"
    "synthetic_growth_defect.parquet"
    "synthetic_lethality.parquet"
    "synthetic_rescue.parquet"
    "two-hybrid.parquet"
    "variant_table.parquet"
    "Virus-Host_PPI_P-HIPSTER_2020.parquet"
    "txgnn_name_mapping.pkl"
    "txgnn_prediction.pkl"
)

# Download progress tracking
TOTAL_FILES=${#DATA_FILES[@]}
CURRENT=0

print_info "Starting download of $TOTAL_FILES data lake files (~$TOTAL_SIZE total)"
print_info "Files will be saved to: $LOCAL_DATA_DIR"
echo ""

# Download each file
for file in "${DATA_FILES[@]}"; do
    CURRENT=$((CURRENT + 1))
    print_progress "[$CURRENT/$TOTAL_FILES] Processing $file"
    
    download_file \
        "$S3_BASE_URL/data_lake/$file" \
        "$LOCAL_DATA_DIR/$file" \
        "$file"
done

echo ""
print_info "Downloading benchmark data..."

# Download benchmark files (structure: benchmark/hle/*)
# First, try to download the benchmark zip if available
if curl -f -I "$S3_BASE_URL/benchmark.zip" >/dev/null 2>&1; then
    print_info "Downloading benchmark.zip..."
    download_file \
        "$S3_BASE_URL/benchmark.zip" \
        "$BENCHMARK_DIR/benchmark.zip" \
        "benchmark.zip"
    
    # Extract if downloaded
    if [ -f "$BENCHMARK_DIR/benchmark.zip" ]; then
        print_info "Extracting benchmark data..."
        unzip -q -o "$BENCHMARK_DIR/benchmark.zip" -d "$BENCHMARK_DIR"
        rm "$BENCHMARK_DIR/benchmark.zip"
    fi
else
    # Try to download individual benchmark files
    print_warning "benchmark.zip not found, attempting to download benchmark/hle directory..."
    mkdir -p "$BENCHMARK_DIR/hle"
    
    # Common benchmark files (you may need to adjust based on actual structure)
    BENCHMARK_FILES=(
        "hle/test_data.parquet"
        "hle/ground_truth.parquet"
    )
    
    for file in "${BENCHMARK_FILES[@]}"; do
        if curl -f -I "$S3_BASE_URL/benchmark/$file" >/dev/null 2>&1; then
            download_file \
                "$S3_BASE_URL/benchmark/$file" \
                "$BENCHMARK_DIR/$file" \
                "benchmark/$file"
        fi
    done
fi

echo ""
print_info "================== Download Summary =================="
print_info "✓ Data lake files downloaded to: $LOCAL_DATA_DIR"
print_info "✓ Benchmark files downloaded to: $BENCHMARK_DIR"

# Calculate actual size
if command -v du &> /dev/null; then
    DATA_SIZE=$(du -sh "$LOCAL_DATA_DIR" 2>/dev/null | cut -f1)
    print_info "✓ Total data lake size: $DATA_SIZE"
fi

# Count downloaded files
FILE_COUNT=$(find "$LOCAL_DATA_DIR" -type f | wc -l | tr -d ' ')
print_info "✓ Total files downloaded: $FILE_COUNT"

echo ""
print_info "====================================================="
print_info "Data download complete!"
print_info ""
print_info "Next steps:"
print_info "1. The data is now stored locally at: $(pwd)/data/"
print_info "2. Run Docker container with: docker-compose -f docker-compose-tier1-2.yml up"
print_info "3. The container will mount this data automatically"
print_info ""
print_info "Note: This data will be reused for all future container runs."
print_info "No need to download again unless you delete the data directory."

exit 0