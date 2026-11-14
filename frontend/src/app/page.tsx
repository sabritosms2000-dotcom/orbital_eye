
"use client";

import { useEffect, useState, type FormEvent } from "react";

const API_URL = "http://127.0.0.1:8000";

type Observation = {
  id: string;
  filename: string;
  date: string | null;
  mjd: number | null;
  image_shape: number[];
  unit: string | null;
  available: boolean;
};

type Page =
  | "Overview"
  | "Observations"
  | "Coordinate Search"
  | "Image Viewer"
  | "Time-Lapse"
  | "Archive Timeline"
  | "Image Comparison"
  | "Scientific Analysis"
  | "Motion Detection"
  | "102-Band Explorer"
  | "External Catalogs"
  | "Candidate Ranking"
  | "Validation Lab";

// Phase 4 Types
type BandMeta = {
  band: string;
  detector: string;
  wavelength_min_um: number;
  wavelength_max_um: number;
  channels_count: number;
  resolving_power: number;
  primary_features: string;
  archive_records_wise0855: number;
  color: string;
};

type ChannelItem = {
  channel_id: number;
  band: string;
  detector: string;
  channel_in_band: number;
  wavelength_um: number;
  bandwidth_um: number;
  resolving_power: number;
  science_notes: string;
  is_cutout_band: boolean;
};

type BandSummaryResponse = {
  status: string;
  target: string;
  total_channels: number;
  spectral_range_um: [number, number];
  bands: BandMeta[];
  channels: ChannelItem[];
  note: string;
};

type ExtractedSpectrumResponse = {
  status: string;
  target: string;
  pixel: { x: number; y: number };
  in_situ_spectrum: {
    wavelength_um: number;
    bandwidth_um: number;
    detector_band: string;
    matched_channel_id: number;
    net_surface_brightness_mjy_sr: number;
    flux_density_ujy: number;
    flux_uncertainty_ujy: number;
    signal_to_noise: number;
    aperture_pixels: number;
    quality_flags: number[];
  };
  sed_102_channels: {
    channel_id: number;
    band: string;
    wavelength_um: number;
    bandwidth_um: number;
    model_flux_ujy: number;
    measured_flux_ujy: number | null;
    measured_err_ujy: number | null;
    is_measured: boolean;
  }[];
  scientific_interpretation: string;
};

type CatalogSource = {
  id: string;
  ra: number;
  dec: number;
  separation_arcsec: number;
  pixel_x: number;
  pixel_y: number;
  inside_cutout: boolean;
  g_mag?: number | null;
  w1_mag?: number | null;
  w2_mag?: number | null;
  w3_mag?: number | null;
  w4_mag?: number | null;
  pm_ra_mas_yr?: number | null;
  pm_dec_mas_yr?: number | null;
  total_pm_mas_yr?: number | null;
  parallax_mas?: number | null;
};

type CatalogOverlayResponse = {
  query: {
    center_ra: number;
    center_dec: number;
    radius_arcmin: number;
    target: string;
  };
  gaia_dr3: CatalogSource[];
  allwise: CatalogSource[];
  catwise2020: CatalogSource[];
  total_sources: number;
  inside_cutout_count: number;
};

type Candidate = {
  id: string;
  name: string;
  classification: "Likely moving source" | "Possible motion" | "Known matched object" | "Artifact / Flagged";
  rank_score: number;
  position: {
    epoch_1: { pixel_x: number; pixel_y: number };
    epoch_2: { pixel_x: number; pixel_y: number };
    ra_deg: number;
    dec_deg: number;
    sky_coord_str: string;
  };
  motion: {
    delta_x_px: number;
    delta_y_px: number;
    shift_pixels: number;
    angular_shift_arcsec: number;
    annual_rate_arcsec_yr: number;
    motion_type: string;
  };
  observation_count: number;
  epochs: string[];
  photometry: {
    flux_epoch_1_mjy_sr: number;
    flux_epoch_2_mjy_sr: number;
    noise_level: number;
    signal_to_noise: number;
    uncertainty_pct: number;
  };
  catalog_crossmatch: {
    matched: boolean;
    catalog: string;
    source_id: string;
    separation_arcsec: number | null;
    catalog_pm_arcsec_yr: number | null;
    notes: string;
  };
  quality_flags: {
    epoch_1_flag: number;
    epoch_2_flag: number;
    status: string;
    interpretation: string;
  };
  scientific_justification: string;
};

type CandidateRankingResponse = {
  status: string;
  target: string;
  total_candidates: number;
  classification_counts: Record<string, number>;
  candidates: Candidate[];
  scientific_guideline: string;
};

type SearchMatch = Observation & {
  inside_image: boolean;
  pixel_x: number | null;
  pixel_y: number | null;
  image_url: string | null;
};

type SearchResponse = {
  searched_coordinates: { ra: number; dec: number };
  search_scope: string;
  matches: SearchMatch[];
  message: string;
};

type Frame = Observation & { image_url: string };

type ComparisonResponse = {
  status: string;
  valid_pixels: number;
  total_pixels: number;
  overlap_percentage: number;
  unit: string;
  first_observation: {
    background: number;
    source_candidates: number;
    noise: number;
  };
  second_observation: {
    background: number;
    source_candidates: number;
    noise: number;
  };
  background_offset: number;
  difference_median: number;
  difference_std: number;
  scientific_note: string;
};

type DetectionResponse = {
  observation_id: string;
  method: string;
  result: {
    number_of_sources: number;
    background_level: number;
    noise: number;
    sources: {
      x: number;
      y: number;
      flux: number;
      sharpness: number;
      roundness: number;
    }[];
  };
  scientific_note: string;
};

type MotionObservation = {
  observation: string;
  status: string;
  date?: string;
  predicted_ra?: number;
  predicted_dec?: number;
  pixel_x?: number;
  pixel_y?: number;
  inside_image?: boolean;
  image_width?: number;
  image_height?: number;
  message?: string;
};

type MotionResponse = {
  target: string;
  method: string;
  reference_epoch_mjd: number;
  observations: MotionObservation[];
  scientific_note: string;
};

type TimelineItem = {
  date: string;
  energy_bandpassname: string;
  records: number;
  unique_observations: number;
};

type TimelineResponse = {
  status: string;
  total_dates: number;
  total_bands: number;
  total_groups: number;
  timeline: TimelineItem[];
};

type ValidationTarget = {
  id: string; name: string; object_type: string; science_case: string; science_goal: string;
  reference: { catalog: string; catalog_id: string; frame: string; ra_deg: number; dec_deg: number; epoch_label: string; epoch_mjd: number;
    pm_ra_cosdec_mas_yr: number | null; pm_dec_mas_yr: number | null; parallax_mas: number | null; provenance: string; reference_url: string };
};
type ValidationReport = {
  target: ValidationTarget; validation_status: string; archive_discovery: { archive_status: string; record_count: number; distinct_dates: number; bands: string[]; live_query_error?: string | null; record_source?: string };
  local_fits: { observation_id: string; path: string; exists: boolean }[];
  data_quality: { filename: string; accepted: boolean; rejection_reasons: string[]; warnings: string[]; flagged_pixel_fraction?: number; l1_quality_flag?: string | null; l2_quality_flag?: string | null }[];
  epochs: { observation: string; observation_id?: string; status: string; date?: string; mjd?: number; band?: string; detector?: number; unit?: string;
    predicted?: { ra_deg: number; dec_deg: number; pixel_x: number | null; pixel_y: number | null; inside_image: boolean };
    measured_centroid?: { ra_deg: number; dec_deg: number; uncertainty_arcsec?: number } | null;
    photometry?: { status: string; flux_jy?: number; flux_error_jy?: number; snr?: number; quality_flags?: { value: number; name: string; pixels: number }[]; contamination_warning?: string } | null;
    source_detection_confidence?: { warning?: string; centroid_accepted?: boolean } }[];
  epoch_comparison: Record<string, number | string | null>; photometric_test: { result: string; interpretation: string; significance_sigma?: number | null };
  image_comparison: { status: string; note?: string; reason?: string; valid_pixels?: number; overlap_fraction?: number };
  limitations: string[]; is_confirmed_detection: boolean;
};

const navigation: { icon: string; label: Page }[] = [
  { icon: "🔬", label: "Validation Lab" },
  { icon: "◈", label: "Overview" },
  { icon: "◎", label: "Observations" },
  { icon: "⌖", label: "Coordinate Search" },
  { icon: "▤", label: "Image Viewer" },
  { icon: "▶", label: "Time-Lapse" },
  { icon: "▦", label: "Archive Timeline" },
  { icon: "◫", label: "Image Comparison" },
  { icon: "⌁", label: "Scientific Analysis" },
  { icon: "✧", label: "Motion Detection" },
  { icon: "λ", label: "102-Band Explorer" },
  { icon: "⚯", label: "External Catalogs" },
  { icon: "★", label: "Candidate Ranking" },
];

