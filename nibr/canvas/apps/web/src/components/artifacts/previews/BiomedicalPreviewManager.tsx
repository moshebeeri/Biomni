import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { 
  Eye, FlaskConical, Dna, FileText, Database, 
  Activity, Pill, TestTube, Microscope 
} from "lucide-react";
import { cn } from "@/lib/utils";
import { MoleculeViewer } from "./MoleculeViewer";
import { GenomeBrowser } from "./GenomeBrowser";
import { ClinicalDataViewer } from "./ClinicalDataViewer";
import { SequenceViewer } from "./SequenceViewer";

export type BiomedicalPreviewType = 
  | "molecule" 
  | "genome" 
  | "protein" 
  | "sequence" 
  | "clinical" 
  | "pharmacology"
  | "none";

interface BiomedicalPreviewManagerProps {
  content: string;
  isHovering: boolean;
  onClose?: () => void;
}

export function BiomedicalPreviewManager({ 
  content, 
  isHovering, 
  onClose 
}: BiomedicalPreviewManagerProps) {
  const [showPreview, setShowPreview] = useState(false);
  const [previewType, setPreviewType] = useState<BiomedicalPreviewType>("none");
  const [detectedFormat, setDetectedFormat] = useState<string>("");

  useEffect(() => {
    // Detect biomedical data type
    const detectBiomedicalType = (): [BiomedicalPreviewType, string] => {
      const trimmedContent = content.trim();
      const firstLine = trimmedContent.split("\n")[0];
      
      // SMILES notation detection
      if (isSMILES(trimmedContent)) {
        return ["molecule", "SMILES"];
      }
      
      // FASTA format detection
      if (firstLine.startsWith(">")) {
        return ["sequence", "FASTA"];
      }
      
      // PDB format detection
      if (firstLine.startsWith("HEADER") || firstLine.startsWith("ATOM")) {
        return ["protein", "PDB"];
      }
      
      // VCF format detection
      if (firstLine.startsWith("##fileformat=VCF")) {
        return ["genome", "VCF"];
      }
      
      // BED format detection
      if (looksLikeBED(trimmedContent)) {
        return ["genome", "BED"];
      }
      
      // GFF/GTF format detection
      if (firstLine.startsWith("##gff-version")) {
        return ["genome", "GFF"];
      }
      
      // SAM/BAM format detection
      if (firstLine.startsWith("@HD") || firstLine.startsWith("@SQ")) {
        return ["genome", "SAM"];
      }
      
      // Clinical trial data detection
      if (content.includes("patient") || content.includes("trial") || 
          content.includes("adverse") || content.includes("dose")) {
        return ["clinical", "Clinical Data"];
      }
      
      // Drug/Pharmacology data detection
      if (content.includes("IC50") || content.includes("EC50") || 
          content.includes("Ki") || content.includes("drug")) {
        return ["pharmacology", "Pharmacology Data"];
      }
      
      return ["none", ""];
    };

    const [type, format] = detectBiomedicalType();
    setPreviewType(type);
    setDetectedFormat(format);
  }, [content]);

  // SMILES validation
  const isSMILES = (str: string): boolean => {
    // Basic SMILES pattern checking
    const smilesPattern = /^[A-Za-z0-9@+\-\[\]()=#$\\\/\.]+$/;
    const lines = str.split("\n");
    const firstLine = lines[0].trim();
    
    // Check if it's a single line and matches SMILES pattern
    if (lines.length === 1 && smilesPattern.test(firstLine)) {
      // Additional checks for common SMILES elements
      return firstLine.includes("C") || firstLine.includes("c") || 
             firstLine.includes("O") || firstLine.includes("N");
    }
    
    // Check for multi-line SMILES (compound list)
    if (lines.every(line => !line.trim() || smilesPattern.test(line.trim()))) {
      return lines.some(line => {
        const trimmed = line.trim();
        return trimmed && (trimmed.includes("C") || trimmed.includes("c"));
      });
    }
    
    return false;
  };

  // BED format detection
  const looksLikeBED = (content: string): boolean => {
    const lines = content.split("\n").filter(l => l.trim() && !l.startsWith("#"));
    if (lines.length === 0) return false;
    
    const firstLine = lines[0].split("\t");
    // BED format: chr start end [name] [score] ...
    return firstLine.length >= 3 && 
           firstLine[0].startsWith("chr") && 
           !isNaN(Number(firstLine[1])) && 
           !isNaN(Number(firstLine[2]));
  };

  const getPreviewIcon = () => {
    switch (previewType) {
      case "molecule":
        return <FlaskConical className="w-4 h-4 mr-2" />;
      case "genome":
        return <Dna className="w-4 h-4 mr-2" />;
      case "protein":
        return <Microscope className="w-4 h-4 mr-2" />;
      case "sequence":
        return <FileText className="w-4 h-4 mr-2" />;
      case "clinical":
        return <Activity className="w-4 h-4 mr-2" />;
      case "pharmacology":
        return <Pill className="w-4 h-4 mr-2" />;
      default:
        return <Eye className="w-4 h-4 mr-2" />;
    }
  };

  const getPreviewLabel = () => {
    if (detectedFormat) {
      return `View ${detectedFormat}`;
    }
    
    switch (previewType) {
      case "molecule":
        return "View Molecule";
      case "genome":
        return "Open Genome Browser";
      case "protein":
        return "View 3D Structure";
      case "sequence":
        return "View Sequence";
      case "clinical":
        return "View Clinical Data";
      case "pharmacology":
        return "View Drug Data";
      default:
        return "Preview";
    }
  };

  const renderPreview = () => {
    if (!showPreview) return null;

    const handleClose = () => {
      setShowPreview(false);
      if (onClose) onClose();
    };

    switch (previewType) {
      case "molecule":
        // Extract first SMILES if multiple
        const smiles = content.split("\n")[0].trim();
        return (
          <MoleculeViewer
            smiles={smiles}
            onClose={handleClose}
          />
        );
      
      case "genome":
        // Determine file type from detected format
        const fileType = detectedFormat.toLowerCase() as any;
        return (
          <GenomeBrowser
            data={content}
            fileType={fileType}
            onClose={handleClose}
          />
        );
      
      case "sequence":
        return (
          <SequenceViewer
            sequence={content}
            format={detectedFormat}
            onClose={handleClose}
          />
        );
      
      case "clinical":
        return (
          <ClinicalDataViewer
            data={content}
            onClose={handleClose}
          />
        );
      
      default:
        return null;
    }
  };

  if (previewType === "none") {
    return null;
  }

  return (
    <div className="relative">
      {isHovering && !showPreview && (
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