# 🏛️ Auction AI - Intelligent Auction Notice Extraction System

**Auction AI** is an enterprise-grade, AI-powered automated document processing and information extraction system designed to extract structured auction notice records from scanned newspaper clippings, images, and multi-page PDF catalogues.

Built with **FastAPI**, **SQLAlchemy (Async)**, **PaddleOCR**, **PyMuPDF**, and **Google Gemini AI**, the system parses complex, multi-column bank sale notices and converts them into standardized, database-ready JSON records.

---

## 📋 Table of Contents
1. [Key Features](#-key-features)
2. [Complete System Workflow](#-complete-system-workflow)
   - [Image Processing Pipeline](#1-image-processing-pipeline)
   - [PDF Processing Pipeline (16-Stage Engine)](#2-pdf-processing-pipeline-16-stage-engine)
3. [System Architecture](#-system-architecture)
4. [Database Schema & Data Fields](#-database-schema--data-fields)
5. [API Reference & Endpoints](#-api-reference--endpoints)
6. [Getting Started](#-getting-started)
   - [Prerequisites](#prerequisites)
   - [Installation](#installation)
   - [Environment Configuration](#environment-configuration)
   - [Running the Application](#running-the-application)
7. [Web User Interface](#-web-user-interface)
8. [Directory Structure](#-directory-structure)

---

## ✨ Key Features

- **Multi-Format Processing**: Supports scanned newspaper images (`PNG`, `JPG`, `TIFF`) and digital/scanned `PDF` documents.
- **Image Enhancement**: Auto-binarization, deskewing, noise reduction, and contrast tuning for high OCR accuracy.
- **Layout Segmentation**: Detects multi-column newspaper layouts and splits combined pages into individual auction notice blocks.
- **Hybrid Extraction Engine**: Combines deterministic Regex pattern matching with Google Gemini LLM fallback for ambiguous text.
- **Dedicated 16-Stage PDF Engine**: Comprehensive lot boundary detection, bank details extraction, vehicle specs parsing, and gold karat aggregation.
- **Automated Validation & Normalization**: Standardizes dates, INR currency values, phone numbers, and calculates extraction confidence scores.
- **Built-in Web Dashboard**: Modern web interface at `/` for interactive file uploads, real-time results viewing, and search.
- **RESTful API**: Fully documented API with Swagger UI (`/docs`) and ReDoc (`/redoc`).

---

## 🔄 Complete System Workflow

The application operates using two primary processing pipelines based on the input document type:

```
                      ┌────────────────────────┐
                      │  User Upload (UI/API)  │
                      └───────────┬────────────┘
                                  │
                  ┌───────────────┴───────────────┐
                  ▼                               ▼
       [ Image File (.png/jpg) ]        [ PDF Document (.pdf) ]
                  │                               │
                  ▼                               ▼
        Image Processing Pipeline       16-Stage PDF Pipeline
                  │                               │
                  └───────────────┬───────────────┘
                                  ▼
                    ┌───────────────────────────┐
                    │ Data Normalization &      │
                    │ Validation Engine         │
                    └─────────────┬─────────────┘
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │   Async Database Storage  │
                    │    (SQLite / MySQL / DB)  │
                    └───────────────────────────┘
```

---

### 1. Image Processing Pipeline

Used for single or batch image files of newspaper sale notices.

1. **File Upload & Ingestion (`UploadService`)**:
   - Saves file to disk (`uploads/` directory).
   - Creates an `Upload` database record with unique UUID and metadata.

2. **Image Preprocessing & Enhancement (`ImageEnhancer`)**:
   - Binarizes grayscale/colored scans.
   - Corrects image skew angle.
   - Cleans noise and enhances text contrast for PaddleOCR.

3. **Layout Detection & Segmentation (`LayoutDetector` & `AuctionSplitter`)**:
   - Scans image for visual separators, bounding boxes, and column structures.
   - Crops multi-notice pages into individual auction notice clippings.

4. **OCR Text Extraction (`PaddleOCRService`)**:
   - Runs PaddleOCR on image clippings to extract text tokens with bounding coordinates.

5. **Hybrid AI & Regex Extraction (`AuctionParser` & `regex.py`)**:
   - **Regex Engine**: Parses known structural patterns (Borrower name, Reserve Price, EMD Amount, Auction Dates, Bank Name, IFSC code).
   - **Gemini LLM Parser**: Passes complex or low-confidence text blocks to Google Gemini API for deep semantic extraction.

6. **Field Normalization & Validation (`Validator`)**:
   - Validates currency formats, date-time bounds, and required attributes.
   - Computes an overall confidence score for the extracted record.

7. **Database Storage (`DatabaseService`)**:
   - Saves parsed attributes as `Auction` database records linked to the original upload ID.

---

### 2. PDF Processing Pipeline (16-Stage Engine)

Specifically engineered for multi-page bank auction catalogues and complex PDF documents (`PDFParserService` / `PDFPipeline`).

| Stage | Name | Description |
|---|---|---|
| **Stage 1** | **Document Classifier** | Identifies document category (Bank SARFAESI Notice, Gold Auction Catalogue, Vehicle Repository, Commercial Real Estate). |
| **Stage 2** | **Text & Bounding Box Extraction** | Uses `PyMuPDF` (`fitz`) to extract structured text blocks with exact coordinates. |
| **Stage 3** | **Header & Metadata Parser** | Extracts overarching document metadata (Institution/Bank Name, Notice ID, Department, Office). |
| **Stage 4** | **Lot Boundary Detector** | Detects individual property/vehicle lot boundaries across single or multi-page documents. |
| **Stage 5** | **Lot Content Parser** | Parses lot numbers, detailed asset descriptions, asset categories, and location details. |
| **Stage 6** | **Price Parser** | Extracts reserve prices (`auction_start_price`), increment values, and currency (`INR`). |
| **Stage 7** | **Bank & EMD Details Parser** | Extracts EMD deposit details: EMD bank name, account number, IFSC code, and total EMD amount. |
| **Stage 8** | **Schedule & Date Parser** | Extracts auction start/end datetimes, submission deadlines, and property inspection schedules. |
| **Stage 9** | **Officer & Contact Parser** | Identifies authorized officer names and phone/mobile contact numbers. |
| **Stage 10** | **Specialized Category Extractor** | - **Vehicles**: Year, Reg No, Repo Date, KM Driven, RC Status, Chassis No.<br>- **Gold**: Sum of Net/Gross weights, Karat breakup (18K to 24K). |
| **Stage 11** | **LLM Semantic Parser** | Invokes Gemini AI to resolve unparsed or ambiguous fields. |
| **Stage 12** | **Field Normalizer** | Formats date strings to standard ISO format (`YYYY-MM-DD HH:MM:SS`) and cleans monetary strings to `Decimal`. |
| **Stage 13** | **Document & Field Validator** | Enforces structural constraints and drops invalid records. |
| **Stage 14** | **Confidence Scoring Engine** | Calculates per-record quality metrics (`0.00` to `1.00`). |
| **Stage 15** | **Retry Engine** | Triggers fallback extraction logic for records missing key fields (e.g. reserve price or borrower). |
| **Stage 16** | **Persistence & Response Builder** | Writes records to the database and formats response JSON. |

---

## 🏗️ System Architecture

```
auction-ai/
├── app/
│   ├── api/                  # FastAPI Web & API Routers
│   │   ├── router.py         # Main V1 Router aggregation
│   │   └── v1/
│   │       ├── auction.py    # Record query, search, delete & statistics
│   │       ├── process.py    # Document upload & pipeline execution
│   │       ├── upload.py     # Upload status & file retrieval
│   │       └── health.py     # System health check
│   ├── core/                 # Core settings, configurations, logging
│   │   ├── config.py         # Environment variables configuration (Pydantic)
│   │   └── logger.py         # Centralized logging framework
│   ├── database/             # SQLAlchemy async engine & session handlers
│   ├── models/               # Database ORM models (`Auction`, `Upload`)
│   ├── repositories/         # Database access layer
│   ├── schemas/              # Pydantic request/response validation schemas
│   ├── services/             # Core Pipeline Services
│   │   ├── pipeline.py       # Main Image Processing Orchestrator
│   │   ├── document_pipeline.py # Main PDF Processing Orchestrator
│   │   ├── preprocess/       # OpenCV & Image Enhancement
│   │   ├── detection/        # Layout detection algorithms
│   │   ├── ocr/              # PaddleOCR wrapper
│   │   ├── extractor/        # Regex & LLM field parsers
│   │   └── pdf/              # 16-Stage PDF Processing Pipeline modules
│   └── templates/            # Web UI Dashboard (index.html)
└── run.py                    # Application launch script
```

---

## 📊 Database Schema & Data Fields

The extracted data is stored in the `auctions` table. Below are key extracted attributes:

### 🏠 General & Asset Information
- `asset_type`: (e.g. Real Estate, Vehicle, Gold, Machinery)
- `asset_category`: (e.g. Residential Plot, Commercial Shop, 4-Wheeler)
- `auction_no` & `notice_auction_id`
- `auction_description`: Full raw description text
- `assets_location`: Physical address or city location
- `borrower`: Borrower / Defaulter name(s)
- `institution_seller`: Bank / Financial Institution selling the property

### 💰 Price & Payment Details
- `auction_start_price`: Reserve price (Decimal)
- `emd_amount`: Earnest Money Deposit amount (Decimal)
- `increment_price`: Minimum bid increment step
- `payment_type`: Mode of payment / terms

### 🏦 EMD Bank Account Details
- `emd_bank_name`: Bank for EMD deposit
- `emd_account_no`: EMD Account number
- `emd_ifsc`: IFSC code

### 📅 Schedule & Timings
- `auction_start_datetime`: Start date and time
- `auction_end_datetime`: End date and time
- `inspection_from_date` / `inspection_to_date`: Property inspection window

### 👤 Contact Details
- `authorized_officer_name`: Name of bank officer
- `authorized_officer_number`: Contact phone number(s)

### 🚗 Vehicle & Gold Specific Fields
- **Vehicle**: `year`, `reg_no`, `repo_date`, `km_driven`, `rc`, `chassis_number`
- **Gold**: Karat breakups (`sum_of_carat_18` to `sum_of_carat_24`), `sum_of_net_weight_total`, `sum_of_gross_weight_total`

---

## 📡 API Reference & Endpoints

### 🚀 Processing Endpoints (`/api/v1/process`)
- `POST /api/v1/process/`: Upload an image or PDF file to execute the extraction pipeline.
- `POST /api/v1/process/image`: Process a file already present on local disk.
- `POST /api/v1/process/batch`: Upload multiple files for concurrent batch execution.

### 🏛️ Auction Data Endpoints (`/api/v1/auctions`)
- `GET /api/v1/auctions/`: Retrieve all extracted auction records.
- `GET /api/v1/auctions/{auction_id}`: Get detailed record by ID.
- `GET /api/v1/auctions/upload/{upload_id}`: Get all records generated from a single upload.
- `GET /api/v1/auctions/search/{keyword}`: Search records by keyword (bank name, borrower, city).
- `GET /api/v1/auctions/statistics`: Get extraction performance and totals statistics.
- `GET /api/v1/auctions/count`: Get total auction record count.
- `DELETE /api/v1/auctions/{auction_id}`: Delete an auction record.

### 🛠️ Health & Info Endpoints
- `GET /ping`: Health check ping (`"pong"`).
- `GET /info`: Environment status, version, and debug flag info.

---

## 🛠️ Getting Started

### Prerequisites
- **Python**: 3.10 or higher
- **PaddleOCR** / **OpenCV** system dependencies
- **Google Gemini API Key** (for LLM semantic parsing fallback)

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository_url>
   cd auction-ai
   ```

2. **Create and activate a Virtual Environment**:
   ```bash
   # Windows (PowerShell)
   python -m venv myenv
   .\myenv\Scripts\Activate.ps1

   # Linux / macOS
   python3 -m venv myenv
   source myenv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Environment Configuration

Create a `.env` file in the root directory:

```env
ENVIRONMENT=development
DEBUG=True
HOST=0.0.0.0
PORT=8000

# Database Configuration
DATABASE_URL=sqlite+aiosqlite:///./auction_ai.db

# Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here
```

### Running the Application

Execute the launch script:

```bash
python run.py
```

The application will start at `http://localhost:8000`.

- **Web Dashboard**: [http://localhost:8000/](http://localhost:8000/)
- **Swagger Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 💻 Web User Interface

The integrated frontend (`app/templates/index.html`) provides a visual dashboard to:
- Drag & drop newspaper images or PDF catalogues for processing.
- View real-time status, processing speed, and detected notice count.
- Search and filter extracted auction records by bank name, location, or borrower.
- Inspect structured field outputs and confidence scores.

---

## 📂 Directory Structure

```
d:/auction-ai/auction-ai/
├── app/
│   ├── api/               # FastAPI endpoints
│   ├── core/              # Config, settings, and logging setup
│   ├── database/          # Database connection & base models
│   ├── models/            # SQLAlchemy database entities
│   ├── repositories/      # Data access layer
│   ├── schemas/           # Pydantic schemas
│   ├── services/          # Preprocessing, OCR, Regex, PDF, and Pipeline logic
│   └── templates/         # Dashboard UI HTML
├── logs/                  # System logs
├── uploads/               # Stored uploaded files
├── .env                   # Environment variable definitions
├── requirements.txt       # Python dependencies
├── run.py                 # Application launcher
└── README.md              # Documentation (This file)
```
