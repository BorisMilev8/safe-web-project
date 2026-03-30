import backendResults from "./data/backendResults.json";

export default function App() {
  return (
    <div style={{ padding: "20px", fontFamily: "Arial, sans-serif" }}>
      <h1>Safe Web Dashboard</h1>
      <p>Based on 25 trial runs per browser.</p>

      {backendResults.length === 0 ? (
        <p>No backend results yet. Run the backend first.</p>
      ) : (
        backendResults.map((run, i) => (
          <div key={i} style={{ marginBottom: "10px" }}>
            <strong>{run.browser}</strong> — CPU: {run.cpu}% | Memory: {run.memory} MB
          </div>
        ))
      )}
    </div>
  );
}
