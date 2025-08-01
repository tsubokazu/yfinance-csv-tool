import { NextResponse } from 'next/server';

export async function GET() {
  return NextResponse.json({ message: 'API Route is working' });
}

export async function POST() {
  return NextResponse.json({ message: 'POST method is working' });
}