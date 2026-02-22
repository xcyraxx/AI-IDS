import { useEffect, useState, useRef } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  AreaChart,
  Area
} from "recharts";

const API_BASE = "http://127.0.0.1:8000";
const WS_URL = "ws://127.0.0.1:8000/ws/alerts";

export default function App() {
  const [status, setStatus] = useState("loading...");
  const [alerts, setAlerts] = useState([]);
  const [wsStatus, setWsStatus] = useState("disconnected");
  const [timeline, setTimeline] = useState([]);
  const [sysInfo, setSysInfo] = useState(null);
  const [stats, setStats] = useState(null);
  const [shapTimestamp, setShapTimestamp] = useState(Date.now());

  // Initialize Data
  useEffect(() => {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 4000);

    fetch(`${API_BASE}/status`, { signal: controller.signal })
      .then((r) => r.json())
      .then((d) => setStatus(d.status || d.backend || "ok"))
      .catch(() => setStatus("offline"))
      .finally(() => clearTimeout(timeout));

    fetch(`${API_BASE}/alerts`)
      .then((r) => r.json())
      .then((d) => setAlerts(Array.isArray(d) ? d : []))
      .catch(() => setAlerts([]));

    fetch(`${API_BASE}/model-info`)
      .then((r) => r.json())
      .then((d) => setSysInfo(d))
      .catch(() => setSysInfo(null));

    const pollData = () => {
      fetch(`${API_BASE}/statistics`)
        .then((r) => r.json())
        .then((d) => setStats(d))
        .catch(() => { });

      fetch(`${API_BASE}/scores`)
        .then((r) => r.json())
        .then((d) => {
          if (Array.isArray(d)) {
            const formatted = d.map(p => ({
              time: p.time ? p.time.split(' ')[1] : '-',
              score: p.anomaly_score,
              count: p.anomaly_score < 0.1 ? 1 : 0
            }));
            setTimeline(formatted);
          }
        })
        .catch(() => { });
    };

    pollData();
    const interval = setInterval(pollData, 5000);
    return () => {
      clearInterval(interval);
      clearTimeout(timeout);
    };
  }, []);

  // WebSocket
  useEffect(() => {
    let ws;
    let retry;
    const connect = () => {
      ws = new WebSocket(WS_URL);
      ws.onopen = () => setWsStatus("connected");
      ws.onclose = () => {
        setWsStatus("reconnecting");
        retry = setTimeout(connect, 2000);
      };
      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          const batch = Array.isArray(payload) ? payload : [payload];
          setShapTimestamp(Date.now());
          setAlerts((prev) => [...batch, ...prev].slice(0, 500));
        } catch (e) {
          console.error("WS error:", e);
        }
      };
    };
    connect();
    return () => {
      clearTimeout(retry);
      ws?.close();
    };
  }, []);

  const getDanger = (score) => {
    if (score == null) return { level: "?", label: "N/A", color: "#94a3b8" };
    if (score < 0.05) return { level: 10, label: "CRITICAL", color: "#f43f5e" };
    if (score < 0.1) return { level: 8, label: "HIGH", color: "#ef4444" };
    if (score < 0.2) return { level: 6, label: "MEDIUM", color: "#f59e0b" };
    return { level: 2, label: "SAFE", color: "#10b981" };
  };

  return (
    <div className="dashboard-container">

      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
        <div>
          <h1 style={{ fontSize: "1.75rem", fontWeight: 800 }}>Cool Name</h1>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem" }}>Real-time Neural Intrusion Detection</p>
        </div>
        <div style={{ display: "flex", gap: "0.75rem" }}>
          <span className={`status-badge ${status === 'ok' ? 'badge-ok' : 'badge-error'}`}>
            API: {status}
          </span>
          <span className={`status-badge ${wsStatus === 'connected' ? 'badge-ok' : 'badge-wait'}`}>
            Live Stream: {wsStatus}
          </span>
        </div>
      </header>

      <main className="main-grid">
        {/* Left Column: Stats + Timeline + Alerts */}
        <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem", minHeight: 0 }}>

          <div className="stat-grid">
            <div className="glass-card stat-card">
              <span className="stat-label">Total Alerts</span>
              <span className="stat-value">{stats?.total_alerts || 0}</span>
            </div>
            <div className="glass-card stat-card">
              <span className="stat-label">Avg Anomaly Score</span>
              <span className="stat-value" style={{ color: (stats?.average_anomaly_score < 0.2) ? 'var(--accent-red)' : 'var(--text-primary)' }}>
                {stats?.average_anomaly_score || "0.0000"}
              </span>
            </div>
            <div className="glass-card stat-card">
              <span className="stat-label">System Health</span>
              <span className="stat-value" style={{ color: 'var(--accent-green)' }}>EXCELLENT</span>
            </div>
          </div>

          <div className="glass-card" style={{ flex: 1, minHeight: "300px" }}>
            <h3 className="heading-font" style={{ marginBottom: "1.25rem", fontSize: "1.1rem" }}>Anomaly Timeline</h3>
            <div style={{ flex: 1 }}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={timeline}>
                  <defs>
                    <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#38bdf8" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="rgba(255,255,255,0.05)" vertical={false} />
                  <XAxis dataKey="time" axisLine={false} tickLine={false} tick={{ fill: '#475569', fontSize: 10 }} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fill: '#475569', fontSize: 10 }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                    itemStyle={{ color: '#fff' }}
                  />
                  <Area type="monotone" dataKey="score" stroke="#38bdf8" fillOpacity={1} fill="url(#colorScore)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="glass-card" style={{ flex: 1.2, minHeight: 0 }}>
            <h3 className="heading-font" style={{ marginBottom: "1rem", fontSize: "1.1rem" }}>Incursion Log</h3>
            <div className="table-container">
              <table className="custom-table">
                <thead>
                  <tr>
                    <th>TIMESTAMP</th>
                    <th>SOURCE IP</th>
                    <th>THREAT LEVEL</th>
                  </tr>
                </thead>
                <tbody>
                  {alerts.map((a, i) => {
                    const d = getDanger(a?.anomaly_score);
                    return (
                      <tr key={i}>
                        <td style={{ color: "var(--text-secondary)", fontFamily: "monospace" }}>{a?.time || "-"}</td>
                        <td style={{ fontWeight: 600 }}>{a?.src_ip || "-"}</td>
                        <td style={{ color: d.color, fontWeight: 700 }}>
                          <span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', background: d.color, marginRight: 8 }}></span>
                          {d.label}
                        </td>
                      </tr>
                    );
                  })}
                  {alerts.length === 0 && (
                    <tr>
                      <td colSpan="3" style={{ textAlign: "center", padding: "3rem", opacity: 0.3 }}>Monitoring network for threats...</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right Column: SHAP + System Info */}
        <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
          <div className="glass-card" style={{ height: "450px" }}>
            <h3 className="heading-font" style={{ marginBottom: "1rem", fontSize: "1.1rem" }}>Neural Explanation (SHAP)</h3>
            <div className="shap-container">
              <img
                src={`${API_BASE}/explain/shap_feature_importance.png?t=${shapTimestamp}`}
                alt="Explanation Graph"
                style={{ maxWidth: "100%", maxHeight: "100%", objectFit: "contain" }}
                onError={(e) => { e.target.style.display = 'none'; }}
                onLoad={(e) => { e.target.style.display = 'block'; }}
              />
              <div style={{ position: 'absolute', opacity: 0.2, fontSize: "0.75rem", textAlign: "center", padding: "2rem" }}>
                Waiting for anomaly detection to generate XAI visualization...
              </div>
            </div>
          </div>

          <div className="glass-card">
            <h3 className="heading-font" style={{ marginBottom: "1.25rem", fontSize: "1.1rem" }}>System Intelligence</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "0.85rem" }}>
              <div style={sysRow}>
                <span style={sysLabel}>AI Model</span>
                <span style={sysVal}>{sysInfo?.model || "Isolation Forest"}</span>
              </div>
              <div style={sysRow}>
                <span style={sysLabel}>Analysis Window</span>
                <span style={sysVal}>{sysInfo?.window || "10.0s"}</span>
              </div>
              <div style={sysRow}>
                <span style={sysLabel}>Sensitivity</span>
                <span style={sysVal}>{sysInfo?.threshold || "0.10"}</span>
              </div>
              <div style={sysRow}>
                <span style={sysLabel}>Engine Status</span>
                <span style={{ ...sysVal, color: 'var(--accent-green)' }}>OPTIMIZED</span>
              </div>
            </div>

            <div style={{ marginTop: "1.5rem", padding: "1rem", background: "rgba(56, 189, 248, 0.05)", borderRadius: "0.75rem", border: "1px border var(--border-subtle)" }}>
              <h4 style={{ fontSize: "0.75rem", color: "var(--accent-blue)", marginBottom: "0.5rem", fontWeight: 700 }}>ACTIVE FEATURES</h4>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem" }}>
                {sysInfo?.features?.map((f, i) => (
                  <span key={i} style={{ fontSize: "0.65rem", padding: "0.2rem 0.5rem", background: "rgba(255,255,255,0.05)", borderRadius: "4px", color: "var(--text-secondary)" }}>{f}</span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

const sysRow = { display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid rgba(255,255,255,0.03)", paddingBottom: "0.5rem" };
const sysLabel = { fontSize: "0.8125rem", color: "var(--text-secondary)" };
const sysVal = { fontSize: "0.8125rem", fontWeight: 600, fontFamily: "monospace" };
