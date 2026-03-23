import React, { useState } from 'react';
import { useAuditData, useManifest } from './hooks/useAuditData';
import { StatCard, MiniBar, DifficultyBadge, OpportunityBadge, Chip, LoadingState, EmptyState, FilterBar, DataTable, CheckBox } from './components/Shared';
import './App.css';

// ═══════════════════════════════════════════════════════
// NAV CONFIG
// ═══════════════════════════════════════════════════════

const PAGES = [
  { id: 'overview', label: 'Overview', icon: '📊' },
  { id: 'keywords', label: 'Keywords', icon: '🔑', file: 'keywords.json' },
  { id: 'competitors', label: 'Competitors', icon: '🏢', file: 'competitors.json' },
  { id: 'pages', label: 'Top Pages', icon: '📄', file: 'top-pages.json' },
  { id: 'gaps', label: 'Gap Analysis', icon: '🎯', file: 'gap-analysis.json' },
  { id: 'backlinks', label: 'Backlinks', icon: '🔗', file: 'backlinks.json' },
  { id: 'interlinking', label: 'Interlinking', icon: '🕸️', file: 'interlinking.json' },
  { id: 'actionplan', label: 'Action Plan', icon: '🚀', file: 'action-plan.json' },
];

// ═══════════════════════════════════════════════════════
// OVERVIEW PAGE
// ═══════════════════════════════════════════════════════

