#!/usr/bin/env python3
"""
FastAPI application for ProPresenter txt to .pro conversion
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
import tempfile
import uuid
from pathlib import Path

# Add proto_generated to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'proto_generated'))

from txt_to_pro import parse_txt_file, load_template, txt_to_pro

app = FastAPI(
    title="ProPresenter Converter API",
    description="Convert text files to ProPresenter .pro format",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store template path (can be configured)
TEMPLATE_PATH = os.getenv("TEMPLATE_PATH", "/mnt/c/Users/joelv/Downloads/No One Like The Lord.proBundle/No One Like The Lord.pro")


@app.get("/")
async def root():
    """API health check"""
    return {
        "status": "ok",
        "message": "ProPresenter Converter API",
        "version": "1.0.0",
        "endpoints": {
            "convert": "/convert",
            "health": "/health",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    template_exists = os.path.exists(TEMPLATE_PATH)

    return {
        "status": "healthy" if template_exists else "degraded",
        "template_configured": template_exists,
        "template_path": TEMPLATE_PATH
    }


@app.post("/convert")
async def convert_txt_to_pro(
    file: UploadFile = File(..., description="Text file with song lyrics"),
    template: UploadFile = File(None, description="Optional: Custom template .pro file")
):
    """
    Convert a text file to ProPresenter .pro format

    **Input format:**
    ```
    # Song Title: Amazing Grace

    [Verse 1]
    Amazing grace how sweet the sound
    That saved a wretch like me

    [Chorus]
    How sweet the sound
    That saved a wretch like me
    ```

    **Returns:** .pro file ready for ProPresenter
    """

    # Validate input file
    if not file.filename.endswith('.txt'):
        raise HTTPException(status_code=400, detail="Input file must be a .txt file")

    # Create temp directory for processing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)

        # Save uploaded txt file
        txt_path = temp_dir_path / file.filename
        with open(txt_path, 'wb') as f:
            content = await file.read()
            f.write(content)

        # Determine template path
        if template:
            if not template.filename.endswith('.pro'):
                raise HTTPException(status_code=400, detail="Template file must be a .pro file")

            template_path = temp_dir_path / template.filename
            with open(template_path, 'wb') as f:
                template_content = await template.read()
                f.write(template_content)
        else:
            template_path = TEMPLATE_PATH
            if not os.path.exists(template_path):
                raise HTTPException(
                    status_code=500,
                    detail="No template configured. Please upload a template file."
                )

        # Parse to get song title
        try:
            data = parse_txt_file(str(txt_path))
            song_title = data['title']
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse txt file: {str(e)}")

        # Generate output path
        output_filename = f"{song_title}.pro".replace(" ", "_")
        output_path = temp_dir_path / output_filename

        # Convert
        try:
            success = txt_to_pro(str(txt_path), str(template_path), str(output_path))
            if not success:
                raise HTTPException(status_code=500, detail="Conversion failed")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Conversion error: {str(e)}")

        # Return the file
        if not output_path.exists():
            raise HTTPException(status_code=500, detail="Output file was not created")

        # Read file into memory before temp directory is deleted
        with open(output_path, 'rb') as f:
            file_content = f.read()

        # Return as bytes response
        from fastapi.responses import Response
        return Response(
            content=file_content,
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={output_filename}"
            }
        )


@app.post("/parse")
async def parse_txt(file: UploadFile = File(..., description="Text file with song lyrics")):
    """
    Parse a text file and return the song structure without converting

    **Useful for:** Validating input before conversion
    """

    if not file.filename.endswith('.txt'):
        raise HTTPException(status_code=400, detail="Input file must be a .txt file")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        txt_path = temp_dir_path / file.filename

        with open(txt_path, 'wb') as f:
            content = await file.read()
            f.write(content)

        try:
            data = parse_txt_file(str(txt_path))

            # Calculate statistics
            total_slides = sum(len(section['slides']) for section in data['sections'])

            return {
                "title": data['title'],
                "sections": [
                    {
                        "name": section['name'],
                        "slide_count": len(section['slides']),
                        "slides": [
                            {
                                "line1": slide[0] if len(slide) > 0 else "",
                                "line2": slide[1] if len(slide) > 1 else ""
                            }
                            for slide in section['slides']
                        ]
                    }
                    for section in data['sections']
                ],
                "statistics": {
                    "section_count": len(data['sections']),
                    "total_slides": total_slides
                }
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse txt file: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
