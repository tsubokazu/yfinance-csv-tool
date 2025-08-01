import { NextRequest, NextResponse } from 'next/server';

const BACKEND_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  console.log('AI Backtest API - Request received');
  
  try {
    const body = await request.json();
    console.log('AI Backtest API - Request body:', body);
    
    const authorization = request.headers.get('authorization');
    console.log('AI Backtest API - Authorization header:', authorization ? 'Present' : 'Missing');
    
    const backendUrl = `${BACKEND_BASE_URL}/trading/ai-backtest`;
    console.log('AI Backtest API - Backend URL:', backendUrl);
    
    const backendResponse = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(authorization && { 'Authorization': authorization }),
      },
      body: JSON.stringify(body),
    });

    console.log('AI Backtest API - Backend response status:', backendResponse.status);

    const responseData = await backendResponse.json();
    console.log('AI Backtest API - Backend response data:', responseData);

    if (!backendResponse.ok) {
      return NextResponse.json(
        responseData,
        { status: backendResponse.status }
      );
    }

    return NextResponse.json(responseData);
  } catch (error) {
    console.error('AI Backtest API Error:', error);
    return NextResponse.json(
      { 
        detail: 'バックテストAPIの呼び出しに失敗しました',
        error: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}