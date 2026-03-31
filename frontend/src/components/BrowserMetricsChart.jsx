import { useEffect, useMemo, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

const METRIC_OPTIONS = [
  { value: "avg_load_time_sec", label: "Average Load Time (sec)" },
  { value: "avg_cpu_percent", label: "Average CPU (%)" },
  { value: "peak_cpu_percent", label: "Peak CPU (%)" },
  { value: "avg_rss_mb", label: "Average Memory (MB)" },
  { value: "peak_rss_mb", label: "Peak Memory (MB)" },
];

const DISPLAY_NAMES = {
  chromium: "Chromium",
  firefox: "Firefox",
  webkit: "WebKit",
};

export default function BrowserMetricsChart() {
  const [summaryData, setSummaryData] = useState([]);
  const [configData, setConfigData] = useState(null);
  const [generatedAt, setGeneratedAt] = useState("");
  const [metric, setMetric] = useState("avg_load_time_sec");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadResults() {
      try {
        setLoading(true);
        setError("");

        const response = await fetch("/safe_web_results_real.json");

        if (!response.ok) {
          throw new Error("Could not load benchmark results.");
        }

        const json = await response.json();

        setSummaryData(Array.isArray(json.summary) ? json.summary : []);
        setConfigData(json.config || null);
        setGeneratedAt(json.generated_at || "");
      } catch (err) {
        setError(err.message || "Failed to load results.");
      } finally {
        setLoading(false);
      }
    }

    loadResults();
  }, []);

  const chartData = useMemo(() => {
    return summaryData.map((item) => ({
      ...item,
      browserLabel: DISPLAY_NAMES[item.browser] || item.browser,
    }));
  }, [summaryData]);

  const selectedMetricLabel =
    METRIC_OPTIONS.find((option) => option.value === metric)?.label || metric;

  if (loading) {
    return <div className="card">Loading benchmark data...</div>;
  }

  if (error) {
    return <div className="card error">Error: {error}</div>;
  }

  if (!summaryData.length) {
    return <div className="card">No benchmark data found.</div>;
  }

  return (
    <section className="dashboard-grid">
      <div className="card">
        <div className="card-header">
          <h2>Browser Comparison</h2>

          <div className="control-group">
            <label htmlFor="metric-select">Metric</label>
            <select
              id="metric-select"
              value={metric}
              onChange={(e) => setMetric(e.target.value)}
            >
              {METRIC_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="chart-wrap">
          <ResponsiveContainer width="100%" height={380}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="browserLabel" />
              <YAxis />
              <Tooltip formatter={(value) => formatValue(value)} />
              <Legend />
              <Bar dataKey={metric} name={selectedMetricLabel} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="card">
        <h2>Run Summary</h2>
        <div className="meta-grid">
          <div className="meta-item">
            <span className="meta-label">Generated</span>
            <span className="meta-value">
              {generatedAt ? new Date(generatedAt).toLocaleString() : "N/A"}
            </span>
          </div>

          <div className="meta-item">
            <span className="meta-label">Browsers</span>
            <span className="meta-value">
              {configData?.browsers?.map((b) => DISPLAY_NAMES[b] || b).join(", ") ||
                "N/A"}
            </span>
          </div>

          <div className="meta-item">
            <span className="meta-label">Trials per Browser</span>
            <span className="meta-value">
              {configData?.trials_per_browser ?? "N/A"}
            </span>
          </div>

          <div className="meta-item">
            <span className="meta-label">URLs Tested</span>
            <span className="meta-value">
              {configData?.urls_tested?.length ?? "N/A"}
            </span>
          </div>
        </div>
      </div>

      <div className="card full-width">
        <h2>Detailed Summary Table</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Browser</th>
                <th>Runs</th>
                <th>Avg Load Time</th>
                <th>Avg CPU</th>
                <th>Peak CPU</th>
                <th>Avg Memory</th>
                <th>Peak Memory</th>
              </tr>
            </thead>
            <tbody>
              {summaryData.map((row) => (
                <tr key={row.browser}>
                  <td>{DISPLAY_NAMES[row.browser] || row.browser}</td>
                  <td>{row.runs ?? "N/A"}</td>
                  <td>{formatValue(row.avg_load_time_sec)}</td>
                  <td>{formatValue(row.avg_cpu_percent)}</td>
                  <td>{formatValue(row.peak_cpu_percent)}</td>
                  <td>{formatValue(row.avg_rss_mb)}</td>
                  <td>{formatValue(row.peak_rss_mb)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}

function formatValue(value) {
  if (value === null || value === undefined) {
    return "N/A";
  }
  return Number(value).toFixed(2);
}
