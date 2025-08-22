import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Eye, Code2, FileText, Table, GitBranch, Database, FileJson, Dna, FlaskConical, Activity } from "lucide-react";
import { cn } from "@/lib/utils";
import { ArtifactCodeV3, ArtifactMarkdownV3 } from "@opencanvas/shared/types";
import { HTMLPreview } from "../HTMLPreview";
import { JupyterPreview } from "./JupyterPreview";
import { TablePreview } from "./TablePreview";
import { MarkdownPreview } from "./MarkdownPreview";
import { PythonPreview } from "./PythonPreview";
import { TreePreview } from "./TreePreview";
import { BiomedicalPreviewManager } from "./BiomedicalPreviewManager";
import { ProteinViewer } from "./ProteinViewer";
import { PharmacophoreViewer } from "./PharmacophoreViewer";
import { PhylogeneticTreeViewer } from "./PhylogeneticTreeViewer";

export type PreviewType = "html" | "jupyter" | "table" | "markdown" | "python" | "r" | "json" | "tree" | "protein" | "pharmacophore" | "phylogenetic" | "none";

interface PreviewManagerProps {
  artifact: ArtifactCodeV3 | ArtifactMarkdownV3;
  isHovering: boolean;
  editorRef?: any;
}

export function PreviewManager({ artifact, isHovering, editorRef }: PreviewManagerProps) {
  const [showPreview, setShowPreview] = useState(false);
  const [previewType, setPreviewType] = useState<PreviewType>("none");

  useEffect(() => {
    // Detect preview type based on content
    const detectPreviewType = (): PreviewType => {
      if (artifact.type === "text") {
        return "markdown";
      }
      
      if (artifact.type === "code") {
        const { language, code } = artifact;
        
        // Check for Jupyter notebook JSON structure
        if (language === "json" && code.includes('"cells"') && code.includes('"nbformat"')) {
          return "jupyter";
        }
        
        // Check for PDB protein structure
        if (code.includes("ATOM") && code.includes("HELIX") || code.includes("SHEET")) {
          return "protein";
        }
        
        // Check for pharmacophore data
        if (code.toUpperCase().includes("HBD") || code.toUpperCase().includes("HBA") || 
            code.toUpperCase().includes("PHARMACOPHORE")) {
          return "pharmacophore";
        }
        
        // Check for phylogenetic tree (Newick format)
        if (code.includes("(") && code.includes(")") && code.includes(":") && 
            code.includes(";") && code.split("(").length > 2) {
          return "phylogenetic";
        }
        
        // Check for CSV/TSV data
        if ((language === "other" || language === "python") && 
            (code.includes(",") || code.includes("\t")) && 
            code.split("\n").length > 2) {
          const lines = code.split("\n").filter(l => l.trim());
          if (lines.length > 1) {
            const firstLineCommas = (lines[0].match(/,/g) || []).length;
            const firstLineTabs = (lines[0].match(/\t/g) || []).length;
            if ((firstLineCommas > 0 || firstLineTabs > 0) && lines.length > 2) {
              return "table";
            }
          }
        }
        
        // Language-specific previews
        switch (language) {
          case "html":
            // HTML is now handled directly in CodeRenderer with tabs
            return "none";
          case "python":
            return "python";
          case "json":
            return "json";
          default:
            return "none";
        }
      }
      
      return "none";
    };

    setPreviewType(detectPreviewType());
  }, [artifact]);

  const getPreviewIcon = () => {
    switch (previewType) {
      case "html":
      case "markdown":
        return <Eye className="w-4 h-4 mr-2" />;
      case "jupyter":
        return <FileText className="w-4 h-4 mr-2" />;
      case "table":
        return <Table className="w-4 h-4 mr-2" />;
      case "python":
      case "r":
        return <Code2 className="w-4 h-4 mr-2" />;
      case "json":
      case "tree":
        return <GitBranch className="w-4 h-4 mr-2" />;
      case "protein":
        return <Dna className="w-4 h-4 mr-2" />;
      case "pharmacophore":
        return <FlaskConical className="w-4 h-4 mr-2" />;
      case "phylogenetic":
        return <Activity className="w-4 h-4 mr-2" />;
      default:
        return null;
    }
  };

  const getPreviewLabel = () => {
    switch (previewType) {
      case "html":
        return "Preview HTML";
      case "jupyter":
        return "View Notebook";
      case "table":
        return "View Table";
      case "markdown":
        return "Preview";
      case "python":
        return "Run Python";
      case "r":
        return "Run R";
      case "json":
        return "Tree View";
      case "protein":
        return "View 3D Structure";
      case "pharmacophore":
        return "View Pharmacophore";
      case "phylogenetic":
        return "View Tree";
      default:
        return "Preview";
    }
  };

  const renderPreview = () => {
    if (!showPreview) return null;

    switch (previewType) {
      case "html":
        if (artifact.type === "code") {
          return (
            <HTMLPreview
              code={artifact.code}
              onClose={() => setShowPreview(false)}
            />
          );
        }
        break;
      
      case "jupyter":
        if (artifact.type === "code") {
          return (
            <JupyterPreview
              notebookJson={artifact.code}
              onClose={() => setShowPreview(false)}
            />
          );
        }
        break;
      
      case "table":
        if (artifact.type === "code") {
          return (
            <TablePreview
              data={artifact.code}
              onClose={() => setShowPreview(false)}
            />
          );
        }
        break;
      
      case "markdown":
        if (artifact.type === "text") {
          return (
            <MarkdownPreview
              content={artifact.fullMarkdown}
              onClose={() => setShowPreview(false)}
            />
          );
        }
        break;
      
      case "python":
        if (artifact.type === "code") {
          return (
            <PythonPreview
              code={artifact.code}
              onClose={() => setShowPreview(false)}
            />
          );
        }
        break;
      
      case "json":
        if (artifact.type === "code") {
          return (
            <TreePreview
              jsonData={artifact.code}
              onClose={() => setShowPreview(false)}
            />
          );
        }
        break;
      
      case "protein":
        if (artifact.type === "code") {
          return (
            <ProteinViewer
              pdbData={artifact.code}
              onClose={() => setShowPreview(false)}
            />
          );
        }
        break;
      
      case "pharmacophore":
        if (artifact.type === "code") {
          return (
            <PharmacophoreViewer
              data={artifact.code}
              onClose={() => setShowPreview(false)}
            />
          );
        }
        break;
      
      case "phylogenetic":
        if (artifact.type === "code") {
          return (
            <PhylogeneticTreeViewer
              data={artifact.code}
              onClose={() => setShowPreview(false)}
            />
          );
        }
        break;
    }
    
    return null;
  };

  if (previewType === "none") {
    return null;
  }

  return (
    <div className="relative">
      {/* Check for biomedical content first */}
      <BiomedicalPreviewManager
        content={artifact.type === "code" ? artifact.code : artifact.fullMarkdown}
        isHovering={isHovering}
        onClose={() => {}}
      />
      
      {/* Regular preview manager */}
      {isHovering && !showPreview && previewType !== "none" && (
        <div className="absolute top-2 right-2 z-10">
          <Button
            onClick={() => setShowPreview(true)}
            variant="outline"
            size="sm"
            className="bg-white shadow-md"
          >
            {getPreviewIcon()}
            {getPreviewLabel()}
          </Button>
        </div>
      )}
      
      {showPreview && (
        <div className="absolute inset-0 z-20 bg-white rounded-lg shadow-lg overflow-hidden">
          {renderPreview()}
        </div>
      )}
    </div>
  );
}