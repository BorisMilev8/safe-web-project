import { useEffect, useMemo, useState } from "react";

export default function BrowserMetricsDashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [selectedBrowser, setSelectedBrowser] = useState("All");

  useEffect(() => {
    fetch("/safe_web_results_real.json")
      .then((response) => {
        if (!response.ok) {
          throw new Error("Could not load safe_web_results_real.json");
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
    const peakCpu = Math.max(...filteredResults.map((item) => Number(item.peak_cpu_percent || 0)));
    const avgMemory =
      filteredResults.reduce((sum, item) => sum + Number(item.avg_rss_mb || 0), 0) / runs;
    const peakMemory = Math.max(...filteredResults.map((item) => Number(item.peak_rss_mb || 0)));

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
      <section className="card">
        <h2>Dashboard Error</h2>
        <p>{error}</p>
        <p>Make sure frontend/public/safe_web_results_real.json exists.</p>
      </section>
    );
  }

  if (!data) {
    return (
      <section className="card">
        <h2>Loading Dashboard...</h2>
      </section>
    );
  }

  return (
    <div className="dashboard">
      <section className="card">
        <div className="row">
          <div>
            <h2>Overview</h2>
            <p>
              Generated: <strong>{data.generated_at || "N/A"}</strong>
            </p>
          </div>

          <div>
            <label htmlFor="browserFilter"><strong>Filter Browser:</strong></label>
            <select
              id="browserFilter"
              value={selectedBrowser}
              onChange={(e) => setSelectedBrowser(e.target.value)}
            >
              {browsers.map((browser) => (
                <option key={browser} value={browser}>
                  {browser}
                </option>
              ))}
            </select>
          </div>
        </div>
      </section>

      <section className="stats-grid">
        <div className="stat-card">
          <h3>Total Runs</h3>
          <p>{summary.runs}</p>
        </div>
        <div className="stat-card">
          <h3>Avg Load Time</h3>
          <p>{summary.avgLoadTime.toFixed(2)} s</p>
        </div>
        <div className="stat-card">
          <h3>Avg CPU</h3>
          <p>{summary.avgCpu.toFixed(2)} %</p>
        </div>
        <div className="stat-card">
          <h3>Peak CPU</h3>
          <p>{summary.peakCpu.toFixed(2)} %</p>
        </div>
        <div className="stat-card">
          <h3>Avg Memory</h3>
          <p>{summary.avgMemory.toFixed(2)} MB</p>
        </div>
        <div className="stat-card">
          <h3>Peak Memory</h3>
          <p>{summary.peakMemory.toFixed(2)} MB</p>
        </div>
      </section>

      <section className="card">
        <h2>Test Results</h2>
        <div className="table-wrap">
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
                <tr key={`${item.timestamp}-${index}`}>
                  <td>{item.timestamp}</td>
                  <td>{item.browser}</td>
                  <td className="url-cell">{item.url}</td>
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
      </section>
    </div>
  );
}
