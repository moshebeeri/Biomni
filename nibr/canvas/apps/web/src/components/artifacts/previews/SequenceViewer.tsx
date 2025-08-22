import React, { useState, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { X, Download, Search, Copy, Check, Dna, Hash } from "lucide-react";
import { Input } from "@/components/ui/input";

interface SequenceViewerProps {
  sequence: string;
  format: string;
  onClose: () => void;
}

interface ParsedSequence {
  header: string;
  sequence: string;
  length: number;
  gc_content?: number;
  molecular_weight?: number;
}

export function SequenceViewer({ sequence, format, onClose }: SequenceViewerProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [copied, setCopied] = useState(false);
  const [showComplement, setShowComplement] = useState(false);
  const [colorScheme, setColorScheme] = useState<"none" | "nucleotide" | "hydrophobicity">("nucleotide");

  const parsedSequences = useMemo(() => {
    const sequences: ParsedSequence[] = [];
    
    if (format === "FASTA") {
      const entries = sequence.split(">").filter(e => e.trim());
      
      entries.forEach(entry => {
        const lines = entry.split("\n");
        const header = lines[0];
        const seq = lines.slice(1).join("").replace(/\s/g, "").toUpperCase();
        
        // Calculate GC content for DNA/RNA
        const gcCount = (seq.match(/[GC]/g) || []).length;
        const gc_content = seq.length > 0 ? (gcCount / seq.length) * 100 : 0;
        
        // Calculate molecular weight (approximate)
        const mw = calculateMolecularWeight(seq);
        
        sequences.push({
          header,
          sequence: seq,
          length: seq.length,
          gc_content: isNucleotide(seq) ? gc_content : undefined,
          molecular_weight: mw,
        });
      });
    } else {
      // Plain sequence
      const seq = sequence.replace(/\s/g, "").toUpperCase();
      sequences.push({
        header: "Unnamed Sequence",
        sequence: seq,
        length: seq.length,
        gc_content: isNucleotide(seq) ? 
          ((seq.match(/[GC]/g) || []).length / seq.length) * 100 : undefined,
        molecular_weight: calculateMolecularWeight(seq),
      });
    }
    
    return sequences;
  }, [sequence, format]);

  const isNucleotide = (seq: string): boolean => {
    return /^[ATCGUN]+$/.test(seq);
  };

  const calculateMolecularWeight = (seq: string): number => {
    const weights: { [key: string]: number } = {
      // Nucleotides (monophosphate)
      A: 331.2, T: 322.2, G: 347.2, C: 307.2, U: 308.2,
      // Amino acids
      R: 174.2, N: 132.1, D: 133.1, Q: 146.1, E: 147.1,
      H: 155.2, I: 131.2, L: 131.2, K: 146.2, M: 149.2,
      F: 165.2, P: 115.1, S: 105.1, W: 204.2, Y: 181.2,
      V: 117.1,
    };
    
    return Array.from(seq).reduce((sum, char) => 
      sum + (weights[char] || 110), 0
    );
  };

  const getComplement = (seq: string): string => {
    const complements: { [key: string]: string } = {
      A: "T", T: "A", G: "C", C: "G", U: "A", N: "N"
    };
    return Array.from(seq).map(base => complements[base] || base).join("");
  };

  const getReverseComplement = (seq: string): string => {
    return getComplement(seq).split("").reverse().join("");
  };

  const highlightSequence = (seq: string): JSX.Element[] => {
    const chunks: JSX.Element[] = [];
    const chunkSize = 10;
    
    for (let i = 0; i < seq.length; i += chunkSize) {
      const chunk = seq.slice(i, i + chunkSize);
      const highlighted = searchTerm && chunk.includes(searchTerm.toUpperCase());
      
      chunks.push(
        <span
          key={i}
          className={cn(
            "font-mono",
            highlighted && "bg-yellow-200",
            i % (chunkSize * 2) === 0 && "mr-2"
          )}
        >
          {colorScheme !== "none" ? (
            Array.from(chunk).map((char, j) => (
              <span
                key={`${i}-${j}`}
                className={getColorClass(char, colorScheme)}
              >
                {char}
              </span>
            ))
          ) : (
            chunk
          )}
        </span>
      );
    }
    
    return chunks;
  };

  const getColorClass = (char: string, scheme: string): string => {
    if (scheme === "nucleotide") {
      switch (char) {
        case "A": return "text-red-600";
        case "T": case "U": return "text-blue-600";
        case "G": return "text-green-600";
        case "C": return "text-yellow-600";
        default: return "text-gray-600";
      }
    } else if (scheme === "hydrophobicity") {
      // Hydrophobic amino acids
      if ("AILMFWV".includes(char)) return "text-red-600";
      // Hydrophilic
      if ("RNDQEHKST".includes(char)) return "text-blue-600";
      // Neutral
      return "text-gray-600";
    }
    return "";
  };

  const handleCopy = () => {
    const allSeqs = parsedSequences.map(s => `>${s.header}\n${s.sequence}`).join("\n");
    navigator.clipboard.writeText(allSeqs);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const allSeqs = parsedSequences.map(s => `>${s.header}\n${s.sequence}`).join("\n");
    const blob = new Blob([allSeqs], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "sequences.fasta";
    a.click();
    URL.revokeObjectURL(url);
  };

  const cn = (...classes: any[]) => classes.filter(Boolean).join(" ");

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      <div className="flex justify-between items-center p-4 border-b">
        <div className="flex items-center gap-3">
          <Dna className="w-5 h-5 text-blue-600" />
          <div>
            <h3 className="text-lg font-semibold">Sequence Viewer</h3>
            <p className="text-sm text-gray-600">
              {parsedSequences.length} sequence(s) • {format}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input
              type="text"
              placeholder="Search sequence..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 w-48"
            />
          </div>
          <select
            value={colorScheme}
            onChange={(e) => setColorScheme(e.target.value as any)}
            className="px-3 py-1 border rounded-md text-sm"
          >
            <option value="none">No coloring</option>
            <option value="nucleotide">Nucleotide</option>
            <option value="hydrophobicity">Hydrophobicity</option>
          </select>
          <Button
            onClick={handleCopy}
            variant="outline"
            size="sm"
          >
            {copied ? (
              <>
                <Check className="w-4 h-4 mr-2" />
                Copied!
              </>
            ) : (
              <>
                <Copy className="w-4 h-4 mr-2" />
                Copy
              </>
            )}
          </Button>
          <Button
            onClick={handleDownload}
            variant="outline"
            size="sm"
          >
            <Download className="w-4 h-4 mr-2" />
            Download
          </Button>
          <Button onClick={onClose} variant="ghost" size="sm">
            <X className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {parsedSequences.map((seq, index) => (
          <div key={index} className="mb-6 border rounded-lg p-4">
            {/* Sequence Header */}
            <div className="mb-3">
              <h4 className="font-semibold text-sm mb-1">{seq.header}</h4>
              <div className="flex gap-4 text-xs text-gray-600">
                <span>Length: {seq.length} bp</span>
                {seq.gc_content !== undefined && (
                  <span>GC: {seq.gc_content.toFixed(1)}%</span>
                )}
                <span>MW: {(seq.molecular_weight / 1000).toFixed(1)} kDa</span>
              </div>
            </div>

            {/* Sequence Display */}
            <div className="bg-gray-50 p-3 rounded-md overflow-x-auto">
              <div className="text-xs leading-relaxed">
                {/* Position ruler */}
                <div className="text-gray-400 mb-2 font-mono">
                  {Array.from({ length: Math.ceil(seq.sequence.length / 60) }, (_, i) => (
                    <div key={i} className="mb-1">
                      <span className="inline-block w-16 text-right mr-2">
                        {i * 60 + 1}
                      </span>
                      {highlightSequence(seq.sequence.slice(i * 60, (i + 1) * 60))}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Complement for DNA */}
            {isNucleotide(seq.sequence) && (
              <div className="mt-3">
                <Button
                  onClick={() => setShowComplement(!showComplement)}
                  variant="outline"
                  size="sm"
                >
                  {showComplement ? "Hide" : "Show"} Reverse Complement
                </Button>
                {showComplement && (
                  <div className="mt-2 bg-blue-50 p-3 rounded-md overflow-x-auto">
                    <div className="text-xs font-mono">
                      {getReverseComplement(seq.sequence)}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}