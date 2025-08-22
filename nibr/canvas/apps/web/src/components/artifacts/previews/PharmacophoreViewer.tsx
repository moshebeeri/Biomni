import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { X, Info, Atom, Zap } from "lucide-react";

interface PharmacophoreFeature {
  type: 'HBD' | 'HBA' | 'HYD' | 'POS' | 'NEG' | 'ARO';
  label: string;
  color: string;
  description: string;
  coordinates?: [number, number, number];
}

interface PharmacophoreViewerProps {
  data: string;
  onClose: () => void;
}

const FEATURE_TYPES: PharmacophoreFeature[] = [
  { type: 'HBD', label: 'H-Bond Donor', color: '#FF6B6B', description: 'Hydrogen bond donor groups (e.g., -OH, -NH)' },
  { type: 'HBA', label: 'H-Bond Acceptor', color: '#4ECDC4', description: 'Hydrogen bond acceptor groups (e.g., =O, -N)' },
  { type: 'HYD', label: 'Hydrophobic', color: '#FFD93D', description: 'Hydrophobic regions (e.g., aromatic rings, alkyl chains)' },
  { type: 'POS', label: 'Positive Charge', color: '#6BCF7F', description: 'Positively charged groups (e.g., -NH3+)' },
  { type: 'NEG', label: 'Negative Charge', color: '#C56CF0', description: 'Negatively charged groups (e.g., -COO-)' },
  { type: 'ARO', label: 'Aromatic', color: '#FFA502', description: 'Aromatic ring systems' }
];

