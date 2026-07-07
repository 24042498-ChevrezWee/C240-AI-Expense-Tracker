import Navbar from "../components/Navbar";

function Home() {
    return (
        <>
            <Navbar />

            <div style={{ textAlign: "center", marginTop: "60px" }}>
                <h1>Welcome to AI Expense Tracker</h1>

                <p>
                    Upload your receipts and let AI organize your expenses.
                </p>
            </div>
        </>
    );
}

export default Home;