import React from "react";
import "./KPICards.css";

const formatValue = (value, prefix = "", suffix = "") => {
  if (value === undefined || value === null || isNaN(value)) return "—";
  const num = Number(value);
  if (Math.abs(num) >= 1_000_000) return `${prefix}${(num / 1_000_000).toFixed(1)}M${suffix}`;
  if (Math.abs(num) >= 1_000) return `${prefix}${(num / 1_000).toFixed(1)}K${suffix}`;
  return `${prefix}${num.toFixed(2)}${suffix}`;
};

const deriveKPIs = (data) => {
  const kpis = [];

  // Total Revenue
  const revenue = data.total_revenue ?? data.total_sales ?? data.total_amount;
  if (revenue !== undefined) {
    kpis.push({
      id: "revenue",
      title: "Total Revenue",
      value: formatValue(revenue, "$"),
      icon: "💰",
      gradient: "var(--gradient-card-blue)",
      glow: "rgba(59, 130, 246, 0.3)",
    });
  }

  // Total Orders / Rows
  const orders = data.total_orders ?? data.total_rows;
  if (orders !== undefined) {
    kpis.push({
      id: "orders",
      title: data.total_orders !== undefined ? "Total Orders" : "Total Records",
      value: Number(orders).toLocaleString(),
      icon: "📦",
      gradient: "var(--gradient-card-green)",
      glow: "rgba(16, 185, 129, 0.3)",
    });
  }

  // Avg Order Value
  const avg = data.avg_order_value;
  if (avg !== undefined) {
    kpis.push({
      id: "avg",
      title: "Avg Order Value",
      value: formatValue(avg, "$"),
      icon: "💵",
      gradient: "var(--gradient-card-purple)",
      glow: "rgba(124, 58, 237, 0.3)",
    });
  }

  // Profit Margin
  const margin = data.profit_margin;
  if (margin !== undefined) {
    kpis.push({
      id: "margin",
      title: "Profit Margin",
      value: `${(Number(margin) * 100).toFixed(1)}%`,
      icon: "📈",
      gradient: "var(--gradient-card-orange)",
      glow: "rgba(217, 119, 6, 0.3)",
    });
  }

  // Total Columns
  if (kpis.length < 4 && data.total_columns !== undefined) {
    kpis.push({
      id: "cols",
      title: "Columns",
      value: data.total_columns,
      icon: "📊",
      gradient: "linear-gradient(135deg, #0e7490 0%, #0891b2 100%)",
      glow: "rgba(6, 182, 212, 0.3)",
    });
  }

  return kpis;
};

export default function KPICards({ data }) {
  const kpis = deriveKPIs(data);

  if (!kpis.length) return null;

  const handleMouseMove = (e) => {
    const card = e.currentTarget;
    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    // Set variables for holographic spotlight position
    card.style.setProperty("--mouse-x", `${x}px`);
    card.style.setProperty("--mouse-y", `${y}px`);

    const xc = rect.width / 2;
    const yc = rect.height / 2;
    const angleX = (yc - y) / (yc / 8);
    const angleY = (x - xc) / (xc / 8);
    card.style.transition = "transform 0.05s ease-out";
    card.style.transform = `perspective(1000px) rotateX(${angleX}deg) rotateY(${angleY}deg) translateY(-6px)`;
  };

  const handleMouseLeave = (e) => {
    const card = e.currentTarget;
    card.style.transition = "transform 0.5s cubic-bezier(0.25, 1, 0.5, 1)";
    card.style.transform = `perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(0px)`;
  };

  return (
    <div className="kpi-grid animate-fade-up">
      {kpis.map((kpi, i) => (
        <div
          key={kpi.id}
          className="kpi-card"
          onMouseMove={handleMouseMove}
          onMouseLeave={handleMouseLeave}
          style={{
            background: kpi.gradient,
            animationDelay: `${i * 80}ms`,
            transition: "box-shadow 0.2s ease, transform 0.5s cubic-bezier(0.25, 1, 0.5, 1)",
          }}
        >
          <div className="kpi-glow" style={{ background: kpi.glow }} />
          <div className="kpi-content">
            <p className="kpi-label">{kpi.title}</p>
            <p className="kpi-value">{kpi.value}</p>
          </div>
          <span className="kpi-icon">{kpi.icon}</span>
        </div>
      ))}
    </div>
  );
}
