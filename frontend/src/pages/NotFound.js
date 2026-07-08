import { Link } from "react-router-dom";
import Navbar from "../components/Navbar";
import "../components/ReceiptUpload.css";

function NotFound() {
    return (
        <>
            <Navbar />
            <main id="main-content" className="receipt-container">
                <h2>Page not found</h2>
                <p>The page you’re looking for doesn’t exist or may have moved.</p>
                <Link to="/" className="upload-button" style={{ display: "inline-block", textDecoration: "none" }}>
                    Go back home
                </Link>
            </main>
        </>
    );
}

export default NotFound;
