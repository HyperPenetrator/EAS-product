import React, { memo } from "react";
import "./InsightsFeed.css";

/**
 * InsightsFeed Component
 * Displays qualitative insights and narratives extracted from the dataset.
 * 
 * @param {Object} props
 * @param {Object} props.data The dashboard data payload containing insights
 */
const InsightsFeed = memo(({ data }) => {
  if (!data) return null;

  const insights = data.insights;
  if (!insights) {
    return (
      <div className="insights-feed-empty glass-card">
        <p>No qualitative insights were found in this dataset. We'll stick to the charts below!</p>
      </div>
    );
  }

  const {
    dataset_summary,
    primary_topics = [],
    narrative_insights = [],
    data_quality_observations = [],
  } = insights;

  /**
   * Returns an emoji icon based on the severity level
   * @param {string} severity The severity level (high, medium, low)
   * @returns {string} Emoji character
   */
  const getSeverityIcon = (severity) => {
    switch (severity?.toLowerCase()) {
      case "high":
        return "⚠️";
      case "medium":
        return "🔍";
      case "low":
      default:
        return "💬";
    }
  };

  return (
    <div className="insights-feed-container animate-fade-up">
      {/* Narrative Intro */}
      <div className="insights-intro-card glass-card">
        <div className="insights-intro-header">
          <span className="insights-sparkle">✨</span>
          <h3>Dataset Narrative</h3>
        </div>
        <p className="insights-summary-text">{dataset_summary}</p>
        <div className="insights-meta-row">
          <span className="insights-meta-pill">
            📊 {data.total_rows?.toLocaleString() || "—"} records
          </span>
          <span className="insights-meta-pill">
            🗂️ {data.total_columns || "—"} fields
          </span>
          <span className="insights-meta-pill">
            🧹 {data.null_percentage !== undefined ? `${data.null_percentage.toFixed(1)}% empty cells` : "—"}
          </span>
        </div>
      </div>

      {/* Grid: Topics & Narratives */}
      <div className="insights-grid">
        {/* Left Column: Primary Topics */}
        {primary_topics.length > 0 && (
          <div className="insights-column">
            <h4 className="column-title">Extracted Themes & Topics</h4>
            <div className="topics-list">
              {primary_topics.map((topic, i) => (
                <div
                  key={topic.topic_name || i}
                  className="topic-card glass-card animate-fade-up"
                  style={{ animationDelay: `${i * 100}ms` }}
                >
                  <div className="topic-header">
                    <h5 className="topic-name">{topic.topic_name}</h5>
                    {topic.confidence !== undefined && (
                      <span className="topic-confidence">
                        {(topic.confidence * 100).toFixed(0)}% fit
                      </span>
                    )}
                  </div>
                  <p className="topic-desc">{topic.description}</p>
                  {topic.keywords && topic.keywords.length > 0 && (
                    <div className="topic-keywords">
                      {topic.keywords.map((kw) => (
                        <span key={kw} className="keyword-tag">
                          #{kw}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Right Column: Narrative Observations */}
        {narrative_insights.length > 0 && (
          <div className="insights-column">
            <h4 className="column-title">Key Observations</h4>
            <div className="narratives-list">
              {narrative_insights.map((item, i) => (
                <div
                  key={item.title || i}
                  className={`narrative-card severity-${item.severity?.toLowerCase() || "low"} glass-card animate-fade-up`}
                  style={{ animationDelay: `${i * 100}ms` }}
                >
                  <div className="narrative-header">
                    <span className="narrative-icon">
                      {getSeverityIcon(item.severity)}
                    </span>
                    <h5 className="narrative-title">{item.title}</h5>
                    <span className={`severity-badge badge-${item.severity?.toLowerCase() || "low"}`}>
                      {item.severity || "low"}
                    </span>
                  </div>
                  <p className="narrative-text">{item.insight}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Data Quality / Hygiene Section */}
      {data_quality_observations.length > 0 && (
        <div className="quality-card glass-card">
          <div className="quality-header">
            <span>🧼</span>
            <h4>Data Hygiene & Quality Notes</h4>
          </div>
          <ul className="quality-list">
            {data_quality_observations.map((obs, i) => (
              <li key={i}>{obs}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
});

export default InsightsFeed;
