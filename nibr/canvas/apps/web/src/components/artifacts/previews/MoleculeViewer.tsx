import React, { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { X, Download, FlaskConical, Info } from "lucide-react";
// @ts-ignore
import SmilesDrawer from "smiles-drawer";

interface MoleculeViewerProps {
  smiles: string;
  onClose: () => void;
}

interface MoleculeInfo {
  molecularWeight?: number;
  logP?: number;
  hbondDonors?: number;
  hbondAcceptors?: number;
  rotableBonds?: number;
  formula?: string;
}

export function MoleculeViewer({ smiles, onClose }: MoleculeViewerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [moleculeInfo, setMoleculeInfo] = useState<MoleculeInfo>({});
  const [showInfo, setShowInfo] = useState(false);

  useEffect(() => {
    if (!canvasRef.current) return;

    try {
      const smilesDrawer = new SmilesDrawer.Drawer({
        width: 800,
        height: 600,
        bondThickness: 1.5,
        bondLength: 30,
        shortBondLength: 0.85,
        bondSpacing: 0.18,
        fontSizeLarge: 16,
        fontSizeSmall: 14,
        padding: 20,
        explicitHydrogens: false,
        terminalCarbons: false,
        debug: false,
      });

      SmilesDrawer.parse(
        smiles,
        (tree: any) => {
          smilesDrawer.draw(tree, canvasRef.current, "light", false);
          
          // Calculate basic molecular properties
          try {
            const atoms = tree.graph.vertices || [];
            const bonds = tree.graph.edges || [];
            
            // Count atoms by type
            const atomCounts: { [key: string]: number } = {};
            let hDonors = 0;
            let hAcceptors = 0;
            
            atoms.forEach((atom: any) => {
              const element = atom.element || "C";
              atomCounts[element] = (atomCounts[element] || 0) + 1;
              
              // Simple H-bond donor/acceptor counting
              if (element === "N" || element === "O") {
                hAcceptors++;
                if (atom.bracket && atom.bracket.hcount > 0) {
                  hDonors++;
                }
              }
            });
            
            // Calculate molecular formula
            const formula = Object.entries(atomCounts)
              .sort(([a], [b]) => {
                if (a === "C") return -1;
                if (b === "C") return 1;
                if (a === "H") return -1;
                if (b === "H") return 1;
                return a.localeCompare(b);
              })
              .map(([element, count]) => 
                count === 1 ? element : `${element}${count}`
              )
              .join("");
            
            // Calculate molecular weight (approximate)
            const atomicWeights: { [key: string]: number } = {
              H: 1.008, C: 12.011, N: 14.007, O: 15.999,
              F: 18.998, S: 32.065, Cl: 35.453, Br: 79.904,
              I: 126.904, P: 30.974
            };
            
            const molWeight = Object.entries(atomCounts).reduce(
              (sum, [element, count]) => 
                sum + (atomicWeights[element] || 0) * count,
              0
            );
            
            // Count rotatable bonds (single bonds not in rings)
            const rotableBonds = bonds.filter((bond: any) => 
              bond.bondType === "-" && !bond.isPartOfAromaticRing
            ).length;
            
            setMoleculeInfo({
              formula,
              molecularWeight: Math.round(molWeight * 100) / 100,
              hbondDonors: hDonors,
              hbondAcceptors: hAcceptors,
              rotableBonds,
            });
          } catch (err) {
            console.error("Error calculating molecular properties:", err);
          }
          
          setError(null);
        },
        (err: any) => {
          console.error("Error parsing SMILES:", err);
          setError("Invalid SMILES string");
        }
      );
    } catch (err) {
      console.error("Error rendering molecule:", err);
      setError("Failed to render molecule");
    }
  }, [smiles]);

  const downloadImage = () => {
    if (!canvasRef.current) return;
    
    const link = document.createElement("a");
    link.download = "molecule.png";
    link.href = canvasRef.current.toDataURL();
    link.click();
  };

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      <div className="flex justify-between items-center p-4 border-b">
        <div>
          <h3 className="text-lg font-semibold">Molecule Viewer</h3>
          <p className="text-sm text-gray-600 font-mono">{smiles}</p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            onClick={() => setShowInfo(!showInfo)}
            variant="outline"
            size="sm"
          >
            <Info className="w-4 h-4 mr-2" />
            Properties
          </Button>
          <Button
            onClick={downloadImage}
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
      <div className="flex-1 flex">
        {/* Canvas */}
        <div className="flex-1 flex items-center justify-center p-4">
          {error ? (
            <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-md">
              {error}
            </div>
          ) : (
            <canvas
              ref={canvasRef}
              className="border rounded-lg shadow-sm"
              width={800}
              height={600}
            />
          )}
        </div>

        {/* Properties Panel */}
        {showInfo && (
          <div className="w-80 border-l p-4 bg-gray-50">
            <h4 className="font-semibold mb-4 flex items-center gap-2">
              <FlaskConical className="w-4 h-4" />
              Molecular Properties
            </h4>
            <div className="space-y-3">
              {moleculeInfo.formula && (
                <div>
                  <span className="text-sm text-gray-600">Formula:</span>
                  <p className="font-mono font-semibold">{moleculeInfo.formula}</p>
                </div>
              )}
              {moleculeInfo.molecularWeight && (
                <div>
                  <span className="text-sm text-gray-600">Molecular Weight:</span>
                  <p className="font-semibold">{moleculeInfo.molecularWeight} g/mol</p>
                </div>
              )}
              <div>
                <span className="text-sm text-gray-600">H-Bond Donors:</span>
                <p className="font-semibold">{moleculeInfo.hbondDonors || 0}</p>
              </div>
              <div>
                <span className="text-sm text-gray-600">H-Bond Acceptors:</span>
                <p className="font-semibold">{moleculeInfo.hbondAcceptors || 0}</p>
              </div>
              <div>
                <span className="text-sm text-gray-600">Rotatable Bonds:</span>
                <p className="font-semibold">{moleculeInfo.rotableBonds || 0}</p>
              </div>
              
              {/* Lipinski's Rule of Five */}
              <div className="mt-4 pt-4 border-t">
                <h5 className="text-sm font-semibold mb-2">Lipinski's Rule of Five</h5>
                <div className="space-y-1 text-sm">
                  <div className={moleculeInfo.molecularWeight && moleculeInfo.molecularWeight <= 500 ? "text-green-600" : "text-red-600"}>
                    ✓ MW ≤ 500 Da
                  </div>
                  <div className={moleculeInfo.hbondDonors && moleculeInfo.hbondDonors <= 5 ? "text-green-600" : "text-red-600"}>
                    ✓ H-bond donors ≤ 5
                  </div>
                  <div className={moleculeInfo.hbondAcceptors && moleculeInfo.hbondAcceptors <= 10 ? "text-green-600" : "text-red-600"}>
                    ✓ H-bond acceptors ≤ 10
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}