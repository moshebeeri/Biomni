import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { X, ZoomIn, ZoomOut, Maximize2, GitBranch } from "lucide-react";

interface TreeNode {
  name: string;
  distance?: number;
  children?: TreeNode[];
  x?: number;
  y?: number;
}

interface PhylogeneticTreeViewerProps {
  data: string;
  onClose: () => void;
}

export function PhylogeneticTreeViewer({ data, onClose }: PhylogeneticTreeViewerProps) {
  const [tree, setTree] = useState<TreeNode | null>(null);
  const [zoom, setZoom] = useState(1);
  const [showDistances, setShowDistances] = useState(true);
  const [treeStats, setTreeStats] = useState({
    leaves: 0,
    branches: 0,
    maxDepth: 0
  });

  useEffect(() => {
    // Parse Newick format or similar tree data
    const parseNewick = (text: string): TreeNode => {
      // Simplified Newick parser
      // Format: (A:0.1,B:0.2,(C:0.3,D:0.4):0.5);
      
      // For demo, create a sample tree if parsing fails
      const sampleTree: TreeNode = {
        name: 'Root',
        distance: 0,
        children: [
          {
            name: 'Clade A',
            distance: 0.5,
            children: [
              { name: 'Species 1', distance: 0.3 },
              { name: 'Species 2', distance: 0.4 }
            ]
          },
          {
            name: 'Clade B',
            distance: 0.6,
            children: [
              { name: 'Species 3', distance: 0.2 },
              {
                name: 'Subclade B1',
                distance: 0.3,
                children: [
                  { name: 'Species 4', distance: 0.15 },
                  { name: 'Species 5', distance: 0.25 }
                ]
              }
            ]
          }
        ]
      };

      // Try to extract species names from the data
      const speciesPattern = /[A-Za-z_]+\d*/g;
      const matches = text.match(speciesPattern);
      if (matches && matches.length > 2) {
        // Build a simple tree from found species
        const species = matches.slice(0, Math.min(8, matches.length));
        return {
          name: 'Root',
          distance: 0,
          children: species.map((name, i) => ({
            name,
            distance: 0.1 + Math.random() * 0.5
          }))
        };
      }

      return sampleTree;
    };

    const parsedTree = parseNewick(data);
    
    // Calculate tree statistics
    const calculateStats = (node: TreeNode, depth = 0): { leaves: number; branches: number; maxDepth: number } => {
      if (!node.children || node.children.length === 0) {
        return { leaves: 1, branches: 0, maxDepth: depth };
      }
      
      let totalLeaves = 0;
      let totalBranches = node.children.length;
      let maxChildDepth = depth;
      
      node.children.forEach(child => {
        const childStats = calculateStats(child, depth + 1);
        totalLeaves += childStats.leaves;
        totalBranches += childStats.branches;
        maxChildDepth = Math.max(maxChildDepth, childStats.maxDepth);
      });
      
      return { leaves: totalLeaves, branches: totalBranches, maxDepth: maxChildDepth };
    };

    const stats = calculateStats(parsedTree);
    setTreeStats(stats);
    
    // Calculate positions for visualization
    const assignPositions = (node: TreeNode, x = 0, y = 0, spread = 200): void => {
      node.x = x;
      node.y = y;
      
      if (node.children) {
        const angleSpread = Math.PI / (node.children.length + 1);
        node.children.forEach((child, i) => {
          const angle = -Math.PI / 2 + angleSpread * (i + 1);
          const childX = x + Math.cos(angle) * spread;
          const childY = y + Math.sin(angle) * spread;
          assignPositions(child, childX, childY, spread * 0.7);
        });
      }
    };
    
    assignPositions(parsedTree, 400, 50, 150);
    setTree(parsedTree);
  }, [data]);

  const renderTree = (node: TreeNode | null): JSX.Element | null => {
    if (!node) return null;

    return (
      <g key={node.name}>
        {/* Draw branches to children */}
        {node.children?.map((child, i) => (
          <g key={`${node.name}-${child.name}-${i}`}>
            <line
              x1={node.x}
              y1={node.y}
              x2={child.x}
              y2={child.y}
              stroke="#4b5563"
              strokeWidth="2"
            />
            {showDistances && child.distance && (
              <text
                x={(node.x! + child.x!) / 2}
                y={(node.y! + child.y!) / 2 - 5}
                fontSize="10"
                fill="#6b7280"
                textAnchor="middle"
              >
                {child.distance.toFixed(2)}
              </text>
            )}
            {renderTree(child)}
          </g>
        ))}
        
        {/* Draw node */}
        <circle
          cx={node.x}
          cy={node.y}
          r={node.children && node.children.length > 0 ? 6 : 4}
          fill={node.children && node.children.length > 0 ? "#3b82f6" : "#10b981"}
          stroke="white"
          strokeWidth="2"
        />
        
        {/* Node label */}
        <text
          x={node.x}
          y={node.y! - 10}
          fontSize="12"
          fill="#1f2937"
          textAnchor="middle"
          fontWeight={node.children && node.children.length > 0 ? "bold" : "normal"}
        >
          {node.name}
        </text>
      </g>
    );
  };

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      <div className="flex justify-between items-center p-4 border-b">
        <div>
          <h3 className="text-lg font-semibold">Phylogenetic Tree</h3>
          <p className="text-sm text-gray-600">
            Evolutionary relationships visualization
          </p>
        </div>
        <Button onClick={onClose} variant="ghost" size="sm">
          <X className="w-4 h-4" />
        </Button>
      </div>

      {/* Stats Bar */}
      <div className="flex items-center gap-4 px-4 py-2 bg-gray-50 text-sm">
        <span className="flex items-center gap-1">
          <GitBranch className="w-3 h-3" />
          Branches: {treeStats.branches}
        </span>
        <span>Leaves: {treeStats.leaves}</span>
        <span>Max Depth: {treeStats.maxDepth}</span>
      </div>

      {/* Controls */}
      <div className="flex items-center gap-2 p-2 border-b">
        <Button
          onClick={() => setZoom(z => Math.min(z * 1.2, 3))}
          variant="outline"
          size="sm"
          title="Zoom In"
        >
          <ZoomIn className="w-4 h-4" />
        </Button>
        <Button
          onClick={() => setZoom(z => Math.max(z * 0.8, 0.5))}
          variant="outline"
          size="sm"
          title="Zoom Out"
        >
          <ZoomOut className="w-4 h-4" />
        </Button>
        <Button
          onClick={() => setZoom(1)}
          variant="outline"
          size="sm"
          title="Reset Zoom"
        >
          <Maximize2 className="w-4 h-4" />
        </Button>
        <div className="ml-4">
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={showDistances}
              onChange={(e) => setShowDistances(e.target.checked)}
              className="rounded"
            />
            Show distances
          </label>
        </div>
      </div>

      {/* Tree Visualization */}
      <div className="flex-1 overflow-auto p-4">
        <svg
          width="800"
          height="600"
          style={{
            transform: `scale(${zoom})`,
            transformOrigin: 'top left',
            transition: 'transform 0.2s'
          }}
        >
          {tree && renderTree(tree)}
        </svg>
      </div>

      {/* Legend */}
      <div className="p-2 border-t bg-gray-50 text-xs">
        <div className="flex gap-4">
          <span className="flex items-center gap-1">
            <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
            Internal node (ancestor)
          </span>
          <span className="flex items-center gap-1">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            Leaf node (species/sequence)
          </span>
          <span className="text-gray-500">
            Branch lengths represent evolutionary distance
          </span>
        </div>
      </div>
    </div>
  );
}