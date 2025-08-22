import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  // For development - just return success
  return NextResponse.json({ success: true });
}