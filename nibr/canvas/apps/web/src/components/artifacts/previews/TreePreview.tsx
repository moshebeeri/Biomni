import React, { useState, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { X, ChevronRight, ChevronDown, Copy, Check, Search, Code, FileJson } from "lucide-react";
import { JSONTree } from "react-json-tree";

interface TreePreviewProps {
  jsonData: string;
  onClose: () => void;
}

export function TreePreview({ jsonData, onClose }: TreePreviewProps) {
  const [parsedData, setParsedData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [showRaw, setShowRaw] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [copied, setCopied] = useState(false);
  const [expandedPaths, setExpandedPaths] = useState<Set<string>>(new Set());

  // Parse JSON data
  useMemo(() => {
    try {
      const parsed = JSON.parse(jsonData);
      setParsedData(parsed);
      setError(null);
    } catch (err) {
      console.error("Failed to parse JSON:", err);
      setError("Invalid JSON format");
    }
  }, [jsonData]);

  const handleCopy = () => {
    navigator.clipboard.writeText(jsonData);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Custom theme for JSON tree
  const theme = {
    scheme: "custom",
    author: "custom",
    base00: "#ffffff", // Background
    base01: "#f7f7f7",
    base02: "#e3e3e3",
    base03: "#969696",
    base04: "#808080",
    base05: "#4a4a4a", // Default text
    base06: "#303030",
    base07: "#1a1a1a",
    base08: "#d73a49", // Null, undefined, functions, symbols
    base09: "#e36209", // Numbers and booleans
    base0A: "#79b8ff", // Objects keys
    base0B: "#22863a", // Strings
    base0C: "#1b7c83",
    base0D: "#0366d6", // Object/array expand/collapse
    base0E: "#6f42c1", // Object names
    base0F: "#b08800",
  };

  const shouldExpandNode = (keyPath: string[], data: any, level: number) => {
    // Expand first 2 levels by default
    if (level < 2) return true;
    
    // Check if path is in expanded paths
    const path = keyPath.join(".");
    return expandedPaths.has(path);
  };

  const renderNodeLabel = ({ style, ...labelProps }: any) => {
    const isHighlighted = searchTerm && 
      JSON.stringify(labelProps).toLowerCase().includes(searchTerm.toLowerCase());
    
    return (
      <span
        style={{
          ...style,
          backgroundColor: isHighlighted ? "#fef3c7" : undefined,
          padding: isHighlighted ? "0 2px" : undefined,
          borderRadius: isHighlighted ? "2px" : undefined,
        }}
        {...labelProps}
      />
    );
  };

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + " " + sizes[i];
  };

  const getStats = () => {
    if (!parsedData) return null;
    
    const stats = {
      size: formatBytes(new Blob([jsonData]).size),
      keys: 0,
      arrays: 0,
      objects: 0,
    };

    const countElements = (obj: any) => {
      if (Array.isArray(obj)) {
        stats.arrays++;
        obj.forEach(countElements);
      } else if (obj && typeof obj === "object") {
        stats.objects++;
        Object.keys(obj).forEach(key => {
          stats.keys++;
          countElements(obj[key]);
        });
      }
    };

    countElements(parsedData);
    return stats;
  };

  const stats = getStats();

  if (error) {
    return (
      <div className="p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">JSON Tree View</h3>
          <Button onClick={onClose} variant="ghost" size="sm">
            <X className="w-4 h-4" />
          </Button>
        </div>
        <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-md">
          {error}
        </div>
      </div>
    );
  }

  if (!parsedData) {
    return (
      <div className="p-6">
        <div className="flex justify-center items-center h-32">
          <div className="text-gray-500">Loading JSON...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      <div className="flex justify-between items-center p-4 border-b">
        <div>
          <h3 className="text-lg font-semibold">JSON Tree Viewer</h3>
          {stats && (
            <p className="text-sm text-gray-600">
              {stats.size} • {stats.keys} keys • {stats.objects} objects • {stats.arrays} arrays
            </p>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Button
            onClick={() => setShowRaw(!showRaw)}
            variant="outline"
            size="sm"
          >
            {showRaw ? (
              <>
                <FileJson className="w-4 h-4 mr-2" />
                Tree View
              </>
            ) : (
              <>
                <Code className="w-4 h-4 mr-2" />
                Raw JSON
              </>
            )}
          </Button>
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
          <Button onClick={onClose} variant="ghost" size="sm">
            <X className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Search (only in tree view) */}
      {!showRaw && (
        <div className="p-4 border-b">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input
              type="text"
              placeholder="Search JSON..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>
      )}

      {/* Content */}
      <div className="flex-1 overflow-auto p-4">
        {showRaw ? (
          <pre className="whitespace-pre-wrap font-mono text-sm bg-gray-50 p-4 rounded-lg">
            {JSON.stringify(parsedData, null, 2)}
          </pre>
        ) : (
          <div className="font-mono text-sm">
            <JSONTree
              data={parsedData}
              theme={theme}
              invertTheme={false}
              hideRoot={false}
              shouldExpandNode={shouldExpandNode}
              labelRenderer={renderNodeLabel}
              valueRenderer={(raw, value, ...keyPath) => {
                const isHighlighted = searchTerm && 
                  String(value).toLowerCase().includes(searchTerm.toLowerCase());
                
                return (
                  <span
                    style={{
                      backgroundColor: isHighlighted ? "#fef3c7" : undefined,
                      padding: isHighlighted ? "0 2px" : undefined,
                      borderRadius: isHighlighted ? "2px" : undefined,
                    }}
                  >
                    {String(value)}
                  </span>
                );
              }}
              getItemString={(type, data, itemType, itemString, keyPath) => {
                if (type === "Array") {
                  return <span className="text-gray-500"> [{data.length}]</span>;
                } else if (type === "Object") {
                  const keys = Object.keys(data).length;
                  return <span className="text-gray-500"> {`{${keys}}`}</span>;
                }
                return <span className="text-gray-500"> {itemString}</span>;
              }}
            />
          </div>
        )}
      </div>
    </div>
  );
}