import { useEffect, useState, useRef } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

const API_BASE = "http://127.0.0.1:8000";
const WS_URL = "ws://127.0.0.1:8000/ws/alerts";

const card = {
  background: "linear-gradient(180deg, #020617, #020617ee)",
  borderRadius: 16,
  padding: 16,
  border: "1px solid #1e293b",
  boxShadow: "0 10px 24px rgba(2,6,23,0.6)",
};

export default function App() {
  const [status, setStatus] = useState("loading...");
  const [alerts, setAlerts] = useState([]);
  const [wsStatus, setWsStatus] = useState("disconnected");
  const [timeline, setTimeline] = useState([]);
  const beepRef = useRef(null);

  // Backend status
  useEffect(() => {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 4000);

    fetch(`${API_BASE}/status`, { signal: controller.signal })
      .then((r) => {
        if (!r.ok) throw new Error("backend down");
        return r.json();
      })
      .then((d) => setStatus(d.status || d.backend || "ok"))
      .catch(() => setStatus("backend down"))
      .finally(() => clearTimeout(timeout));

    fetch(`${API_BASE}/alerts?limit=500`)
      .then((r) => r.json())
      .then((d) => setAlerts(Array.isArray(d) ? d : []))
      .catch(() => setAlerts([]));
  }, []);

  // WebSocket (robust + reconnect)
  useEffect(() => {
    let ws;
    let retry;

    const connect = () => {
      ws = new WebSocket(WS_URL);

      ws.onopen = () => setWsStatus("connected");
      ws.onerror = () => setWsStatus("error");

      ws.onclose = () => {
        setWsStatus("reconnecting");
        retry = setTimeout(connect, 2000);
      };

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          const batch = Array.isArray(payload) ? payload : [payload];
          const now = new Date().toLocaleTimeString();

          setTimeline((prev) => [
            ...prev.slice(-30),
            { time: now, count: batch.length },
          ]);

          setAlerts((prev) => {
            const updated = [...batch, ...prev].slice(0, 500);
            const critical = batch.some((a) => a?.anomaly_score < 0.05);
            if (critical && beepRef.current) beepRef.current.play().catch(() => {});
            return updated;
          });
        } catch (e) {
          console.error("WS parse error:", e);
        }
      };
    };

    connect();
    return () => {
      clearTimeout(retry);
      ws?.close();
    };
  }, []);

  const badge = (state) => {
    if (state === "loading...") {
      return {
        padding: "5px 12px",
        borderRadius: 999,
        fontWeight: 700,
        fontSize: 12,
        background: "rgba(148,163,184,0.15)",
        color: "#94a3b8",
        border: "1px solid rgba(148,163,184,0.35)",
      };
    }
    const ok = state === "connected" || state === "ok";
    return {
      padding: "5px 12px",
      borderRadius: 999,
      fontWeight: 700,
      fontSize: 12,
      background: ok ? "rgba(34,197,94,0.15)" : "rgba(220,38,38,0.15)",
      color: ok ? "#22c55e" : "#ef4444",
      border: `1px solid ${ok ? "rgba(34,197,94,0.35)" : "rgba(220,38,38,0.35)"}`,
    };
  };

  const dangerLevel = (score) => {
    if (score == null) return { level: "?", label: "N/A", color: "#94a3b8", glow: false };
    if (score < 0.05) return { level: 10, label: "CRITICAL", color: "#dc2626", glow: true };
    if (score < 0.1) return { level: 8, label: "HIGH", color: "#ef4444", glow: true };
    if (score < 0.2) return { level: 6, label: "MEDIUM", color: "#f59e0b", glow: false };
    if (score < 0.3) return { level: 4, label: "LOW", color: "#eab308", glow: false };
    return { level: 2, label: "SAFE", color: "#22c55e", glow: false };
  };

  const avgRisk =
    alerts.length === 0
      ? 0
      : Math.round(
          alerts
            .slice(0, 20)
            .reduce((a, b) => a + dangerLevel(b?.anomaly_score).level, 0) /
            Math.min(20, alerts.length)
        );

  const attackConfidence = avgRisk >= 8 ? "HIGH" : avgRisk >= 5 ? "MEDIUM" : "LOW";

  return (
    <div style={{ height: "100vh", width: "100vw", background: "radial-gradient(circle at top, #0b1220, #020617)", color: "#e5e7eb" }}>
      <audio ref={beepRef} src="/beep.mp3" preload="auto" />

      <div style={{ padding: 18, height: "100%", display: "grid", gridTemplateRows: "auto 1fr", gap: 14 }}>
        <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h1 style={{ fontSize: 22 }}>🛡 IDS Security Dashboard</h1>
          <div style={{ display: "flex", gap: 10 }}>
            <span style={badge(status)}>Backend: {status}</span>
            <span style={badge(wsStatus)}>WS: {wsStatus}</span>
          </div>
        </header>

        <div style={{ display: "grid", gridTemplateColumns: "1.7fr 1fr", gap: 16, height: "100%" }}>
          {/* LEFT */}
          <div style={{ display: "grid", gridTemplateRows: "auto 1fr", gap: 16 }}>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16 }}>
              <div style={card}>
                <div style={{ opacity: 0.6 }}>Active Alerts</div>
                <div style={{ fontSize: 32, fontWeight: 900 }}>{alerts.length}</div>
              </div>
              <div style={card}>
                <div style={{ opacity: 0.6 }}>Risk Meter</div>
                <div style={{ fontSize: 32, fontWeight: 900, color: avgRisk >= 8 ? "#dc2626" : avgRisk >= 5 ? "#f59e0b" : "#22c55e" }}>
                  {avgRisk}/10
                </div>
              </div>
              <div style={card}>
                <div style={{ opacity: 0.6 }}>Attack Confidence</div>
                <div style={{ fontSize: 18, fontWeight: 800 }}>{attackConfidence}</div>
              </div>
            </div>

            <div style={{ ...card, overflow: "hidden", display: "grid", gridTemplateRows: "auto 1fr" }}>
              <div style={{ fontWeight: 700, marginBottom: 10 }}>🚨 Live Alerts</div>
              <div style={{ overflowY: "auto" }}>
                <table width="100%" style={{ borderCollapse: "collapse", fontSize: 13 }}>
                  <thead>
                    <tr style={{ opacity: 0.6 }}>
                      <th align="left">Time</th>
                      <th align="left">Source</th>
                      <th align="left">Danger</th>
                    </tr>
                  </thead>
                  <tbody>
                    {alerts.map((a, i) => {
                      const d = dangerLevel(a?.anomaly_score);
                      return (
                        <tr key={i} style={{ borderTop: "1px solid #1e293b", boxShadow: d.glow ? "inset 0 0 0 9999px rgba(220,38,38,0.08)" : "none" }}>
                          <td>{a?.time || "-"}</td>
                          <td>{a?.src_ip || "-"}</td>
                          <td style={{ fontWeight: 700, color: d.color }}>
                            {d.level}/10 {d.label}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* RIGHT */}
          <div style={{ display: "grid", gridTemplateRows: "1.2fr 1fr 1fr", gap: 16 }}>
            <div style={card}>
              <div style={{ fontWeight: 700, marginBottom: 8 }}>📈 Anomaly Timeline</div>
              <div style={{ height: 260 }}>
                <ResponsiveContainer>
                  <LineChart data={timeline}>
                    <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
                    <XAxis dataKey="time" tick={{ fill: "#94a3b8", fontSize: 12 }} />
                    <YAxis tick={{ fill: "#94a3b8", fontSize: 12 }} />
                    <Tooltip contentStyle={{ background: "#020617", border: "1px solid #1e293b" }} />
                    <Line type="monotone" dataKey="count" stroke="#38bdf8" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div style={card}>
              <div style={{ fontWeight: 700 }}>🧠 Feature Importance</div>
              <div style={{ opacity: 0.6, fontSize: 12 }}>SHAP visualization available in backend</div>
            </div>

            <div style={card}>
              <div style={{ fontWeight: 700 }}>ℹ️ System Info</div>
              <ul style={{ fontSize: 13, opacity: 0.85, lineHeight: 1.8, paddingLeft: 16 }}>
                <li>Model: Isolation Forest</li>
                <li>Window: 10s</li>
                <li>WebSocket: Real-time</li>
                <li>Explainable AI: SHAP</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
