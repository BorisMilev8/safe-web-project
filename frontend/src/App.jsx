import BrowserMetricsChart from "./components/BrowserMetricsChart";

export default function App() {
  return (
    <div className="app">
      <header className="hero">
        <h1>Safe Web Dashboard</h1>
        <p>
          Real browser benchmarking across lightweight, medium, and heavy
          websites.
        </p>
      </header>

      <BrowserMetricsChart />
    </div>
  );
}
