# 🌊 Flood WebGIS HEC-RAS

Hệ thống WebGIS mô phỏng ngập lụt thực tế sử dụng HEC-RAS và Leaflet.

## 📋 Tổng quan

Flood WebGIS HEC-RAS là một nền tảng mô phỏng ngập lụt theo yêu cầu, cho phép người dùng:

- Nhập thông số kịch bản mô phỏng (lượng mưa, thời gian)
- Gửi yêu cầu đến HEC-RAS chạy trên Windows PC từ xa
- Xem kết quả ngập lụt trực tiếp trên WebGIS

## 🏗️ Kiến trúc
Squarespace → Leaflet WebGIS → FastAPI Backend → Job Queue → HEC-RAS Agent → HEC-RAS
↓
GIS Processing
↓
GeoTIFF/COG
↓
Storage
↓
Leaflet WebGIS ←───────────────────────────────────────────────────────────────┘

### Công nghệ sử dụng

- **Frontend**: Leaflet.js, HTML, CSS, JavaScript
- **Backend**: Python, FastAPI
- **Database**: Neon PostgreSQL
- **GIS Processing**: GDAL, Rasterio, GeoPandas
- **Raster**: GeoTIFF, Cloud Optimized GeoTIFF (COG)
- **Hydraulic Model**: HEC-RAS (Windows PC)

## 📦 Cấu trúc repository
flood-webgis-hecras/
├── frontend/ # Leaflet WebGIS application
├── backend/ # FastAPI backend
├── agent/ # HEC-RAS remote agent
├── gis-processing/ # GIS processing utilities
├── database/ # Database schema
├── docs/ # Documentation
├── scripts/ # Utility scripts
└── tests/ # Test suites

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 16+ (cho frontend)
- PostgreSQL 14+ (hoặc Neon)
- Git

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/flood-webgis-hecras.git
cd flood-webgis-hecras

# Setup environment
cp .env.example .env
# Edit .env with your configuration

# Setup backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Setup frontend
cd ../frontend
npm install

# Setup database
# Run migrations from /database/schema

Running Development

# Backend
cd backend
uvicorn app.main:app --reload

# Frontend (if using dev server)
cd frontend
npm run dev

# Agent
cd agent
python src/main.py

🧪 Testing
# Run backend tests
cd backend
pytest

# Run integration tests
cd tests
pytest integration/
📖 Documentation
System Architecture

API Reference

Deployment Guide

User Manual
🔒 Security
All sensitive data stored in .env

HTTPS required for production

Input validation on all endpoints

Authentication and authorization

No arbitrary command execution

🤝 Contributing
Fork repository

Create feature branch (git checkout -b feature/amazing)

Commit changes (git commit -m 'Add amazing feature')

Push to branch (git push origin feature/amazing)

Open Pull Request

📝 License
MIT License - see LICENSE file for details

📧 Contact
Project Lead: Your Name

Issue Tracker: GitHub Issues

---

## 6. .gitignore

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST
pip-log.txt
pip-delete-this-directory.txt
.pytest_cache/
.coverage
htmlcov/
.tox/
.mypy_cache/
.dmypy.json
dmypy.json
.pyre/
*.log

# Environment
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Database
*.db
*.sqlite
*.sqlite3

# HEC-RAS
*.prj
*.p01
*.p02
*.p03
*.g01
*.g02
*.f01
*.f02
*.o01
*.o02
*.out
*.hdf
*.tmp
*.bak
*.temp

# GIS / Raster
*.tif
*.tiff
*.geotiff
*.cog
*.vrt
*.aux.xml
*.ovr
*.gwf
*.tfw
*.prj
*.shp
*.shx
*.dbf
*.sbn
*.sbx
*.fbn
*.fbx
*.ain
*.aih
*.ixs
*.mxs
*.atx
*.cpg
*.qix

# Storage / Uploads
uploads/
storage/
temp/
tmp/
*.tmp
*.temp
*.cache

# Frontend
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
dist/
build/
*.local

# Backend
alembic/versions/*.py
!alembic/versions/__init__.py
instance/
webapp.db

# Agent
jobs/
working_dir/
*.pid
*.log

# Testing
*.test
*.spec
test_output/

# Misc
*.key
*.pem
*.crt
*.csr
*.p12
*.pfx
*.jks
*.keystore
*.truststore
*.pub
*.priv
*.secret
*.token
*.api_key
*.password

# Docker
*.dockerignore
Dockerfile.*
*.tar
*.tar.gz

# OS
Thumbs.db
Desktop.ini
$RECYCLE.BIN/

# Logs
logs/
*.log
*.out

# Coverage
coverage/
.coveralls.yml
*.coveragerc

# Jupyter Notebooks
.ipynb_checkpoints/
*.ipynb

# Git
*.orig
*.rej
*.patch
*.diff

# Backup
*.backup
*.bak
*.old
*.orig

# Certificates
*.crt
*.key
*.pem
*.p12
*.pfx

# Agent specific
agent/working_dir/
agent/jobs/
agent/logs/
agent/*.pid
agent/hecras_temp/
agent/model_template_backup/

# GIS Processing
gis-processing/temp/
gis-processing/output/
gis-processing/*_processed.*

# Database
database/*.sqlite
database/*.db
database/data/