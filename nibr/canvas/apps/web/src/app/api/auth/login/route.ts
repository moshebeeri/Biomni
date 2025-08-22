import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { username, password } = body;

    // For development - accept any credentials that look like our test accounts
    const validCredentials = [
      { username: 'admin@example.com', password: 'admin' },
      { username: 'researcher@example.com', password: 'researcher' },
      { username: 'scientist@example.com', password: 'scientist' },
    ];

    const isValid = validCredentials.some(cred => 
      cred.username === username && cred.password === password
    );

    if (isValid) {
      return NextResponse.json({ 
        success: true, 
        message: 'Login successful',
        redirect: '/'
      });
    } else {
      return NextResponse.json({ 
        success: false, 
        error: 'Invalid credentials' 
      }, { status: 401 });
    }
  } catch (error) {
    return NextResponse.json({ 
      success: false, 
      error: 'Internal server error' 
    }, { status: 500 });
  }
}