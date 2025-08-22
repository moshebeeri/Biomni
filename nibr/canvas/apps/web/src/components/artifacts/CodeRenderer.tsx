import { ArtifactCodeV3 } from "@opencanvas/shared/types";
import React, { MutableRefObject, useEffect, useState } from "react";
import CodeMirror, { EditorView } from "@uiw/react-codemirror";
import { javascript } from "@codemirror/lang-javascript";
import { cpp } from "@codemirror/lang-cpp";
import { java } from "@codemirror/lang-java";
import { php } from "@codemirror/lang-php";
import { python } from "@codemirror/lang-python";
import { html } from "@codemirror/lang-html";
import { sql } from "@codemirror/lang-sql";
import { json } from "@codemirror/lang-json";
import { rust } from "@codemirror/lang-rust";
import { xml } from "@codemirror/lang-xml";
import { clojure } from "@nextjournal/lang-clojure";
import { csharp } from "@replit/codemirror-lang-csharp";
import styles from "./CodeRenderer.module.css";
import { cleanContent } from "@/lib/normalize_string";
import { cn } from "@/lib/utils";
import { CopyText } from "./components/CopyText";
import { getArtifactContent } from "@opencanvas/shared/utils/artifacts";
import { useGraphContext } from "@/contexts/GraphContext";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export interface CodeRendererProps {
  editorRef: MutableRefObject<EditorView | null>;
  isHovering: boolean;
}

const getLanguageExtension = (language: string) => {
  switch (language) {
    case "javascript":
      return javascript({ jsx: true, typescript: false });
    case "typescript":
      return javascript({ jsx: true, typescript: true });
    case "cpp":
      return cpp();
    case "java":
      return java();
    case "php":
      return php();
    case "python":
      return python();
    case "html":
      return html();
    case "sql":
      return sql();
    case "json":
      return json();
    case "rust":
      return rust();
    case "xml":
      return xml();
    case "clojure":
      return clojure();
    case "csharp":
      return csharp();
    default:
      return [];
  }
};

export function CodeRendererComponent(props: Readonly<CodeRendererProps>) {
  const { graphData } = useGraphContext();
  const {
    artifact,
    isStreaming,
    updateRenderedArtifactRequired,
    firstTokenReceived,
    setArtifactContent,
    setUpdateRenderedArtifactRequired,
  } = graphData;

  const artifactContent = artifact ? getArtifactContent(artifact) as ArtifactCodeV3 : null;
  const isHtml = artifactContent?.language === "html";
  const [activeTab, setActiveTab] = useState<"code" | "preview">(isHtml ? "preview" : "code");

  useEffect(() => {
    if (updateRenderedArtifactRequired) {
      setUpdateRenderedArtifactRequired(false);
    }
  }, [updateRenderedArtifactRequired]);

  // Set active tab to preview when HTML artifact is loaded
  useEffect(() => {
    if (isHtml && activeTab === "code") {
      setActiveTab("preview");
    }
  }, [isHtml]);

  if (!artifact || !artifactContent) {
    return null;
  }

  const extensions = [getLanguageExtension(artifactContent.language)];

  if (!artifactContent.code) {
    return null;
  }

  const isEditable = !isStreaming;

  // For HTML, show tabs with preview
  if (isHtml) {
    return (
      <div className="relative h-full">
        <style jsx global>{`
          .pulse-code .cm-content {
            animation: codePulse 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite;
          }

          @keyframes codePulse {
            0%,
            100% {
              opacity: 1;
            }
            50% {
              opacity: 0.3;
            }
          }
        `}</style>
        
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as "code" | "preview")} className="h-full">
          <div className="flex justify-between items-center px-4 py-2 border-b">
            <TabsList>
              <TabsTrigger value="code">Code</TabsTrigger>
              <TabsTrigger value="preview">Preview</TabsTrigger>
            </TabsList>
            {props.isHovering && activeTab === "code" && (
              <CopyText currentArtifactContent={artifactContent} />
            )}
          </div>
          
          <TabsContent value="code" className="h-full mt-0">
            <CodeMirror
              editable={isEditable}
              className={cn(
                "w-full min-h-full",
                styles.codeMirrorCustom,
                isStreaming && !firstTokenReceived ? "pulse-code" : ""
              )}
              value={cleanContent(artifactContent.code)}
              height="800px"
              extensions={extensions}
              onChange={(c) => setArtifactContent(artifactContent.index, c)}
              onCreateEditor={(view) => {
                props.editorRef.current = view;
              }}
            />
          </TabsContent>
          
          <TabsContent value="preview" className="h-full mt-0 p-4">
            <div className="w-full h-full min-h-[600px] border rounded-lg overflow-hidden bg-white">
              <iframe
                srcDoc={artifactContent.code}
                title="HTML Preview"
                className="w-full h-full"
                sandbox="allow-scripts allow-same-origin"
                style={{ minHeight: "600px" }}
              />
            </div>
          </TabsContent>
        </Tabs>
      </div>
    );
  }

  // For non-HTML, show regular code editor
  return (
    <div className="relative">
      <style jsx global>{`
        .pulse-code .cm-content {
          animation: codePulse 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }

        @keyframes codePulse {
          0%,
          100% {
            opacity: 1;
          }
          50% {
            opacity: 0.3;
          }
        }
      `}</style>
      {props.isHovering && (
        <div className="absolute top-0 right-4 z-10">
          <CopyText currentArtifactContent={artifactContent} />
        </div>
      )}
      <CodeMirror
        editable={isEditable}
        className={cn(
          "w-full min-h-full",
          styles.codeMirrorCustom,
          isStreaming && !firstTokenReceived ? "pulse-code" : ""
        )}
        value={cleanContent(artifactContent.code)}
        height="800px"
        extensions={extensions}
        onChange={(c) => setArtifactContent(artifactContent.index, c)}
        onCreateEditor={(view) => {
          props.editorRef.current = view;
        }}
      />
    </div>
  );
}

export const CodeRenderer = React.memo(CodeRendererComponent);
