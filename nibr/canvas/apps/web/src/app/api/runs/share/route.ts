import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  const { runId } = await req.json();

  if (!runId) {
    return new NextResponse(
      JSON.stringify({
        error: "`runId` is required to share run.",
      }),
      {
        status: 400,
        headers: { "Content-Type": "application/json" },
      }
    );
  }

  // Mock implementation - return a LangSmith-compatible format URL
  // The GraphContext expects this specific format with /public/ in the path
  const shareId = runId.substring(0, 8); // Use first 8 chars of runId as share ID
  const sharedRunURL = `https://smith.langchain.com/public/${shareId}/r`;

  console.log(`Mock sharing run ${runId} - returning LangSmith-format URL: ${sharedRunURL}`);

  return new NextResponse(JSON.stringify({ sharedRunURL }), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}