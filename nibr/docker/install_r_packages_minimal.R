#!/usr/bin/env Rscript

# Minimal R package installation - only essentials
# This is much faster than the full installation

cat("Installing minimal R packages for Biomni...\n")

# Set repository and timeout
options(repos = c(CRAN = "https://cran.rstudio.com/"))
options(timeout = 300)  # 5 minute timeout per package

# Only install the most essential packages
essential_packages <- c(
  "ggplot2",
  "dplyr",
  "tidyr"
)

for (pkg in essential_packages) {
  if (!require(pkg, character.only = TRUE, quietly = TRUE)) {
    cat(sprintf("Installing %s...\n", pkg))
    tryCatch({
      install.packages(pkg, dependencies = FALSE, quiet = TRUE)
      cat(sprintf("✓ Installed %s\n", pkg))
    }, error = function(e) {
      cat(sprintf("✗ Failed to install %s: %s\n", pkg, e$message))
    })
  } else {
    cat(sprintf("✓ %s already installed\n", pkg))
  }
}

cat("\nMinimal R package installation complete!\n")
cat("Note: Advanced R-based tools may not work without full package installation.\n")