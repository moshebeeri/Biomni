import { ProgrammingLanguageOptions } from "@opencanvas/shared/types";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "./dropdown-menu";
import { Code } from "lucide-react";
import { Button } from "./button";
import { TooltipIconButton } from "./assistant-ui/tooltip-icon-button";

interface ProgrammingLanguageListProps {
  handleSubmit: (portLanguage: ProgrammingLanguageOptions) => Promise<void>;
}

export function ProgrammingLanguageList(
  props: Readonly<ProgrammingLanguageListProps>
) {
  return (
    <div className="flex flex-col gap-3 items-center w-full text-left">
      <TooltipIconButton
        tooltip="PHP"
        variant="ghost"
        className="transition-colors w-full h-fit"
        delayDuration={400}
        onClick={async () => await props.handleSubmit("php")}
      >
        <p>PHP</p>
      </TooltipIconButton>
      <TooltipIconButton
        tooltip="TypeScript"
        variant="ghost"
        className="transition-colors w-full h-fit px-1 py-1"
        delayDuration={400}
        onClick={async () => await props.handleSubmit("typescript")}
      >
        <p>TypeScript</p>
      </TooltipIconButton>
      <TooltipIconButton
        tooltip="JavaScript"
        variant="ghost"
        className="transition-colors w-full h-fit"
        delayDuration={400}
        onClick={async () => await props.handleSubmit("javascript")}
      >
        <p>JavaScript</p>
      </TooltipIconButton>
      <TooltipIconButton
        tooltip="C++"
        variant="ghost"
        className="transition-colors w-full h-fit"
        delayDuration={400}
        onClick={async () => await props.handleSubmit("cpp")}
      >
        <p>C++</p>
      </TooltipIconButton>
      <TooltipIconButton
        tooltip="Java"
        variant="ghost"
        className="transition-colors w-full h-fit"
        delayDuration={400}
        onClick={async () => await props.handleSubmit("java")}
      >
        <p>Java</p>
      </TooltipIconButton>
      <TooltipIconButton
        tooltip="Python"
        variant="ghost"
        className="transition-colors w-full h-fit"
        delayDuration={400}
        onClick={async () => await props.handleSubmit("python")}
      >
        <p>Python</p>
      </TooltipIconButton>
      <TooltipIconButton
        tooltip="HTML"
        variant="ghost"
        className="transition-colors w-full h-fit"
        delayDuration={400}
        onClick={async () => await props.handleSubmit("html")}
      >
        <p>HTML</p>
      </TooltipIconButton>
      <TooltipIconButton
        tooltip="SQL"
        variant="ghost"
        className="transition-colors w-full h-fit"
        delayDuration={400}
        onClick={async () => await props.handleSubmit("sql")}
      >
        <p>SQL</p>
      </TooltipIconButton>
    </div>
  );
}

const LANGUAGES: Array<{ label: string; key: ProgrammingLanguageOptions; category?: string }> = [
  // Programming Languages
  { label: "Python", key: "python", category: "Programming" },
  { label: "JavaScript", key: "javascript", category: "Programming" },
  { label: "TypeScript", key: "typescript", category: "Programming" },
  { label: "Java", key: "java", category: "Programming" },
  { label: "C++", key: "cpp", category: "Programming" },
  { label: "Rust", key: "rust", category: "Programming" },
  { label: "PHP", key: "php", category: "Programming" },
  
  // Web & Data
  { label: "HTML", key: "html", category: "Web" },
  { label: "SQL", key: "sql", category: "Data" },
  { label: "JSON", key: "json", category: "Data" },
  { label: "CSV/Table", key: "other", category: "Data" },
  { label: "XML", key: "xml", category: "Data" },
  { label: "Jupyter Notebook", key: "json", category: "Data" },
  
  // Chemistry & Drug Discovery
  { label: "SMILES (Molecule)", key: "other", category: "Chemistry" },
  { label: "MOL/SDF (Structure)", key: "other", category: "Chemistry" },
  { label: "PDB (Protein)", key: "other", category: "Chemistry" },
  
  // Genomics & Bioinformatics
  { label: "FASTA (Sequence)", key: "other", category: "Genomics" },
  { label: "VCF (Variants)", key: "other", category: "Genomics" },
  { label: "BED (Genomic Regions)", key: "other", category: "Genomics" },
  { label: "BAM/SAM (Alignments)", key: "other", category: "Genomics" },
  { label: "GFF/GTF (Annotations)", key: "other", category: "Genomics" },
  { label: "GenBank (Sequence)", key: "other", category: "Genomics" },
  
  // Clinical & Research
  { label: "Clinical Trial Data", key: "json", category: "Clinical" },
  { label: "Patient Data (CSV)", key: "other", category: "Clinical" },
];

export const ProgrammingLanguagesDropdown = ({
  handleSubmit,
}: {
  handleSubmit: (portLanguage: ProgrammingLanguageOptions) => void;
}) => {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          className="text-gray-500 hover:text-gray-700 transition-colors ease-in rounded-2xl flex items-center justify-center gap-2 w-[250px] h-[64px]"
        >
          New Code File
          <Code />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="max-h-[600px] w-[280px] overflow-y-auto scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100">
        <DropdownMenuLabel>Select File Type</DropdownMenuLabel>
        
        {/* Group languages by category */}
        {["Programming", "Web", "Data", "Chemistry", "Genomics", "Clinical"].map(category => {
          const categoryLanguages = LANGUAGES.filter(lang => lang.category === category);
          if (categoryLanguages.length === 0) return null;
          
          return (
            <div key={category}>
              <DropdownMenuLabel className="text-xs text-gray-500 mt-2">
                {category}
              </DropdownMenuLabel>
              {categoryLanguages.map((lang) => (
                <DropdownMenuItem
                  key={`${category}-${lang.label}`}
                  onSelect={() => handleSubmit(lang.key)}
                  className="flex items-center justify-start gap-1 pl-4"
                >
                  {lang.label}
                </DropdownMenuItem>
              ))}
            </div>
          );
        })}
      </DropdownMenuContent>
    </DropdownMenu>
  );
};
