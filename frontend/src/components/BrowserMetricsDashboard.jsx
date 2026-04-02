import { useEffect, useMemo, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") || "";
const RESULTS_URL = API_BASE ? `${API_BASE}/api/results` : "/safe_web_results_real.json";

export default function BrowserMetricsDashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [selectedBrowser, setSelectedBrowser] = useState("All");

  useEffect(() => {
    fetch(RESULTS_URL)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Could not load data from ${RESULTS_URL}`);
        }
        return response.json();
      })
      .then((json) => {
        setData(json);
      })
      .catch((err) => {
        setError(err.message);
      });
  }, []);

  const browsers = useMemo(() => {
    if (!data?.results) return ["All"];
    const unique = [...new Set(data.results.map((item) => item.browser))];
    return ["All", ...unique];
  }, [data]);

  const filteredResults = useMemo(() => {
    if (!data?.results) return [];
    if (selectedBrowser === "All") return data.results;
    return data.results.filter((item) => item.browser === selectedBrowser);
  }, [data, selectedBrowser]);

  const summary = useMemo(() => {
    if (!filteredResults.length) {
      return {
        runs: 0,
        avgLoadTime: 0,
        avgCpu: 0,
        peakCpu: 0,
        avgMemory: 0,
        peakMemory: 0,
      };
    }

    const runs = filteredResults.length;
    const avgLoadTime =
      filteredResults.reduce((sum, item) => sum + Number(item.load_time_sec || 0), 0) / runs;
    const avgCpu =
      filteredResults.reduce((sum, item) => sum + Number(item.avg_cpu_percent || 0), 0) / runs;
    const peakCpu = Math.max(
      ...filteredResults.map((item) => Number(item.peak_cpu_percent || 0))
    );
    const avgMemory =
      filteredResults.reduce((sum, item) => sum + Number(item.avg_rss_mb || 0), 0) / runs;
    const peakMemory = Math.max(
      ...filteredResults.map((item) => Number(item.peak_rss_mb || 0))
    );

    return {
      runs,
      avgLoadTime,
      avgCpu,
      peakCpu,
      avgMemory,
      peakMemory,
    };
  }, [filteredResults]);

  if (error) {
    return (
      <div className="dashboard">
        <h2>Dashboard Error</h2>
        <p>{error}</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="dashboard">
        <h2>Loading Dashboard...</h2>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <h2>Overview</h2>
      <p><strong>Generated:</strong> {data.generated_at || "N/A"}</p>

      <label>
        Filter Browser:{" "}
        <select
          value={selectedBrowser}
          onChange={(e) => setSelectedBrowser(e.target.value)}
        >
          {browsers.map((browser) => (
            <option key={browser} value={browser}>
              {browser}
            </option>
          ))}
        </select>
      </label>

      <div className="summary-grid">
        <div><h3>Total Runs</h3><p>{summary.runs}</p></div>
        <div><h3>Avg Load Time</h3><p>{summary.avgLoadTime.toFixed(2)} s</p></div>
        <div><h3>Avg CPU</h3><p>{summary.avgCpu.toFixed(2)} %</p></div>
        <div><h3>Peak CPU</h3><p>{summary.peakCpu.toFixed(2)} %</p></div>
        <div><h3>Avg Memory</h3><p>{summary.avgMemory.toFixed(2)} MB</p></div>
        <div><h3>Peak Memory</h3><p>{summary.peakMemory.toFixed(2)} MB</p></div>
      </div>

      <h2>Test Results</h2>
      <table>
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Browser</th>
            <th>URL</th>
            <th>Load Time (s)</th>
            <th>Avg CPU (%)</th>
            <th>Peak CPU (%)</th>
            <th>Avg Memory (MB)</th>
            <th>Peak Memory (MB)</th>
          </tr>
        </thead>
        <tbody>
          {filteredResults.map((item, index) => (
            <tr key={`${item.timestamp}-${item.browser}-${index}`}>
              <td>{item.timestamp}</td>
              <td>{item.browser}</td>
              <td>{item.url}</td>
              <td>{Number(item.load_time_sec || 0).toFixed(2)}</td>
              <td>{Number(item.avg_cpu_percent || 0).toFixed(2)}</td>
              <td>{Number(item.peak_cpu_percent || 0).toFixed(2)}</td>
              <td>{Number(item.avg_rss_mb || 0).toFixed(2)}</td>
              <td>{Number(item.peak_rss_mb || 0).toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
