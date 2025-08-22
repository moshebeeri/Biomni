import { NextRequest, NextResponse } from 'next/server';
import { getAuthService } from '@/lib/auth/ad-auth';

export async function GET(request: NextRequest) {
  try {
    if (process.env.NODE_ENV !== 'development') {
      return NextResponse.json(
        { error: 'Test accounts only available in development' },
        { status: 403 }
      );
    }
    
    const authService = getAuthService();
    const accounts = authService.getTestAccounts();
    
    return NextResponse.json({
      accounts: accounts
    });
  } catch (error) {
    console.error('Get test accounts error:', error);
    return NextResponse.json(
      { error: 'Failed to get test accounts' },
      { status: 500 }
    );
  }
}
