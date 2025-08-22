import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Download, 
  Code, 
  FileText, 
  Brain, 
  Database,
  ChevronRight,
  Copy,
  Check
} from 'lucide-react';

interface Artifact {
  type: 'code' | 'data' | 'visualization';
  language?: string;
  content: string;
  metadata?: any;
}

interface Insight {
  text: string;
  confidence?: number;
  source?: string;
}

interface ResearchResponse {
  sessionId?: string;
  executionId?: string;
  markdown: string;
  artifacts: Artifact[];
  insights: string[] | Insight[];
  toolsUsed: string[];
  dataAdded?: Record<string, string>;
  timestamp?: string;
  context?: {
    previousExecutions: number;
    sessionTitle: string;
  };
}

interface ResearchResponseViewerProps {
  response: ResearchResponse;
  onExport?: (format: 'markdown' | 'pdf') => void;
  onAddData?: (data: any) => void;
  onContinueResearch?: (prompt: string) => void;
}

export const ResearchResponseViewer: React.FC<ResearchResponseViewerProps> = ({
  response,
  onExport,
  onAddData,
  onContinueResearch
}) => {
  const [copied, setCopied] = useState(false);
  const [selectedArtifact, setSelectedArtifact] = useState<number | null>(null);
  const [continuePrompt, setContinuePrompt] = useState('');

  const handleCopyMarkdown = () => {
    navigator.clipboard.writeText(response.markdown);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleExportMarkdown = () => {
    const blob = new Blob([response.markdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `research_${response.executionId || 'response'}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const formatToolName = (tool: string) => {
    return tool
      .replace(/_/g, ' ')
      .replace(/\b\w/g, l => l.toUpperCase());
  };

  const getInsightText = (insight: string | Insight): string => {
    return typeof insight === 'string' ? insight : insight.text;
  };

  return (
    <div className="research-response-viewer space-y-4">
      {/* Header with context */}
      {response.context && (
        <Card className="p-4 bg-blue-50 dark:bg-blue-950">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-medium text-blue-900 dark:text-blue-100">
                Research Session: {response.context.sessionTitle}
              </h3>
              <p className="text-xs text-blue-700 dark:text-blue-300 mt-1">
                Execution #{response.context.previousExecutions + 1} • 
                Building on previous findings
              </p>
            </div>
            <Badge variant="secondary">
              <Brain className="w-3 h-3 mr-1" />
              Context Applied
            </Badge>
          </div>
        </Card>
      )}

      {/* Main content tabs */}
      <Tabs defaultValue="response" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="response">Response</TabsTrigger>
          <TabsTrigger value="insights">
            Insights ({response.insights.length})
          </TabsTrigger>
          <TabsTrigger value="artifacts">
            Artifacts ({response.artifacts.length})
          </TabsTrigger>
          <TabsTrigger value="tools">
            Tools ({response.toolsUsed.length})
          </TabsTrigger>
        </TabsList>

        {/* Response Tab */}
        <TabsContent value="response" className="space-y-4">
          <Card className="p-4">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold">Research Response</h2>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleCopyMarkdown}
                >
                  {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                  {copied ? 'Copied!' : 'Copy'}
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleExportMarkdown}
                >
                  <Download className="w-4 h-4 mr-1" />
                  Export MD
                </Button>
              </div>
            </div>
            
            <ScrollArea className="h-[500px] w-full rounded-md border p-4">
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <ReactMarkdown
                  components={{
                    code: ({ node, inline, className, children, ...props }) => {
                      const match = /language-(\w+)/.exec(className || '');
                      return !inline && match ? (
                        <div className="relative">
                          <pre className="bg-gray-100 dark:bg-gray-900 p-4 rounded-md overflow-x-auto">
                            <code className={className} {...props}>
                              {children}
                            </code>
                          </pre>
                          <Badge 
                            className="absolute top-2 right-2"
                            variant="secondary"
                          >
                            {match[1]}
                          </Badge>
                        </div>
                      ) : (
                        <code className="bg-gray-100 dark:bg-gray-900 px-1 py-0.5 rounded" {...props}>
                          {children}
                        </code>
                      );
                    }
                  }}
                >
                  {response.markdown}
                </ReactMarkdown>
              </div>
            </ScrollArea>
          </Card>

          {/* Continue Research */}
          <Card className="p-4">
            <h3 className="text-sm font-medium mb-3">Continue Research</h3>
            <div className="flex gap-2">
              <input
                type="text"
                className="flex-1 px-3 py-2 border rounded-md"
                placeholder="Add data or evolve the analysis..."
                value={continuePrompt}
                onChange={(e) => setContinuePrompt(e.target.value)}
              />
              <Button
                onClick={() => {
                  if (continuePrompt && onContinueResearch) {
                    onContinueResearch(continuePrompt);
                    setContinuePrompt('');
                  }
                }}
                disabled={!continuePrompt}
              >
                <ChevronRight className="w-4 h-4 mr-1" />
                Continue
              </Button>
            </div>
          </Card>
        </TabsContent>

        {/* Insights Tab */}
        <TabsContent value="insights">
          <Card className="p-4">
            <h2 className="text-lg font-semibold mb-4">Key Insights</h2>
            <ScrollArea className="h-[500px]">
              <div className="space-y-3">
                {response.insights.map((insight, idx) => (
                  <Card key={idx} className="p-3 bg-green-50 dark:bg-green-950">
                    <div className="flex items-start gap-2">
                      <Brain className="w-5 h-5 text-green-600 dark:text-green-400 mt-0.5" />
                      <p className="text-sm text-gray-700 dark:text-gray-300">
                        {getInsightText(insight)}
                      </p>
                    </div>
                  </Card>
                ))}
                {response.insights.length === 0 && (
                  <p className="text-sm text-gray-500">No insights detected in this response.</p>
                )}
              </div>
            </ScrollArea>
          </Card>
        </TabsContent>

        {/* Artifacts Tab */}
        <TabsContent value="artifacts">
          <Card className="p-4">
            <h2 className="text-lg font-semibold mb-4">Generated Artifacts</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {response.artifacts.map((artifact, idx) => (
                <Card 
                  key={idx} 
                  className="p-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-900"
                  onClick={() => setSelectedArtifact(idx)}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      {artifact.type === 'code' ? (
                        <Code className="w-4 h-4" />
                      ) : artifact.type === 'data' ? (
                        <Database className="w-4 h-4" />
                      ) : (
                        <FileText className="w-4 h-4" />
                      )}
                      <span className="text-sm font-medium">
                        {artifact.type === 'code' ? `Code (${artifact.language || 'plain'})` : artifact.type}
                      </span>
                    </div>
                    <Badge variant="outline" className="text-xs">
                      Artifact #{idx + 1}
                    </Badge>
                  </div>
                  <pre className="text-xs bg-gray-100 dark:bg-gray-800 p-2 rounded overflow-hidden">
                    {artifact.content.substring(0, 150)}...
                  </pre>
                </Card>
              ))}
              {response.artifacts.length === 0 && (
                <p className="text-sm text-gray-500">No artifacts generated in this response.</p>
              )}
            </div>
          </Card>
        </TabsContent>

        {/* Tools Tab */}
        <TabsContent value="tools">
          <Card className="p-4">
            <h2 className="text-lg font-semibold mb-4">Tools Used</h2>
            <div className="flex flex-wrap gap-2">
              {response.toolsUsed.map((tool, idx) => (
                <Badge key={idx} variant="secondary" className="py-1.5 px-3">
                  {formatToolName(tool)}
                </Badge>
              ))}
              {response.toolsUsed.length === 0 && (
                <p className="text-sm text-gray-500">No tools were used in this response.</p>
              )}
            </div>
            
            {response.dataAdded && Object.keys(response.dataAdded).length > 0 && (
              <div className="mt-6">
                <h3 className="text-sm font-medium mb-3">Data Added</h3>
                <div className="space-y-2">
                  {Object.entries(response.dataAdded).map(([path, description], idx) => (
                    <div key={idx} className="flex items-center gap-2 text-sm">
                      <Database className="w-4 h-4 text-blue-500" />
                      <span className="font-mono">{path}</span>
                      <span className="text-gray-500">- {description}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </Card>
        </TabsContent>
      </Tabs>

      {/* Selected Artifact Modal */}
      {selectedArtifact !== null && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          onClick={() => setSelectedArtifact(null)}
        >
          <Card 
            className="w-4/5 max-w-4xl max-h-[80vh] p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">
                Artifact Details
              </h3>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setSelectedArtifact(null)}
              >
                ✕
              </Button>
            </div>
            <ScrollArea className="h-[60vh]">
              <pre className="text-sm bg-gray-100 dark:bg-gray-900 p-4 rounded-md overflow-x-auto">
                {response.artifacts[selectedArtifact].content}
              </pre>
            </ScrollArea>
          </Card>
        </div>
      )}
    </div>
  );
};