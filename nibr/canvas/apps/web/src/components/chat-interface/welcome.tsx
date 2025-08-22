import { ProgrammingLanguageOptions } from "@opencanvas/shared/types";
import { ThreadPrimitive, useThreadRuntime } from "@assistant-ui/react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { FC, useMemo } from "react";
import { TighterText } from "../ui/header";
import { NotebookPen } from "lucide-react";
import { ProgrammingLanguagesDropdown } from "../ui/programming-lang-dropdown";
import { Button } from "../ui/button";

const QUICK_START_PROMPTS_SEARCH = [
  "Write a market analysis of AI chip manufacturers in 2025",
  "Create a blog post about the latest climate change policies and their impact",
  "Draft an investor update on renewable energy trends this quarter",
  "Write a report on current cybersecurity threats in cloud computing",
  "Analyze the latest developments in quantum computing for a tech newsletter",
  "Create a summary of emerging medical breakthroughs in cancer treatment",
  "Write about the impact of current interest rates on the housing market",
  "Draft an article about breakthroughs in battery technology this year",
  "Analyze current supply chain disruptions in semiconductor manufacturing",
  "Write about how recent AI regulations affect business innovation",
];

const QUICK_START_PROMPTS = [
  "Create a Jupyter notebook for analyzing gene expression data",
  "Write Python code to visualize protein structures",
  "Generate an HTML dashboard for clinical trial results",
  "Create a CSV table with sample patient demographics",
  "Build a Python script to parse FASTA sequences",
  "Write a function to calculate drug-drug interactions",
  "Create a JSON structure for storing genomic variants",
  "Generate an interactive HTML plot for dose-response curves",
  "Write Python code for analyzing CRISPR screening data",
  "Create a Jupyter notebook for PCA analysis of RNA-seq data",
  "Build a simple molecular weight calculator in Python",
  "Generate a markdown report on recent FDA drug approvals",
  "Create an HTML page with an interactive compound structure viewer",
  "Write Python code to query the PubMed database",
];

function getRandomPrompts(prompts: string[], count: number = 4): string[] {
  return [...prompts].sort(() => Math.random() - 0.5).slice(0, count);
}

interface QuickStartButtonsProps {
  handleQuickStart: (
    type: "text" | "code",
    language?: ProgrammingLanguageOptions
  ) => void;
  composer: React.ReactNode;
  searchEnabled: boolean;
}

interface QuickStartPromptsProps {
  searchEnabled: boolean;
}

const QuickStartPrompts = ({ searchEnabled }: QuickStartPromptsProps) => {
  const threadRuntime = useThreadRuntime();

  const handleClick = (text: string) => {
    threadRuntime.append({
      role: "user",
      content: [{ type: "text", text }],
    });
  };

  const selectedPrompts = useMemo(
    () =>
      getRandomPrompts(
        searchEnabled ? QUICK_START_PROMPTS_SEARCH : QUICK_START_PROMPTS
      ),
    [searchEnabled]
  );

  return (
    <div className="flex flex-col w-full gap-2">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 w-full">
        {selectedPrompts.map((prompt, index) => (
          <Button
            key={`quick-start-prompt-${index}`}
            onClick={() => handleClick(prompt)}
            variant="outline"
            className="min-h-[60px] w-full flex items-center justify-center p-6 whitespace-normal text-gray-500 hover:text-gray-700 transition-colors ease-in rounded-2xl"
          >
            <p className="text-center break-words text-sm font-normal">
              {prompt}
            </p>
          </Button>
        ))}
      </div>
    </div>
  );
};

const QuickStartButtons = (props: QuickStartButtonsProps) => {
  const handleLanguageSubmit = (language: ProgrammingLanguageOptions) => {
    props.handleQuickStart("code", language);
  };

  return (
    <div className="flex flex-col gap-8 items-center justify-center w-full">
      <div className="flex flex-col gap-6">
        <p className="text-gray-600 text-sm">Start with a blank canvas</p>
        <div className="flex flex-col gap-4 items-center justify-center w-full">
          <div className="flex flex-row gap-1 items-center justify-center w-full">
            <Button
              variant="outline"
              className="text-gray-500 hover:text-gray-700 transition-colors ease-in rounded-2xl flex items-center justify-center gap-2 w-[250px] h-[64px]"
              onClick={() => props.handleQuickStart("text")}
            >
              New Markdown
              <NotebookPen />
            </Button>
            <ProgrammingLanguagesDropdown handleSubmit={handleLanguageSubmit} />
          </div>
          
          {/* Quick access biomedical formats */}
          <div className="flex flex-wrap gap-2 justify-center">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleLanguageSubmit("other")}
              className="text-xs"
              title="Create SMILES molecule notation"
            >
              🧪 SMILES
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleLanguageSubmit("other")}
              className="text-xs"
              title="Create FASTA sequence file"
            >
              🧬 FASTA
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleLanguageSubmit("other")}
              className="text-xs"
              title="Create VCF variant file"
            >
              🔬 VCF
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleLanguageSubmit("other")}
              className="text-xs"
              title="Create PDB protein structure"
            >
              🦠 PDB
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleLanguageSubmit("json")}
              className="text-xs"
              title="Create clinical trial data"
            >
              📊 Clinical Data
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleLanguageSubmit("json")}
              className="text-xs"
              title="Create Jupyter notebook"
            >
              📓 Jupyter
            </Button>
          </div>
          
          <div className="text-xs text-gray-500 text-center">
            Biomedical Tools: Molecule Viewer • Genome Browser • Sequence Analyzer • Clinical Dashboard • Protein Structure
          </div>
        </div>
      </div>
      <div className="flex flex-col gap-6 mt-2 w-full">
        <p className="text-gray-600 text-sm">or with a message</p>
        {props.composer}
        <QuickStartPrompts searchEnabled={props.searchEnabled} />
      </div>
    </div>
  );
};

interface ThreadWelcomeProps {
  handleQuickStart: (
    type: "text" | "code",
    language?: ProgrammingLanguageOptions
  ) => void;
  composer: React.ReactNode;
  searchEnabled: boolean;
}

export const ThreadWelcome: FC<ThreadWelcomeProps> = (
  props: ThreadWelcomeProps
) => {
  return (
    <ThreadPrimitive.Empty>
      <div className="flex items-center justify-center mt-16 w-full">
        <div className="text-center max-w-3xl w-full">
          <Avatar className="mx-auto">
            <AvatarImage src="/lc_logo.jpg" alt="LangChain Logo" />
            <AvatarFallback>LC</AvatarFallback>
          </Avatar>
          <TighterText className="mt-4 text-lg font-medium">
            What would you like to write today?
          </TighterText>
          <div className="mt-8 w-full">
            <QuickStartButtons
              composer={props.composer}
              handleQuickStart={props.handleQuickStart}
              searchEnabled={props.searchEnabled}
            />
          </div>
        </div>
      </div>
    </ThreadPrimitive.Empty>
  );
};
