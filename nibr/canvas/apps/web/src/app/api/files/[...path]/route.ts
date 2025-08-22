import { NextRequest, NextResponse } from 'next/server';
import { getFileStorage } from '@/lib/storage/file-storage';
import { getSession } from '@/lib/auth/server';

export async function GET(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  try {
    // Check authentication
    const user = await getSession();
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const [userId, ...filePathParts] = params.path;
    const filename = filePathParts.join('/');

    // Security: Users can only access their own files unless admin
    if (userId !== user.id && !user.isAdmin) {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
    }

    const fileStorage = getFileStorage();
    const fileId = filename.split('.')[0];
    const fileBuffer = await fileStorage.getFile(userId, fileId);

    if (!fileBuffer) {
      return NextResponse.json({ error: 'File not found' }, { status: 404 });
    }

    // Determine content type based on extension
    const extension = filename.split('.').pop()?.toLowerCase();
    let contentType = 'application/octet-stream';

    switch (extension) {
      case 'pdf':
        contentType = 'application/pdf';
        break;
      case 'png':
        contentType = 'image/png';
        break;
      case 'jpg':
      case 'jpeg':
        contentType = 'image/jpeg';
        break;
      case 'csv':
        contentType = 'text/csv';
        break;
      case 'json':
        contentType = 'application/json';
        break;
      case 'txt':
        contentType = 'text/plain';
        break;
      case 'py':
        contentType = 'text/x-python';
        break;
      case 'js':
      case 'ts':
        contentType = 'text/javascript';
        break;
    }

    return new NextResponse(fileBuffer, {
      headers: {
        'Content-Type': contentType,
        'Content-Disposition': `inline; filename="${filename}"`,
        'Cache-Control': 'private, max-age=3600'
      }
    });
  } catch (error) {
    console.error('Error serving file:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    // Check authentication
    const user = await getSession();
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const formData = await request.formData();
    const file = formData.get('file') as File;

    if (!file) {
      return NextResponse.json({ error: 'No file provided' }, { status: 400 });
    }

    // Check file size
    const maxSize = parseInt(process.env.MAX_FILE_SIZE || '104857600'); // 100MB default
    if (file.size > maxSize) {
      return NextResponse.json(
        { error: `File too large. Maximum size is ${maxSize / 1048576}MB` },
        { status: 400 }
      );
    }

    const fileStorage = getFileStorage();
    const buffer = Buffer.from(await file.arrayBuffer());

    const result = await fileStorage.uploadFile(
      buffer,
      file.name,
      user.id,
      {
        mimeType: file.type,
        size: file.size
      }
    );

    return NextResponse.json({
      success: true,
      file: {
        id: result.id,
        url: result.url,
        name: file.name,
        size: file.size
      }
    });
  } catch (error) {
    console.error('Error uploading file:', error);
    return NextResponse.json(
      { error: 'Failed to upload file' },
      { status: 500 }
    );
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  try {
    // Check authentication
    const user = await getSession();
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const [userId, fileId] = params.path;

    // Security: Users can only delete their own files unless admin
    if (userId !== user.id && !user.isAdmin) {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
    }

    const fileStorage = getFileStorage();
    const deleted = await fileStorage.deleteFile(userId, fileId);

    if (!deleted) {
      return NextResponse.json({ error: 'File not found' }, { status: 404 });
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Error deleting file:', error);
    return NextResponse.json(
      { error: 'Failed to delete file' },
      { status: 500 }
    );
  }
}