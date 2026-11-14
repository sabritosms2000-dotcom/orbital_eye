# orbital_eye
# ORBITAL EYE — NASA SPHEREx Challenge Platform
 
A scientific validation and data exploration platform for the **NASA SPHEREx mission**. Analyzes 5 high-priority astronomical targets using SPHEREx Data Release 1 (DR1) observations.
 
## 🎯 Targets
 
| Target | Type | Science Case |
|--------|------|--------------|
| **WISE 0855** | Y-dwarf brown dwarf (coldest known) | Astrometry — motion detection |
| **Barnard's Star** | M4V high-proper-motion red dwarf | Astrometry — proper motion + parallax |
| **Epsilon Indi Ba/Bb** | Binary brown dwarf (T1 + T6) | Astrometry — detectability & motion |
| **RW Aurigae** | T Tauri binary system | Photometry — variability |
| **R Draconis** | Mira-type long-period variable | Photometry — brightness changes |
 
---
 
## 🏗️ Architecture
 
```
SPHEREx_Project/
├── backend/                 # FastAPI server (port 8001)
│   ├── main.py              # API routes + endpoints
│   ├── validation/          # Phase 5: Scientific Validation Engine
│   │   ├── engine.py        # Validation orchestration
│   │   ├── photometry.py    # Aperture photometry (memory-efficient)
│   │   ├── astrometry.py    # Proper motion + parallax propagation
│   │   ├── target_registry.py # 5 target reference records
│   │   └── observation_discovery.py # IRSA SIA queries
│   ├── image_processing.py  # FITS alignment, background matching, difference imaging
│   ├── motion_detection.py  # PM + parallax prediction
│   ├── band_explorer.py     # Phase 4A: 102-band SED explorer
│   ├── catalog_overlay.py   # Phase 4B: Gaia/AllWISE/CatWISE overlay
│   ├── candidate_ranking.py # Phase 4C: Candidate ranking (stub)
│   └── test_*.py            # 10 passing tests
├── frontend/                # Next.js 16 + React 19 (port 3000)
│   ├── src/app/             # 13-page SPA (App Router)
│   └── src/components/      # Reusable UI components
└── data/                    # Local FITS files (33 files, ~2 GB)
```
 
---
 
## 🚀 Quick Start
 
### Prerequisites
- **Python 3.11+** with: `fastapi`, `uvicorn`, `astropy`, `photutils`, `astroquery`, `numpy`, `pytest`
- **Node.js 18+** with: `npm`
- **Windows PowerShell** (commands below use PowerShell syntax)
 
### 1. Start Backend
```powershell
cd "C:\Users\standalone\Desktop\orbital_eye\andrew\The project\The project\SPHEREx_Project\backend"
python -m uvicorn main:app --port 8001 --host 127.0.0.1
```
**Verify:** `http://127.0.0.1:8001/api/health` → `{"status":"ok"}`
 
### 2. Start Frontend (new terminal)
```powershell
cd "C:\Users\standalone\Desktop\orbital_eye\andrew\The project\The project\SPHEREx_Project\frontend"
npm run dev
```
**Open:** `http://localhost:3000`
 
---
 
## 🧪 Testing
 
### Backend Tests
```powershell
cd backend
python -m pytest test_validation.py test_validation_synthetic.py test_validation_api.py -v
```
**Expected:** 10 passed, 0 failed
 
### Frontend Build
```powershell
cd frontend
npm run build
```
**Expected:** Clean compilation, TypeScript pass, static generation
 
---
 
## 🔬 Key Features
 
### Phase 4: Data Exploration
- **102-Band Explorer** (`/bands`): Full 6-detector spectral explorer with WCS-WAVE extraction
- **Catalog Overlay** (`/catalogs`): Gaia DR3, AllWISE, CatWISE cone search with FITS projection
- **Candidate Ranking** (`/candidates`): Framework for cross-epoch source matching
 
