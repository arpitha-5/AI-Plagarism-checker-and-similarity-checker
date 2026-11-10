# PlagiarismAI

AI‑Powered Plagiarism & Similarity Detection Platform.

## Overview

PlagiarismAI is a full‑stack SaaS application that allows users to upload documents or paste text and receive detailed similarity, originality, and AI‑generated‑content analysis. It provides a secure, responsive UI built with React, a FastAPI backend, PostgreSQL storage, and a modular machine‑learning engine for text processing.

## Features
- User registration, login, JWT authentication.
- Document upload (PDF, DOCX, TXT) and text input.
- Exact, TF‑IDF, and semantic similarity detection.
- AI‑generated‑content confidence scoring.
- Comparison of multiple documents.
- downloadable PDF reports.
- Admin‑style dashboard with analytics.
- Comprehensive test suite.
- Deployable to Vercel (frontend) and Render (backend).

## Repository Structure
```
PlagiarismAI/
│
├── frontend/                # React + Vite UI
├── backend/                 # FastAPI server
├── ml_engine/               # ML/NLP processing modules
├── tests/                   # Integration & unit tests
├── docs/                    # Documentation
├── .gitignore
├── .env.example
├── README.md
└── DEVELOPMENT_STATUS.md
```
