"use client";

import React, { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { X, ZoomIn, ZoomOut, Home, ChevronLeft, ChevronRight, Dna } from "lucide-react";

interface GenomeBrowserProps {
  data: string;
  fileType: "bed" | "vcf" | "bam" | "fasta" | "gff" | "gtf";
  onClose: () => void;
}

export function GenomeBrowser({ data, fileType, onClose }: GenomeBrowserProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const browserRef = useRef<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentLocus, setCurrentLocus] = useState("chr1:1-1000000");

  useEffect(() => {
    if (!containerRef.current) return;

    const initBrowser = async () => {
      try {
        // Dynamic import to avoid SSR issues
        const igv = (await import('igv')).default || await import('igv');
        
        // Create a blob from the data
        const blob = new Blob([data], { type: "text/plain" });
        const url = URL.createObjectURL(blob);

        // IGV configuration
        const options = {
          genome: "hg38",
          locus: currentLocus,
          tracks: [
            {
              name: `${fileType.toUpperCase()} Track`,
              url: url,
              format: fileType,
              displayMode: fileType === "vcf" ? "EXPANDED" : "COLLAPSED",
              height: 100,
              autoHeight: false,
            }
          ]
        };

        // Create browser
        const browser = await igv.createBrowser(containerRef.current, options);
        browserRef.current = browser;
        setIsLoading(false);
      } catch (err) {
        console.error("Error initializing genome browser:", err);
        setError("Failed to initialize genome browser");
        setIsLoading(false);
      }
    };

    initBrowser();

    return () => {
      if (browserRef.current) {
        try {
          igv.removeBrowser(browserRef.current);
        } catch (e) {
          // Ignore cleanup errors
        }
      }
    };
  }, [data, fileType]);

  const handleZoomIn = () => {
    if (browserRef.current) {
      browserRef.current.zoomIn();
    }
  };

  const handleZoomOut = () => {
    if (browserRef.current) {
      browserRef.current.zoomOut();
    }
  };

  const handleHome = () => {
    if (browserRef.current) {
      browserRef.current.search(currentLocus);
    }
  };

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      <div className="flex justify-between items-center p-4 border-b">
        <div>
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Dna className="w-5 h-5" />
            Genome Browser
          </h3>
          <p className="text-sm text-gray-600">
            Viewing {fileType.toUpperCase()} file • {currentLocus}
          </p>
        </div>
        <Button onClick={onClose} variant="ghost" size="sm">
          <X className="w-4 h-4" />
        </Button>
      </div>

      {/* Controls */}
      <div className="flex items-center gap-2 p-2 border-b bg-gray-50">
        <Button
          onClick={handleHome}
          variant="outline"
          size="sm"
          title="Reset view"
        >
          <Home className="w-4 h-4" />
        </Button>
        <div className="flex items-center gap-1">
          <Button
            onClick={handleZoomOut}
            variant="outline"
            size="sm"
            title="Zoom out"
          >
            <ZoomOut className="w-4 h-4" />
          </Button>
          <Button
            onClick={handleZoomIn}
            variant="outline"
            size="sm"
            title="Zoom in"
          >
            <ZoomIn className="w-4 h-4" />
          </Button>
        </div>
        <div className="ml-auto text-xs text-gray-500">
          Powered by IGV.js
        </div>
      </div>

      {/* Browser Container */}
      <div className="flex-1 relative">
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-white z-10">
            <div className="text-gray-500">Loading genome browser...</div>
          </div>
        )}
        {error && (
          <div className="absolute inset-0 flex items-center justify-center bg-white z-10">
            <div className="text-red-500">{error}</div>
          </div>
        )}
        <div
          ref={containerRef}
          className="w-full h-full"
          style={{ minHeight: "400px" }}
        />
      </div>
    </div>
  );
}