function OverviewPage() {
  const { data: kw } = useAuditData('keywords.json');
  const { data: comp } = useAuditData('competitors.json');
  const { data: gaps } = useAuditData('gap-analysis.json');
  const { data: bl } = useAuditData('backlinks.json');
  const { data: il } = useAuditData('interlinking.json');
  const { data: plan } = useAuditData('action-plan.json');

  return (
    <div>
      <div className="page-header">
        <h2>SEO Audit Overview</h2>
        <p>Last updated: {plan?.generated_at ? new Date(plan.generated_at).toLocaleString() : 'N/A'}</p>
      </div>

      {plan && (
        <div className="card" style={{ borderColor: 'var(--accent)', borderWidth: 2, marginBottom: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
            <div style={{ width: 80, height: 80, borderRadius: '50%', background: `conic-gradient(var(--accent) ${plan.score * 3.6}deg, var(--surface-3) 0deg)`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              <div style={{ width: 60, height: 60, borderRadius: '50%', background: 'var(--surface)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 900, fontSize: 22, fontFamily: 'Fraunces, serif' }}>{plan.score}</div>
            </div>
            <div>
              <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 4 }}>SEO Health Score</div>
              <div style={{ color: 'var(--text-2)', fontSize: 13, lineHeight: 1.6 }}>{plan.summary}</div>
            </div>
          </div>
        </div>
      )}

      <div className="grid-4" style={{ marginBottom: 24 }}>
        <StatCard value={kw?.total?.toLocaleString() || '—'} label="Keywords Tracked" accent="var(--accent)" />
        <StatCard value={comp?.total || '—'} label="Competitors Found" accent="var(--cyan)" />
        <StatCard value={gaps?.total_keyword_gaps?.toLocaleString() || '—'} label="Keyword Gaps" accent="var(--amber)" />
        <StatCard value={bl?.da30_plus_domains?.toLocaleString() || '—'} label="DA 30+ Link Gaps" accent="var(--red)" />
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-title">🔑 Keyword Groups</div>
          {kw?.groups && Object.entries(kw.groups).slice(0, 8).map(([group, count]) => (
            <div key={group} style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 10 }}>
              <span style={{ fontSize: 13, color: 'var(--text-2)', width: 160, flexShrink: 0 }}>{group}</span>
              <MiniBar value={count} max={Math.max(...Object.values(kw.groups))} color="var(--accent)" />
              <span className="mono" style={{ fontSize: 12, color: 'var(--text-3)', width: 50, textAlign: 'right' }}>{count}</span>
            </div>
          ))}
        </div>
        <div className="card">
          <div className="card-title">🚀 Quick Wins</div>
          {plan?.quick_wins?.slice(0, 5).map((item, i) => (
            <div key={i} style={{ padding: '10px 0', borderBottom: '1px solid var(--border)' }}>
              <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 4 }}>{item.title}</div>
              <div style={{ display: 'flex', gap: 8 }}>
                <span className={`action-priority priority-${item.priority?.toLowerCase()}`}>{item.priority}</span>
                <span style={{ fontSize: 11, color: 'var(--text-3)' }}>{item.timeline}</span>
              </div>
            </div>
          ))}
          {!plan?.quick_wins && <EmptyState icon="⏳" title="No data yet" description="Run the audit to see quick wins" />}
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════
// KEYWORDS PAGE
// ═══════════════════════════════════════════════════════

function KeywordsPage() {
  const { data, loading, error } = useAuditData('keywords.json');
  const [search, setSearch] = useState('');
  const [groupFilter, setGroupFilter] = useState('All');

  if (loading) return <LoadingState />;
  if (error || !data) return <EmptyState icon="🔑" title="No keyword data" description="Run the keyword research agent first" />;

  const keywords = data.keywords || [];
  const filtered = keywords.filter(kw => {
    if (groupFilter !== 'All' && kw.group !== groupFilter) return false;
    if (search && !kw.keyword.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });
  const maxVol = Math.max(...keywords.map(k => k.volume || 0), 1);

  return (
    <div>
      <div className="page-header">
        <h2>Keyword Research</h2>
        <p>{data.total?.toLocaleString()} keywords across {Object.keys(data.groups || {}).length} groups</p>
      </div>
      <div className="grid-4" style={{ marginBottom: 20 }}>
        <StatCard value={data.total?.toLocaleString()} label="Total Keywords" />
        <StatCard value={Object.keys(data.groups || {}).length} label="Groups" />
        <StatCard value={`${(keywords.reduce((a, k) => a + (k.volume || 0), 0) / 1000).toFixed(0)}K`} label="Total Volume" />
        <StatCard value={`$${(keywords.reduce((a, k) => a + (k.cpc || 0), 0) / Math.max(keywords.length, 1)).toFixed(2)}`} label="Avg CPC" />
      </div>

      {data.groups && (
        <div className="card" style={{ marginBottom: 16 }}>
          <div className="card-title">📁 Keyword Groups</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {Object.entries(data.groups).map(([g, c]) => (
              <Chip key={g} active={groupFilter === g} onClick={() => setGroupFilter(groupFilter === g ? 'All' : g)}>{g} ({c})</Chip>
            ))}
          </div>
        </div>
      )}

      <FilterBar count={filtered.length}>
        <input className="form-input" placeholder="Search keywords..." value={search} onChange={e => setSearch(e.target.value)} />
        <select className="form-input" value={groupFilter} onChange={e => setGroupFilter(e.target.value)}>
          <option value="All">All Groups</option>
          {Object.keys(data.groups || {}).map(g => <option key={g}>{g}</option>)}
        </select>
      </FilterBar>

      <DataTable>
        <thead><tr><th>#</th><th>Keyword</th><th>Volume</th><th style={{ width: 120 }}>Vol</th><th>KD</th><th>CPC</th><th>Pos</th><th>Group</th><th>Opp</th></tr></thead>
        <tbody>
          {filtered.slice(0, 300).map((kw, i) => (
            <tr key={i}>
              <td className="mono">{i + 1}</td>
              <td style={{ fontWeight: 600, color: 'var(--text)' }}>{kw.keyword}</td>
              <td className="mono">{(kw.volume || 0).toLocaleString()}</td>
              <td><MiniBar value={kw.volume || 0} max={maxVol} /></td>
              <td><DifficultyBadge value={kw.difficulty || 0} /></td>
              <td className="mono">${kw.cpc || 0}</td>
              <td className="mono">{kw.position || '—'}</td>
              <td><Chip>{kw.group}</Chip></td>
              <td><OpportunityBadge value={kw.opportunity || 'Medium'} /></td>
            </tr>
          ))}
        </tbody>
      </DataTable>
    </div>
  );
}

// ═══════════════════════════════════════════════════════
// COMPETITORS PAGE
// ═══════════════════════════════════════════════════════

function CompetitorsPage() {
  const { data, loading, error } = useAuditData('competitors.json');

  if (loading) return <LoadingState />;
  if (error || !data) return <EmptyState icon="🏢" title="No competitor data" description="Run the competitor discovery agent first" />;

  const competitors = data.competitors || [];

  return (
    <div>
      <div className="page-header">
        <h2>Competitor Discovery</h2>
        <p>{data.total} competitors identified — verify and select for deep analysis</p>
      </div>
      <div className="grid-3" style={{ marginBottom: 20 }}>
        <StatCard value={data.total} label="Found" />
        <StatCard value={competitors.filter(c => c.verified).length} label="Verified" />
        <StatCard value={competitors.filter(c => c.selected).length} label="Selected" />
      </div>
      <div className="card">
        <div className="card-title">🏢 Competitor Websites</div>
        <DataTable>
          <thead><tr><th>Status</th><th>Domain</th><th>DA</th><th>Est. Traffic</th><th>Keywords</th><th>Overlap</th><th style={{ width: 120 }}>Overlap</th></tr></thead>
          <tbody>
            {competitors.map((c, i) => (
              <tr key={i}>
                <td>
                  <div style={{ display: 'flex', gap: 6 }}>
                    {c.verified && <span style={{ color: 'var(--green)', fontSize: 12, fontWeight: 700 }}>✓ Verified</span>}
                    {c.selected && <span style={{ color: 'var(--accent-2)', fontSize: 12, fontWeight: 700 }}>● Selected</span>}
                    {!c.verified && !c.selected && <span style={{ color: 'var(--text-3)', fontSize: 12 }}>Pending</span>}
                  </div>
                </td>
                <td style={{ fontWeight: 600, color: 'var(--text)' }}>{c.domain}</td>
                <td className="mono">{c.da}</td>
                <td className="mono">{c.estimated_traffic}</td>
                <td className="mono">{(c.total_keywords || 0).toLocaleString()}</td>
                <td className="mono">{c.overlap_pct}%</td>
                <td><MiniBar value={c.overlap_pct} max={100} color="var(--cyan)" /></td>
              </tr>
            ))}
          </tbody>
        </DataTable>
        <div style={{ marginTop: 12, fontSize: 12, color: 'var(--text-3)' }}>
          💡 To mark competitors as verified/selected, edit <code>competitors.json</code> in the audit data or re-run the agent with updated <code>known_competitors</code> in config.
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════
// TOP PAGES PAGE
// ═══════════════════════════════════════════════════════

function TopPagesPage() {
  const { data, loading, error } = useAuditData('top-pages.json');
  const [compFilter, setCompFilter] = useState('All');
  const [typeFilter, setTypeFilter] = useState('All');
  const [search, setSearch] = useState('');

  if (loading) return <LoadingState />;
  if (error || !data) return <EmptyState icon="📄" title="No pages data" description="Run the top pages agent first" />;

  const pages = data.pages || [];
  const filtered = pages.filter(p => {
    if (compFilter !== 'All' && p.competitor !== compFilter) return false;
    if (typeFilter !== 'All' && p.page_type !== typeFilter) return false;
    if (search && !p.url.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });
  const maxTraffic = Math.max(...pages.map(p => p.estimated_traffic || 0), 1);
  const competitors = [...new Set(pages.map(p => p.competitor))];

  return (
    <div>
      <div className="page-header">
        <h2>Competitor Top Pages</h2>
        <p>{data.total?.toLocaleString()} pages analyzed across {competitors.length} competitors</p>
      </div>

      {data.page_type_distribution && (
        <div className="card" style={{ marginBottom: 16 }}>
          <div className="card-title">📊 Page Type Distribution</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {Object.entries(data.page_type_distribution).map(([type, count]) => (
              <Chip key={type} active={typeFilter === type} onClick={() => setTypeFilter(typeFilter === type ? 'All' : type)}>{type} ({count})</Chip>
            ))}
          </div>
        </div>
      )}

      <FilterBar count={filtered.length}>
        <input className="form-input" placeholder="Search pages..." value={search} onChange={e => setSearch(e.target.value)} />
        <select className="form-input" value={compFilter} onChange={e => setCompFilter(e.target.value)}>
          <option value="All">All Competitors</option>
          {competitors.map(c => <option key={c}>{c}</option>)}
        </select>
      </FilterBar>

      <DataTable>
        <thead><tr><th>#</th><th>Competitor</th><th>URL</th><th>Traffic</th><th style={{ width: 100 }}>Traffic</th><th>Keywords</th><th>Type</th></tr></thead>
        <tbody>
          {filtered.slice(0, 200).map((p, i) => (
            <tr key={i}>
              <td className="mono">{i + 1}</td>
              <td className="mono" style={{ fontSize: 11 }}>{p.competitor}</td>
              <td style={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: 12 }}>{p.url}</td>
              <td className="mono">{(p.estimated_traffic || 0).toLocaleString()}</td>
              <td><MiniBar value={p.estimated_traffic || 0} max={maxTraffic} color="var(--green)" /></td>
              <td className="mono">{(p.keyword_count || 0).toLocaleString()}</td>
              <td><Chip>{p.page_type}</Chip></td>
            </tr>
          ))}
        </tbody>
      </DataTable>
    </div>
  );
}

// ═══════════════════════════════════════════════════════
// GAP ANALYSIS PAGE
// ═══════════════════════════════════════════════════════

function GapAnalysisPage() {
  const { data, loading, error } = useAuditData('gap-analysis.json');
  const [tab, setTab] = useState('keyword');

  if (loading) return <LoadingState />;
  if (error || !data) return <EmptyState icon="🎯" title="No gap data" description="Run the gap analysis agent first" />;

  const items = tab === 'keyword' ? (data.keyword_gaps || []) : (data.content_gaps || []);

  return (
    <div>
      <div className="page-header">
        <h2>Gap Analysis</h2>
        <p>{data.total_keyword_gaps?.toLocaleString()} keyword gaps, {data.total_content_gaps} content gaps ({data.missing_keywords?.toLocaleString()} completely missing)</p>
      </div>

      <div className="grid-3" style={{ marginBottom: 20 }}>
        <StatCard value={data.total_keyword_gaps?.toLocaleString()} label="Keyword Gaps" accent="var(--amber)" />
        <StatCard value={data.missing_keywords?.toLocaleString()} label="Missing Keywords" accent="var(--red)" />
        <StatCard value={data.total_content_gaps} label="Content Gaps" accent="var(--cyan)" />
      </div>

      <div className="tab-bar">
        <button className={`tab-item ${tab === 'keyword' ? 'active' : ''}`} onClick={() => setTab('keyword')}>🔑 Keyword Gap</button>
        <button className={`tab-item ${tab === 'content' ? 'active' : ''}`} onClick={() => setTab('content')}>📄 Content Gap</button>
      </div>

      <DataTable>
        <thead>
          <tr>
            <th>#</th>
            <th>{tab === 'keyword' ? 'Keyword' : 'Page Type'}</th>
            <th>Your Pos</th>
            <th>Volume</th>
            <th>{tab === 'keyword' ? 'KD' : 'Competitors'}</th>
            <th>Opportunity</th>
          </tr>
        </thead>
        <tbody>
          {items.slice(0, 200).map((item, i) => (
            <tr key={i}>
              <td className="mono">{i + 1}</td>
              <td style={{ fontWeight: 600, color: 'var(--text)' }}>{item.term}</td>
              <td className="mono">{item.your_position || '—'}</td>
              <td className="mono">{(item.volume || 0).toLocaleString()}</td>
              <td>
                {tab === 'keyword'
                  ? <DifficultyBadge value={item.difficulty || 0} />
                  : <span className="mono">{item.competitors_count || Object.keys(item.competitor_positions || {}).length}</span>
                }
              </td>
              <td><OpportunityBadge value={item.opportunity} /></td>
            </tr>
          ))}
        </tbody>
      </DataTable>
    </div>
  );
}

// ═══════════════════════════════════════════════════════
// BACKLINKS PAGE
// ═══════════════════════════════════════════════════════

function BacklinksPage() {
  const { data, loading, error } = useAuditData('backlinks.json');
  const [tab, setTab] = useState('all');
  const [typeFilter, setTypeFilter] = useState('All');

  if (loading) return <LoadingState />;
  if (error || !data) return <EmptyState icon="🔗" title="No backlink data" description="Run the backlink agent first" />;

  const allDomains = data.referring_domain_gap || [];
  const da30 = data.da30_plus_gap || allDomains.filter(d => d.is_da30_plus);
  const domains = tab === 'da30' ? da30 : allDomains;
  const filtered = typeFilter === 'All' ? domains : domains.filter(d => d.domain_type === typeFilter);
  const types = [...new Set(allDomains.map(d => d.domain_type))];

  return (
    <div>
      <div className="page-header">
        <h2>Backlink & Referring Domain Gap</h2>
        <p>{data.total_referring_domains} domain gaps found, {data.da30_plus_domains} with DA 30+</p>
      </div>

      <div className="grid-4" style={{ marginBottom: 20 }}>
        <StatCard value={data.your_referring_domains?.toLocaleString() || '—'} label="Your Ref Domains" />
        <StatCard value={data.total_referring_domains?.toLocaleString()} label="Domain Gaps" accent="var(--amber)" />
        <StatCard value={data.da30_plus_domains?.toLocaleString()} label="DA 30+ Gaps" accent="var(--red)" />
        <StatCard value={Object.keys(data.backlink_gap_summary || {}).length} label="Competitors Analyzed" />
      </div>

      {data.backlink_gap_summary && (
        <div className="card" style={{ marginBottom: 16 }}>
          <div className="card-title">📊 Gap by Competitor</div>
          {Object.entries(data.backlink_gap_summary).map(([comp, count]) => (
            <div key={comp} style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
              <span style={{ fontSize: 13, color: 'var(--text-2)', width: 180, flexShrink: 0 }}>{comp}</span>
              <MiniBar value={count} max={Math.max(...Object.values(data.backlink_gap_summary))} color="var(--red)" />
              <span className="mono" style={{ fontSize: 12, color: 'var(--text-3)', width: 50, textAlign: 'right' }}>{count}</span>
            </div>
          ))}
        </div>
      )}

      <div className="tab-bar" style={{ marginBottom: 12 }}>
        <button className={`tab-item ${tab === 'all' ? 'active' : ''}`} onClick={() => setTab('all')}>All Domains ({allDomains.length})</button>
        <button className={`tab-item ${tab === 'da30' ? 'active' : ''}`} onClick={() => setTab('da30')}>DA 30+ ({da30.length})</button>
      </div>

      <FilterBar count={filtered.length}>
        <select className="form-input" value={typeFilter} onChange={e => setTypeFilter(e.target.value)}>
          <option value="All">All Types</option>
          {types.map(t => <option key={t}>{t}</option>)}
        </select>
      </FilterBar>

      <DataTable>
        <thead><tr><th>#</th><th>Domain</th><th>DA</th><th>Type</th><th>Competitors</th><th>Opportunity</th></tr></thead>
        <tbody>
          {filtered.slice(0, 200).map((d, i) => (
            <tr key={i}>
              <td className="mono">{i + 1}</td>
              <td style={{ fontWeight: 600, color: 'var(--text)' }}>{d.domain}</td>
              <td><DifficultyBadge value={d.da} /></td>
              <td><Chip>{d.domain_type}</Chip></td>
              <td className="mono">{d.competitors_linking || Object.values(d.competitor_presence || {}).filter(Boolean).length}</td>
              <td><OpportunityBadge value={d.opportunity} /></td>
            </tr>
          ))}
        </tbody>
      </DataTable>
    </div>
  );
}

// ═══════════════════════════════════════════════════════
// INTERLINKING PAGE
// ═══════════════════════════════════════════════════════

function InterlinkingPage() {
  const { data, loading, error } = useAuditData('interlinking.json');
  const [tab, setTab] = useState('suggestions');

  if (loading) return <LoadingState />;
  if (error || !data) return <EmptyState icon="🕸️" title="No interlinking data" description="Run the interlinking agent first" />;

  return (
    <div>
      <div className="page-header">
        <h2>Interlinking Analysis</h2>
        <p>{data.total_suggestions} link suggestions, {data.orphan_pages?.length || 0} orphan pages</p>
      </div>

      <div className="grid-3" style={{ marginBottom: 20 }}>
        <StatCard value={data.total_suggestions} label="Link Suggestions" />
        <StatCard value={data.orphan_pages?.length || 0} label="Orphan Pages" accent="var(--red)" />
        <StatCard value={data.hub_pages?.length || 0} label="Hub Pages" accent="var(--green)" />
      </div>

      <div className="tab-bar">
        <button className={`tab-item ${tab === 'suggestions' ? 'active' : ''}`} onClick={() => setTab('suggestions')}>Suggestions</button>
        <button className={`tab-item ${tab === 'orphans' ? 'active' : ''}`} onClick={() => setTab('orphans')}>Orphan Pages</button>
        <button className={`tab-item ${tab === 'hubs' ? 'active' : ''}`} onClick={() => setTab('hubs')}>Hub Pages</button>
      </div>

      {tab === 'suggestions' && (
        <DataTable>
          <thead><tr><th>#</th><th>From (Source)</th><th>To (Target)</th><th>Anchor Text</th><th>Priority</th></tr></thead>
          <tbody>
            {(data.suggestions || []).slice(0, 200).map((s, i) => (
              <tr key={i}>
                <td className="mono">{i + 1}</td>
                <td style={{ fontSize: 12, maxWidth: 250, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{s.source_url}</td>
                <td style={{ fontSize: 12, maxWidth: 250, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{s.target_url}</td>
                <td style={{ fontWeight: 600, color: 'var(--accent-2)' }}>{s.anchor_text}</td>
                <td><OpportunityBadge value={s.priority} /></td>
              </tr>
            ))}
          </tbody>
        </DataTable>
      )}

      {tab === 'orphans' && (
        <DataTable>
          <thead><tr><th>#</th><th>URL</th></tr></thead>
          <tbody>
            {(data.orphan_pages || []).map((url, i) => (
              <tr key={i}><td className="mono">{i + 1}</td><td style={{ fontSize: 12 }}>{url}</td></tr>
            ))}
          </tbody>
        </DataTable>
      )}

      {tab === 'hubs' && (
        <DataTable>
          <thead><tr><th>#</th><th>URL</th><th>Keywords</th><th>Top Keyword</th></tr></thead>
          <tbody>
            {(data.hub_pages || []).map((h, i) => (
              <tr key={i}>
                <td className="mono">{i + 1}</td>
                <td style={{ fontSize: 12 }}>{h.url}</td>
                <td className="mono">{h.keyword_count}</td>
                <td>{h.top_keyword}</td>
              </tr>
            ))}
          </tbody>
        </DataTable>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════
// ACTION PLAN PAGE
// ═══════════════════════════════════════════════════════

function ActionPlanPage() {
  const { data, loading, error } = useAuditData('action-plan.json');

  if (loading) return <LoadingState />;
  if (error || !data) return <EmptyState icon="🚀" title="No action plan" description="Run the action plan agent first" />;

  return (
    <div>
      <div className="page-header">
        <h2>SEO Action Plan</h2>
        <p>{data.total_actions} actions prioritized — {data.quick_wins?.length} quick wins</p>
      </div>

      <div className="card" style={{ marginBottom: 24, borderColor: 'var(--accent)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
          <div style={{ width: 80, height: 80, borderRadius: '50%', background: `conic-gradient(${data.score >= 70 ? 'var(--green)' : data.score >= 40 ? 'var(--amber)' : 'var(--red)'} ${data.score * 3.6}deg, var(--surface-3) 0deg)`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            <div style={{ width: 60, height: 60, borderRadius: '50%', background: 'var(--surface)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 900, fontSize: 24, fontFamily: 'Fraunces, serif' }}>{data.score}</div>
          </div>
          <div style={{ color: 'var(--text-2)', fontSize: 14, lineHeight: 1.6 }}>{data.summary}</div>
        </div>
      </div>

      {data.quick_wins?.length > 0 && (
        <div className="card" style={{ marginBottom: 24, borderColor: 'var(--green)40' }}>
          <div className="card-title">⚡ Quick Wins</div>
          {data.quick_wins.map((item, i) => (
            <div key={i} className="action-item">
              <span className="action-priority priority-high">Quick Win</span>
              <div>
                <div style={{ fontWeight: 600, color: 'var(--text)', marginBottom: 2 }}>{item.title}</div>
                <div style={{ fontSize: 12, color: 'var(--text-3)' }}>{item.timeline} · Impact: {item.estimated_impact} · Effort: {item.effort}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {(data.sections || []).map((section, si) => (
        <div key={si} className="action-section" style={{ borderLeftColor: ['var(--accent)', 'var(--red)', 'var(--cyan)', 'var(--amber)'][si % 4] }}>
          <h4>{section.title}</h4>
          <p style={{ fontSize: 12, color: 'var(--text-3)', marginBottom: 12 }}>{section.description}</p>
          {(section.items || []).map((item, i) => (
            <div key={i} className="action-item" style={{ borderBottom: '1px solid var(--border)', paddingBottom: 10 }}>
              <span className={`action-priority priority-${item.priority?.toLowerCase()}`}>{item.priority}</span>
              <div>
                <div style={{ fontWeight: 600, color: 'var(--text)', marginBottom: 4 }}>{item.title}</div>
                <div style={{ fontSize: 12, color: 'var(--text-2)', lineHeight: 1.5 }}>{item.description}</div>
                <div style={{ fontSize: 11, color: 'var(--text-3)', marginTop: 4 }}>
                  {item.timeline} · Impact: {item.estimated_impact} · Effort: {item.effort}
                </div>
              </div>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

// ═══════════════════════════════════════════════════════
// APP SHELL
// ═══════════════════════════════════════════════════════

const PAGE_COMPONENTS = {
  overview: OverviewPage,
  keywords: KeywordsPage,
  competitors: CompetitorsPage,
  pages: TopPagesPage,
  gaps: GapAnalysisPage,
  backlinks: BacklinksPage,
  interlinking: InterlinkingPage,
  actionplan: ActionPlanPage,
};

export default function App() {
  const [activePage, setActivePage] = useState('overview');
  const { manifest, available } = useManifest();

  const ActiveComponent = PAGE_COMPONENTS[activePage] || OverviewPage;

  return (
    <div className="app-shell">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <h1>SEO Audit</h1>
          <p>AI-Powered Analysis</p>
        </div>
        <nav className="sidebar-nav">
          {PAGES.map(page => {
            const hasData = page.id === 'overview' || available[page.id] || available[page.id?.replace('pages', 'topPages').replace('gaps', 'gapAnalysis').replace('actionplan', 'actionPlan')];
            return (
              <div
                key={page.id}
                className={`nav-item ${activePage === page.id ? 'active' : ''} ${hasData ? 'completed' : ''}`}
                onClick={() => setActivePage(page.id)}
              >
                <span className="nav-icon">{page.icon}</span>
                <span>{page.label}</span>
                {hasData && page.id !== 'overview' && <span className="nav-check">✓</span>}
              </div>
            );
          })}
        </nav>
        <div className="progress-container">
          <div style={{ fontSize: 11, color: 'var(--text-3)', marginBottom: 6 }}>
            {manifest?.generated_at ? `Last run: ${new Date(manifest.generated_at).toLocaleDateString()}` : 'No audit data yet'}
          </div>
          <div className="progress-bar-bg">
            <div className="progress-bar-fill" style={{ width: `${Object.values(available).filter(Boolean).length / 7 * 100}%` }} />
          </div>
          <div className="progress-text">{Object.values(available).filter(Boolean).length}/7 stages complete</div>
        </div>
      </aside>

      {/* Main */}
      <main className="main-content">
        <ActiveComponent />
      </main>
    </div>
  );
}
