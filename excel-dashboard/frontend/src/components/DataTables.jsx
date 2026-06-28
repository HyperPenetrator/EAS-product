import React, { useState } from "react";
import "./DataTables.css";

const PAGE_SIZE = 15;

export default function DataTables({ data, jobId }) {
  const [page, setPage] = useState(1);

  // Build rows from monthly or regional data, or fall back to summary stats
  const monthlyRows = data?.monthly_data?.map((r) => ({
    Month: r.month,
    Revenue: typeof r.revenue === "number" ? `$${r.revenue.toLocaleString()}` : r.revenue,
  })) ?? [];

  const regionalRows = data?.regional_data?.map((r) => ({
    Region: r.region,
    Revenue: typeof r.revenue === "number" ? `$${r.revenue.toLocaleString()}` : r.revenue,
  })) ?? [];

  // Summary stats table from flat numeric fields
  const summaryRows = Object.entries(data ?? {})
    .filter(([k, v]) => typeof v === "number" && !["total_rows", "total_columns", "null_percentage"].includes(k))
    .map(([k, v]) => ({
      Metric: k.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
      Value: v >= 1000 ? v.toLocaleString("en-US", { maximumFractionDigits: 2 }) : v.toFixed(2),
    }));

  const sections = [
    { title: "📅 Monthly Breakdown", rows: monthlyRows },
    { title: "🗺️ Regional Breakdown", rows: regionalRows },
    { title: "📊 Summary Statistics", rows: summaryRows },
  ].filter((s) => s.rows.length > 0);

  if (!sections.length) return null;

  return (
    <div className="tables-container animate-fade-up">
      {sections.map((section) => {
        const columns = Object.keys(section.rows[0] || {});
        const totalPages = Math.ceil(section.rows.length / PAGE_SIZE);
        const paged = section.rows.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

        return (
          <div key={section.title} className="table-card glass-card">
            <div className="table-header">
              <h3 className="table-title">{section.title}</h3>
              <span className="table-count">{section.rows.length} rows</span>
            </div>

            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    {columns.map((col) => (
                      <th key={col}>{col}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {paged.map((row, i) => (
                    <tr key={i}>
                      {columns.map((col) => (
                        <td key={col}>{row[col] ?? "—"}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {totalPages > 1 && (
              <div className="table-pagination">
                <button
                  className="btn btn-ghost"
                  style={{ padding: "6px 14px", fontSize: 13 }}
                  disabled={page === 1}
                  onClick={() => setPage((p) => p - 1)}
                >
                  ← Prev
                </button>
                <span style={{ color: "var(--text-secondary)", fontSize: 13 }}>
                  Page {page} of {totalPages}
                </span>
                <button
                  className="btn btn-ghost"
                  style={{ padding: "6px 14px", fontSize: 13 }}
                  disabled={page === totalPages}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Next →
                </button>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
