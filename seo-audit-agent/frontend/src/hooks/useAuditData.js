import { useState, useEffect } from 'react';

const DATA_BASE = import.meta.env.VITE_DATA_BASE_URL || './data';

export function useAuditData(filename) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!filename) { setLoading(false); return; }
    setLoading(true);
    setError(null);

    fetch(`${DATA_BASE}/${filename}`)
      .then(res => {
        if (!res.ok) throw new Error(`Failed to load ${filename}: ${res.status}`);
        return res.json();
      })
      .then(d => { setData(d); setLoading(false); })
      .catch(err => { setError(err.message); setLoading(false); });
  }, [filename]);

  return { data, loading, error };
}

export function useManifest() {
  const [manifest, setManifest] = useState(null);
  const [available, setAvailable] = useState({});

  useEffect(() => {
    fetch(`${DATA_BASE}/manifest.json`)
      .then(r => r.ok ? r.json() : null)
      .then(d => {
        setManifest(d);
        const files = d?.files || [];
        setAvailable({
          keywords: files.includes('keywords.json'),
          competitors: files.includes('competitors.json'),
          topPages: files.includes('top-pages.json'),
          gapAnalysis: files.includes('gap-analysis.json'),
          backlinks: files.includes('backlinks.json'),
          interlinking: files.includes('interlinking.json'),
          actionPlan: files.includes('action-plan.json'),
        });
      })
      .catch(() => setManifest(null));
  }, []);

  return { manifest, available };
}
