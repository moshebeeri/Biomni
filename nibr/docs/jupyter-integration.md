# Jupyter Integration in Biomni Container

## Overview

Jupyter Lab is now integrated directly into the biomni-agent container, providing researchers with immediate access to Python and R environments alongside the Biomni agent capabilities.

## Architecture Changes

### Previous Setup (Removed)
- Separate `biomni-jupyter` container
- Duplicate dependencies and data mounts
- Additional resource overhead
- Complex orchestration with two containers

### New Setup (Integrated)
- Jupyter runs inside `biomni-agent` container
- Shared environment and dependencies
- Single container for both agent and research
- Simplified deployment and management

## Access Information

- **URL**: http://localhost:8888?token=biomni
- **Default Token**: `biomni`
- **Port**: 8888
- **Notebook Directory**: `/biomni_data/notebooks`

## Features

### Integrated Environment
- Direct access to Biomni agent from notebooks
- Shared data lake and results
- No network latency between Jupyter and agent
- Consistent Python environment

### Pre-installed Packages
- **Core**: jupyter, jupyterlab, ipython, notebook
- **Visualization**: matplotlib, seaborn, plotly
- **Widgets**: ipywidgets, nbformat
- **Biomni**: Full biomni package with all tools

### Mounted Directories
```
/biomni_data/
├── notebooks/          # Working directory for notebooks
│   ├── tutorials/      # Biomni tutorials (read-only)
│   └── nibr/          # NIBR-specific notebooks
├── data_lake/         # Biomedical datasets (read-only)
├── cache/             # Agent cache
├── results/           # Analysis results
└── logs/              # Application logs
```

## Configuration

### Environment Variables
```bash
ENABLE_JUPYTER=true     # Enable Jupyter (default: true)
JUPYTER_TOKEN=biomni    # Access token (default: biomni)
```

### Docker Compose Settings
```yaml
biomni-agent:
  environment:
    - ENABLE_JUPYTER=${ENABLE_JUPYTER:-true}
    - JUPYTER_TOKEN=${JUPYTER_TOKEN:-biomni}
  ports:
    - "8888:8888"  # Jupyter port
  volumes:
    - biomni-notebooks:/biomni_data/notebooks
    - ../tutorials:/biomni_data/notebooks/tutorials:ro
    - ./notebooks:/biomni_data/notebooks/nibr
```

## Usage Examples

### Accessing Biomni from Jupyter

```python
# In a Jupyter notebook
from biomni_local_mount import A1LocalMount

# Initialize agent (data already mounted)
agent = A1LocalMount(
    path="/",
    skip_download=True,
    llm="gpt-4"
)

# Run biomedical queries
result = agent.run("Analyze gene expression patterns in GTEx data")
print(result)
```

### Exploring Data Lake

```python
import pandas as pd
import os

# List available datasets
data_path = "/biomni_data/data_lake"
datasets = os.listdir(data_path)
print(f"Available datasets: {len(datasets)}")

# Load a specific dataset
disgenet = pd.read_parquet(f"{data_path}/DisGeNET.parquet")
print(f"DisGeNET shape: {disgenet.shape}")
```

### Visualization Example

```python
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

# Create visualizations using the integrated libraries
# Data is directly accessible from /biomni_data/
```

## Benefits of Integration

1. **Resource Efficiency**
   - Single container reduces memory overhead
   - Shared Python environment and packages
   - No duplicate data mounts

2. **Simplified Management**
   - One container to start/stop/rebuild
   - Unified logging and monitoring
   - Single health check endpoint

3. **Better Performance**
   - No network latency between Jupyter and agent
   - Direct file system access
   - Shared cache and results

4. **Researcher-Friendly**
   - Immediate access to both tools
   - Consistent environment
   - Pre-configured with all dependencies

## Troubleshooting

### Jupyter Not Starting
Check if Jupyter is enabled:
```bash
docker exec biomni-agent env | grep JUPYTER
```

### Token Issues
View the token in logs:
```bash
docker logs biomni-agent | grep token
```

### Port Conflicts
Check if port 8888 is in use:
```bash
lsof -i :8888
```

## Migration from Separate Container

If you were using the separate `biomni-jupyter` container:

1. Stop and remove old container:
   ```bash
   docker stop biomni-jupyter
   docker rm biomni-jupyter
   ```

2. Rebuild biomni-agent with integrated Jupyter:
   ```bash
   ./rebuild-containers.sh --biomni --start
   ```

3. Access Jupyter at the same URL:
   http://localhost:8888?token=biomni

## Security Considerations

- Jupyter runs with the same privileges as the biomni agent
- Token authentication is enabled by default
- Consider using stronger tokens in production
- Restrict network access in production deployments