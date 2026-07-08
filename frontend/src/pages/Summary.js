import { useEffect, useState } from "react";
import Navbar from "../components/Navbar";
import { getDashboardSummary, getRecentReceipts } from "../services/dashboardService";
import { clearAllData } from "../services/apiService";
import "./Summary.css";

function Summary({ user, onLogout }) {
    const [summary, setSummary] = useState(null);
    const [recentReceipts, setRecentReceipts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [actionMessage, setActionMessage] = useState("");
    const [actionMessageType, setActionMessageType] = useState("info");
    const [isClearing, setIsClearing] = useState(false);

    async function loadData() {
        try {
            setLoading(true);
            setError("");
            const dashboardData = await getDashboardSummary(user?.user_id);
            const recentData = await getRecentReceipts(user?.user_id);
            setSummary(dashboardData);
            setRecentReceipts(recentData);
        } catch (err) {
            setError(err.message || "Unable to load summary data.");
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        loadData();
    }, [user?.user_id]);

    const handleClearAllData = async () => {
        if (isClearing) {
            return;
        }

        const confirmed = window.confirm(
            "Are you sure you want to delete all receipts? This action cannot be undone.",
        );
        if (!confirmed) {
            return;
        }

        try {
            setIsClearing(true);
            setActionMessage("");
            setActionMessageType("info");
            await clearAllData();
            await loadData();
            setActionMessage("All receipt data has been cleared successfully.");
            setActionMessageType("success");
        } catch (err) {
            setActionMessage(err.message || "Unable to clear data right now.");
            setActionMessageType("error");
        } finally {
            setIsClearing(false);
        }
    };

    return (
        <>
            <Navbar user={user} onLogout={onLogout} />

            <main id="main-content" className="summary-shell">
                <section className="summary-header">
                    <div className="summary-header-top">
                        <div>
                            <h1>Expense Summary</h1>
                            <p>Track your spending trends and recent receipt activity.</p>
                        </div>
                        <button
                            type="button"
                            className="danger-button"
                            onClick={handleClearAllData}
                            disabled={isClearing}
                        >
                            {isClearing ? "Clearing..." : "Clear All Data"}
                        </button>
                    </div>
                </section>

                {actionMessage ? (
                    <div className={`summary-alert ${actionMessageType}`}>{actionMessage}</div>
                ) : null}

                {loading ? (
                    <div className="summary-card loading-card">Loading summary...</div>
                ) : error ? (
                    <div className="summary-card loading-card">{error}</div>
                ) : summary ? (
                    <>
                        <section className="summary-grid">
                            <article className="summary-card">
                                <p className="summary-label">Total Expenses</p>
                                <h3>SGD {summary.totalExpenses.toFixed(2)}</h3>
                            </article>

                            <article className="summary-card">
                                <p className="summary-label">Monthly Spending</p>
                                <h3>SGD {summary.monthlySpending.toFixed(2)}</h3>
                            </article>

                            <article className="summary-card">
                                <p className="summary-label">Total Receipts</p>
                                <h3>{summary.receiptCount}</h3>
                            </article>

                            <article className="summary-card">
                                <p className="summary-label">Largest Expense</p>
                                <h3>{summary.largestExpense || "-"}</h3>
                            </article>
                        </section>

                        <section className="summary-section">
                            <h2>Spending By Category</h2>
                            <div className="category-list">
                                {summary.categories && summary.categories.length > 0 ? (
                                    summary.categories.map((item) => (
                                        <div key={item.name} className="category-item">
                                            <div>
                                                <strong>{item.name}</strong>
                                                <p>{item.count} receipts</p>
                                            </div>
                                            <strong>SGD {item.total.toFixed(2)}</strong>
                                        </div>
                                    ))
                                ) : (
                                    <p>No category data available yet.</p>
                                )}
                            </div>
                        </section>

                        <section className="summary-section">
                            <h2>Average Expense</h2>
                            <p>SGD {summary.averageExpense?.toFixed(2) || "0.00"}</p>
                        </section>

                        <section className="summary-section">
                            <h2>Recent Receipts</h2>
                            <div className="receipt-list">
                                {recentReceipts.length > 0 ? (
                                    recentReceipts.map((receipt) => (
                                        <div key={receipt.id} className="receipt-item">
                                            <div>
                                                <strong>{receipt.merchant}</strong>
                                                <p>{receipt.category}</p>
                                            </div>
                                            <div>
                                                <strong>{receipt.currency} {Number(receipt.amount).toFixed(2)}</strong>
                                                <p>{receipt.date}</p>
                                            </div>
                                        </div>
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

export default Summary;
