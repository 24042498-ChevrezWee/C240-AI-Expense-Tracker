import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Navbar from "../components/Navbar";
import { getDashboardSummary } from "../services/dashboardService";
import "./Home.css";

function Home({ user, onLogout }) {
    const [summary, setSummary] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        async function loadSummary() {
            try {
                setLoading(true);
                setError("");
                const data = await getDashboardSummary(user?.user_id);
                setSummary(data);
            } catch (err) {
                setError(err.message || "Unable to load dashboard summary.");
            } finally {
                setLoading(false);
            }
        }

        loadSummary();
    }, [user?.user_id]);

    return (
        <>
            <Navbar user={user} onLogout={onLogout} />

            <main id="main-content" className="dashboard-shell">
                <section className="dashboard-hero">
                    <div>
                        <p className="dashboard-eyebrow">AI Receipt & Expense Tracker</p>
                        <h1>Welcome back{user ? `, ${user.first_name || user.email}` : ""}</h1>
                        <p className="dashboard-copy">
                            Keep your receipts organized and your spending under control.
                        </p>
                    </div>

                    <div className="dashboard-actions">
                        <Link to="/upload" className="dashboard-action-card">
                            <strong>Upload Receipt</strong>
                            <span>Scan and save a new receipt</span>
                        </Link>
                        <Link to="/summary" className="dashboard-action-card">
                            <strong>View Summary</strong>
                            <span>See your spending overview</span>
                        </Link>
                    </div>
                </section>

                {loading ? (
                    <div className="dashboard-card loading-card">Loading dashboard...</div>
                ) : error ? (
                    <div className="dashboard-card loading-card">{error}</div>
                ) : summary ? (
                    <>
                        {summary.receiptCount === 0 ? (
                            <section className="dashboard-card loading-card">
                                No receipts uploaded yet.
                            </section>
                        ) : null}

                        <section className="dashboard-grid">
                            <article className="dashboard-card">
                                <p className="card-label">Total expenses</p>
                                <h3>SGD {summary.totalExpenses.toFixed(2)}</h3>
                            </article>

                            <article className="dashboard-card">
                                <p className="card-label">Receipts uploaded</p>
                                <h3>{summary.receiptCount}</h3>
                            </article>

                            <article className="dashboard-card">
                                <p className="card-label">Monthly spending</p>
                                <h3>SGD {summary.monthlySpending.toFixed(2)}</h3>
                            </article>

                            <article className="dashboard-card">
                                <p className="card-label">Top spending category</p>
                                <h3>{summary.topCategory}</h3>
                            </article>
                        </section>

                        <section className="dashboard-section">
                            <div className="dashboard-section-header">
                                <h2>Recent receipts</h2>
                            </div>

                            <div className="recent-list">
                                {summary.recentReceipts.length > 0 ? (
                                    summary.recentReceipts.map((receipt) => (
                                        <article key={receipt.id} className="recent-item">
                                            <div>
                                                <strong>{receipt.merchant}</strong>
                                                <p>{receipt.category}</p>
                                            </div>
                                            <div className="recent-meta">
                                                <strong>{receipt.currency} {Number(receipt.amount).toFixed(2)}</strong>
                                                <span>{receipt.date}</span>
                                            </div>
                                        </article>
                                    ))
                                ) : (
                                    <p>No recent receipts available yet.</p>
                                )}
                            </div>
                        </section>
                    </>
                ) : null}
            </main>
        </>
    );
}

export default Home;