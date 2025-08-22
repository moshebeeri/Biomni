import { NextRequest, NextResponse } from 'next/server';
import { getSession } from '@/lib/auth/server';

export async function GET(request: NextRequest) {
  try {
    // Test auth system
    const user = await getSession();
    
    return NextResponse.json({
      status: 'ok',
      message: 'NIBR Biomni Canvas API is running',
      authenticated: user !== null,
      user: user ? {
        id: user.id,
        username: user.username,
        isAdmin: user.isAdmin
      } : null,
      environment: {
        node_version: process.version,
        env: process.env.NODE_ENV || 'development',
        nibr_env: process.env.NIBR_ENVIRONMENT || 'local-dev'
      }
    });
  } catch (error) {
    return NextResponse.json({
      status: 'error',
      message: error.message
    }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const user = await getSession();
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { prompt } = await request.json();
    
    if (!prompt) {
      return NextResponse.json({ error: 'Prompt is required' }, { status: 400 });
    }

    // Simple test of biomni integration
    // In production, this would use the BiomniAgent class
    return NextResponse.json({
      status: 'ok',
      message: 'Biomni test endpoint',
      user: user.username,
      prompt: prompt,
      response: `This is a test response for: "${prompt}". Biomni integration pending.`
    });
  } catch (error) {
    return NextResponse.json({
      status: 'error',
      message: error.message
    }, { status: 500 });
  }
}