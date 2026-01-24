import React, { useMemo, useState, useEffect } from "react";
import { fetchPlayers } from "./api";
import type { Player } from "./types";
import { Trophy, Calendar, Filter, RefreshCw, Star, Info, Crown, Medal, TrendingUp } from "lucide-react";

const TOP_LEAGUES = [
    { id: 47, name: "Premier League" },
    { id: 87, name: "La Liga" },
    { id: 54, name: "Bundesliga" },
    { id: 55, name: "Serie A" },
    { id: 53, name: "Ligue 1" },
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
                const promises = TOP_LEAGUES.map(l =>
                    fetchPlayers({ leagueId: l.id, season, minMinutes: 0, limit: 15 })
                );
                const results = await Promise.all(promises);
                const merged = results.flat();
                merged.sort((a, b) => b.score - a.score);

                const uniqueMap = new Map<number, Player>();
                merged.forEach(p => {
                    if (!uniqueMap.has(p.id) || p.score > uniqueMap.get(p.id)!.score) {
                        uniqueMap.set(p.id, p);
                    }
                });

                const unique = Array.from(uniqueMap.values());
                unique.sort((a, b) => b.score - a.score);
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

    useEffect(() => {
        load();
    }, [mode]);

    return (
        <div className="app-container">
            <header style={{ marginBottom: 60, textAlign: "center" }}>
                <h1 className="hero-title">
                    Top <span className="accent">Players</span>
                    <div style={{ fontSize: "1rem", letterSpacing: "0.5em", color: "var(--text-tertiary)", marginTop: 10, fontWeight: 400 }}>
                        Global Performance Index
                    </div>
                </h1>

                <div style={{ display: "flex", justifyContent: "center", marginTop: 30 }}>
                    <div className="mode-toggle">
                        <button 
                            className={`mode-btn ${mode === "explorer" ? "active" : ""}`} 
                            onClick={() => setMode("explorer")}
                        >
                            <Filter size={14} style={{ display: 'inline', marginRight: 6 }} />
                            League Explorer
                        </button>
                        <button 
                            className={`mode-btn ${mode === "top10" ? "active" : ""}`} 
                            onClick={() => setMode("top10")}
                        >
                            <Trophy size={14} style={{ display: 'inline', marginRight: 6 }} />
                            Elite Rankings
                        </button>
                    </div>
                </div>
            </header>

            <div className="control-panel">
                <div className="control-group">
                    <span className="control-label"><Star size={12} /> League</span>
                    <select
                        value={mode === "top10" ? "global" : leagueId}
                        onChange={(e) => {
                            if (e.target.value !== "global") setLeagueId(parseInt(e.target.value, 10));
                        }}
                        className="select-box"
                        disabled={mode === "top10"}
                    >
                        {mode === "top10" ? (
                            <option value="global">ALL REGIONS 🌍</option>
                        ) : (
                            TOP_LEAGUES.map((l) => <option key={l.id} value={l.id}>{l.name}</option>)
                        )}
                    </select>
                </div>

                <div className="control-group">
                    <span className="control-label"><Calendar size={12} /> Season</span>
                    <select
                        value={season}
                        onChange={(e) => setSeason(e.target.value)}
                        className="select-box"
                    >
                        {SEASONS.map((s) => <option key={s} value={s}>{s}</option>)}
                    </select>
                </div>

                {mode === "explorer" && (
                    <>
                        <div className="control-group">
                            <span className="control-label">Min Minutes</span>
                            <input
                                type="number"
                                value={minMinutes}
                                onChange={(e) => setMinMinutes(parseInt(e.target.value || "0", 10))}
                                className="input-box"
                                style={{ width: 100 }}
                            />
                        </div>
                        <div className="control-group">
                            <span className="control-label">Limit</span>
                            <select
                                value={limit}
                                onChange={(e) => setLimit(parseInt(e.target.value, 10))}
                                className="select-box"
                                style={{ width: 90 }}
                            >
                                {[10, 25, 50, 100].map(n => <option key={n} value={n}>{n}</option>)}
                            </select>
                        </div>
                    </>
                )}

                <div style={{ flex: 1 }}></div>

                <button onClick={load} disabled={loading} className="btn-action">
                    {loading ? <RefreshCw className="spin" size={18} /> : <RefreshCw size={18} />}
                    <span>{mode === "explorer" ? "UPDATE DATA" : "REFRESH"}</span>
                </button>
            </div>

            {loading && <div className="loader-bar"></div>}
            
            {error && (
                <div style={{ marginBottom: 32, padding: 16, border: "1px solid #ef4444", color: "#ef4444", background: "rgba(239, 68, 68, 0.05)" }}>
                    SYSTEM ERROR: {error}
                </div>
            )}

            {mode === "top10" ? (
                <div style={{ animation: "fadeIn 0.5s ease" }}>
                    {players.length >= 3 ? (
                        <div className="podium-grid">
                            
                            {/* Silver */}
                            <div className="podium-column silver">
                                <div className="rank-badge">2</div>
                                <div className="player-avatar" style={{ fontSize: 40, marginBottom: 20 }}>🥈</div>
                                <div className="player-name-large">{players[1].name}</div>
                                <div className="text-muted u-upper" style={{fontSize: '0.8rem'}}>{players[1].team}</div>
                                <div className="player-score-huge" style={{ marginTop: 'auto', marginBottom: 20, fontSize: '3rem', color: '#a0a0a0' }}>
                                    {players[1].score.toFixed(1)}
                                </div>
                            </div>

                            {/* Gold */}
                            <div className="podium-column gold">
                                <div className="rank-badge" style={{color: 'rgba(212, 175, 55, 0.1)'}}>1</div>
                                <Crown size={40} className="text-gold" style={{ marginBottom: 20 }} />
                                <div className="player-name-large" style={{ fontSize: '1.5rem', color: 'var(--accent-gold)' }}>{players[0].name}</div>
                                <div className="text-muted u-upper" style={{fontSize: '0.9rem'}}>{players[0].team}</div>
                                <div className="player-score-huge" style={{ marginTop: 'auto', marginBottom: 30, color: 'var(--accent-gold)' }}>
                                    {players[0].score.toFixed(1)}
                                </div>
                            </div>

                            {/* Bronze */}
                            <div className="podium-column bronze">
                                <div className="rank-badge">3</div>
                                <div className="player-avatar" style={{ fontSize: 40, marginBottom: 20 }}>🥉</div>
                                <div className="player-name-large">{players[2].name}</div>
                                <div className="text-muted u-upper" style={{fontSize: '0.8rem'}}>{players[2].team}</div>
                                <div className="player-score-huge" style={{ marginTop: 'auto', marginBottom: 20, fontSize: '2.5rem', color: '#cd7f32' }}>
                                    {players[2].score.toFixed(1)}
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-secondary)' }}>INSUFFICIENT DATA FOR PODIUM</div>
                    )}

                    <h3 className="section-title">CHALLENGERS</h3>
                    
                    <div className="data-grid">
                        <div className="grid-row grid-header">
                            <div>RANK</div>
                            <div>PLAYER</div>
                            <div>TEAM</div>
                            <div style={{textAlign: 'right'}}>SCORE</div>
                        </div>
                        {others.map((p, idx) => (
                            <div key={p.id} className="grid-row">
                                <div className="cell-rank">{idx + 4}</div>
                                <div style={{fontWeight: 700}}>{p.name}</div>
                                <div className="text-muted u-upper" style={{fontSize: '0.8rem'}}>{p.team}</div>
                                <div style={{textAlign: 'right', fontWeight: 800, color: 'var(--accent-primary)', fontSize: '1.2rem'}}>
                                    {p.score.toFixed(1)}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            ) : (
                <div className="data-grid">
                    <div className="grid-row grid-header">
                        <div>#</div>
                        <div>PLAYER</div>
                        <div style={{textAlign: "center"}}>MIN</div>
                        <div>KEY STATS</div>
                        <div style={{textAlign: "right"}}>INDEX</div>
                    </div>
                    {players.map((p, idx) => (
                        <div key={p.id} className="grid-row">
                            <div className="cell-rank" style={{fontSize: '1rem', color: 'var(--text-tertiary)'}}>{idx + 1}</div>
                            <div>
                                <div style={{ fontWeight: 700, fontSize: '1.1rem' }}>{p.name}</div>
                                <div className="text-muted u-upper" style={{ fontSize: '0.75rem', marginTop: 4 }}>{p.team}</div>
                            </div>
                            <div style={{ textAlign: "center", color: 'var(--text-secondary)' }}>{p.stats.minutes}</div>
                            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                                {p.stats.goal > 0 && <span className="stat-pill highlight">⚽ {p.stats.goal}</span>}
                                {p.stats.assist > 0 && <span className="stat-pill highlight">🅰️ {p.stats.assist}</span>}
                                {p.stats.chancesCreated > 0 && <span className="stat-pill">🔑 {p.stats.chancesCreated}</span>}
                                {p.stats.tackles > 0 && <span className="stat-pill">🛡️ {p.stats.tackles}</span>}
                            </div>
                            <div style={{ textAlign: "right" }}>
                                <div className="score-badge">
                                    {p.score.toFixed(1)}
                                </div>
                            </div>
                        </div>
                    ))}
                    {players.length === 0 && !loading && (
                        <div style={{ padding: 60, textAlign: "center", color: "var(--text-tertiary)" }}>
                            NO PLAYERS MATCH THE CRITERIA
                        </div>
                    )}
                </div>
            )}

            <footer style={{ marginTop: 80, borderTop: "1px solid var(--border-light)", padding: "40px 0", color: "var(--text-tertiary)", fontSize: "0.8rem" }}>
                <div style={{ display: "flex", gap: 24, justifyContent: "center", textTransform: "uppercase", letterSpacing: "0.1em" }}>
                    <span><Info size={14} style={{verticalAlign: 'text-bottom'}} /> Scoring Model v2.1</span>
                    <span>Updated: {new Date().toLocaleDateString()}</span>
                </div>
            </footer>
        </div>
    );
}
