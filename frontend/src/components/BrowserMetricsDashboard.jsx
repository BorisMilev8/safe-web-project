import { useEffect, useState } from "react";

export default function BrowserMetricsDashboard() {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetch("/safe_web_results_real.json")
      .then((res) => res.json())
      .then((json) => setData(json))
      .catch((err) => console.error(err));
  }, []);

  if (!data) {
    return <h2>Loading...</h2>;
  }

  return (
    <div>
      <h2>Safe Web Dashboard</h2>

      <table border="1" cellPadding="10">
        <thead>
          <tr>
            <th>Browser</th>
            <th>Load Time</th>
            <th>Avg CPU</th>
            <th>Peak CPU</th>
            <th>Avg Memory</th>
            <th>Peak Memory</th>
          </tr>
        </thead>
        <tbody>
          {data.results.map((row, i) => (
            <tr key={i}>
              <td>{row.browser}</td>
              <td>{row.load_time_sec}</td>
              <td>{row.avg_cpu_percent}</td>
              <td>{row.peak_cpu_percent}</td>
              <td>{row.avg_rss_mb}</td>
              <td>{row.peak_rss_mb}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
