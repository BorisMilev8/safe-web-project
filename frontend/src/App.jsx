import { sampleRuns } from "./data/sampleRuns";

export default function App() {
  return (
    <div style={{ padding: "20px", fontFamily: "Arial" }}>
      <h1>Safe Web Dashboard</h1>

      {sampleRuns.map((run, i) => (
        <div key={i} style={{ marginBottom: "10px" }}>
          <strong>{run.browser}</strong> — CPU: {run.cpu}% | Memory: {run.memory} MB
        </div>
      ))}
    </div>
  );
}
