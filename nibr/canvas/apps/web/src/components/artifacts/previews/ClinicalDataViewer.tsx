import React, { useState, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { X, Download, BarChart2, Users, Activity, AlertCircle, TrendingUp } from "lucide-react";

interface ClinicalDataViewerProps {
  data: string;
  onClose: () => void;
}

interface ClinicalMetrics {
  totalPatients: number;
  adverseEvents: number;
  efficacyRate?: number;
  treatmentGroups: string[];
  demographics: {
    ageRange: string;
    maleCount: number;
    femaleCount: number;
  };
}

export function ClinicalDataViewer({ data, onClose }: ClinicalDataViewerProps) {
  const [viewMode, setViewMode] = useState<"table" | "summary" | "charts">("summary");
  
  const parsedData = useMemo(() => {
    try {
      // Try to parse as JSON first
      if (data.trim().startsWith("{") || data.trim().startsWith("[")) {
        return JSON.parse(data);
      }
      
      // Try to parse as CSV
      const lines = data.trim().split("\n");
      if (lines.length > 1 && lines[0].includes(",")) {
        const headers = lines[0].split(",").map(h => h.trim());
        const rows = lines.slice(1).map(line => {
          const values = line.split(",").map(v => v.trim());
          return headers.reduce((obj, header, index) => {
            obj[header] = values[index];
            return obj;
          }, {} as any);
        });
        return rows;
      }
      
      // Return as text if parsing fails
      return data;
    } catch (err) {
      console.error("Error parsing clinical data:", err);
      return data;
    }
  }, [data]);

  const metrics = useMemo((): ClinicalMetrics => {
    if (Array.isArray(parsedData)) {
      // Extract metrics from tabular data
      const patients = parsedData.length;
      const adverseEvents = parsedData.filter((row: any) => 
        row.adverse_event === "Yes" || row.ae === "1"
      ).length;
      
      const treatmentGroups = [...new Set(parsedData.map((row: any) => 
        row.treatment_group || row.cohort || "Unknown"
      ))];
      
      // Demographics
      const males = parsedData.filter((row: any) => 
        row.gender === "M" || row.sex === "Male"
      ).length;
      const females = parsedData.filter((row: any) => 
        row.gender === "F" || row.sex === "Female"
      ).length;
      
      // Age range
      const ages = parsedData
        .map((row: any) => parseInt(row.age))
        .filter(age => !isNaN(age));
      const minAge = Math.min(...ages);
      const maxAge = Math.max(...ages);
      
      return {
        totalPatients: patients,
        adverseEvents,
        efficacyRate: undefined,
        treatmentGroups: treatmentGroups as string[],
        demographics: {
          ageRange: ages.length > 0 ? `${minAge}-${maxAge}` : "N/A",
          maleCount: males,
          femaleCount: females,
        }
      };
    }
    
    return {
      totalPatients: 0,
      adverseEvents: 0,
      treatmentGroups: [],
      demographics: {
        ageRange: "N/A",
        maleCount: 0,
        femaleCount: 0,
      }
    };
  }, [parsedData]);

  const downloadData = () => {
    const blob = new Blob([JSON.stringify(parsedData, null, 2)], { 
      type: "application/json" 
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "clinical_data.json";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      <div className="flex justify-between items-center p-4 border-b">
        <div className="flex items-center gap-3">
          <Activity className="w-5 h-5 text-blue-600" />
          <div>
            <h3 className="text-lg font-semibold">Clinical Data Viewer</h3>
            <p className="text-sm text-gray-600">
              Patient and Trial Data Analysis
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex gap-1 bg-gray-100 rounded-md p-1">
            <Button
              onClick={() => setViewMode("summary")}
              variant={viewMode === "summary" ? "default" : "ghost"}
              size="sm"
            >
              Summary
            </Button>
            <Button
              onClick={() => setViewMode("table")}
              variant={viewMode === "table" ? "default" : "ghost"}
              size="sm"
            >
              Table
            </Button>
            <Button
              onClick={() => setViewMode("charts")}
              variant={viewMode === "charts" ? "default" : "ghost"}
              size="sm"
            >
              Charts
            </Button>
          </div>
          <Button
            onClick={downloadData}
            variant="outline"
            size="sm"
          >
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
          <Button onClick={onClose} variant="ghost" size="sm">
            <X className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {viewMode === "summary" && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* Patient Count Card */}
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <Users className="w-5 h-5 text-blue-600" />
                <span className="text-2xl font-bold text-blue-900">
                  {metrics.totalPatients}
                </span>
              </div>
              <h4 className="text-sm font-medium text-blue-700">Total Patients</h4>
              <p className="text-xs text-blue-600 mt-1">
                Enrolled in study
              </p>
            </div>

            {/* Adverse Events Card */}
            <div className="bg-red-50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <AlertCircle className="w-5 h-5 text-red-600" />
                <span className="text-2xl font-bold text-red-900">
                  {metrics.adverseEvents}
                </span>
              </div>
              <h4 className="text-sm font-medium text-red-700">Adverse Events</h4>
              <p className="text-xs text-red-600 mt-1">
                {metrics.totalPatients > 0 
                  ? `${((metrics.adverseEvents / metrics.totalPatients) * 100).toFixed(1)}% of patients`
                  : "No data"}
              </p>
            </div>

            {/* Treatment Groups Card */}
            <div className="bg-green-50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <TrendingUp className="w-5 h-5 text-green-600" />
                <span className="text-2xl font-bold text-green-900">
                  {metrics.treatmentGroups.length}
                </span>
              </div>
              <h4 className="text-sm font-medium text-green-700">Treatment Arms</h4>
              <p className="text-xs text-green-600 mt-1">
                {metrics.treatmentGroups.slice(0, 2).join(", ")}
                {metrics.treatmentGroups.length > 2 && "..."}
              </p>
            </div>

            {/* Demographics Card */}
            <div className="bg-purple-50 rounded-lg p-4 col-span-full">
              <h4 className="text-sm font-medium text-purple-700 mb-3">Demographics</h4>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <span className="text-xs text-purple-600">Age Range</span>
                  <p className="font-semibold text-purple-900">{metrics.demographics.ageRange}</p>
                </div>
                <div>
                  <span className="text-xs text-purple-600">Male</span>
                  <p className="font-semibold text-purple-900">{metrics.demographics.maleCount}</p>
                </div>
                <div>
                  <span className="text-xs text-purple-600">Female</span>
                  <p className="font-semibold text-purple-900">{metrics.demographics.femaleCount}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {viewMode === "table" && (
          <div className="overflow-x-auto">
            {Array.isArray(parsedData) ? (
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    {Object.keys(parsedData[0] || {}).map(key => (
                      <th
                        key={key}
                        className="px-4 py-2 text-left text-xs font-medium text-gray-700 uppercase tracking-wider"
                      >
                        {key.replace(/_/g, " ")}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {parsedData.slice(0, 100).map((row: any, index: number) => (
                    <tr key={index} className="hover:bg-gray-50">
                      {Object.values(row).map((value: any, cellIndex: number) => (
                        <td
                          key={cellIndex}
                          className="px-4 py-2 text-sm text-gray-900"
                        >
                          {String(value)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <pre className="p-4 bg-gray-50 rounded-lg text-sm">
                {typeof parsedData === "string" ? parsedData : JSON.stringify(parsedData, null, 2)}
              </pre>
            )}
          </div>
        )}

        {viewMode === "charts" && (
          <div className="space-y-6">
            {/* Simple bar chart representation */}
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="text-sm font-medium mb-3 flex items-center gap-2">
                <BarChart2 className="w-4 h-4" />
                Treatment Group Distribution
              </h4>
              <div className="space-y-2">
                {metrics.treatmentGroups.map((group, index) => {
                  const count = Array.isArray(parsedData) 
                    ? parsedData.filter((row: any) => 
                        (row.treatment_group || row.cohort) === group
                      ).length
                    : 0;
                  const percentage = metrics.totalPatients > 0 
                    ? (count / metrics.totalPatients) * 100 
                    : 0;
                  
                  return (
                    <div key={index} className="flex items-center gap-3">
                      <span className="text-sm w-32 truncate">{group}</span>
                      <div className="flex-1 bg-gray-200 rounded-full h-6 relative">
                        <div
                          className="bg-blue-500 h-full rounded-full flex items-center justify-end pr-2"
                          style={{ width: `${percentage}%` }}
                        >
                          <span className="text-xs text-white font-medium">
                            {count}
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Gender distribution */}
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="text-sm font-medium mb-3">Gender Distribution</h4>
              <div className="flex gap-4">
                <div className="flex-1 text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {metrics.demographics.maleCount}
                  </div>
                  <div className="text-sm text-gray-600">Male</div>
                </div>
                <div className="flex-1 text-center">
                  <div className="text-2xl font-bold text-pink-600">
                    {metrics.demographics.femaleCount}
                  </div>
                  <div className="text-sm text-gray-600">Female</div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}