### Phase 5: Scientific Validation
- **Validation Lab** (`/validation`): Per-target validation with:
  - FITS quality checks (L1/L2, WCS, flags)
  - Aperture photometry (2px radius, variance propagation)
  - Astrometry (PM + parallax propagation, centroiding, SNR≥5 gate)
  - Epoch comparison (motion, photometry, image difference)
  - Publication-grade plots (light curve, motion, difference image)
 
### Core API Endpoints
| Feature | Endpoint |
|---------|----------|
| Health | `GET /api/health` |
| Observations | `GET /api/observations` |
| FITS Image | `GET /api/observations/{id}/image` |
| Time-Lapse | `GET /api/timelapse` |
| Spectrum Extraction | `POST /api/bands/extract` |
| SED Plot | `GET /api/bands/spectral-plot` |
| Catalog Overlay | `GET /api/catalogs/overlay-image/{id}` |
| **Validation Run** | `POST /api/validation/run/{target_id}` |
| Validation Results | `GET /api/validation/results/{target_id}` |
| Light Curve Plot | `GET /api/validation/lightcurve/{target_id}` |
| Motion Plot | `GET /api/validation/motion/{target_id}` |
| Difference Image | `GET /api/validation/difference-image/{target_id}` |
 
---
 
## 📊 Current Status
 
| Component | Status |
|-----------|--------|
| Backend API | ✅ Running |
| Frontend UI | ✅ Building |
| Backend Tests | ✅ 10/10 pass |
| FITS Data | ⚠️ 31/33 valid (2 truncated) |
| Validation Engine | ✅ Runs for all 5 targets |
| Validation Status | All targets: `INCONCLUSIVE` |
 
**Why `INCONCLUSIVE`?** Centroid-only uncertainties exclude WCS covariance, spacecraft pointing, and calibration systematics. Measured shifts differ from predictions at ~2-3σ but cannot confirm motion without full error budget.
 
---
 
## 📁 Data
 
Local FITS stored in `data/`:
- **WISE 0855:** 2 original cutouts (59×58 px) + 1 full frame
- **Barnard's Star:** 12 full frames (2040×2040, ~60 MB each)
- **Epsilon Indi B:** 12 full frames
- **RW Aurigae:** 2 full frames
- **R Draconis:** 4 full frames
 
**Truncated files needing re-download:**
- `barnards_star_2025W33_2C_0321_1_SPHEREx-D6.fits` (51/65 MB)
- `wise_0855_2025W19_1B_0116_1_SPHEREx-D3.fits` (42/65 MB)
 
---
 
## 🛠️ Development
 
### Run Validation Manually
```powershell
# Via API (backend must be running)
Invoke-RestMethod -Uri 'http://127.0.0.1:8001/api/validation/run/wise_0855' -Method POST -Body '{"live_archive_query":false,"use_discovery_cache":true}' -ContentType 'application/json'
 
# Check results
Invoke-RestMethod -Uri 'http://127.0.0.1:8001/api/validation/results/wise_0855'
```
 
### Add New Target
1. Add entry to `backend/validation/target_registry.py` with reference astrometry
2. Download FITS via IRSA SIA (`backend/download_fits.py` pattern)
3. Add `local_fits` entries to registry
 
---
 
## ⚠️ Known Limitations
 
1. **No PSF photometry** — aperture-only, no PSF matching for difference imaging
2. **No full uncertainty propagation** — WCS covariance, spacecraft ephemeris excluded
3. **Candidate Ranking stub** — returns empty; cross-epoch matching not implemented
4. **IRSA live queries unreliable** — fallback to local FITS/cache only
5. **2 truncated FITS files** — re-download needed
 
---
 
## 📄 License
 
NASA SPHEREx Challenge submission. See individual file headers for licensing.
 
---
 
## 🙏 Acknowledgments
 
- **SPHEREx Team** for DR1 data access via IRSA
- **Astropy/Photutils/Astroquery** communities
- **NASA/IPAC IRSA** for archive services
