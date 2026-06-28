import React, { memo } from "react";
import {
  LineChart, Line,
  BarChart, Bar,
  XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
} from "recharts";
import "./Charts.css";

const chartTheme = {
  gridColor: "rgba(255,255,255,0.06)",
  axisColor: "#4a5270",
  tickColor: "#6b7394",
  tooltipBg: "#0f1629",
  tooltipBorder: "rgba(99,102,241,0.3)",
};

/**
 * Custom tooltip component for charts
 * @param {Object} props
 * @param {boolean} props.active
 * @param {Array} props.payload
 * @param {string} props.label
 */
const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: chartTheme.tooltipBg,
      border: `1px solid ${chartTheme.tooltipBorder}`,
      borderRadius: 10,
      padding: "10px 14px",
      fontSize: 13,
      boxShadow: "0 8px 32px rgba(0,0,0,0.6)",
    }}>
      <p style={{ color: "#8b95b8", marginBottom: 4, fontWeight: 600 }}>{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color, fontWeight: 700 }}>
          {p.name}: {typeof p.value === "number"
            ? p.value >= 1000
              ? `$${(p.value / 1000).toFixed(1)}K`
              : p.value.toLocaleString()
            : p.value}
        </p>
      ))}
    </div>
  );
};

/**
 * Charts Component
 * Displays Monthly Revenue and Revenue by Region charts if data is available.
 * 
 * @param {Object} props
 * @param {Object} props.data The dashboard data payload containing monthly_data and regional_data
 */
const Charts = memo(({ data }) => {
  const hasMonthly = data?.monthly_data?.length > 0;
  const hasRegional = data?.regional_data?.length > 0;

  if (!hasMonthly && !hasRegional) return null;

  return (
    <div className="charts-grid animate-fade-up">
      {hasMonthly && (
        <div className="chart-card glass-card">
          <div className="chart-header">
            <span className="chart-dot" style={{ background: "#6366f1" }} />
            <h3 className="chart-title">Monthly Revenue Trend</h3>
          </div>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={data.monthly_data} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={chartTheme.gridColor} vertical={false} />
              <XAxis
                dataKey="month"
                stroke={chartTheme.axisColor}
                tick={{ fill: chartTheme.tickColor, fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                stroke={chartTheme.axisColor}
                tick={{ fill: chartTheme.tickColor, fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                tickFormatter={(v) => v >= 1000 ? `$${(v/1000).toFixed(0)}K` : `$${v}`}
              />
              <Tooltip content={<CustomTooltip />} />
              <Line
                type="monotone"
                dataKey="revenue"
                stroke="#6366f1"
                strokeWidth={2.5}
                dot={{ fill: "#6366f1", r: 4, strokeWidth: 0 }}
                activeDot={{ r: 6, fill: "#818cf8" }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {hasRegional && (
        <div className="chart-card glass-card">
          <div className="chart-header">
            <span className="chart-dot" style={{ background: "#10b981" }} />
            <h3 className="chart-title">Revenue by Region</h3>
          </div>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={data.regional_data} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={chartTheme.gridColor} vertical={false} />
              <XAxis
                dataKey="region"
                stroke={chartTheme.axisColor}
                tick={{ fill: chartTheme.tickColor, fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                stroke={chartTheme.axisColor}
                tick={{ fill: chartTheme.tickColor, fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                tickFormatter={(v) => v >= 1000 ? `$${(v/1000).toFixed(0)}K` : `$${v}`}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="revenue" fill="url(#barGreen)" radius={[6, 6, 0, 0]} maxBarSize={50} />
              <defs>
                <linearGradient id="barGreen" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#10b981" />
                  <stop offset="100%" stopColor="#059669" stopOpacity="0.7" />
                </linearGradient>
              </defs>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
});

export default Charts;
