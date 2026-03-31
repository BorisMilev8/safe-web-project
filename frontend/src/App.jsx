import BrowserMetricsChart from "./components/BrowserMetricsChart";

export default function App() {
  return (
    <div className="app">
      <header className="hero">
        <h1>Safe Web Dashboard</h1>
        <p>
          Real browser benchmarking results for Chromium, Firefox, and WebKit.
        </p>
      </header>

      <main>
        <BrowserMetricsChart />
      </main>
    </div>
  );
}
