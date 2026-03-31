import BrowserMetricsDashboard from "./components/BrowserMetricsDashboard";

export default function App() {
  return (
    <div className="app">
      <header className="hero">
        <h1>Safe Web Interactive Dashboard</h1>
        <p>
          Compare browser load time, CPU usage, and memory usage across tested websites.
        </p>
      </header>

      <main>
        <BrowserMetricsDashboard />
      </main>
    </div>
  );
}
