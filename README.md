# LA Mini Project - Image Color Manipulation

## Problem Statement
Matrix Multiplication - Manipulate image colours similar to Photo Filters for Images

## Tech Stack
- FastAPI backend for image processing API
- Custom HTML/CSS/JavaScript frontend with KaTeX for LaTeX rendering
- NumPy + Pillow for matrix-based transformations

## Core Matrix Operations
- **Color Matrix Transforms** (3×3 RGB multiplication): 9 filter presets + custom blending
- **Hue Rotation**: YIQ color space basis change for rotation math
- **Tone Controls**: Exposure, contrast, saturation via matrix operations
- **Grayscale Projection**: Orthogonal projection onto luminance vector
- **Vibrance Boost**: Selective saturation amplification

## Advanced LA Features
- **Least Squares Color Correction**: Solves `min_X ||AX - B||²_F` for optimal color mapping
- **PCA Compression**: Eigendecomposition + reconstruction at reduced rank (k=1,2,3)
- **Covariance Analysis**: Full color covariance matrix from pixel distribution

## Dashboard & Analysis 
- **Transformation Diagnostics**: Rank, nullity, determinant, condition number, invertibility
- **Matrix Properties**: Trace, Frobenius norm, RREF via Gaussian elimination
- **Eigenanalysis**: Dominant eigenvector, explained variance per component
- **Color Statistics**: Mean RGB, standard deviation, dynamic range

## UI Features
- **Live Preview**: Real-time split/original/edited view modes
- **Interactive Controls**: Sliders for all 14 parameters with smart tooltips 
- **Formula Rendering**: KaTeX + safe math parser for tooltip formulas

## Setup & Run

**Requirements**: Python 3.8+

**Installation**:
```bash
python -m venv venv

# On Windows:
venv/Scripts/activate          
# On Unix/Mac
source venv/bin/activate

pip install -r requirements.txt
```

**Start the App**:
```bash
python app.py
```
The server will start on `http://127.0.0.1:8000` with hot-reload enabled. Upload an image and adjust controls to see live matrix transforms and LA metrics update in real-time.

## Project Structure
- `app.py`: Single app entrypoint + FastAPI routes
- `src/filter_matrices.py`: Filter presets, hue rotation, tonal/enhancement controls
- `src/la_core.py`: Matrix operations, RREF, rank, determinant, structure analysis
- `src/analysis.py`: Least squares correction, eigendecomposition, PCA, color statistics
- `src/image_pipeline.py`: Full pipeline orchestration + response payload
- `frontend/index.html`: UI layout (images left, controls right)
- `frontend/styles.css`: Professional dark theme with modern gradients
- `frontend/app.js`: Live controls, KaTeX formula rendering, smart tooltips
- `draft.md`: Project report
