import React, { useMemo, useState, useEffect } from "react";
import { fetchPlayers } from "./api";
import type { Player } from "./types";
import { Trophy, Calendar, Filter, RefreshCw, Star, Info } from "lucide-react";

const TOP_LEAGUES = [
    { id: 47, name: "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿" },
    { id: 87, name: "La Liga 🇪🇸" },
    { id: 54, name: "Bundesliga 🇩🇪" },
    { id: 55, name: "Serie A 🇮🇹" },
    { id: 53, name: "Ligue 1 🇫🇷" },
];

const SEASONS = ["2024/2025", "2023/2024", "2022/2023"];

export default function App() {
    const [mode, setMode] = useState<"explorer" | "top10">("explorer");
    const [leagueId, setLeagueId] = useState<number>(47);
    const [season, setSeason] = useState<string>("2024/2025");
    const [minMinutes, setMinMinutes] = useState<number>(0);
    const [limit, setLimit] = useState<number>(50);
    const [loading, setLoading] = useState(false);
    const [players, setPlayers] = useState<Player[]>([]);
    const [error, setError] = useState<string | null>(null);

    const top3 = useMemo(() => players.slice(0, 3), [players]);
    const others = useMemo(() => players.slice(3, 10), [players]);

    async function load() {
        setLoading(true);
        setError(null);
        try {
            if (mode === "top10") {
                // Fetch all 5 leagues in parallel
                const promises = TOP_LEAGUES.map(l =>
                    fetchPlayers({ leagueId: l.id, season, minMinutes: 0, limit: 15 })
                );
                const results = await Promise.all(promises);
                const merged = results.flat();

                // Sort by score
                merged.sort((a, b) => b.score - a.score);

                // Keep only unique players (in case of league transfers)
                const unique = Array.from(new Map(merged.map(p => [p.id, p])).values());
                setPlayers(unique.slice(0, 10));
            } else {
                const data = await fetchPlayers({ leagueId, season, minMinutes, limit });
                setPlayers(data);
            }
        } catch (e: any) {
            setError(e?.message ?? "Unknown error");
        } finally {
            setLoading(false);
        }
    }

    // Auto load on start or mode change
    useEffect(() => {
        load();
    }, [mode]);

    return (
        <div className="container" style={{ maxWidth: 1200, margin: "0 auto", padding: "40px 20px" }}>
            <header style={{ marginBottom: 40, textAlign: "center" }}>
                <h1 style={{ fontSize: "2.5rem", fontWeight: 800, marginBottom: 12, background: "linear-gradient(135deg, #60a5fa 0%, #a855f7 100%)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
                    <Trophy size={36} style={{ verticalAlign: "middle", marginRight: 12, color: "#60a5fa" }} />
                    Top Players Index
                </h1>

                <div style={{ display: "inline-flex", gap: 8, background: "rgba(30, 41, 59, 0.5)", backdropFilter: "blur(8px)", padding: 6, borderRadius: 12, border: "1px solid var(--border)", marginBottom: 12 }}>
                    <button className={`nav-tab ${mode === "explorer" ? "active" : ""}`} onClick={() => setMode("explorer")}>League Explorer</button>
                    <button className={`nav-tab ${mode === "top10" ? "active" : ""}`} onClick={() => setMode("top10")}>Elite Rankings</button>
                </div>
                <div style={{ marginTop: 8, fontSize: 11, color: "var(--primary)", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em" }}>
                    Stats aggregated: Domestic League + Cups + UCL/UEL
                </div>
            </header>

            <div className="card" style={{ marginBottom: 32, padding: 32 }}>
                <div className="row" style={{ gap: 24, justifyContent: "center" }}>
                    <label style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                        <span style={{ fontSize: 13, fontWeight: 600, color: "#64748b", display: "flex", alignItems: "center", gap: 6 }}>
                            <Star size={14} /> League
                        </span>
                        <select
                            value={mode === "top10" ? "global" : leagueId}
                            onChange={(e) => {
                                if (e.target.value !== "global") {
                                    setLeagueId(parseInt(e.target.value, 10));
                                }
                            }}
                            className="input-field"
                            disabled={mode === "top10"}
                        >
                            {mode === "top10" ? (
                                <option value="global">All Top 5 Leagues 🌍</option>
                            ) : (
                                TOP_LEAGUES.map((l) => (
                                    <option key={l.id} value={l.id}>{l.name}</option>
                                ))
                            )}
                        </select>
                    </label>

                    <label style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                        <span style={{ fontSize: 13, fontWeight: 600, color: "#64748b", display: "flex", alignItems: "center", gap: 6 }}>
                            <Calendar size={14} /> Season
                        </span>
                        <select
                            value={season}
                            onChange={(e) => setSeason(e.target.value)}
                            className="input-field"
                        >
                            {SEASONS.map((s) => (
                                <option key={s} value={s}>{s}</option>
                            ))}
                        </select>
                    </label>

                    {mode === "explorer" && (
                        <>
                            <label style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                                <span style={{ fontSize: 13, fontWeight: 600, color: "#64748b", display: "flex", alignItems: "center", gap: 6 }}>
                                    <Filter size={14} /> Min Min.
                                </span>
                                <input
                                    type="number"
                                    value={minMinutes}
                                    onChange={(e) => setMinMinutes(parseInt(e.target.value || "0", 10))}
                                    className="input-field"
                                    style={{ width: 100 }}
                                />
                            </label>

                            <label style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                                <span style={{ fontSize: 13, fontWeight: 600, color: "#64748b", display: "flex", alignItems: "center", gap: 6 }}>
                                    <Filter size={14} /> Limit
                                </span>
                                <select
                                    value={limit}
                                    onChange={(e) => setLimit(parseInt(e.target.value, 10))}
                                    className="input-field"
                                    style={{ width: 90 }}
                                >
                                    {[10, 25, 50, 100].map(n => <option key={n} value={n}>{n}</option>)}
                                </select>
                            </label>
                        </>
                    )}

                    <button
                        onClick={load}
                        disabled={loading}
                        className="btn-primary"
                        style={{ alignSelf: "flex-end", height: 44 }}
                    >
                        {loading ? <RefreshCw className="spin" size={20} /> : <RefreshCw size={20} />}
                        <span>{mode === "explorer" ? "Update Ranking" : "Refresh Top 10"}</span>
                    </button>
                </div>

                {error && (
                    <div style={{ marginTop: 24, padding: "12px 16px", background: "rgba(239, 68, 68, 0.1)", border: "1px solid rgba(239, 68, 68, 0.2)", borderRadius: 12, color: "#ef4444", fontSize: 14 }}>
                        Error: {error}
                    </div>
                )}
            </div>

            {mode === "top10" ? (
                <div style={{ animation: "fadeIn 0.5s ease" }}>
                    {players.length >= 3 ? (
                        <div className="pyramid-container">
                            {/* Ranking 2 (Left) */}
                            <div className="podium-step rank-2">
                                <div className="player-avatar">🥈</div>
                                <div className="podium-box" style={{ height: "auto" }}>
                                    <div style={{ fontWeight: 800, fontSize: 18 }}>{players[1].name}</div>
                                    <div style={{ color: "#94a3b8", fontSize: 13 }}>{players[1].team}</div>
                                    <div style={{ marginTop: 4, fontSize: 11, color: "var(--primary)" }}>{players[1].league ?? ""}</div>
                                    <div style={{ marginTop: 20, fontSize: 32, fontWeight: 900, color: "var(--text-main)" }}>
                                        {players[1].score.toFixed(1)}
                                    </div>
                                </div>
                            </div>

                            {/* Ranking 1 (Center) */}
                            <div className="podium-step rank-1">
                                <div className="player-avatar" style={{ transform: "scale(1.2)", marginBottom: 24 }}>👑</div>
                                <div className="podium-box" style={{ height: "auto" }}>
                                    <div style={{ fontWeight: 800, fontSize: 24 }}>{players[0].name}</div>
                                    <div style={{ color: "#94a3b8", fontSize: 14 }}>{players[0].team}</div>
                                    <div style={{ marginTop: 4, fontSize: 12, color: "var(--primary)", fontWeight: 600 }}>{players[0].league ?? ""}</div>
                                    <div style={{ marginTop: 24, fontSize: 48, fontWeight: 900, color: "#f59e0b" }}>
                                        {players[0].score.toFixed(1)}
                                    </div>
                                </div>
                            </div>

                            {/* Ranking 3 (Right) */}
                            <div className="podium-step rank-3">
                                <div className="player-avatar">🥉</div>
                                <div className="podium-box" style={{ height: "auto" }}>
                                    <div style={{ fontWeight: 800, fontSize: 16 }}>{players[2].name}</div>
                                    <div style={{ color: "#94a3b8", fontSize: 12 }}>{players[2].team}</div>
                                    <div style={{ marginTop: 4, fontSize: 11, color: "var(--primary)" }}>{players[2].league ?? ""}</div>
                                    <div style={{ marginTop: 16, fontSize: 28, fontWeight: 900, color: "#b45309" }}>
                                        {players[2].score.toFixed(1)}
                                    </div>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div style={{ textAlign: "center", padding: 40 }}>Not enough players for podium.</div>
                    )}

                    <div style={{ maxWidth: 800, margin: "0 auto" }}>
                        {others.map((p, idx) => (
                            <div key={p.id} className="rank-item">
                                <div className="rank-number">{idx + 4}</div>
                                <div style={{ flex: 1 }}>
                                    <div style={{ fontWeight: 700 }}>{p.name}</div>
                                    <div style={{ fontSize: 12, color: "#94a3b8" }}>{p.team} • {p.position}</div>
                                    <div style={{ fontSize: 11, color: "var(--primary)", marginTop: 2 }}>{p.league}</div>
                                </div>
                                <div style={{ fontSize: 18, fontWeight: 800, color: "#60a5fa" }}>
                                    {p.score.toFixed(1)}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            ) : (
                <>
                    {top3.length > 0 && (
                        <div style={{ marginBottom: 40 }}>
                            <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16, display: "flex", alignItems: "center", gap: 8, color: "#e2e8f0" }}>
                                <Trophy size={20} color="#f59e0b" /> Quick Podium
                            </h2>
                            <div className="row" style={{ gap: 20 }}>
                                {top3.map((p, i) => (
                                    <div key={p.id} className="card podium-card" style={{ flex: 1, position: "relative", overflow: "hidden", padding: 24 }}>
                                        <div style={{ position: "absolute", top: -10, right: -10, fontSize: 60, opacity: 0.05, fontWeight: 900 }}>
                                            {i + 1}
                                        </div>
                                        <div style={{ fontSize: 12, fontWeight: 700, color: i === 0 ? "#f59e0b" : "#94a3b8", marginBottom: 8 }}>RANK #{i + 1}</div>
                                        <div style={{ fontSize: 20, fontWeight: 800, marginBottom: 4 }}>{p.name}</div>
                                        <div style={{ color: "#94a3b8", fontSize: 14 }}>{p.team ?? "—"}</div>
                                        <div style={{ marginTop: 16, fontSize: 24, fontWeight: 800, color: "#60a5fa" }}>
                                            {p.score.toFixed(1)} <span style={{ fontSize: 12, fontWeight: 500, color: "#64748b" }}>pts</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    <div className="card" style={{ padding: 0, overflow: "visible" }}>
                        <table style={{ width: "100%", borderCollapse: "collapse" }}>
                            <thead style={{ background: "#1e293b" }}>
                                <tr>
                                    <th style={{ padding: "16px 20px", color: "#64748b", fontWeight: 700 }}>#</th>
                                    <th style={{ padding: "16px 20px", color: "#e2e8f0" }}>Player</th>
                                    <th style={{ padding: "16px 20px", textAlign: "center" }}>Min</th>
                                    <th style={{ padding: "16px 20px", textAlign: "center" }}>Stats Summary</th>
                                    <th style={{ padding: "16px 20px", textAlign: "center" }}>Score Index</th>
                                </tr>
                            </thead>
                            <tbody>
                                {players.map((p, idx) => (
                                    <tr key={p.id} className="table-row">
                                        <td style={{ padding: "16px 20px", color: "#64748b", fontWeight: 600 }}>{idx + 1}</td>
                                        <td style={{ padding: "16px 20px" }}>
                                            <div style={{ fontWeight: 600 }}>{p.name}</div>
                                            <div style={{ fontSize: 12, color: "#94a3b8" }}>{p.team ?? "—"} • {p.position ?? "?"}</div>
                                        </td>
                                        <td style={{ padding: "16px 20px", textAlign: "center", color: "#94a3b8", fontSize: 13 }}>{p.stats.minutes}</td>
                                        <td style={{ padding: "16px 20px" }}>
                                            <div className="stat-grid">
                                                {p.stats.goal > 0 && <span className="stat-tag">⚽ <b>{p.stats.goal}</b></span>}
                                                {p.stats.assist > 0 && <span className="stat-tag">🅰️ <b>{p.stats.assist}</b></span>}
                                                {p.stats.chancesCreated > 0 && <span className="stat-tag">🔑 <b>{p.stats.chancesCreated}</b></span>}
                                                {p.stats.tackles > 0 && <span className="stat-tag">🛡️ <b>{p.stats.tackles}</b></span>}
                                                {p.stats.interceptions > 0 && <span className="stat-tag">🛑 <b>{p.stats.interceptions}</b></span>}
                                                {p.stats.penaltyWon > 0 && <span className="stat-tag" title="Penalty Won">🎯 <b>{p.stats.penaltyWon}</b></span>}
                                                {p.stats.possWonAtt3rd > 0 && <span className="stat-tag" title="Possession Won Final 3rd">⚡ <b>{p.stats.possWonAtt3rd}</b></span>}
                                                {p.stats.bigChanceMissed > 0 && <span className="stat-tag" style={{ background: "rgba(239, 68, 68, 0.1)" }} title="Big Chance Missed">❌ <b>{p.stats.bigChanceMissed}</b></span>}
                                                {(p.stats.yellowCard > 0 || p.stats.redCard > 0) && (
                                                    <span className="stat-tag" style={{ background: "rgba(239, 68, 68, 0.1)" }}>
                                                        🎴 <b>{p.stats.yellowCard + p.stats.redCard * 2}</b>
                                                    </span>
                                                )}
                                            </div>
                                        </td>
                                        <td style={{ padding: "16px 20px", textAlign: "center" }}>
                                            <div
                                                data-tooltip={Object.entries(p.breakdown)
                                                    .filter(([_, v]) => Math.abs(v) > 0.01)
                                                    .map(([k, v]) => `${k}: ${v > 0 ? "+" : ""}${v.toFixed(1)}`)
                                                    .join(" | ")}
                                                style={{
                                                    display: "inline-block",
                                                    padding: "6px 12px",
                                                    borderRadius: 8,
                                                    background: "rgba(96, 165, 250, 0.1)",
                                                    color: "#60a5fa",
                                                    fontWeight: 800,
                                                    border: "1px solid rgba(96, 165, 250, 0.2)"
                                                }}
                                            >
                                                {p.score.toFixed(1)}
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                        {players.length === 0 && !loading && (
                            <div style={{ padding: 60, textAlign: "center", color: "#64748b" }}>
                                No data available for the selected criteria.
                            </div>
                        )}
                    </div>
                </>
            )}

            <footer style={{ marginTop: 60, padding: "40px 0", borderTop: "1px solid var(--border)", display: "flex", flexDirection: "column", gap: 16, color: "#64748b" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <Info size={16} />
                    <small>
                        <b>Scoring Weights:</b> Goals: 5.0 | Assists: 3.0 | Penalty Won: 2.0 | Big Chance Missed: -1.0 | Poss. Won 3rd: 0.2
                    </small>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <RefreshCw size={16} />
                    <small>
                        Data is aggregated across domestic leagues, national cups (FA Cup, Copa del Rey, etc.), and European trophies (UCL, UEL, UECL).
                    </small>
                </div>
            </footer>
        </div>
    );
}
