import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { X, ChevronRight, ChevronDown, Code, FileText, Terminal } from "lucide-react";
import { cn } from "@/lib/utils";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import ReactMarkdown from "react-markdown";

interface NotebookCell {
  cell_type: "code" | "markdown" | "raw";
  source: string | string[];
  outputs?: any[];
  execution_count?: number | null;
  metadata?: any;
}

interface NotebookData {
  cells: NotebookCell[];
  metadata?: any;
  nbformat?: number;
  nbformat_minor?: number;
}

interface JupyterPreviewProps {
  notebookJson: string;
  onClose: () => void;
}

export function JupyterPreview({ notebookJson, onClose }: JupyterPreviewProps) {
  const [notebook, setNotebook] = useState<NotebookData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [collapsedCells, setCollapsedCells] = useState<Set<number>>(new Set());

  useEffect(() => {
    try {
      const parsed = JSON.parse(notebookJson);
      setNotebook(parsed);
      setError(null);
    } catch (err) {
      console.error("Failed to parse notebook JSON:", err);
      setError("Invalid notebook format");
    }
  }, [notebookJson]);

  const toggleCellCollapse = (index: number) => {
    setCollapsedCells(prev => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return newSet;
    });
  };

  const formatSource = (source: string | string[]): string => {
    if (Array.isArray(source)) {
      return source.join("");
    }
    return source;
  };

  const renderOutput = (output: any, index: number) => {
    if (!output) return null;

    // Text output
    if (output.output_type === "stream" || output.output_type === "execute_result") {
      const text = output.text || output.data?.["text/plain"] || "";
      const formattedText = Array.isArray(text) ? text.join("") : text;
      
      return (
        <div key={index} className="bg-gray-900 text-gray-100 p-3 rounded-md font-mono text-sm overflow-x-auto">
          <pre>{formattedText}</pre>
        </div>
      );
    }

    // Error output
    if (output.output_type === "error") {
      return (
        <div key={index} className="bg-red-50 border border-red-200 text-red-800 p-3 rounded-md font-mono text-sm overflow-x-auto">
          <div className="font-bold text-red-900">{output.ename}: {output.evalue}</div>
          {output.traceback && (
            <pre className="mt-2 text-xs">{output.traceback.join("\n")}</pre>
          )}
        </div>
      );
    }

    // Display data (images, HTML, etc.)
    if (output.output_type === "display_data" && output.data) {
      // HTML output
      if (output.data["text/html"]) {
        const html = Array.isArray(output.data["text/html"]) 
          ? output.data["text/html"].join("") 
          : output.data["text/html"];
        
        return (
          <div 
            key={index}
            className="bg-white p-3 rounded-md overflow-x-auto"
            dangerouslySetInnerHTML={{ __html: html }}
          />
        );
      }

      // Image output
      if (output.data["image/png"]) {
        return (
          <div key={index} className="bg-white p-3 rounded-md">
            <img 
              src={`data:image/png;base64,${output.data["image/png"]}`}
              alt="Output"
              className="max-w-full h-auto"
            />
          </div>
        );
      }

      // Plain text fallback
      if (output.data["text/plain"]) {
        const text = Array.isArray(output.data["text/plain"]) 
          ? output.data["text/plain"].join("") 
          : output.data["text/plain"];
        
        return (
          <div key={index} className="bg-gray-100 p-3 rounded-md font-mono text-sm overflow-x-auto">
            <pre>{text}</pre>
          </div>
        );
      }
    }

    return null;
  };

  const renderCell = (cell: NotebookCell, index: number) => {
    const isCollapsed = collapsedCells.has(index);
    
    return (
      <div key={index} className="border rounded-lg mb-4 overflow-hidden">
        {/* Cell Header */}
        <div 
          className={cn(
            "flex items-center justify-between p-2 cursor-pointer hover:bg-gray-50",
            cell.cell_type === "code" ? "bg-blue-50" : "bg-green-50"
          )}
          onClick={() => toggleCellCollapse(index)}
        >
          <div className="flex items-center gap-2">
            {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            {cell.cell_type === "code" ? (
              <>
                <Code className="w-4 h-4 text-blue-600" />
                <span className="text-sm font-medium text-blue-700">
                  Code {cell.execution_count ? `[${cell.execution_count}]` : ""}
                </span>
              </>
            ) : (
              <>
                <FileText className="w-4 h-4 text-green-600" />
                <span className="text-sm font-medium text-green-700">Markdown</span>
              </>
            )}
          </div>
        </div>

        {/* Cell Content */}
        {!isCollapsed && (
          <div className="p-4">
            {cell.cell_type === "code" ? (
              <>
                <SyntaxHighlighter
                  language="python"
                  style={vscDarkPlus}
                  customStyle={{
                    margin: 0,
                    borderRadius: "0.375rem",
                    fontSize: "0.875rem",
                  }}
                >
                  {formatSource(cell.source)}
                </SyntaxHighlighter>
                
                {/* Outputs */}
                {cell.outputs && cell.outputs.length > 0 && (
                  <div className="mt-4 space-y-2">
                    <div className="text-xs font-medium text-gray-600 uppercase tracking-wider">Output:</div>
                    {cell.outputs.map((output, outputIndex) => renderOutput(output, outputIndex))}
                  </div>
                )}
              </>
            ) : cell.cell_type === "markdown" ? (
              <div className="prose prose-sm max-w-none">
                <ReactMarkdown>{formatSource(cell.source)}</ReactMarkdown>
              </div>
            ) : (
              <pre className="bg-gray-100 p-3 rounded-md text-sm overflow-x-auto">
                {formatSource(cell.source)}
              </pre>
            )}
          </div>
        )}
      </div>
    );
  };

  if (error) {
    return (
      <div className="p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Notebook Preview</h3>
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

  if (!notebook) {
    return (
      <div className="p-6">
        <div className="flex justify-center items-center h-32">
          <div className="text-gray-500">Loading notebook...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="flex justify-between items-center p-4 bg-white border-b">
        <div>
          <h3 className="text-lg font-semibold">Jupyter Notebook</h3>
          <p className="text-sm text-gray-600">
            {notebook.cells.length} cells • Format {notebook.nbformat}.{notebook.nbformat_minor}
          </p>
        </div>
        <Button onClick={onClose} variant="ghost" size="sm">
          <X className="w-4 h-4" />
        </Button>
      </div>

      {/* Cells */}
      <div className="flex-1 overflow-y-auto p-4">
        {notebook.cells.map((cell, index) => renderCell(cell, index))}
      </div>
    </div>
  );
}