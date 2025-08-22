import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { X, Play, Loader2, Terminal, AlertCircle } from "lucide-react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";

interface PythonPreviewProps {
  code: string;
  onClose: () => void;
}

interface ExecutionResult {
  output?: string;
  error?: string;
  plots?: string[];
  tables?: any[];
}

export function PythonPreview({ code, onClose }: PythonPreviewProps) {
  const [isExecuting, setIsExecuting] = useState(false);
  const [result, setResult] = useState<ExecutionResult | null>(null);
  const [showCode, setShowCode] = useState(true);

  const executeCode = async () => {
    setIsExecuting(true);
    setResult(null);

    try {
      // Call backend API to execute Python code
      const response = await fetch("http://localhost:54367/api/execute/python", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ code }),
      });

      if (!response.ok) {
        throw new Error(`Execution failed: ${response.statusText}`);
      }

      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error("Failed to execute Python code:", error);
      setResult({
        error: error instanceof Error ? error.message : "Failed to execute code",
      });
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      <div className="flex justify-between items-center p-4 border-b">
        <div>
          <h3 className="text-lg font-semibold">Python Executor</h3>
          <p className="text-sm text-gray-600">
            Run Python code with Biomni environment
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            onClick={() => setShowCode(!showCode)}
            variant="outline"
            size="sm"
          >
            {showCode ? "Hide Code" : "Show Code"}
          </Button>
          <Button
            onClick={executeCode}
            disabled={isExecuting}
            variant="default"
            size="sm"
          >
            {isExecuting ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Running...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 mr-2" />
                Run
              </>
            )}
          </Button>
          <Button onClick={onClose} variant="ghost" size="sm">
            <X className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {/* Code Section */}
        {showCode && (
          <div className="border-b">
            <div className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <Terminal className="w-4 h-4 text-blue-600" />
                <span className="text-sm font-medium text-gray-700">Code</span>
              </div>
              <SyntaxHighlighter
                language="python"
                style={vscDarkPlus}
                customStyle={{
                  margin: 0,
                  borderRadius: "0.375rem",
                  fontSize: "0.875rem",
                  maxHeight: "400px",
                }}
              >
                {code}
              </SyntaxHighlighter>
            </div>
          </div>
        )}

        {/* Results Section */}
        {result && (
          <div className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <Terminal className="w-4 h-4 text-green-600" />
              <span className="text-sm font-medium text-gray-700">Output</span>
            </div>

            {/* Standard Output */}
            {result.output && (
              <div className="mb-4">
                <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto font-mono text-sm">
                  {result.output}
                </pre>
              </div>
            )}

            {/* Error Output */}
            {result.error && (
              <div className="mb-4">
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <div className="flex items-start gap-2">
                    <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                    <div className="flex-1">
                      <h4 className="text-sm font-medium text-red-900 mb-1">
                        Execution Error
                      </h4>
                      <pre className="text-red-700 text-sm whitespace-pre-wrap">
                        {result.error}
                      </pre>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Plots/Images */}
            {result.plots && result.plots.length > 0 && (
              <div className="mb-4">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Plots</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {result.plots.map((plot, index) => (
                    <div key={index} className="border rounded-lg p-2">
                      <img
                        src={`data:image/png;base64,${plot}`}
                        alt={`Plot ${index + 1}`}
                        className="w-full h-auto"
                      />
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Tables */}
            {result.tables && result.tables.length > 0 && (
              <div className="mb-4">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Data Tables</h4>
                {result.tables.map((table, index) => (
                  <div key={index} className="mb-4 overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200 border border-gray-200 rounded-lg">
                      <thead className="bg-gray-50">
                        <tr>
                          {Object.keys(table[0] || {}).map((header) => (
                            <th
                              key={header}
                              className="px-4 py-2 text-left text-xs font-medium text-gray-700 uppercase tracking-wider"
                            >
                              {header}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {table.map((row, rowIndex) => (
                          <tr key={rowIndex}>
                            {Object.values(row).map((cell, cellIndex) => (
                              <td
                                key={cellIndex}
                                className="px-4 py-2 text-sm text-gray-900"
                              >
                                {String(cell)}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Empty State */}
        {!result && !isExecuting && (
          <div className="flex flex-col items-center justify-center h-64 text-gray-500">
            <Terminal className="w-12 h-12 mb-3 text-gray-300" />
            <p className="text-sm">Click "Run" to execute the Python code</p>
            <p className="text-xs mt-1 text-gray-400">
              Code will run in the Biomni environment
            </p>
          </div>
        )}

        {/* Loading State */}
        {isExecuting && (
          <div className="flex flex-col items-center justify-center h-64">
            <Loader2 className="w-12 h-12 mb-3 text-blue-600 animate-spin" />
            <p className="text-sm text-gray-600">Executing Python code...</p>
          </div>
        )}
      </div>
    </div>
  );
}