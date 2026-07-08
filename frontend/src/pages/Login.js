import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "../components/Navbar";
import { loginUser } from "../services/apiService";
import "./Login.css";

function Login({ user, onLoginSuccess, onLogout }) {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [message, setMessage] = useState("");
    const [messageType, setMessageType] = useState("info");
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = async (event) => {
        event.preventDefault();
        setLoading(true);
        setMessage("");
        setMessageType("info");

        try {
            const data = await loginUser({
                email: email.trim(),
                password,
            });
            onLoginSuccess(data.user);
            setMessage("Login successful. Redirecting...");
            setMessageType("success");
            window.setTimeout(() => navigate("/", { replace: true }), 200);
        } catch (error) {
            setMessage(error.message || "Unable to connect to the server.");
            setMessageType("error");
        } finally {
            setLoading(false);
        }
    };

    return (
        <>
            <Navbar user={user} onLogout={onLogout} />

            <main id="main-content" className="login-container">
                <div className="login-card">
                    <h2>Login</h2>
                    <p>Please sign in to continue.</p>

                    <form onSubmit={handleSubmit} className="login-form">
                        <div className="login-field">
                            <label htmlFor="email" className="login-label">
                                Email address
                            </label>
                            <input
                                id="email"
                                name="email"
                                type="email"
                                value={email}
                                onChange={(event) => setEmail(event.target.value)}
                                placeholder="you@example.com"
                                className="login-input"
                                autoComplete="email"
                                required
                            />
                        </div>

                        <div className="login-field">
                            <label htmlFor="password" className="login-label">
                                Password
                            </label>
                            <input
                                id="password"
                                name="password"
                                type="password"
                                value={password}
                                onChange={(event) => setPassword(event.target.value)}
                                placeholder="Enter your password"
                                className="login-input"
                                autoComplete="current-password"
                                required
                            />
                        </div>

                        <button type="submit" disabled={loading} className="login-button">
                            {loading ? "Signing in..." : "Login"}
                        </button>
                    </form>

                    {message && <p className={`login-message ${messageType}`}>{message}</p>}
                </div>
            </main>
        </>
    );
}

export default Login;
