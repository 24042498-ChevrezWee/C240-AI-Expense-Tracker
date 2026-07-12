import Navbar from "../components/Navbar";
import "./Register.css";

const rawBotpressSignupUrl = process.env.REACT_APP_BOTPRESS_SIGNUP_URL;
const botpressSignupUrl = (rawBotpressSignupUrl || "").trim().replace(/^['"]|['"]$/g, "");

function Register({ user, onLogout }) {
    const handleSignUpClick = () => {
        if (!botpressSignupUrl) {
            window.alert("Add your Botpress share link as REACT_APP_BOTPRESS_SIGNUP_URL in frontend/.env and restart the React app.");
            return;
        }

        window.open(botpressSignupUrl, "_blank", "noopener,noreferrer");
    };

    return (
        <>
            <Navbar user={user} onLogout={onLogout} />

            <main id="main-content" className="register-container">
                <section className="register-card">
                    <h2>Create an account</h2>
                    <p>Start the guided sign-up chat to create your Expense Tracker account.</p>

                    <button type="button" className="signup-button" onClick={handleSignUpClick}>
                        Sign Up
                    </button>
                </section>
            </main>
        </>
    );
}

export default Register;
