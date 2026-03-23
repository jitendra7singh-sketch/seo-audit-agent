import React from 'react';

export function StatCard({ value, label, accent }) {
  return (
    <div className="stat-card">
      <div className="stat-value" style={accent ? { background: `linear-gradient(135deg, ${accent}, var(--text))`, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' } : {}}>
        {value}
      </div>
      <div className="stat-label">{label}</div>
    </div>
  );
}

export function MiniBar({ value, max, color = 'var(--accent)' }) {
  const pct = Math.min((value / Math.max(max, 1)) * 100, 100);
  return (
    <div style={{ width: '100%', height: 6, background: 'var(--surface-2)', borderRadius: 3, overflow: 'hidden' }}>
      <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: 3, transition: 'width 0.6s ease' }} />
    </div>
  );
}

export function DifficultyBadge({ value }) {
  const color = value < 30 ? '#22c55e' : value < 60 ? '#f59e0b' : '#ef4444';
  return (
    <span style={{ display: 'inline-block', padding: '2px 10px', borderRadius: 20, fontSize: 11, fontWeight: 700, background: `${color}18`, color, border: `1px solid ${color}40` }}>
      {value}
    </span>
  );
}

export function OpportunityBadge({ value }) {
  const colors = { High: '#22c55e', Medium: '#f59e0b', Low: '#94a3b8' };
  const c = colors[value] || '#94a3b8';
  return (
    <span style={{ display: 'inline-block', padding: '2px 10px', borderRadius: 20, fontSize: 11, fontWeight: 700, background: `${c}18`, color: c, border: `1px solid ${c}40` }}>
      {value}
    </span>
  );
}

export function Chip({ children, active, onClick }) {
  return (
    <button
      className="chip"
      style={active ? { background: 'var(--accent)22', color: 'var(--accent-2)', borderColor: 'var(--accent)', cursor: 'pointer' } : { cursor: 'pointer' }}
      onClick={onClick}
    >
      {children}
    </button>
  );
}

export function LoadingState({ message = 'Loading data...' }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 60, flexDirection: 'column', gap: 16 }}>
      <div style={{ display: 'flex', gap: 6 }}>
        <span className="loading-dot" />
        <span className="loading-dot" />
        <span className="loading-dot" />
      </div>
      <span style={{ color: 'var(--text-3)', fontSize: 13 }}>{message}</span>
    </div>
  );
}

export function EmptyState({ icon = '📭', title, description }) {
  return (
    <div className="card" style={{ textAlign: 'center', padding: 48 }}>
      <div style={{ fontSize: 40, marginBottom: 12 }}>{icon}</div>
      <div style={{ fontWeight: 700, marginBottom: 8 }}>{title}</div>
      <div style={{ color: 'var(--text-3)', fontSize: 13, maxWidth: 400, margin: '0 auto' }}>{description}</div>
    </div>
  );
}

export function FilterBar({ children, count }) {
  return (
    <div className="filter-bar">
      {children}
      {count !== undefined && <span className="result-count">{count.toLocaleString()} results</span>}
    </div>
  );
}

export function DataTable({ children }) {
  return (
    <div className="table-scroll">
      <table className="data-table">
        {children}
      </table>
    </div>
  );
}

export function CheckBox({ checked, variant = 'default', onClick }) {
  const cls = checked ? (variant === 'verified' ? 'check-box verified' : 'check-box checked') : 'check-box';
  return (
    <div className={cls} onClick={onClick}>
      {checked && <span style={{ color: 'white', fontSize: 12, fontWeight: 700 }}>✓</span>}
    </div>
  );
}
