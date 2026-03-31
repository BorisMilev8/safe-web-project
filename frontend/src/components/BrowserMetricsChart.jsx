import { useEffect, useState } from "react";

export default function BrowserMetricsChart() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch("/safe_web_results_real.json")
      .then((res) => {
        if (!res.ok) {
          throw new Error("Could not load safe_web_results_real.json");
        }
        return res.json();
      })
      .then((json) => {
        setData(json);
      })
      .catch((err) => {
        setError(err.message);
      });
  }, []);

  if (error) {
    return <div style={{ padding: "1rem" }}>Error: {error}</div>;
  }

  if (!data) {
    return <div style={{ padding: "1rem" }}>Loading metrics...</div>;
  }

  const summary = data.summary || [];

  return (
    <div style={{ padding: "1rem" }}>
      <h2>Browser Resource Metrics</h2>
      <p>
        <strong>Generated:</strong> {data.generated_at || "N/A"}
      </p>

      <table
        style={{
          width: "100%",
          borderCollapse: "collapse",
          marginTop: "1rem",
        }}
      >
        <thead>
          <tr>
            <th style={th}>Browser</th>
            <th style={th}>Runs</th>
            <th style={th}>Avg Load Time (s)</th>
            <th style={th}>Avg CPU (%)</th>
            <th style={th}>Peak CPU (%)</th>
            <th style={th}>Avg Memory (MB)</th>
            <th style={th}>Peak Memory (MB)</th>
          </tr>
        </thead>
        <tbody>
          {summary.map((row, index) => (
            <tr key={index}>
              <td style={td}>{row.browser}</td>
              <td style={td}>{row.runs}</td>
              <td style={td}>{row.avg_load_time_sec?.toFixed(2)}</td>
              <td style={td}>{row.avg_cpu_percent?.toFixed(2)}</td>
              <td style={td}>{row.peak_cpu_percent?.toFixed(2)}</td>
              <td style={td}>{row.avg_rss_mb?.toFixed(2)}</td>
              <td style={td}>{row.peak_rss_mb?.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h3 style={{ marginTop: "2rem" }}>Raw Test Results</h3>
      <table
        style={{
          width: "100%",
          borderCollapse: "collapse",
          marginTop: "1rem",
        }}
      >
        <thead>
          <tr>
            <th style={th}>Timestamp</th>
            <th style={th}>Browser</th>
            <th style={th}>URL</th>
            <th style={th}>Load Time (s)</th>
            <th style={th}>Avg CPU (%)</th>
            <th style={th}>Peak CPU (%)</th>
            <th style={th}>Avg Memory (MB)</th>
            <th style={th}>Peak Memory (MB)</th>
          </tr>
        </thead>
        <tbody>
          {(data.results || []).map((row, index) => (
            <tr key={index}>
              <td style={td}>{row.timestamp}</td>
              <td style={td}>{row.browser}</td>
              <td style={td}>{row.url}</td>
              <td style={td}>{row.load_time_sec?.toFixed(2)}</td>
              <td style={td}>{row.avg_cpu_percent?.toFixed(2)}</td>
              <td style={td}>{row.peak_cpu_percent?.toFixed(2)}</td>
              <td style={td}>{row.avg_rss_mb?.toFixed(2)}</td>
              <td style={td}>{row.peak_rss_mb?.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const th = {
  border: "1px solid #ccc",
  padding: "8px",
  background: "#f5f5f5",
  textAlign: "left",
};

const td = {
  border: "1px solid #ccc",
  padding: "8px",
};
