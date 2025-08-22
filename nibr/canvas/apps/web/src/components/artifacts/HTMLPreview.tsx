"use client";

import React, { useMemo } from "react";
import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import { Button } from "@/components/ui/button";
import { X } from "lucide-react";

interface HTMLPreviewProps {
  code: string;
  onClose: () => void;
  title?: string;
}

export function HTMLPreview({ code, onClose, title = "HTML Preview" }: HTMLPreviewProps) {
  // Create a safe HTML document with proper sandboxing
  const srcDoc = useMemo(() => {
    // Add base tag to handle relative URLs and sandbox the content
    const sandboxedHtml = `
      <!DOCTYPE html>
      <html>
        <head>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <base target="_blank">
          <style>
            /* Reset some styles for better isolation */
            body { 
              margin: 0; 
              padding: 8px;
              font-family: system-ui, -apple-system, sans-serif;
            }
          </style>
        </head>
        <body>
          ${code.replace(/<script/gi, '<!-- script').replace(/<\/script>/gi, '</script -->')}
        </body>
      </html>
    `;
    return sandboxedHtml;
  }, [code]);

  return (
    <Card className="w-full h-full overflow-hidden">
      <Tabs defaultValue="preview" className="w-full h-full flex flex-col">
        <div className="px-4 pt-4 pb-2 border-b flex justify-between items-center">
          <div>
            <h3 className="text-sm font-medium text-muted-foreground mb-2">{title}</h3>
            <TabsList className="grid w-full max-w-[200px] grid-cols-2">
              <TabsTrigger value="preview">Preview</TabsTrigger>
              <TabsTrigger value="code">Code</TabsTrigger>
            </TabsList>
          </div>
          <Button onClick={onClose} variant="ghost" size="sm">
            <X className="w-4 h-4" />
          </Button>
        </div>
        
        <TabsContent value="preview" className="flex-1 p-4">
          <div className="w-full h-full min-h-[400px] border rounded-lg overflow-hidden bg-white">
            <iframe
              srcDoc={srcDoc}
              title={title}
              className="w-full h-full"
              sandbox="allow-same-origin"
              style={{ minHeight: "400px" }}
            />
          </div>
        </TabsContent>
        
        <TabsContent value="code" className="flex-1 overflow-auto p-0">
          <SyntaxHighlighter 
            language="html" 
            style={vscDarkPlus}
            customStyle={{
              margin: 0,
              borderRadius: 0,
              fontSize: "14px"
            }}
          >
            {code}
          </SyntaxHighlighter>
        </TabsContent>
      </Tabs>
    </Card>
  );
}