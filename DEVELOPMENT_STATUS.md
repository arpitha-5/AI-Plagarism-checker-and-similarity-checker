# Development Status

## Completed Phases
- Frontend application shell and route-driven React experience
- Professional PlagiarismAI landing, authentication, workspace, checker, comparison, history, and result views
- Modular plagiarism analysis service foundation

## Implemented Features
- React entrypoint now renders `AppRoutes` instead of the default Vite screen.
- FastAPI backend now exposes working `/health`, `/auth/register`, and `/auth/login` endpoints with SQLite persistence, PBKDF2 password hashing, JWT access tokens, and frontend CORS configuration.
- Protected routes are connected to the authentication context and token storage.
- Document upload and pasted-text analysis UI supports PDF, DOCX, and TXT validation.
- Exact-match, near-duplicate, and optional semantic-analysis controls are wired to API service functions.
- Results and history screens use backend response data only and show honest unavailable states.
- Backend analysis modules provide preprocessing, exact matching, cosine near-duplicate matching, optional Sentence Transformers semantic matching, source matching, and structured analysis output.
- Report generation now creates branded multi-section PDFs with actual document metadata, similarity methodology, source tables, detailed matching passages, integrity limitations, page numbers, and authenticated owner-only downloads.
- Uploaded-document analysis excludes the newly submitted document from its own comparison corpus and counts unique candidate sentence positions once.
- Analysis responses now include source categories, match-group availability, explicit filters, evidence-based integrity flags, calculation methodology, and extracted document text for the report viewer.
- Large-document analysis now uses token-indexed near-duplicate candidate selection instead of comparing every sentence against every source sentence; the frontend allows up to 120 seconds for legitimate large-file processing.
- Similarity-inflation corrections now exclude the current document ID and SHA-256 file hash, backfill hashes for historical SQLite documents, restrict sources to the authenticated user's corpus, and deduplicate identical source content.
- Meaningful-match filtering now excludes academic headings, punctuation, names, and short fragments; exact and near-duplicate matches use unique candidate coverage, preserve source sentence positions, and avoid repeated candidate/overlapping matches.
- PDF detailed matching now groups consecutive entries instead of emitting one report block for every sentence.
- The PDF generator now follows the supplied iThenticate-style information architecture: sparse cover, two-page integrity overview, ranked source/coverage page, two-column analysed-document pages, numbered source markers, detailed matching, integrity observations, methodology, and fixed headers/footers.
- Uploaded files are now retained in an owner-scoped backend upload directory and passed to report generation. PDF uploads use the original uploaded page as the document page and overlay source-coloured highlights/number markers on actual searchable text matches; DOCX/TXT uploads use their extracted original content in the same reference-inspired page renderer.

## Files Created
- `frontend/src/components/layout/AppLayout.tsx`
- `frontend/src/components/common/ProtectedRoute.tsx`
- `frontend/src/components/common/PageHeader.tsx`
- `frontend/src/components/common/MetricCard.tsx`
- `frontend/src/components/common/StatusBadge.tsx`
- `frontend/src/components/common/EmptyState.tsx`
- `frontend/src/pages/LandingPage.tsx`
- `frontend/src/pages/RegisterPage.tsx`
- `frontend/src/pages/DashboardPage.tsx`
- `frontend/src/pages/CheckerPage.tsx`
- `frontend/src/pages/ComparePage.tsx`
- `frontend/src/pages/HistoryPage.tsx`
- `frontend/src/pages/ResultPage.tsx`
- `frontend/src/services/api.ts`
- `frontend/src/index.css`
- `backend/app/services/plagiarism/`
- `backend/app/services/report_generator.py`
- `backend/migrations/001_add_report_metadata.sql`

## Commands Executed
- `npm run build` in `frontend/`
- `python -m compileall app` in `backend/`
- Started Vite on port 5175 for browser verification

## Tests Passed
- Frontend TypeScript/Vite production build
- Backend plagiarism service Python syntax compilation
- End-to-end upload, analysis, PDF generation, and owner authorization checks
- Comprehensive report inspection: generated sample PDF contained 9 pages and all required sections.
- Large DOCX benchmark: 2.65 MB document completed analysis in 0.51 seconds against the current local corpus.
- Browser verification of landing page, protected-route redirect, login page, and checker workspace
- Plagiarism engine regression suite: 8 tests passed, including self-match exclusion when raw upload hashes differ but extracted-content hashes are identical, duplicate sources, partial overlap, unrelated documents, short fragments, repeated sentences, and preserved positions.
- Added a non-destructive `documents.content_hash` migration and backfill. Raw upload hashes remain intact, while extracted-content hashes now exclude identical DOCX uploads regardless of ZIP/container byte differences and deduplicate source retrieval.
- Actual fresh `REVIEW 2 IEEE PAPER.docx` verification: 257 meaningful unique sentences, 0.0% similarity, 0 sources, 0 exact matches, and 0 near-duplicate matches after excluding the current document ID, raw hash, and extracted-content hash.
- Regenerated verification PDF: 13 pages, valid PDF, required Top Sources and Detailed Matching sections present, and no duplicate source rows.
- Reference comparison completed against `Downloads/IEEE PAPER -TC15 (1).pdf`: both reports contain 13 pages; the new report preserves the reference's cover/overview/source/document-page rhythm while retaining PlagiarismAI branding and explicitly marking unavailable source providers.
- Final sample saved as `backend/reports/3/reference-style-review2.pdf` and visually inspected page-by-page at rendered-page scale.
- Authenticated API verification passed for a real PDF upload and owner-only report download: upload `200`, download `200 application/pdf`, valid `%PDF` signature, and one uploaded source page rendered without overflow.
- Highlighted PDF test verification passed: 6-page report, actual uploaded page retained, one exact match highlighted, calculated similarity `33.33%`, one unique source, and one direct match.
- Fresh content-hash verification report saved as `backend/reports/f205ea7d-5fe2-43ae-ad8d-3d57b97c3514/review2-contenthash-fixed.pdf`; it contains 13 pages and was rendered as a contact sheet for visual inspection.

## Known Issues
- The current backend uses a local SQLite database for development. PostgreSQL models, migrations, document persistence, and analysis routers are still pending.
- Semantic matching is optional and returns unavailable when Sentence Transformers is not installed/configured.
- The frontend does not claim internet-wide detection; analysis is scoped to the available corpus.
- The current development database remains SQLite; the requested PostgreSQL/Alembic production migration is not present in this repository snapshot.
- Formatting and character-substitution integrity flags are explicitly reported as unavailable rather than inferred.
- PDF/DOCX page associations are available for PDF metadata where extraction supports it; DOCX/TXT page numbers require a rendering pipeline and are reported unavailable.
- Historical duplicate document rows are preserved for data safety; comparison retrieval deduplicates them by content hash rather than deleting records.
- The source reference contains original publisher-side formatting and page images; the generated report has extracted-text two-column pages because DOCX rendering/page-coordinate data is not available in the current backend. Match markers are dynamic and appear only when actual candidate positions are returned.

## Remaining Tasks
- Implement PostgreSQL-backed FastAPI authentication, document, analysis, comparison, and history endpoints.
- Add database models and Alembic migrations for users, documents, analyses, and source matches.
- Connect document extraction (PDF/DOCX/TXT) to the plagiarism analyzer.
- Add backend pytest and frontend integration tests against a running API.
- Re-run the authenticated frontend upload flow for the corrected IEEE document in the browser and inspect the downloaded owner-only report.
- Move report metadata and analysis persistence to the production PostgreSQL/Alembic stack when that stack is added.

## Deployment Status
- Not started
