import { useMemo } from "react";
import backendResults from "./data/backendResults.json";

function average(values) {
  if (!values.length) return 0;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

export default function App() {
  const browserSummary = useMemo(() => {
    const grouped = {};

    for (const row of backendResults) {
      if (!grouped[row.browser]) {
        grouped[row.browser] = [];
      }
      grouped[row.browser].push(row);
    }

    return Object.entries(grouped).map(([browser, rows]) => ({
      browser,
      avgCpu: average(rows.map((r) => r.cpu)).toFixed(2),
      avgMemory: average(rows.map((r) => r.memory)).toFixed(2),
    }));
  }, []);

  const maxCpu = Math.max(...browserSummary.map((b) => Number(b.avgCpu)), 1);
  const maxMemory = Math.max(...browserSummary.map((b) => Number(b.avgMemory)), 1);

  return (
    <div style={{ padding: "20px", fontFamily: "Arial, sans-serif" }}>
      <h1>Safe Web Dashboard</h1>

      {browserSummary.length === 0 ? (
        <p>No backend results yet. Run the backend first.</p>
      ) : (
        <>
          <h2>Average CPU by Browser</h2>
          <div style={{ marginBottom: "30px" }}>
            {browserSummary.map((item, index) => (
              <div key={index} style={{ marginBottom: "16px" }}>
                <div style={{ marginBottom: "4px" }}>
                  <strong>{item.browser}</strong> — {item.avgCpu}%
                </div>
                <div
                  style={{
                    background: "#e5e7eb",
                    height: "24px",
                    borderRadius: "8px",
                    overflow: "hidden",
                  }}
                >
                  <div
                    style={{
                      width: `${(Number(item.avgCpu) / maxCpu) * 100}%`,
                      height: "100%",
                      background: "#3b82f6",
                    }}
                  />
                </div>
              </div>
            ))}
          </div>

          <h2>Average Memory by Browser</h2>
          <div style={{ marginBottom: "30px" }}>
            {browserSummary.map((item, index) => (
              <div key={index} style={{ marginBottom: "16px" }}>
                <div style={{ marginBottom: "4px" }}>
                  <strong>{item.browser}</strong> — {item.avgMemory} MB
                </div>
                <div
                  style={{
                    background: "#e5e7eb",
                    height: "24px",
                    borderRadius: "8px",
                    overflow: "hidden",
                  }}
                >
                  <div
                    style={{
                      width: `${(Number(item.avgMemory) / maxMemory) * 100}%`,
                      height: "100%",
                      background: "#10b981",
                    }}
                  />
                </div>
              </div>
            ))}
          </div>

          <h2>Raw Results</h2>
          {backendResults.map((run, i) => (
            <div
              key={i}
              style={{
                marginBottom: "10px",
                padding: "10px",
                border: "1px solid #ddd",
                borderRadius: "8px",
              }}
            >
              <strong>{run.browser}</strong> — CPU: {run.cpu}% | Memory: {run.memory} MB
            </div>
          ))}
        </>
      )}
    </div>
  );
}
