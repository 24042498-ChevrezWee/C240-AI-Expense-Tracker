import { Link } from "react-router-dom";
import "./Navbar.css";

function Navbar({ user, onLogout }) {
    return (
        <>
            <a href="#main-content" className="skip-link">
                Skip to content
            </a>

            <nav className="navbar" aria-label="Primary">
            <Link to="/" className="logo">
                AI Expense Tracker
            </Link>

            <ul className="nav-links">
                <li>
                    <Link to="/">Home</Link>
                </li>

                <li>
                    <Link to="/upload">Upload Receipt</Link>
                </li>

                <li>
                    <Link to="/summary">Expense Summary</Link>
                </li>

                {user ? (
                    <>
                        <li className="nav-user">{user.first_name || user.email}</li>
                        <li>
                            <button type="button" className="logout-button" onClick={onLogout}>
                                Logout
                            </button>
                        </li>
                    </>
                ) : (
                    <li>
                        <Link to="/login">Login</Link>
                    </li>
                )}
            </ul>
            </nav>
        </>
    );
}

export default Navbar;