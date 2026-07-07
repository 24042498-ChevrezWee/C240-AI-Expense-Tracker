import { Link } from "react-router-dom";
import "./Navbar.css";

function Navbar() {
    return (
        <nav className="navbar">
            <div className="logo">
                AI Expense Tracker
            </div>

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
            </ul>
        </nav>
    );
}

export default Navbar;