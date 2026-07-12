import { useState } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import Home from "./pages/Home";
import Summary from "./pages/Summary";
import ReceiptUpload from "./components/ReceiptUpload";
import Login from "./pages/Login";
import NotFound from "./pages/NotFound";
import Register from "./pages/Register";

function ProtectedRoute({ user, children }) {
    if (!user) {
        return <Navigate to="/login" replace />;
    }

    return children;
}

function App() {
    const [user, setUser] = useState(() => {
        const storedUser = localStorage.getItem("loggedInUser");
        return storedUser ? JSON.parse(storedUser) : null;
    });

    const handleLoginSuccess = (loggedInUser) => {
        localStorage.setItem("loggedInUser", JSON.stringify(loggedInUser));
        setUser(loggedInUser);
    };

    const handleLogout = () => {
        localStorage.removeItem("loggedInUser");
        setUser(null);
    };

    return (
        <BrowserRouter>
            <Routes>
                <Route
                    path="/login"
                    element={
                        user ? (
                            <Navigate to="/" replace />
                        ) : (
                            <Login
                                user={user}
                                onLoginSuccess={handleLoginSuccess}
                                onLogout={handleLogout}
                            />
                        )
                    }
                />

                <Route
                    path="/register"
                    element={
                        user ? (
                            <Navigate to="/" replace />
                        ) : (
                            <Register user={user} onLogout={handleLogout} />
                        )
                    }
                />

                <Route
                    path="/"
                    element={
                        <ProtectedRoute user={user}>
                            <Home user={user} onLogout={handleLogout} />
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/upload"
                    element={
                        <ProtectedRoute user={user}>
                            <ReceiptUpload user={user} onLogout={handleLogout} />
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/summary"
                    element={
                        <ProtectedRoute user={user}>
                            <Summary user={user} onLogout={handleLogout} />
                        </ProtectedRoute>
                    }
                />

                <Route path="*" element={<NotFound />} />
            </Routes>
        </BrowserRouter>
    );
}

export default App;
