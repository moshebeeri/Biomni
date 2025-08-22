import { Annotation, END, START, StateGraph } from "@langchain/langgraph";
import { BaseMessage, HumanMessage, AIMessage } from "@langchain/core/messages";
import { BiomniAgent } from "./biomni-agent";

// Define the state for our graph
const BiomniGraphState = Annotation.Root({
  messages: Annotation<BaseMessage[]>({
    reducer: (x, y) => x.concat(y),
  }),
  userId: Annotation<string>(),
  agentId: Annotation<string>(),
  artifacts: Annotation<any[]>({
    reducer: (x, y) => x.concat(y),
    default: () => [],
  }),
  insights: Annotation<string[]>({
    reducer: (x, y) => x.concat(y),
    default: () => [],
  }),
  toolsUsed: Annotation<string[]>({
    reducer: (x, y) => x.concat(y),
    default: () => [],
  }),
});

// Biomni execution node
async function biomniNode(state: typeof BiomniGraphState.State) {
  const lastMessage = state.messages[state.messages.length - 1];
  
  if (!lastMessage || !(lastMessage instanceof HumanMessage)) {
    return state;
  }

  const prompt = lastMessage.content as string;
  const agent = new BiomniAgent(state.userId, state.agentId);
  
  try {
    await agent.initialize();
    
    const responseContent: string[] = [];
    const artifacts: any[] = [];
    const insights: string[] = [];
    const toolsUsed: string[] = [];
    
    // Execute and collect results
    const executeGen = await agent.execute(prompt);
    for await (const message of executeGen) {
      if (message.type === 'step' && message.content) {
        responseContent.push(message.content);
      }
      
      if (message.tool_execution) {
        toolsUsed.push(message.tool_execution.name);
      }
      
      if (message.insight) {
        insights.push(message.insight);
      }
      
      if (message.code_artifact) {
        artifacts.push({
          type: 'code',
          language: message.code_artifact.language,
          content: message.code_artifact.content,
          timestamp: new Date().toISOString()
        });
      }
    }
    
    agent.terminate();
    
    // Create AI message with response
    const aiMessage = new AIMessage({
      content: responseContent.join('\n'),
      additional_kwargs: {
        artifacts: artifacts.length,
        insights: insights.length,
        tools_used: toolsUsed.length
      }
    });
    
    return {
      messages: [aiMessage],
      artifacts,
      insights,
      toolsUsed
    };
    
  } catch (error) {
    console.error('Biomni execution error:', error);
    agent.terminate();
    
    return {
      messages: [
        new AIMessage({
          content: `Error executing biomni agent: ${error instanceof Error ? error.message : String(error)}`,
          additional_kwargs: { error: true }
        })
      ]
    };
  }
}

// Create the biomni graph
export function createBiomniGraph() {
  const workflow = new StateGraph(BiomniGraphState)
    .addNode("biomni", biomniNode)
    .addEdge(START, "biomni")
    .addEdge("biomni", END);
  
  return workflow.compile();
}

// Export for use in v
export { BiomniAgent } from "./biomni-agent";
export type { BiomniMessage } from "./biomni-agent";