export default function Home() {
  const [activePage, setActivePage] = useState<Page>("Overview");

  const [observations, setObservations] = useState<Observation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [selectedObservation, setSelectedObservation] = useState("first");
  const [zoom, setZoom] = useState(100);

  const [ra, setRa] = useState("133.79513");
  const [dec, setDec] = useState("-7.24515");
  const [searchResults, setSearchResults] = useState<SearchResponse | null>(null);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState("");

  const [frames, setFrames] = useState<Frame[]>([]);
  const [frameIndex, setFrameIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  const [comparison, setComparison] = useState<ComparisonResponse | null>(null);
  const [comparisonError, setComparisonError] = useState("");
  const [comparisonLoading, setComparisonLoading] = useState(false);

  const [detections, setDetections] = useState<Record<string, DetectionResponse>>({});
  const [detectionLoading, setDetectionLoading] = useState<Record<string, boolean>>({});
  const [detectionErrors, setDetectionErrors] = useState<Record<string, string>>({});

  const [motion, setMotion] = useState<MotionResponse | null>(null);
  const [motionLoading, setMotionLoading] = useState(false);
  const [motionError, setMotionError] = useState("");

  const [timeline, setTimeline] = useState<TimelineResponse | null>(null);
  const [timelineLoading, setTimelineLoading] = useState(false);
  const [timelineError, setTimelineError] = useState("");

  // Backend API URL (default 8001 due to Splunk on 8000)
  const [apiUrl, setApiUrl] = useState("http://127.0.0.1:8001");

  // Phase 4A: 102-Band Explorer states
  const [bandsSummary, setBandsSummary] = useState<BandSummaryResponse | null>(null);
  const [bandsLoading, setBandsLoading] = useState(false);
  const [bandsError, setBandsError] = useState("");
  const [selectedChannelId, setSelectedChannelId] = useState(50);
  const [specObsId, setSpecObsId] = useState("first");
  const [specPixelX, setSpecPixelX] = useState("28.22");
  const [specPixelY, setSpecPixelY] = useState("28.74");
  const [extractedSpectrum, setExtractedSpectrum] = useState<ExtractedSpectrumResponse | null>(null);
  const [spectrumLoading, setSpectrumLoading] = useState(false);
  const [spectrumError, setSpectrumError] = useState("");

  // Phase 4B: External Catalogs states
  const [catalogData, setCatalogData] = useState<CatalogOverlayResponse | null>(null);
  const [catalogLoading, setCatalogLoading] = useState(false);
  const [catalogError, setCatalogError] = useState("");
  const [catRa, setCatRa] = useState("133.79513");
  const [catDec, setCatDec] = useState("-7.24515");
  const [catRadius, setCatRadius] = useState("2.0");
  const [catObsId, setCatObsId] = useState("first");
  const [showGaia, setShowGaia] = useState(true);
  const [showWise, setShowWise] = useState(true);
  const [showCatwise, setShowCatwise] = useState(true);
  const [catalogTab, setCatalogTab] = useState<"all" | "gaia" | "wise" | "catwise">("all");

  // Phase 4C: Candidate Ranking states
  const [rankingData, setRankingData] = useState<CandidateRankingResponse | null>(null);
  const [rankingLoading, setRankingLoading] = useState(false);
  const [rankingError, setRankingError] = useState("");
  const [selectedCandidateId, setSelectedCandidateId] = useState("CAND-01");
  const [validationTargets, setValidationTargets] = useState<ValidationTarget[]>([]);
  const [validationReports, setValidationReports] = useState<Record<string, ValidationReport>>({});
  const [validationSelected, setValidationSelected] = useState("barnards_star");
  const [validationLoading, setValidationLoading] = useState(false);
  const [validationError, setValidationError] = useState("");
  const [validationLive, setValidationLive] = useState(true);

  const firstObservation = observations.find((item) => item.id === "first");
  const secondObservation = observations.find((item) => item.id === "second");

  async function loadObservations() {
    try {
      setLoading(true);
      setError("");
      const response = await fetch(`${apiUrl}/api/observations`);
      if (!response.ok) throw new Error("Could not load observations.");
      const data = await response.json();
      setObservations(data.observations || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Backend connection failed.");
    } finally {
      setLoading(false);
    }
  }

  async function loadFrames() {
    try {
      const response = await fetch(`${apiUrl}/api/timelapse`);
      if (!response.ok) throw new Error("Could not load time-lapse frames.");
      const data = await response.json();
      const loadedFrames = (data.frames || []).map((frame: Frame) => ({
        ...frame,
        image_url: frame.image_url?.startsWith("http")
          ? frame.image_url
          : `${apiUrl}${frame.image_url}`,
      }));
      setFrames(loadedFrames);
    } catch (err) {
      console.error("Time-lapse loading error:", err);
    }
  }

  async function loadTimeline() {
    try {
      setTimelineLoading(true);
      setTimelineError("");
      const response = await fetch(`${apiUrl}/api/timeline`);
      const data = await response.json();

      if (!response.ok || data.status !== "success") {
        throw new Error(data.detail || data.message || "Could not load archive timeline.");
      }

      setTimeline(data);
    } catch (err) {
      setTimelineError(
        err instanceof Error ? err.message : "Timeline loading failed."
      );
    } finally {
      setTimelineLoading(false);
    }
  }

  useEffect(() => {
    loadObservations();
    loadFrames();
  }, []);

  useEffect(() => {
    if (activePage === "Archive Timeline" && !timeline) {
      loadTimeline();
    }
  }, [activePage]);

  useEffect(() => {
    if (!isPlaying || frames.length === 0) return;

    const timer = window.setInterval(() => {
      setFrameIndex((current) => (current + 1) % frames.length);
    }, 1200);

    return () => window.clearInterval(timer);
  }, [isPlaying, frames.length]);

  async function searchCoordinates(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSearchLoading(true);
    setSearchError("");
    setSearchResults(null);

    try {
      const response = await fetch(
        `${apiUrl}/api/search?ra=${encodeURIComponent(ra)}&dec=${encodeURIComponent(dec)}`
      );
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Coordinate search failed.");
      }

      setSearchResults(data);
    } catch (err) {
      setSearchError(err instanceof Error ? err.message : "Search failed.");
    } finally {
      setSearchLoading(false);
    }
  }

  async function loadComparison() {
    setComparisonLoading(true);
    setComparisonError("");

    try {
      const response = await fetch(`${apiUrl}/api/analysis/comparison`);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Could not compare observations.");
      }

      setComparison(data);
    } catch (err) {
      setComparisonError(err instanceof Error ? err.message : "Comparison failed.");
    } finally {
      setComparisonLoading(false);
    }
  }

  async function runDetection(id: string) {
    setDetectionLoading((previous) => ({ ...previous, [id]: true }));
    setDetectionErrors((previous) => ({ ...previous, [id]: "" }));

    try {
      const response = await fetch(`${apiUrl}/api/analysis/detection/${id}`);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Source detection failed.");
      }

      setDetections((previous) => ({ ...previous, [id]: data }));
    } catch (err) {
      setDetectionErrors((previous) => ({
        ...previous,
        [id]: err instanceof Error ? err.message : "Detection failed.",
      }));
    } finally {
      setDetectionLoading((previous) => ({ ...previous, [id]: false }));
    }
  }

  async function loadMotion() {
    setMotionLoading(true);
    setMotionError("");

    try {
      const response = await fetch(`${apiUrl}/api/analysis/motion`);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Motion analysis failed.");
      }

      setMotion(data);
    } catch (err) {
      setMotionError(err instanceof Error ? err.message : "Motion analysis failed.");
    } finally {
      setMotionLoading(false);
    }
  }

  async function loadBandsSummary() {
    setBandsLoading(true);
    setBandsError("");
    try {
      const res = await fetch(`${apiUrl}/api/bands/summary`);
      if (!res.ok) throw new Error("Could not load SPHEREx 102-band summary.");
      const data = await res.json();
      setBandsSummary(data);
    } catch (err) {
      setBandsError(err instanceof Error ? err.message : "Failed to load bands.");
    } finally {
      setBandsLoading(false);
    }
  }

  async function handleExtractSpectrum(e?: FormEvent) {
    if (e) e.preventDefault();
    setSpectrumLoading(true);
    setSpectrumError("");
    try {
      const res = await fetch(
        `${apiUrl}/api/bands/extract?observation_id=${specObsId}&pixel_x=${encodeURIComponent(specPixelX)}&pixel_y=${encodeURIComponent(specPixelY)}&radius=2.0`
      );
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Spectrum extraction failed.");
      setExtractedSpectrum(data);
    } catch (err) {
      setSpectrumError(err instanceof Error ? err.message : "Extraction failed.");
    } finally {
      setSpectrumLoading(false);
    }
  }

  async function loadCatalogs(e?: FormEvent) {
    if (e) e.preventDefault();
    setCatalogLoading(true);
    setCatalogError("");
    try {
      const res = await fetch(
        `${apiUrl}/api/catalogs/overlay?ra=${encodeURIComponent(catRa)}&dec=${encodeURIComponent(catDec)}&radius_arcmin=${encodeURIComponent(catRadius)}&observation_id=${catObsId}`
      );
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Catalog query failed.");
      setCatalogData(data);
    } catch (err) {
      setCatalogError(err instanceof Error ? err.message : "Catalog cone search failed.");
    } finally {
      setCatalogLoading(false);
    }
  }

  async function loadCandidateRankings() {
    setRankingLoading(true);
    setRankingError("");
    try {
      const res = await fetch(`${apiUrl}/api/candidates/rank`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Candidate ranking failed.");
      setRankingData(data);
    } catch (err) {
      setRankingError(err instanceof Error ? err.message : "Candidate ranking failed.");
    } finally {
      setRankingLoading(false);
    }
  }

  async function loadValidationTargets() {
    setValidationError("");
    try {
      const response = await fetch(`${apiUrl}/api/validation/targets`);
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Could not load validation target registry.");
      setValidationTargets(data.targets || []);
    } catch (err) { setValidationError(err instanceof Error ? err.message : "Could not load targets."); }
  }

  async function runValidationLab() {
    setValidationLoading(true); setValidationError("");
    try {
      const targets = validationTargets.length ? validationTargets : (await (async () => {
        const response = await fetch(`${apiUrl}/api/validation/targets`); const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Could not load targets."); setValidationTargets(data.targets || []); return data.targets || [];
      })());
      const reports = await Promise.all(targets.map(async (target: ValidationTarget) => {
        const response = await fetch(`${apiUrl}/api/validation/run/${target.id}?live_archive_query=${validationLive}&use_discovery_cache=true`, { method: "POST" });
        const data = await response.json(); if (!response.ok) throw new Error(`${target.name}: ${data.detail || "Validation failed."}`); return data as ValidationReport;
      }));
      setValidationReports(Object.fromEntries(reports.map((report) => [report.target.id, report])));
    } catch (err) { setValidationError(err instanceof Error ? err.message : "Validation run failed."); }
    finally { setValidationLoading(false); }
  }

  useEffect(() => {
    if (activePage === "Image Comparison" && !comparison) {
      loadComparison();
    }
    if (activePage === "Motion Detection" && !motion) {
      loadMotion();
    }
    if (activePage === "102-Band Explorer" && !bandsSummary) {
      loadBandsSummary();
      handleExtractSpectrum();
    }
    if (activePage === "External Catalogs" && !catalogData) {
      loadCatalogs();
    }
    if (activePage === "Candidate Ranking" && !rankingData) {
      loadCandidateRankings();
    }
    if (activePage === "Validation Lab" && validationTargets.length === 0) loadValidationTargets();
  }, [activePage]);

  function formatNumber(value: number | undefined, digits = 6) {
    if (value === undefined || value === null || !Number.isFinite(value)) return "—";
    return value.toFixed(digits);
  }

  function Heading({
    title,
    subtitle,
    description,
  }: {
    title: string;
    subtitle: string;
    description: string;
  }) {
    return (
      <div className="mb-8">
        <p className="mb-3 text-xs font-medium uppercase tracking-[0.18em] text-cyan-400">
          {subtitle}
        </p>
        <h1 className="text-3xl font-bold tracking-tight text-white md:text-4xl">
          {title}
        </h1>
        <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-400">
          {description}
        </p>
      </div>
    );
  }

  function StatCard({ label, value }: { label: string; value: string | number }) {
    return (
      <div className="rounded-2xl border border-white/10 bg-[#111c2e] p-5">
        <p className="text-sm text-slate-500">{label}</p>
        <p className="mt-3 text-2xl font-bold text-white">{value}</p>
      </div>
    );
  }

  function ImageCard({
    observation,
    title,
  }: {
    observation: Observation;
    title: string;
  }) {
    return (
      <div className="rounded-2xl border border-white/10 bg-[#111c2e] p-5">
        <h3 className="mb-4 font-semibold text-white">{title}</h3>
        <img
          src={`${apiUrl}/api/observations/${observation.id}/image`}
          alt={title}
          className="w-full rounded-xl bg-black object-contain"
        />
        <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
          <div>
            <p className="text-slate-500">Date</p>
            <p className="mt-1 text-slate-200">{observation.date || "—"}</p>
          </div>
          <div>
            <p className="text-slate-500">Image Size</p>
            <p className="mt-1 text-slate-200">
              {observation.image_shape?.join(" × ") || "—"}
            </p>
          </div>
          <div className="col-span-2">
            <p className="text-slate-500">Unit</p>
            <p className="mt-1 text-slate-200">{observation.unit || "—"}</p>
          </div>
        </div>
      </div>
    );
  }

  const currentFrame = frames[frameIndex];

  return (
    <main className="min-h-screen bg-[#080d18] text-white">
      <div className="flex min-h-screen">
        <aside className="hidden w-[292px] shrink-0 border-r border-white/10 bg-[#0b1322] px-4 py-6 lg:flex lg:flex-col">
          <div className="mb-9 px-3">
            <h1 className="text-3xl font-black tracking-tight text-cyan-400">
              SPHEREx.
            </h1>
            <p className="mt-1 text-xs uppercase tracking-[0.2em] text-slate-500">
              Space Explorer
            </p>
          </div>

          <nav className="space-y-2">
            {navigation.map((item) => (
              <button
                key={item.label}
                onClick={() => setActivePage(item.label)}
                className={`flex w-full items-center gap-3 rounded-xl px-4 py-3 text-left text-sm transition ${
                  activePage === item.label
                    ? "bg-cyan-500/15 font-semibold text-cyan-300"
                    : "text-slate-400 hover:bg-white/5 hover:text-white"
                }`}
              >
                <span className="w-5 text-lg">{item.icon}</span>
                {item.label}
              </button>
            ))}
          </nav>

          <div className="mt-auto rounded-2xl border border-white/10 p-5">
            <p className="text-xs uppercase tracking-wider text-slate-500">
              System Status
            </p>
            <p className="mt-3 flex items-center gap-2 text-sm font-medium text-emerald-300">
              <span className="h-2 w-2 rounded-full bg-emerald-400" />
              Backend connected
            </p>
          </div>
        </aside>

        <section className="min-w-0 flex-1 px-5 py-7 md:px-9 lg:px-12">
          <div className="mb-8 flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">
                Space Science / Exploration
              </p>
              <h2 className="mt-2 text-2xl font-bold">{activePage}</h2>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setApiUrl((prev) => (prev.includes("8001") ? "http://127.0.0.1:8000" : "http://127.0.0.1:8001"))}
                className="rounded-full border border-cyan-400/30 bg-cyan-400/10 px-3 py-1.5 font-mono text-xs text-cyan-300 hover:border-cyan-400"
                title="Click to toggle between port 8001 and 8000"
              >
                Port: {apiUrl.includes("8001") ? "8001 (Active)" : "8000"}
              </button>
              <span className="rounded-full border border-emerald-400/20 bg-emerald-400/5 px-4 py-2 text-xs text-emerald-300">
                Backend Connected
              </span>
            </div>
          </div>

          <div className="mb-6 flex gap-2 overflow-x-auto pb-2 lg:hidden">
            {navigation.map((item) => (
              <button
                key={item.label}
                onClick={() => setActivePage(item.label)}
                className={`shrink-0 rounded-lg px-3 py-2 text-xs ${
                  activePage === item.label
                    ? "bg-cyan-500/15 text-cyan-300"
                    : "bg-white/5 text-slate-400"
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>

          {error && (
            <div className="mb-6 rounded-xl border border-red-400/20 bg-red-400/5 p-4 text-sm text-red-300">
              {error}
            </div>
          )}

          {activePage === "Overview" && (
            <>
              <div className="overflow-hidden rounded-[28px] border border-cyan-400/20 bg-gradient-to-br from-[#172c4b] to-[#19112e] p-8 md:p-12">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-300">
                  Active Research Target
                </p>
                <h1 className="mt-5 text-5xl font-black tracking-tight md:text-6xl">
                  WISE 0855
                </h1>
                <p className="mt-5 text-lg text-slate-200">
                  Exploring the coldest known brown dwarfs.
                </p>
                <p className="mt-6 max-w-3xl leading-8 text-slate-400">
                  Explore SPHEREx observations, inspect infrared images, compare
                  observations over time, and investigate the predicted motion of
                  WISE 0855.
                </p>
                <button
                  onClick={() => setActivePage("Motion Detection")}
                  className="mt-8 rounded-xl bg-cyan-400 px-6 py-4 font-bold text-slate-950 transition hover:bg-cyan-300"
                >
                  Explore Motion Detection
                </button>
              </div>

              <div className="mt-10 grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
                <StatCard label="Target" value="WISE 0855" />
                <StatCard label="Observations" value={loading ? "…" : observations.length} />
                <StatCard label="Spectral Bands" value="6" />
                <StatCard label="Data Release" value="SPHEREx DR1" />
              </div>

              <div className="mt-12">
                <Heading
                  title="Mission Overview"
                  subtitle="Data Collection"
                  description="Downloaded SPHEREx observations."
                />
                {loading ? (
                  <p className="text-slate-400">Loading observations...</p>
                ) : (
                  <div className="overflow-x-auto rounded-2xl border border-white/10 bg-[#111c2e]">
                    <table className="w-full text-left text-sm">
                      <thead className="text-slate-500">
                        <tr>
                          <th className="p-5">Observation</th>
                          <th className="p-5">Date</th>
                          <th className="p-5">Image Size</th>
                          <th className="p-5">Unit</th>
                        </tr>
                      </thead>
                      <tbody>
                        {observations.map((item) => (
                          <tr key={item.id} className="border-t border-white/5">
                            <td className="p-5 font-medium">{item.filename}</td>
                            <td className="p-5">{item.date || "—"}</td>
                            <td className="p-5">{item.image_shape.join(" × ")}</td>
                            <td className="p-5">{item.unit || "—"}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </>
          )}

          {activePage === "Observations" && (
            <>
              <Heading
                title="Observations"
                subtitle="Data Collection"
                description="All downloaded FITS observations."
              />
              {loading ? (
                <p className="text-slate-400">Loading observations...</p>
              ) : observations.length === 0 ? (
                <p className="text-slate-400">No observations available.</p>
              ) : (
                <div className="grid gap-6 xl:grid-cols-2">
                  {observations.map((item) => (
                    <ImageCard
                      key={item.id}
                      observation={item}
                      title={item.filename}
                    />
                  ))}
                </div>
              )}
            </>
          )}

          {activePage === "Coordinate Search" && (
            <>
              <Heading
                title="Coordinate Search"
                subtitle="Sky Explorer"
                description="Search the downloaded images using celestial coordinates."
              />

              <form
                onSubmit={searchCoordinates}
                className="rounded-2xl border border-white/10 bg-[#111c2e] p-6"
              >
                <div className="grid gap-5 md:grid-cols-2">
                  <label className="block text-sm font-medium">
                    Right Ascension (degrees)
                    <input
                      value={ra}
                      onChange={(event) => setRa(event.target.value)}
                      type="number"
                      step="any"
                      required
                      className="mt-3 w-full rounded-xl border border-white/10 bg-[#080d18] px-4 py-4 text-white outline-none focus:border-cyan-400"
                    />
                  </label>
                  <label className="block text-sm font-medium">
                    Declination (degrees)
                    <input
                      value={dec}
                      onChange={(event) => setDec(event.target.value)}
                      type="number"
                      step="any"
                      required
                      className="mt-3 w-full rounded-xl border border-white/10 bg-[#080d18] px-4 py-4 text-white outline-none focus:border-cyan-400"
                    />
                  </label>
                </div>

                <button
                  disabled={searchLoading}
                  className="mt-6 rounded-xl bg-cyan-400 px-7 py-4 font-bold text-slate-950 disabled:opacity-50"
                >
                  {searchLoading ? "Searching..." : "Search Coordinates"}
                </button>
              </form>

              {searchError && (
                <p className="mt-5 text-sm text-red-300">{searchError}</p>
              )}

              {searchResults && (
                <div className="mt-8 rounded-2xl border border-white/10 bg-[#111c2e] p-6">
                  <h3 className="text-lg font-semibold">Search Results</h3>
                  <p className="mt-2 text-sm text-slate-400">
                    {searchResults.message}
                  </p>
                  <p className="mt-3 text-xs text-slate-500">
                    RA {searchResults.searched_coordinates.ra}° · DEC{" "}
                    {searchResults.searched_coordinates.dec}°
                  </p>
                  <div className="mt-5 space-y-3">
                    {searchResults.matches?.map((match) => (
                      <div
                        key={match.id}
                        className="rounded-xl border border-white/10 p-4"
                      >
                        <p className="font-semibold">{match.filename}</p>
                        <p className="mt-2 text-sm text-slate-400">
                          {match.inside_image ? "Inside image" : "Outside image"}
                          {" · "}Pixel X: {formatNumber(match.pixel_x ?? undefined, 3)}
                          {" · "}Pixel Y: {formatNumber(match.pixel_y ?? undefined, 3)}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}

          {activePage === "Image Viewer" && (
            <>
              <Heading
                title="Image Viewer"
                subtitle="Infrared Imaging"
                description="Inspect the downloaded SPHEREx infrared observations."
              />
              <div className="mb-6 flex flex-wrap gap-3">
                {observations.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => setSelectedObservation(item.id)}
                    className={`rounded-xl px-5 py-3 text-sm ${
                      selectedObservation === item.id
                        ? "bg-cyan-400 font-semibold text-slate-950"
                        : "border border-white/10 bg-[#111c2e] text-slate-300"
                    }`}
                  >
                    {item.id === "first" ? "First Observation" : "Second Observation"}
                  </button>
                ))}
              </div>

              <div className="rounded-2xl border border-white/10 bg-[#111c2e] p-5">
                <div className="mb-5 flex items-center justify-between">
                  <h3 className="font-semibold">Image Zoom</h3>
                  <span className="text-sm text-cyan-300">{zoom}%</span>
                </div>
                <input
                  type="range"
                  min="50"
                  max="250"
                  value={zoom}
                  onChange={(event) => setZoom(Number(event.target.value))}
                  className="w-full accent-cyan-400"
                />
                <button
                  onClick={() => setZoom(100)}
                  className="mt-4 rounded-lg border border-white/10 px-4 py-2 text-sm"
                >
                  Reset Zoom
                </button>
              </div>

              {observations.map(
                (item) =>
                  item.id === selectedObservation && (
                    <div
                      key={item.id}
                      className="mt-6 overflow-auto rounded-2xl border border-white/10 bg-[#111c2e] p-5"
                    >
                      <h3 className="mb-4 font-semibold">{item.filename}</h3>
                      <img
                        src={`${apiUrl}/api/observations/${item.id}/image`}
                        alt={item.filename}
                        style={{ width: `${zoom}%`, maxWidth: "none" }}
                        className="mx-auto rounded-xl"
                      />
                    </div>
                  )
              )}
            </>
          )}

          {activePage === "Time-Lapse" && (
            <>
              <Heading
                title="Time-Lapse"
                subtitle="Observation Sequence"
                description="Browse the downloaded image sequence. This time-lapse currently contains the two locally downloaded FITS images."
              />

              {frames.length === 0 ? (
                <div className="rounded-2xl border border-white/10 bg-[#111c2e] p-6 text-slate-400">
                  No time-lapse frames are available from the backend.
                </div>
              ) : (
                <div className="rounded-2xl border border-white/10 bg-[#111c2e] p-6">
                  <div className="flex min-h-[420px] items-center justify-center rounded-xl bg-black p-4">
                    {currentFrame && (
                      <img
                        src={currentFrame.image_url}
                        alt={currentFrame.filename}
                        className="max-h-[620px] max-w-full object-contain"
                      />
                    )}
                  </div>

                  <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
                    <button
                      onClick={() => {
                        setIsPlaying(false);
                        setFrameIndex(0);
                      }}
                      className="rounded-lg border border-white/10 px-4 py-3"
                    >
                      First
                    </button>
                    <button
                      onClick={() => {
                        setIsPlaying(false);
                        setFrameIndex((index) => Math.max(0, index - 1));
                      }}
                      className="rounded-lg border border-white/10 px-4 py-3"
                    >
                      Previous
                    </button>
                    <button
                      onClick={() => setIsPlaying((value) => !value)}
                      className="rounded-lg bg-cyan-400 px-5 py-3 font-semibold text-slate-950"
                    >
                      {isPlaying ? "Pause" : "Play"}
                    </button>
                    <button
                      onClick={() => {
                        setIsPlaying(false);
                        setFrameIndex((index) => Math.min(frames.length - 1, index + 1));
                      }}
                      className="rounded-lg border border-white/10 px-4 py-3"
                    >
                      Next
                    </button>
                    <button
                      onClick={() => {
                        setIsPlaying(false);
                        setFrameIndex(frames.length - 1);
                      }}
                      className="rounded-lg border border-white/10 px-4 py-3"
                    >
                      Last
                    </button>
                  </div>

                  <input
                    type="range"
                    min="0"
                    max={Math.max(0, frames.length - 1)}
                    value={frameIndex}
                    onChange={(event) => {
                      setIsPlaying(false);
                      setFrameIndex(Number(event.target.value));
                    }}
                    className="mt-6 w-full accent-cyan-400"
                  />

                  <p className="mt-4 text-center text-sm text-slate-400">
                    {currentFrame?.filename} · Frame {frameIndex + 1} of {frames.length}
                  </p>
                </div>
              )}
            </>
          )}

          {activePage === "Archive Timeline" && (
            <>
              <Heading
                title="SPHEREx Observation Archive"
                subtitle="27-DATE DATA TIMELINE"
                description="Explore the available observation records across six spectral bands from the SPHEREx DR1 archive."
              />

              {timelineError && (
                <div className="mb-5 rounded-xl border border-red-400/20 bg-red-400/5 p-4 text-sm text-red-300">
                  {timelineError}
                  <button
                    onClick={loadTimeline}
                    className="ml-3 underline underline-offset-4"
                  >
                    Try again
                  </button>
                </div>
              )}

              {timelineLoading && !timeline && (
                <p className="text-slate-400">Loading archive timeline...</p>
              )}

              {timeline && (
                <>
                  <div className="mb-7 grid grid-cols-1 gap-4 sm:grid-cols-3">
                    <StatCard
                      label="Observation Dates"
                      value={timeline.total_dates}
                    />
                    <StatCard
                      label="Spectral Bands"
                      value={timeline.total_bands}
                    />
                    <StatCard
                      label="Date-Band Groups"
                      value={timeline.total_groups}
                    />
                  </div>

                  <div className="mb-7 rounded-2xl border border-white/10 bg-[#111c2e] p-6">
                    <h3 className="mb-5 text-lg font-semibold">
                      Observation Coverage
                    </h3>
                    <div className="space-y-4">
                      {Array.from(
                        new Set(timeline.timeline.map((item) => item.date))
                      ).map((date) => {
                        const dayItems = timeline.timeline.filter(
                          (item) => item.date === date
                        );
                        const totalRecords = dayItems.reduce(
                          (sum, item) => sum + item.records,
                          0
                        );

                        return (
                          <div key={date}>
                            <div className="mb-2 flex items-center justify-between gap-4 text-sm">
                              <span className="text-slate-300">{date}</span>
                              <span className="text-cyan-300">
                                {totalRecords} records · {dayItems.length} bands
                              </span>
                            </div>
                            <div className="flex h-3 overflow-hidden rounded-full bg-white/5">
                              {dayItems.map((item) => (
                                <div
                                  key={`${date}-${item.energy_bandpassname}`}
                                  title={`${item.energy_bandpassname}: ${item.records} records`}
                                  style={{
                                    width: `${(item.records / Math.max(totalRecords, 1)) * 100}%`,
                                  }}
                                  className="border-r border-[#080d18] bg-cyan-400"
                                />
                              ))}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  <div className="overflow-x-auto rounded-2xl border border-white/10 bg-[#111c2e]">
                    <div className="border-b border-white/10 p-5">
                      <h3 className="font-semibold">Archive Records by Date and Band</h3>
                      <p className="mt-2 text-sm text-slate-400">
                        {timeline.total_groups} date-band groups from{" "}
                        {timeline.total_dates} observation dates.
                      </p>
                    </div>

                    <table className="w-full text-left text-sm">
                      <thead className="bg-white/5 text-cyan-300">
                        <tr>
                          <th className="p-4">Observation Date</th>
                          <th className="p-4">Spectral Band</th>
                          <th className="p-4">Records</th>
                          <th className="p-4">Unique Observations</th>
                        </tr>
                      </thead>
                      <tbody>
                        {timeline.timeline.map((item, index) => (
                          <tr
                            key={`${item.date}-${item.energy_bandpassname}-${index}`}
                            className="border-t border-white/5"
                          >
                            <td className="p-4 text-slate-200">{item.date}</td>
                            <td className="p-4 font-semibold text-cyan-300">
                              {item.energy_bandpassname}
                            </td>
                            <td className="p-4 text-slate-300">{item.records}</td>
                            <td className="p-4 text-slate-300">
                              {item.unique_observations}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  <p className="mt-5 text-sm leading-7 text-slate-400">
                    The archive summary contains 27 distinct observation dates,
                    six spectral bands, and 70 date-band groups. These are
                    archive metadata records, not 70 downloaded FITS images.
                    The current image time-lapse remains based on the two
                    locally downloaded FITS cutouts.
                  </p>
                </>
              )}
            </>
          )}

          {activePage === "Image Comparison" && (
            <>
              <Heading
                title="Image Comparison"
                subtitle="Comparative Analysis"
                description="Compare the two downloaded observations after image alignment."
              />

              {comparisonLoading && (
                <p className="text-slate-400">Analyzing observations...</p>
              )}

              {comparisonError && (
                <p className="text-sm text-red-300">{comparisonError}</p>
              )}

              {comparison && (
                <>
                  <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                    <StatCard
                      label="Pixel Overlap"
                      value={`${formatNumber(comparison.overlap_percentage, 2)}%`}
                    />
                    <StatCard
                      label="Valid Pixels"
                      value={comparison.valid_pixels}
                    />
                    <StatCard
                      label="Background Offset"
                      value={formatNumber(comparison.background_offset, 6)}
                    />
                    <StatCard
                      label="Difference Std"
                      value={formatNumber(comparison.difference_std, 6)}
                    />
                  </div>

                  <div className="mt-7 grid gap-6 xl:grid-cols-2">
                    {observations.map((item) => (
                      <ImageCard
                        key={item.id}
                        observation={item}
                        title={item.filename}
                      />
                    ))}
                  </div>

                  <div className="mt-7 rounded-2xl border border-white/10 bg-[#111c2e] p-6">
                    <h3 className="font-semibold">Preliminary Difference Image</h3>
                    <img
                      src={`${apiUrl}/api/analysis/difference/image`}
                      alt="Preliminary image difference"
                      className="mt-5 w-full rounded-xl bg-white"
                    />
                    <p className="mt-4 text-sm leading-7 text-slate-400">
                      {comparison.scientific_note ||
                        "This is a preliminary difference image. It should not be interpreted as a confirmed detection of variability."}
                    </p>
                  </div>
                </>
              )}
            </>
          )}

          {activePage === "Scientific Analysis" && (
            <>
              <Heading
                title="Scientific Analysis"
                subtitle="Scientific Processing"
                description="Run source detection on the downloaded observations."
              />

              <div className="grid gap-6 xl:grid-cols-2">
                {observations.map((item) => {
                  const result = detections[item.id];
                  const isLoading = detectionLoading[item.id];

                  return (
                    <div
                      key={item.id}
                      className="rounded-2xl border border-white/10 bg-[#111c2e] p-6"
                    >
                      <h3 className="font-semibold">{item.filename}</h3>
                      <button
                        onClick={() => runDetection(item.id)}
                        disabled={isLoading}
                        className="mt-6 rounded-xl bg-cyan-400 px-6 py-4 font-semibold text-slate-950 disabled:opacity-50"
                      >
                        {isLoading ? "Analyzing..." : "Run Source Detection"}
                      </button>

                      {detectionErrors[item.id] && (
                        <p className="mt-4 text-sm text-red-300">
                          {detectionErrors[item.id]}
                        </p>
                      )}

                      {result && (
                        <div className="mt-6">
                          <p className="font-semibold text-cyan-300">
                            Candidate sources: {result.result.number_of_sources}
                          </p>
                          <p className="mt-3 text-sm text-slate-300">
                            Background: {formatNumber(result.result.background_level, 6)}
                          </p>
                          <p className="mt-2 text-sm text-slate-300">
                            Noise: {formatNumber(result.result.noise, 6)}
                          </p>

                          <div className="mt-5 max-h-80 space-y-2 overflow-y-auto">
                            {result.result.sources.map((source, index) => (
                              <div
                                key={index}
                                className="border-b border-white/5 py-3 text-sm text-slate-400"
                              >
                                Source {index + 1}: X {formatNumber(source.x, 2)},
                                Y {formatNumber(source.y, 2)}, Flux{" "}
                                {formatNumber(source.flux, 3)}
                              </div>
                            ))}
                          </div>

                          <p className="mt-5 text-xs leading-6 text-slate-500">
                            {result.scientific_note}
                          </p>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </>
          )}

          {activePage === "Motion Detection" && (
            <>
              <Heading
                title="Motion Detection"
                subtitle="Astrometric Prediction"
                description="Explore the predicted position of WISE 0855 using proper motion and approximate annual parallax."
              />

              {motionLoading && (
                <p className="text-slate-400">Calculating predicted positions...</p>
              )}

              {motionError && (
                <p className="text-sm text-red-300">{motionError}</p>
              )}

              {motion && (
                <>
                  <div className="grid gap-4 sm:grid-cols-2">
                    <StatCard label="Target" value={motion.target} />
                    <StatCard
                      label="Successful Predictions"
                      value={motion.observations.filter((item) => item.status === "success").length}
                    />
                  </div>

                  <h3 className="mb-5 mt-10 text-xl font-semibold">
                    Predicted Observation Positions
                  </h3>

                  <div className="grid gap-6 xl:grid-cols-2">
                    {motion.observations.map((item, index) => (
                      <div
                        key={`${item.observation}-${index}`}
                        className="rounded-2xl border border-white/10 bg-[#111c2e] p-6"
                      >
                        <div className="flex items-center justify-between gap-3">
                          <h3 className="font-semibold">{item.observation}</h3>
                          <span
                            className={`rounded-full px-3 py-2 text-xs ${
                              item.inside_image
                                ? "bg-emerald-400/10 text-emerald-300"
                                : "bg-amber-400/10 text-amber-300"
                            }`}
                          >
                            {item.inside_image ? "Inside image" : "Outside image"}
                          </span>
                        </div>

                        <p className="mt-4 text-sm text-slate-400">
                          Date: {item.date || "—"}
                        </p>

                        {item.status === "success" ? (
                          <>
                            <div className="mt-6 grid grid-cols-2 gap-3">
                              <div className="rounded-xl bg-white/5 p-4">
                                <p className="text-xs text-slate-500">Predicted RA</p>
                                <p className="mt-2 font-mono text-cyan-300">
                                  {formatNumber(item.predicted_ra)}°
                                </p>
                              </div>
                              <div className="rounded-xl bg-white/5 p-4">
                                <p className="text-xs text-slate-500">Predicted DEC</p>
                                <p className="mt-2 font-mono text-cyan-300">
                                  {formatNumber(item.predicted_dec)}°
                                </p>
                              </div>
                              <div className="rounded-xl bg-white/5 p-4">
                                <p className="text-xs text-slate-500">Pixel X</p>
                                <p className="mt-2 font-mono text-xl">
                                  {formatNumber(item.pixel_x, 3)}
                                </p>
                              </div>
                              <div className="rounded-xl bg-white/5 p-4">
                                <p className="text-xs text-slate-500">Pixel Y</p>
                                <p className="mt-2 font-mono text-xl">
                                  {formatNumber(item.pixel_y, 3)}
                                </p>
                              </div>
                            </div>

                            <div className="mt-6 rounded-xl bg-[#080d18] p-5">
                              <p className="text-sm text-slate-400">
                                Predicted pixel location (schematic)
                              </p>
                              <div className="mx-auto mt-4 flex h-64 w-full max-w-[300px] items-center justify-center border border-cyan-400/30 bg-[#111c2e]">
                                <div className="relative h-full w-full">
                                  <span
                                    className="absolute h-4 w-4 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-cyan-200 bg-cyan-400 shadow-[0_0_15px_rgba(34,211,238,0.7)]"
                                    style={{
                                      left: `${((item.pixel_x || 0) / (item.image_width || 58)) * 100}%`,
                                      top: `${(1 - (item.pixel_y || 0) / (item.image_height || 59)) * 100}%`,
                                    }}
                                  />
                                </div>
                              </div>
                              <p className="mt-3 text-center text-xs text-slate-500">
                                Image: {item.image_width} × {item.image_height} pixels
                              </p>
                            </div>
                          </>
                        ) : (
                          <p className="mt-4 text-sm text-red-300">
                            {item.message || "Could not analyze this observation."}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>

                  <div className="mt-6 rounded-xl border border-amber-400/20 bg-amber-400/5 p-5">
                    <h3 className="font-semibold text-amber-300">Scientific Note</h3>
                    <p className="mt-3 text-sm leading-7 text-slate-300">
                      {motion.scientific_note}
                    </p>
                    <p className="mt-3 text-xs leading-6 text-slate-400">
                      The plotted marker is a schematic representation of the
                      predicted pixel coordinate, not an automatically detected
                      source in the FITS image.
                    </p>
                  </div>
                </>
              )}
            </>
          )}


          {/* ========================================================= */}
          {/* PHASE 4A: 102-BAND EXPLORER */}
          {/* ========================================================= */}
          {activePage === "102-Band Explorer" && (
            <>
              <Heading
                title="102-Band Spectroscopic Explorer"
                subtitle="Phase 4A · Multi-Channel LVF Spectroscopy"
                description="Explore the continuous 0.75 – 5.0 µm spectral coverage provided by SPHEREx's 6 Linear Variable Filters (D1 to D6). Select any of the 102 channels or extract local in-situ spectra directly from FITS WCS-WAVE tables."
              />

              {bandsLoading && <p className="text-slate-400">Loading SPHEREx 102-band metadata...</p>}
              {bandsError && <p className="text-sm text-red-300">{bandsError}</p>}

              {/* Top Control Grid: Channel Selector & Spectrum Extraction */}
              <div className="grid gap-6 lg:grid-cols-2">
                {/* Wavelength & Channel Selector */}
                <div className="rounded-2xl border border-white/10 bg-[#111c2e] p-6">
                  <h3 className="text-lg font-semibold text-white">102-Channel Selector</h3>
                  <p className="mt-1 text-xs text-slate-400">
                    Slide or select any discrete SPHEREx spectroscopic channel across the 6 detectors.
                  </p>

                  <div className="mt-5 space-y-4">
                    <div>
                      <div className="flex justify-between text-xs font-mono">
                        <span className="text-slate-400">Channel ID:</span>
                        <span className="font-bold text-cyan-300">
                          Channel #{selectedChannelId} / 102
                        </span>
                      </div>
                      <input
                        type="range"
                        min={1}
                        max={102}
                        value={selectedChannelId}
                        onChange={(e) => setSelectedChannelId(Number(e.target.value))}
                        className="mt-2 w-full accent-cyan-400"
                      />
                    </div>

                    {/* Quick Jumps to Key Atmospheric Windows */}
                    <div>
                      <p className="text-xs text-slate-500">Quick Jump to Scientific Windows:</p>
                      <div className="mt-2 flex flex-wrap gap-2">
                        {[
                          { id: 10, label: "D1: FeH / 0.93µm" },
                          { id: 25, label: "D2: 1.4µm H2O" },
                          { id: 45, label: "D3: 2.1µm Bump" },
                          { id: 50, label: "D3: 2.36µm (Cutout)" },
                          { id: 60, label: "D4: 2.7µm Ice" },
                          { id: 75, label: "D5: 4.3µm CO2" },
                          { id: 95, label: "D6: 4.5µm Peak" },
                        ].map((btn) => (
                          <button
                            key={btn.id}
                            onClick={() => setSelectedChannelId(btn.id)}
                            className={`rounded-lg px-2.5 py-1 text-xs font-mono transition ${
                              selectedChannelId === btn.id
                                ? "bg-cyan-500/20 text-cyan-300 border border-cyan-400/40"
                                : "bg-white/5 text-slate-400 hover:bg-white/10"
                            }`}
                          >
                            {btn.label}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Channel Detail Card */}
                    {bandsSummary && (
                      (() => {
                        const ch = bandsSummary.channels.find((c) => c.channel_id === selectedChannelId);
                        if (!ch) return null;
                        return (
                          <div className="rounded-xl bg-[#080d18] p-4 font-mono text-xs space-y-2 border border-white/5">
                            <div className="flex justify-between border-b border-white/5 pb-1.5">
                              <span className="text-slate-400">Detector Array:</span>
                              <span className="font-bold text-cyan-300">{ch.detector} (Band {ch.band})</span>
                            </div>
                            <div className="flex justify-between border-b border-white/5 pb-1.5">
                              <span className="text-slate-400">Central Wavelength (λ):</span>
                              <span className="font-bold text-emerald-400">{ch.wavelength_um.toFixed(4)} µm</span>
                            </div>
                            <div className="flex justify-between border-b border-white/5 pb-1.5">
                              <span className="text-slate-400">Bandwidth (Δλ):</span>
                              <span className="text-slate-200">{ch.bandwidth_um.toFixed(4)} µm</span>
                            </div>
                            <div className="flex justify-between border-b border-white/5 pb-1.5">
                              <span className="text-slate-400">Spectral Resolving Power (R):</span>
                              <span className="text-slate-200">~{ch.resolving_power}</span>
                            </div>
                            <div className="pt-1">
                              <span className="text-slate-400 block text-[11px]">Primary Astrophysical Features:</span>
                              <span className="text-amber-300 text-[11px]">{ch.science_notes}</span>
                            </div>
                          </div>
                        );
                      })()
                    )}
                  </div>
                </div>

                {/* In-situ Spectrum Extraction Tool */}
                <div className="rounded-2xl border border-white/10 bg-[#111c2e] p-6">
                  <h3 className="text-lg font-semibold text-white">In-Situ Spectrum Extraction</h3>
                  <p className="mt-1 text-xs text-slate-400">
                    Extracts calibrated wavelength from the FITS WCS-WAVE table & aperture flux density.
                  </p>

                  <form onSubmit={handleExtractSpectrum} className="mt-5 space-y-3">
                    <div className="grid grid-cols-3 gap-2">
                      <div>
                        <label className="text-[11px] text-slate-400">Observation</label>
                        <select
                          value={specObsId}
                          onChange={(e) => setSpecObsId(e.target.value)}
                          className="mt-1 w-full rounded-xl bg-white/5 px-3 py-2 text-xs font-mono text-white focus:outline-none"
                        >
                          <option value="first">Epoch 1 (2025)</option>
                          <option value="second">Epoch 2 (2026)</option>
                        </select>
                      </div>
                      <div>
                        <label className="text-[11px] text-slate-400">Pixel X</label>
                        <input
                          type="text"
                          value={specPixelX}
                          onChange={(e) => setSpecPixelX(e.target.value)}
                          className="mt-1 w-full rounded-xl bg-white/5 px-3 py-2 text-xs font-mono text-white focus:outline-none"
                          placeholder="28.22"
                        />
                      </div>
                      <div>
                        <label className="text-[11px] text-slate-400">Pixel Y</label>
                        <input
                          type="text"
                          value={specPixelY}
                          onChange={(e) => setSpecPixelY(e.target.value)}
                          className="mt-1 w-full rounded-xl bg-white/5 px-3 py-2 text-xs font-mono text-white focus:outline-none"
                          placeholder="28.74"
                        />
                      </div>
                    </div>

                    <div className="flex items-center gap-2 pt-1">
                      <button
                        type="button"
                        onClick={() => {
                          setSpecPixelX("28.22");
                          setSpecPixelY("28.74");
                        }}
                        className="rounded-lg bg-white/5 px-2.5 py-1.5 text-[11px] font-mono text-slate-400 hover:bg-white/10"
                      >
                        🎯 Target Preset (28.22, 28.74)
                      </button>
                      <button
                        type="submit"
                        disabled={spectrumLoading}
                        className="rounded-lg bg-cyan-500/20 px-4 py-1.5 text-xs font-medium text-cyan-300 hover:bg-cyan-500/30 transition disabled:opacity-50"
                      >
                        {spectrumLoading ? "Extracting..." : "Extract Spectrum"}
                      </button>
                    </div>
                  </form>

                  {spectrumError && <p className="mt-3 text-xs text-red-300">{spectrumError}</p>}

                  {extractedSpectrum && (
                    <div className="mt-4 rounded-xl bg-[#080d18] p-4 font-mono text-xs space-y-2 border border-white/5">
                      <div className="flex justify-between border-b border-white/5 pb-1">
                        <span className="text-slate-400">Calibrated Wavelength:</span>
                        <span className="font-bold text-cyan-300">
                          {extractedSpectrum.in_situ_spectrum.wavelength_um.toFixed(4)} µm (Band D3)
                        </span>
                      </div>
                      <div className="flex justify-between border-b border-white/5 pb-1">
                        <span className="text-slate-400">Aperture Flux Density:</span>
                        <span className="font-bold text-amber-300">
                          {extractedSpectrum.in_situ_spectrum.flux_density_ujy.toFixed(2)} ± {extractedSpectrum.in_situ_spectrum.flux_uncertainty_ujy.toFixed(2)} µJy
                        </span>
                      </div>
                      <div className="flex justify-between border-b border-white/5 pb-1">
                        <span className="text-slate-400">Signal-to-Noise Ratio:</span>
                        <span className="text-emerald-400 font-bold">
                          {extractedSpectrum.in_situ_spectrum.signal_to_noise.toFixed(2)}σ
                        </span>
                      </div>
                      <div className="flex justify-between border-b border-white/5 pb-1">
                        <span className="text-slate-400">FITS Quality Flags:</span>
                        <span className="text-slate-300">
                          {extractedSpectrum.in_situ_spectrum.quality_flags.join(", ") || "Clean (0)"}
                        </span>
                      </div>
                      <p className="pt-1 text-[11px] leading-relaxed text-slate-400">
                        {extractedSpectrum.scientific_interpretation}
                      </p>
                    </div>
                  )}
                </div>
              </div>

              {/* Spectral Energy Distribution Plot */}
              <div className="mt-8 rounded-2xl border border-white/10 bg-[#111c2e] p-6">
                <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <h3 className="text-lg font-semibold text-white">
                      Full 102-Band Spectral Energy Distribution (SED)
                    </h3>
                    <p className="text-xs text-slate-400">
                      Sonora Bobcat / ATMO synthetic cold brown dwarf model (250 K) across all 6 SPHEREx LVF arrays, overlaid with current FITS cutout measurement.
                    </p>
                  </div>
                  <span className="rounded-full bg-cyan-400/10 px-3 py-1 font-mono text-xs text-cyan-300 border border-cyan-400/30">
                    Selected Channel: #{selectedChannelId}
                  </span>
                </div>

                <div className="flex justify-center overflow-hidden rounded-xl bg-black border border-white/10 p-2">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={`${apiUrl}/api/bands/spectral-plot?channel_id=${selectedChannelId}&observation_id=${specObsId}&pixel_x=${specPixelX}&pixel_y=${specPixelY}`}
                    alt="SPHEREx 102-Band SED"
                    className="max-h-[460px] w-auto object-contain"
                  />
                </div>
              </div>

              {/* 6-Detector Architecture Comparison Cards */}
              <h3 className="mb-4 mt-10 text-xl font-semibold">SPHEREx 6-Detector Array Architecture</h3>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {bandsSummary?.bands.map((b) => (
                  <div
                    key={b.band}
                    className="rounded-2xl border border-white/10 bg-[#111c2e] p-5 relative overflow-hidden"
                  >
                    <div
                      className="absolute top-0 left-0 right-0 h-1"
                      style={{ backgroundColor: b.color }}
                    />
                    <div className="flex items-center justify-between">
                      <h4 className="text-base font-bold text-white">{b.detector}</h4>
                      <span
                        className="rounded-full px-2.5 py-0.5 text-xs font-mono font-bold"
                        style={{ backgroundColor: `${b.color}20`, color: b.color }}
                      >
                        Band {b.band}
                      </span>
                    </div>

                    <div className="mt-4 space-y-1.5 font-mono text-xs">
                      <div className="flex justify-between text-slate-400">
                        <span>Wavelength Range:</span>
                        <span className="text-white">{b.wavelength_min_um.toFixed(2)} – {b.wavelength_max_um.toFixed(2)} µm</span>
                      </div>
                      <div className="flex justify-between text-slate-400">
                        <span>Spectral Channels:</span>
                        <span className="text-white">{b.channels_count} channels</span>
                      </div>
                      <div className="flex justify-between text-slate-400">
                        <span>Resolving Power:</span>
                        <span className="text-white">R ~ {b.resolving_power}</span>
                      </div>
                      <div className="flex justify-between text-slate-400">
                        <span>Archive Records:</span>
                        <span className="text-cyan-300 font-bold">{b.archive_records_wise0855} records</span>
                      </div>
                    </div>

                    <p className="mt-3 text-[11px] text-slate-400 leading-snug border-t border-white/5 pt-2">
                      {b.primary_features}
                    </p>
                  </div>
                ))}
              </div>

              {/* Scientific Note on Linear Variable Filters */}
              <div className="mt-8 rounded-xl border border-cyan-400/20 bg-cyan-400/5 p-5">
                <h3 className="font-semibold text-cyan-300">Linear Variable Filter (LVF) Operation Note</h3>
                <p className="mt-2 text-sm leading-7 text-slate-300">
                  SPHEREx does not use a dispersive grating or grism; instead, each focal plane array is overlaid
                  with a Linear Variable Filter (LVF) whose bandpass shifts continuously across the detector columns.
                  A source’s spectrum is built up as the telescope steps across the sky in multiple visits and dithers.
                </p>
              </div>
            </>
          )}

          {/* ========================================================= */}
          {/* PHASE 4B: EXTERNAL CATALOG OVERLAY */}
          {/* ========================================================= */}
          {activePage === "External Catalogs" && (
            <>
              <Heading
                title="External Catalog Overlay"
                subtitle="Phase 4B · Multi-Wavelength Cone Search"
                description="Cross-reference SPHEREx observations against authoritative astrometric and infrared catalogs (Gaia DR3, AllWISE, CatWISE) via IRSA Cone Search."
              />

              {/* Cone Search & Layer Controls */}
              <div className="rounded-2xl border border-white/10 bg-[#111c2e] p-6">
                <form onSubmit={loadCatalogs} className="flex flex-wrap items-end gap-3">
                  <div>
                    <label className="text-xs text-slate-400">Right Ascension (RA)</label>
                    <input
                      type="text"
                      value={catRa}
                      onChange={(e) => setCatRa(e.target.value)}
                      className="mt-1 block rounded-xl bg-white/5 px-3 py-2 text-xs font-mono text-white focus:outline-none w-32"
                      placeholder="133.79513"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-slate-400">Declination (Dec)</label>
                    <input
                      type="text"
                      value={catDec}
                      onChange={(e) => setCatDec(e.target.value)}
                      className="mt-1 block rounded-xl bg-white/5 px-3 py-2 text-xs font-mono text-white focus:outline-none w-32"
                      placeholder="-7.24515"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-slate-400">Search Radius</label>
                    <input
                      type="text"
                      value={catRadius}
                      onChange={(e) => setCatRadius(e.target.value)}
                      className="mt-1 block rounded-xl bg-white/5 px-3 py-2 text-xs font-mono text-white focus:outline-none w-24"
                      placeholder="2.0"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-slate-400">Observation</label>
                    <select
                      value={catObsId}
                      onChange={(e) => setCatObsId(e.target.value)}
                      className="mt-1 block rounded-xl bg-white/5 px-3 py-2 text-xs font-mono text-white focus:outline-none"
                    >
                      <option value="first">Epoch 1 (May 2025)</option>
                      <option value="second">Epoch 2 (May 2026)</option>
                    </select>
                  </div>
                  <button
                    type="submit"
                    disabled={catalogLoading}
                    className="rounded-xl bg-cyan-500/20 px-5 py-2 text-xs font-semibold text-cyan-300 hover:bg-cyan-500/30 transition disabled:opacity-50"
                  >
                    {catalogLoading ? "Searching IRSA..." : "Run Cone Search"}
                  </button>
                </form>

                {/* Layer Toggle Checkboxes */}
                <div className="mt-4 flex flex-wrap items-center gap-4 pt-3 border-t border-white/5 text-xs font-mono">
                  <span className="text-slate-500 uppercase tracking-wider">Overlay Layers:</span>
                  <label className="flex items-center gap-2 cursor-pointer text-cyan-300">
                    <input
                      type="checkbox"
                      checked={showGaia}
                      onChange={(e) => setShowGaia(e.target.checked)}
                      className="accent-cyan-400 rounded"
                    />
                    <span>Gaia DR3 (Stars ◇)</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer text-amber-300">
                    <input
                      type="checkbox"
                      checked={showWise}
                      onChange={(e) => setShowWise(e.target.checked)}
                      className="accent-amber-400 rounded"
                    />
                    <span>AllWISE (IR Sources □)</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer text-indigo-300">
                    <input
                      type="checkbox"
                      checked={showCatwise}
                      onChange={(e) => setShowCatwise(e.target.checked)}
                      className="accent-indigo-400 rounded"
                    />
                    <span>CatWISE 2020</span>
                  </label>
                </div>
              </div>

              {catalogLoading && <p className="mt-4 text-slate-400">Querying NASA/IPAC IRSA catalogs...</p>}
              {catalogError && <p className="mt-4 text-sm text-red-300">{catalogError}</p>}

              {/* Summary Metric Cards */}
              {catalogData && (
                <div className="mt-6 grid gap-4 sm:grid-cols-4">
                  <StatCard label="Total Catalog Sources" value={catalogData.total_sources} />
                  <StatCard label="Inside FITS Cutout" value={catalogData.inside_cutout_count} />
                  <StatCard label="Gaia DR3 Stars" value={catalogData.gaia_dr3.length} />
                  <StatCard label="AllWISE Infrared Sources" value={catalogData.allwise.length} />
                </div>
              )}

              {/* Visual Overlay Image */}
              <div className="mt-8 rounded-2xl border border-white/10 bg-[#111c2e] p-6">
                <div className="mb-4 flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-white">FITS Cutout with Catalog Astrometric Overlay</h3>
                  <span className="text-xs font-mono text-slate-400">
                    Diamonds: Gaia Stars · Squares: AllWISE Sources · Reticle: Target
                  </span>
                </div>
                <div className="flex justify-center overflow-hidden rounded-xl bg-black border border-white/10 p-2">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={`${apiUrl}/api/catalogs/overlay-image/${catObsId}?ra=${catRa}&dec=${catDec}&show_gaia=${showGaia}&show_wise=${showWise}&show_catwise=${showCatwise}`}
                    alt="Catalog Overlay Preview"
                    className="max-h-[460px] w-auto object-contain"
                  />
                </div>
              </div>

              {/* Catalog Cross-Match Table */}
              {catalogData && (
                <div className="mt-8 rounded-2xl border border-white/10 bg-[#111c2e] p-6">
                  <div className="mb-4 flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-white">Cone Search Sources</h3>
                    <div className="flex gap-1 bg-[#080d18] p-1 rounded-lg">
                      {(["all", "gaia", "wise", "catwise"] as const).map((tab) => (
                        <button
                          key={tab}
                          onClick={() => setCatalogTab(tab)}
                          className={`rounded px-3 py-1 text-xs font-mono uppercase ${
                            catalogTab === tab ? "bg-cyan-500/20 text-cyan-300 font-bold" : "text-slate-400 hover:text-white"
                          }`}
                        >
                          {tab}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs font-mono">
                      <thead>
                        <tr className="border-b border-white/10 text-slate-400">
                          <th className="py-2.5 px-3">Catalog / ID</th>
                          <th className="py-2.5 px-3">RA / Dec (deg)</th>
                          <th className="py-2.5 px-3">Pixel (X, Y)</th>
                          <th className="py-2.5 px-3">Photometry</th>
                          <th className="py-2.5 px-3">Proper Motion (mas/yr)</th>
                          <th className="py-2.5 px-3">Dist. (arcsec)</th>
                          <th className="py-2.5 px-3">Cutout Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-white/5 text-slate-200">
                        {(catalogTab === "all" || catalogTab === "gaia") &&
                          catalogData.gaia_dr3.slice(0, 15).map((s) => (
                            <tr key={`gaia-${s.id}`}>
                              <td className="py-2.5 px-3 font-semibold text-cyan-300">Gaia {s.id}</td>
                              <td className="py-2.5 px-3">{s.ra.toFixed(4)}, {s.dec.toFixed(4)}</td>
                              <td className="py-2.5 px-3">X={s.pixel_x}, Y={s.pixel_y}</td>
                              <td className="py-2.5 px-3 text-cyan-200">{s.g_mag ? `G=${s.g_mag}` : "—"}</td>
                              <td className="py-2.5 px-3">
                                {s.pm_ra_mas_yr !== null ? `pmRA: ${s.pm_ra_mas_yr}, pmDE: ${s.pm_dec_mas_yr}` : "—"}
                              </td>
                              <td className="py-2.5 px-3">{s.separation_arcsec.toFixed(1)}″</td>
                              <td className="py-2.5 px-3">
                                <span className={`px-2 py-0.5 rounded text-[10px] ${s.inside_cutout ? "bg-emerald-400/10 text-emerald-300" : "bg-slate-800 text-slate-400"}`}>
                                  {s.inside_cutout ? "Inside" : "Outside"}
                                </span>
                              </td>
                            </tr>
                          ))}

                        {(catalogTab === "all" || catalogTab === "wise") &&
                          catalogData.allwise.slice(0, 15).map((s) => (
                            <tr key={`wise-${s.id}`}>
                              <td className="py-2.5 px-3 font-semibold text-amber-300">AllWISE {s.id}</td>
                              <td className="py-2.5 px-3">{s.ra.toFixed(4)}, {s.dec.toFixed(4)}</td>
                              <td className="py-2.5 px-3">X={s.pixel_x}, Y={s.pixel_y}</td>
                              <td className="py-2.5 px-3 text-amber-200">
                                {s.w1_mag ? `W1=${s.w1_mag}` : ""} {s.w2_mag ? `W2=${s.w2_mag}` : ""}
                              </td>
                              <td className="py-2.5 px-3">—</td>
                              <td className="py-2.5 px-3">{s.separation_arcsec.toFixed(1)}″</td>
                              <td className="py-2.5 px-3">
                                <span className={`px-2 py-0.5 rounded text-[10px] ${s.inside_cutout ? "bg-emerald-400/10 text-emerald-300" : "bg-slate-800 text-slate-400"}`}>
                                  {s.inside_cutout ? "Inside" : "Outside"}
                                </span>
                              </td>
                            </tr>
                          ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </>
          )}

          {/* ========================================================= */}
          {/* PHASE 4C: CANDIDATE RANKING SYSTEM */}
          {/* ========================================================= */}
          {activePage === "Candidate Ranking" && (
            <>
              <Heading
                title="Candidate Ranking & Motion Intelligence"
                subtitle="Phase 4C · Scientific Verification & Ranking"
                description="Rigorous categorization and ranking of candidate moving sources and stationary catalog objects, distinguishing physical proper motion from detector artifacts."
              />

              {/* Scientific Guidelines Notice */}
              <div className="rounded-xl border border-amber-400/30 bg-amber-400/5 p-5 mb-6">
                <h3 className="font-semibold text-amber-300">NASA Science Scientific Integrity Protocol</h3>
                <p className="mt-2 text-xs leading-6 text-slate-300">
                  Candidate ranking is withheld unless independent, quality-controlled measurements support it. Fixed residual scores, projected WCS shifts, and unverified matches are not evidence of source motion. The term &ldquo;Discovery&rdquo; is never asserted without multi-epoch physical verification.
                </p>
              </div>

              {rankingLoading && <p className="text-slate-400">Analyzing candidates and quality flags...</p>}
              {rankingError && <p className="text-sm text-red-300">{rankingError}</p>}

              {rankingData && (
                <>
                  {/* Category Breakdown */}
                  <div className="grid gap-4 sm:grid-cols-4 mb-8">
                    <StatCard label="Total Candidates" value={rankingData.total_candidates} />
                    <StatCard
                      label="Likely Moving Sources"
                      value={rankingData.classification_counts["Likely moving source"] || 0}
                    />
                    <StatCard
                      label="Possible Motion Candidates"
                      value={rankingData.classification_counts["Possible motion"] || 0}
                    />
                    <StatCard
                      label="Known Matched Objects"
                      value={rankingData.classification_counts["Known matched object"] || 0}
                    />
                  </div>

                  {/* Candidates List */}
                  <div className="space-y-6">
                    {rankingData.candidates.map((cand) => (
                      <div
                        key={cand.id}
                        className={`rounded-2xl border p-6 transition ${
                          cand.classification === "Likely moving source"
                            ? "border-emerald-500/40 bg-[#0d1e2e]"
                            : cand.classification === "Possible motion"
                            ? "border-amber-500/40 bg-[#161c28]"
                            : cand.classification === "Known matched object"
                            ? "border-indigo-500/40 bg-[#12172a]"
                            : "border-slate-700/40 bg-[#0d111a]"
                        }`}
                      >
                        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 pb-4">
                          <div className="flex items-center gap-3">
                            <span className="rounded-lg bg-white/10 px-2.5 py-1 text-xs font-mono font-bold text-white">
                              {cand.id}
                            </span>
                            <h3 className="text-base font-bold text-white">{cand.name}</h3>
                          </div>

                          <div className="flex items-center gap-2">
                            <span
                              className={`rounded-full px-3 py-1 text-xs font-semibold ${
                                cand.classification === "Likely moving source"
                                  ? "bg-emerald-400/20 text-emerald-300 border border-emerald-400/40"
                                  : cand.classification === "Possible motion"
                                  ? "bg-amber-400/20 text-amber-300 border border-amber-400/40"
                                  : cand.classification === "Known matched object"
                                  ? "bg-indigo-400/20 text-indigo-300 border border-indigo-400/40"
                                  : "bg-slate-800 text-slate-400"
                              }`}
                            >
                              {cand.classification}
                            </span>
                            <span className="font-mono text-xs text-slate-400">
                              Score: <strong className="text-white">{cand.rank_score}</strong>/100
                            </span>
                          </div>
                        </div>

                        {/* Candidate Data Grid */}
                        <div className="mt-4 grid gap-4 md:grid-cols-3 font-mono text-xs">
                          {/* Astrometry & Motion */}
                          <div className="rounded-xl bg-black/40 p-4 space-y-1.5 border border-white/5">
                            <p className="text-[11px] font-bold text-cyan-300 uppercase tracking-wider mb-2">
                              Astrometry & Motion
                            </p>
                            <div className="flex justify-between text-slate-400">
                              <span>Epoch 1 Pixel:</span>
                              <span className="text-white">({cand.position.epoch_1.pixel_x}, {cand.position.epoch_1.pixel_y})</span>
                            </div>
                            <div className="flex justify-between text-slate-400">
                              <span>Epoch 2 Pixel:</span>
                              <span className="text-white">({cand.position.epoch_2.pixel_x}, {cand.position.epoch_2.pixel_y})</span>
                            </div>
                            <div className="flex justify-between text-slate-400">
                              <span>Total Pixel Shift:</span>
                              <span className="text-amber-300 font-bold">{cand.motion.shift_pixels} px</span>
                            </div>
                            <div className="flex justify-between text-slate-400">
                              <span>Annual Motion Rate:</span>
                              <span className="text-emerald-400 font-bold">{cand.motion.annual_rate_arcsec_yr}″ / yr</span>
                            </div>
                          </div>

                          {/* Photometry & SNR */}
                          <div className="rounded-xl bg-black/40 p-4 space-y-1.5 border border-white/5">
                            <p className="text-[11px] font-bold text-indigo-300 uppercase tracking-wider mb-2">
                              Photometry & SNR
                            </p>
                            <div className="flex justify-between text-slate-400">
                              <span>Flux (Epoch 1):</span>
                              <span className="text-white">{cand.photometry.flux_epoch_1_mjy_sr} MJy/sr</span>
                            </div>
                            <div className="flex justify-between text-slate-400">
                              <span>Flux (Epoch 2):</span>
                              <span className="text-white">{cand.photometry.flux_epoch_2_mjy_sr} MJy/sr</span>
                            </div>
                            <div className="flex justify-between text-slate-400">
                              <span>Signal-to-Noise:</span>
                              <span className="text-emerald-300 font-bold">{cand.photometry.signal_to_noise}σ</span>
                            </div>
                            <div className="flex justify-between text-slate-400">
                              <span>Uncertainty:</span>
                              <span className="text-slate-300">±{cand.photometry.uncertainty_pct}%</span>
                            </div>
                          </div>

                          {/* Quality Flags & Catalog */}
                          <div className="rounded-xl bg-black/40 p-4 space-y-1.5 border border-white/5">
                            <p className="text-[11px] font-bold text-amber-300 uppercase tracking-wider mb-2">
                              Catalog & Quality Flags
                            </p>
                            <div className="flex justify-between text-slate-400">
                              <span>Catalog Match:</span>
                              <span className="text-white">{cand.catalog_crossmatch.catalog}</span>
                            </div>
                            <div className="flex justify-between text-slate-400">
                              <span>Quality Status:</span>
                              <span className="text-white font-bold">{cand.quality_flags.status}</span>
                            </div>
                            <div className="text-[11px] text-slate-400 pt-1 border-t border-white/5">
                              <span>Flag detail: </span>
                              <span className="text-slate-300">{cand.quality_flags.interpretation}</span>
                            </div>
                          </div>
                        </div>

                        {/* Evidence Subplot Cutout Strip */}
                        <div className="mt-4 pt-3 border-t border-white/10">
                          <p className="text-xs font-mono text-slate-400 mb-2">
                            Evidence Cutout Strip [Epoch 1 Zoom | Epoch 2 Zoom | Difference Map Zoom]:
                          </p>
                          <div className="flex justify-center overflow-hidden rounded-xl bg-black p-2 border border-white/10">
                            {/* eslint-disable-next-line @next/next/no-img-element */}
                            <img
                              src={`${apiUrl}/api/candidates/${cand.id}/evidence`}
                              alt={`Evidence for ${cand.id}`}
                              className="max-h-40 w-auto object-contain"
                            />
                          </div>
                        </div>

                        <p className="mt-3 text-xs leading-relaxed text-slate-400 italic">
                          Scientific Justification: {cand.scientific_justification}
                        </p>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </>
          )}

          {activePage === "Validation Lab" && (
            <div className="space-y-6">
              <Heading title="Scientific Validation Lab" subtitle="Phase 5 · Five targets" description="Archive metadata, catalog predictions, and measurements are identified separately. A successful API response does not imply a scientific validation." />
              <div className="rounded-xl border border-amber-400/30 bg-amber-400/5 p-4 text-sm text-slate-300">Predicted positions are not detections. Low-SNR centroids are excluded from measured motion. Incompatible photometry is never compared.</div>
              <div className="flex flex-wrap items-center gap-3">
                <label className="flex items-center gap-2 text-xs text-slate-300"><input type="checkbox" checked={validationLive} onChange={(event) => setValidationLive(event.target.checked)} />Query IRSA live</label>
                <button onClick={runValidationLab} className="rounded-lg bg-cyan-400 px-4 py-2 font-semibold text-slate-950">{validationLoading ? "Running…" : "Run five-target validation"}</button>
              </div>
              {validationError && <p className="text-sm text-red-300">{validationError}</p>}
              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">{validationTargets.map((target) => {
                const report = validationReports[target.id];
                return <button key={target.id} onClick={() => setValidationSelected(target.id)} className={`rounded-xl border p-4 text-left ${validationSelected === target.id ? "border-cyan-400 bg-cyan-400/10" : "border-white/10 bg-[#111c2e]"}`}>
                  <strong className="text-sm text-white">{target.name}</strong><p className="mt-2 text-xs text-slate-400">{report?.validation_status || target.science_case}</p>
                </button>;
              })}</div>
              {(() => {
                const report = validationReports[validationSelected];
                const target = report?.target || validationTargets.find((item) => item.id === validationSelected);
                if (!target) return <p className="text-sm text-slate-400">Loading five-target registry…</p>;
                const ref = target.reference;
                return <div className="space-y-5">
                  <section className="rounded-xl border border-white/10 bg-[#111c2e] p-5">
                    <h3 className="text-xl font-semibold">{target.name}</h3><p className="mt-1 text-sm text-slate-400">{target.object_type} · {target.science_goal}</p>
                    <p className="mt-3 text-xs leading-6 text-slate-400">{ref.catalog} · {ref.frame} · {ref.epoch_label} · RA {ref.ra_deg.toFixed(6)}°, Dec {ref.dec_deg.toFixed(6)}° · PM {ref.pm_ra_cosdec_mas_yr ?? "unknown"}, {ref.pm_dec_mas_yr ?? "unknown"} mas/yr · parallax {ref.parallax_mas ?? "unknown"} mas</p>
                    <p className="text-xs text-slate-500">{ref.provenance} · <a className="text-cyan-300 underline" href={ref.reference_url} target="_blank" rel="noreferrer">Reference source</a></p>
                  </section>
                  {report && <>
                    <section className="rounded-xl border border-white/10 bg-[#111c2e] p-5">
                      <h3 className="font-semibold">{report.validation_status}</h3><p className="mt-2 text-sm text-slate-300">Confirmed detection: no</p>
                      <p className="mt-2 text-xs text-slate-400">Archive: {report.archive_discovery.archive_status} · {report.archive_discovery.record_count ?? 0} rows · {report.archive_discovery.distinct_dates ?? 0} dates · {report.archive_discovery.bands?.join(", ") || "bands unknown"}</p>
                      {report.archive_discovery.live_query_error && <p className="mt-2 text-xs text-amber-200">Archive query error: {report.archive_discovery.live_query_error}</p>}
                      <p className="mt-2 text-xs text-slate-400">Image comparison: {report.image_comparison.status}. {report.image_comparison.note || report.image_comparison.reason || "No compatible multi-epoch images."}</p>
                      <p className="mt-2 text-xs text-slate-400">Photometry: {report.photometric_test.result}. {report.photometric_test.interpretation}</p>
                      <p className="mt-2 text-xs text-amber-200">FITS quality: {report.data_quality.map((q) => `${q.filename}: ${q.accepted ? "accepted" : q.rejection_reasons.join("; ")}, L1=${q.l1_quality_flag ?? "unknown"}, L2=${q.l2_quality_flag ?? "unknown"}, flagged=${q.flagged_pixel_fraction == null ? "unknown" : `${(q.flagged_pixel_fraction * 100).toFixed(1)}%`}${q.warnings.length ? `; ${q.warnings.join("; ")}` : ""}`).join(" · ") || "No local FITS quality assessment"}</p>
                    </section>
                    <div className="grid gap-4 lg:grid-cols-2">
                      <figure className="rounded-xl border border-white/10 bg-black p-3"><img className="w-full" src={`${apiUrl}/api/validation/astrometry/${validationSelected}/plot`} alt="Predicted and measured astrometry" /><figcaption className="text-xs text-slate-400">Catalog predictions and accepted measured centroids</figcaption></figure>
                      <figure className="rounded-xl border border-white/10 bg-black p-3"><img className="w-full" src={`${apiUrl}/api/validation/photometry/${validationSelected}/plot`} alt="Photometry with uncertainty bars" /><figcaption className="text-xs text-slate-400">Aperture flux with 1σ uncertainties</figcaption></figure>
                      {report.image_comparison.status === "wcs_aligned" && <figure className="rounded-xl border border-white/10 bg-black p-3"><img className="w-full" src={`${apiUrl}/api/validation/difference/${validationSelected}`} alt="WCS-aligned exploratory image difference" /><figcaption className="text-xs text-slate-400">WCS-aligned exploratory difference; PSF matching and variance propagation are not applied</figcaption></figure>}
                    </div>
                    <div className="overflow-x-auto rounded-xl border border-white/10"><table className="w-full text-left text-xs"><thead className="text-slate-400"><tr><th className="p-3">Observation / date</th><th className="p-3">Detector / band</th><th className="p-3">SNR / flags</th><th className="p-3">Predicted / measured position</th><th className="p-3">Flux ± error</th></tr></thead><tbody>{report.epochs.map((epoch) => <tr key={epoch.observation} className="border-t border-white/5"><td className="p-3">{epoch.observation_id || epoch.observation}<br />{epoch.date || "date unknown"}</td><td className="p-3">{epoch.detector ?? "?"} / {epoch.band || "unknown"}</td><td className="p-3">{epoch.photometry?.snr?.toFixed(2) ?? "—"}<br />{epoch.photometry?.quality_flags?.map((f) => `${f.value}:${f.name}`).join(", ") || "none"}<br />{epoch.photometry?.contamination_warning || ""}</td><td className="p-3">{epoch.predicted ? `${epoch.predicted.ra_deg.toFixed(5)}, ${epoch.predicted.dec_deg.toFixed(5)}` : "—"}<br />{epoch.measured_centroid ? `${epoch.measured_centroid.ra_deg.toFixed(5)}, ${epoch.measured_centroid.dec_deg.toFixed(5)} ± ${epoch.measured_centroid.uncertainty_arcsec?.toFixed(2) ?? "?"}″` : "no accepted centroid"}<br />{epoch.source_detection_confidence?.warning || ""}</td><td className="p-3">{epoch.photometry?.flux_jy?.toExponential(3) ?? "—"} ± {epoch.photometry?.flux_error_jy?.toExponential(2) ?? "—"} Jy</td></tr>)}</tbody></table></div>
                    <div className="grid gap-4 sm:grid-cols-2">{report.local_fits.filter((item) => item.exists).map((item) => <figure key={item.observation_id} className="rounded-xl border border-white/10 bg-black p-3"><img className="w-full" src={`${apiUrl}/api/validation/image/${validationSelected}/${item.observation_id}`} alt={`${target.name} ${item.observation_id}`} /><figcaption className="text-xs text-slate-400">{item.observation_id} · cyan marker is predicted position</figcaption></figure>)}</div>
                    <ul className="list-disc space-y-1 pl-5 text-xs text-amber-200">{report.limitations.map((limitation) => <li key={limitation}>{limitation}</li>)}</ul>
                  </>}
                </div>;
              })()}
            </div>
          )}

          <footer className="mt-12 border-t border-white/10 pt-6 text-center text-xs text-slate-600">
            SPHEREx Explorer · NASA Space Apps Challenge 2026
            <br />
            Scientific visualization and analysis project
          </footer>
        </section>
      </div>
    </main>
  );
}