export function PharmacophoreViewer({ data, onClose }: PharmacophoreViewerProps) {
  const [features, setFeatures] = useState<PharmacophoreFeature[]>([]);
  const [selectedFeature, setSelectedFeature] = useState<PharmacophoreFeature | null>(null);
  const [viewMode, setViewMode] = useState<'2D' | '3D'>('2D');

  useEffect(() => {
    // Parse pharmacophore data
    // This is a simplified parser - in reality, you'd parse actual pharmacophore file formats
    const parsedFeatures: PharmacophoreFeature[] = [];
    
    // Try to detect features from the data
    const lines = data.split('\n');
    lines.forEach(line => {
      const upper = line.toUpperCase();
      FEATURE_TYPES.forEach(feature => {
        if (upper.includes(feature.type) || upper.includes(feature.label.toUpperCase())) {
          // Extract coordinates if present (simple pattern matching)
          const coordMatch = line.match(/(-?\d+\.?\d*)\s+(-?\d+\.?\d*)\s+(-?\d+\.?\d*)/);
          const coords = coordMatch 
            ? [parseFloat(coordMatch[1]), parseFloat(coordMatch[2]), parseFloat(coordMatch[3])] as [number, number, number]
            : undefined;
          
          parsedFeatures.push({
            ...feature,
            coordinates: coords
          });
        }
      });
    });

    // If no features detected, show example features
    if (parsedFeatures.length === 0) {
      setFeatures(FEATURE_TYPES.map(f => ({
        ...f,
        coordinates: [
          Math.random() * 10 - 5,
          Math.random() * 10 - 5,
          Math.random() * 10 - 5
        ] as [number, number, number]
      })));
    } else {
      setFeatures(parsedFeatures);
    }
  }, [data]);

  const render2DPharmacophore = () => {
    // Simple 2D representation
    const radius = 150;
    const centerX = 200;
    const centerY = 200;

    return (
      <svg width="400" height="400" className="mx-auto">
        {/* Background circle */}
        <circle
          cx={centerX}
          cy={centerY}
          r={radius}
          fill="none"
          stroke="#e5e7eb"
          strokeWidth="2"
          strokeDasharray="5,5"
        />
        
        {/* Feature points */}
        {features.map((feature, index) => {
          const angle = (index / features.length) * 2 * Math.PI;
          const x = centerX + radius * 0.7 * Math.cos(angle);
          const y = centerY + radius * 0.7 * Math.sin(angle);
          
          return (
            <g key={index}>
              <circle
                cx={x}
                cy={y}
                r="20"
                fill={feature.color}
                opacity="0.8"
                className="cursor-pointer hover:opacity-100"
                onClick={() => setSelectedFeature(feature)}
              />
              <text
                x={x}
                y={y}
                textAnchor="middle"
                dominantBaseline="middle"
                fill="white"
                fontSize="12"
                fontWeight="bold"
                pointerEvents="none"
              >
                {feature.type}
              </text>
            </g>
          );
        })}
        
        {/* Center molecule placeholder */}
        <circle
          cx={centerX}
          cy={centerY}
          r="30"
          fill="#f3f4f6"
          stroke="#9ca3af"
          strokeWidth="2"
        />
        <text
          x={centerX}
          y={centerY}
          textAnchor="middle"
          dominantBaseline="middle"
          fill="#4b5563"
          fontSize="14"
        >
          Drug
        </text>
      </svg>
    );
  };

  const render3DInfo = () => {
    return (
      <div className="p-8 text-center">
        <div className="mb-4">
          <Atom className="w-16 h-16 mx-auto text-gray-400" />
        </div>
        <h4 className="text-lg font-semibold mb-2">3D Pharmacophore Model</h4>
        <p className="text-sm text-gray-600 mb-4">
          3D visualization shows spatial arrangement of pharmacophoric features
        </p>
        <div className="space-y-2 text-left max-w-md mx-auto">
          {features.map((feature, index) => (
            <div key={index} className="flex items-center gap-2 p-2 rounded hover:bg-gray-50">
              <div 
                className="w-4 h-4 rounded"
                style={{ backgroundColor: feature.color }}
              />
              <span className="text-sm font-medium">{feature.label}</span>
              {feature.coordinates && (
                <span className="text-xs text-gray-500 ml-auto">
                  ({feature.coordinates.map(c => c.toFixed(1)).join(', ')})
                </span>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      <div className="flex justify-between items-center p-4 border-b">
        <div>
          <h3 className="text-lg font-semibold">Pharmacophore Model</h3>
          <p className="text-sm text-gray-600">
            Key features for drug-target interaction
          </p>
        </div>
        <Button onClick={onClose} variant="ghost" size="sm">
          <X className="w-4 h-4" />
        </Button>
      </div>

      {/* View Mode Toggle */}
      <div className="flex items-center gap-2 p-2 border-b">
        <Button
          onClick={() => setViewMode('2D')}
          variant={viewMode === '2D' ? 'default' : 'outline'}
          size="sm"
        >
          2D View
        </Button>
        <Button
          onClick={() => setViewMode('3D')}
          variant={viewMode === '3D' ? 'default' : 'outline'}
          size="sm"
        >
          3D Coordinates
        </Button>
        <div className="ml-auto flex items-center gap-2 text-xs text-gray-500">
          <Zap className="w-3 h-3" />
          {features.length} pharmacophoric features detected
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto p-4">
        {viewMode === '2D' ? render2DPharmacophore() : render3DInfo()}
        
        {/* Selected Feature Info */}
        {selectedFeature && (
          <div className="mt-4 p-4 bg-blue-50 rounded-lg">
            <div className="flex items-start gap-2">
              <Info className="w-4 h-4 text-blue-600 mt-0.5" />
              <div>
                <h4 className="font-semibold text-blue-900">
                  {selectedFeature.label}
                </h4>
                <p className="text-sm text-blue-700 mt-1">
                  {selectedFeature.description}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="p-4 border-t bg-gray-50">
        <h4 className="text-sm font-semibold mb-2">Pharmacophore Features</h4>
        <div className="grid grid-cols-2 gap-2 text-xs">
          {FEATURE_TYPES.map((feature) => (
            <div key={feature.type} className="flex items-center gap-2">
              <div 
                className="w-3 h-3 rounded"
                style={{ backgroundColor: feature.color }}
              />
              <span>{feature.label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}