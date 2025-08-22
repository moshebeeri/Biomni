import React, { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { X, Eye, EyeOff, Copy, Check } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import mermaid from "mermaid";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";

interface MarkdownPreviewProps {
  content: string;
  onClose: () => void;
}

export function MarkdownPreview({ content, onClose }: MarkdownPreviewProps) {
  const [showRaw, setShowRaw] = useState(false);
  const [copied, setCopied] = useState(false);
  const mermaidRef = useRef<number>(0);

  useEffect(() => {
    // Initialize mermaid
    mermaid.initialize({
      startOnLoad: true,
      theme: "default",
      securityLevel: "loose",
      themeVariables: {
        primaryColor: "#fff",
        primaryTextColor: "#000",
        primaryBorderColor: "#000",
        lineColor: "#000",
      },
    });

    // Render mermaid diagrams
    if (!showRaw) {
      const renderMermaid = async () => {
        const mermaidElements = document.querySelectorAll(".mermaid-diagram");
        
        for (const element of Array.from(mermaidElements)) {
          const code = element.getAttribute("data-mermaid");
          if (code) {
            try {
              const id = `mermaid-${mermaidRef.current++}`;
              const { svg } = await mermaid.render(id, code);
              element.innerHTML = svg;
            } catch (error) {
              console.error("Mermaid rendering error:", error);
              element.innerHTML = `<pre class="text-red-600">Error rendering diagram</pre>`;
            }
          }
        }
      };

      renderMermaid();
    }
  }, [content, showRaw]);

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const components = {
    code({ node, inline, className, children, ...props }: any) {
      const match = /language-(\w+)/.exec(className || "");
      const language = match ? match[1] : "";
      
      // Handle mermaid code blocks
      if (language === "mermaid" && !inline) {
        const code = String(children).replace(/\n$/, "");
        return (
          <div 
            className="mermaid-diagram my-4 p-4 bg-gray-50 rounded-lg flex justify-center"
            data-mermaid={code}
          />
        );
      }

      // Regular code blocks
      if (!inline && match) {
        return (
          <SyntaxHighlighter
            style={vscDarkPlus}
            language={language}
            PreTag="div"
            customStyle={{
              margin: "1rem 0",
              borderRadius: "0.375rem",
              fontSize: "0.875rem",
            }}
            {...props}
          >
            {String(children).replace(/\n$/, "")}
          </SyntaxHighlighter>
        );
      }

      // Inline code
      return (
        <code className="bg-gray-100 text-red-600 px-1 py-0.5 rounded text-sm" {...props}>
          {children}
        </code>
      );
    },
    // Enhanced table rendering
    table({ children, ...props }: any) {
      return (
        <div className="overflow-x-auto my-4">
          <table className="min-w-full divide-y divide-gray-200 border border-gray-200 rounded-lg" {...props}>
            {children}
          </table>
        </div>
      );
    },
    thead({ children, ...props }: any) {
      return (
        <thead className="bg-gray-50" {...props}>
          {children}
        </thead>
      );
    },
    th({ children, ...props }: any) {
      return (
        <th className="px-4 py-2 text-left text-xs font-medium text-gray-700 uppercase tracking-wider" {...props}>
          {children}
        </th>
      );
    },
    td({ children, ...props }: any) {
      return (
        <td className="px-4 py-2 text-sm text-gray-900 border-t border-gray-200" {...props}>
          {children}
        </td>
      );
    },
    // Enhanced blockquote
    blockquote({ children, ...props }: any) {
      return (
        <blockquote className="border-l-4 border-blue-500 pl-4 py-2 my-4 bg-blue-50 italic" {...props}>
          {children}
        </blockquote>
      );
    },
    // Enhanced lists
    ul({ children, ...props }: any) {
      return (
        <ul className="list-disc list-inside space-y-1 my-4 ml-4" {...props}>
          {children}
        </ul>
      );
    },
    ol({ children, ...props }: any) {
      return (
        <ol className="list-decimal list-inside space-y-1 my-4 ml-4" {...props}>
          {children}
        </ol>
      );
    },
    // Enhanced headings
    h1({ children, ...props }: any) {
      return (
        <h1 className="text-3xl font-bold my-4 pb-2 border-b border-gray-200" {...props}>
          {children}
        </h1>
      );
    },
    h2({ children, ...props }: any) {
      return (
        <h2 className="text-2xl font-semibold my-3 pb-1 border-b border-gray-100" {...props}>
          {children}
        </h2>
      );
    },
    h3({ children, ...props }: any) {
      return (
        <h3 className="text-xl font-semibold my-3" {...props}>
          {children}
        </h3>
      );
    },
    // Links
    a({ children, href, ...props }: any) {
      return (
        <a 
          href={href}
          className="text-blue-600 hover:text-blue-800 underline"
          target="_blank"
          rel="noopener noreferrer"
          {...props}
        >
          {children}
        </a>
      );
    },
  };

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      <div className="flex justify-between items-center p-4 border-b">
        <div>
          <h3 className="text-lg font-semibold">Markdown Preview</h3>
        </div>
        <div className="flex items-center gap-2">
          <Button
            onClick={() => setShowRaw(!showRaw)}
            variant="outline"
            size="sm"
          >
            {showRaw ? (
              <>
                <Eye className="w-4 h-4 mr-2" />
                Preview
              </>
            ) : (
              <>
                <EyeOff className="w-4 h-4 mr-2" />
                Raw
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

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {showRaw ? (
          <pre className="whitespace-pre-wrap font-mono text-sm bg-gray-50 p-4 rounded-lg">
            {content}
          </pre>
        ) : (
          <div className="prose prose-lg max-w-none">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={components}
            >
              {content}
            </ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}