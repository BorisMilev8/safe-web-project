import React, { useMemo } from "react";
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
      runs: rows.length,
      avgCpu: average(rows.map((r) => Number(r.cpu))),
      avgMemory: average(rows.map((r) => Number(r.memory))),
    }));
  }, []);

  const bestCpu =
    browserSummary.length > 0
      ? [...browserSummary].sort((a, b) => a.avgCpu - b.avgCpu)[0]
      : null;

  const bestMemory =
    browserSummary.length > 0
      ? [...browserSummary].sort((a, b) => a.avgMemory - b.avgMemory)[0]
      : null;

  const maxCpu = Math.max(...browserSummary.map((b) => b.avgCpu), 1);
  const maxMemory = Math.max(...browserSummary.map((b) => b.avgMemory), 1);

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#f8fafc",
        fontFamily: "Arial, sans-serif",
        color: "#111827",
        padding: "32px",
      }}
    >
      <div style={{ maxWidth: "1200px", margin: "0 auto" }}>
        <div
          style={{
            background: "white",
            borderRadius: "20px",
            padding: "28px",
            boxShadow: "0 8px 24px rgba(0,0,0,0.08)",
            marginBottom: "24px",
          }}
        >
          <div
            style={{
              display: "inline-block",
              padding: "6px 12px",
              background: "#e0f2fe",
              color: "#0369a1",
              borderRadius: "999px",
              fontSize: "13px",
              fontWeight: "bold",
              marginBottom: "14px",
            }}
          >
            Alpha Dashboard
          </div>

          <h1 style={{ margin: 0, fontSize: "42px" }}>Safe Web Dashboard</h1>
          <p style={{ marginTop: "12px", fontSize: "18px", color: "#4b5563" }}>
            Comparing Safari, Google Chrome, and Firefox across 25 trial runs
            per browser using CPU and memory metrics.
          </p>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
            gap: "18px",
            marginBottom: "24px",
          }}
        >
          <div
            style={{
              background: "white",
              borderRadius: "18px",
              padding: "22px",
              boxShadow: "0 6px 18px rgba(0,0,0,0.06)",
            }}
          >
            <div style={{ color: "#6b7280", fontSize: "14px" }}>Total Runs</div>
            <div style={{ fontSize: "34px", fontWeight: "bold", marginTop: "8px" }}>
              {backendResults.length}
            </div>
          </div>

          <div
            style={{
              background: "white",
              borderRadius: "18px",
              padding: "22px",
              boxShadow: "0 6px 18px rgba(0,0,0,0.06)",
            }}
          >
            <div style={{ color: "#6b7280", fontSize: "14px" }}>Browsers Compared</div>
            <div style={{ fontSize: "34px", fontWeight: "bold", marginTop: "8px" }}>
              {browserSummary.length}
            </div>
          </div>

          <div
            style={{
              background: "white",
              borderRadius: "18px",
              padding: "22px",
              boxShadow: "0 6px 18px rgba(0,0,0,0.06)",
            }}
          >
            <div style={{ color: "#6b7280", fontSize: "14px" }}>Best Avg CPU</div>
            <div style={{ fontSize: "24px", fontWeight: "bold", marginTop: "8px" }}>
              {bestCpu ? bestCpu.browser : "N/A"}
            </div>
            <div style={{ color: "#4b5563", marginTop: "6px" }}>
              {bestCpu ? `${bestCpu.avgCpu.toFixed(2)}%` : ""}
            </div>
          </div>

          <div
            style={{
              background: "white",
              borderRadius: "18px",
              padding: "22px",
              boxShadow: "0 6px 18px rgba(0,0,0,0.06)",
            }}
          >
            <div style={{ color: "#6b7280", fontSize: "14px" }}>Best Avg Memory</div>
            <div style={{ fontSize: "24px", fontWeight: "bold", marginTop: "8px" }}>
              {bestMemory ? bestMemory.browser : "N/A"}
            </div>
            <div style={{ color: "#4b5563", marginTop: "6px" }}>
              {bestMemory ? `${bestMemory.avgMemory.toFixed(2)} MB` : ""}
            </div>
          </div>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: "24px",
            marginBottom: "24px",
          }}
        >
          <div
            style={{
              background: "white",
              borderRadius: "20px",
              padding: "24px",
              boxShadow: "0 8px 24px rgba(0,0,0,0.06)",
            }}
          >
            <h2 style={{ marginTop: 0 }}>Average CPU by Browser</h2>
            {browserSummary.map((item) => (
              <div key={item.browser} style={{ marginBottom: "18px" }}>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    marginBottom: "6px",
                    fontWeight: "bold",
                  }}
                >
                  <span>{item.browser}</span>
                  <span>{item.avgCpu.toFixed(2)}%</span>
                </div>
                <div
                  style={{
                    background: "#e5e7eb",
                    height: "22px",
                    borderRadius: "999px",
                    overflow: "hidden",
                  }}
                >
                  <div
                    style={{
                      width: `${(item.avgCpu / maxCpu) * 100}%`,
                      height: "100%",
                      background: "#2563eb",
                    }}
                  />
                </div>
              </div>
            ))}
          </div>

          <div
            style={{
              background: "white",
              borderRadius: "20px",
              padding: "24px",
              boxShadow: "0 8px 24px rgba(0,0,0,0.06)",
            }}
          >
            <h2 style={{ marginTop: 0 }}>Average Memory by Browser</h2>
            {browserSummary.map((item) => (
              <div key={item.browser} style={{ marginBottom: "18px" }}>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    marginBottom: "6px",
                    fontWeight: "bold",
                  }}
                >
                  <span>{item.browser}</span>
                  <span>{item.avgMemory.toFixed(2)} MB</span>
                </div>
                <div
                  style={{
                    background: "#e5e7eb",
                    height: "22px",
                    borderRadius: "999px",
                    overflow: "hidden",
                  }}
                >
                  <div
                    style={{
                      width: `${(item.avgMemory / maxMemory) * 100}%`,
                      height: "100%",
                      background: "#059669",
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div
          style={{
            background: "white",
            borderRadius: "20px",
            padding: "24px",
            boxShadow: "0 8px 24px rgba(0,0,0,0.06)",
          }}
        >
          <h2 style={{ marginTop: 0 }}>Browser Summary</h2>

          {browserSummary.length === 0 ? (
            <p>No backend results yet. Run the backend first.</p>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table
                style={{
                  width: "100%",
                  borderCollapse: "collapse",
                  marginTop: "8px",
                }}
              >
                <thead>
                  <tr style={{ textAlign: "left", borderBottom: "2px solid #e5e7eb" }}>
                    <th style={{ padding: "12px 8px" }}>Browser</th>
                    <th style={{ padding: "12px 8px" }}>Trials</th>
                    <th style={{ padding: "12px 8px" }}>Avg CPU</th>
                    <th style={{ padding: "12px 8px" }}>Avg Memory</th>
                  </tr>
                </thead>
                <tbody>
                  {browserSummary.map((item) => (
                    <tr key={item.browser} style={{ borderBottom: "1px solid #e5e7eb" }}>
                      <td style={{ padding: "12px 8px", fontWeight: "bold" }}>{item.browser}</td>
                      <td style={{ padding: "12px 8px" }}>{item.runs}</td>
                      <td style={{ padding: "12px 8px" }}>{item.avgCpu.toFixed(2)}%</td>
                      <td style={{ padding: "12px 8px" }}>{item.avgMemory.toFixed(2)} MB</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
