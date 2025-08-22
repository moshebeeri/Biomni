import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  // For development - return a mock user session
  return NextResponse.json({
    user: {
      id: 'dev_user_001',
      email: 'admin@example.com',
      username: 'admin',
      isAdmin: true
    }
  });
}