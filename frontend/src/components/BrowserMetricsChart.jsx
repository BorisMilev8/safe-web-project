import { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export default function BrowserMetricsChart() {
  const [data, setData] = useState([]);

  useEffect(() => {
    fetch("/safe_web_results_real.json")
      .then((res) => res.json())
      .then((json) => setData(json.summary || []));
  }, []);

  return (
    <div style={{ width: "100%", height: 400 }}>
      <ResponsiveContainer>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="browser" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="avg_load_time_sec" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
