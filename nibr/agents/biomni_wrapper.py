#!/usr/bin/env python3
"""
Biomni Local Mount Wrapper
This wrapper extends the A1 agent to skip S3 downloads when data is pre-mounted locally.
Perfect for Docker containers with volume-mounted data lakes.
"""

import os
import sys
from typing import Optional, Union
from biomni.agent import A1


class A1LocalMount(A1):
    """
    Extended A1 agent that uses locally mounted data instead of downloading from S3.
    
    This class is designed for containerized deployments where the data lake
    is mounted as a volume from the host filesystem.
    """
    
    def __init__(
        self,
        path: str = "./",
        llm: Optional[str] = None,
        use_tool_retriever: bool = True,
        timeout_seconds: int = 600,
        source: Optional[str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        skip_download: bool = True,
        validate_data: bool = True
    ):
        """
        Initialize A1 agent with local mount support.
        
        Args:
            path: Base path for biomni data (default: "./")
            llm: LLM model to use
            use_tool_retriever: Whether to use tool retriever
            timeout_seconds: Timeout for operations
            source: LLM source
            base_url: Base URL for LLM API
            api_key: API key for LLM
            skip_download: Skip S3 download check (default: True)
            validate_data: Validate that required data files exist (default: True)
        """
        
        # Check if we should skip downloads (from env or parameter)
        self.skip_download = skip_download or os.environ.get('BIOMNI_SKIP_DOWNLOAD', 'false').lower() == 'true'
        
        if self.skip_download:
            print("[LocalMount] Skipping S3 download - using pre-mounted data")
            
            # Set up paths - check for environment variable or use default
            biomni_data_path = os.environ.get('BIOMNI_DATA_PATH', '/biomni_data')
            
            # If path is absolute and exists, use it; otherwise join with provided path
            if os.path.isabs(biomni_data_path) and os.path.exists(biomni_data_path):
                biomni_data_dir = biomni_data_path
            else:
                biomni_data_dir = os.path.join(path, "biomni_data")
            
            data_lake_dir = os.path.join(biomni_data_dir, "data_lake")
            benchmark_dir = os.path.join(biomni_data_dir, "benchmark")
            
            # Create directories if they don't exist
            os.makedirs(biomni_data_dir, exist_ok=True)
            os.makedirs(data_lake_dir, exist_ok=True)
            os.makedirs(benchmark_dir, exist_ok=True)
            
            # Validate data if requested
            if validate_data:
                self._validate_mounted_data(data_lake_dir, benchmark_dir)
            
            # Override the check_and_download_s3_files function temporarily
            import biomni.utils
            original_check_download = biomni.utils.check_and_download_s3_files
            
            def skip_download_stub(*args, **kwargs):
                """Stub function that skips downloads"""
                print("[LocalMount] Data download skipped - using mounted volumes")
                return {}
            
            # Temporarily replace the download function
            biomni.utils.check_and_download_s3_files = skip_download_stub
            
            try:
                # Initialize parent class
                super().__init__(
                    path=path,
                    llm=llm,
                    use_tool_retriever=use_tool_retriever,
                    timeout_seconds=timeout_seconds,
                    source=source,
                    base_url=base_url,
                    api_key=api_key
                )
            finally:
                # Restore original function
                biomni.utils.check_and_download_s3_files = original_check_download
        else:
            # Normal initialization with S3 download
            super().__init__(
                path=path,
                llm=llm,
                use_tool_retriever=use_tool_retriever,
                timeout_seconds=timeout_seconds,
                source=source,
                base_url=base_url,
                api_key=api_key
            )
    
    def _validate_mounted_data(self, data_lake_dir: str, benchmark_dir: str):
        """
        Validate that essential data files are present in mounted volumes.
        
        Args:
            data_lake_dir: Path to data lake directory
            benchmark_dir: Path to benchmark directory
        """
        # Check for some essential files (not all 79, just key ones)
        essential_files = [
            "gene_info.parquet",
            "DisGeNET.parquet",
            "kg.csv",  # Knowledge graph
            "gtex_tissue_gene_tpm.parquet"
        ]
        
        missing_files = []
        for file in essential_files:
            file_path = os.path.join(data_lake_dir, file)
            if not os.path.exists(file_path):
                missing_files.append(file)
        
        if missing_files:
            print(f"[LocalMount] Warning: Some essential files are missing: {missing_files}")
            print("[LocalMount] You may need to run ./download-data-lake.sh first")
        else:
            print("[LocalMount] ✓ Essential data files validated")
        
        # Check benchmark directory
        benchmark_hle = os.path.join(benchmark_dir, "hle")
        if not os.path.exists(benchmark_hle):
            print("[LocalMount] Warning: Benchmark data not found at", benchmark_hle)
        else:
            print("[LocalMount] ✓ Benchmark data validated")
        
        # Count total files
        if os.path.exists(data_lake_dir):
            file_count = len([f for f in os.listdir(data_lake_dir) if os.path.isfile(os.path.join(data_lake_dir, f))])
            print(f"[LocalMount] Found {file_count} files in data lake")
            
            if file_count < 70:
                print(f"[LocalMount] Warning: Expected ~79 files but found only {file_count}")
                print("[LocalMount] Some functionality may be limited")


def main():
    """
    Example usage of A1LocalMount agent.
    """
    import os
    
    # Set environment to skip downloads
    os.environ['BIOMNI_SKIP_DOWNLOAD'] = 'true'
    
    # Initialize agent with local mount
    print("Initializing Biomni with local data mount...")
    agent = A1LocalMount(
        path="./",
        skip_download=True,
        validate_data=True
    )
    
    print("\nBiomni agent initialized successfully!")
    print("Data is being read from local mounted volumes.")
    
    # Example: Run a simple query
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        print(f"\nProcessing query: {query}")
        result = agent.run(query)
        print(f"\nResult: {result}")
    else:
        print("\nAgent ready. You can now use it for biomedical queries.")
        print("Example: python biomni_local_mount.py 'What genes are associated with Alzheimer disease?'")


if __name__ == "__main__":
    main()