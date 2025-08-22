import React, { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { X, RotateCw, ZoomIn, ZoomOut, Move3D } from "lucide-react";

interface ProteinViewerProps {
  pdbData: string;
  onClose: () => void;
}

export function ProteinViewer({ pdbData, onClose }: ProteinViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [viewerReady, setViewerReady] = useState(false);
  const [proteinInfo, setProteinInfo] = useState<{
    title?: string;
    atoms?: number;
    chains?: string[];
    residues?: number;
  }>({});

  useEffect(() => {
    // Parse PDB data for basic information
    const lines = pdbData.split('\n');
    let title = '';
    const atoms = new Set();
    const chains = new Set<string>();
    const residues = new Set<string>();

    lines.forEach(line => {
      if (line.startsWith('TITLE')) {
        title += line.substring(10).trim() + ' ';
      } else if (line.startsWith('ATOM')) {
        atoms.add(line.substring(6, 11).trim());
        const chain = line.substring(21, 22).trim();
        if (chain) chains.add(chain);
        const residue = line.substring(17, 20).trim() + line.substring(22, 26).trim();
        residues.add(residue);
      }
    });

    setProteinInfo({
      title: title.trim() || 'Protein Structure',
      atoms: atoms.size,
      chains: Array.from(chains),
      residues: residues.size
    });

    // Load 3Dmol.js library dynamically
    const script = document.createElement('script');
    script.src = 'https://3Dmol.org/build/3Dmol-min.js';
    script.async = true;
    script.onload = () => {
      setViewerReady(true);
    };
    document.body.appendChild(script);

    return () => {
      document.body.removeChild(script);
    };
  }, [pdbData]);

  useEffect(() => {
    if (viewerReady && containerRef.current && (window as any).$3Dmol) {
      const $3Dmol = (window as any).$3Dmol;
      
      // Create viewer
      const viewer = $3Dmol.createViewer(containerRef.current, {
        backgroundColor: 'white'
      });

      // Add PDB data
      viewer.addModel(pdbData, 'pdb');
      
      // Style the protein
      viewer.setStyle({}, {
        cartoon: { color: 'spectrum' },
        stick: { radius: 0.15 }
      });
      
      // Add surface for selected residues
      viewer.addSurface($3Dmol.SurfaceType.VDW, {
        opacity: 0.85,
        color: 'white'
      }, { hetflag: false });

      viewer.zoomTo();
      viewer.render();

      // Store viewer for controls
      (containerRef.current as any).viewer = viewer;
    }
  }, [viewerReady, pdbData]);

  const handleRotate = () => {
    if (containerRef.current && (containerRef.current as any).viewer) {
      const viewer = (containerRef.current as any).viewer;
      viewer.rotate(90, { x: 1, y: 0, z: 0 });
      viewer.render();
    }
  };

  const handleZoomIn = () => {
    if (containerRef.current && (containerRef.current as any).viewer) {
      const viewer = (containerRef.current as any).viewer;
      viewer.zoom(0.8);
      viewer.render();
    }
  };

  const handleZoomOut = () => {
    if (containerRef.current && (containerRef.current as any).viewer) {
      const viewer = (containerRef.current as any).viewer;
      viewer.zoom(1.2);
      viewer.render();
    }
  };

  const handleReset = () => {
    if (containerRef.current && (containerRef.current as any).viewer) {
      const viewer = (containerRef.current as any).viewer;
      viewer.zoomTo();
      viewer.render();
    }
  };

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      <div className="flex justify-between items-center p-4 border-b">
        <div>
          <h3 className="text-lg font-semibold">Protein Structure Viewer</h3>
          <p className="text-sm text-gray-600">{proteinInfo.title}</p>
        </div>
        <Button onClick={onClose} variant="ghost" size="sm">
          <X className="w-4 h-4" />
        </Button>
      </div>

      {/* Info Bar */}
      <div className="flex items-center gap-4 px-4 py-2 bg-gray-50 text-sm">
        <span>Atoms: {proteinInfo.atoms || 0}</span>
        <span>Chains: {proteinInfo.chains?.join(', ') || 'N/A'}</span>
        <span>Residues: {proteinInfo.residues || 0}</span>
      </div>

      {/* Controls */}
      <div className="flex items-center gap-2 p-2 border-b">
        <Button
          onClick={handleRotate}
          variant="outline"
          size="sm"
          title="Rotate 90°"
        >
          <RotateCw className="w-4 h-4" />
        </Button>
        <Button
          onClick={handleZoomIn}
          variant="outline"
          size="sm"
          title="Zoom In"
        >
          <ZoomIn className="w-4 h-4" />
        </Button>
        <Button
          onClick={handleZoomOut}
          variant="outline"
          size="sm"
          title="Zoom Out"
        >
          <ZoomOut className="w-4 h-4" />
        </Button>
        <Button
          onClick={handleReset}
          variant="outline"
          size="sm"
          title="Reset View"
        >
          <Move3D className="w-4 h-4" />
        </Button>
        <div className="ml-auto text-xs text-gray-500">
          Drag to rotate • Scroll to zoom • Shift+drag to translate
        </div>
      </div>

      {/* 3D Viewer */}
      <div className="flex-1 relative">
        {!viewerReady && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-gray-500">Loading 3D viewer...</div>
          </div>
        )}
        <div
          ref={containerRef}
          className="w-full h-full"
          style={{ minHeight: '500px' }}
        />
      </div>

      {/* Legend */}
      <div className="p-2 border-t bg-gray-50 text-xs">
        <div className="flex gap-4">
          <span className="flex items-center gap-1">
            <div className="w-3 h-3 bg-blue-500 rounded"></div>
            N-terminus
          </span>
          <span className="flex items-center gap-1">
            <div className="w-3 h-3 bg-red-500 rounded"></div>
            C-terminus
          </span>
          <span className="flex items-center gap-1">
            <div className="w-3 h-3 bg-gradient-to-r from-blue-500 to-red-500 rounded"></div>
            Rainbow (N→C)
          </span>
        </div>
      </div>
    </div>
  );
}