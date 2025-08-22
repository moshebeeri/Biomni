import { NextRequest, NextResponse } from "next/server";

// Mock feedback storage (in production, this would be stored in a database)
const feedbackStore = new Map<string, any>();

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { runId, feedbackKey, score, comment } = body;

    if (!runId || !feedbackKey) {
      return NextResponse.json(
        { error: "`runId` and `feedbackKey` are required." },
        { status: 400 }
      );
    }

    // Store feedback in mock storage
    const feedbackId = `${runId}-${feedbackKey}`;
    const feedback = {
      id: feedbackId,
      runId,
      feedbackKey,
      score,
      comment,
      createdAt: new Date().toISOString(),
    };
    
    feedbackStore.set(feedbackId, feedback);
    console.log(`Mock storing feedback for run ${runId}: ${feedbackKey} = ${score}`);

    return NextResponse.json(
      { success: true, feedback: feedback },
      { status: 200 }
    );
  } catch (error) {
    console.error("Failed to process feedback request:", error);

    return NextResponse.json(
      { error: "Failed to submit feedback." },
      { status: 500 }
    );
  }
}

export async function GET(req: NextRequest) {
  try {
    const searchParams = req.nextUrl.searchParams;
    const runId = searchParams.get("runId");
    const feedbackKey = searchParams.get("feedbackKey");

    if (!runId || !feedbackKey) {
      return new NextResponse(
        JSON.stringify({
          error: "`runId` and `feedbackKey` are required.",
        }),
        {
          status: 400,
          headers: { "Content-Type": "application/json" },
        }
      );
    }

    // Retrieve feedback from mock storage
    const feedbackId = `${runId}-${feedbackKey}`;
    const feedback = feedbackStore.get(feedbackId);
    const runFeedback = feedback ? [feedback] : [];

    console.log(`Mock retrieving feedback for run ${runId}: ${feedbackKey}`);

    return new NextResponse(
      JSON.stringify({
        feedback: runFeedback,
      }),
      {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }
    );
  } catch (error) {
    console.error("Failed to fetch feedback:", error);
    return NextResponse.json(
      { error: "Failed to fetch feedback." },
      { status: 500 }
    );
  }
}